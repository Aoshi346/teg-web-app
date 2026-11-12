#!/usr/bin/env python3
"""gen_core_capas.py — genera LAS CAPAS del Core con datos reales del repo, no páginas vacías.

POR QUÉ EXISTE. El hub del Core listaba seis capas "sin datos todavía" y remitía a comandos que
nadie iba a correr. Eso es un índice honesto y un entregable inútil: quien lo abre ve seis huecos.
Las capas que se pueden derivar del repo SE DERIVAN — y las que no, siguen diciendo cómo se llenan.

QUÉ DERIVA Y DE DÓNDE
  · overview     ← el inventario real de .claude/ (rules, skills, agentes, hooks, workflows…)
  · arquitectura ← graph-dataset.json (el grafo del harness) agrupado por capa
  · datos        ← los formatos que el harness lee y escribe, con su generador y su consumidor
  · flujo        ← el informe de flujo + los gates deterministas que existen en disco
  · decisiones   ← .docs/adr/ si hay; si no, dice que no hay y qué las dispara
"""
import html, json, os, re, subprocess, sys
from collections import Counter
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))

def shared_css():
    tpl = open(os.path.join(HERE, "index.template.html"), encoding="utf-8").read()
    return re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", tpl, re.S).group(0)

PAGE_CSS = """
  html,body{margin:0;background:var(--paper);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:15.5px;line-height:1.62}
  .wrap{max-width:1080px;margin:0 auto;padding:26px 20px 60px}
  .eyebrow{font-family:ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent);font-weight:700}
  h1{margin:6px 0 10px;font-size:30px;letter-spacing:-.02em;color:var(--navy)}
  h2{margin:30px 0 10px;font-size:20px;color:var(--navy);letter-spacing:-.01em}
  h3{margin:22px 0 6px;font-size:16px;color:var(--navy)}
  p{max-width:74ch;margin:0 0 12px}
  .lead{color:var(--muted);max-width:74ch}
  .kpis{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;min-width:96px}
  .kpi b{display:block;font-size:23px;color:var(--navy);line-height:1.1}
  .kpi span{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
  table{width:100%;border-collapse:collapse;margin:14px 0 22px;background:var(--card);
    border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:14px}
  th,td{text-align:left;padding:10px 13px;border-bottom:1px solid var(--line);vertical-align:top}
  th{background:#f4f1ea;color:var(--navy);font-size:11.5px;text-transform:uppercase;letter-spacing:.06em}
  tr:last-child td{border-bottom:0}
  td.n{font-family:ui-monospace,Menlo,monospace;text-align:right;white-space:nowrap;color:var(--navy);font-weight:600}
  code{font-family:ui-monospace,Menlo,monospace;font-size:.88em;background:#f1ede4;
    border:1px solid var(--line);border-radius:5px;padding:1px 5px}
  .nota{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--navy);
    border-radius:12px;padding:14px 16px;margin:20px 0;font-size:14px;color:var(--muted)}
  .nota b{color:var(--navy)}
  .warn{border-left-color:var(--accent)}
  .bar{height:9px;border-radius:5px;background:#efece4;overflow:hidden;min-width:90px}
  .bar i{display:block;height:100%;background:var(--navy)}
  ul{max-width:74ch} li{margin:4px 0}
  .gwrap{background:var(--card);border:1px solid var(--line);border-radius:14px;
    padding:14px;margin:14px 0 22px;overflow-x:auto}
  .gwrap svg{min-width:860px}
  footer{margin-top:34px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--faint)}

  /* core-sistema · el inventario buscable */
  .aviso{background:#fff8ec;border:1px solid #f0d9a8;border-left:3px solid var(--amber);
    border-radius:10px;padding:12px 16px;margin:16px 0;max-width:80ch;font-size:14.5px}
  .filtros{position:sticky;top:0;z-index:5;background:var(--paper);padding:12px 0 8px;
    border-bottom:1px solid var(--line);margin-bottom:6px}
  .filtros input{width:100%;max-width:520px;padding:9px 13px;border:1px solid var(--line);
    border-radius:var(--radius-pill);font-size:14.5px;background:var(--card);color:var(--ink)}
  .chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}
  .chip{border:1px solid var(--line);background:var(--card);color:var(--muted);cursor:pointer;
    border-radius:var(--radius-pill);padding:4px 11px;font-size:12.5px;font-family:inherit}
  .chip b{color:var(--ink);margin-left:3px}
  .chip.on{background:var(--navy);border-color:var(--navy);color:#fff}
  .chip.on b{color:#fff}
  .cuenta{font-size:12.5px;color:var(--muted);margin:8px 0 0}
  .grp h2 .n{font-family:var(--mono);font-size:13px;color:var(--muted);font-weight:600}
  .quees{font-size:13.5px;color:var(--muted);margin:0 0 10px;max-width:80ch}
  table.inv{width:100%;border-collapse:collapse;font-size:14px;background:var(--card);
    border:1px solid var(--line);border-radius:10px;overflow:hidden}
  table.inv th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;
    color:var(--muted);padding:8px 12px;border-bottom:1px solid var(--line);background:#fbfaf7}
  table.inv td{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
  table.inv tr:last-child td{border-bottom:0}
  table.inv td:first-child{width:23%}
  table.inv td.fi{text-align:right;font-family:var(--mono);color:var(--muted);width:60px}
  .ruta{font-size:11px;color:var(--faint)}
  .sin{color:var(--faint)}
  .huer{background:#fdecec;color:var(--red);font-size:10.5px;font-weight:700;padding:1px 6px;
    border-radius:var(--radius-pill);text-transform:uppercase;letter-spacing:.04em}
  .como{font-size:11.5px;font-weight:600;padding:2px 9px;border-radius:var(--radius-pill);
    white-space:nowrap;border:1px solid}
  .como.teclea{background:#eaf5ec;color:var(--green);border-color:#bfe0c6}
  .como.cita{background:#eef2fb;color:var(--blue);border-color:#c9d6f0}
  .como.evento{background:#fdecec;color:var(--red);border-color:#f2c9c9}
  .como.plug{background:#f3f1ec;color:var(--muted);border-color:var(--line)}
  @media(max-width:720px){table.inv td:first-child{width:auto}.ruta{display:none}}
"""

def page(titulo, eyebrow, cuerpo, gen):
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title>
<style>{shared_css()}</style><style>{PAGE_CSS}</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
<p class="eyebrow">{html.escape(eyebrow)}</p>
{cuerpo}
<footer>Página generada por <code>gen_core_capas.py</code> el {gen} — no editar a mano.</footer>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────────────────────────────────
def contar(repo):
    j = lambda *p: os.path.join(repo, ".claude", *p)
    def n(path, pat="*"):
        d = j(path)
        if not os.path.isdir(d): return 0
        import glob
        return len([x for x in glob.glob(os.path.join(d, pat)) if "_archive" not in x])
    import glob
    return {
        "rules": n("rules", "*.md"), "skills": len([x for x in glob.glob(j("skills", "*")) if os.path.isdir(x)]),
        "agentes": n("agents", "*.md"), "hooks": n("hooks", "*.sh"), "workflows": n("workflows", "*.js"),
        "comandos": n("commands", "*.md"), "scripts": n("scripts", "*.py"),
        "patrones": n(os.path.join("patterns", "stack"), "*"),
    }

def overview(repo, gen):
    c = contar(repo)
    kpis = "".join(f'<div class="kpi"><b>{v}</b><span>{k}</span></div>' for k, v in c.items())
    return page("Qué hace este sistema", "core · capa 1 · qué hace", f"""
<h1>Qué hace este sistema</h1>
<p class="lead">Este repositorio no es una aplicación: es <b>el harness</b> — la configuración que
gobierna cómo trabaja un agente de programación sobre un proyecto. Se copia a cada proyecto nuevo y
se personaliza. Lo que aquí se arregla, se propaga; lo que aquí se rompe, también.</p>
<div class="kpis">{kpis}</div>

<h2>Las ocho capas, y qué decide cada una</h2>
<p>La pregunta que ordena todo el sistema es <b>en qué capa vive una norma</b>, porque de eso depende
si se puede ignorar o no. El criterio completo está en <code>rules/layer-decision.md</code>.</p>
<table><thead><tr><th>Capa</th><th>Qué es</th><th>¿Se puede ignorar?</th></tr></thead><tbody>
<tr><td><code>CLAUDE.md</code> · rules</td><td>Intención y routing</td><td><b>Sí — es advisory.</b> Lo dice la doc oficial</td></tr>
<tr><td>Hooks</td><td>Enforcement determinista</td><td><b>No.</b> Los ejecuta el harness y pueden bloquear</td></tr>
<tr><td>Skills</td><td>Procedimientos repetibles</td><td>Se activan por su <code>description</code> — si está floja, no se disparan nunca</td></tr>
<tr><td>Subagentes</td><td>Criterio independiente, contexto limpio</td><td>Se invocan a propósito</td></tr>
<tr><td>Workflows</td><td>Orquestación determinista</td><td>Script: igual en cada ejecución</td></tr>
<tr><td>Agent-teams</td><td>Varias sesiones que se hablan</td><td>Caro: una sesión por miembro</td></tr>
<tr><td>Plugins</td><td>Capacidad de terceros, versionada</td><td>Es cadena de suministro, no comodidad</td></tr>
<tr><td>MCP</td><td>Acceso gobernado a lo externo</td><td>Sin revisión de código, no se conecta</td></tr>
</tbody></table>

<div class="nota"><b>La frase que decide todo lo demás:</b> «las instrucciones de CLAUDE.md son
advisory — Claude puede ignorarlas». No es un defecto, es la definición. Por eso una norma cuyo
incumplimiento es caro <b>no se escribe más fuerte: se baja de capa</b> a un hook.</div>

<h2>Cómo se propaga a un proyecto</h2>
<ul>
<li><b>Traer lo nuevo</b> → <code>update-agent</code> (motor <code>template_diff.py</code>, sha256, respeta lo personalizado)</li>
<li><b>Saber QUÉ traer</b> → <code>mapear-sistema</code>, que cruza lo que el código <i>es</i> con lo que el harness <i>tiene</i></li>
<li><b>Devolver lo aprendido</b> → <code>/consolidate-agent-learnings</code></li>
</ul>
<div class="nota warn"><b>El bucle tiene dos sentidos y solo se practica uno.</b> Añadir se hace
solo; <b>podar hay que agendarlo</b>. Sin la fase de poda esto es un trinquete: el harness solo
puede crecer, y cada pieza que no se usa compite por atención con las que sí
(<code>rules/self-improvement-loop.md</code> §5).</div>""", gen)

def arquitectura(repo, plan, gen):
    gp = os.path.join(plan, "graph-dataset.json")
    if not os.path.exists(gp):
        cuerpo = """<h1>Arquitectura</h1>
<div class="nota warn"><b>Sin grafo todavía.</b> Se genera con
<code>python3 .claude/scripts/gen_harness_graph.py --root &lt;proyecto&gt;</code> (para el harness) o
<code>/code-graph</code> (para el código). No se rellena con un diagrama de demostración: publicar
un mapa inventado es peor que no publicar ninguno.</div>"""
        return page("Arquitectura", "core · capa 2b · arquitectura", cuerpo, gen)

    g = json.load(open(gp, encoding="utf-8"))
    nodos, aristas = g["nodes"], g["edges"]
    grupos = Counter(n["group"] for n in nodos)
    tipos = Counter(e.get("kind", "?") for e in aristas)
    rotas = [e for e in aristas if e.get("kind") == "roto"]
    # `huerfana` y no `fan_in == 0`: un comando o un hook con fan_in 0 es lo NORMAL —se teclea,
    # o lo dispara un evento—, y contarlos daba 53 «piezas que nadie nombra» donde había 4.
    huerf = [n for n in nodos
             if n.get("huerfana", n.get("fan_in", 0) == 0 and n.get("group") != "roto")]
    top = sorted(nodos, key=lambda n: -(n.get("fan_in", 0)), reverse=False)[:0]
    mas = sorted(nodos, key=lambda n: -n.get("fan_in", 0))[:10]
    mx = max((n.get("fan_in", 0) for n in nodos), default=1) or 1

    fg = "".join(f'<tr><td><code>{html.escape(k)}</code></td><td class="n">{v}</td>'
                 f'<td><div class="bar"><i style="width:{100*v/max(grupos.values()):.0f}%"></i></div></td></tr>'
                 for k, v in grupos.most_common())
    ft = "".join(f'<tr><td><code>{html.escape(k)}</code></td><td class="n">{v}</td></tr>' for k, v in tipos.most_common(8))
    fm = "".join(f'<tr><td><code>{html.escape(n["label"])}</code></td><td>{html.escape(n.get("group",""))}</td>'
                 f'<td class="n">{n.get("fan_in",0)}</td>'
                 f'<td><div class="bar"><i style="width:{100*n.get("fan_in",0)/mx:.0f}%"></i></div></td></tr>'
                 for n in mas)
    fr = "".join(f'<li><code>{html.escape(e["from"])}</code> → <code>{html.escape(str(e["to"]))}</code></li>' for e in rotas[:10])
    fh = ", ".join(f'<code>{html.escape(n["label"])}</code>' for n in huerf[:14])

    cuerpo = f"""<h1>Cómo está construido</h1>
<p class="lead">El grafo real del sistema, extraído del frontmatter y de las referencias cruzadas —
no de una lectura a ojo. Cada arista es una cita verificable.</p>
<div class="kpis">
 <div class="kpi"><b>{len(nodos)}</b><span>piezas</span></div>
 <div class="kpi"><b>{len(aristas)}</b><span>relaciones</span></div>
 <div class="kpi"><b>{len(rotas)}</b><span>referencias rotas</span></div>
 <div class="kpi"><b>{len(huerf)}</b><span>que nadie nombra</span></div>
</div>
<p>El grafo navegable está en <a href="{_href_plan(plan, 'structure.html')}">Estructura</a>. Aquí van los números que
importan al mirarlo.</p>

<h2>De qué se compone</h2>
<table><thead><tr><th>Tipo de pieza</th><th>Nº</th><th></th></tr></thead><tbody>{fg}</tbody></table>

<h2>Cómo se relacionan</h2>
<table><thead><tr><th>Relación</th><th>Nº</th></tr></thead><tbody>{ft}</tbody></table>

<h2>Lo más citado — lo que duele al tocar</h2>
<table><thead><tr><th>Pieza</th><th>Tipo</th><th>Citas</th><th></th></tr></thead><tbody>{fm}</tbody></table>

<h2>Las dos señales que hay que mirar</h2>
<div class="nota warn"><b>{len(rotas)} referencias rotas</b> — una pieza cita a otra que no existe.
Así se encontró que el Gate 0 mandaba invocar un agente archivado, y fallaba en silencio en toda
tarea grande.<ul>{fr or '<li>ninguna</li>'}</ul></div>
<div class="nota"><b>{len(huerf)} piezas que nadie nombra</b> (<code>fan_in: 0</code>). No significa
que sobren: significa que <b>nadie las va a encontrar</b>. Casi siempre el problema es la
<code>description</code>, no la pieza — primero se arregla la puerta, y solo si sigue sin entrar
nadie se retira la habitación.<br><br>{fh or 'ninguna'}</div>""" 
    return page("Cómo está construido", "core · capa 2b · arquitectura", cuerpo, gen)

def datos(repo, gen):
    filas = [
        ("<code>report.json</code>", "Los items de un plan y las decisiones del Usuario",
         "<code>tasks_to_items.py</code> ← <code>tasks.md</code>", "todo el informe · <code>server.py</code>"),
        ("<code>graph-dataset.json</code>", "El grafo: nodos, aristas, comunidades",
         "<code>gen_harness_graph.py</code> · <code>graphify_to_dataset.py</code> · <code>/code-graph</code>", "<code>structure.html</code>"),
        ("<code>PROGRESS.json</code>", "Estado de la tarea en curso — fuente de verdad del Supervisor",
         "el TL, en vivo", "<code>otto-briefing.sh</code> · supervisión externa"),
        ("<code>inventario.json</code>", "Qué hay en la raíz del repo y quién lo cita",
         "<code>gen_inventario.py</code>", "el informe de auditoría"),
        ("<code>audit/*.jsonl</code>", "Cadena de hashes de cada tool use — <b>fuera del repo</b>",
         "<code>hooks/audit-log.sh</code>", "<code>--verify</code> · <code>harness-telemetry</code>"),
        ("<code>trend.json</code>", "Evolución de la nota de un auditor entre rondas",
         "cada auditor", "<code>/qa-loop</code> · <code>trend_lint.py</code>"),
        ("<code>baseline/*.json</code>", "La deuda congelada de un patrón (trinquete)",
         "<code>pattern_baseline.py freeze</code>", "<code>pattern_check_*.py</code>"),
    ]
    tb = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in filas)
    cuerpo = f"""<h1>Qué datos maneja</h1>
<p class="lead">Este harness no tiene base de datos: sus «entidades» son <b>ficheros con formato
acordado</b>, cada uno con un generador y un consumidor. Si el generador cambia el formato y el
consumidor no se entera, la página deja de funcionar sin avisar — por eso importa saber quién
escribe cada uno.</p>
<table><thead><tr><th>Fichero</th><th>Qué guarda</th><th>Quién lo escribe</th><th>Quién lo lee</th></tr></thead>
<tbody>{tb}</tbody></table>
<div class="nota"><b>La regla que evita perder decisiones:</b> lo que escribe el Usuario
(<code>decision</code>, <code>note</code>, <code>tested</code>, <code>nocturno</code>) es
<b>KEEP</b> — sobrevive a cualquier regeneración. Lo que escribe un agente es <b>CARRY</b> y se
actualiza. Un campo nuevo que se olvide de la lista KEEP se borra en el siguiente rebuild, en
silencio: le pasó a <code>refs[]</code>.</div>
<div class="nota warn"><b>Y la que evita pisarse:</b> el merge de <code>report.json</code> es
idempotente <b>por <code>id</code></b>, nunca por concatenación. Concatenar es exactamente cómo se
pierden las decisiones.</div>"""
    return page("Qué datos maneja", "core · capa 3 · datos", cuerpo, gen)

def flujo(repo, plan, gen):
    gates = [("check-ram.sh", "hooks", "Antes de cualquier test. OOM = fallo crítico"),
             ("task_progress.py --gate", "scripts", "Cierre de wave: los checkboxes son aritmética"),
             ("spec_lint.py", "scripts", "Estructura de la spec: ERROR bloquea, WARN se documenta"),
             ("check_mechanisms.py", "scripts", "Que los mecanismos declarados existan de verdad"),
             ("check_shared_block.py", "scripts", "Que el CSS compartido no diverja entre plantillas"),
             ("audit_sistema_ia.py --gate", "scripts", "Que el proyecto tenga las piezas que su código pide")]
    fg = "".join(
        f"<tr><td><code>{g}</code></td><td>{'✅' if os.path.exists(os.path.join(repo,'.claude',d,g.split()[0])) else '⚠️'}</td><td>{q}</td></tr>"
        for g, d, q in gates)
    inf = "sources/04-flujo-y-human-in-the-loop.html"
    enlace = (f'<p><a href="{_href_plan(plan, inf)}"><b>→ El flujo completo, paso a paso, con la tabla de qué tiene que '
              f'hacer la persona en cada parada</b></a></p>') if os.path.exists(os.path.join(plan, inf)) else ""
    cuerpo = f"""<h1>Cómo se trabaja, y dónde para a esperarte</h1>
<p class="lead">Un agente que trabaja solo hasta el final no es autonomía: es un riesgo sin
supervisión. Estas son las paradas — y lo importante es que <b>hay tres clases distintas y se
confunden constantemente</b>.</p>

<h2>Las tres clases de parada</h2>
<table><thead><tr><th>Clase</th><th>Quién la dispara</th><th>¿Se salta?</th><th>Qué haces tú</th></tr></thead><tbody>
<tr><td><b>Gate determinista</b></td><td>un script con exit ≠ 0</td><td><b>No</b> — no lo decide el modelo</td><td>Normalmente nada: arreglar lo que dice</td></tr>
<tr><td><b>Aprobación</b></td><td>el catálogo de <code>governance.md</code> §2</td><td>Solo aprobándola</td><td><b>Decidir</b>: sí, no, o con cambios</td></tr>
<tr><td><b>Escalado</b></td><td>el propio agente, cuando duda</td><td>Sigue si no contestas y es reversible</td><td><b>Responder la duda</b>, no revisar el trabajo</td></tr>
</tbody></table>
<div class="nota"><b>Solo la segunda es realmente «aprobar».</b> La primera protege de un fallo
mecánico; la tercera, de que el agente adivine.</div>


<h2>El recorrido de una tarea grande, y dónde se detiene</h2>
<div class="gwrap"><svg viewBox="0 0 1080 300" style="width:100%;height:300px" role="img"
  aria-label="Diagrama del flujo de una tarea grande con sus puntos de parada">
 <defs><marker id="f" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
   <path d="M0,0 L0,6 L9,3 z" fill="rgba(27,42,74,.4)"/></marker></defs>

 <text x="20" y="24" style="font:600 11px ui-monospace;fill:#c2410c;letter-spacing:.1em">EL RECORRIDO</text>

 <!-- fila 1: los gates de plan -->
 <rect x="20" y="42" width="150" height="56" rx="7" fill="#fff" stroke="#c2410c" stroke-width="2"/>
 <rect x="20" y="42" width="150" height="4" rx="2" fill="#c2410c"/>
 <text x="32" y="66" style="font:600 12px -apple-system;fill:#1b2a4a">Gate 0b · dudas</text>
 <text x="32" y="84" style="font:10.5px -apple-system;fill:#6b6b76">⏸ RESPONDES</text>

 <line x1="170" y1="70" x2="205" y2="70" stroke="rgba(27,42,74,.4)" marker-end="url(#f)"/>
 <rect x="210" y="42" width="150" height="56" rx="7" fill="#fff" stroke="#c2410c" stroke-width="2"/>
 <rect x="210" y="42" width="150" height="4" rx="2" fill="#c2410c"/>
 <text x="222" y="66" style="font:600 12px -apple-system;fill:#1b2a4a">Gate 0 · Otto</text>
 <text x="222" y="84" style="font:10.5px -apple-system;fill:#6b6b76">⏸ APRUEBAS la jugada</text>

 <line x1="360" y1="70" x2="395" y2="70" stroke="rgba(27,42,74,.4)" marker-end="url(#f)"/>
 <rect x="400" y="42" width="180" height="56" rx="7" fill="#fff" stroke="rgba(27,42,74,.25)"/>
 <text x="412" y="66" style="font:600 12px -apple-system;fill:#1b2a4a">Gates A-E</text>
 <text x="412" y="84" style="font:10.5px -apple-system;fill:#6b6b76">research · ADR · vía de datos</text>

 <line x1="580" y1="70" x2="615" y2="70" stroke="rgba(27,42,74,.4)" marker-end="url(#f)"/>
 <rect x="620" y="42" width="150" height="56" rx="7" fill="#f6f4ef" stroke="rgba(27,42,74,.25)"/>
 <text x="632" y="72" style="font:600 12px -apple-system;fill:#1b2a4a">plan escrito</text>

 <!-- baja a la fila 2 -->
 <path d="M695,98 L695,124 L60,124 L60,148" fill="none" stroke="rgba(27,42,74,.4)" marker-end="url(#f)"/>

 <!-- fila 2: ejecución con gates deterministas -->
 <rect x="20" y="152" width="190" height="66" rx="7" fill="#fff" stroke="#2563eb" stroke-width="2"/>
 <rect x="20" y="152" width="190" height="4" rx="2" fill="#2563eb"/>
 <text x="32" y="176" style="font:600 12px -apple-system;fill:#1b2a4a">waves + gates</text>
 <text x="32" y="193" style="font:10px ui-monospace;fill:#6b6b76">check-ram · task_progress</text>
 <text x="32" y="209" style="font:600 10px -apple-system;fill:#2563eb">NO LO DECIDE EL MODELO</text>

 <line x1="210" y1="185" x2="245" y2="185" stroke="rgba(27,42,74,.4)" marker-end="url(#f)"/>
 <rect x="250" y="152" width="170" height="66" rx="7" fill="#fff" stroke="rgba(27,42,74,.25)"/>
 <text x="262" y="176" style="font:600 12px -apple-system;fill:#1b2a4a">verificación</text>
 <text x="262" y="194" style="font:10.5px -apple-system;fill:#6b6b76">4 niveles · doble evidencia</text>
 <text x="262" y="210" style="font:10.5px -apple-system;fill:#6b6b76">+ /qa-loop si hay UI</text>

 <line x1="420" y1="185" x2="455" y2="185" stroke="rgba(27,42,74,.4)" marker-end="url(#f)"/>
 <rect x="460" y="152" width="160" height="66" rx="7" fill="#fff" stroke="#c2410c" stroke-width="2"/>
 <rect x="460" y="152" width="160" height="4" rx="2" fill="#c2410c"/>
 <text x="472" y="176" style="font:600 12px -apple-system;fill:#1b2a4a">READY_MERGE</text>
 <text x="472" y="194" style="font:10.5px -apple-system;fill:#6b6b76">⏸ APRUEBAS</text>

 <line x1="620" y1="185" x2="655" y2="185" stroke="rgba(27,42,74,.4)" marker-end="url(#f)"/>
 <rect x="660" y="152" width="160" height="66" rx="7" fill="#fff" stroke="#c2410c" stroke-width="2"/>
 <rect x="660" y="152" width="160" height="4" rx="2" fill="#c2410c"/>
 <text x="672" y="176" style="font:600 12px -apple-system;fill:#1b2a4a">READY_COMMIT</text>
 <text x="672" y="194" style="font:10.5px -apple-system;fill:#6b6b76">⏸ APRUEBAS</text>

 <line x1="820" y1="185" x2="855" y2="185" stroke="#991b1b" stroke-dasharray="4 3" marker-end="url(#f)"/>
 <rect x="860" y="152" width="150" height="66" rx="7" fill="#fef2f2" stroke="#991b1b" stroke-width="2"/>
 <rect x="860" y="152" width="150" height="4" rx="2" fill="#991b1b"/>
 <text x="872" y="176" style="font:600 12px -apple-system;fill:#991b1b">push</text>
 <text x="872" y="194" style="font:10.5px -apple-system;fill:#991b1b">DECISIÓN APARTE</text>

 <!-- leyenda -->
 <rect x="20" y="248" width="14" height="12" rx="3" fill="#c2410c"/>
 <text x="42" y="259" style="font:11px -apple-system;fill:#6b6b76">para y espera a una persona</text>
 <rect x="270" y="248" width="14" height="12" rx="3" fill="#2563eb"/>
 <text x="292" y="259" style="font:11px -apple-system;fill:#6b6b76">gate determinista: bloquea sin preguntar</text>
 <rect x="640" y="248" width="14" height="12" rx="3" fill="#991b1b"/>
 <text x="662" y="259" style="font:11px -apple-system;fill:#6b6b76">nunca automático, ni de madrugada</text>
</svg></div>

<h2>Los gates que existen de verdad</h2>
<p>Estos no dependen de que nadie lea nada: son scripts, y bloquean.</p>
<table><thead><tr><th>Gate</th><th>Existe</th><th>Qué protege</th></tr></thead><tbody>{fg}</tbody></table>

<h2>El flujo, por situación</h2>
<table><thead><tr><th>Situación</th><th>Paradas</th></tr></thead><tbody>
<tr><td><b>Bugfix de 1-3 ficheros</b></td><td><b>Ninguna.</b> Meter ceremonia aquí es lo que hace que se dejen de leer los avisos</td></tr>
<tr><td><b>Tarea grande</b></td><td>Gate 0b (responde dudas) → Otto → research / mapa / ADR / vía de datos → waves con gates → <b>READY_MERGE</b> → <b>READY_COMMIT</b></td></tr>
<tr><td><b>Con interfaz</b></td><td>+ <code>/qa-loop</code> sobre build congelado; si no converge en 5 rondas, escala</td></tr>
<tr><td><b>Sin nadie mirando</b></td><td>Criterio de parada · Stop hook · tope de presupuesto · <b>commit sí, push no</b></td></tr>
<tr><td><b>Incidente en producción</b></td><td><code>governance.md</code> §8: <b>esto no aplica</b>. Solo el post-mortem es obligatorio</td></tr>
</tbody></table>
{enlace}
<div class="nota warn"><b>Un agente nunca pregunta en blanco.</b> El formato obligado exige que
traiga su mejor respuesta, la alternativa y el coste de equivocarse. Si te llega un «¿qué hago?»
pelado, el agente está incumpliendo.</div>
<div class="nota"><b>Límite honesto:</b> esto refleja lo que las rules <b>declaran</b>. Con
enforcement real solo están los gates de arriba y los hooks; el resto depende de que el agente lea
y obedezca — que es justo el motivo de bajar de capa lo que no se puede permitir que se ignore.</div>"""
    return page("Cómo se trabaja", "core · capa 5 · flujo y paradas", cuerpo, gen)

def decisiones(repo, gen):
    adr_dir = os.path.join(repo, ".docs", "adr")
    adrs = sorted(f for f in os.listdir(adr_dir) if f.endswith(".md")) if os.path.isdir(adr_dir) else []
    adrs = [a for a in adrs if a.lower() != "readme.md"]
    if adrs:
        tb = "".join(f'<tr><td><code>{html.escape(a)}</code></td>'
                     f'<td><a href="../../adr/{html.escape(a)}">abrir</a></td></tr>' for a in adrs)
        cuerpo = f"<h1>Qué se decidió y por qué</h1><table><tbody>{tb}</tbody></table>"
    else:
        cuerpo = """<h1>Qué se decidió y por qué</h1>
<p class="lead">Un ADR es una página que registra una decisión <b>cara de revertir</b>, con su
contexto, sus alternativas descartadas y sus consecuencias.</p>
<div class="nota warn"><b>No hay ninguno todavía.</b> Y sí ha habido decisiones que lo merecían:
el grafo propio en vez de graphify para el harness, el baseline por fichero en vez de por línea,
o el <code>report.json</code> como fuente única del informe. Se tomaron y no se registraron.</div>
<h2>Qué lo dispara</h2>
<p>El <b>Gate D</b> de <code>rules/plan-gates.md</code>: una tarea grande que cambia
<b>arquitectura, schema o un contrato de API</b> no cierra el plan sin su ADR. Acotado a propósito
— si se pide para toda tarea grande, no se escribe ninguno.</p>
<pre><code>cp .claude/templates/adr-template.md .docs/adr/0001-&lt;slug&gt;.md</code></pre>
<div class="nota"><b>Por qué importa, en una frase:</b> git dice QUÉ cambió; el ADR dice
<b>por qué se descartó lo otro</b>. Sin él, dentro de un año la discusión empieza de cero — o peor,
se cambia sin saber qué se rompe.</div>"""
    return page("Qué se decidió", "core · capa 6 · decisiones", cuerpo, gen)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# core · capa 8 · LAS PIEZAS. El inventario de lo que el harness tiene y —lo que no se sabía—
# CÓMO llega cada pieza a usarse. Un comando lo tecleas, un hook salta solo, y una skill solo
# existe si el modelo la encuentra por su `description`. Esa columna es la que convierte una
# lista de nombres en algo con lo que se puede trabajar.
GRUPOS = [
    ("command",  "Comandos",  "Los tecleas: <code>/nombre</code>. Es la superficie que usa una persona."),
    ("workflow", "Workflows", "También se teclean. Orquestan varios agentes de forma determinista."),
    ("skill",    "Skills",    "Procedimientos. El modelo las activa por su <code>description</code>: si está vaga, la skill no se activa nunca."),
    ("agente",   "Agentes",   "Criterio independiente, con contexto limpio. Quién audita qué."),
    ("rule",     "Rules",     "El criterio escrito. Advisory: se leen, no se ejecutan."),
    ("hook",     "Hooks",     "Saltan solos en un evento. Lo único que bloquea de verdad."),
    ("pattern",  "Patrones",  "Cómo se escribe el código en esta casa, con su comprobador."),
    ("script",   "Scripts",   "Los gates y generadores que hacen el trabajo determinista."),
    ("plugin",   "Plugins",   "Capacidades de terceros. Instalarlas es cadena de suministro, no comodidad."),
]
COMO = {"se teclea": ("teclea", "La escribes tú"),
        "cita":      ("cita",   "El modelo la encuentra"),
        "evento":    ("evento", "Salta sola"),
        "instalada": ("plug",   "Instalada")}


def sistema(repo, gen):
    """Las piezas del harness, buscables. Fuente: graph-dataset.full.json (gen_harness_graph.py).

    Se lee el `.full` y NO el enfocado: el enfocado colapsa comandos, plugins y workflows en un
    nodo «(+21 más)» para que el GRAFO se lea, y para un inventario eso es exactamente lo
    contrario de lo que hace falta.
    """
    ruta = os.path.join(repo, ".claude", "graph-dataset.full.json")
    if not os.path.exists(ruta):
        cuerpo = ("<h1>Las piezas del sistema</h1>"
                  "<p class='lead'>Todavía no se ha generado el inventario.</p>"
                  "<pre><code>python3 .claude/scripts/gen_harness_graph.py</code></pre>")
        return page("Las piezas — sin datos todavía", "core · capa 8 · las piezas", cuerpo, gen)

    d = json.load(open(ruta, encoding="utf-8"))
    nodos = [n for n in d["nodes"] if n.get("kind") != "agregado" and n["group"] != "roto"]
    por = {}
    for n in nodos:
        por.setdefault(n["group"], []).append(n)

    tecleables = sum(len(por.get(g, [])) for g in ("command", "workflow"))
    por_cita = sum(len(por.get(g, [])) for g in ("skill", "agente", "rule", "pattern", "script"))
    huerfanas = [n for n in nodos if n.get("huerfana")]

    filas = []
    for gid, titulo, quees in GRUPOS:
        ns = sorted(por.get(gid, []), key=lambda x: -x.get("fan_in", 0))
        if not ns:
            continue
        filas.append(
            '<section class="grp" data-g="%s"><h2>%s <span class="n">%d</span></h2>'
            '<p class="quees">%s</p><table class="inv"><thead><tr><th>Pieza</th>'
            '<th>Para qué</th><th>Cómo se usa</th>'
            '<th title="cuántas piezas la nombran">Citada</th></tr></thead><tbody>'
            % (gid, html.escape(titulo), len(ns), quees))
        for n in ns:
            cls, txt = COMO.get(n.get("descubrimiento", ""), ("cita", "—"))
            desc = html.escape((n.get("desc") or "").strip()) or '<i class="sin">sin descripción</i>'
            fic = html.escape((n.get("files") or [""])[0])
            huer = (' <span class="huer" title="fan_in 0 y solo se encuentra por cita">'
                    'nadie la nombra</span>') if n.get("huerfana") else ""
            filas.append(
                '<tr data-b="%s"><td><b>%s</b>%s<br><code class="ruta">%s</code></td>'
                '<td>%s</td><td><span class="como %s">%s</span></td><td class="fi">%d</td></tr>'
                % (html.escape((n["label"] + " " + (n.get("desc") or "")).lower()),
                   html.escape(n["label"]), huer, fic, desc, cls, txt, n.get("fan_in", 0)))
        filas.append("</tbody></table></section>")

    chips = "".join('<button class="chip" data-f="%s">%s <b>%d</b></button>'
                    % (g, t, len(por.get(g, []))) for g, t, _ in GRUPOS if por.get(g))

    js = """
(function(){
  var q=document.getElementById('q'), cuenta=document.getElementById('cuenta'),
      chips=[].slice.call(document.querySelectorAll('.chip')), filtro='*';
  function pinta(){
    var t=(q.value||'').trim().toLowerCase(), vis=0;
    [].forEach.call(document.querySelectorAll('.grp'), function(s){
      var okg=(filtro==='*'||s.dataset.g===filtro), n=0;
      [].forEach.call(s.querySelectorAll('tbody tr'), function(tr){
        var ok=okg && (!t || tr.dataset.b.indexOf(t)>=0);
        tr.style.display=ok?'':'none'; if(ok) n++;
      });
      s.style.display=n?'':'none'; vis+=n;
    });
    cuenta.textContent=vis+' pieza'+(vis===1?'':'s')+((t||filtro!=='*')?' · filtrando':'');
  }
  q.addEventListener('input', pinta);
  chips.forEach(function(c){ c.addEventListener('click', function(){
    chips.forEach(function(x){x.classList.remove('on');}); c.classList.add('on');
    filtro=c.dataset.f; pinta();
  });});
  pinta();
})();
"""

    cuerpo = """<h1>Las piezas del <em>sistema</em></h1>
<p class="lead">Todo lo que este harness tiene instalado, y <b>cómo llega cada pieza a usarse</b>.
No es lo mismo un comando que tecleas que una skill que el modelo tiene que <i>encontrar</i>:
lo segundo depende de que su descripción esté bien escrita, y por eso una pieza que nadie
nombra es una pieza que, en la práctica, no existe.</p>

<div class="kpis">
  <div class="kpi"><b>%d</b><span>piezas en total</span></div>
  <div class="kpi"><b>%d</b><span>las escribes tú (/comando)</span></div>
  <div class="kpi"><b>%d</b><span>el modelo las encuentra</span></div>
  <div class="kpi%s"><b>%d</b><span>no las nombra nadie</span></div>
</div>

<div class="aviso"><b>La columna que importa es «cómo se usa».</b> Las %d piezas que el modelo
tiene que encontrar solo se activan si su <code>description</code> lo permite: con una vaga, la
pieza no se dispara nunca y parece que no está. Es la diferencia entre una skill muerta y una
mal descrita — y solo se distingue arreglando primero la descripción
(<code>rules/self-improvement-loop.md</code> §5).</div>

<div class="filtros">
  <input id="q" type="search" placeholder="Buscar por nombre o por para qué sirve…" autocomplete="off">
  <div class="chips"><button class="chip on" data-f="*">Todas</button>%s</div>
</div>
<p id="cuenta" class="cuenta"></p>

%s
<script>%s</script>""" % (len(nodos), tecleables, por_cita,
                          " warn" if huerfanas else "", len(huerfanas), por_cita,
                          chips, "".join(filas), js)
    return page("Las piezas del sistema", "core · capa 8 · las piezas", cuerpo, gen)


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


def _href_plan(plan, pag):
    """PV-3 · un enlace a una página DEL PLAN, escrito desde donde toque. Si esta capa se
    escribe en .docs/core/, la ruta pasa por ../plans/<plan>/ — la misma en disco y servida,
    porque server.py monta /plans/. Si se escribe en el propio plan, es relativa y ya."""
    return pag if _out_dir(plan) == plan else f"../plans/{os.path.basename(plan)}/{pag}"

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    plan = os.path.abspath(sys.argv[1])
    repo = subprocess.run(["git", "-C", plan, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip() or os.getcwd()
    gen = date.today().isoformat()
    for nombre, fn in (("core-overview.html", lambda: overview(repo, gen)),
                       ("core-arquitectura.html", lambda: arquitectura(repo, plan, gen)),
                       ("core-datos.html", lambda: datos(repo, gen)),
                       ("core-flujo.html", lambda: flujo(repo, plan, gen)),
                       ("core-sistema.html", lambda: sistema(repo, gen)),
                       ("core-decisiones.html", lambda: decisiones(repo, gen))):
        open(os.path.join(_out_dir(plan), nombre), "w", encoding="utf-8").write(fn())
        print(f"OK {nombre}")

if __name__ == "__main__":
    main()
