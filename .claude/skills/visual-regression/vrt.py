#!/usr/bin/env python3
"""vrt.py — regresión visual con baseline local (sin SaaS, sin red, sin coste por snapshot).

Subcomandos
    capture   captura las páginas de vrt.json en un directorio (Playwright/Chromium)
    compare   compara current contra baseline y escribe los diffs (exit 1 si hay regresión)
    bless     promueve current a baseline (el cambio ERA intencionado)

Flujo típico
    python3 vrt.py capture --config vrt.json --out .vrt/current
    python3 vrt.py compare --config vrt.json                  # exit 1 => revisar .vrt/diff/
    python3 vrt.py bless   --config vrt.json                  # solo si el cambio era querido

Config (vrt.json):
{
  "base_url": "http://127.0.0.1:8000",
  "baseline_dir": ".vrt/baseline",
  "current_dir":  ".vrt/current",
  "diff_dir":     ".vrt/diff",
  "threshold_pct": 0.20,          # % de píxeles distintos tolerado por captura
  "channel_tolerance": 12,        # delta por canal que ya NO se considera ruido de render
  "viewports": {"desktop": [1440, 900], "mobile": [390, 844]},
  "pages": [
    {"name": "home", "path": "/", "wait_for": "[data-testid=hero]",
     "mask": [[0, 0, 1440, 64]]}   # zonas dinámicas: [x1,y1,x2,y2] en px del viewport
  ]
}
"""
import argparse
import json
import os
import shutil
import sys

from PIL import Image, ImageChops, ImageDraw


# ---------------------------------------------------------------- utilidades

def load_config(path):
    cfg = json.load(open(path))
    cfg.setdefault("baseline_dir", ".vrt/baseline")
    cfg.setdefault("current_dir", ".vrt/current")
    cfg.setdefault("diff_dir", ".vrt/diff")
    cfg.setdefault("threshold_pct", 0.20)
    cfg.setdefault("channel_tolerance", 12)
    cfg.setdefault("viewports", {"desktop": [1440, 900]})
    return cfg


def find_chrome():
    """Mismo criterio que .claude/scripts/screenshot.py: nunca hardcodear el binario."""
    for name in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def shot_name(page, viewport):
    return f"{page['name']}--{viewport}.png"


def apply_masks(img, mask):
    """Pinta de negro las zonas dinámicas para que no generen falsos positivos."""
    if not mask:
        return img
    d = ImageDraw.Draw(img)
    for box in mask:
        d.rectangle(box, fill=(0, 0, 0))
    return img


# ------------------------------------------------------------------ capture

def cmd_capture(cfg, outdir):
    from playwright.sync_api import sync_playwright

    os.makedirs(outdir, exist_ok=True)
    written = []
    launch = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage",
                                         "--force-device-scale-factor=1",
                                         "--hide-scrollbars", "--font-render-hinting=none"]}
    chrome = find_chrome()
    if chrome:
        launch["executable_path"] = chrome
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        for vp_name, (w, h) in cfg["viewports"].items():
            ctx = browser.new_context(viewport={"width": w, "height": h},
                                      device_scale_factor=1,
                                      reduced_motion="reduce")
            page = ctx.new_page()
            for spec in cfg["pages"]:
                url = cfg["base_url"].rstrip("/") + spec["path"]
                page.goto(url, wait_until="load")
                if spec.get("wait_for"):
                    page.wait_for_selector(spec["wait_for"], timeout=10000)
                page.evaluate("() => document.fonts && document.fonts.ready")
                out = os.path.join(outdir, shot_name(spec, vp_name))
                page.screenshot(path=out, full_page=spec.get("full_page", True))
                img = apply_masks(Image.open(out).convert("RGB"), spec.get("mask"))
                img.save(out)
                written.append(out)
            ctx.close()
        browser.close()
    for w in written:
        print(f"capturado  {w}")
    return 0


# ------------------------------------------------------------------ compare

def compare_pair(base_path, cur_path, diff_path, channel_tolerance):
    """Devuelve (pct_distinto, bbox_cambios | None, motivo | None)."""
    base = Image.open(base_path).convert("RGB")
    cur = Image.open(cur_path).convert("RGB")
    if base.size != cur.size:
        return 100.0, None, f"tamaño distinto: baseline {base.size} vs current {cur.size}"

    diff = ImageChops.difference(base, cur).convert("L")
    # binariza: por debajo de la tolerancia es ruido de render (antialias, subpíxel)
    mask = diff.point(lambda v: 255 if v > channel_tolerance else 0)
    changed = sum(mask.histogram()[255:])
    total = base.size[0] * base.size[1]
    pct = 100.0 * changed / total
    bbox = mask.getbbox()

    if changed:
        os.makedirs(os.path.dirname(diff_path) or ".", exist_ok=True)
        overlay = cur.copy()
        red = Image.new("RGB", cur.size, (255, 0, 0))
        overlay.paste(red, mask=mask)                       # zonas cambiadas en rojo
        out = Image.blend(cur, overlay, 0.55)
        if bbox:
            ImageDraw.Draw(out).rectangle(bbox, outline=(255, 0, 0), width=3)
        out.save(diff_path)
    return pct, bbox, None


def cmd_compare(cfg):
    base_dir, cur_dir, diff_dir = cfg["baseline_dir"], cfg["current_dir"], cfg["diff_dir"]
    if not os.path.isdir(base_dir):
        print(f"NO HAY BASELINE en {base_dir} — créalo con: vrt.py bless (tras revisar current)")
        return 2
    fails, checked = [], 0
    for vp_name in cfg["viewports"]:
        for spec in cfg["pages"]:
            name = shot_name(spec, vp_name)
            b, c = os.path.join(base_dir, name), os.path.join(cur_dir, name)
            if not os.path.exists(c):
                fails.append((name, "falta la captura actual", None)); continue
            if not os.path.exists(b):
                fails.append((name, "sin baseline (página nueva)", None)); continue
            checked += 1
            pct, bbox, err = compare_pair(b, c, os.path.join(diff_dir, name),
                                          cfg["channel_tolerance"])
            thr = spec.get("threshold_pct", cfg["threshold_pct"])
            if err:
                fails.append((name, err, None))
            elif pct > thr:
                fails.append((name, f"{pct:.3f}% de píxeles distintos (umbral {thr}%)", bbox))
            else:
                print(f"OK    {name}  ({pct:.3f}% ≤ {thr}%)")
    for name, motivo, bbox in fails:
        loc = f"  zona {bbox}" if bbox else ""
        print(f"DIFF  {name}  {motivo}{loc}")
    print(f"\n# comparadas: {checked} · regresiones: {len(fails)}"
          + (f" · diffs en {diff_dir}/" if fails else ""))
    return 1 if fails else 0


# -------------------------------------------------------------------- bless

def cmd_bless(cfg, only=None):
    base_dir, cur_dir = cfg["baseline_dir"], cfg["current_dir"]
    os.makedirs(base_dir, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(cur_dir)):
        if not f.endswith(".png") or (only and only not in f):
            continue
        shutil.copy2(os.path.join(cur_dir, f), os.path.join(base_dir, f))
        print(f"bendecido  {f}")
        n += 1
    if os.path.isdir(cfg["diff_dir"]):
        shutil.rmtree(cfg["diff_dir"])
    print(f"\n# baseline actualizado: {n} capturas en {base_dir}"
          f"\n# commitea el baseline junto al cambio que lo justifica")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["capture", "compare", "bless"])
    ap.add_argument("--config", default="vrt.json")
    ap.add_argument("--out", help="capture: directorio destino (default: current_dir)")
    ap.add_argument("--only", help="bless: bendice solo las capturas que contengan este texto")
    a = ap.parse_args()
    cfg = load_config(a.config)
    if a.cmd == "capture":
        return cmd_capture(cfg, a.out or cfg["current_dir"])
    if a.cmd == "compare":
        return cmd_compare(cfg)
    return cmd_bless(cfg, a.only)


if __name__ == "__main__":
    sys.exit(main())
