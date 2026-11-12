#!/usr/bin/env python3
"""gen_core_hub.py (report-kit) — la página HUB del grupo Core de un informe.

NOMBRE (2026-10-19, LI-11): se llamaba `gen_core.py`, igual que `.claude/scripts/gen_core.py`,
que hace otra cosa (el índice de la doc viva `.docs/core/index.html`). Dos scripts con el mismo
nombre y funciones distintas: ahora este lleva el sufijo de sus hermanos (`gen_core_capas.py`,
`gen_core_patrones.py`…).

QUÉ RESPONDE. El resto del informe trata de lo que hay que HACER; el Core trata de lo que el
sistema ES. Cinco capas, de lo resumido a lo detallado: qué hace · cómo está construido · qué datos
maneja · cómo se usa · qué se decidió y por qué.

POR QUÉ ES UNA PÁGINA GENERADA Y NO ESCRITA. Porque su trabajo es decir la VERDAD sobre qué
documentación existe hoy, y eso cambia con cada comando que se corre. Un índice escrito a mano
empieza a mentir en cuanto alguien genera un mapa nuevo o borra uno viejo — que es exactamente el
fallo que `rules/plan-docs-structure.md` existe para evitar.

LA REGLA QUE LA HACE ÚTIL: una capa sin datos NO se deja en blanco. Dice **con qué comando se
consigue**. Una página vacía parece un informe roto; una página que te dice qué teclear es una
instrucción.
"""
import html, json, os, re, subprocess, sys
from datetime import date

CAPAS = [
    dict(id="overview", n="1", label="Qué hace este sistema",
         que="El resumen en una pantalla: a quién sirve, qué resuelve y de qué se compone.",
         origen="escrito", pagina="core-overview.html", como="Se escribe a mano y se fecha."),
    dict(id="structure", n="2", label="Cómo está construido",
         que="El grafo real del código: módulos, quién llama a quién, acoplamiento y candidatos a deuda.",
         origen="generado", pagina="structure.html",
         como="<code>/code-graph</code> para el grafo del código · <code>graphify_to_dataset.py</code> si el proyecto usa graphify · <code>gen_harness_graph.py --root &lt;proyecto&gt;</code> si lo que se mapea es el <code>.claude/</code>"),
    dict(id="architecture", n="2b", label="Arquitectura",
         que="Componentes y dependencias, con el camino caliente marcado.",
         origen="generado", pagina="core-arquitectura.html", como="<code>/visual-map</code>"),
    dict(id="data", n="3", label="Qué datos maneja",
         que="Entidades, relaciones y por dónde entran y salen los datos.",
         origen="generado", pagina="core-datos.html", como="<code>/visual-map</code>"),
    dict(id="flows", n="4", label="Cómo se usa",
         que="Los recorridos de usuario paso a paso, con su pantalla y su endpoint.",
         origen="generado", pagina="user-flows.html", como="<code>/visual-map</code>"),
    dict(id="schemas", n="4b", label="Esquemas de negocio",
         que="Lean canvas, casos de uso, historias de usuario: lo que no sale del código.",
         origen="escrito", pagina="schemas/index.html", como="<code>/schema &lt;id&gt;</code>"),
    dict(id="flujo", n="5", label="El flujo de trabajo y sus paradas",
         que="En qué orden se hacen las cosas y <b>en qué momentos para y espera a una persona</b>: gate determinista, aprobación o escalado por incertidumbre.",
         origen="escrito", pagina="core-flujo.html",
         como="Se deriva de las rules del proyecto. Hoy los puntos de parada viven en 14 ficheros distintos."),
    dict(id="adr", n="6", label="Qué se decidió y por qué",
         que="Las decisiones caras de revertir, con su contexto y sus alternativas descartadas.",
         origen="escrito", pagina="core-decisiones.html",
         como="<code>cp .claude/templates/adr-template.md .docs/adr/000N-&lt;slug&gt;.md</code> (Gate D)"),
    dict(id="levels", n="7", label="El harness por niveles",
         que="Todo el sistema en diagramas que se abren: la sesión → las capas → sus familias → cada pieza, y un proyecto de ejemplo de «empieza» a producción.",
         origen="generado", pagina="core-levels.html",
         como="<code>gen_harness_graph.py</code> y <code>gen_core_levels.py &lt;plan&gt; --out .docs/core</code>"),
]

def sha_de(plan):
    try:
        return subprocess.run(["git", "-C", plan, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or "—"
    except Exception:
        return "—"

def build(plan):
    meta = {}
    rp = os.path.join(plan, "report.json")
    if os.path.exists(rp):
        meta = json.load(open(rp, encoding="utf-8")).get("meta", {})
    # PV-3 · dos sitios distintos, y el hub tiene que saber cuál es cuál. Las capas del Core
    # (core-*.html) viven junto a este hub en .docs/core/; las demás (structure, user-flows,
    # schemas) son páginas DEL PLAN. Cuando el hub se escribe en el core, esas necesitan
    # ../plans/<plan>/ — y esa misma ruta vale servida, porque server.py monta /plans/.
    fuera = _out_dir(plan) != plan
    def _donde(pag):
        """(ruta en disco para comprobar si existe, href para el enlace)."""
        if pag.startswith("core-") or not fuera:
            return os.path.join(_out_dir(plan) if pag.startswith("core-") else plan, pag), pag
        return os.path.join(plan, pag), f"../plans/{os.path.basename(plan)}/{pag}"

    filas, hay, faltan = [], 0, 0
    for c in CAPAS:
        disco, enlace = _donde(c["pagina"]) if c["pagina"] else ("", "")
        existe = bool(c["pagina"]) and os.path.exists(disco)
        hay += existe; faltan += (not existe)
        badge = ('<span class="ok">disponible</span>' if existe
                 else '<span class="no">sin datos todavía</span>')
        titulo = (f'<a href="{enlace}">{html.escape(c["label"])}</a>' if existe
                  else html.escape(c["label"]))
        accion = ("" if existe else
                  f'<div class="como"><b>Cómo se consigue:</b> {c["como"]}</div>')
        filas.append(f'''<tr class="{'si' if existe else 'nope'}">
      <td class="num">{c["n"]}</td>
      <td><div class="t">{titulo}</div><div class="q">{c["que"]}</div>{accion}</td>
      <td class="or">{c["origen"]}</td>
      <td>{badge}</td></tr>''')

    proyecto = html.escape(str(meta.get("project", "")))
    plan_id = html.escape(str(meta.get("plan_id", "")))
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Core — {proyecto}</title>
<style>
/* SHARED:BEGIN */
  :root{{
    --ink:#1b1b1f;--muted:#6b6b76;--faint:#6c6c78;--paper:#f6f4ef;--card:#fff;--line:#e4e0d7;
    --navy:#1b2a4a;--accent:#c2410c;--green:#15803d;--amber:#b45309;--blue:#1d4ed8;--red:#b42318;
    --radius-sm:6px;--radius-md:10px;--radius:14px;--radius-pill:999px;
    --shadow-modal:0 20px 60px rgba(27,27,31,.28);
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --s-backlog:#6b6b76;--s-doing:#b45309;--s-review:#1d4ed8;--s-done:#15803d;--s-blocked:#b42318;
    --d-aprobar:#15803d;--d-modificar:#1d4ed8;--d-aplazar:#b45309;--d-descartar:#b42318;
  }}
  *{{box-sizing:border-box}}
  h1{{font-size:clamp(24px,3.6vw,38px);margin:0 0 10px;letter-spacing:-.02em;color:var(--ink)}}
  h1 em{{font-style:italic;color:var(--navy)}}
  .eyebrow{{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0 0 10px}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}
  .kpi{{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px}}
  .kpi b{{display:block;font-size:28px;font-weight:700;letter-spacing:-.02em;color:var(--navy);line-height:1.15}}
  .kpi span{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}}
  .kpi.warn b{{color:var(--red)}}
  .badge{{display:inline-block;font-size:11px;font-weight:700;padding:3px 10px;border-radius:var(--radius-pill);color:#fff;text-transform:uppercase;letter-spacing:.04em}}
  .nodata{{max-width:560px;margin:80px auto;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:28px 32px;text-align:center}}
  .nodata code{{font-family:var(--mono);font-size:.9em;background:#efece4;color:var(--navy);padding:2px 6px;border-radius:6px}}
  .icon{{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;vertical-align:-2px}}
  .demo-banner{{display:flex;align-items:center;gap:8px;background:#fdf3e3;border:1px solid #eed9b0;border-radius:var(--radius-sm);padding:8px 14px;margin:14px 0 0;font-size:12.5px;color:#78350f}}
  .demo-banner .icon{{flex:none}}
  .demo-banner[hidden]{{display:none}}  /* [hidden] pierde ante .demo-banner{{display:flex}} — sin esto el banner de demo sale SIEMPRE */
  .audience-note{{display:flex;align-items:center;gap:8px;background:#eef1f5;border:1px solid #d7dee8;border-radius:var(--radius-sm);padding:8px 14px;margin:12px 0 0;font-size:12.5px;color:var(--navy)}}
  .audience-note .icon{{flex:none}}
  .scroll-hint{{display:none;font-size:11px;color:var(--faint);text-align:right;margin:0 0 6px}}
  @media(max-width:767px){{.scroll-hint{{display:block}}}}
  /* nav responsive: la gestiona el bloque que inyecta render_nav.py (fuente única) */
  /* SHARED:END */
</style>
<style>
  html,body{{margin:0;background:var(--paper,#f6f4ef);color:var(--ink,#1b1b1f);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:15.5px;line-height:1.6}}
  .wrap{{max-width:1080px;margin:0 auto;padding:26px 20px 60px}}
  .eyebrow{{font-family:ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent,#c2410c);font-weight:700}}
  h1{{margin:6px 0 8px;font-size:30px;letter-spacing:-.02em;color:var(--navy,#1b2a4a)}}
  .lead{{color:var(--muted,#6b6b76);max-width:70ch;margin:0 0 6px}}
  .kpis{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 6px}}
  .kpi{{background:var(--card,#fff);border:1px solid var(--line,#e4e0d7);border-radius:12px;padding:10px 14px}}
  .kpi b{{display:block;font-size:22px;color:var(--navy,#1b2a4a);line-height:1.1}}
  .kpi span{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted,#6b6b76)}}
  table{{width:100%;border-collapse:collapse;margin:18px 0;background:var(--card,#fff);
    border:1px solid var(--line,#e4e0d7);border-radius:12px;overflow:hidden}}
  th,td{{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line,#e4e0d7);vertical-align:top}}
  th{{background:#f4f1ea;color:var(--navy,#1b2a4a);font-size:11.5px;text-transform:uppercase;letter-spacing:.06em}}
  tr:last-child td{{border-bottom:0}}
  tr.nope{{background:#fbfaf7}}
  .num{{font-family:ui-monospace,Menlo,monospace;color:var(--faint,#9a958a);white-space:nowrap;width:44px}}
  .t{{font-weight:650;color:var(--navy,#1b2a4a);font-size:15px}}
  .t a{{color:var(--navy,#1b2a4a)}}
  .q{{color:var(--muted,#6b6b76);font-size:13.5px;margin-top:2px}}
  .or{{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--muted,#6b6b76);white-space:nowrap}}
  .ok{{background:#dcfce7;color:#166534;padding:2px 9px;border-radius:20px;font-size:11.5px;font-weight:650;white-space:nowrap}}
  .no{{background:#f4f1ea;color:#6b6b76;padding:2px 9px;border-radius:20px;font-size:11.5px;white-space:nowrap}}
  .como{{margin-top:8px;padding:8px 10px;background:#f6f4ef;border-left:3px solid var(--accent,#c2410c);
    border-radius:8px;font-size:13px;color:var(--ink,#1b1b1f)}}
  code{{font-family:ui-monospace,Menlo,monospace;font-size:.88em;background:#f1ede4;
    border:1px solid var(--line,#e4e0d7);border-radius:5px;padding:1px 5px}}
  .nota{{background:var(--card,#fff);border:1px solid var(--line,#e4e0d7);border-left:3px solid var(--navy,#1b2a4a);
    border-radius:12px;padding:14px 16px;margin:22px 0;font-size:14px;color:var(--muted,#6b6b76)}}
  .nota b{{color:var(--navy,#1b2a4a)}}
  footer{{margin-top:34px;padding-top:14px;border-top:1px solid var(--line,#e4e0d7);
    font-size:12px;color:var(--faint,#9a958a)}}
</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
  <p class="eyebrow">{proyecto} · {plan_id} · core</p>
  <h1>El sistema, en cinco capas</h1>
  <p class="lead">El resto del informe trata de lo que hay que <b>hacer</b>. Esta sección trata de lo
  que el sistema <b>es</b>: qué hace, cómo está construido, qué datos maneja, cómo se usa, cómo se
  trabaja sobre él y qué se decidió por el camino.</p>
  <p class="lead">Si llegas nuevo al proyecto, se lee en este orden.</p>

  <div class="kpis">
    <div class="kpi"><b>{hay}</b><span>capas disponibles</span></div>
    <div class="kpi"><b>{faltan}</b><span>sin datos todavía</span></div>
    <div class="kpi"><b>{sha_de(plan)}</b><span>sha del repo</span></div>
    <div class="kpi"><b>{date.today().isoformat()}</b><span>generado</span></div>
  </div>

  <table>
    <thead><tr><th>#</th><th>Capa</th><th>Origen</th><th>Estado</th></tr></thead>
    <tbody>
{chr(10).join(filas)}
    </tbody>
  </table>

  <div class="nota">
    <b>Por qué una capa vacía dice cómo llenarse.</b> Una página en blanco parece un informe roto y
    quien la abre concluye que no hay nada. Una página que te dice qué comando teclear es una
    instrucción. Y por eso tampoco se rellena con datos de demostración: publicar un diagrama
    inventado es peor que no publicar ninguno — ya nos costó dos <code>structure.html</code> que
    enseñaban un proyecto que no existía.
    <br><br>
    <b>Lo generado envejece con el código; lo escrito, con el calendario.</b> Esta página se
    regenera (<code>gen_core_hub.py</code>), así que no puede mentir sobre qué existe. Lo que sí puede
    quedarse viejo es el contenido de cada capa: mira su fecha antes de fiarte.
  </div>

  <footer>Report-kit · página generada — no editar a mano, se regenera con
  <code>python3 gen_core_hub.py &lt;plan&gt;</code></footer>
</div></body></html>"""

def _out_dir(plan):
    """Dónde se ESCRIBE. Por defecto el propio plan (compatibilidad con los informes ya
    generados); con --out, .docs/core/ — PV-3: el Core describe lo que el proyecto ES, así que
    no puede morir cuando se cierra el plan del que salieron sus datos. De DÓNDE se leen los
    datos no cambia: sigue siendo el plan activo que se pasa como argumento."""
    if "--out" in sys.argv:
        d = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])
        os.makedirs(d, exist_ok=True)
        return d
    return plan

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = os.path.abspath(sys.argv[1])
    out = os.path.join(_out_dir(plan), "core.html")
    open(out, "w", encoding="utf-8").write(build(plan))
    print(f"OK {out}")

if __name__ == "__main__":
    main()
