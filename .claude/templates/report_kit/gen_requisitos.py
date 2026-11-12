#!/usr/bin/env python3
"""requisitos.html — cada requisito con sus 11 apartados y su MÁQUINA DE ESTADOS de uso.

DE DÓNDE VIENE. Cosechado de `/home/proxera/accounting_AMC/scripts/gen_requisitos.py`, que el
Usuario señaló como modelo: *«está súper bien hecho, todo el tema de la máquina de estados, de
cómo está funcionando… esto se puede coger tal cual»*. Allí funciona y renderiza 7 requisitos.

EL CAMBIO QUE HABÍA QUE HACER AL COSECHARLO, y no es cosmético: aquel script lleva **los datos
dentro** (`REQUISITOS = [...]`, 762 líneas). Copiado tal cual, cada proyecto tendría que editar un
script de 762 líneas para escribir su producto. Aquí los datos viven en
`<plan>/arranque/requisitos.json` y el script solo dibuja.

LOS 11 APARTADOS: los 7 del original + los 4 que pidió el Usuario el 2026-09-12 (qué hace el
usuario · su entrada · su salida · ejemplos con datos reales). Molde:
`.claude/templates/requisito-template.md`.

    python3 gen_requisitos.py <dir-del-plan>
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

APARTADOS = [
    ("producto",  "Qué deja en las manos del usuario"),
    ("quien",     "Quién y cuándo"),
    ("hace",      "Qué hace el usuario"),
    ("entrada",   "Cuál es su entrada"),
    ("salida",    "Cuál es la salida"),
    ("como",      "Cómo se usa"),
    ("beneficio", "Qué beneficio tiene"),
    ("porque",    "Por qué se usa así y no de otra manera"),
    ("falta",     "Qué falta"),
]
TIPO_COLOR = {"inicio": "#7c3aed", "trabajo": "#2563eb", "fin": "#16803c", "problema": "#b91c1c"}


def shared() -> str:
    t = (HERE / "index.template.html").read_text(encoding="utf-8")
    m = re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", t, re.S)
    return m.group(0) if m else ""


def svg_estados(estados: dict, pasos: list) -> tuple[str, list]:
    """La máquina de estados. Layout por columnas declaradas; si no vienen, en cadena.

    El original de AMC traía las coordenadas puestas a mano. Aquí son opcionales: sin ellas se
    coloca por orden, que es peor pero no obliga a nadie a calcular posiciones para empezar.
    """
    avisos = []
    if not estados:
        return "", ["sin estados declarados"]
    ids = list(estados)
    pos, W, H = {}, 168, 62
    for i, k in enumerate(ids):
        e = estados[k]
        col = e.get("col", i % 4)
        fila = e.get("fila", i // 4)
        pos[k] = (col * (W + 100) + 12, fila * (H + 46) + 12)   # 100 y no 34: la etiqueta
        # de la transición tiene que caber ENTRE las cajas, no encima de ellas
    ancho = max(x for x, _ in pos.values()) + W + 12
    alto = max(y for _, y in pos.values()) + H + 34

    if not any(estados[k].get("tipo") == "fin" for k in ids):
        avisos.append("ningún estado FINAL: el trabajo no puede terminar nunca")

    g = []
    for (desde, hasta, que, quien) in [tuple(p)[:4] for p in pasos if len(p) >= 3]:
        if desde not in pos or hasta not in pos:
            avisos.append(f"paso {desde}→{hasta}: algún estado no existe")
            continue
        x1, y1 = pos[desde]; x2, y2 = pos[hasta]
        g.append(f'<path d="M{x1+W} {y1+H/2} C{x1+W+20} {y1+H/2}, {x2-20} {y2+H/2}, {x2} {y2+H/2}" '
                 f'fill="none" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#a)"/>'
                 if y1 == y2 else
                 f'<path d="M{x1+W/2} {y1+H} V{y1+H+20} H{x2+W/2} V{y2}" fill="none" '
                 f'stroke="#94a3b8" stroke-width="1.6" marker-end="url(#a)"/>')
        # La etiqueta va ENCIMA de la flecha y recortada: entre dos cajas adyacentes solo hay
        # 34 px, y un texto largo se metía dentro de la caja de al lado — el anti-pattern de
        # `plan-docs-structure.md` («líneas que cruzan por dentro de las cajas»). Se vio en la
        # captura, no leyendo el código.
        if que:
            # En la misma fila, la etiqueta va en el HUECO INMEDIATO a la derecha del origen,
            # no en el centro del recorrido: una transición que salta dos columnas tenía su
            # punto medio encima de la caja intermedia. Límite conocido y aceptado: dos
            # transiciones que salen del mismo estado y van a la derecha se pisan entre sí;
            # para eso se declaran `fila` distintas en el JSON.
            mx = (x1 + W + 50) if y1 == y2 else (x1 + x2 + W) / 2
            my = (y1 + H / 2) - 9 if y1 == y2 else (y1 + H + 14)
            txt = str(que)
            corto = txt if len(txt) <= 16 else txt[:15] + "…"
            g.append(f'<text x="{mx}" y="{my}" font-size="9.5" fill="#64748b" '
                     f'text-anchor="middle"><title>{html.escape(txt)}</title>'
                     f'{html.escape(corto)}</text>')
    for k, (x, y) in pos.items():
        e = estados[k]
        col = TIPO_COLOR.get(e.get("tipo", "trabajo"), "#64748b")
        g.append(f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="9" fill="#fff" '
                 f'stroke="{col}" stroke-width="2"/>'
                 f'<text x="{x+10}" y="{y+24}" font-size="12" font-weight="700" fill="{col}">'
                 f'{html.escape(str(e.get("label", k))[:24])}</text>'
                 f'<text x="{x+10}" y="{y+43}" font-size="10" fill="#64748b">'
                 f'{html.escape(e.get("tipo", "trabajo"))}</text>')
    return (f'<svg width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">'
            f'<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="3" '
            f'orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#94a3b8"/></marker></defs>'
            + "".join(g) + "</svg>", avisos)


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("uso: gen_requisitos.py <dir-del-plan>")
    plan = pathlib.Path(sys.argv[1]).resolve()
    f = plan / "arranque" / "requisitos.json"
    if not f.exists():
        print(f"· no hay {f.relative_to(plan)} — lo escribe /arrancar en su fase 1b.\n"
              f"  No se genera la página: un informe no enseña un ejemplo inventado.")
        return 0
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: requisitos.json no es JSON válido: {e.msg} (línea {e.lineno})")
    if d.get("_semilla"):
        print("· requisitos.json sigue siendo la SEMILLA — rellénala y quita `_semilla`.")
        return 0
    reqs = d.get("requisitos", [])
    if not reqs:
        print("· requisitos.json sin requisitos — no se genera"); return 0

    bloques, todos_avisos = [], []
    for i, r in enumerate(reqs, 1):
        rid = r.get("id", f"R-{i}")
        svg, avisos = svg_estados(r.get("estados", {}), r.get("pasos", []))
        todos_avisos += [f"{rid}: {a}" for a in avisos]

        aps = "".join(
            f'<div class="ap"><h4>{html.escape(lab)}</h4><p>{html.escape(str(r[k]))}</p></div>'
            for k, lab in APARTADOS if r.get(k))
        faltan = [lab for k, lab in APARTADOS if not r.get(k)]
        if faltan:
            todos_avisos.append(f"{rid}: sin rellenar — {', '.join(faltan[:3])}"
                                + ("…" if len(faltan) > 3 else ""))

        ejs = r.get("ejemplos", [])
        tabla = ("".join(f'<tr><td>{html.escape(str(e.get("situacion","")))}</td>'
                         f'<td>{html.escape(str(e.get("entra","")))}</td>'
                         f'<td>{html.escape(str(e.get("sale","")))}</td></tr>' for e in ejs))
        gher = r.get("gherkin", [])
        bloques.append(f"""<section class="req" data-id="{html.escape(rid)}">
<h3>{html.escape(rid)} · {html.escape(r.get('titulo', ''))}</h3>
<div class="aps">{aps}</div>
{'<h4>Ejemplos</h4><table><thead><tr><th>Situación</th><th>Entra</th><th>Sale</th></tr></thead><tbody>' + tabla + '</tbody></table>' if ejs else '<p class="falta">Sin ejemplos con datos reales — el apartado que más veces salva una discusión seis meses después.</p>'}
<h4>El recorrido, como máquina de estados</h4>
{'<div class="svgbox">' + svg + '</div>' if svg else '<p class="falta">Sin máquina de estados declarada.</p>'}
{'<h4>Criterios de aceptación</h4><ul>' + "".join(f'<li><code>{html.escape(str(g))}</code></li>' for g in gher) + '</ul>' if gher else '<p class="falta">Sin criterios en Gherkin — <code>spec_lint.py</code> E3 lo marcará.</p>'}
</section>""")

    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Requisitos y uso · {html.escape(plan.name)}</title>
<style>{shared()}
.wrap{{max-width:1100px;margin:0 auto;padding:20px}}
.req{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px;margin:16px 0}}
.aps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:12px 0}}
.ap h4{{margin:0 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:.4px;color:#64748b}}
.ap p{{margin:0;font-size:14px}}
.svgbox{{overflow-x:auto;border:1px solid #e2e8f0;border-radius:8px;padding:10px;background:#fafafa}}
.falta{{color:#a16207;background:#fef9c3;padding:8px 12px;border-radius:8px;font-size:13px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0}}
.avisos{{background:#fff7ed;border:1px solid #fdba74;border-radius:10px;padding:12px 14px;margin:14px 0;font-size:13px}}
</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
<h1>Los {len(reqs)} requisitos, y cómo se usa cada uno</h1>
<p class="sub">Cada uno con sus 11 apartados y su <b>máquina de estados de uso</b>: no «pulsa aquí
y luego allí», sino <b>en qué situación queda el trabajo</b>, qué lo mueve y dónde se atasca.</p>
{'<div class="avisos"><b>' + str(len(todos_avisos)) + ' avisos:</b><ul>' + "".join(f'<li>{html.escape(a)}</li>' for a in todos_avisos[:10]) + '</ul></div>' if todos_avisos else ''}
{"".join(bloques)}
</div></body></html>"""

    out = plan / "requisitos.html"
    out.write_text(doc, encoding="utf-8")
    print(f"OK {out}  ({len(reqs)} requisitos"
          + (f", {len(todos_avisos)} avisos" if todos_avisos else "") + ")")
    for a in todos_avisos[:5]:
        print(f"   ⚠ {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
