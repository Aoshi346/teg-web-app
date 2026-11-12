#!/usr/bin/env python3
"""gen_core.py — genera .docs/core/index.html, el punto de entrada único a la doc VIVA.

Lee el manifiesto `.docs/core/core.json` (QUÉ documentos forman el core y quién los
genera) y resuelve contra el DISCO y contra GIT el estado real de cada uno: si existe,
de cuándo es, de dónde sale esa fecha, y si el código cambió después. Inyecta el JSON
en `.claude/templates/core/index.template.html` (placeholder EXACTO
`const DB = /*__DATA__*/null;`, mismo patrón que gen_docs.py y report_kit/build.py).

El manifiesto declara la ESTRUCTURA; las FECHAS nunca se escriben a mano — se descubren.
Por eso el índice no puede mentir: un documento sin fecha sale marcado como tal.

Uso:
  python3 .claude/scripts/gen_core.py                      genera .docs/core/index.html
  python3 .claude/scripts/gen_core.py --init               crea .docs/core/ desde las plantillas
  python3 .claude/scripts/gen_core.py --check              exit 1 si el índice está desfasado
  python3 .claude/scripts/gen_core.py --promote <id> <src> promueve un doc generado al core
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TPL_DIR = ROOT / ".claude" / "templates" / "core"
TEMPLATE = TPL_DIR / "index.template.html"
CORE = ROOT / ".docs" / "core"
MANIFEST = CORE / "core.json"
OUT = CORE / "index.html"
PLACEHOLDER = "/*__DATA__*/null"
REGEN = "python3 .claude/scripts/gen_core.py"

TODAY = datetime.date.today()
DATE_RX = re.compile(r"(\d{4}-\d{2}-\d{2})")
# Marcador que gen_core.py estampa al promover — es lo que hace "declarada" a una fecha.
META_RX = re.compile(r"core-meta:\s*(.*?)-->", re.S)

DEFAULT_LAYERS = [
    {"id": "overview", "title": "1 · Overview", "question": "¿Qué es este sistema y qué resuelve?"},
    {"id": "arquitectura", "title": "2 · Arquitectura y estructura", "question": "¿De qué piezas está hecho?"},
    {"id": "datos", "title": "3 · Modelo de datos", "question": "¿Qué se guarda y cómo se relaciona?"},
    {"id": "ux", "title": "4 · UX y flujos", "question": "¿Cómo lo usa una persona?"},
    {"id": "decisiones", "title": "5 · Decisiones tomadas", "question": "¿Por qué está hecho así?"},
]


# ═══════════════ helpers ═══════════════

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def git(*args) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def git_last_date(paths) -> str:
    """Fecha (YYYY-MM-DD) del último commit que tocó esos pathspecs. '' si no hay."""
    paths = [p for p in paths if p]
    if not paths:
        return ""
    return git("log", "-1", "--format=%cs", "--", *paths)


def mtime_date(path: Path) -> str:
    try:
        return datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()
    except OSError:
        return ""


def newest_mtime_date(dirs) -> str:
    """Fecha del fichero más reciente bajo esos directorios (fallback sin git)."""
    newest = 0.0
    for d in dirs:
        p = ROOT / d
        if not p.exists():
            continue
        if p.is_file():
            newest = max(newest, p.stat().st_mtime)
            continue
        for f in p.rglob("*"):
            if f.is_file() and not any(part in {".git", "node_modules", "__pycache__", "dist", "build"}
                                       for part in f.parts):
                newest = max(newest, f.stat().st_mtime)
    return datetime.date.fromtimestamp(newest).isoformat() if newest else ""


def declared_meta(path: Path) -> dict:
    """Fecha/sha que el documento declara DE SÍ MISMO.

    HTML: marcador `<!-- core-meta: date=YYYY-MM-DD sha=abc1234 via=/visual-map -->`.
    Markdown: frontmatter `reviewed: YYYY-MM-DD` (+ `reviewed_by:`).
    """
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return {}
    m = META_RX.search(head)
    if m:
        kv = dict(re.findall(r"(\w+)\s*=\s*([^\s]+)", m.group(1)))
        if DATE_RX.fullmatch(kv.get("date", "")):
            return {"date": kv["date"], "sha": kv.get("sha", ""), "by": kv.get("by", "")}
    fm = re.match(r"^---\n(.*?)\n---", head, re.S)
    if fm:
        rv = re.search(r"^reviewed:\s*(\S+)\s*$", fm.group(1), re.M)
        if rv and DATE_RX.fullmatch(rv.group(1)):
            by = re.search(r"^reviewed_by:\s*(.+?)\s*$", fm.group(1), re.M)
            return {"date": rv.group(1), "sha": "", "by": (by.group(1) if by else "")}
    return {}


def last_plan() -> dict:
    """El plan más reciente de .docs/plans/<YYYY-MM-DD-slug>/ — dispara la revisión de lo escrito."""
    plans = []
    d = ROOT / ".docs" / "plans"
    if d.is_dir():
        for p in d.iterdir():
            m = re.match(r"^(\d{4}-\d{2}-\d{2})-", p.name)
            if p.is_dir() and m:
                plans.append({"id": p.name, "date": m.group(1)})
    plans.sort(key=lambda x: x["date"])
    return plans[-1] if plans else {}


# ═══════════════ resolución de un documento ═══════════════

def resolve_adrs(cfg: dict, doc: dict) -> dict:
    """La capa 5 no se declara ADR por ADR: se escanea el directorio."""
    adr_dir = (CORE / doc.get("file", "../adr")).resolve()
    entries, dates = [], []
    if adr_dir.is_dir():
        for f in sorted(adr_dir.glob("*.md")):
            if f.stem.lower() in {"readme", "index"}:
                continue
            text = read(f)[:2000]
            h1 = re.search(r"^#\s+(.+?)\s*$", text, re.M)
            # La plantilla de ADR pone el estado en una fila de tabla: «| **Estado** | Aceptado |».
            stm = (re.search(r"^\|\s*\**(?:Estado|Status)\**\s*\|\s*(.+?)\s*\|\s*$", text, re.M)
                   or re.search(r"^\**\s*(?:Estado|Status)\s*:?\**\s*:?\s*(.+?)\s*$", text, re.M))
            num = re.match(r"^(\d{3,4})", f.stem)
            found = DATE_RX.search(text)
            if found:
                dates.append(found.group(1))
            entries.append({
                "num": num.group(1) if num else "—",
                "title": re.sub(r"^ADR[- ]?\d+\s*[—–:-]\s*", "", h1.group(1)).strip() if h1 else f.stem,
                "status": re.sub(r"[*`]", "", stm.group(1))[:28] if stm else "",
                "href": _rel(adr_dir / f.name),
            })
    doc["adrs"] = entries
    doc["exists"] = bool(entries)
    doc["href"] = _rel(adr_dir / "README.md") if (adr_dir / "README.md").exists() else ""
    if entries:
        doc["state"] = "al-dia"
        doc["date"] = max(dates) if dates else git_last_date([_repo_rel(adr_dir)])
        doc["date_source"] = "declarada" if dates else ("git" if doc["date"] else "")
        doc["why"] = (f"{len(entries)} decisiones registradas, la última del {doc['date'] or '—'}. Un ADR "
                      f"no caduca: es el acta de una decisión. Si deja de valer, se escribe uno nuevo "
                      f"que lo reemplaza — nunca se edita el viejo.")
    else:
        doc["state"] = "vacio"
        doc["date"] = ""
        doc["date_source"] = ""
        doc["why"] = ("Todavía no hay ninguna decisión registrada. No es un fallo si el proyecto no "
                      "ha tomado decisiones caras de revertir — sí lo es si las tomó y no se anotaron.")
        doc["fix"] = doc.get("via", "cp .claude/templates/adr-template.md .docs/adr/0001-<slug>.md")
    return doc


def _rel(p: Path) -> str:
    """Ruta relativa desde .docs/core/index.html hacia el fichero."""
    try:
        return os.path.relpath(p, CORE).replace("\\", "/")
    except ValueError:
        return str(p)


def _repo_rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def resolve_doc(cfg: dict, doc: dict, code_date: str, plan: dict) -> dict:
    doc = dict(doc)
    doc.setdefault("optional", False)
    doc.setdefault("origin", "generado")
    review_days = int(cfg.get("review_days", 90))

    if doc.get("kind") == "adr":
        return resolve_adrs(cfg, doc)

    target = (CORE / doc["file"]).resolve()
    doc["exists"] = target.is_file()
    doc["href"] = _rel(target)
    doc["promoted"] = CORE.resolve() in target.parents

    if not doc["exists"]:
        doc["state"] = "opcional-falta" if doc["optional"] else "falta"
        doc["date"] = ""
        doc["date_source"] = ""
        doc["why"] = ("Declarado en core.json pero el fichero no existe todavía."
                      if not doc["optional"] else
                      "Documento opcional que este proyecto aún no usa.")
        doc["fix"] = fix_for(doc)
        return doc

    # ── fecha: declarada > git > mtime ──
    # Para lo ESCRITO a mano solo vale la declarada: git y mtime dicen cuándo cambiaron los bytes,
    # no cuándo un humano confirmó que el contenido sigue siendo cierto (un typo resetearía ambas).
    meta = declared_meta(target)
    if meta.get("date"):
        doc["date"], doc["date_source"], doc["sha"] = meta["date"], "declarada", meta.get("sha", "")
    elif doc["origin"] == "escrito":
        doc["date"], doc["date_source"] = "", ""
    else:
        gd = git_last_date([_repo_rel(target)])
        # Un documento regenerado y aún sin commitear es de HOY: sus bytes son de hoy. Sin esto el
        # índice que se escribe antes del commit dice «obsoleto» y, tras el commit, el mismo disco
        # da «al día» — así que `--check` fallaba justo después de regenerar (sub-ola 1.07).
        if git("status", "--porcelain", "--", _repo_rel(target)):
            gd = TODAY.isoformat()
        if gd:
            doc["date"], doc["date_source"] = gd, "git"
        else:
            md = mtime_date(target)
            doc["date"], doc["date_source"] = md, ("mtime" if md else "")

    # ── código relevante para ESTE documento ──
    doc_code_date = code_date
    if doc.get("watch"):
        doc_code_date = git_last_date(doc["watch"]) or code_date

    # ── estado ──
    if not doc["date"]:
        doc["state"] = "sin-fecha"
        doc["why"] = ("El documento existe pero no declara cuándo se revisó por última vez "
                      "(falta `reviewed:` en el frontmatter). Nadie ha firmado que siga siendo "
                      "cierto, así que no se puede confiar en él."
                      if doc["origin"] == "escrito" else
                      "El documento existe pero no dice de cuándo es: sin marcador core-meta y sin "
                      "rastro en git. No se sabe a qué versión del sistema corresponde.")
    elif doc["origin"] == "generado":
        if doc_code_date and doc_code_date > doc["date"]:
            doc["state"] = "obsoleto"
            doc["why"] = (f"Se generó el {doc['date']} y el código cambió después "
                          f"({doc_code_date}). Regenéralo antes de creértelo.")
        else:
            doc["state"] = "al-dia"
            doc["why"] = f"Generado el {doc['date']}; el código no ha cambiado desde entonces."
    else:
        age = (TODAY - datetime.date.fromisoformat(doc["date"])).days
        plan_after = plan.get("date", "") > doc["date"]
        if age > review_days:
            doc["state"] = "por-revisar"
            doc["why"] = (f"Escrito a mano y revisado por última vez hace {age} días "
                          f"(el umbral de este proyecto son {review_days}).")
        elif plan_after:
            doc["state"] = "por-revisar"
            doc["why"] = (f"Se cerró el plan {plan['id']} el {plan['date']}, después de la última "
                          f"revisión ({doc['date']}). Toca confirmar que sigue siendo cierto.")
        else:
            doc["state"] = "al-dia"
            doc["why"] = f"Revisado el {doc['date']}."

    if doc["exists"] and not doc["promoted"]:
        doc["why"] += (" Además vive dentro de un plan, que es una foto de un momento: promuévelo a "
                       ".docs/core/ para que deje de moverse bajo tus pies."
                       if "/plans/" in doc["href"] else
                       " Vive fuera de .docs/core/, así que lo mantiene otro proceso: si ese proceso "
                       "se para, el core se entera tarde.")
    if doc["state"] != "al-dia":
        doc["fix"] = fix_for(doc)
    return doc


def fix_for(doc: dict) -> str:
    """El comando exacto y copiable para llevar este documento a 'al día'."""
    if doc["origin"] == "generado":
        return (f"{doc.get('via', '/visual-map')}   # luego: {REGEN} "
                f"--promote {doc['id']} <ruta-del-html-generado>")
    tpl = f".claude/templates/core/{Path(doc['file']).name}"
    if not doc.get("exists"):
        return f"cp {tpl} .docs/core/{Path(doc['file']).name} && $EDITOR .docs/core/{Path(doc['file']).name}"
    return (f"$EDITOR .docs/core/{Path(doc['file']).name}   # revisa el contenido y pon "
            f"reviewed: {TODAY.isoformat()} en el frontmatter")


# ═══════════════ ensamblado ═══════════════

def build_db(cfg: dict) -> dict:
    code_dirs = cfg.get("code_dirs") or []
    existing = [d for d in code_dirs if (ROOT / d).exists()]
    code_date = git_last_date(code_dirs)
    code_source = "git"
    if not code_date:
        code_date = newest_mtime_date(existing)
        code_source = "mtime" if code_date else ""
    # El core documenta el estado COMMITEADO del sistema: el trabajo sin commitear todavía no es
    # el sistema. La suciedad del working tree se informa, pero no marca obsoleto todo el core.
    dirty = bool(git("status", "--porcelain", "--", *code_dirs)) if existing else False

    plan = last_plan()
    docs = [resolve_doc(cfg, d, code_date, plan) for d in cfg.get("docs", [])]
    counts: dict = {}
    for d in docs:
        counts[d["state"]] = counts.get(d["state"], 0) + 1

    return {
        "meta": {
            "project": cfg.get("project", "proyecto"),
            "fecha": TODAY.isoformat(),
            "sha": git("rev-parse", "--short", "HEAD") or "nogit",
            "regen": REGEN,
            "review_days": cfg.get("review_days", 90),
            "code_dirs": code_dirs or ["(sin code_dirs en core.json)"],
            "code_date": code_date,
            "code_source": code_source,
            "code_dirty": dirty,
            "last_plan": plan,
        },
        "layers": cfg.get("layers") or DEFAULT_LAYERS,
        "docs": docs,
        "counts": counts,
    }


def render(db: dict) -> str:
    tpl = read(TEMPLATE)
    payload = json.dumps(db, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace(PLACEHOLDER, payload)
    if html == tpl:
        sys.exit(f"ERROR: {TEMPLATE.name} no tiene el placeholder {PLACEHOLDER}")
    return html


def normalize(s: str) -> str:
    """Para --check: ignorar lo que cambia cada día sin que cambie el contenido real."""
    for key in ("fecha", "sha", "code_date"):
        s = re.sub(rf'"{key}":\s*"[^"]*"', f'"{key}":""', s)
    # `code_dirty` es estado del WORKING TREE, no del core: build_db ya lo dice ("se informa, pero
    # no marca obsoleto todo el core"). Si contara para --check, cualquier edición o commit en
    # `code_dirs` —aunque no toque un solo documento del core— dejaría el índice en rojo, y el gate
    # se volvería ruido que se aprende a ignorar.
    s = re.sub(r'"code_dirty":\s*(?:true|false)', '"code_dirty":null', s)
    # El comando de arreglo lleva `reviewed: <hoy>`: cambia cada día sin que cambie nada, y hacía
    # que `--check` saliera rojo al día siguiente de regenerar (visto por el verificador de la 1.07).
    s = re.sub(r"reviewed: \d{4}-\d{2}-\d{2}", "reviewed: <hoy>", s)
    # Y la edad («hace 104 días»): pasado el umbral cambiaría cada día. El cambio de MOTIVO (de «se
    # cerró un plan» a «hace N días») sí cuenta, y con él basta regenerar una vez.
    s = re.sub(r"hace \d+ días", "hace N días", s)
    return s


# ═══════════════ acciones ═══════════════

def cmd_init():
    CORE.mkdir(parents=True, exist_ok=True)
    for name in ("core.json", "overview.md", "ux.md", "design-system.md"):
        src, dst = TPL_DIR / name, CORE / name
        if dst.exists():
            print(f"  = {dst.relative_to(ROOT)} (ya existe, no se toca)")
        else:
            shutil.copy2(src, dst)
            print(f"  + {dst.relative_to(ROOT)}")
    print(f"Core inicializado en {CORE.relative_to(ROOT)} — personaliza core.json y overview.md.")


def cmd_promote(doc_id: str, src: str, date: str = ""):
    """Copia un documento generado al core y lo SELLA con su fecha y su sha.

    Convierte la foto de un plan en la versión viva del core. La fecha del sello es la del
    ORIGEN (su marcador, o el último commit que lo tocó), nunca la de hoy: promover mueve un
    documento, no lo rejuvenece. Sellar con hoy un mapa de hace tres meses sería la primera
    mentira del índice. `--date` la fuerza solo si sabes que el contenido se acaba de regenerar.
    """
    cfg = json.loads(read(MANIFEST))
    doc = next((d for d in cfg.get("docs", []) if d.get("id") == doc_id), None)
    if not doc:
        sys.exit(f"ERROR: '{doc_id}' no está declarado en {MANIFEST.relative_to(ROOT)}")
    source = Path(src) if Path(src).is_absolute() else ROOT / src
    if not source.is_file():
        sys.exit(f"ERROR: no existe {source}")

    stamp = date or declared_meta(source).get("date") or git_last_date([_repo_rel(source)]) \
        or mtime_date(source) or TODAY.isoformat()
    if not DATE_RX.fullmatch(stamp):
        sys.exit(f"ERROR: fecha inválida '{stamp}' (formato YYYY-MM-DD)")
    sha = git("rev-parse", "--short", "HEAD") or "nogit"
    body = f'core-meta: date={stamp} sha={sha} via={doc.get("via", "?")} '

    declared = (CORE / doc["file"]).resolve()
    # Dentro del core a CUALQUIER profundidad (p. ej. `producto/01-product-brief.md`) se respeta la
    # ruta declarada. Antes solo valía el primer nivel: lo de una subcarpeta se copiaba a la raíz y
    # el índice lo seguía buscando en la subcarpeta → «falta» justo después de promoverlo.
    inside = CORE.resolve() in declared.parents
    dst = declared if inside else CORE / Path(doc["file"]).name
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = read(source)
    if META_RX.search(text):
        text = META_RX.sub(body + "-->", text, count=1)
    elif "</head>" in text:
        text = text.replace("</head>", f"<!-- {body}-->\n</head>", 1)
    else:
        text = f"<!-- {body}-->\n{text}"
    dst.write_text(text, encoding="utf-8")
    print(f"Promovido {doc_id}: {_repo_rel(source)} → {dst.relative_to(ROOT)} (sellado {stamp} · {sha})")
    if stamp != TODAY.isoformat():
        print(f"  nota: sellado con la fecha del origen ({stamp}), no con hoy — el contenido es de entonces.")
    if not inside:
        print(f'  ⚠ core.json declara "file": "{doc["file"]}" (fuera de core/): el índice seguirá '
              f'mirando ahí. Cámbialo a "{dst.name}" para que use la copia promovida.')


def main():
    args = sys.argv[1:]
    if not TEMPLATE.exists():
        sys.exit(f"ERROR: falta la plantilla {TEMPLATE}")

    if "--init" in args:
        cmd_init()
    elif "--promote" in args:
        i = args.index("--promote")
        if len(args) < i + 3:
            sys.exit("Uso: gen_core.py --promote <doc-id> <ruta-del-fichero-generado> [--date YYYY-MM-DD]")
        forced = args[args.index("--date") + 1] if "--date" in args else ""
        cmd_promote(args[i + 1], args[i + 2], forced)

    if not MANIFEST.exists():
        sys.exit(f"ERROR: falta {MANIFEST.relative_to(ROOT)} — corre `{REGEN} --init` primero.")

    db = build_db(json.loads(read(MANIFEST)))
    content = render(db)
    c = db["counts"]
    resumen = " · ".join(f"{k}: {v}" for k, v in sorted(c.items())) or "sin documentos"

    if "--check" in args:
        current = read(OUT) if OUT.exists() else ""
        if normalize(current) != normalize(content):
            print(f"DESFASADO: {OUT.relative_to(ROOT)} no refleja el estado real ({resumen})")
            sys.exit(1)
        print(f"OK: {OUT.relative_to(ROOT)} al día ({resumen})")
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    print(f"Escrito {OUT.relative_to(ROOT)} — {len(db['docs'])} documentos · {resumen}")
    dudosos = [d["title"] for d in db["docs"] if d["state"] in ("sin-fecha", "falta", "obsoleto")]
    if dudosos:
        print("  ⚠ no fiables ahora mismo: " + ", ".join(dudosos))


if __name__ == "__main__":
    main()
