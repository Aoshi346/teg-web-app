#!/usr/bin/env python3
"""embed.py — imágenes autocontenidas (base64) para el report-kit.

API:  from embed import make_embed → data-URI (JPEG recomprimido si hay Pillow, si no el fichero tal cual)
CLI:  python3 embed.py <plan-dir>   → recorre report.json y embebe evidence[kind=img] en report.embedded.json

Adaptado de feedback_audit/build_report.py:make_embed (mismo enfoque: resize ~820px, quality ~52,
data:image/jpeg;base64) — el único camino a un HTML con capturas que abre OFFLINE.
"""
import base64
import io
import json
import mimetypes
import os
import sys

MAX_W = 820
QUALITY = 52


def make_embed(path, max_w=MAX_W, quality=QUALITY):
    """Devuelve un data-URI. Con Pillow recomprime (JPEG); sin Pillow, embebe el fichero tal cual."""
    if not path or not os.path.exists(path):
        return None
    try:
        from PIL import Image  # opcional

        im = Image.open(path)
        if im.mode in ("RGBA", "P", "LA"):
            im = im.convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, int(im.height * max_w / im.width)))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        mime = mimetypes.guess_type(path)[0] or "image/png"
        with open(path, "rb") as f:
            return f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"aviso: no pude embeber {path}: {e}", file=sys.stderr)
        return None


def embed_report(plan_dir):
    src = os.path.join(plan_dir, "report.json")
    doc = json.load(open(src, encoding="utf-8"))
    n_ok = n_miss = 0
    for it in doc.get("items", []):
        for ev in it.get("evidence", []):
            if ev.get("kind") != "img" or str(ev.get("src", "")).startswith("data:"):
                continue
            uri = make_embed(os.path.join(plan_dir, ev["src"]))
            if uri:
                ev["src_original"] = ev["src"]
                ev["src"] = uri
                n_ok += 1
            else:
                n_miss += 1
    out = os.path.join(plan_dir, "report.embedded.json")
    json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Escrito {out} — {n_ok} imágenes embebidas, {n_miss} no encontradas")
    return out


if __name__ == "__main__":
    embed_report(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd())
