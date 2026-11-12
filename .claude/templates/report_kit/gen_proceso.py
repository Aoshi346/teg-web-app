#!/usr/bin/env python3
"""proceso.html — el proceso entero como MÁQUINA DE ESTADOS, y cada estado se abre.

POR QUÉ EXISTE. Petición del Usuario (2026-09-12): *«todo este proceso tiene que estar en una
máquina de estados […] y yo poder dar clic en cada uno de los estados para ver la documentación
correspondiente o la página correspondiente. Si le doy al diseño, puedo ver el diseño. Si hay
muchos, que tenga paginación o pueda filtrar.»*

QUÉ RESPONDE, y por qué no lo responde ninguna otra página:
  · `dashboard.html`  → qué hay que hacer y en qué estado está cada ITEM
  · `flujo.html`      → en qué ORDEN se ejecuta lo aprobado
  · `requisitos.html` → la máquina de estados de UN requisito, de cara al usuario
  · **esta**          → la máquina de estados del PROCESO de construir: dónde estamos, qué falta
                        para pasar de fase, y **se entra a cada artefacto desde su estado**

NO INVENTA NADA. Cada estado se colorea con lo que mide `flow_state.py` (que a su vez recalcula del
disco), y cada artefacto se lista solo si el fichero EXISTE. Un estado verde con cero artefactos es
imposible por construcción: si no hay documento, el gate no puede estar en verde.

    python3 gen_proceso.py <dir-del-plan>
"""
from __future__ import annotations

import html
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Los estados del proceso, en orden. `gate` los ata a lo que mide flow_state/gate_arranque;
# `busca` son los patrones de artefacto que se listan al pulsar (relativos a la raíz del repo).
ESTADOS = [
    ("encuadre",   "Encuadre",        "¿qué es y para quién?",        "prd",
     ["{plan}/arranque/00-encuadre.md"]),
    ("prd",        "PRD",             "el problema y el éxito",       "prd",
     ["{plan}/arranque/01-prd.md", ".docs/core/producto/01-product-brief.md"]),
    ("requisitos", "Requisitos",      "los 11 apartados + Gherkin",   "requisitos",
     ["{plan}/arranque/02-requisitos.md", "{plan}/requisitos.html"]),
    ("datos",      "Datos y flujos",  "el ERD de diseño",             "datos",
     ["{plan}/arranque/03-modelo-datos.md", "{plan}/arranque/04-flujos.md",
      "{plan}/data-model.html", "{plan}/user-flows.html", "{plan}/trazas.html"]),
    ("stack",      "Stack y ADR",     "con qué y por qué",            "stack",
     ["{plan}/arranque/05-stack.md", ".docs/adr/*.md", "{plan}/schemas/*.html"]),
    ("etica",      "Ética y RGPD",    "qué datos y con qué base legal", "etica",
     ["{plan}/arranque/06-etica-privacidad.md", ".docs/core/privacidad.md"]),
    ("seguridad",  "Superficie",      "por dónde entran, y las defensas", "seguridad",
     ["{plan}/arranque/07-superficie.md", ".docs/core/seguridad.md"]),
    ("marca",      "Marca",           "identidad · guía · kit",       None,
     ["{plan}/arranque/10-identidad.md", "{plan}/arranque/11-guia-marca.md",
      "{plan}/arranque/12-kit-marca/*", "{plan}/brand.html", ".docs/core/design-system.md"]),
    ("lowfi",      "Baja fidelidad",  "¿está bien organizado?",       None,
     ["{plan}/bocetos/*lowfi*.html", "{plan}/wireframes/*.html"]),
    ("highfi",     "Alta fidelidad",  "¿está bien resuelto?",         None,
     ["{plan}/bocetos/*.html", "{plan}/mockups/*.html"]),
    ("mockup",     "Mockup vivo",     "funciona con datos simulados", None,
     ["{plan}/mockups/*", "mocks/*/panel.html"]),
    # «Backend» era un nombre engañoso: después del mockup viene el DESARROLLO ENTERO — backend,
    # base de datos, y terminar el frontend de verdad, porque el mockup vive de datos simulados
    # con MSW y hay que conectarlo. El momento exacto de esa conexión es sustituir el `schema.yml`
    # de diseño por el que genera `manage.py spectacular` y regenerar los tipos: a partir de ahí
    # el frontend deja de hablar con el simulador y habla con el backend.
    ("desarrollo", "Desarrollo",      "backend · datos · frontend conectado", None,
     ["{plan}/architecture.html", "{plan}/structure.html", "{plan}/codigo.html",
      "{plan}/patron.html", "{plan}/entregas.html"]),
    ("qa",         "QA",              "auditores y doble evidencia",  None,
     ["{plan}/results.html", "{plan}/pruebas.html", "{plan}/feedback/**/REPORT.md"]),
]

COLOR = {"cumple": ("#16803c", "#dcfce7"), "no_cumple": ("#b91c1c", "#fee2e2"),
         "no_medible": ("#a16207", "#fef9c3"), "waived": ("#6b21a8", "#f3e8ff"),
         "pendiente": ("#64748b", "#f1f5f9")}


def shared() -> str:
    """El bloque CSS compartido, verbatim (rules/report-kit.md regla 5)."""
    import re
    t = (HERE / "index.template.html").read_text(encoding="utf-8")
    m = re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", t, re.S)
    return m.group(0) if m else ""


def medir(raiz: pathlib.Path) -> dict:
    """El estado de cada fase, DERIVADO. Si no se puede medir, se dice — no se pinta verde."""
    est = {}
    for script, flag in ((".claude/scripts/gate_arranque.py", "--json"),):
        p = raiz / script
        if not p.exists():
            continue
        try:
            r = subprocess.run([sys.executable, str(p), str(raiz), flag],
                               capture_output=True, text=True, timeout=90)
            if r.stdout.strip():
                for f in json.loads(r.stdout).get("fases", []):
                    est[f["fase"]] = f["estado"]
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
            pass          # sin medición → todo queda 'pendiente', que NO es verde
    return est


# Páginas que el report-kit GENERA SIEMPRE (build.py, con o sin datos) y plantillas del core con sus
# huecos sin rellenar. Se LISTAN —para poder abrirlas desde el estado— pero NO cuentan como material:
# medido el 2026-09-14 en un proyecto recién montado y sin una línea escrita, «Marca», «Desarrollo» y
# «QA» salían con 1, 5 y 2 artefactos (design-system.md de plantilla, structure/architecture/results/
# pruebas generados vacíos) y el tablero decía «hay material sin verificar» de lo que no existía.
_GENERADAS_SIEMPRE = {"results.html", "pruebas.html", "structure.html", "architecture.html",
                      "data-model.html", "user-flows.html", "trazas.html", "requisitos.html",
                      "codigo.html", "patron.html", "entregas.html", "stack.html", "schemas.html"}


def es_material(a: dict) -> bool:
    """Un artefacto cuenta como material si alguien lo produjo a propósito: ni una página que el kit
    genera de oficio, ni una plantilla con [PERSONALIZAR] dentro."""
    return not a.get("generada") and not a.get("plantilla")


def estado_sin_gate(arts: list[dict]) -> str:
    """Sin gate que lo compruebe, tener material NO es «cerrado»: es «hay material y nadie lo ha
    verificado» (no_medible), que JAMÁS cuenta como verde. Sin material: pendiente."""
    return "no_medible" if any(es_material(a) for a in arts) else "pendiente"


def artefactos(raiz: pathlib.Path, plan: pathlib.Path, patrones: list[str]) -> list[dict]:
    out, vistos = [], set()
    for pat in patrones:
        pat = pat.replace("{plan}", str(plan.relative_to(raiz)))
        for f in sorted(raiz.glob(pat)):
            if not f.is_file() or f in vistos:
                continue
            vistos.add(f)
            # Un PLACEHOLDER no es un artefacto. `gen_placeholders.py` genera la pestaña vacía
            # en TODOS los planes, así que contarla haría que «QA» y «Backend» salieran con
            # material sin que nadie haya hecho ni una ronda ni escrito una línea. Lo encontré
            # mirando el screenshot: tres estados en verde sin haberse hecho.
            if f.suffix == ".html":
                try:
                    if "gen_placeholders" in f.read_text(encoding="utf-8", errors="replace")[:4000]:
                        continue
                except OSError:
                    continue
            rel = f.relative_to(raiz)
            plantilla = False
            if f.suffix == ".md":
                try:
                    plantilla = "[PERSONALIZAR" in f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    plantilla = False
            out.append({"nombre": f.name, "ruta": str(rel),
                        "href": str(pathlib.os.path.relpath(f, plan)),
                        "kb": max(1, f.stat().st_size // 1024),
                        "tipo": "página" if f.suffix == ".html" else "documento",
                        "generada": f.suffix == ".html" and f.name in _GENERADAS_SIEMPRE,
                        "plantilla": plantilla})
    return out


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("uso: gen_proceso.py <dir-del-plan>")
    plan = pathlib.Path(sys.argv[1]).resolve()
    r = subprocess.run(["git", "-C", str(plan), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    raiz = pathlib.Path(r.stdout.strip()) if r.returncode == 0 else plan.parents[2]

    medido = medir(raiz)
    datos = []
    for eid, label, sub, gate, pats in ESTADOS:
        arts = artefactos(raiz, plan, pats)
        # Sin gate que lo compruebe, tener ficheros NO es «cerrado»: es «hay material y nadie
        # lo ha verificado», que en el vocabulario de `rules/verification.md` es no_medible — y
        # no_medible JAMÁS cuenta como verde. Pintarlo de verde sería el falso positivo que este
        # trabajo entero existe para evitar, y en la primera captura pasó: marca, backend y QA
        # salieron cerrados sin haberse tocado.
        est = medido.get(gate, "pendiente") if gate else estado_sin_gate(arts)
        datos.append({"id": eid, "label": label, "sub": sub, "estado": est,
                      "gate": gate, "artefactos": arts})

    hechos = sum(1 for d in datos if d["estado"] == "cumple")
    actual = next((d for d in datos if d["estado"] != "cumple"), None)

    nodos, W, GAP = [], 172, 22
    for i, d in enumerate(datos):
        col, fila = i % 5, i // 5
        nodos.append({**d, "x": col * (W + GAP) + 10, "y": fila * 118 + 10})
    alto = ((len(datos) - 1) // 5 + 1) * 118 + 20
    ancho = 5 * (W + GAP) + 10

    svg = []
    for i, n in enumerate(nodos):
        borde, fondo = COLOR[n["estado"]]
        if i + 1 < len(nodos):
            a, b = n, nodos[i + 1]
            if a["y"] == b["y"]:
                svg.append(f'<line x1="{a["x"]+W}" y1="{a["y"]+44}" x2="{b["x"]}" '
                           f'y2="{b["y"]+44}" stroke="#cbd5e1" stroke-width="2" '
                           f'marker-end="url(#f)"/>')
            else:   # salto de fila: baja por el pasillo de la derecha, no cruza las cajas
                svg.append(f'<path d="M{a["x"]+W/2} {a["y"]+88} V{a["y"]+104} H{b["x"]+W/2} '
                           f'V{b["y"]}" fill="none" stroke="#cbd5e1" stroke-width="2" '
                           f'marker-end="url(#f)"/>')
        n_art = sum(1 for a in n["artefactos"] if es_material(a))
        svg.append(
            f'<g class="nodo" data-id="{n["id"]}" style="cursor:pointer">'
            f'<rect x="{n["x"]}" y="{n["y"]}" width="{W}" height="88" rx="10" fill="{fondo}" '
            f'stroke="{borde}" stroke-width="2"/>'
            f'<text x="{n["x"]+12}" y="{n["y"]+26}" font-size="14" font-weight="700" '
            f'fill="{borde}">{html.escape(n["label"])}</text>'
            f'<text x="{n["x"]+12}" y="{n["y"]+46}" font-size="11" fill="#475569">'
            f'{html.escape(n["sub"][:30])}</text>'
            f'<text x="{n["x"]+12}" y="{n["y"]+70}" font-size="11" fill="{borde}" '
            f'font-weight="600">{n_art} artefacto{"s" if n_art != 1 else ""}</text></g>')

    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>El proceso · {html.escape(plan.name)}</title>
<style>{shared()}
.wrap{{max-width:1180px;margin:0 auto;padding:20px}}
.svgbox{{overflow-x:auto;background:#fff;border:1px solid var(--bd,#e2e8f0);border-radius:12px;padding:12px}}
.nodo:hover rect{{filter:brightness(.96)}}
.panel{{margin-top:18px;background:#fff;border:1px solid var(--bd,#e2e8f0);border-radius:12px;padding:16px}}
.art{{display:flex;justify-content:space-between;align-items:center;padding:9px 12px;
 border:1px solid #e2e8f0;border-radius:8px;margin:6px 0}}
.art a{{font-weight:600;text-decoration:none}}
.vacio{{color:#64748b;font-style:italic;padding:10px 0}}
.pag{{display:flex;gap:6px;margin-top:10px;align-items:center}}
.pag button{{padding:4px 10px;border:1px solid #cbd5e1;background:#fff;border-radius:6px;cursor:pointer}}
input.f{{width:100%;padding:8px 10px;border:1px solid #cbd5e1;border-radius:8px;margin:8px 0}}
.ley{{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;margin:10px 0;color:#475569}}
.ley i{{width:12px;height:12px;border-radius:3px;display:inline-block;margin-right:5px;vertical-align:-1px}}
</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
<h1>El proceso, como máquina de estados</h1>
<p class="sub">Dónde estamos, qué falta para pasar de fase, y <b>se entra a cada artefacto pulsando
su estado</b>. Los colores no se declaran: los mide <code>gate_arranque.py</code> recalculando del
disco. Verde = un gate lo comprobó. Ámbar = hay material y <b>nadie lo ha verificado</b>: tener ficheros no es haberlo hecho.</p>
<p><b>{hechos} de {len(datos)}</b> estados cerrados ·
{"ahora: <b>" + html.escape(actual["label"]) + "</b>" if actual else "<b>proceso completo</b>"}</p>
<div class="ley">
 <span><i style="background:#dcfce7;border:1px solid #16803c"></i>cerrado</span>
 <span><i style="background:#fee2e2;border:1px solid #b91c1c"></i>incompleto</span>
 <span><i style="background:#fef9c3;border:1px solid #a16207"></i>hay material, sin verificar</span>
 <span><i style="background:#f1f5f9;border:1px solid #64748b"></i>sin empezar</span>
</div>
<div class="svgbox"><svg width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">
<defs><marker id="f" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
<path d="M0,0 L0,6 L8,3 z" fill="#cbd5e1"/></marker></defs>
{"".join(svg)}
</svg></div>
<div class="panel" id="panel"><div class="vacio">Pulsa un estado para ver su documentación.</div></div>
</div>
<script>
const D = {json.dumps(datos, ensure_ascii=False)};
const POR_PAG = 8;
let sel = null, pag = 0, filtro = "";
function pinta(){{
  const p = document.getElementById('panel');
  if(!sel){{ return; }}
  const d = D.find(x => x.id === sel);
  let arts = d.artefactos.filter(a => !filtro || a.nombre.toLowerCase().includes(filtro)
                                   || a.ruta.toLowerCase().includes(filtro));
  const tot = arts.length, paginas = Math.max(1, Math.ceil(tot / POR_PAG));
  if(pag >= paginas) pag = paginas - 1;
  const vis = arts.slice(pag * POR_PAG, (pag + 1) * POR_PAG);
  let h = `<h2>${{d.label}} — ${{d.sub}}</h2>`;
  h += `<p class="sub">estado: <b>${{d.estado.replace('_',' ')}}</b>` +
       (d.gate ? ` · lo mide <code>gate_arranque.py --fase ${{d.gate}}</code>` : '') + `</p>`;
  if(d.artefactos.length > POR_PAG)
    h += `<input class="f" placeholder="filtrar entre ${{d.artefactos.length}} artefactos…"
          value="${{filtro}}" oninput="filtro=this.value.toLowerCase();pag=0;pinta()">`;
  if(!tot) h += `<div class="vacio">Sin artefactos todavía.` +
    (d.gate ? ` Lo genera <code>/arrancar</code> en su fase <b>${{d.gate}}</b>.` : '') + `</div>`;
  vis.forEach(a => {{
    h += `<div class="art"><a href="${{a.href}}" target="_blank">${{a.nombre}}</a>` +
         `<span class="sub">${{a.tipo}}${{a.generada ? ' · generada por el kit (sin datos propios todavía)' : ''}}${{a.plantilla ? ' · plantilla sin rellenar' : ''}} · ${{a.kb}} KB · <code>${{a.ruta}}</code></span></div>`;
  }});
  if(paginas > 1){{
    h += `<div class="pag"><button onclick="pag=Math.max(0,pag-1);pinta()">‹</button>` +
         `<span class="sub">página ${{pag+1}} de ${{paginas}} · ${{tot}} artefactos</span>` +
         `<button onclick="pag=Math.min(${{paginas-1}},pag+1);pinta()">›</button></div>`;
  }}
  p.innerHTML = h;
}}
document.querySelectorAll('.nodo').forEach(n => n.addEventListener('click', () => {{
  sel = n.dataset.id; pag = 0; filtro = ""; pinta();
  document.getElementById('panel').scrollIntoView({{behavior:'smooth', block:'nearest'}});
}}));
</script></body></html>"""

    out = plan / "proceso.html"
    out.write_text(doc, encoding="utf-8")
    print(f"OK {out}  ({hechos}/{len(datos)} estados cerrados, "
          f"{sum(len(d['artefactos']) for d in datos)} artefactos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
