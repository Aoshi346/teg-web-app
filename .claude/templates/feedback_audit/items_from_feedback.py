#!/usr/bin/env python3
"""
Paso 0 — feedback de cliente -> items.json (trazable, idempotente).

Convierte un fichero de feedback (.docx / .txt / .md) en items verificables. Cada párrafo/bullet
no vacío se vuelve un item con su CITA VERBATIM (texto_original) para CTRL+F — anti-alucinación:
NO se inventa copy, se ancla a lo que dijo el cliente.

Uso:
    python3 items_from_feedback.py <feedback.(docx|txt|md)> <audit_dir> [--page GEN]

- <audit_dir> es la carpeta de trabajo de la auditoría (contiene/contendrá items.json, pages_config.json,
  shots/, verdicts.json). Si no existe items.json, lo crea con un meta mínimo.
- Tag de página por item: una línea puede empezar con "[CODE] ..." o "CODE: ..." para asignarla a esa
  página (los codes deben existir en pages_config.json si lo hay). Sin tag -> --page (default GEN).
- IDs: <PAGE>-<n> incremental por página, preservando los ya existentes.
- Idempotente: un párrafo cuyo texto ya coincide (difflib, con boost por substring) con un item
  existente NO se vuelve a añadir.

Read-only salvo escribir <audit_dir>/items.json.
"""
import json, os, re, sys, zipfile, difflib
from xml.etree import ElementTree as ET

NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def q(t):
    return "{%s}%s" % (NS, t)


def docx_paragraphs(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("word/document.xml"))
    out = []
    for p in root.iter(q("p")):
        txt = "".join(t.text or "" for t in p.iter(q("t")))
        if txt.strip():
            out.append(txt.strip())  # verbatim, sin corregir
    return out


def text_paragraphs(path):
    """txt/md -> un item por LÍNEA no vacía. Una línea INDENTADA (espacio/tab inicial) o que
    sigue tras coma/sin puntuación se trata como continuación (texto envuelto) del item anterior.
    Línea en blanco siempre separa. Quita marcadores de bullet/numeración."""
    raw = open(path, encoding="utf-8").read()
    blocks, cur = [], []

    def flush():
        if cur:
            blocks.append(" ".join(cur).strip())
            cur.clear()

    for line in raw.splitlines():
        s = line.strip()
        if not s:
            flush()
            continue
        indented = line[:1] in (" ", "\t")
        clean = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)
        if indented and cur:
            cur.append(clean)          # continuación explícita (sub-línea)
        else:
            flush()                    # nueva línea = nuevo item
            cur.append(clean)
    flush()
    return [b for b in blocks if b]


def paragraphs(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return docx_paragraphs(path)
    return text_paragraphs(path)


def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


TAG_RE = re.compile(r"^\s*(?:\[([A-Z][A-Z0-9]{0,7})\]|([A-Z][A-Z0-9]{0,7})\s*:)\s*(.*)$", re.S)


def split_tag(text, default_page):
    m = TAG_RE.match(text)
    if m:
        code = m.group(1) or m.group(2)
        return code, m.group(3).strip()
    return default_page, text.strip()


def is_dup(cand, existing_norm):
    """True si el párrafo ya está representado por un item (difflib + boost substring)."""
    cn = norm(cand)
    head = cn[:60]
    for en in existing_norm:
        r = difflib.SequenceMatcher(None, cn[:400], en[:400]).ratio()
        if head and head in en:
            r = max(r, 0.9)
        if r >= 0.85:
            return True
    return False


def load_items(audit_dir):
    p = os.path.join(audit_dir, "items.json")
    if os.path.exists(p):
        return json.load(open(p))
    return {
        "meta": {
            "title": "Feedback audit",
            "epics": {"A": {"name": "General", "color": "#444"}},
            "statuses": ["backlog", "doing", "review", "done", "blocked"],
            "decisions": ["aprobar", "modificar", "aplazar", "descartar"],
            "clarities": ["claro", "duda"],
            "pages": [],
        },
        "items": [],
    }


def next_n(items, page):
    ns = [int(it["id"].rsplit("-", 1)[1]) for it in items
          if it["id"].startswith(page + "-") and it["id"].rsplit("-", 1)[1].isdigit()]
    return (max(ns) + 1) if ns else 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    feedback, audit_dir = args[0], args[1]
    default_page = "GEN"
    if "--page" in opts:
        default_page = opts[opts.index("--page") + 1]
    os.makedirs(audit_dir, exist_ok=True)

    d = load_items(audit_dir)
    items = d["items"]
    existing_norm = [norm(it.get("texto_original") or it.get("text", "")) for it in items]
    known_pages = {p["code"] for p in d["meta"].get("pages", [])}

    added, dups = 0, 0
    for para in paragraphs(feedback):
        page, text = split_tag(para, default_page)
        if known_pages and page not in known_pages and page != default_page:
            # code desconocido -> trátalo como texto normal de la página default
            page, text = default_page, para
        if is_dup(text, existing_norm):
            dups += 1
            continue
        nid = "%s-%d" % (page, next_n(items, page))
        items.append({
            "id": nid, "page": page, "epic": "A", "severity": "P2", "effort": "M",
            "clarity": "claro", "text": text, "texto_original": text,
            "blocks": "", "agent": "—", "status": "backlog", "blocked": False,
            "decision": "", "note": "", "before": "", "after": "",
            "src": os.path.basename(feedback),
        })
        existing_norm.append(norm(text))
        added += 1

    d["meta"]["total"] = len(items)
    d["meta"]["source"] = os.path.basename(feedback)
    json.dump(d, open(os.path.join(audit_dir, "items.json"), "w"),
              ensure_ascii=False, indent=1)
    print("añadidos %d items (saltados %d duplicados) · total %d" % (added, dups, len(items)))
    from collections import Counter
    print("por página:", dict(Counter(it["page"] for it in items)))


if __name__ == "__main__":
    main()
