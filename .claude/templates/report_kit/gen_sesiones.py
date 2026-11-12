#!/usr/bin/env python3
"""gen_sesiones.py — la pestaña «Sesiones»: qué sesiones de Claude hay que crear, y cómo.

EL HUECO QUE CIERRA (petición del Usuario, 2026-09-26):
Cuando un plan se reparte en frentes paralelos —sesiones en worktrees mandadas desde una sesión
directora—, la información de «qué sesión crear, con qué nombre, en qué worktree, qué ficheros
reclama y con qué comando se lanza» vivía en prosa dentro del plan. El Usuario pidió verla en el
informe, con el comando listo para copiar, para ponerle nombre a cada sesión o dejar que la
directora las cree.

LA REGLA QUE LO HACE FIABLE: una sola fuente.
`<plan>/sesiones.json` es lo único que se edita. De él salen DOS cosas que no pueden divergir:
  1. esta página (`sesiones.html`), con el comando de cada sesión;
  2. el comando que se EJECUTA de verdad: `gen_sesiones.py --comando <plan> <nombre>` imprime
     exactamente el mismo que se enseña, y es lo que llama el lanzador. Si el comando se
     escribiera en dos sitios, el que se enseña y el que corre acabarían siendo distintos.

Con `--vivo`, cruza cada sesión con `claude agents --json` y pinta su estado REAL (activa, en
espera, no existe). Sin `--vivo` pinta el estado declarado en el JSON, y lo dice.

Uso:
    python3 gen_sesiones.py <plan> [--vivo]        # genera sesiones.html
    python3 gen_sesiones.py --comando <plan> <nombre>   # imprime el comando de lanzamiento
Luego: python3 render_nav.py --all <plan>
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import shlex
import subprocess
import sys

KIT = pathlib.Path(__file__).parent

EJEMPLO = {
    "directora": {"nombre": "<sesión que manda>", "cwd": "<ruta>", "franja": "main"},
    "repo": "<ruta del repo>",
    "pizarra": "<carpeta fuera de git para los reportes de cada frente>",
    "sesiones": [{
        "nombre": "evo-catalogo", "ola": "4b-5", "estado": "pendiente",
        "worktree": ".claude/worktrees/evo-catalogo", "rama": "worktree-evo-catalogo",
        "franja": {"db": "…", "runserver": 8032},
        "mision": "…", "claims": ["apps/catalog/**"], "no_toca": ["apps/agents/**"],
        "depende_de": ["ola 4a"], "prompt": "mando/prompts/evo-catalogo.md",
    }],
}


def shared_css() -> str:
    """Los tokens del set, leídos al generar (no copiados): así no puede divergir del resto."""
    tpl = (KIT / "index.template.html").read_text(encoding="utf-8")
    m = re.search(r"/\* SHARED:BEGIN \*/(.*?)/\* SHARED:END \*/", tpl, re.S)
    return m.group(1) if m else ""


def cargar(plan: pathlib.Path) -> dict | None:
    f = plan / "sesiones.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def comando(doc: dict, plan: pathlib.Path, s: dict) -> str:
    """EL comando de lanzamiento. Único sitio donde se construye: la página y el lanzador lo leen."""
    repo = doc.get("repo", ".")
    piz = doc.get("pizarra")
    modo = s.get("permission_mode") or doc.get("permission_mode") or "acceptEdits"
    prompt = plan / s["prompt"] if s.get("prompt") else None
    partes = ["claude", "--bg", "-n", s["nombre"], "--worktree", s["nombre"], "--permission-mode", modo]
    if piz:
        partes += ["--add-dir", piz]
    partes += ["--add-dir", str(plan / "mando")]
    base = " ".join(shlex.quote(p) for p in partes)
    if prompt:
        base += f' "$(cat {shlex.quote(str(prompt))})"'
    # La guarda de las diez comprobaciones (AN-20): la del template, salvo que el plan traiga aún
    # el lanzador viejo en su pizarra (`<pizarra>/bin/lanzar_frente.sh <nombre>`, sin el plan).
    viejo = pathlib.Path(piz, "bin", "lanzar_frente.sh") if piz else None
    if viejo and viejo.exists():
        guarda = f"bash {shlex.quote(str(viejo))} {shlex.quote(s['nombre'])} --solo-guarda && "
    else:
        guarda = (f"bash .claude/scripts/launch_front.sh {shlex.quote(str(plan))} "
                  f"{shlex.quote(s['nombre'])} --solo-guarda && ")
    return f"cd {shlex.quote(repo)} && {guarda}{base}"


def comando_alt(doc: dict, plan: pathlib.Path, s: dict) -> str:
    """Alternativa interactiva (tmux), por si --bg y --worktree no casan en una versión concreta."""
    return comando(doc, plan, s).replace("claude --bg ", "claude --tmux ")


def estado_vivo() -> dict[str, dict]:
    try:
        r = subprocess.run(["claude", "agents", "--json"], capture_output=True, text=True, timeout=20)
        return {a.get("name"): a for a in json.loads(r.stdout or "[]") if a.get("name")}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {}


def chips(valores, clase="chip") -> str:
    return "".join(f'<span class="{clase}">{html.escape(str(v))}</span>' for v in valores or [])


def tarjeta(doc: dict, plan: pathlib.Path, s: dict, vivo: dict | None) -> str:
    nombre = s["nombre"]
    if vivo is not None:
        a = vivo.get(nombre)
        estado = (a.get("status") or a.get("state") or "?") if a else "no existe todavía"
        fuente = "en vivo · claude agents"
    else:
        estado, fuente = s.get("estado", "pendiente"), "declarado en sesiones.json"
    fr = s.get("franja") or {}
    franja = " · ".join(f"{k} {v}" for k, v in fr.items())
    cmd = comando(doc, plan, s)
    alt = comando_alt(doc, plan, s)
    return f"""
<article class="ses" id="{html.escape(nombre)}">
  <header><h2>{html.escape(nombre)}</h2>
    <span class="est est-{re.sub(r'[^a-z]', '', estado.lower())[:12]}">{html.escape(estado)}</span>
    <span class="fuente">{fuente}</span></header>
  <p class="mision">{html.escape(s.get('mision', ''))}</p>
  <dl>
    <dt>Ola</dt><dd>{html.escape(str(s.get('ola', '—')))}</dd>
    <dt>Worktree · rama</dt><dd><code>{html.escape(s.get('worktree', '—'))}</code> · <code>{html.escape(s.get('rama', '—'))}</code></dd>
    <dt>Franja</dt><dd>{html.escape(franja or '—')}</dd>
    <dt>Reclama</dt><dd>{chips(s.get('claims'))}</dd>
    <dt>No toca</dt><dd>{chips(s.get('no_toca'), 'chip chip-no')}</dd>
    <dt>Depende de</dt><dd>{chips(s.get('depende_de'), 'chip chip-dep')}</dd>
  </dl>
  <div class="cmd"><div class="cmd-h">Comando para crearla <button data-copy="{html.escape(cmd)}">copiar</button></div>
    <pre>{html.escape(cmd)}</pre></div>
  <details><summary>Alternativa interactiva (tmux)</summary>
    <div class="cmd"><div class="cmd-h">Si <code>--bg</code> no casa con <code>--worktree</code> <button data-copy="{html.escape(alt)}">copiar</button></div>
    <pre>{html.escape(alt)}</pre></div></details>
</article>"""


def pagina(doc: dict | None, plan: pathlib.Path, vivo: dict | None) -> str:
    if doc is None:
        cuerpo = ('<section class="vacio"><h2>Este plan no reparte trabajo en sesiones</h2>'
                  "<p>Si el plan tiene frentes paralelos (worktrees, sesiones mandadas por una directora), "
                  "declara cada sesión en <code>sesiones.json</code>, dentro del plan, y vuelve a generar:</p>"
                  f"<pre>{html.escape(json.dumps(EJEMPLO, ensure_ascii=False, indent=2))}</pre>"
                  "<p class=\"nota\">Se enseña vacía a propósito: decir que no hay reparto es información.</p></section>")
        intro = ""
    else:
        d = doc.get("directora", {})
        sesiones = doc.get("sesiones", [])
        reglas = "".join(f"<li>{html.escape(r)}</li>" for r in doc.get("reglas", []))
        nopar = "".join(f"<li>{html.escape(r)}</li>" for r in doc.get("no_en_paralelo", []))
        subag = "".join(f"<li><strong>{html.escape(x.get('id', ''))}</strong> — {html.escape(x.get('tema', ''))}</li>"
                        for x in doc.get("subagentes", []))
        intro = f"""
<section class="dir">
  <h2>La directora</h2>
  <p><strong>{html.escape(d.get('nombre', '—'))}</strong> · cwd <code>{html.escape(d.get('cwd', '—'))}</code>
  · franja <code>{html.escape(str(d.get('franja', '—')))}</code></p>
  <p class="nota">Manda por el canal entre sesiones con un <em>puntero</em> a un encargo commiteado
  (<code>mando/encargos/&lt;frente&gt;.md</code>); cada frente reporta en su fichero de la pizarra
  <code>{html.escape(doc.get('pizarra', '—'))}</code>. El prompt inicial de cada sesión es la
  autorización del Usuario para aceptar esos encargos (rules/parallelization.md §Sesiones que se hablan).</p>
  {'<h3>Reglas del reparto</h3><ul>' + reglas + '</ul>' if reglas else ''}
  {'<h3>Lo que NO va en paralelo</h3><ul>' + nopar + '</ul>' if nopar else ''}
  {'<h3>Mejor con subagentes desde la directora (no son sesiones)</h3><ul>' + subag + '</ul>' if subag else ''}
</section>"""
        cuerpo = "".join(tarjeta(doc, plan, s, vivo) for s in sesiones) or '<p class="nota">sesiones.json no declara ninguna sesión.</p>'
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<!-- GENERADO por gen_sesiones.py desde sesiones.json — NO editar a mano. -->
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report-kit · Sesiones</title>
<style>
{shared_css()}
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55}}
  .wrap{{max-width:1100px;margin:0 auto;padding:0 22px 60px}}
  .page-head{{border-bottom:1px solid var(--line);padding:36px 0 24px;margin-bottom:2rem}}
  .page-head h1{{font-size:28px;margin:0 0 8px;letter-spacing:-.01em}}
  .page-head .sub{{font-size:16px;color:var(--muted);max-width:78ch;margin:0}}
  code{{background:var(--line);border-radius:4px;padding:.1em .35em;font-size:.9em}}
  .dir,.ses,.vacio{{border:1px solid var(--line);border-radius:var(--radius-md);background:var(--card);
    padding:1.2rem 1.4rem;margin:0 0 1.4rem}}
  .ses header{{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap}}
  .ses h2,.dir h2{{margin:0;font-size:1.2rem}}
  .dir h3{{font-size:.95rem;margin:1rem 0 .3rem}}
  .est{{font:600 .72rem/1 system-ui;border-radius:var(--radius-pill);padding:.3rem .6rem;
    background:var(--line);color:var(--ink)}}
  .fuente,.nota{{font-size:.78rem;color:var(--muted)}}
  .mision{{margin:.6rem 0 .8rem}}
  dl{{display:grid;grid-template-columns:max-content 1fr;gap:.35rem 1rem;margin:0 0 1rem;font-size:.9rem}}
  dt{{color:var(--muted)}} dd{{margin:0}}
  .chip{{display:inline-block;font-size:.75rem;border:1px solid var(--line);border-radius:var(--radius-pill);
    padding:.1rem .5rem;margin:0 .3rem .3rem 0;font-family:ui-monospace,monospace}}
  .chip-no{{opacity:.75;text-decoration:line-through}}
  .cmd{{border:1px solid var(--line);border-radius:var(--radius-md);overflow:hidden;margin:.4rem 0}}
  .cmd-h{{display:flex;justify-content:space-between;align-items:center;padding:.45rem .8rem;
    font-size:.8rem;border-bottom:1px solid var(--line)}}
  .cmd pre,.vacio pre{{margin:0;padding:.8rem;overflow-x:auto;font-size:.78rem;white-space:pre-wrap;word-break:break-all}}
  button{{font:inherit;font-size:.78rem;border:1px solid var(--line);background:var(--paper);
    border-radius:var(--radius-pill);padding:.25rem .8rem;cursor:pointer}}
  button:focus-visible{{outline:2px solid var(--blue);outline-offset:2px}}
  details summary{{cursor:pointer;font-size:.85rem;color:var(--muted);margin-top:.4rem}}
</style>
</head>
<body>
<!-- NAV:BEGIN -->
<!-- NAV:END -->
<main class="wrap">
  <header class="page-head">
    <h1>Sesiones</h1>
    <p class="sub">Qué sesiones de Claude hay que crear para este plan, qué hace cada una, qué ficheros
    reclama y el comando exacto para lanzarla. El comando que se ve aquí es el mismo que ejecuta el
    lanzador: los dos salen de <code>sesiones.json</code>.</p>
  </header>
  {intro}
  {cuerpo}
</main>
<script>
document.addEventListener('click', function (e) {{
  var b = e.target.closest('button[data-copy]'); if (!b) return;
  var t = b.getAttribute('data-copy');
  var ok = function () {{ var o = b.textContent; b.textContent = 'copiado ✓'; setTimeout(function () {{ b.textContent = o; }}, 1400); }};
  if (navigator.clipboard) navigator.clipboard.writeText(t).then(ok, function () {{ prompt('Copia el comando:', t); }});
  else prompt('Copia el comando:', t);
}});
</script>
</body>
</html>
"""


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--comando"]:
        if len(args) != 3:
            sys.exit("uso: gen_sesiones.py --comando <plan> <nombre>")
        plan = pathlib.Path(args[1]).resolve()
        doc = cargar(plan)
        s = next((x for x in (doc or {}).get("sesiones", []) if x.get("nombre") == args[2]), None)
        if not doc or not s:
            sys.exit(f"ERROR: «{args[2]}» no está en {plan}/sesiones.json")
        print(comando(doc, plan, s))
        return 0
    if not args:
        sys.exit("uso: gen_sesiones.py <plan> [--vivo]  |  --comando <plan> <nombre>")
    plan = pathlib.Path(args[0]).resolve()
    if not plan.is_dir():
        sys.exit(f"ERROR: no existe {plan}")
    doc = cargar(plan)
    vivo = estado_vivo() if "--vivo" in args else None
    (plan / "sesiones.html").write_text(pagina(doc, plan, vivo), encoding="utf-8")
    n = len((doc or {}).get("sesiones", []))
    print(f"OK {plan / 'sesiones.html'} — {n} sesión(es)" + (" · estado en vivo" if vivo is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
