#!/usr/bin/env python3
"""
Paso 1 — Captura masiva + dump DOM (paralelo) + auditoría de enlaces.
Read-only sobre el sitio objetivo. NO modifica nada del servidor.

Lee <audit_dir>/pages_config.json. Por cada página:
  - full-page desktop (1440)  -> shots/pages/<code>-full.jpg
  - full-page mobile  (390)   -> shots/pages/<code>-m.jpg
  - slices verticales desktop -> shots/pages/<code>-s<N>.jpg
  - dump DOM (headings, secciones+bg+geometría, anchors) -> shots/pages/<code>.dom.json
Audit global de status HTTP de enlaces internos -> shots/pages/_links_audit.json

Uso:
    python3 capture_pages.py <audit_dir>

pages_config.json: { "meta": {"base": "http://127.0.0.1:8000/"},
                     "pages": [ {"code":"HOME","slug":"","url":"...optativa..."}, ... ] }
La URL de cada página = page.url si está, si no meta.base + slug.
"""
import asyncio, json, os, sys
from urllib.parse import urlparse
from playwright.async_api import async_playwright

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
SEM = asyncio.Semaphore(4)

DOM_JS = r"""
() => {
  const txt = e => (e.textContent || '').trim().replace(/\s+/g,' ').slice(0,160);
  const heads = [...document.querySelectorAll('h1,h2,h3,h4')].map(h => ({
    tag: h.tagName.toLowerCase(), text: txt(h),
    y: Math.round(h.getBoundingClientRect().top + window.scrollY)
  })).filter(h => h.text);
  const secs = [...document.querySelectorAll('section,.wp-block-group,header,footer,main,article')].slice(0,120).map(s => {
    const cs = getComputedStyle(s);
    const r = s.getBoundingClientRect();
    return {
      tag: s.tagName.toLowerCase(),
      cls: (s.className||'').toString().slice(0,120),
      bg: cs.backgroundColor,
      y: Math.round(r.top + window.scrollY),
      h: Math.round(r.height)
    };
  }).filter(s => s.h > 40);
  const links = [...document.querySelectorAll('a[href]')].map(a => ({
    text: txt(a).slice(0,60),
    href: a.getAttribute('href'),
    abs: a.href,
    y: Math.round(a.getBoundingClientRect().top + window.scrollY)
  }));
  return {
    title: document.title, url: location.href, lang: document.documentElement.lang,
    height: document.body.scrollHeight, headings: heads, sections: secs, links: links
  };
}
"""


def find_chrome():
    """Primer binario de Chrome/Chromium disponible, o None (Playwright usa el suyo)."""
    import shutil
    for name in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


async def autoscroll(page):
    await page.evaluate(r"""async () => {
      await new Promise(res => {
        let y = 0; const step = 700;
        const t = setInterval(() => {
          window.scrollTo(0, y); y += step;
          if (y >= document.body.scrollHeight) { clearInterval(t); res(); }
        }, 60);
      });
    }""")
    await page.wait_for_timeout(600)
    await page.evaluate("window.scrollTo(0,0)")
    await page.wait_for_timeout(300)


async def capture(browser, out, code, url, link_acc):
    async with SEM:
        ctx = await browser.new_context(viewport=DESKTOP, device_scale_factor=1,
                                        ignore_https_errors=True)
        page = await ctx.new_page()
        dom = {}
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                print(f"[ERR] {code} goto: {e}")
        try:
            await autoscroll(page)
            await page.screenshot(path=f"{out}/{code}-full.jpg", full_page=True, type="jpeg", quality=72)
            dom = await page.evaluate(DOM_JS)
            h = dom.get("height", 0) or 3000
            n = min(8, max(1, (h + 1499) // 1500))
            for i in range(n):
                await page.evaluate(f"window.scrollTo(0,{i*1500})")
                await page.wait_for_timeout(250)
                await page.screenshot(path=f"{out}/{code}-s{i}.jpg", type="jpeg", quality=70)
            for l in dom.get("links", []):
                ab = l.get("abs", "")
                if ab.startswith("http"):
                    link_acc.add(ab)
        except Exception as e:
            print(f"[ERR] {code} desktop: {e}")
        await ctx.close()
        ctx2 = await browser.new_context(viewport=MOBILE, device_scale_factor=1,
                                         is_mobile=True, ignore_https_errors=True)
        page2 = await ctx2.new_page()
        try:
            await page2.goto(url, wait_until="networkidle", timeout=60000)
            await autoscroll(page2)
            await page2.screenshot(path=f"{out}/{code}-m.jpg", full_page=True, type="jpeg", quality=70)
        except Exception as e:
            print(f"[ERR] {code} mobile: {e}")
        await ctx2.close()
        with open(f"{out}/{code}.dom.json", "w", encoding="utf-8") as f:
            json.dump(dom, f, ensure_ascii=False, indent=1)
        print(f"[OK] {code}  links+={len(dom.get('links',[]))}  h={dom.get('height')}")


async def audit_links(browser, out, links, host):
    uniq = sorted({l for l in links if host and host in l})
    ctx = await browser.new_context(ignore_https_errors=True)
    req = ctx.request
    sem = asyncio.Semaphore(8)
    res = {}

    async def chk(u):
        async with sem:
            try:
                r = await req.get(u, timeout=25000)
                res[u] = r.status
            except Exception as e:
                res[u] = f"ERR:{type(e).__name__}"

    await asyncio.gather(*[chk(u) for u in uniq])
    await ctx.close()
    with open(f"{out}/_links_audit.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    bad = {u: s for u, s in res.items() if s != 200}
    print(f"[LINKS] {len(uniq)} únicos, {len(bad)} != 200")


async def main(audit_dir):
    cfg = json.load(open(os.path.join(audit_dir, "pages_config.json")))
    base = cfg.get("meta", {}).get("base", "")
    out = os.path.join(audit_dir, "shots", "pages")
    os.makedirs(out, exist_ok=True)
    host = urlparse(base).netloc if base else ""

    def url_of(p):
        if p.get("url"):
            return p["url"]
        slug = p.get("slug", "")
        return base + (slug + "/" if slug else "")

    pages = cfg["pages"]
    link_acc = set()
    chrome = find_chrome()
    launch = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if chrome:
        launch["executable_path"] = chrome
        print(f"[capture_pages] usando {chrome}")
    else:
        print("[capture_pages] sin Chrome del sistema; usando el Chromium de Playwright")
    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch)
        await asyncio.gather(*[capture(browser, out, pg["code"], url_of(pg), link_acc) for pg in pages])
        await audit_links(browser, out, link_acc, host)
        await browser.close()
    print("DONE pages:", len(pages))


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    asyncio.run(main(d))
