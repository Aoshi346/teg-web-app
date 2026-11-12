#!/usr/bin/env python3
"""trazas.html — el viaje del dato, capa por capa, con cuatro zooms.

POR QUÉ EXISTE. Petición del Usuario (2026-09-12): *«quiero ver gráficos de todo, no de
arquitectura. El usuario envía esto · el frontend recibe esto · mediante Axios habla con el backend
y le dice esto · el backend lo procesa, lo guarda en Postgres y devuelve la respuesta · el frontend
con su store global lo actualiza y se transforma en esto. Como si le preguntara a un junior «¿cómo
funciona esto?» y me lo contara sin tener que ver el código.»*

QUÉ NO LO CUBRÍA, medido antes de escribir esto:
  · `architecture.html` → módulos y dependencias. No sigue un dato.
  · `data-model.html`   → entidades y relaciones. Estructura, no recorrido.
  · `user-flows.html`   → pantallas paso a paso. Se queda en la UI: no cruza a la API.
  · `requisitos.html`   → en qué ESTADO queda el trabajo. No por qué capas pasó.
  · `flujo.html`        → en qué orden lo construimos NOSOTROS. Plan, no runtime.

LOS CUATRO ZOOMS que pidió: global · módulo · requisito · bloque de pantalla.

FUENTE: `<plan>/arranque/trazas.json` — lo rellena `/arrancar` en su fase 2 (diseño) y lo puede
enriquecer `/code-graph` (construido). Dos productores, un contrato, como el ERD.

    python3 gen_trazas.py <dir-del-plan>
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Las capas del viaje, en orden. El color no es decorativo: agrupa por dónde vive el salto.
CAPAS = [
    ("usuario",  "Usuario",        "#7c3aed"),
    ("pantalla", "Pantalla",       "#2563eb"),
    ("estado",   "Store / estado", "#0891b2"),
    ("red",      "Red (HTTP)",     "#059669"),
    ("vista",    "Vista / API",    "#ca8a04"),
    ("servicio", "Servicio",       "#ea580c"),
    ("datos",    "Base de datos",  "#be123c"),
    ("externo",  "Sistema externo", "#475569"),
]
CAPA_COLOR = {c: col for c, _, col in CAPAS}
CAPA_NOMBRE = {c: n for c, n, _ in CAPAS}

EJEMPLO = {
    "_semilla": True,   # lo quita quien la rellene; mientras esté, NO se publica
    "_doc": ("Cada traza es UN recorrido completo de un dato. Los saltos van EN ORDEN. "
             "`estado`: construido | disenado (previsto y aún no escrito). "
             "Se rellena en /arrancar fase 2 y se enriquece con /code-graph."),
    "trazas": [{
        "id": "alta-cliente", "titulo": "Dar de alta un cliente",
        "modulo": "clientes", "requisito": "R-1", "bloque": "Botón «Guardar» del alta",
        "saltos": [
            {"capa": "usuario", "quien": "La recepcionista", "que": "rellena nombre y NIF y pulsa Guardar",
             "hacia": "el formulario", "devuelve": "", "guarda": "", "estado": "construido", "ref": ""},
            {"capa": "pantalla", "quien": "ClienteForm.tsx", "que": "valida con zod y llama a la mutación",
             "hacia": "useCrearCliente", "devuelve": "errores por campo si no valida",
             "guarda": "", "estado": "construido", "ref": "src/features/clientes/components/ClienteForm.tsx:48"},
            {"capa": "red", "quien": "axios", "que": "POST /api/clientes/ con {nombre, nif}",
             "hacia": "el backend", "devuelve": "201 con el cliente creado · 400 con errores",
             "guarda": "", "estado": "construido", "ref": "src/api/clientes.ts:22"},
            {"capa": "vista", "quien": "ClienteViewSet.create", "que": "valida el serializer y llama al servicio",
             "hacia": "servicios.crear_cliente", "devuelve": "400 si el NIF ya existe",
             "guarda": "", "estado": "construido", "ref": "apps/clientes/views.py:60"},
            {"capa": "datos", "quien": "Postgres", "que": "INSERT en clientes",
             "hacia": "", "devuelve": "la fila con su id", "guarda": "cliente (nombre, nif, creado_por)",
             "estado": "construido", "ref": "apps/clientes/models.py:18"},
            {"capa": "estado", "quien": "TanStack Query", "que": "invalida la lista y la recarga",
             "hacia": "la tabla", "devuelve": "", "guarda": "caché de clientes",
             "estado": "construido", "ref": "src/features/clientes/hooks/useClientes.ts:31"},
        ]}]
}


def shared() -> str:
    t = (HERE / "index.template.html").read_text(encoding="utf-8")
    m = re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", t, re.S)
    return m.group(0) if m else ""


def duplicados(trazas: list[dict]) -> list[dict]:
    """Dos bloques distintos cuyo recorrido acaba en el mismo endpoint y verbo.

    Es el caso que nombró el Usuario —«si lo duplicaba un botón»— y no se ve leyendo el código:
    los dos componentes son correctos por separado. Aquí salta solo.
    """
    por_destino: dict[str, list[dict]] = {}
    for t in trazas:
        for s in t.get("saltos", []):
            if s.get("capa") != "red":
                continue
            m = re.search(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(\S+)", s.get("que", ""), re.I)
            if m:
                por_destino.setdefault(f"{m.group(1).upper()} {m.group(2)}", []).append(
                    {"traza": t.get("titulo", t.get("id")), "bloque": t.get("bloque", "—")})
    return [{"destino": k, "usos": v} for k, v in por_destino.items() if len(v) > 1]


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("uso: gen_trazas.py <dir-del-plan>")
    plan = pathlib.Path(sys.argv[1]).resolve()
    f = plan / "arranque" / "trazas.json"

    if not f.exists():
        # No se inventa un ejemplo y se publica: eso es lo que hizo que dos informes enseñaran
        # un proyecto Django que no existía. Se deja la semilla y se dice.
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(EJEMPLO, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"· no había {f.relative_to(plan)} — escrita la SEMILLA con un recorrido de ejemplo.\n"
              f"  Rellénala en /arrancar fase 2 y vuelve a correr esto. NO se genera la página con\n"
              f"  el ejemplo dentro: un informe no enseña datos inventados.")
        return 0

    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: trazas.json no es JSON válido: {e.msg} (línea {e.lineno})")
    if d.get("_semilla"):
        # La semilla que este mismo script escribe la leería el siguiente run como si fuera real
        # y publicaría el ejemplo inventado — exactamente el fallo que costó dos informes
        # enseñando un proyecto Django que no existía. Se quita la marca al rellenarla.
        print(f"· {f.relative_to(plan)} sigue siendo la SEMILLA (lleva `_semilla: true`).\n"
              f"  Rellénala con los recorridos reales y quita esa línea. No se publica un ejemplo.")
        return 0
    trazas = [t for t in d.get("trazas", []) if t.get("saltos")]
    if not trazas:
        print("· trazas.json sin recorridos — no se genera la página"); return 0

    dups = duplicados(trazas)
    n_dis = sum(1 for t in trazas for s in t["saltos"] if s.get("estado") == "disenado")
    modulos = sorted({t.get("modulo", "—") for t in trazas})

    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recorridos · {html.escape(plan.name)}</title>
<style>{shared()}
.wrap{{max-width:1180px;margin:0 auto;padding:20px}}
.filtros{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:14px 0}}
.filtros select,.filtros input{{padding:7px 10px;border:1px solid #cbd5e1;border-radius:8px}}
.traza{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin:14px 0}}
.meta{{font-size:12px;color:#64748b;margin-bottom:10px}}
.meta b{{color:#334155}}
.salto{{display:grid;grid-template-columns:120px 1fr;gap:12px;padding:10px 0;
 border-top:1px dashed #e2e8f0}}
.capa{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;padding-top:2px}}
.q{{font-weight:600}}
.det{{font-size:13px;color:#475569;margin-top:3px}}
.det code{{font-size:12px}}
.dis{{background:#fef9c3;border-left:3px solid #a16207;padding-left:9px;margin-left:-12px}}
.aviso{{background:#fff7ed;border:1px solid #fdba74;border-radius:10px;padding:12px 14px;margin:14px 0}}
.pill{{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;
 background:#f1f5f9;color:#475569;margin-left:6px}}
</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
<h1>Recorridos: el viaje del dato</h1>
<p class="sub">Qué envía el usuario, qué recibe la pantalla, qué pide al backend, qué se guarda y
qué vuelve. <b>Sin abrir el código</b> — pero con la línea exacta al lado, por si quieres.
Los saltos en <span style="background:#fef9c3;padding:1px 5px">ámbar</span> están
<b>diseñados y aún NO construidos</b>.</p>

<div class="filtros">
  <label>Zoom
  <select id="z" onchange="pinta()">
    <option value="global">Global — todos los recorridos</option>
    <option value="modulo">Por módulo</option>
    <option value="requisito">Por requisito</option>
    <option value="bloque">Por bloque de pantalla</option>
  </select></label>
  <select id="v" onchange="pinta()"></select>
  <input id="q" placeholder="buscar en los saltos…" oninput="pinta()">
  <span class="sub" id="cuenta"></span>
</div>

{'<div class="aviso"><b>' + str(len(dups)) + ' endpoint(s) alcanzados desde más de un sitio.</b> '
 'No siempre es un error —una lista y un buscador pueden compartir el mismo GET— pero es el caso '
 'que nadie ve leyendo el código, porque cada bloque es correcto por separado:<ul>'
 + "".join(f'<li><code>{html.escape(x["destino"])}</code> ← '
           + " · ".join(html.escape(f'{u["traza"]} ({u["bloque"]})') for u in x["usos"]) + '</li>'
           for x in dups) + '</ul></div>' if dups else ''}
{'<div class="aviso"><b>' + str(n_dis) + ' saltos diseñados y aún no construidos.</b> '
 'Salen en ámbar dentro de su recorrido.</div>' if n_dis else ''}

<div id="out"></div>
</div>
<script>
const T = {json.dumps(trazas, ensure_ascii=False)};
const COLOR = {json.dumps(CAPA_COLOR, ensure_ascii=False)};
const NOMBRE = {json.dumps(CAPA_NOMBRE, ensure_ascii=False)};
const esc = s => (s||"").replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}})[c]);

function opciones(){{
  const z = document.getElementById('z').value, v = document.getElementById('v');
  if(z === 'global'){{ v.style.display = 'none'; return; }}
  v.style.display = '';
  const vals = [...new Set(T.map(t => t[z] || '—'))].sort();
  const prev = v.value;
  v.innerHTML = vals.map(x => `<option>${{esc(x)}}</option>`).join('');
  if(vals.includes(prev)) v.value = prev;
}}
function pinta(){{
  opciones();
  const z = document.getElementById('z').value, v = document.getElementById('v').value;
  const q = document.getElementById('q').value.toLowerCase();
  let vis = z === 'global' ? T : T.filter(t => (t[z] || '—') === v);
  if(q) vis = vis.filter(t => JSON.stringify(t).toLowerCase().includes(q));
  document.getElementById('cuenta').textContent =
    `${{vis.length}} de ${{T.length}} recorridos`;
  document.getElementById('out').innerHTML = vis.map(t => {{
    const saltos = t.saltos.map((s, i) => {{
      const col = COLOR[s.capa] || '#64748b';
      const det = [];
      if(s.hacia)    det.push(`→ <b>${{esc(s.hacia)}}</b>`);
      if(s.devuelve) det.push(`devuelve: ${{esc(s.devuelve)}}`);
      if(s.guarda)   det.push(`guarda: <b>${{esc(s.guarda)}}</b>`);
      if(s.ref)      det.push(`<code>${{esc(s.ref)}}</code>`);
      return `<div class="salto ${{s.estado === 'disenado' ? 'dis' : ''}}">
        <div class="capa" style="color:${{col}}">${{i+1}}. ${{esc(NOMBRE[s.capa] || s.capa)}}</div>
        <div><div class="q">${{esc(s.quien)}} — ${{esc(s.que)}}</div>
        ${{det.length ? `<div class="det">${{det.join(' · ')}}</div>` : ''}}</div></div>`;
    }}).join('');
    return `<div class="traza"><h2>${{esc(t.titulo || t.id)}}</h2>
      <div class="meta">módulo <b>${{esc(t.modulo||'—')}}</b>
        <span class="pill">${{esc(t.requisito||'sin requisito')}}</span>
        <span class="pill">${{esc(t.bloque||'—')}}</span>
        <span class="pill">${{t.saltos.length}} saltos</span></div>
      ${{saltos}}</div>`;
  }}).join('') || '<p class="sub">Ningún recorrido con ese filtro.</p>';
}}
pinta();
</script></body></html>"""

    out = plan / "trazas.html"
    out.write_text(doc, encoding="utf-8")
    print(f"OK {out}  ({len(trazas)} recorridos, "
          f"{sum(len(t['saltos']) for t in trazas)} saltos, {len(modulos)} módulos"
          + (f", {len(dups)} endpoints compartidos" if dups else "") + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
