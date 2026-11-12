#!/usr/bin/env python3
"""gen_placeholders.py — genera la página de las pestañas que este plan aún no tiene datos para llenar.

POR QUÉ EXISTE, y es una corrección a lo que hacíamos antes. `render_nav.py` omitía del menú la
pestaña cuyo fichero no existía, con este razonamiento: «una pestaña que da 404 es peor que no
tenerla». Cierto, pero llevaba a algo peor todavía: **el menú cambiaba de un plan a otro**, así que
no había forma de saber si a este informe le falta la Arquitectura o si el informe es de otro tipo.
Y para quien mira, un menú que cambia solo es un menú en el que no se puede confiar.

La tercera salida es la que ya decía `rules/plan-docs-structure.md` desde el principio y se había
perdido: **donde no haya datos, la página dice CÓMO conseguirlos**. Ni 404, ni hueco en el menú:
una página que te dice qué falta, con qué comando se consigue y qué vas a ver cuando esté.

Lo que NO hace, y es deliberado: no inventa contenido de demostración. Publicar un diagrama de
mentira es el anti-pattern que ya costó dos `structure.html` enseñando un Django que no existía.

  python3 gen_placeholders.py <plan> [--perfil proyecto]
"""
import html, json, os, re, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))


def shared_css():
    tpl = open(os.path.join(HERE, "index.template.html"), encoding="utf-8").read()
    return re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", tpl, re.S).group(0)


CSS = """
  html,body{margin:0;background:var(--paper);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:15.5px;line-height:1.62}
  .wrap{max-width:820px;margin:0 auto;padding:38px 20px 70px}
  .eyebrow{font-family:ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent);font-weight:700;margin:0 0 10px}
  h1{font-size:clamp(26px,4vw,38px);margin:0 0 10px;letter-spacing:-.02em}
  .lead{font-size:16.5px;color:var(--muted);margin:0 0 26px}
  .box{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 24px;margin:18px 0}
  .box h2{margin:0 0 8px;font-size:16.5px}
  .box p{margin:0 0 12px;color:var(--muted);font-size:14.5px}
  pre{background:#1b2a4a;color:#f6f4ef;border-radius:10px;padding:13px 15px;overflow-x:auto;
    font-family:ui-monospace,Menlo,monospace;font-size:13px;margin:0}
  .copy{margin-top:9px;font:inherit;font-size:13px;border:1px solid var(--line);background:#fff;
    color:var(--ink);border-radius:9px;padding:6px 12px;cursor:pointer}
  .copy:hover{background:#efece4}
  .nota{border-left:3px solid var(--accent);padding:2px 0 2px 14px;color:var(--muted);
    font-size:14px;margin:14px 0 0}
  .por-que{background:#fbf7ef;border:1px solid #ecdfc8;border-radius:12px;padding:16px 18px;
    color:#6b5b3e;font-size:14px;margin-top:26px}
  footer{margin-top:34px;color:var(--faint);font-size:12.5px}
"""


# ⚠️ El placeholder emite los marcadores NAV:BEGIN/END ÉL MISMO, y no es cosmético.
# `render_nav.py --all` solo AUTO-inserta marcadores en la raíz del plan y en sources/; más
# adentro exige que la página ya los traiga (esa guarda existe para no pintarle la topnav a los
# fixtures de material vendorizado, caso PRU-9). Sin esta línea, los placeholders de subcarpeta
# —`feedback/personas.html`, `schemas/schemas.html`— salían SIN NAV: al entrar, el menú
# desaparecía. Es justo el anti-pattern «nav parcial» de plan-docs-structure.md, y lo introdujo
# T-047 al crear los placeholders. Detectado por el Usuario navegando, no por el generador.
def page(label, titulo, como, plan_nombre):
    cmd = html.escape(como.get("cmd", ""))
    return f"""<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(label)} — sin datos todavía</title><link rel="icon" href="data:,">
<style>{shared_css()}{CSS}</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
  <p class="eyebrow">{html.escape(plan_nombre)} · pestaña sin datos</p>
  <h1>{html.escape(label)}</h1>
  <p class="lead">Esta pestaña existe en todos los informes, pero <b>este plan todavía no tiene los
  datos que la llenan</b>. No está rota: está vacía a propósito, y aquí abajo está cómo llenarla.</p>

  <div class="box">
    <h2>Qué se vería aquí</h2>
    <p>{html.escape(como.get("que", "—"))}</p>
  </div>

  <div class="box">
    <h2>Cómo se consigue</h2>
    <pre><code id="cmd">{cmd}</code></pre>
    <button class="copy" type="button"
      onclick="navigator.clipboard.writeText(document.getElementById('cmd').textContent).then(()=>{{this.textContent='copiado';setTimeout(()=>this.textContent='copiar el comando',1400)}})">copiar el comando</button>
    {f'<p class="nota">{html.escape(como.get("nota",""))}</p>' if como.get("nota") else ""}
  </div>

  <div class="por-que">
    <b>Por qué esta página existe y no un hueco en el menú.</b> Antes, la pestaña cuya página no
    existía <i>desaparecía</i> de la barra. Evitaba el 404 y creaba algo peor: el menú cambiaba de
    un plan a otro, así que era imposible saber si a este informe le faltaba la Arquitectura o si
    simplemente es de otro tipo. Un menú que cambia solo es un menú en el que no se puede confiar.
    <br><br>
    Y por qué no se rellena con un ejemplo: publicar un diagrama de demostración es exactamente el
    fallo que ya costó dos <code>structure.html</code> enseñando un proyecto que no existía. Vacío y
    dicho es honesto; inventado, no.
  </div>

  <footer>Generado por <code>gen_placeholders.py</code> el {date.today().isoformat()} — desaparece
  solo en cuanto el fichero real exista.</footer>
</div></body></html>"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = os.path.abspath(sys.argv[1])
    # nav del kit + las pestañas propias del proyecto (report_kit_local/nav.json, MO-34): una
    # pestaña local sin datos también lleva su «cómo se consigue».
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "scripts")))
    try:
        from render_nav import cargar_nav
    except ImportError:                     # render_nav.py anterior a la 2.15: solo el del kit
        def cargar_nav(p):
            return json.load(open(p, encoding="utf-8"))
    nav = cargar_nav(os.path.join(HERE, "nav.json"))
    perfil = None
    rp = os.path.join(plan, "report.json")
    if os.path.exists(rp):
        perfil = json.load(open(rp, encoding="utf-8")).get("meta", {}).get("profile")
    if "--perfil" in sys.argv:
        perfil = sys.argv[sys.argv.index("--perfil") + 1]
    ids = nav.get("profiles", {}).get(perfil or "proyecto") or [i["id"] for i in nav["items"]]
    perm = set(nav.get("permanent", []))
    como_todos = nav.get("como_se_llena", {})
    core = os.path.join(os.path.dirname(os.path.dirname(plan)), "core")

    hechos, sin_receta = [], []
    for it in nav["items"]:
        if it["id"] not in ids or it["id"] in perm:
            continue                                  # lo permanente vive en .docs/core/, no aquí
        destino = os.path.join(plan, it["href"])
        if os.path.exists(destino):
            continue
        como = como_todos.get(it["id"])
        if not como:
            # Sin receta no se genera nada: una página que dice "sin datos" y no dice cómo
            # conseguirlos es un callejón sin salida, que es justo lo que esto viene a evitar.
            sin_receta.append(it["id"]); continue
        os.makedirs(os.path.dirname(destino) or plan, exist_ok=True)
        open(destino, "w", encoding="utf-8").write(
            page(it["label"], it["id"], como, os.path.basename(plan)))
        hechos.append(it["id"])

    print(f"OK placeholders: {', '.join(hechos) if hechos else 'ninguno (el plan ya tiene todo)'}")
    if sin_receta:
        print(f"aviso: sin receta en nav.json#como_se_llena, NO generadas: {', '.join(sin_receta)}")


if __name__ == "__main__":
    main()
