#!/usr/bin/env python3
"""construir_pdf.py — la documentación de un proyecto en PDF: uno completo con portada e índice y,
con --separados, uno por capítulo. Lo usa la skill `documentar` (paso 8).

Uso (desde la raíz del proyecto):
  python3 .claude/skills/documentar/construir_pdf.py [--config RUTA] [--separados] [--html-solo]
                                                      [--avisar]

  --config      documentacion.json (por defecto .docs/documentacion/documentacion.json). Si no
                existe, toma .docs/documentacion/NN-*.md en orden y la marca neutra.
  --separados   además del completo, un PDF por capítulo en <carpeta>/pdf/ (para subirlos sueltos).
  --html-solo   escribe el HTML intermedio y para (para mirar el maquetado en un navegador).
  --avisar      los diagramas ilegibles se listan pero NO abortan (triaje la primera vez).

Qué hace con los diagramas (Mermaid), que es lo que más se rompe:
  1. Los pinta con letra de 15 px y mide, ya pintado, a qué tamaño queda la letra en la página.
  2. Si en vertical baja de `diagramas.letra_minima_px` (10,5 px ≈ 8 pt), lo saca a una página
     APAISADA propia. Si ni apaisado llega, ABORTA diciendo cuál: hay que partirlo en dos.
  3. Avisa (sin abortar) de los diagramas con más de `diagramas.max_nodos` nodos (12).
  4. Mide el ENREDO ya pintado (`enredo.js`): cruces de líneas, etiquetas pisadas, líneas por encima
     de cajas ajenas, abanicos (≥4 flechas a una caja), rodeos y la misma etiqueta en ≥3 flechas.
     Con `diagramas.motor: "auto"` prueba dagre y ELK en flujos y estados y se queda el menos
     enredado. Por encima de `diagramas.enredo_max` (3 puntos) ABORTA: hay que reorganizarlo.

Lo que no sale de la máquina:
  · Todo lo que esté entre `<!-- pdf:omitir -->` y `<!-- /pdf:omitir -->` se queda en el repo.
  · `sustituir` (en la config) reemplaza rutas o nombres de la máquina al generar.

Tres desenlaces, nunca dos (rules/verification.md): sale el PDF · aborta con código 2 diciendo qué
no se pintó (capítulo que falta, diagrama que no compila o ilegible, imagen rota, error de JS). Un
PDF al que le falta algo en silencio es peor que no tener PDF.
"""
import argparse
import datetime
import html as html_mod
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

OMITIR = re.compile(r"<!--\s*pdf:omitir\s*-->.*?<!--\s*/pdf:omitir\s*-->\n?", re.S)
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
CAPITULO_NN = re.compile(r"^\d{2}-.+\.md$")

MARCA_NEUTRA = {
    "nombre": "",
    "logo": None,
    "colores": {"papel": "#F7F6F2", "papel2": "#ECEAE3", "tinta": "#1F2430", "suave": "#565E6E",
                "linea": "#D6D3CA", "acento": "#1F5F99", "acento_vivo": "#5AA9E6", "piel": "#E6EEF5"},
    # familia CSS de cada papel; `ficheros` opcional: [{"peso": 400, "ruta": "…woff2"}]
    "fuentes": {"display": {"familia": "Georgia, serif"},
                "cuerpo": {"familia": "system-ui, -apple-system, 'Segoe UI', sans-serif"},
                "mono": {"familia": "ui-monospace, SFMono-Regular, Menlo, monospace"}},
    "titulos_en_mayusculas": False,
}
DIAGRAMAS = {"letra_px": 15, "letra_minima_px": 10.5, "max_nodos": 12, "motor": "auto", "enredo_max": 3}


def abortar(msg: str) -> None:
    print(f"ABORTO: {msg}", file=sys.stderr)
    sys.exit(2)


def raiz_git() -> Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(r.stdout.strip()) if r.returncode == 0 else Path.cwd()


def cargar_config(raiz: Path, ruta: str | None) -> tuple[dict, Path]:
    cfg_path = Path(ruta) if ruta else raiz / ".docs/documentacion/documentacion.json"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            abortar(f"{cfg_path} no es JSON válido: {e}")
    elif ruta:
        abortar(f"no existe la config {cfg_path}")
    carpeta = raiz / cfg.get("carpeta", ".docs/documentacion")
    marca = {**MARCA_NEUTRA, **cfg.get("marca", {})}
    marca["colores"] = {**MARCA_NEUTRA["colores"], **cfg.get("marca", {}).get("colores", {})}
    marca["fuentes"] = {**MARCA_NEUTRA["fuentes"], **cfg.get("marca", {}).get("fuentes", {})}
    cfg["marca"] = marca
    cfg["diagramas"] = {**DIAGRAMAS, **cfg.get("diagramas", {})}
    if "capitulos" in cfg:
        cfg["capitulos"] = [raiz / c for c in cfg["capitulos"]]
    else:
        if not carpeta.is_dir():
            abortar(f"no existe {carpeta.relative_to(raiz)} y no hay `capitulos` en la config")
        cfg["capitulos"] = sorted(p for p in carpeta.iterdir() if CAPITULO_NN.match(p.name))
    if not cfg["capitulos"]:
        abortar(f"no hay capítulos (NN-*.md) en {carpeta.relative_to(raiz)}")
    cfg.setdefault("titulo", "Documentación")
    cfg.setdefault("entradilla", "Qué es, cómo está construido, cómo se opera y cómo se usa. Cada "
                                 "capítulo empieza con «En corto» para quien no es técnico; el "
                                 "detalle viene debajo.")
    cfg.setdefault("nombre_fichero", "documentacion")
    cfg.setdefault("prefijo_capitulos", cfg["nombre_fichero"])
    cfg["sustituir"] = cfg.get("sustituir", [])
    return cfg, carpeta


def leer(ruta: Path, raiz: Path, sustituir: list) -> str:
    if not ruta.exists():
        abortar(f"falta el capítulo {ruta.relative_to(raiz)}")
    texto = FRONTMATTER.sub("", ruta.read_text(encoding="utf-8"), count=1)
    texto = OMITIR.sub("", texto)
    if "pdf:omitir" in texto:
        abortar(f"{ruta.name}: hay un `pdf:omitir` sin cerrar (o mal escrito): no sé qué omitir")
    for real, marcador in sustituir:
        texto = texto.replace(real, marcador)
    return re.sub(r"!\[([^\]]*)\]\((?!https?:|file:|/)([^)]+)\)",
                  lambda m: f"![{m.group(1)}]({(ruta.parent / m.group(2)).resolve().as_uri()})", texto)


def css_fuentes(marca: dict, raiz: Path) -> str:
    reglas = []
    for papel in ("display", "cuerpo", "mono"):
        f = marca["fuentes"][papel]
        nombre = f["familia"].split(",")[0].strip().strip("'\"")
        for fich in f.get("ficheros", []):
            ruta = (raiz / fich["ruta"]).resolve()
            if not ruta.exists():
                abortar(f"la fuente {fich['ruta']} no existe")
            reglas.append(f"@font-face {{ font-family: '{nombre}'; font-weight: {fich.get('peso', 400)}; "
                          f"src: url({ruta.as_uri()}); }}")
    return "\n".join(reglas)


PLANTILLA = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>__TITULO_TXT__</title>
<style>
__FUENTES__
:root { __COLORES__ --display: __F_DISPLAY__; --cuerpo: __F_CUERPO__; --mono: __F_MONO__; }
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
@page apaisada { size: A4 landscape; margin: 14mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: var(--cuerpo); color: var(--tinta); font-size: 10pt; line-height: 1.55; margin: 0; background: #fff; }
h1, h2, h3 { font-family: var(--display); font-weight: 400; letter-spacing: .01em; line-height: 1.25; break-after: avoid; __MAYUS__ }
h1 { font-size: 24pt; margin: 0 0 6mm; border-bottom: 3px solid var(--tinta); padding-bottom: 2mm; }
h2 { font-size: 14pt; margin: 8mm 0 3mm; color: var(--acento); }
h3 { font-size: 11pt; margin: 6mm 0 2mm; }
h4 { font-size: 10pt; margin: 4mm 0 1mm; }
a { color: var(--acento); text-decoration: none; }
code, pre { font-family: var(--mono); font-size: 7.6pt; }
code { background: var(--papel2); padding: 0 .25em; border-radius: 2px; overflow-wrap: anywhere; }
pre { background: var(--papel); border-left: 3px solid var(--acento); padding: 3mm; white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 3mm 0; font-size: 8.6pt; }
th { text-align: left; background: var(--papel2); color: var(--suave); font-weight: 600; }
th, td { border-bottom: 1px solid var(--linea); padding: 1.6mm 2mm; vertical-align: top; overflow-wrap: anywhere; }
tr { break-inside: avoid; }
td:first-child, th:first-child { min-width: 8mm; }
blockquote { margin: 3mm 0; padding: 2mm 4mm; background: var(--piel); border-left: 3px solid var(--acento); }
img { max-width: 100%; border: 1px solid var(--linea); margin: 2mm 0; break-inside: avoid; }
figure.diagrama { margin: 5mm 0; text-align: center; break-inside: avoid; }
figure.diagrama svg { height: auto; max-width: none; }
figure.diagrama figcaption { font-size: 7.5pt; color: var(--suave); margin-top: 1.5mm; }
section.apaisada { page: apaisada; break-before: page; break-after: page; display: flex; flex-direction: column; justify-content: center; min-height: 170mm; }
section.apaisada figure.diagrama { margin: 0; }
.capitulo { break-before: page; }
.num { font-family: var(--mono); font-size: 9pt; color: var(--acento); letter-spacing: .1em; }
.portada { height: 257mm; background: var(--tinta); color: var(--papel); padding: 30mm 22mm; display: flex; flex-direction: column; justify-content: space-between; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.portada img { border: 0; width: 70mm; }
.portada h1 { font-size: 40pt; border-color: var(--acento_vivo); color: var(--papel); }
.portada p { font-size: 12pt; color: var(--papel2); max-width: 130mm; }
.portada .pie { font-family: var(--mono); font-size: 8pt; color: var(--acento_vivo); }
.indice { break-before: page; }
.indice ol { list-style: none; padding: 0; }
.indice > ol > li { margin: 0 0 3mm; font-weight: 600; font-size: 11pt; }
.indice ol ol { font-weight: 400; font-size: 8.6pt; color: var(--suave); columns: 2; margin: 1mm 0 0 8mm; }
</style></head><body>
<section class="portada">
  __LOGO__
  <div><h1>__TITULO__</h1><p>__ENTRADILLA__</p></div>
  <div class="pie">__PIE__</div>
</section>
<section class="indice"><h1>Índice</h1><ol id="indice"></ol></section>
<main id="doc"></main>
<script src="https://cdn.jsdelivr.net/npm/marked@14/marked.min.js"></script>
<script>__ENREDO__</script>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
import elk from "https://cdn.jsdelivr.net/npm/@mermaid-js/layout-elk@0/dist/mermaid-layout-elk.esm.min.mjs";
mermaid.registerLayoutLoaders(elk);
const CAPS = __DATOS__;
const D = __DIAGRAMAS__;
// Ancho y alto útiles en px CSS (96 ppp): A4 vertical 178×~235 mm de caja; apaisado 265×~165 mm.
const CAJA = { vertical: { w: 672, h: 880 }, apaisada: { w: 1000, h: 600 } };
const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-");
const doc = document.getElementById("doc"), indice = document.getElementById("indice");
CAPS.forEach(([n, md]) => {
  const sec = document.createElement("section");
  sec.className = "capitulo";
  sec.innerHTML = marked.parse(md);
  const h1 = sec.querySelector("h1");
  const titulo = h1 ? h1.textContent : "Capítulo " + n;
  const id = "cap-" + n, nn = String(n).padStart(2, "0");
  if (h1) { h1.id = id; h1.insertAdjacentHTML("beforebegin", `<div class="num">${nn}</div>`); }
  const subs = [...sec.querySelectorAll("h2")].map((h) => { h.id = id + "-" + slug(h.textContent); return `<li><a href="#${h.id}">${h.textContent}</a></li>`; });
  indice.insertAdjacentHTML("beforeend", `<li><a href="#${id}">${nn} · ${titulo}</a><ol>${subs.join("")}</ol></li>`);
  let k = 0;
  sec.querySelectorAll("pre > code.language-mermaid").forEach((c) => {
    k += 1;
    const fig = document.createElement("figure"); fig.className = "diagrama";
    fig.dataset.src = c.textContent.trim();
    const primera = fig.dataset.src.split("\n")[0].trim();
    const cab = [...sec.querySelectorAll("h2, h3")].filter((h) => h.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING).pop();
    fig.dataset.donde = `cap ${nn}, diagrama ${k} (${primera}) — sección «${cab ? cab.textContent : titulo}»`;
    c.parentElement.replaceWith(fig);
  });
  doc.appendChild(sec);
});
mermaid.initialize({ startOnLoad: false, theme: "base", securityLevel: "strict",
  flowchart: { useMaxWidth: false, htmlLabels: true }, sequence: { useMaxWidth: false },
  er: { useMaxWidth: false }, state: { useMaxWidth: false }, journey: { useMaxWidth: false },
  themeVariables: __TEMA__ });
window.__fallos = []; window.__ilegibles = []; window.__densos = []; window.__apaisados = [];
window.__enredados = []; window.__liosos = []; window.__motores = [];
const describe = (r) => [r.cruces && `${r.cruces} cruces`, r.solapes && `${r.solapes} etiquetas pisadas`,
  r.atraviesa && `${r.atraviesa} líneas sobre cajas ajenas`, r.abanico >= 4 && `${r.abanico} flechas a la misma caja`,
  r.rodeos && `${r.rodeos} rodeos`, r.repetidas && `la misma etiqueta en ${r.repetidas} flechas`].filter(Boolean).join(", ");
function encajar(fig) {
  const svg = fig.querySelector("svg");
  const vb = svg.viewBox && svg.viewBox.baseVal;
  const w = vb && vb.width ? vb.width : svg.getBBox().width, h = vb && vb.height ? vb.height : svg.getBBox().height;
  const escala = (caja) => Math.min(1, caja.w / w, caja.h / h);
  let modo = "vertical", e = escala(CAJA.vertical);
  if (D.letra_px * e < D.letra_minima_px) {
    const ea = escala(CAJA.apaisada);
    if (ea > e) { modo = "apaisada"; e = ea; }
  }
  svg.style.width = (w * e) + "px"; svg.removeAttribute("height"); svg.style.maxWidth = "none";
  const letra = D.letra_px * e;
  if (letra < D.letra_minima_px) window.__ilegibles.push(`${fig.dataset.donde}: letra ${letra.toFixed(1)} px (mínimo ${D.letra_minima_px}) incluso apaisado → pártelo`);
  if (modo === "apaisada") {
    const s = document.createElement("section"); s.className = "apaisada";
    fig.replaceWith(s); s.appendChild(fig);
    window.__apaisados.push(fig.dataset.donde);
  }
  const nodos = svg.querySelectorAll("g.node, g.actor-man, rect.actor-top, g.entityBox, g[id^='entity-']").length;
  if (nodos > D.max_nodos) window.__densos.push(`${fig.dataset.donde}: ${nodos} nodos (máx. recomendado ${D.max_nodos})`);
}
// Pinta con un motor y lo deja medido, a tamaño natural (los umbrales del medidor van en px reales).
async function pintarCon(fig, motor, i) {
  const src = fig.dataset.src;
  const conMotor = motor === "elk" ? `---\nconfig:\n  layout: elk\n---\n${src}` : src;
  const { svg } = await mermaid.render(`m${i}${motor}`, conMotor);
  fig.innerHTML = svg;
  const el = fig.querySelector("svg"); el.style.maxWidth = "none";
  return window.analizarSVG(el);
}
(async () => {
  const figs = [...document.querySelectorAll("figure.diagrama")];
  for (let i = 0; i < figs.length; i++) {
    const fig = figs[i], tipo = fig.dataset.src.split(/\s/)[0];
    const motores = /^(flowchart|graph|stateDiagram)/.test(tipo)
      ? (D.motor === "auto" ? ["dagre", "elk"] : [D.motor]) : ["dagre"];
    let mejor = null;
    try {
      for (const m of motores) {
        const r = await pintarCon(fig, m, i);
        if (!mejor || r.puntos < mejor.r.puntos) mejor = { m, r, html: fig.innerHTML };
        if (r.puntos === 0) break;
      }
    } catch (e) { window.__fallos.push(`${fig.dataset.donde}: no compila (${String(e.message || e).split("\n")[0].slice(0, 90)})`); fig.innerHTML = ""; continue; }
    fig.innerHTML = mejor.html;
    if (motores.length > 1) window.__motores.push(`${mejor.m}`);
    const r = mejor.r;
    if (r.puntos > D.enredo_max) window.__enredados.push(`${fig.dataset.donde}: enredo ${r.puntos} (máx. ${D.enredo_max}) — ${describe(r)} → reorganízalo`);
    else if (r.puntos > 0) window.__liosos.push(`${fig.dataset.donde}: enredo ${r.puntos} — ${describe(r)}`);
    encajar(fig);
  }
  window.__listo = true;
})().catch((e) => { window.__fallos.push("error del pintor: " + String(e)); window.__listo = true; });
</script></body></html>"""


def html(caps: list[tuple[int, str]], cfg: dict, raiz: Path, titulo: str, entradilla: str, pie: str) -> str:
    m = cfg["marca"]
    c = m["colores"]
    logo = ""
    if m.get("logo"):
        ruta = (raiz / m["logo"]).resolve()
        if not ruta.exists():
            abortar(f"el logo {m['logo']} no existe")
        logo = f'<img src="{ruta.as_uri()}" alt="">'
    tema = {"fontFamily": m["fuentes"]["cuerpo"]["familia"], "fontSize": f"{cfg['diagramas']['letra_px']}px",
            "primaryColor": c["piel"], "primaryBorderColor": c["acento"], "primaryTextColor": c["tinta"],
            "lineColor": c["suave"], "secondaryColor": c["papel2"], "tertiaryColor": c["papel"]}
    rep = {
        "__TITULO_TXT__": html_mod.escape(re.sub("<[^>]+>", " ", titulo)),
        "__FUENTES__": css_fuentes(m, raiz),
        "__COLORES__": " ".join(f"--{k}: {v};" for k, v in c.items()),
        "__F_DISPLAY__": m["fuentes"]["display"]["familia"],
        "__F_CUERPO__": m["fuentes"]["cuerpo"]["familia"],
        "__F_MONO__": m["fuentes"]["mono"]["familia"],
        "__MAYUS__": "text-transform: uppercase;" if m.get("titulos_en_mayusculas") else "",
        "__LOGO__": logo,
        "__TITULO__": titulo,
        "__ENTRADILLA__": html_mod.escape(entradilla),
        "__PIE__": html_mod.escape(pie),
        "__DATOS__": json.dumps(caps, ensure_ascii=False).replace("</", "<\\/"),
        "__DIAGRAMAS__": json.dumps(cfg["diagramas"]),
        "__TEMA__": json.dumps(tema),
        "__ENREDO__": (Path(__file__).with_name("enredo.js")).read_text(encoding="utf-8"),
    }
    out = PLANTILLA
    for k, v in rep.items():
        out = out.replace(k, v)
    return out


def pintar(nav, pagina: Path, salida: Path, pie: str, avisar: bool) -> dict:
    pag = nav.new_page()
    errores: list[str] = []
    pag.on("pageerror", lambda e: errores.append(str(e)))
    pag.goto(pagina.as_uri(), wait_until="networkidle")
    try:
        pag.wait_for_function("window.__listo === true", timeout=300_000)
    except Exception:
        abortar(f"{salida.name}: la página no terminó de pintarse (¿sin red para marked/mermaid?)")
    r = pag.evaluate("({fallos: __fallos, ilegibles: __ilegibles, densos: __densos, apaisados: __apaisados,"
                     " enredados: __enredados, liosos: __liosos, motores: __motores,"
                     " rotas: [...document.images].filter(i => !i.naturalWidth).map(i => i.src)})")
    for d in r["liosos"]:
        print(f"  aviso · lioso: {d}")
    for d in r["enredados"]:
        print(f"  {'aviso' if avisar else 'ERROR'} · enredado: {d}")
    if r["motores"]:
        print(f"  motor elegido: dagre ×{r['motores'].count('dagre')} · elk ×{r['motores'].count('elk')}")
    for d in r["densos"]:
        print(f"  aviso · denso: {d}")
    for d in r["apaisados"]:
        print(f"  apaisado: {d}")
    for d in r["ilegibles"]:
        print(f"  {'aviso' if avisar else 'ERROR'} · ilegible: {d}")
    if errores or r["fallos"] or r["rotas"] or ((r["ilegibles"] or r["enredados"]) and not avisar):
        nav.close()
        abortar(f"{salida.name}: errores={errores} diagramas={r['fallos']} ilegibles={len(r['ilegibles'])} enredados={len(r['enredados'])} "
                f"imágenes rotas={r['rotas']}")
    pag.wait_for_timeout(800)
    pag.pdf(path=str(salida), print_background=True, prefer_css_page_size=True, display_header_footer=True,
            header_template="<span></span>",
            footer_template='<div style="font:7pt sans-serif;color:#565E6E;width:100%;padding:0 16mm;'
                            'display:flex;justify-content:space-between">'
                            f'<span>{html_mod.escape(pie)}</span>'
                            '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    pag.close()
    print(salida)
    return r


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config")
    ap.add_argument("--separados", action="store_true")
    ap.add_argument("--html-solo", action="store_true")
    ap.add_argument("--avisar", action="store_true")
    a = ap.parse_args()

    raiz = raiz_git()
    cfg, carpeta = cargar_config(raiz, a.config)
    fecha = datetime.date.today().isoformat()
    version = subprocess.run(["git", "-C", str(raiz), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip() or "sin-git"
    caps = [(n, leer(c, raiz, cfg["sustituir"])) for n, c in enumerate(cfg["capitulos"], start=1)]
    tmp = carpeta / "_pdf"
    tmp.mkdir(exist_ok=True)
    nombre = cfg["marca"].get("nombre") or ""
    pie_doc = f"{nombre} · {re.sub('<[^>]+>', ' ', cfg['titulo'])}".strip(" ·")
    completo = tmp / "completo.html"
    completo.write_text(html(caps, cfg, raiz, cfg["titulo"], cfg["entradilla"],
                             f"{fecha} · versión {version} · uso interno"), encoding="utf-8")
    if a.html_solo:
        print(completo)
        return

    from playwright.sync_api import sync_playwright
    chrome = next((shutil.which(n) for n in ("google-chrome", "chromium-browser", "chromium") if shutil.which(n)), None)
    with sync_playwright() as p:
        nav = p.chromium.launch(headless=True, args=["--no-sandbox", "--allow-file-access-from-files"],
                                **({"executable_path": chrome} if chrome else {}))
        pintar(nav, completo, carpeta / f"{cfg['nombre_fichero']}.pdf", pie_doc, a.avisar)
        if a.separados:
            (carpeta / "pdf").mkdir(exist_ok=True)
            for (n, md), ruta in zip(caps, cfg["capitulos"]):
                mt = re.search(r"^# (.+)$", md, re.M)
                titulo = mt.group(1).strip() if mt else ruta.stem
                stem = ruta.stem if CAPITULO_NN.match(ruta.name) else f"{n:02d}-{ruta.stem}"
                pagina = tmp / f"{stem}.html"
                pagina.write_text(html([(n, md)], cfg, raiz, f'<span class="num">{n:02d}</span><br>{html_mod.escape(titulo)}',
                                       f"{pie_doc}. Capítulo suelto; la colección completa está en "
                                       f"«{cfg['nombre_fichero']}.pdf».", f"{fecha} · versión {version} · uso interno"),
                                  encoding="utf-8")
                pintar(nav, pagina, carpeta / "pdf" / f"{cfg['prefijo_capitulos']}-{stem}.pdf",
                       f"{pie_doc} · {n:02d} · {titulo}", a.avisar)
        nav.close()


if __name__ == "__main__":
    main()
