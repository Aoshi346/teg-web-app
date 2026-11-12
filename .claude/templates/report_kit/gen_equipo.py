#!/usr/bin/env python3
"""gen_equipo.py — la capa EQUIPO del Core: quién forma el equipo IA y qué ha hecho.

POR QUÉ NO EXISTÍA Y HACE FALTA. Los datos estaban todos y nadie los juntaba: el frontmatter de
cada agente (qué audita, su coste de error, su fase de autonomía), el audit log (quién corrió y
cuándo) y las carpetas de feedback (qué rondas dejó en disco). Sin cruzarlos, la pregunta «¿quién
es mi equipo y cuál de ellos ha corrido de verdad?» solo se responde mirando carpetas a mano.

Y el dato que lo justifica: **un agente que nunca ha corrido NO es cobertura**. Trece auditores
declarados con diez sin estrenar es la diferencia entre parecer cubierto y estarlo.
"""
import html, json, os, re, subprocess, sys
from collections import Counter
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))

def shared():
    t = open(os.path.join(HERE, "index.template.html"), encoding="utf-8").read()
    return re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", t, re.S).group(0)

def frontmatter(p):
    try:
        t = open(p, encoding="utf-8").read()
    except OSError:
        return {}
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    d = {}
    if m:
        for ln in m.group(1).splitlines():
            k, _, v = ln.partition(":")
            if _: d[k.strip()] = v.strip().strip('"').strip("'")
    d["_desc"] = (d.get("description", "") or "")[:200]
    return d

def corridas(repo):
    """Quién ha corrido DE VERDAD: audit log + carpetas de feedback en disco.

    No se pregunta al agente ni se deduce de que exista: se mira si dejó rastro."""
    vis = Counter()
    alog = os.path.expanduser("~/.claude/audit")
    if os.path.isdir(alog):
        for f in os.listdir(alog):
            try:
                for ln in open(os.path.join(alog, f), encoding="utf-8"):
                    try: d = json.loads(ln)
                    except Exception: continue
                    if d.get("agent"): vis[str(d["agent"]).strip().lower()] += 1
            except OSError:
                continue
    fb = os.path.join(repo, ".docs", "feedback")
    for base, dirs, _ in os.walk(fb) if os.path.isdir(fb) else []:
        for d in dirs:
            vis[d.lower()] += 0 if d.lower() in vis else 1
    return vis

def build(repo, plan):
    adir = os.path.join(repo, ".claude", "agents")
    agentes = []
    for f in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        if not f.endswith(".md") or f == "README.md": continue
        fm = frontmatter(os.path.join(adir, f))
        agentes.append({
            "id": f[:-3],
            "err": fm.get("error_cost", ""),
            "fase": fm.get("autonomy_phase", ""),
            "modelo": fm.get("model", ""),
            "desc": fm.get("_desc", ""),
        })
    vis = corridas(repo)
    for a in agentes:
        a["corridas"] = vis.get(a["id"].lower(), 0)

    n = len(agentes)
    sin_fase = sum(1 for a in agentes if not a["fase"])
    sin_err = sum(1 for a in agentes if not a["err"])
    sin_correr = sum(1 for a in agentes if not a["corridas"])
    ERR = {"false-positive": ("marcar lo correcto", "#c2410c"),
           "false-negative": ("que se le escape", "#991b1b"),
           "symmetric": ("simétrico", "#6b6b76")}
    filas = ""
    for a in sorted(agentes, key=lambda x: (-x["corridas"], x["id"])):
        e = ERR.get(a["err"], ("— sin declarar", "#9a958a"))
        filas += (f'<tr><td><code>{html.escape(a["id"])}</code>'
                  f'<div class="q">{html.escape(a["desc"][:110])}…</div></td>'
                  f'<td><span style="color:{e[1]};font-size:12.5px">{e[0]}</span></td>'
                  f'<td class="c">{html.escape(a["fase"] or "—")}</td>'
                  f'<td class="c">{html.escape(a["modelo"] or "—")}</td>'
                  f'<td class="c">{"<b>"+str(a["corridas"])+"</b>" if a["corridas"] else "<span class=no>nunca</span>"}</td>'
                  f'</tr>')

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>El equipo IA</title>
<style>{shared()}</style><style>
  html,body{{margin:0;background:var(--paper);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:15.5px;line-height:1.6}}
  .wrap{{max-width:1120px;margin:0 auto;padding:26px 20px 60px}}
  .eyebrow{{font-family:ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent);font-weight:700}}
  h1{{margin:6px 0 8px;font-size:30px;letter-spacing:-.02em;color:var(--navy)}}
  h2{{margin:28px 0 8px;font-size:19px;color:var(--navy)}}
  .lead{{color:var(--muted);max-width:74ch}}
  .kpis{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}}
  .kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;min-width:96px}}
  .kpi b{{display:block;font-size:23px;color:var(--navy);line-height:1.1}}
  .kpi span{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}}
  table{{width:100%;border-collapse:collapse;margin:12px 0;background:var(--card);
    border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:14px}}
  th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
  th{{background:#f4f1ea;color:var(--navy);font-size:11px;text-transform:uppercase;letter-spacing:.06em}}
  tr:last-child td{{border-bottom:0}}
  td.c{{text-align:center;font-family:ui-monospace,Menlo,monospace;font-size:12.5px}}
  .q{{color:var(--muted);font-size:12.5px;margin-top:2px;max-width:56ch}}
  .no{{color:var(--faint);font-size:12px}}
  code{{font-family:ui-monospace,Menlo,monospace;font-size:.88em;background:#f1ede4;
    border:1px solid var(--line);border-radius:5px;padding:1px 5px}}
  .nota{{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);
    border-radius:12px;padding:14px 16px;margin:18px 0;font-size:14px;color:var(--muted)}}
  .nota b{{color:var(--navy)}}
  footer{{margin-top:32px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--faint)}}
</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
<p class="eyebrow">core · capa 7 · el equipo</p>
<h1>Quién forma el equipo IA</h1>
<p class="lead">Cada agente con lo que audita, <b>qué error le sale caro</b>, cuánta autonomía
tiene y —lo que no se sabía— <b>si ha corrido alguna vez</b>.</p>

<div class="kpis">
  <div class="kpi"><b>{n}</b><span>agentes</span></div>
  <div class="kpi"><b>{n - sin_correr}</b><span>han corrido</span></div>
  <div class="kpi"><b>{sin_fase}</b><span>sin fase declarada</span></div>
  <div class="kpi"><b>{sin_err}</b><span>sin coste de error</span></div>
</div>

<div class="nota"><b>Un agente que nunca ha corrido NO es cobertura.</b> Parece protección y no la
da. Por eso esta columna existe y por eso se mide de la única forma fiable: mirando si dejó rastro
—en el audit log o en una carpeta de feedback—, no preguntándole ni dando por hecho que existir es
haber trabajado.</div>

<div class="nota"><b>El coste de error no es un adorno: es la calibración.</b> A quien le sale caro
el <b>falso negativo</b> (que se le escape algo) reporta ante la duda y acepta ruido. A quien le
sale caro el <b>falso positivo</b> (marcar como problema algo correcto) calla si no tiene evidencia
dura — porque un auditor que marca lo que está bien quema su credibilidad y deja de leerse.
Hoy <b>{sin_err} de {n}</b> no lo declaran, así que operan sin calibrar.</div>

<h2>La flota</h2>
<table><thead><tr><th>Agente</th><th>Su error caro es…</th><th>Fase</th><th>Modelo</th><th>Corridas</th></tr></thead>
<tbody>{filas}</tbody></table>

<div class="nota"><b>Límite honesto.</b> «Corridas» cuenta lo que el audit log registra desde que
empezó a registrar agentes (2026-08-21) más las carpetas de feedback en disco. Un agente que corrió
antes de esa fecha y no dejó carpeta aparece como «nunca» sin serlo. El número sube desde hoy; hasta
que haya semanas de registro, léelo como suelo, no como verdad.</div>

<footer>Generado por <code>gen_equipo.py</code> el {date.today().isoformat()} — no editar a mano.</footer>
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
    if len(sys.argv) < 2: sys.exit("uso: gen_equipo.py <plan-dir>")
    plan = os.path.abspath(sys.argv[1])
    repo = subprocess.run(["git", "-C", plan, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip() or os.getcwd()
    out = os.path.join(_out_dir(plan), "core-equipo.html")
    open(out, "w", encoding="utf-8").write(build(repo, plan))
    print(f"OK {out}")

if __name__ == "__main__":
    main()
