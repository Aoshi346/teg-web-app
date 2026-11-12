#!/usr/bin/env python3
"""
Paso 3 — 1 captura enfocada POR ITEM (paralelo), con anchors + fallbacks trazables.
Read-only sobre el sitio objetivo.

Lee <audit_dir>/verdicts.json (salida del Paso 2) que por item trae:
  {id, anchor_type(text|selector|scroll_pct), anchor_value, viewport}
y recorta una captura de la zona evidenciada -> shots/<OUT_SUB>/<ID>.jpg

Fallbacks SIN truncado silencioso (todo va a _capture_log.txt):
  text/selector no encontrado -> scroll_pct -> centro
La página de cada item se resuelve por su prefijo de id (<CODE>-n) contra pages_config.json.

Uso:
    python3 capture_items.py <audit_dir>
    OUT_SUB=items_pre PRE_BASE=https://staging.old/ python3 capture_items.py <audit_dir>   # snapshot ANTES

Env:
    OUT_SUB   subdir bajo shots/ (default "items" = estado ACTUAL; "items_pre"/"items_after")
    PRE_BASE  override de la base URL (para capturar un sitio "antes" congelado)
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
PAD = 120
SEM = asyncio.Semaphore(4)
LOG = []


def find_chrome():
    import shutil
    for name in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


def page_of(item_id):
    return item_id.rsplit("-", 1)[0]


async def shoot_region(page, y_center, path):
    top = max(0, int(y_center) - PAD)
    await page.evaluate(f"window.scrollTo(0,{top})")
    await page.wait_for_timeout(250)
    await page.screenshot(path=path, type="jpeg", quality=78)


async def resolve_and_shoot(page, it, path):
    at, av = it.get("anchor_type", "scroll_pct"), it.get("anchor_value", "")
    loc, used = None, ""
    try:
        if at == "selector" and av:
            loc = page.locator(av).first
            used = f"selector:{av}"
        elif at == "text" and av:
            loc = page.get_by_text(av, exact=False).first
            used = f"text:{av[:40]}"
    except Exception:
        loc = None
    if loc is not None:
        try:
            if await loc.count() >= 1:
                await loc.scroll_into_view_if_needed(timeout=6000)
                await page.wait_for_timeout(300)
                box = await loc.bounding_box()
                if box and box["height"] > 4:
                    yc = box["y"] + (await page.evaluate("()=>window.scrollY")) + box["height"] / 2
                    await shoot_region(page, yc, path)
                    return used
        except Exception as e:
            LOG.append(f"{it['id']}: anchor {used} fallo ({type(e).__name__}); fallback")
    try:
        pct = float(str(av).strip() or "50") if at == "scroll_pct" else 50.0
        total = await page.evaluate("() => document.body.scrollHeight")
        yc = total * max(0, min(100, pct)) / 100.0
        await shoot_region(page, yc, path)
        LOG.append(f"{it['id']}: fallback scroll_pct={pct}")
        return f"scroll_pct:{pct}"
    except Exception as e:
        LOG.append(f"{it['id']}: fallback final centro ({type(e).__name__})")
        try:
            await shoot_region(page, 600, path)
        except Exception:
            pass
        return "center"


async def do_item(browser, it, url, out_dir):
    vp = MOBILE if it.get("viewport") == "mobile" else DESKTOP
    path = os.path.join(out_dir, f"{it['id']}.jpg")
    async with SEM:
        ctx = await browser.new_context(viewport=vp, ignore_https_errors=True, is_mobile=(vp is MOBILE))
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.evaluate(r"""async()=>{await new Promise(r=>{let y=0;const t=setInterval(()=>{window.scrollTo(0,y);y+=800;if(y>=document.body.scrollHeight){clearInterval(t);r();}},50);});}""")
            await page.wait_for_timeout(400)
            used = await resolve_and_shoot(page, it, path)
            print(f"[OK] {it['id']:10} ({it.get('viewport','desktop')}) via {used}")
        except Exception as e:
            LOG.append(f"{it['id']}: ERROR pagina ({type(e).__name__}: {e})")
            print(f"[ERR] {it['id']}: {e}")
        await ctx.close()


def load_items(verdicts_path):
    data = json.load(open(verdicts_path))
    if isinstance(data, dict) and "pages" in data:
        return [r for pg in data["pages"] for r in pg.get("results", [])]
    if isinstance(data, list):
        return data
    return []


async def main(audit_dir):
    cfg = json.load(open(os.path.join(audit_dir, "pages_config.json")))
    base = os.environ.get("PRE_BASE") or cfg.get("meta", {}).get("base", "")
    url_by_code = {}
    for p in cfg["pages"]:
        if os.environ.get("PRE_BASE"):
            url_by_code[p["code"]] = base + (p.get("slug", "") + "/" if p.get("slug") else "")
        else:
            url_by_code[p["code"]] = p.get("url") or base + (p.get("slug", "") + "/" if p.get("slug") else "")

    out_sub = os.environ.get("OUT_SUB", "items")
    out_dir = os.path.join(audit_dir, "shots", out_sub)
    os.makedirs(out_dir, exist_ok=True)
    items = load_items(os.path.join(audit_dir, "verdicts.json"))
    print(f"items a capturar: {len(items)}")

    chrome = find_chrome()
    launch = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if chrome:
        launch["executable_path"] = chrome
    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch)
        WAVE = 8
        for i in range(0, len(items), WAVE):
            batch = items[i:i + WAVE]
            await asyncio.gather(*[
                do_item(browser, it, url_by_code.get(page_of(it["id"]), base), out_dir)
                for it in batch
            ])
        await browser.close()
    with open(os.path.join(out_dir, "_capture_log.txt"), "w") as f:
        f.write("\n".join(LOG) or "(sin incidencias)")
    print(f"DONE. capturas en shots/{out_sub}/. incidencias/fallbacks: {len(LOG)} (ver _capture_log.txt)")


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    asyncio.run(main(d))
