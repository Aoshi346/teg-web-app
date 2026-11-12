#!/usr/bin/env python3
"""verify_ticket.py — verificar un ticket Django es UN comando: criterios → capturas → informe.

QUÉ ES (WA-4, sub-ola 4.16). En develop cada ticket fabricaba sus herramientas: `sesion.py`, un
`pwlib.py` copiado de ticket en ticket y un `build_informe.py` de ~750 líneas reescrito cada vez.
Aquí se declara el ticket en `ticket.json` y sale el informe del report-kit, sin escribir código:

  1. una cookie de sesión por actor, sin contraseña (`session_login.py`: se niega con DEBUG=False
     o con una BBDD no local);
  2. por criterio: abre la URL como su actor, espera a los loaders, comprueba estado HTTP y textos,
     y captura SOLO tras la guarda de datos personales (`scripts/guarda_pii_capturas.py`: enmascara
     las celdas declaradas y descarta la captura si queda un dato real);
  3. `resultados.json` → `report.json` del kit (un item por criterio, uno por auditor en
     «Anotaciones del auditor», uno para la revisión visual de las capturas y `meta.pedido`);
  4. `embed.py` + `build.py` (perfil `minimo`) y, con `--pdf`, el PDF de `results.html`.

USO (con un python que tenga playwright; el de Django se pasa aparte si es otro):
    python3 .claude/skills/verify-ticket/verify_ticket.py <plan>/verificacion/ticket.json \\
        [--django-python backend/.venv/bin/python] [--pdf]
    python3 .claude/skills/verify-ticket/verify_ticket.py --self-test      # sin Django ni navegador

Salida: 0 todos los criterios `done` · 1 alguno no, o un guard se negó (login, PII) · 2 no se pudo
medir (ticket ilegible, base_url no local, sin playwright). Formato de `ticket.json`: SKILL.md.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import functools
import http.server
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlparse

KIT = pathlib.Path(__file__).resolve().parent
CLAUDE = KIT.parent.parent
REPORT_KIT = CLAUDE / "templates" / "report_kit"
SCHEMA = "ticket-verify/1"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
#: Lo que Python y Chromium parsean distinto (WHATWG trata «\» como «/»): fuera de base_url y url.
URL_TRAPS = re.compile(r"[\\@\s]|[\x00-\x1f]")
VERDICT_STATUS = {"done": "done", "partial": "review", "notdone": "review", "blocked": "blocked",
                  "review": "review", None: "review"}
EPICS = {"AC": {"name": "Criterios de aceptación", "color": "#2563eb"},
         "AUD": {"name": "Anotaciones del auditor", "color": "#7c3aed"},
         "PII": {"name": "Revisión de capturas", "color": "#b45309"}}


class Unmeasurable(RuntimeError):
    """No se pudo medir: exit 2."""


class GuardRefused(RuntimeError):
    """session_login.py se negó (DEBUG, BBDD, usuario): exit 1, sin capturar nada."""


# --------------------------------------------------------------------------- ticket.json


def load_ticket(path: pathlib.Path) -> dict:
    try:
        t = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Unmeasurable(f"no puedo leer {path}: {exc}") from exc
    return validate_ticket(t)


def validate_ticket(t: dict) -> dict:
    if not isinstance(t, dict) or t.get("schema") != SCHEMA:
        raise Unmeasurable(f"ticket.json necesita \"schema\": \"{SCHEMA}\"")
    for key in ("ticket", "base_url", "criteria"):
        if not t.get(key):
            raise Unmeasurable(f"ticket.json sin «{key}»")
    base = urlparse(t["base_url"])
    host = (base.hostname or "").lower()
    if base.scheme not in ("http", "https") or URL_TRAPS.search(t["base_url"]):
        raise Unmeasurable("base_url: solo http(s) y sin «\\», «@» ni espacios")
    if host not in LOCAL_HOSTS:
        raise Unmeasurable(f"base_url apunta a '{host}': el kit solo verifica contra 127.0.0.1")
    actors = t.get("actors") or {}
    ids = set()
    for c in t["criteria"]:
        for key in ("id", "title", "url"):
            if not c.get(key):
                raise Unmeasurable(f"criterio sin «{key}»: {c}")
        if not SAFE_ID.fullmatch(str(c["id"])):
            raise Unmeasurable(f"id de criterio no válido (letras, números, . _ -): {c['id']!r}")
        u = str(c["url"])
        if u.startswith("//") or "://" in u or URL_TRAPS.search(u):
            raise Unmeasurable(f"{c['id']}: «url» es una ruta de la app (/x/), no otra dirección")
        if c["id"] in ids:
            raise Unmeasurable(f"criterio repetido: {c['id']}")
        ids.add(c["id"])
        if c.get("actor") and c["actor"] not in actors:
            raise Unmeasurable(f"{c['id']}: el actor '{c['actor']}' no está en «actors»")
    if any(c.get("actor") for c in t["criteria"]) and not t.get("settings"):
        raise Unmeasurable("hay actores y falta «settings» (los settings de desarrollo)")
    return t


# --------------------------------------------------------------------------- sesiones


def actor_cookie(t: dict, actor: str, django_python: str, backend_dir: pathlib.Path) -> dict:
    """La cookie del actor, pidiéndosela a session_login.py con el python del proyecto."""
    host = urlparse(t["base_url"]).hostname
    argv = [django_python, str(KIT / "session_login.py"), "--settings", t["settings"],
            "--username", t["actors"][actor]["username"], "--domain", host]
    if t.get("forbidden_db"):
        argv += ["--forbidden-db", *t["forbidden_db"]]
    try:
        r = subprocess.run(argv, cwd=backend_dir, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Unmeasurable(f"actor '{actor}': no pude lanzar session_login con {django_python}: {exc}") from exc
    if r.returncode == 1 and "me niego" in r.stderr:
        raise GuardRefused(f"actor '{actor}': {r.stderr.strip()}")
    if r.returncode != 0:
        raise Unmeasurable(f"actor '{actor}': session_login salió con {r.returncode}: {r.stderr.strip()}")
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise Unmeasurable(f"actor '{actor}': session_login no devolvió una cookie: {r.stdout[-200:]}") from exc


# --------------------------------------------------------------------------- navegador


def run_criteria(t: dict, cookies: dict, out: pathlib.Path, project_root: pathlib.Path) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise Unmeasurable("este python no tiene playwright: usa uno que lo tenga") from exc
    sys.path.insert(0, str(KIT))
    import pw

    results = []
    with sync_playwright() as p:
        browser = pw.launch(p)
        contexts: dict = {}
        try:
            for c in t["criteria"]:
                actor = c.get("actor")
                if actor not in contexts:
                    contexts[actor] = pw.user_context(browser, cookies.get(actor))
                page = contexts[actor].new_page()
                try:
                    results.append(check_one(pw, page, t, c, out, project_root))
                finally:
                    page.close()
        finally:
            browser.close()
    return results


def check_one(pw, page, t: dict, c: dict, out: pathlib.Path, project_root: pathlib.Path) -> dict:
    url = t["base_url"].rstrip("/") + "/" + c["url"].lstrip("/")
    who = c.get("actor") or "anónimo"
    res = {"id": c["id"], "actor": who, "url": c["url"], "checks": [], "shot": None}
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as exc:  # noqa: BLE001 — servidor caído o URL rota: no es «no cumple»
        raise Unmeasurable(f"{c['id']}: no pude abrir {url}: {str(exc).splitlines()[0]}") from exc
    status = resp.status if resp else None
    want = c.get("expect_status", 200)
    res["checks"].append({"what": f"HTTP {want}", "ok": status == want, "seen": f"HTTP {status}"})
    try:
        pw.wait_loader(page, (t.get("wait_loader") or []) + (c.get("wait_loader") or []))
    except TimeoutError as exc:
        res["checks"].append({"what": "carga completa", "ok": False, "seen": str(exc)})
    body = page.inner_text("body") if page.query_selector("body") else ""
    for txt in c.get("expect_text") or []:
        res["checks"].append({"what": f"se ve «{txt}»", "ok": txt in body,
                              "seen": "presente" if txt in body else "no aparece"})
    for txt in c.get("expect_absent") or []:
        res["checks"].append({"what": f"no se ve «{txt}»", "ok": txt not in body,
                              "seen": "no aparece" if txt not in body else "aparece"})
    if c.get("capture", True):
        conf = pw.pii_config(project_root, c.get("mask"), c.get("allow"))
        shot = out / "shots" / f"{c['id']}.png"
        try:
            res["masked"] = pw.capture(page, shot, conf, f"{c['id']} ({c['url']})")
            res["shot"] = f"shots/{c['id']}.png"
        except pw.PiiFound as exc:
            # Solo la muestra tapada que da la guarda: el valor real no se escribe en ningún sitio.
            res["pii"] = [{"tipo": f["tipo"], "muestra": f["muestra"]} for f in exc.found]
            res["pii_report"] = str(exc)
    res["verdict"] = verdict_of(res)
    return res


def verdict_of(res: dict) -> str:
    if res.get("pii"):
        return "blocked"
    return "done" if all(ch["ok"] for ch in res["checks"]) else "notdone"


# --------------------------------------------------------------------------- auditores


def _find_verdict(d: dict) -> dict:
    for path in (("verdict",), ("post", "verdict")):
        cur = d
        for k in path:
            cur = cur.get(k) if isinstance(cur, dict) else None
        if isinstance(cur, dict):
            return cur
        if isinstance(cur, str):
            return {"verdict": cur}
    return {}


def auditor_item(path: pathlib.Path, base: pathlib.Path) -> dict:
    """Un item «Anotaciones del auditor» con lo que el auditor dejó escrito; sin re-juzgarlo."""
    rel = os.path.relpath(path, base)
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"id": f"AUD-{path.stem}", "epic": "AUD", "title": f"Auditor sin leer: {rel}",
                "status": "blocked", "verdict": "blocked",
                "why": f"🔎 Fichero: {rel}\n👁 No se pudo leer: {exc}",
                "howto": "Vuelve a lanzar al auditor o corrige la ruta en ticket.json → auditors"}
    auditor = d.get("auditor") if isinstance(d.get("auditor"), dict) else {}
    agent = re.sub(r"[^A-Za-z0-9._-]", "-", str(d.get("agent") or auditor.get("agent") or path.parent.name))
    v = _find_verdict(d)
    verdict = v.get("verdict") if v.get("verdict") in VERDICT_STATUS else "review"
    post = d.get("post") if isinstance(d.get("post"), dict) else {}
    # impacto/1 (Pilar) deja sus cambios y lo no verificado dentro de «post»
    findings = (d.get("findings")
                or (post.get("behavior_changes") or []) + (post.get("db_changes") or []))
    lines = [f"🔎 Fichero: {rel} · esquema {d.get('schema', '—')}"]
    if v.get("global"):
        lines.append(f"Veredicto del auditor: {v['global']}")
    if v.get("overall_risk"):
        lines.append(f"Riesgo: {v['overall_risk']}")
    if v.get("why"):
        lines.append(str(v["why"]))
    for f in findings[:12]:
        if not isinstance(f, dict):
            lines.append(f"· {f}")
            continue
        title = f.get("title") or f.get("symbol") or f.get("migration") or ""
        sev = f.get("severity") or f.get("class") or ""
        lines.append(f"· [{f.get('id', '?')}] {sev} {title}"
                     f"{' — ' + str(f['file']) if f.get('file') else ''}".strip())
    if len(findings) > 12:
        lines.append(f"· … y {len(findings) - 12} más en {rel}")
    pending = d.get("unconfirmed") or post.get("unverified") or []
    for u in pending[:5]:
        text = (u.get("what") or u) if isinstance(u, dict) else u
        lines.append(f"No confirmado: {text}")
    if (d.get("autonomy_phase") or auditor.get("autonomy_phase")) == 1:
        lines.append("Auditor en fase 1: su veredicto no bloquea; lo decide el Usuario.")
    return {"id": f"AUD-{agent}", "epic": "AUD", "title": f"Anotaciones del auditor: {agent}",
            "status": VERDICT_STATUS.get(verdict, "review"), "verdict": verdict,
            "confidence": v.get("confidence"), "why": "\n".join(lines), "howto": v.get("howto", ""),
            "evidence": [{"kind": "data", "label": "fichero", "src": rel}]}


# --------------------------------------------------------------------------- informe


def criterion_item(c: dict, r: dict) -> dict:
    checks = "\n".join(f"{'✓' if ch['ok'] else '✗'} {ch['what']}: {ch['seen']}" for ch in r["checks"])
    why = f"🔎 Criterio: {c.get('goal') or c['title']}\n👁 En vivo: GET {r['url']} como {r['actor']}\n{checks}"
    if r.get("masked"):
        why += f"\nCeldas enmascaradas antes de capturar: {r['masked']}"
    howto = ""
    if r.get("pii"):
        why += "\nCaptura DESCARTADA por la guarda de datos personales."
        howto = ("La página enseña datos personales que no están en la lista blanca: enmascara la celda "
                 "(«mask» del criterio) o usa datos sintéticos. Detalle en resultados.json.")
    elif r["verdict"] != "done":
        howto = "; ".join(ch["what"] for ch in r["checks"] if not ch["ok"])
    ev = [{"kind": "img", "label": "ACTUAL", "src": r["shot"], "caption": f"{r['url']} · {r['actor']}"}] \
        if r.get("shot") else []
    return {"id": c["id"], "epic": "AC", "title": c["title"], "goal": c.get("goal") or c["title"],
            "status": VERDICT_STATUS[r["verdict"]], "verdict": r["verdict"], "why": why,
            "howto": howto, "evidence": ev}


def review_item(out: pathlib.Path) -> dict:
    """La tercera capa de la guarda: ¿alguien MIRÓ cada captura? Lo dice guarda_pii_capturas."""
    sys.path.insert(0, str(CLAUDE / "scripts"))
    import guarda_pii_capturas as gp

    shots = out / "shots"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = gp.comprobar(shots) if shots.is_dir() else 0
    done = rc == 0
    return {"id": "PII-REV", "epic": "PII", "title": "Revisión visual de las capturas antes de entregar",
            "status": "done" if done else "review", "verdict": "done" if done else "review",
            "why": "🔎 guarda_pii_capturas.py --comprobar shots/\n👁 " + (buf.getvalue().strip()[-600:] or "sin capturas"),
            "howto": "" if done else ("Abre cada PNG de shots/ y anótalo: python3 .claude/scripts/"
                                      "guarda_pii_capturas.py --registrar shots --por \"<quién>\" <png…>; "
                                      "después vuelve a correr el kit.")}


def diff_stamp(t: dict, project_root: pathlib.Path) -> dict | None:
    if not t.get("diff_base"):
        return None
    sys.path.insert(0, str(CLAUDE / "scripts"))
    try:
        import diff_hash
        base = diff_hash.merge_base(project_root, t["diff_base"])
        return {"base": t["diff_base"], "base_sha": base,
                "diff_sha256": diff_hash.diff_sha256(project_root, base)}
    except Exception as exc:  # noqa: BLE001 — sin repo el informe lo dice, no se cae
        print(f"[verify_ticket] aviso: no pude sellar el diff contra {t['diff_base']}: {exc}", file=sys.stderr)
        return {"base": t["diff_base"], "error": str(exc)}


def build_report(t: dict, results: list[dict], out: pathlib.Path, ticket_dir: pathlib.Path,
                 project_root: pathlib.Path, today: str | None = None) -> dict:
    by_id = {r["id"]: r for r in results}
    items = [criterion_item(c, by_id[c["id"]]) for c in t["criteria"] if c["id"] in by_id]
    for a in t.get("auditors") or []:
        path = (ticket_dir / a).resolve()
        # solo lo que está dentro del ticket o del proyecto llega al informe
        if not (path.is_relative_to(ticket_dir) or path.is_relative_to(project_root.resolve())):
            raise Unmeasurable(f"auditors: {a} queda fuera del ticket y del proyecto")
        items.append(auditor_item(path, out))
    items.append(review_item(out))
    pedido = [{"que": c["title"], "donde": f"dashboard.html#{c['id']}", "id": c["id"],
               "estado": "hecho" if by_id.get(c["id"], {}).get("verdict") == "done" else "falta"}
              for c in t["criteria"]]
    meta = {"project": t["ticket"], "plan_id": t["ticket"], "title": t.get("title") or t["ticket"],
            "profile": "minimo", "generated": today or dt.date.today().isoformat(), "pedido": pedido,
            "site": t["base_url"], "shots": "shots", "epics": EPICS,
            "pages": [{"code": "T", "name": "Ticket"}]}
    stamp = diff_stamp(t, project_root)
    if stamp:
        meta["diff"] = stamp
    for it in items:
        it.setdefault("page", "T")
    return {"meta": meta, "items": items}


def build_html(out: pathlib.Path) -> None:
    for argv in ([sys.executable, str(REPORT_KIT / "embed.py"), str(out)],
                 [sys.executable, str(REPORT_KIT / "build.py"), str(out), "--embed"]):
        r = subprocess.run(argv, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise Unmeasurable(f"{pathlib.Path(argv[1]).name} salió con {r.returncode}: "
                               f"{(r.stderr or r.stdout).strip()[-800:]}")


def make_pdf(out: pathlib.Path) -> pathlib.Path:
    """results.html a PDF, servido en 127.0.0.1 (nunca 0.0.0.0) solo mientras dura la impresión."""
    sys.path.insert(0, str(KIT))
    from playwright.sync_api import sync_playwright

    import pw

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # el log de cada GET no aporta nada a la salida del kit
            pass

    # se sirve una copia de results.html sola (lleva las capturas embebidas), no la carpeta entera
    serve_dir = tempfile.mkdtemp(prefix="verify-ticket-pdf-")
    shutil.copy2(out / "results.html", serve_dir)
    handler = functools.partial(Quiet, directory=serve_dir)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    pdf = out / "informe.pdf"
    try:
        with sync_playwright() as p:
            b = pw.launch(p)
            try:
                page = b.new_page()
                page.goto(f"http://127.0.0.1:{httpd.server_address[1]}/results.html", wait_until="load")
                page.emulate_media(media="print")
                page.pdf(path=str(pdf), format="A4", print_background=True,
                         margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"})
            finally:
                b.close()
    finally:
        httpd.shutdown()
        shutil.rmtree(serve_dir, ignore_errors=True)
    return pdf


# --------------------------------------------------------------------------- comando


def verify(ticket_path: pathlib.Path, django_python: str, out: pathlib.Path | None, pdf: bool,
           build: bool = True) -> int:
    t = load_ticket(ticket_path)
    ticket_dir = ticket_path.parent.resolve()
    out = (out or ticket_dir).resolve()
    sys.path.insert(0, str(CLAUDE / "scripts"))
    import guarda_pii_capturas as gp
    project_root = pathlib.Path(t["project_root"]).resolve() if t.get("project_root") \
        else gp.raiz_del_proyecto(ticket_dir)
    backend_dir = (project_root / t.get("backend_dir", ".")).resolve()

    cookies = {}
    for actor in sorted({c["actor"] for c in t["criteria"] if c.get("actor")}):
        try:
            cookies[actor] = actor_cookie(t, actor, django_python, backend_dir)
        except GuardRefused as exc:
            print(f"[verify_ticket] guard: {exc}\n[verify_ticket] no se captura nada.", file=sys.stderr)
            return 1
    results = run_criteria(t, cookies, out, project_root)
    (out / "resultados.json").write_text(json.dumps({"schema": "ticket-results/1", "ticket": t["ticket"],
                                                     "results": results}, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    report = build_report(t, results, out, ticket_dir, project_root)
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if build:
        build_html(out)
        if pdf:
            print(f"[verify_ticket] PDF: {make_pdf(out)}")
    for r in results:
        print(f"  {'✓' if r['verdict'] == 'done' else '✗'} {r['id']} · {r['verdict']} · {r['url']} ({r['actor']})")
        if r.get("pii_report"):
            print(r["pii_report"], file=sys.stderr)
    rev = next(i for i in report["items"] if i["id"] == "PII-REV")
    if rev["verdict"] != "done":
        print("[verify_ticket] falta la revisión visual de las capturas antes de entregar (PII-REV)")
    print(f"[verify_ticket] informe: {out / 'results.html'} · servir: cd {out} && python3 server.py")
    return 0 if all(r["verdict"] == "done" for r in results) else 1


# --------------------------------------------------------------------------- autoprueba


def self_test() -> int:
    import tempfile

    fails = []

    def ok(name, cond):
        print(f"  {'✓' if cond else '✗'} {name}")
        if not cond:
            fails.append(name)

    base = {"schema": SCHEMA, "ticket": "T-1", "base_url": "http://127.0.0.1:8000", "settings": "s",
            "actors": {"a": {"username": "u"}}, "criteria": [{"id": "AC-1", "title": "x", "url": "/", "actor": "a"}]}
    ok("ticket válido pasa", validate_ticket(json.loads(json.dumps(base)))["ticket"] == "T-1")
    for name, mut in (("base_url remota → no se mide", {"base_url": "https://app.example.com"}),
                      ("schema ausente → no se mide", {"schema": None}),
                      ("actor sin declarar → no se mide",
                       {"criteria": [{"id": "AC-1", "title": "x", "url": "/", "actor": "z"}]}),
                      ("id repetido → no se mide",
                       {"criteria": [{"id": "A", "title": "x", "url": "/"}, {"id": "A", "title": "y", "url": "/"}]}),
                      ("actores sin settings → no se mide", {"settings": None}),
                      ("base_url con «\\@» (Chromium iría a otro host) → no se mide",
                       {"base_url": "http://evil.com\\@127.0.0.1:8000"}),
                      ("id con ../ → no se mide",
                       {"criteria": [{"id": "../../x", "title": "x", "url": "/"}]}),
                      ("url absoluta a otro host → no se mide",
                       {"criteria": [{"id": "A", "title": "x", "url": "//evil.com/"}]})):
        t = dict(json.loads(json.dumps(base)), **mut)
        try:
            validate_ticket(t)
            ok(name, False)
        except Unmeasurable:
            ok(name, True)

    ok("verdict: un check falla → notdone",
       verdict_of({"checks": [{"ok": True}, {"ok": False}]}) == "notdone")
    ok("verdict: PII → blocked aunque todo pase", verdict_of({"checks": [{"ok": True}], "pii": [{}]}) == "blocked")

    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "roberto").mkdir()
        (d / "roberto" / "findings.json").write_text(json.dumps({
            "schema": "code-findings/1", "agent": "roberto-clean-code", "autonomy_phase": 1,
            "findings": [{"id": "ROB-001", "severity": "P1", "title": "helper duplicado", "file": "a.py"}],
            "verdict": {"global": "PASA_CON_AVISOS", "verdict": "partial", "confidence": "alta"}}))
        (d / "impacto.json").write_text(json.dumps({
            "schema": "impacto/1", "auditor": {"agent": "pilar-impacto-produccion", "autonomy_phase": 2},
            "post": {"verdict": {"verdict": "notdone", "overall_risk": "alto", "why": "🔎 … / 👁 …"},
                     "behavior_changes": [{"id": "C1", "severity": "P0", "symbol": "la ficha da 404"}],
                     "unverified": [{"what": "la cola de Celery"}]}}))
        (d / "roto.json").write_text("{no es json")
        rob = auditor_item(d / "roberto" / "findings.json", d)
        ok("Roberto: partial, con su hallazgo y el aviso de fase 1",
           rob["verdict"] == "partial" and "ROB-001" in rob["why"] and "fase 1" in rob["why"])
        pil = auditor_item(d / "impacto.json", d)
        ok("Pilar: post.verdict, riesgo, cambios y no verificado de post.*",
           pil["verdict"] == "notdone" and "alto" in pil["why"] and "C1" in pil["why"]
           and "cola de Celery" in pil["why"] and "fase 1" not in pil["why"])
        ok("auditor ilegible → blocked, no se inventa", auditor_item(d / "roto.json", d)["verdict"] == "blocked")

        t = dict(json.loads(json.dumps(base)), auditors=["roberto/findings.json", "impacto.json"])
        res = [{"id": "AC-1", "actor": "a", "url": "/", "checks": [{"what": "HTTP 200", "ok": True, "seen": "HTTP 200"}],
                "shot": None, "verdict": "done"}]
        try:
            build_report(dict(t, auditors=["/etc/hostname"]), res, d, d, d)
            ok("auditor fuera del ticket y del proyecto → no se mide", False)
        except Unmeasurable:
            ok("auditor fuera del ticket y del proyecto → no se mide", True)
        rep = build_report(t, res, d, d, d, today="2026-10-31")
        ids = [i["id"] for i in rep["items"]]
        ok("report.json: criterio + 2 auditores + revisión de capturas",
           ids == ["AC-1", "AUD-roberto-clean-code", "AUD-pilar-impacto-produccion", "PII-REV"])
        ok("meta.pedido apunta al item del dashboard y dice hecho",
           rep["meta"]["pedido"][0] == {"que": "x", "donde": "dashboard.html#AC-1", "id": "AC-1", "estado": "hecho"})
        ok("perfil minimo y estados del esquema",
           rep["meta"]["profile"] == "minimo"
           and all(i["status"] in {"backlog", "doing", "review", "done", "blocked"} for i in rep["items"]))
        (d / "shots").mkdir()
        (d / "shots" / "AC-1.png").write_bytes(b"\x89PNG fake")
        ok("captura sin mirar → PII-REV en review", review_item(d)["verdict"] == "review")
    print(f"\n{'OK' if not fails else 'FALLA'}: {len(fails)} fallo(s)")
    return 1 if fails else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ticket", nargs="?", help="ruta a ticket.json")
    ap.add_argument("--django-python", default=sys.executable,
                    help="python con el Django del proyecto (por defecto, este)")
    ap.add_argument("--out", help="carpeta del informe (por defecto, la de ticket.json)")
    ap.add_argument("--pdf", action="store_true", help="además, informe.pdf de results.html")
    ap.add_argument("--no-build", action="store_true", help="solo resultados.json y report.json")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.ticket:
        ap.error("falta ticket.json")
    try:
        return verify(pathlib.Path(a.ticket), a.django_python, pathlib.Path(a.out) if a.out else None,
                      a.pdf, build=not a.no_build)
    except Unmeasurable as exc:
        print(f"[verify_ticket] NO MEDIDO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
