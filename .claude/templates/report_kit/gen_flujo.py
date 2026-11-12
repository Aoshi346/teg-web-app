#!/usr/bin/env python3
"""gen_flujo.py — la pestaña «Flujo de acción»: el plan de EJECUCIÓN de lo aprobado.

QUÉ RESPONDE, y por qué no lo responde ninguna otra página del informe:
  · el Dashboard dice QUÉ hay que hacer y en qué estado está
  · Core → «Cómo se trabaja» dice cómo funciona el harness EN GENERAL
  · esta página dice **en qué ORDEN se va a ejecutar ESTO, quién lo hace y qué lo bloquea**

EL AGUJERO QUE CIERRA. El Usuario aprobó 41 items y el sistema no se enteró: las decisiones se
quedaban en `report.json` y no había nada que las convirtiera en trabajo. Sin que él preguntara
«¿ya lo has hecho?», no se hacía nunca. Esta página es la vista de ese puente
(`scripts/items_to_speckit.py`), y lo hace visible ANTES de ejecutar nada — que es el punto: se
mira, se confirma, y entonces corre.

Se genera desde el `tasks.md` de la sesión SpecKit, que es la fuente de verdad de la ejecución.
"""
import html, json, os, re, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))

def shared():
    t = open(os.path.join(HERE, "index.template.html"), encoding="utf-8").read()
    return re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", t, re.S).group(0)

CSS = """
  html,body{margin:0;background:var(--paper);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:15.5px;line-height:1.6}
  .wrap{max-width:1120px;margin:0 auto;padding:26px 20px 60px}
  .eyebrow{font-family:ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent);font-weight:700}
  h1{margin:6px 0 8px;font-size:30px;letter-spacing:-.02em;color:var(--navy)}
  .lead{color:var(--muted);max-width:74ch;margin:0 0 8px}
  .kpis{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 4px}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;min-width:92px}
  .kpi b{display:block;font-size:23px;color:var(--navy);line-height:1.1}
  .kpi span{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
  .wv{background:var(--card);border:1px solid var(--line);border-radius:14px;margin:16px 0;overflow:hidden}
  .wv>h2{margin:0;padding:14px 18px;font-size:17px;color:var(--navy);background:#f4f1ea;
    border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px;flex-wrap:wrap}
  .wv>h2 .n{font-family:ui-monospace,Menlo,monospace;font-size:11px;background:var(--navy);color:#fff;
    padding:3px 9px;border-radius:20px;letter-spacing:.06em}
  .wv>h2 .rg{margin-left:auto;font-size:11.5px;font-weight:400;color:var(--muted)}
  .wv .body{padding:6px 18px 16px}
  .wv .por{color:var(--muted);font-size:13.5px;margin:10px 0 12px;max-width:74ch}
  table{width:100%;border-collapse:collapse;font-size:14px}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
  tr:last-child td{border-bottom:0}
  td.id{font-family:ui-monospace,Menlo,monospace;font-size:12px;white-space:nowrap}
  td.id a{color:var(--navy);text-decoration:none;border-bottom:1px dotted var(--line)}
  .sev{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;padding:1px 6px;border-radius:5px;
    background:#f1ede4;color:var(--muted)}
  .sev.P0{background:#fee2e2;color:#991b1b} .sev.P1{background:#ffedd5;color:#9a3412}
  .st{font-size:11px;padding:2px 8px;border-radius:20px;white-space:nowrap}
  .st.pend{background:#f4f1ea;color:#6b6b76} .st.done{background:#dcfce7;color:#166534}
  .st.blk{background:#fee2e2;color:#991b1b}
  .gate{margin:12px 0 0;padding:9px 12px;background:#f6f4ef;border-left:3px solid var(--navy);
    border-radius:8px;font-size:13px}
  .nota{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--navy);
    border-radius:12px;padding:14px 16px;margin:20px 0;font-size:14px;color:var(--muted)}
  .nota.warn{border-left-color:var(--accent)}
  .nota b{color:var(--navy)}
  code{font-family:ui-monospace,Menlo,monospace;font-size:.88em;background:#f1ede4;
    border:1px solid var(--line);border-radius:5px;padding:1px 5px}
  .bar{display:flex;height:10px;border-radius:6px;overflow:hidden;margin:14px 0 4px;background:#efece4}
  .bar i{display:block} .bar .b1{background:#2563eb}.bar .b2{background:#0891b2}
  .bar .b3{background:#c2410c}.bar .b4{background:#991b1b}
  .leg{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-bottom:6px}
  .leg i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}
  /* Selector de vista. Mismo patrón que el dashboard (Lista/Kanban/Gantt/Mapa mental): las tres
     vistas responden preguntas distintas sobre los MISMOS datos, así que son vistas y no páginas
     — comparten filtros y estado, y una vista que no respeta el filtro que acabas de poner miente. */
  .vistas{display:flex;gap:6px;margin:18px 0 4px;flex-wrap:wrap}
  .vistas button{font:inherit;font-size:13px;padding:7px 14px;border:1px solid var(--line);
    background:var(--card);color:var(--muted);border-radius:9px;cursor:pointer}
  .vistas button:hover{background:#efece4;color:var(--navy)}
  .vistas button.on{background:var(--navy);color:#fff;border-color:var(--navy)}
  .vista{display:none} .vista.on{display:block}
  .gwrap{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;overflow-x:auto}
  .gwrap svg{min-width:900px}
  /* Nodo clicable. Se marca con cursor y foco visible porque si no, nadie sabe que se puede
     pulsar — un elemento interactivo que no lo parece es un elemento que no existe. */
  .wnode{cursor:pointer}
  .wnode rect:first-of-type{transition:filter .12s}
  .wnode:hover rect:first-of-type{filter:brightness(.97) drop-shadow(0 2px 6px rgba(0,0,0,.13))}
  .wnode:focus{outline:none}
  .wnode:focus rect:first-of-type{stroke-width:3;filter:drop-shadow(0 0 0 3px rgba(194,65,12,.3))}
  .wnode.sel rect:first-of-type{stroke-width:3}
  .ficha{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);
    border-radius:14px;padding:16px 18px;margin:14px 0}
  .ficha h3{margin:0 0 10px;font-size:18px;color:var(--navy)}
  .ficha h4{margin:16px 0 4px;font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--accent)}
  .ficha p{margin:0;font-size:14px;color:var(--muted);max-width:74ch}
  .ficha .meta{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);
    padding-bottom:10px;border-bottom:1px solid var(--line)}
  .ficha .meta b{color:var(--navy);font-size:14px}
  .ficha .gate{margin-top:4px;padding:9px 11px;background:#f6f4ef;border-radius:8px;font-size:12.5px}
  .ficha .peq{font-size:12px;color:var(--faint);margin-top:6px}
  .tl{list-style:none;padding:0;margin:6px 0 0;max-height:340px;overflow-y:auto}
  .tl li{padding:6px 0;border-bottom:1px solid var(--line);font-size:13.5px}
  .tl li:last-child{border-bottom:0}
  .tl a{text-decoration:none;color:var(--navy)}
  .tl a:hover code{background:var(--navy);color:#fff}
  .hint{font-size:12.5px;color:var(--faint);margin:8px 0 0}
  .tl li.tk{cursor:pointer;padding:7px 8px;border-radius:7px}
  .tl li.tk:hover{background:#f6f4ef}
  .tl li.tk code{background:#f1ede4;border:1px solid var(--line);border-radius:5px;padding:1px 5px;
    font-size:11.5px;color:var(--navy)}
  /* Modal: se abre EN la página. Antes el clic navegaba al dashboard y perdías el contexto del
     flujo — que es justo lo que habías ido a mirar. */
  .backdrop{position:fixed;inset:0;background:rgba(15,12,8,.42);display:none;z-index:60;
    align-items:center;justify-content:center;padding:20px}
  .backdrop.on{display:flex}
  .modal{background:var(--card);border-radius:16px;max-width:680px;width:100%;max-height:82vh;
    overflow-y:auto;padding:22px 24px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
  .modal h3{margin:0 0 4px;font-size:19px;color:var(--navy)}
  .modal .sub{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--muted);margin-bottom:14px}
  .modal .bloque{margin:14px 0}
  .modal .bloque b{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.07em;
    color:var(--accent);margin-bottom:3px}
  .modal .bloque p{margin:0;font-size:14px;color:var(--ink);white-space:pre-wrap}
  .modal .cerrar{position:sticky;top:0;float:right;font:inherit;font-size:20px;line-height:1;
    background:none;border:0;cursor:pointer;color:var(--muted);padding:0 4px}
  .modal .cerrar:hover{color:var(--navy)}
  .modal .ir{display:inline-block;margin-top:14px;font-size:13px;text-decoration:none;
    color:var(--navy);border:1px solid var(--line);border-radius:8px;padding:6px 12px}
  .modal .ir:hover{background:var(--navy);color:#fff}
  /* Barra de estado vivo */
  .vivo{display:flex;gap:12px;flex-wrap:wrap;align-items:center;background:var(--card);
    border:1px solid var(--line);border-radius:12px;padding:9px 14px;margin:14px 0;font-size:13px}
  .vivo .pt{width:8px;height:8px;border-radius:50%;background:#16a34a;display:inline-block;
    margin-right:6px;animation:lat 1.6s ease-in-out infinite}
  @keyframes lat{0%,100%{opacity:1}50%{opacity:.35}}
  .vivo.off .pt{background:#9a958a;animation:none}
  .vivo b{color:var(--navy)} .vivo .sep{color:var(--line)}
  .vivo .act{margin-left:auto;font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--faint)}
  .car{background:var(--card);border:1px solid var(--line);border-radius:14px;margin:14px 0;overflow:hidden}
  .car h3{margin:0;padding:11px 16px;font-size:14px;background:#f4f1ea;border-bottom:1px solid var(--line);
    color:var(--navy);display:flex;gap:10px;align-items:center}
  .car h3 .tag{font-family:ui-monospace,Menlo,monospace;font-size:10px;padding:2px 8px;border-radius:20px;
    background:var(--navy);color:#fff}
  .car h3 .par{margin-left:auto;font-size:11px;font-weight:400;color:var(--muted)}
  .pistas{padding:12px 16px;display:flex;flex-wrap:wrap;gap:6px}
  .pz{font-size:12px;padding:5px 9px;border-radius:7px;background:#f6f4ef;border:1px solid var(--line);
    font-family:ui-monospace,Menlo,monospace;color:var(--navy);white-space:nowrap}
  .pz.P0{border-color:#fca5a5;background:#fef2f2} .pz.P1{border-color:#fdba74;background:#fff7ed}
  .pz.blk{opacity:.55;text-decoration:line-through}
  footer{margin-top:32px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--faint)}
"""

COMO_SE_EJECUTA = {1: ('en paralelo', '6 a la vez (el tope es min(16, CPUs−2) y esta máquina tiene 8)', 'Cada tarea la escribe un agente y la <b>verifica otro</b> con contexto limpio: abre los ficheros, reejecuta los comandos y comprueba las cifras. Un «lo dice el informe del otro» vale <code>parcial</code>, nunca <code>sí</code>.'), 2: ('en paralelo', '6 a la vez', 'Igual que la 1. Además, antes de archivar nada se comprueba <b>quién lo cita</b>: una pieza retirada que otras nombran deja referencias rotas, y eso es peor que la pieza de más.'), 3: ('<b>secuencial</b>', 'una detrás de otra', 'Varias tocan <code>agents/</code> y <code>skills/</code>. Dos agentes editando el mismo directorio no se arreglan en el merge (<code>parallelization.md</code> §file claims), así que aquí no se reparte.'), 4: ('<b>secuencial</b>', 'una detrás de otra', 'Tocan <b>enforcement</b>: hooks y permisos. Un hook mal puesto bloquea el trabajo de todos, así que van al final y de una en una.')}

POR_QUE = {
 1: "Escriben algo que <b>no existe todavía</b>: un patrón, un README, un fichero de referencia. "
    "No tocan nada que ya funcione, así que ninguna puede romper el tronco — y son independientes "
    "entre sí, que es lo que las hace repartibles en paralelo (no que sean muchas).",
 2: "Archivan o mueven ficheros. <b>Reversible con git</b>: lo archivado va a <code>_archive/</code> "
    "con su README, nunca se borra. El riesgo real no es perder algo: es que otra pieza lo cite y "
    "se quede apuntando al vacío — por eso cada archivado comprueba antes quién lo nombra.",
 3: "Mueven piezas entre capas — de agente a skill, de skill a rule. <b>NO se reparte en paralelo</b>: "
    "varias tocan <code>agents/</code> y <code>skills/</code>, y dos agentes editando el mismo "
    "directorio no se arreglan en el merge (<code>parallelization.md</code> §file claims).",
 4: "Tocan <b>enforcement</b>: hooks y permisos. Van al final porque un hook mal puesto bloquea el "
    "trabajo de todos, y porque cambiar <code>settings.json</code> requiere aprobación aparte "
    "(<code>governance.md</code> §2).",
}

def parse(tasks_md):
    txt = open(tasks_md, encoding="utf-8").read()
    waves, cur = [], None
    for ln in txt.splitlines():
        m = re.match(r"^## (Wave \d+ — .+)$", ln)
        if m:
            cur = {"titulo": m.group(1), "n": int(re.search(r"Wave (\d+)", m.group(1)).group(1)),
                   "tareas": [], "gate": ""}
            waves.append(cur); continue
        if cur is None: continue
        t = re.match(r"^- \[([ x>!])\] `([A-Z0-9-]+)` \[([^/\]]*)/([^\]]*)\] (.+?)(?:\s*<!--.*)?$", ln)
        if t:
            cur["tareas"].append({"st": t.group(1), "id": t.group(2), "sev": t.group(3),
                                  "eff": t.group(4), "titulo": t.group(5)})
        g = re.search(r"\*\*GATE Wave \d+:\*\*\s*(.+)", ln)
        if g: cur["gate"] = g.group(1)
    return waves

def build(plan, tasks_md, sesion):
    import json as _json
    waves = parse(tasks_md)
    tot = sum(len(w["tareas"]) for w in waves)
    done = sum(1 for w in waves for t in w["tareas"] if t["st"] == "x")
    blk = sum(1 for w in waves for t in w["tareas"] if t["st"] == "!")
    # los items completos van al HTML para que el modal no tenga que navegar a ninguna parte
    datos_items = {}
    _rp = os.path.join(plan, "report.json")
    if os.path.exists(_rp):
        for _i in json.load(open(_rp, encoding="utf-8")).get("items", []):
            datos_items[_i["id"]] = {
                "t": _i.get("title", ""), "g": _i.get("goal", ""),
                "d": str(_i.get("desc", ""))[:1400], "s": _i.get("status", ""),
                "sev": _i.get("severity", ""), "ef": _i.get("effort", ""),
                "dec": _i.get("decision", ""),
                "rec": (_i.get("rec") or {}).get("rec", ""),
                "rz": (_i.get("rec") or {}).get("razon", "")[:300],
                "au": str(_i.get("auditor", ""))[:600],
            }

    meta = {}
    rp = os.path.join(plan, "report.json")
    if os.path.exists(rp): meta = json.load(open(rp, encoding="utf-8")).get("meta", {})

    STL = {" ": ("pend", "pendiente"), "x": ("done", "hecha"), ">": ("pend", "en curso"), "!": ("blk", "bloqueada")}
    # el detalle de cada wave, para el panel — se pinta oculto y lo enseña el JS al pulsar
    fichas = ""
    for w in waves:
        modo, conc, verif = COMO_SE_EJECUTA.get(w["n"], ("—", "—", "—"))
        lst = "".join(
            f'<li class="tk" data-id="{html.escape(t["id"])}"><code>{html.escape(t["id"])}</code> '
            f'<span class="sev {html.escape(t["sev"])}">{html.escape(t["sev"])}</span> '
            f'{html.escape(t["titulo"])}'
            + (' <span class="st blk">bloqueada</span>' if t["st"] == "!" else
               ' <span class="st done">hecha</span>' if t["st"] == "x" else '')
            + '</li>'
            for t in w["tareas"])
        fichas += f"""<div class="ficha" id="f-{w['n']}" hidden>
  <h3>Wave {w['n']} · {html.escape(w['titulo'].split('— ',1)[-1])}</h3>
  <div class="meta">
    <span><b>{len(w['tareas'])}</b> tareas</span>
    <span>modo: {modo}</span>
    <span>{conc}</span>
    <span>riesgo {w['n']}/4</span>
  </div>
  <h4>Cómo se ejecuta</h4>
  <p>{POR_QUE.get(w['n'],'')}</p>
  <h4>Quién la verifica</h4>
  <p>{verif}</p>
  <h4>Qué la cierra</h4>
  <div class="gate"><code>{html.escape(w['gate'][:160]) if w['gate'] else 'task_progress.py --gate'}</code>
  <br><span class="peq">No se pasa a la wave siguiente sin esto: encadenar sobre un tronco roto es
  peor que parar.</span></div>
  <h4>Las {len(w['tareas'])} tareas</h4>
  <ul class="tl">{lst}</ul>
  <p class="peq">Pulsa un id para abrir su ficha completa en el Dashboard.</p>
</div>"""

    bloques = ""
    for w in waves:
        filas = ""
        for t in w["tareas"]:
            c, lab = STL.get(t["st"], ("pend", "?"))
            filas += (f'<tr><td class="id"><a href="dashboard.html#{html.escape(t["id"])}">{html.escape(t["id"])}</a></td>'
                      f'<td><span class="sev {html.escape(t["sev"])}">{html.escape(t["sev"])}</span></td>'
                      f'<td>{html.escape(t["titulo"])}</td>'
                      f'<td><span class="st {c}">{lab}</span></td></tr>')
        par = ("en paralelo" if w["n"] in (1, 2) else "<b>secuencial</b>")
        bloques += f"""<section class="wv">
  <h2><span class="n">WAVE {w['n']}</span>{html.escape(w['titulo'].split('— ',1)[-1])}
      <span class="rg">{len(w['tareas'])} tareas · {par}</span></h2>
  <div class="body">
    <p class="por">{POR_QUE.get(w['n'],'')}</p>
    <table><thead><tr><th>id</th><th>sev</th><th>tarea</th><th>estado</th></tr></thead>
    <tbody>{filas}</tbody></table>
    {'<div class="gate"><b>No se cierra sin:</b> <code>' + html.escape(w['gate'][:150]) + '</code></div>' if w['gate'] else ''}
  </div></section>"""

    # ═══ VISTA A · GRAFO — las waves como cadena, con lo que va en paralelo dentro ═══
    COL = ["#2563eb", "#0891b2", "#c2410c", "#991b1b"]
    NW, GAP, X0, Y = 218, 46, 22, 74
    piezas = []
    for k, w in enumerate(waves):
        x = X0 + k * (NW + GAP)
        c = COL[min(w["n"] - 1, 3)]
        n = len(w["tareas"]); hech = sum(1 for t in w["tareas"] if t["st"] == "x")
        par = "en paralelo" if w["n"] in (1, 2) else "SECUENCIAL"
        primero = w["n"] == 1
        piezas.append(
            f'<g class="wnode" data-w="{w["n"]}" tabindex="0" role="button" '
            f'aria-label="Wave, pulsa para ver su detalle">'
          f'<rect x="{x}" y="{Y}" width="{NW}" height="96" rx="7" fill="#fff" stroke="{c}" '
          f'stroke-width="{2 if primero else 1.4}"/>'
          f'<rect x="{x}" y="{Y}" width="{NW}" height="4" rx="2" fill="{c}"/>'
          f'<text x="{x+15}" y="{Y+28}" style="font:600 13px -apple-system;fill:#1b2a4a">'
          f'Wave {w["n"]} · {html.escape(w["titulo"].split("— ",1)[-1][:22])}</text>'
          f'<text x="{x+15}" y="{Y+48}" style="font:11px -apple-system;fill:#6b6b76">'
          f'{n} tareas · {hech} hechas</text>'
          f'<text x="{x+15}" y="{Y+67}" style="font:600 10px -apple-system;fill:{c}">'
          f'{"PRIMERO — NADA ANTES" if primero else par}</text>'
          f'<text x="{x+15}" y="{Y+85}" style="font:10px ui-monospace;fill:#9a958a">riesgo {w["n"]}/4 · pulsa aquí</text></g>')
        if k < len(waves) - 1:
            x2 = x + NW
            piezas.append(f'<line x1="{x2}" y1="{Y+48}" x2="{x2+GAP-9}" y2="{Y+48}" '
                          f'stroke="rgba(27,42,74,.34)" stroke-width="1.5" marker-end="url(#fl)"/>')
    ancho = X0 * 2 + len(waves) * NW + (len(waves) - 1) * GAP
    grafo = (f'<div class="gwrap"><svg viewBox="0 0 {ancho} 210" style="width:100%;height:210px">'
             f'<defs><marker id="fl" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">'
             f'<path d="M0,0 L0,6 L9,3 z" fill="rgba(27,42,74,.34)"/></marker></defs>'
             f'<text x="{X0}" y="34" style="font:600 12px ui-monospace;fill:#c2410c;letter-spacing:.1em">'
             f'ORDEN DE EJECUCIÓN — POR RIESGO, NO POR PRIORIDAD</text>'
             f'<text x="{X0}" y="54" style="font:11px -apple-system;fill:#6b6b76">'
             f'Cada wave espera a la anterior. Dentro de una wave, lo que no se pisa corre a la vez.</text>'
             + "".join(piezas) + '</svg></div>')

    # ═══ VISTA B · CARRILES — un carril por wave, con sus tareas como pastillas ═══
    carriles = ""
    for w in waves:
        pz = "".join(
            f'<span class="pz {html.escape(t["sev"])}{" blk" if t["st"]=="!" else ""}" '
            f'title="{html.escape(t["titulo"])}">{html.escape(t["id"])}</span>'
            for t in w["tareas"])
        par = "corren a la vez" if w["n"] in (1, 2) else "una detrás de otra — se pisarían"
        carriles += (f'<div class="car"><h3><span class="tag">W{w["n"]}</span>'
                     f'{html.escape(w["titulo"].split("— ",1)[-1])}'
                     f'<span class="par">{len(w["tareas"])} tareas · {par}</span></h3>'
                     f'<div class="pistas">{pz}</div></div>')

    segs = "".join(f'<i class="b{w["n"]}" style="width:{100*len(w["tareas"])/max(tot,1):.1f}%"></i>' for w in waves)
    leg = "".join(f'<span><i class="b{w["n"]}" style="background:'
                  f'{["#2563eb","#0891b2","#c2410c","#991b1b"][min(w["n"]-1,3)]}"></i>Wave {w["n"]} · {len(w["tareas"])}</span>'
                  for w in waves)

    datos_json = json.dumps(datos_items, ensure_ascii=False)
    return rf"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flujo de acción — {html.escape(str(meta.get('project','')))}</title>
<style>{shared()}</style><style>{CSS}</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
<p class="eyebrow">{html.escape(str(meta.get('project','')))} · {html.escape(str(meta.get('plan_id','')))} · flujo de acción</p>
<h1>En qué orden se ejecuta lo aprobado</h1>
<p class="lead">El <b>Dashboard</b> dice qué hay que hacer. <b>Core → Cómo se trabaja</b> dice cómo
funciona el harness en general. Esta página dice <b>en qué orden se va a ejecutar ESTO, qué va en
paralelo y qué lo bloquea</b>.</p>

<div class="kpis">
 <div class="kpi"><b>{tot}</b><span>tareas</span></div>
 <div class="kpi"><b>{len(waves)}</b><span>waves</span></div>
 <div class="kpi"><b>{done}</b><span>hechas</span></div>
 <div class="kpi"><b>{blk}</b><span>bloqueadas</span></div>
</div>
<div class="bar">{segs}</div><div class="leg">{leg}</div>

<div class="nota warn"><b>Por qué existe esta página.</b> Aprobaste 41 items y el sistema no se
enteró: las decisiones se quedaban en <code>report.json</code> y <b>no había nada que las
convirtiera en trabajo</b>. Sin preguntar «¿ya está hecho?», no se hacía nunca. El puente es
<code>scripts/items_to_speckit.py</code>, y esta página lo hace visible <b>antes</b> de ejecutar
nada: se mira, se confirma, y entonces corre.</div>

<div class="vivo off" id="vivo">
  <span><span class="pt"></span><b id="v-est">—</b></span>
  <span class="sep">·</span><span id="v-wf">sin conexión con el servidor</span>
  <span class="act" id="v-act"></span>
</div>

<div class="vistas" role="group" aria-label="Vista del flujo">
  <button type="button" class="on" onclick="verVista('grafo',this)">Grafo</button>
  <button type="button" onclick="verVista('carriles',this)">Carriles</button>
  <button type="button" onclick="verVista('lista',this)">Lista</button>
</div>

<div class="vista on" id="v-grafo">{grafo}
  <p class="hint">↑ Pulsa una wave para ver sus tareas, cómo se ejecuta y qué la cierra. También con
  el tabulador y Enter.</p>
  {fichas}
  <div class="nota"><b>Cómo se lee.</b> Cada caja es una wave y la flecha es «espera a». Dentro de
  una wave, lo que no toca los mismos ficheros corre a la vez; lo que sí, va detrás. La wave 1 no
  espera a nada porque solo escribe ficheros nuevos.</div></div>

<div class="vista" id="v-carriles">{carriles}
  <div class="nota"><b>Cómo se lee.</b> Un carril por wave, cada pastilla una tarea. Las tachadas
  están bloqueadas y su razón vive en el <code>tasks.md</code> de la sesión. El color marca la
  severidad — que NO decide el orden: eso lo decide el riesgo de la wave.</div></div>

<div class="vista" id="v-lista">{bloques}</div>

<div class="nota"><b>El orden no es por prioridad, es por riesgo.</b> Las waves van de lo que no
puede romper nada a lo que sí. Una P0 de la wave 3 espera a una P2 de la wave 1 — porque la P2
escribe un fichero nuevo y la P0 mueve un agente que otras piezas citan.</div>

<div class="nota warn"><b>Lo que NO entra aquí.</b> Las tareas marcadas <b>bloqueadas</b> tienen su
razón escrita en el <code>tasks.md</code> de la sesión. Y hay una regla que no cambia por estar en
una wave: <b>commit sí, push y merge no</b> sin aprobación (<code>governance.md</code> §2).</div>

<script>
/* Selector de vista. Recuerda la elección por informe, en la clave de UI y NUNCA junto a las
   decisiones (report-kit.md regla 4c): una preferencia de pantalla no es un dato del plan. */
function abrirWave(n){{
  document.querySelectorAll(".ficha").forEach(function(f){{ f.hidden = (f.id !== "f"+"-"+n); }});
  document.querySelectorAll(".wnode").forEach(function(g){{
    g.classList.toggle("sel", g.getAttribute("data-w") === String(n)); }});
  var f = document.getElementById("f"+"-"+n);
  if(f) f.scrollIntoView({{behavior:"smooth", block:"nearest"}});
  try {{ localStorage.setItem("tlr::flujo::wave", n); }} catch(e){{}}
}}
(function(){{
  document.querySelectorAll(".wnode").forEach(function(g){{
    var n = g.getAttribute("data-w");
    g.addEventListener("click", function(){{ abrirWave(n); }});
    // Enter y Espacio: un nodo que solo responde al ratón deja fuera a quien navega con teclado
    g.addEventListener("keydown", function(e){{
      if(e.key === "Enter" || e.key === " "){{ e.preventDefault(); abrirWave(n); }}
    }});
  }});
  var guardada = null;
  try {{ guardada = localStorage.getItem("tlr::flujo::wave"); }} catch(e){{}}
  abrirWave(guardada && document.getElementById("f"+"-"+guardada) ? guardada : 1);
}})();

function verVista(v, btn){{
  document.querySelectorAll(".vista").forEach(function(e){{ e.classList.toggle("on", e.id === "v"+"-"+v); }});
  document.querySelectorAll(".vistas button").forEach(function(b){{ b.classList.remove("on"); }});
  if(btn) btn.classList.add("on");
  try {{ localStorage.setItem("tlr::flujo::vista", v); }} catch(e){{}}
}}
(function(){{
  var v = null; try {{ v = localStorage.getItem("tlr::flujo::vista"); }} catch(e){{}}
  if(!v) return;
  var i = ["grafo","carriles","lista"].indexOf(v); if(i < 0) return;
  verVista(v, document.querySelectorAll(".vistas button")[i]);
}})();
</script>
<script>
const ITEMS = {datos_json};

/* MODAL — el clic abre aquí, no navega. Antes llevaba al dashboard y perdías el contexto del
   flujo, que es justo lo que habías ido a mirar. El enlace al dashboard sigue estando, pero como
   opción al final, no como único camino. */
function esc(x){{
  // Se escapa con replace por carácter y no con un mapa literal: el mapa llevaba una comilla
  // doble escapada que se perdía al pasar por el f-string de Python y rompía TODO el script.
  return String(x==null?'':x)
    .split('&').join('&amp;').split('<').join('&lt;')
    .split('>').join('&gt;').split(String.fromCharCode(34)).join('&quot;');
}}
function md(t){{ return esc(t).replace(/\*\*([^*]+)\*\*/g,"<b>$1</b>").replace(/`([^`]+)`/g,"<code>$1</code>"); }}

function abrirItem(id){{
  var it = ITEMS[id]; if(!it) return;
  var estados = {{done:"hecha", blocked:"bloqueada", doing:"en curso", review:"en revisión", backlog:"pendiente"}};
  var h = '<button class="cerrar" onclick="cerrarModal()" aria-label="Cerrar">&times;</button>'
    + '<h3>' + esc(it.t) + '</h3>'
    + '<p class="sub">' + esc(id) + ' · ' + esc(it.sev) + '/' + esc(it.ef)
    + ' · ' + esc(estados[it.s] || it.s)
    + (it.dec ? ' · decisión: <b>' + esc(it.dec) + '</b>' : '') + '</p>';
  if(it.g) h += '<div class="bloque"><b>Objetivo</b><p>' + md(it.g) + '</p></div>';
  if(it.d) h += '<div class="bloque"><b>Detalle</b><p>' + md(it.d) + '</p></div>';
  if(it.rz) h += '<div class="bloque"><b>Recomendación del revisor (' + esc(it.rec) + ')</b><p>'
    + md(it.rz) + '</p></div>';
  if(it.au) h += '<div class="bloque"><b>Análisis del auditor</b><p>' + md(it.au) + '</p></div>';
  h += '<a class="ir" href="dashboard.html#' + esc(id) + '">Abrir en el Dashboard para decidir &rarr;</a>';
  document.getElementById("md").innerHTML = h;
  document.getElementById("bd").classList.add("on");
}}
function cerrarModal(){{ document.getElementById("bd").classList.remove("on"); }}
document.addEventListener("click", function(e){{
  var li = e.target.closest && e.target.closest("li.tk");
  if(li && li.dataset.id){{ abrirItem(li.dataset.id); return; }}
  if(e.target.id === "bd") cerrarModal();
}});
document.addEventListener("keydown", function(e){{ if(e.key === "Escape") cerrarModal(); }});

/* VIVO — pregunta al servidor cada 5 s. Tres cautelas que no son opcionales:
   1. si el backend no responde, se deja lo inyectado y SE DICE — el informe tiene que seguir
      abriendo offline, que es media razón de que exista;
   2. se para con la pestaña oculta, o un panel abierto toda la noche hace miles de peticiones;
   3. solo pinta contadores: no reescribe la página, para no pisar lo que estés leyendo. */
var TIMER = null;
async function tic(){{
  var b = document.getElementById("vivo");
  try {{
    var r = await fetch("api/vivo", {{cache:"no-store"}});
    if(!r.ok) throw 0;
    var d = await r.json();
    b.classList.remove("off");
    var i = d.items || {{}};
    document.getElementById("v-est").textContent =
      (i.done||0) + " de " + (i.total||0) + " hechas";
    var act = (d.workflows||[]).filter(function(w){{ return w.corriendo > 0 && w.edad_s < 900; }});
    document.getElementById("v-wf").innerHTML = act.length
      ? "<b>" + act.reduce(function(a,w){{return a+w.corriendo;}},0) + " agentes trabajando</b> en "
        + act.length + " workflow(s) — último: <code>" + esc(act[0].ultimo||"") + "</code>"
      : "sin workflows activos";
    var ult = (d.actividad||[])[0];
    document.getElementById("v-act").textContent = ult ? (ult.tool + " " + ult.que) : "";
    // los contadores de arriba también, para no tener dos verdades en la misma pantalla
    var k = document.querySelectorAll(".kpi b");
    if(k[2] && i.done != null) k[2].textContent = i.done;
  }} catch(e){{
    b.classList.add("off");
    document.getElementById("v-wf").textContent =
      "sin conexión con el servidor — los datos son del momento en que se generó la página";
  }}
}}
function arranca(){{ if(TIMER) clearInterval(TIMER); tic(); TIMER = setInterval(tic, 5000); }}
document.addEventListener("visibilitychange", function(){{
  if(document.hidden){{ clearInterval(TIMER); TIMER = null; }} else {{ arranca(); }}
}});
arranca();
</script>
<div class="backdrop" id="bd" role="dialog" aria-modal="true">
  <div class="modal" id="md"></div>
</div>
<footer>Generado por <code>gen_flujo.py</code> desde <code>{html.escape(sesion)}</code>
el {date.today().isoformat()} — no editar a mano.</footer>
</div></body></html>"""

def main():
    if len(sys.argv) < 3:
        sys.exit("uso: gen_flujo.py <plan-dir> <sesion-tasks.md>")
    plan, tm = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    out = os.path.join(plan, "flujo.html")
    open(out, "w", encoding="utf-8").write(build(plan, tm, os.path.basename(os.path.dirname(tm))))
    print(f"OK {out}")

if __name__ == "__main__":
    main()
