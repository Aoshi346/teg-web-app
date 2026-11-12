#!/usr/bin/env python3
"""gen_informe.py — `informe.html`: el informe de UN issue, página del set del kit (perfil «issue»).

QUÉ ES (AN-6, AN-D1; sub-ola 3.09). Un solo informe por issue, siempre igual y en ruta fija
(`.docs/plans/<fecha>-<issue>/informe.html`), en vez de un `build_informe.py` a mano por issue (22
en 5 proyectos, medido en la revisión). La estructura viene de `evo-html-report` de EvoPreven
(contexto, mapa, reproducción, hallazgos, plan, verificación, capturas en base64, imprimir); los
tokens, del bloque SHARED del kit. El Usuario decidió el 18-10 que sea una página más del set.

El agente escribe SOLO JSON (`<plan>/informe.json`, `informe/1`) y esto lo pinta. Los apartados 7
y 8 no los escribe nadie a mano: los pinta `scripts/render_impacto.py` desde `impacto/impacto.json`
(Pilar) y `codigo/findings.json` (Roberto), con sus marcadores, para que `gate_impacto.py` los mida.

Las diez secciones, cada una con `data-seccion="N"` (las comprueba `scripts/issue_close.py`):

    0 Contexto          context: {problem, trigger, expected} o texto         obligatoria
    1 Alcance pedido    scope: {original_text (verbatim), repos[{name, what, why}], planned_files[]}  obligatoria
    2 Mapa              map: {entries[{ref, what}], flow}
    3 Reproducción      reproduction: {steps[], measured, verified}
    4 Hallazgos         findings[{id, title, state: pendiente|falta|resuelto, ref, detail}]
    5 Plan              plan[{phase, what, files[]}]
    6 Verificación      verification: {commands[{cmd, result}], notes}       obligatoria
    7 Impacto en producción   ← render_impacto.py (impacto/impacto.json)
    8 Auditoría de código     ← render_impacto.py (codigo/findings.json); `without_code: "<motivo>"` si no aplica
    9 Capturas          shots[{file, title, caption}] (rutas relativas al plan; se embeben en base64)

Una sección sin datos no sale vacía: con `empty: {"<clave>": "<motivo>"}` lleva `data-vacio` y el
motivo; sin motivo sale marcada `data-falta` y el cierre la rechaza (como «se olvidó», no «no hay»).
La página graba `data-json-sha` (sha256 de informe.json): un informe pintado de otros datos es viejo.

Uso:   python3 gen_informe.py <plan>          (lo llama build.py si existe <plan>/informe.json)
Salida: 0 escrito · 0 sin informe.json (página del perfil: la pone gen_placeholders) · 2 JSON ilegible.
"""
from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent.parent / "scripts"
sys.path.insert(0, str(HERE))
import embed  # noqa: E402

SCHEMA = "informe/1"
# (número, id, título, clave en informe.json, obligatoria)
SECTIONS = (
    (0, "inf-contexto", "Contexto", "context", True),
    (1, "inf-alcance", "Alcance pedido", "scope", True),
    (2, "inf-mapa", "Mapa y puntos de entrada", "map", False),
    (3, "inf-reproduccion", "Reproducción", "reproduction", False),
    (4, "inf-hallazgos", "Hallazgos", "findings", False),
    (5, "inf-plan", "Plan", "plan", False),
    (6, "inf-verificacion", "Verificación", "verification", True),
    (7, "inf-impacto", "Impacto en producción", "impact", True),
    (8, "inf-codigo", "Auditoría de código", "code", True),
    (9, "inf-capturas", "Capturas", "shots", False),
)
# Las que no pueden ir vacías ni con motivo (7 y 8 los exige además gate_impacto.py). La usa issue_close.py.
REQUIRED = frozenset(num for num, _sid, _t, key, req in SECTIONS if req and key not in ("impact", "code"))
STATE = {"pendiente": ("bad", "pendiente"), "falta": ("warn", "falta"), "resuelto": ("ok", "resuelto")}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
        ".gif": "image/gif", ".svg": "image/svg+xml"}


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""), quote=True)


def text(x) -> str:
    """Texto plano a párrafos; `código` entre comillas invertidas sale como <code>."""
    if x is None or x == "":
        return ""
    if isinstance(x, list):
        return "<ul>" + "".join(f"<li>{inline(i)}</li>" for i in x) + "</ul>"
    return "".join(f"<p>{inline(p)}</p>" for p in re.split(r"\n\s*\n", str(x).strip()) if p.strip())


def inline(x) -> str:
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(x)).replace("\n", "<br>")


def shared_block() -> str:
    """El CSS común, copiado LITERAL de index.template.html (regla nº 5 del report-kit)."""
    t = (HERE / "index.template.html").read_text(encoding="utf-8")
    m = re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", t, re.S)
    return m.group(0) if m else ""


def _context(c) -> str:
    if isinstance(c, dict):
        rows = [("El problema", c.get("problem")), ("Qué lo provocó", c.get("trigger")),
                ("Qué se espera", c.get("expected"))]
        return "".join(f"<h3>{k}</h3>{text(v)}" for k, v in rows if v)
    return text(c)


def _scope(s) -> str:
    if not isinstance(s, dict):
        return text(s)
    out = ""
    if s.get("original_text"):
        out += ('<h3>Lo que se pidió, literal</h3><blockquote class="literal">'
                f'{text(s["original_text"])}</blockquote>')
    repos = s.get("repos") or []
    if repos:
        out += _table(["Repo", "Qué cambia", "Por qué"],
                      [[f"<code>{esc(r.get('name'))}</code>", inline(r.get("what")), inline(r.get("why"))]
                       for r in repos])
    files = s.get("planned_files") or []
    if files:
        out += "<h3>Ficheros previstos</h3><ul class='ficheros'>" + "".join(
            f"<li><code>{esc(f)}</code></li>" for f in files) + "</ul>"
    return out


def _map(m) -> str:
    if not isinstance(m, dict):
        return text(m)
    out = ""
    entries = m.get("entries") or []
    if entries:
        out += _table(["Dónde", "Qué hace"], [[f"<code>{esc(e.get('ref'))}</code>", inline(e.get("what"))]
                                              for e in entries])
    if m.get("flow"):
        out += f'<p class="flujo"><code>{esc(m["flow"])}</code></p>'
    return out


def _reproduction(r) -> str:
    if not isinstance(r, dict):
        return text(r)
    out = ""
    if r.get("steps"):
        out += "<ol>" + "".join(f"<li>{inline(s)}</li>" for s in r["steps"]) + "</ol>"
    if r.get("measured"):
        out += f"<h3>Qué se midió</h3>{text(r['measured'])}"
    if r.get("verified") is True:
        out += '<p class="nota ok">✓ Reproducido</p>'
    elif r.get("verified") is False:
        out += '<p class="nota warn">No se pudo reproducir: lo de arriba es la lectura del código.</p>'
    return out


def _findings(items) -> str:
    out = ""
    for f in items or []:
        tone, label = STATE.get(str(f.get("state", "")).lower(), ("warn", f.get("state") or "sin estado"))
        ref = f'<p class="ref"><code>{esc(f["ref"])}</code></p>' if f.get("ref") else ""
        out += (f'<div class="hallazgo {tone}"><p class="cab"><b>{esc(f.get("id", ""))}</b> '
                f'{esc(f.get("title", ""))} <span class="tag {tone}">{esc(label)}</span></p>'
                f'{ref}{text(f.get("detail"))}</div>')
    return out


def _plan(items) -> str:
    if not isinstance(items, list):
        return text(items)
    out = ""
    for i, p in enumerate(items, 1):
        files = " ".join(f"<code>{esc(x)}</code>" for x in p.get("files") or [])
        out += (f'<div class="fase"><p class="cab"><b>{i} · {esc(p.get("phase", ""))}</b></p>'
                f'{text(p.get("what"))}' + (f'<p class="ref">{files}</p>' if files else "") + "</div>")
    return out


def _verification(v) -> str:
    if not isinstance(v, dict):
        return text(v)
    out = ""
    cmds = v.get("commands") or []
    if cmds:
        out += _table(["Comando", "Resultado"], [[f"<code>{esc(c.get('cmd'))}</code>", inline(c.get("result"))]
                                                 for c in cmds])
    return out + text(v.get("notes"))


def _shots(plan: pathlib.Path, shots) -> tuple[str, list[str]]:
    out, warns = "", []
    for s in shots or []:
        path = (plan / str(s.get("file", ""))).resolve()
        mime = MIME.get(path.suffix.lower())
        if not path.is_relative_to(plan.resolve()) or not path.is_file() or not mime:
            warns.append(f"captura no embebida (no está en el plan o no es imagen): {s.get('file')}")
            continue
        uri = embed.make_embed(str(path))
        if not uri:
            warns.append(f"captura no embebida (no se pudo leer): {s.get('file')}")
            continue
        out += (f'<figure><figcaption><b>{esc(s.get("title", path.name))}</b></figcaption>'
                f'<img alt="{esc(s.get("title", path.name))}" src="{uri}">'
                f'<p class="pie">{esc(s.get("caption", ""))}</p></figure>')
    return out, warns


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="envolvente-tabla"><table class="tabla"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _audit_sections(plan: pathlib.Path, data: dict) -> tuple[str, str, list[str]]:
    """Los apartados 7 y 8, pintados por render_impacto.py si hay JSON de Pilar y de Roberto."""
    warns: list[str] = []
    without_code = data.get("without_code")
    try:
        sys.path.insert(0, str(SCRIPTS))
        import render_impacto  # noqa: PLC0415 — solo existe donde viajan Pilar y Roberto
    except ImportError:
        msg = "este proyecto no tiene scripts/render_impacto.py: el apartado no se puede pintar"
        return "", "", [msg]
    imp_ok = (plan / "impacto" / "impacto.json").is_file()
    code_ok = (plan / "codigo" / "findings.json").is_file()
    if not imp_ok:
        return "", "", ["sin impacto/impacto.json: lanza a Pilar (PRE y POST) antes de cerrar"]
    try:
        impact, code = render_impacto.fragments(plan, with_code=code_ok)
    except render_impacto.RenderError as exc:
        return "", "", [str(exc)]
    if not code_ok and not without_code:
        warns.append("sin codigo/findings.json: lanza a Roberto, o declara without_code con el motivo")
    return impact, code or "", warns


def section(num: int, sid: str, title: str, inner: str, required: bool, reason: str | None) -> str:
    attrs = f'id="{sid}" class="inf" data-seccion="{num}"'
    if not inner.strip():
        if reason and not required:
            attrs += f' data-vacio="{esc(reason)}"'
            inner = f'<p class="vacio">{esc(reason)}</p>'
        else:
            attrs += ' data-falta="si"'
            why = "obligatoria: no puede ir vacía" if required else "sin datos ni motivo en informe.json"
            inner = f'<p class="falta">Falta — {why}.</p>'
    return f'<section {attrs}><h2><span class="num">{num}</span> {esc(title)}</h2>{inner}</section>'


CSS = """
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 var(--sans)}
.envoltura{max-width:1080px;margin:0 auto;padding:28px 22px 60px}
.cabecera{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap}
.imprimir{font:600 13px/1 var(--sans);border:1px solid var(--line);background:var(--card);color:var(--ink);
  border-radius:var(--radius-sm);padding:9px 14px;cursor:pointer}
.indice{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 0;padding:0;list-style:none}
.indice a{display:inline-block;font:12.5px/1 var(--sans);color:var(--navy);text-decoration:none;
  border:1px solid var(--line);border-radius:var(--radius-pill);padding:6px 10px;background:var(--card)}
.inf{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:20px 24px;margin:22px 0 0}
.inf h2{margin:0 0 12px;font-size:20px;color:var(--navy);display:flex;align-items:center;gap:10px}
.inf h2 .num{font:700 13px/1 var(--mono);color:#fff;background:var(--accent);border-radius:var(--radius-pill);padding:5px 9px}
.inf h3{font-size:12.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--accent);margin:16px 0 6px}
.inf code{font:12.5px/1.5 var(--mono);background:#efece4;padding:1px 5px;border-radius:5px;overflow-wrap:anywhere}
.literal{margin:0;border-left:3px solid var(--accent);padding:4px 0 4px 14px;color:var(--ink)}
.ficheros{margin:0;padding:0 0 0 18px}
.tabla{width:100%;border-collapse:collapse;margin:8px 0 0;font-size:13.5px}
.tabla th{text-align:left;font-size:11px;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);padding:6px 10px 6px 0}
.tabla td{border-bottom:1px solid var(--line);padding:8px 10px 8px 0;vertical-align:top}
.envolvente-tabla{overflow-x:auto}
.hallazgo,.fase{border:1px solid var(--line);border-left:4px solid var(--line);border-radius:var(--radius-sm);padding:10px 14px;margin:10px 0 0}
.hallazgo.bad{border-left-color:#b42318}.hallazgo.warn{border-left-color:#b45309}.hallazgo.ok{border-left-color:var(--green)}
.cab{margin:0 0 6px}.ref{margin:0 0 6px}
.tag{font:600 11px/1 var(--sans);color:#fff;padding:3px 8px;border-radius:var(--radius-pill);margin-left:6px}
.tag.bad{background:#b42318}.tag.warn{background:#b45309}.tag.ok{background:var(--green)}
.nota{padding:8px 12px;border-radius:var(--radius-sm);font-size:13.5px}
.nota.ok{background:#e9f5ee;color:#14532d}.nota.warn{background:#fdf3e3;color:#78350f}
.vacio{color:var(--muted);font-style:italic;margin:0}
.falta{color:#b42318;font-weight:600;margin:0}
.inf .imp>h2{display:none}
.pendiente{color:#78350f;background:#fdf3e3;border-radius:var(--radius-sm);padding:8px 12px;margin:8px 0 0}
figure{margin:14px 0 0}figure img{max-width:100%;border:1px solid var(--line);border-radius:var(--radius-sm)}
.pie{color:var(--muted);font-size:13px;margin:4px 0 0}
@media (max-width:620px){.envoltura{padding:20px 14px 48px}.inf{padding:16px 14px}.tabla{min-width:460px}}
@media print{nav,.topnav,.imprimir,.indice{display:none!important}body{background:#fff}
  .inf{break-inside:auto;border:none;padding:0;margin:18px 0 0}tr,figure,.hallazgo{break-inside:avoid}}
"""


def build(plan: pathlib.Path) -> tuple[pathlib.Path | None, list[str]]:
    src = plan / "informe.json"
    if not src.is_file():
        return None, []  # la pestaña del perfil la pone gen_placeholders con su receta
    raw = src.read_bytes()
    data = json.loads(raw)
    if data.get("schema") != SCHEMA:
        raise ValueError(f"{src}: schema {data.get('schema')!r}, se esperaba {SCHEMA!r}")
    json_sha = hashlib.sha256(raw).hexdigest()
    empty = data.get("empty") or {}
    impact, code, warns = _audit_sections(plan, data)
    shots, shot_warns = _shots(plan, data.get("shots"))
    warns += shot_warns
    body = {
        "context": _context(data.get("context")), "scope": _scope(data.get("scope")),
        "map": _map(data.get("map")), "reproduction": _reproduction(data.get("reproduction")),
        "findings": _findings(data.get("findings")), "plan": _plan(data.get("plan")),
        "verification": _verification(data.get("verification")), "shots": shots,
    }
    parts = []
    for num, sid, title, key, required in SECTIONS:
        if key == "impact":
            inner = impact or ('<p class="pendiente">Pendiente: Pilar POST → '
                               '<code>render_impacto.py &lt;plan&gt; --inyectar informe.html</code>.</p>')
            parts.append(f'<section id="{sid}" class="inf" data-seccion="{num}">'
                         f'<h2><span class="num">{num}</span> {esc(title)}</h2>{inner}</section>')
        elif key == "code":
            if code:
                inner, extra = code, ""
            elif data.get("without_code"):
                inner = f'<p class="vacio">No aplica: {esc(data["without_code"])}</p>'
                extra = f' data-vacio="{esc(data["without_code"])}"'
            else:
                inner = ('<p class="pendiente">Pendiente: Roberto sobre el diff → '
                         '<code>render_impacto.py &lt;plan&gt; --inyectar informe.html</code>.</p>')
                extra = ""
            parts.append(f'<section id="{sid}" class="inf" data-seccion="{num}"{extra}>'
                         f'<h2><span class="num">{num}</span> {esc(title)}</h2>{inner}</section>')
        else:
            parts.append(section(num, sid, title, body[key], required, empty.get(key)))
    index = "".join(f'<li><a href="#{sid}">{num} · {esc(t)}</a></li>' for num, sid, t, _k, _r in SECTIONS)
    issue = esc(data.get("issue", ""))
    title = esc(data.get("title", ""))
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Informe del issue {issue}: contexto, alcance, hallazgos, verificación, impacto en producción y auditoría de código.">
<link rel="icon" href="data:,">
<title>{issue} · {title}</title>
<style>
{shared_block()}
{CSS}
</style></head>
<body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<main class="envoltura" data-schema="{SCHEMA}" data-json-sha="{json_sha}" data-issue="{issue}">
  <div class="cabecera">
    <div><p class="eyebrow">Informe del issue · {esc(data.get("date", ""))}</p>
      <h1>{issue} — {title}</h1></div>
    <button class="imprimir" type="button" onclick="window.print()">Imprimir / guardar PDF</button>
  </div>
  <ul class="indice">{index}</ul>
  {"".join(parts)}
</main>
</body></html>
"""
    out = plan / "informe.html"
    out.write_text(doc, encoding="utf-8")
    return out, warns


def main(argv: list[str]) -> int:
    plan = pathlib.Path(argv[1] if len(argv) > 1 else ".").resolve()
    try:
        out, warns = build(plan)
    except (ValueError, OSError) as exc:
        print(f"ERROR gen_informe: {exc}", file=sys.stderr)
        return 2
    if out is None:
        print(f"gen_informe: {plan}/informe.json no existe; la pestaña la pone el placeholder")
        return 0
    print(f"Escrito {out}")
    for w in warns:
        print(f"  aviso: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
