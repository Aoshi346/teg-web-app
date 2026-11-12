#!/usr/bin/env python3
"""render_nav.py — materializa la topnav única (nav.json) en las páginas de un set.

Uso:
  python3 .claude/scripts/render_nav.py <pagina.html> [--nav nav.json] [--profile diseño] [--active id] [--depth N]
  python3 .claude/scripts/render_nav.py --all <plan-dir> [--nav nav.json] [--profile diseño]

- Reescribe SOLO el bloque entre <!-- NAV:BEGIN --> y <!-- NAV:END --> (idempotente).
  Si la página no tiene marcadores, la inserta justo tras <body> (y avisa).
- --all: recorre los .html del plan (y subcarpetas conocidas), deduce `active` por nombre de
  fichero y la profundidad por la ruta (prefijo ../ correcto).
- El perfil filtra qué items entran (nav.json#profiles). Sin --profile intenta leer
  report.json del plan (meta.profile); si no, usa todos los items.

Convención: rules/report-kit.md. PROHIBIDA la nav a mano.
"""
import argparse
import html as _html
import json
import re
import sys
from pathlib import Path

BEGIN, END = "<!-- NAV:BEGIN -->", "<!-- NAV:END -->"
DEFAULT_NAV = Path(__file__).resolve().parents[1] / "templates" / "report_kit" / "nav.json"

CSS = """<style>
  /* La barra declara SU tipografía y SU interlineado: se inyecta también en páginas con estilo
     propio (el HTML autor-escrito de `sources/`), y heredar el font-family de la página cambiaba
     el ancho de los items — con `system-ui` el menú pasaba de una línea a dos. La barra debe verse
     igual en las 20+ páginas del set, sea cual sea el CSS de debajo. Cosechado de
     web-manager-coolify, donde se midió. */
  .topnav{position:sticky;top:0;z-index:20;background:rgba(246,244,239,.93);backdrop-filter:blur(8px);border-bottom:1px solid #e4e0d7;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.4}
  .topnav .wrap{max-width:1080px;margin:0 auto;display:flex;align-items:center;gap:4px;flex-wrap:wrap;padding:9px 22px}
  .topnav .brand{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#1b2a4a;font-weight:700;margin-right:8px}
  .topnav a{font-size:13px;color:#6b6b76;text-decoration:none;padding:6px 9px;border-radius:8px}
  .topnav a:hover{background:#efece4;color:#1b2a4a}
  .topnav a.active{background:#1b2a4a;color:#fff}
  /* Grupo desplegable. Se abre por CLIC y no por hover: en táctil el hover no existe, y con
     hover un roce al pasar hacia otra pestaña despliega el menú encima de lo que ibas a pulsar. */
  /* Selector de plan (PV-7, idea del Usuario). Las pestañas PERMANENTES —Core, Equipo,
     Arquitectura— no cambian; las de plan —Dashboard, Flujo, Resultados— siguen a lo que elijas.
     Un solo panel, y el contexto lo pone quien mira. */
  .topnav .selplan{margin-left:auto;display:flex;align-items:center;gap:6px}
  .topnav .selplan label{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:#9a958a}
  .topnav .selplan select{font:inherit;font-size:12.5px;padding:4px 8px;border:1px solid #e4e0d7;
    border-radius:8px;background:#fff;color:#1b2a4a;max-width:230px}
  @media(max-width:900px){.topnav .selplan{margin-left:0;width:100%;padding-top:6px}}
  /* Modal de planes (T-044). Con trece planes el desplegable dejaba de ser un selector y pasaba
     a ser un archivo: se muestran los 5 más recientes y el resto se busca aquí. */
  .planmodal{position:fixed;inset:0;z-index:60;background:rgba(20,18,14,.42);
    display:flex;align-items:flex-start;justify-content:center;padding:8vh 16px}
  .planmodal[hidden]{display:none}
  .planmodal .pmbox{background:#fdfcf9;border:1px solid #e4e0d7;border-radius:14px;width:min(560px,100%);
    max-height:76vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,.22)}
  .planmodal .pmhead{display:flex;gap:8px;padding:12px;border-bottom:1px solid #ece8df}
  .planmodal .pmhead input{flex:1;font:inherit;font-size:14px;padding:9px 11px;border:1px solid #e4e0d7;
    border-radius:9px;background:#fff;color:#1b2a4a}
  .planmodal .pmhead input:focus{outline:2px solid #c2410c;outline-offset:1px}
  .planmodal .pmhead button{font-size:20px;line-height:1;background:none;border:0;cursor:pointer;
    color:#8a8478;padding:0 8px;border-radius:8px}
  .planmodal .pmhead button:hover{background:#efece4;color:#1b2a4a}
  .planmodal .pmlist{list-style:none;margin:0;padding:6px;overflow-y:auto}
  .planmodal .pmlist a{display:flex;justify-content:space-between;gap:12px;align-items:baseline;
    padding:9px 11px;border-radius:9px;text-decoration:none;color:#1b2a4a}
  .planmodal .pmlist a:hover,.planmodal .pmlist a:focus-visible{background:#efece4;outline:none}
  .planmodal .pmlist b{font-weight:600;font-size:14px}
  .planmodal .pmlist span{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#8a8478;white-space:nowrap}
  .planmodal .pmlist em,.topnav .selplan em{font-style:normal;color:#c2410c;font-weight:600}
  .planmodal .pmnone{padding:18px;margin:0;color:#8a8478;font-size:13.5px;text-align:center}
  .topnav .navgroup{position:relative;display:inline-block}
  .topnav .navgroup>button{font:inherit;font-size:13px;color:#6b6b76;background:none;border:0;
    cursor:pointer;padding:6px 9px;border-radius:8px}
  .topnav .navgroup>button:hover{background:#efece4;color:#1b2a4a}
  .topnav .navgroup>button .ngn{display:inline-block;min-width:15px;margin:0 5px 0 2px;padding:0 4px;
    border-radius:999px;background:#e4e0d7;color:#55555f;font-size:10.5px;font-weight:700;
    line-height:15px;text-align:center;vertical-align:1px}
  .topnav .navgroup.active>button .ngn,.topnav .navgroup.ng-abierto>button .ngn{background:#ffffff2e;color:inherit}
  .topnav .navgroup.active>button{background:#1b2a4a;color:#fff}
  .topnav .navgroup>button:focus-visible{outline:2px solid #c2410c;outline-offset:2px}
  .topnav .navmenu{display:none;position:absolute;top:calc(100% + 4px);left:0;min-width:190px;
    background:#fff;border:1px solid #e4e0d7;border-radius:10px;padding:5px;z-index:30;
    box-shadow:0 8px 24px rgba(0,0,0,.10)}
  .topnav .navgroup.ng-abierto .navmenu{display:block}
  .topnav .navmenu a{display:block;white-space:nowrap}
  /* El título del plan puede ser una frase entera («Revisión integral del template — análisis de
     todos los proyectos de /home»): sin tope, él solo empujaba la barra a dos filas a 1280 px. Se
     recorta con «…» y el texto completo queda en el `title` (UX-9, sub-ola 2.15). */
  .topnav .brand{max-width:30ch;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:0 1 auto}
  /* responsive (fuente única — QA TPL1-W3 iter-2 F1/F2/F10, L-008, V-F010):
     ≤860px cubre móvil Y tablet con UNA estrategia: sin wrap, scroll horizontal,
     brand fuera (los items primero), fade de affordance a la derecha y el activo a la vista.

     UX-9 (sub-ola 2.15). A ≤640px los desplegables se pintaban SIEMPRE abiertos y en línea: cada
     grupo era una columna de enlaces y la barra medía 344 px a 390 de ancho (medido en el informe
     de la revisión integral) — media pantalla tapada antes de ver nada. Y entre 641 y 860 el panel
     abría pero no se veía: el `overflow-x` de la tira y su `mask-image` lo recortaban. Ahora el
     grupo vuelve a ser un botón y su panel se superpone BAJO la barra, a todo el ancho: se ancla
     a `.topnav` (el grupo pasa a `position:static`), que está fuera de la tira, así que ni el
     overflow ni la máscara lo alcanzan. Por eso el difuminado de la derecha deja de ser una máscara
     de la tira y pasa a ser un `::after` de la barra. Se cierra al elegir, con Escape o al pulsar
     fuera (NAV_GROUP_JS). No se quita ninguna pestaña: la regla 5b sigue entera. */
  @media(max-width:860px){
    .topnav .wrap{flex-wrap:nowrap;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:9px 14px}
    .topnav::after{content:"";position:absolute;top:0;right:0;bottom:0;width:34px;pointer-events:none;
      background:linear-gradient(90deg,rgba(246,244,239,0),rgba(246,244,239,.97))}
    .topnav .wrap::-webkit-scrollbar{display:none}
    .topnav .brand{display:none}
    .topnav a{flex:none;font-size:12.5px;padding:6px 8px}
    .topnav .navgroup{position:static;flex:none}
    .topnav .navgroup>button{font-size:12.5px;padding:6px 8px}
    .topnav .navmenu{top:calc(100% + 2px);left:10px;right:10px;min-width:0;
      max-height:calc(100vh - 96px);overflow-y:auto}
    .topnav .navmenu a{font-size:14px;padding:10px 12px}
    .topnav .selplan{flex:none;width:auto;margin-left:6px;padding-top:0}
  }
</style>"""

NAV_GROUP_JS = """<script>
/* Desplegables de la topnav. Por clic (ver el CSS), con Escape para cerrar y clic fuera para
   cerrar: sin eso el menú se queda abierto tapando la página y hay que recargar.
   La clase de estado es `ng-abierto` y no `open`: cinco plantillas del kit (fuentes, patron,
   codigo, entregas, stack) tienen su propio `.open{margin-left:auto;border…}` para un botón, y al
   abrir un grupo la barra entera saltaba de alto (medido: 49 → 63 px a 390 y 83 → 97 a 1280 en
   Fuentes). La barra no puede depender del CSS de la página que la recibe (UX-9). */
(function(){
  var gs = [].slice.call(document.querySelectorAll('.topnav .navgroup'));
  gs.forEach(function(g){
    var b = g.querySelector('button'); if(!b) return;
    b.addEventListener('click', function(e){
      e.stopPropagation();
      var abierto = g.classList.contains('ng-abierto');
      gs.forEach(function(o){ o.classList.remove('ng-abierto');
        var ob=o.querySelector('button'); if(ob) ob.setAttribute('aria-expanded','false'); });
      if(!abierto){ g.classList.add('ng-abierto'); b.setAttribute('aria-expanded','true'); }
    });
  });
  document.addEventListener('click', function(){
    gs.forEach(function(o){ o.classList.remove('ng-abierto');
      var ob=o.querySelector('button'); if(ob) ob.setAttribute('aria-expanded','false'); });
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape') gs.forEach(function(o){ o.classList.remove('ng-abierto');
      var ob=o.querySelector('button'); if(ob) ob.setAttribute('aria-expanded','false'); });
  });
})();
</script>"""

PLAN_JS = r"""<script>/* selector de plan + modal de busqueda (T-044, fuente unica render_nav.py) */
(function(){
  var sel=document.getElementById("selp"), mo=document.getElementById("planmodal");
  if(!sel) return;
  var actual=sel.value;
  function abrir(){
    sel.value=actual;              /* "ver todos" no es un plan: el select no puede quedarse ahi */
    if(!mo) return;
    mo.hidden=false;
    var q=document.getElementById("pmq"); if(q){q.value="";filtrar();q.focus();}
  }
  function cerrar(){ if(mo) mo.hidden=true; sel.value=actual; }   /* el select vuelve al plan abierto */
  sel.addEventListener("change",function(){
    if(this.value==="__mas__"){ abrir(); return; }                /* "ver todos" NO navega */
    if(this.value) location.href=this.value;
  });
  if(!mo) return;
  function filtrar(){
    var t=(document.getElementById("pmq").value||"").toLowerCase().trim();
    var n=0;
    mo.querySelectorAll(".pmlist li").forEach(function(li){
      var a=li.querySelector("a"), txt=(a.dataset.b||"")+" "+a.textContent.toLowerCase();
      var ok=!t||t.split(/\s+/).every(function(w){return txt.indexOf(w)>=0});
      li.hidden=!ok; if(ok)n++;
    });
    mo.querySelector(".pmnone").hidden = n>0;
  }
  document.getElementById("pmq").addEventListener("input",filtrar);
  document.getElementById("pmx").addEventListener("click",cerrar);
  mo.addEventListener("click",function(e){ if(e.target===mo) cerrar(); });
  document.addEventListener("keydown",function(e){
    if(e.key==="Escape"&&!mo.hidden) cerrar();
    if(e.key==="Enter"&&!mo.hidden&&document.activeElement&&document.activeElement.id==="pmq"){
      var a=mo.querySelector(".pmlist li:not([hidden]) a"); if(a) location.href=a.getAttribute("href");
    }
  });
})();
</script>"""

NAV_JS = """<script>/* nav: activo visible al cargar en pantallas estrechas (fuente única render_nav.py).
   Si el activo vive dentro de un desplegable (cerrado), lo que se centra es el botón de su grupo. */
(function(){var a=document.querySelector(".topnav .wrap>a.active")||document.querySelector(".topnav .navgroup.active>button");
if(a&&window.matchMedia&&matchMedia("(max-width:860px)").matches){a.scrollIntoView({inline:"center",block:"nearest"});}})();
</script>"""


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dir_local(nav_path: Path | str | None = None) -> Path:
    """`templates/report_kit_local/`: lo PROPIO de un proyecto, al lado del kit y fuera de él."""
    return Path(nav_path or DEFAULT_NAV).resolve().parent.parent / "report_kit_local"


def cargar_nav(nav_path: Path | str | None = None) -> dict:
    """nav.json del kit + las pestañas propias del proyecto (MO-34, sub-ola 2.15).

    Había 10 copias de `report_kit/` en 5 versiones porque cada proyecto que quería una pestaña
    suya (webs: Diseño, Moodboard, Chatbot; AMC: Módulos; risk-couple: Gobernanza) EDITABA su copia
    de `nav.json` o de `build.py`, y a partir de ahí `propagar.py` ya no podía ponerla al día sin
    pisar lo suyo (la protege como DIVERGENTE). Ahora lo propio va en
    `templates/report_kit_local/nav.json` —al lado del kit, no dentro— y se suma al cargar; la copia
    del kit se queda idéntica a la del template. Mismo formato, solo con lo que AÑADE:

        {"items": [{"id": "modulos", "label": "Módulos", "href": "modulos.html"}],
         "profiles": {"proyecto": ["modulos"]},
         "groups": [{"id": "mapas", "children": ["modulos"]}],
         "como_se_llena": {"modulos": {"que": "…", "cmd": "…"}},
         "permanent": [], "optional_pages": {"pages": []}}

    Un `id` que ya existe en el kit no se redefine (se avisa y se salta): sumar, no sustituir, es
    lo que evita que la copia local vuelva a ser una bifurcación con otro nombre. Un grupo con un
    `id` que ya existe suma sus `children` al del kit; uno nuevo se añade entero.
    """
    nav_path = Path(nav_path or DEFAULT_NAV)
    nav = load_json(nav_path)
    extra_p = dir_local(nav_path) / "nav.json"
    if not extra_p.exists():
        return nav
    try:
        extra = load_json(extra_p)
    except (OSError, ValueError) as exc:
        print(f"aviso: {extra_p} no se puede leer ({exc}) — se usa solo el nav.json del kit",
              file=sys.stderr)
        return nav
    if not isinstance(extra, dict):
        print(f"aviso: {extra_p} no es un objeto JSON — se usa solo el nav.json del kit", file=sys.stderr)
        return nav

    def _lista(v, que):
        if v is None:
            return []
        if not isinstance(v, list):
            print(f"aviso: {extra_p}: `{que}` no es una lista — se ignora", file=sys.stderr)
            return []
        return v

    def _mapa(v, que):
        if v is None:
            return {}
        if not isinstance(v, dict):
            print(f"aviso: {extra_p}: `{que}` no es un objeto — se ignora", file=sys.stderr)
            return {}
        return v

    ids = {i["id"] for i in nav["items"]}
    for it in _lista(extra.get("items"), "items"):
        if not isinstance(it, dict) or not it.get("id") or not it.get("href"):
            print(f"aviso: {extra_p}: item sin `id` o sin `href` ({it!r:.80}) — se salta",
                  file=sys.stderr)
            continue
        if it.get("id") in ids:
            print(f"aviso: {extra_p}: '{it['id']}' ya existe en el kit — no se redefine",
                  file=sys.stderr)
            continue
        nav["items"].append(it)
        ids.add(it["id"])
    for perfil, añadir in _mapa(extra.get("profiles"), "profiles").items():
        lista = nav.setdefault("profiles", {}).setdefault(perfil, [])
        lista.extend(i for i in _lista(añadir, f"profiles.{perfil}") if i not in lista)
    grupos = {g["id"]: g for g in nav.setdefault("groups", [])}
    for g in _lista(extra.get("groups"), "groups"):
        if not isinstance(g, dict) or not g.get("id"):
            print(f"aviso: {extra_p}: grupo sin `id` — se salta", file=sys.stderr)
            continue
        if g.get("id") in grupos:
            hijos = grupos[g["id"]].setdefault("children", [])
            hijos.extend(c for c in _lista(g.get("children"), f"groups.{g['id']}.children")
                         if c not in hijos)
        elif isinstance(g.get("children"), list) and g.get("label"):
            nav["groups"].append(g)
        else:
            print(f"aviso: {extra_p}: grupo nuevo «{g['id']}» sin `label` o sin lista `children` — se salta",
                  file=sys.stderr)
    for k, v in _mapa(extra.get("como_se_llena"), "como_se_llena").items():
        nav.setdefault("como_se_llena", {}).setdefault(k, v)
    perm = nav.setdefault("permanent", [])
    perm.extend(i for i in _lista(extra.get("permanent"), "permanent") if i not in perm)
    opc = nav.setdefault("optional_pages", {}).setdefault("pages", [])
    opc.extend(_lista(_mapa(extra.get("optional_pages"), "optional_pages").get("pages"),
                      "optional_pages.pages"))
    return nav


def core_dir(plan: Path | None) -> Path | None:
    """.docs/core/ visto desde el plan. Es hermano de .docs/plans/, así que ../../core."""
    return None if plan is None else (plan.parent.parent / "core")


def nav_block(nav: dict, profile: str | None, active: str | None, depth: int, brand: str,
              plan: Path | None = None, scope: str = "plan") -> str:
    ids = nav.get("profiles", {}).get(profile) if profile else None
    items = [i for i in nav["items"] if (ids is None or i["id"] in ids)]
    # PV-3 · lo PERMANENTE no vive en el plan. Core/Equipo/Arquitectura describen lo que el
    # proyecto ES, así que viven en .docs/core/ y sobreviven al cierre del plan; el resto
    # (Dashboard, Flujo, Resultados…) es de un plan concreto. El href se resuelve segun desde
    # dónde se mire, y las dos rutas son idénticas en disco y servidas — ver nav.json#_doc_permanent.
    perm = set(nav.get("permanent", []))

    def dest(i):
        """Dónde está el fichero de este item EN DISCO (para el filtro de existencia)."""
        if i["id"] in perm:
            return (core_dir(plan) / i["href"]) if plan is not None else None
        return (plan / i["href"]) if plan is not None else None

    def href(i):
        """La ruta relativa que se escribe en el enlace, desde la página que se está pintando."""
        if scope == "core":
            return i["href"] if i["id"] in perm else f"../plans/{plan.name}/{i['href']}"
        return f"../../core/{i['href']}" if i["id"] in perm else i["href"]

    # T-047 · el menú lleva SIEMPRE todas las pestañas del perfil.
    #
    # Antes se omitía la que no existía, para no dar un 404. Evitaba ese fallo y creaba uno peor:
    # el menú cambiaba de un plan a otro, así que era imposible saber si a este informe le falta la
    # Arquitectura o si simplemente es de otro tipo. Un menú que cambia solo no es fiable.
    #
    # Ahora la página que falta la genera `gen_placeholders.py` diciendo qué se vería y con qué
    # comando se consigue. Solo se omite lo que NO tiene página ni receta — ahí sí sería un 404.
    if plan is not None:
        items = [i for i in items if (dest(i) or Path("/nonexistent")).exists()]
    prefix = "../" * depth
    # Grupos: un desplegable por grupo declarado en nav.json#groups. Con 14 entradas la barra se
    # desborda y deja de servir para navegar. Se agrupa lo que responde "qué ES el sistema" y se
    # dejan sueltas las páginas de trabajo. Si un grupo se queda sin hijas presentes, NO se pinta:
    # un desplegable vacío es peor que una entrada de menos.
    presentes = {i["id"]: i for i in items}
    agrupados, bloques = set(), {}
    for g in nav.get("groups", []):
        hijas = [presentes[c] for c in g.get("children", []) if c in presentes]
        if not hijas:
            continue
        agrupados.update(h["id"] for h in hijas)
        bloques[g["children"][0]] = (g, hijas)     # se pinta en la posición de su primera hija

    def enlace(i, extra=""):
        act = ' class="active"' if i["id"] == active else ""
        return f'  <a href="{prefix}{href(i)}"{act}{extra}>{i["label"]}</a>'

    partes = []
    for i in items:
        if i["id"] in bloques:
            g, hijas = bloques[i["id"]]
            act = " active" if any(h["id"] == active for h in hijas) else ""
            sub = "\n".join(f'    <a href="{prefix}{href(h)}"'
                            f'{" class=\"active\"" if h["id"] == active else ""}>{h["label"]}</a>'
                            for h in hijas)
            partes.append(
                f'  <div class="navgroup{act}">'
                # El CONTADOR, no solo el chevron (T-109). El Usuario, que conoce el informe,
                # no encontró las pestañas nuevas y creyó que faltaban del menú: un "▾" de 8px
                # no dice que dentro hay nueve páginas. El número sí, y cuesta un span.
                f'<button type="button" aria-expanded="false" aria-haspopup="true" '
                f'title="{len(hijas)} páginas — clic para abrir">{g["label"]} '
                f'<span class="ngn" aria-hidden="true">{len(hijas)}</span>'
                f'<span aria-hidden="true">&#9662;</span></button>'
                f'\n    <div class="navmenu" role="menu">\n{sub}\n    </div>\n  </div>')
        elif i["id"] not in agrupados:
            partes.append(enlace(i))
    links = "\n".join(partes)
    # EL SELECTOR DE PLAN (PV-7 + T-044). Solo aparece si hay MÁS DE UNO: con un plan sería un
    # desplegable de un elemento, que es ruido.
    #
    # Tres decisiones, y las tres vienen de que la lista crece sola con cada plan:
    #   · Se ordena por CUÁNDO SE TRABAJÓ, no por el nombre. Dos planes del mismo día empataban.
    #   · Se muestran los 5 más recientes. Con trece, el desplegable es un archivo, no un selector.
    #   · El resto vive detrás de «ver todos», con buscador por nombre, fecha y hora.
    #
    # La HORA sale de `meta.generated_at`, que `tasks_to_items.py` empezó a escribir con T-044.
    # Para los planes anteriores no hay hora y **no se inventa**: se enseña solo la fecha. Deducirla
    # del mtime diría cuándo se regeneró el informe, no cuándo se trabajó — el mismo error que ya
    # rompió una vez la elección del plan activo.
    selector = ""
    if plan is not None:
        import json as _j
        from datetime import datetime as _dt

        def _info(h):
            meta, cerrado, ga, pend = {}, False, "", 0
            try:
                rep = _j.loads((h / "report.json").read_text(encoding="utf-8"))
                meta = rep.get("meta", {})
                cerrado = bool(meta.get("closed_at"))
                ga = meta.get("generated_at") or ""
                # T-046 · cuántas decisiones ESPERAN AL USUARIO en ese plan. Sin este número no
                # había forma de saber dónde quedaba trabajo suyo: 148 items sin decidir repartidos
                # en 6 planes, y ninguna pantalla lo decía. `decision` la escribe solo él.
                pend = sum(1 for x in rep.get("items", []) if not x.get("decision"))
            except Exception:
                pass
            fecha_nombre = h.name[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", h.name) else ""
            hora = ""
            if ga:
                try:
                    hora = _dt.fromisoformat(ga).strftime("%H:%M")
                except Exception:
                    pass
            # Se ordena por LO QUE SE VE: la fecha del plan y, para desempatar el mismo día, la
            # hora. Ordenar por «cuándo se trabajó» ponía un plan del 21 por encima de uno del 22
            # y el desplegable parecía roto — el orden tiene que coincidir con lo que lees.
            orden = f"{fecha_nombre} {hora or '00:00'}"
            return dict(dir=h.name, slug=h.name[11:] or h.name, fecha=fecha_nombre,
                        hora=hora, cerrado=cerrado, orden=orden, pend=pend)

        hermanos = [_info(d) for d in plan.parent.iterdir()
                    if d.is_dir() and (d / "report.json").exists()]
        hermanos.sort(key=lambda x: (x["orden"], x["dir"]), reverse=True)   # más reciente arriba

        if len(hermanos) > 1:
            def _href(nom):
                # SIEMPRE por plans/, nunca ../<otro>/ aunque sean hermanos en disco: servido, el
                # plan se monta en la raíz y el navegador recorta ../<otro>/ a /<otro>/ → 404.
                return prefix + (f"../plans/{nom}/index.html" if scope == "core"
                                 else f"../../plans/{nom}/index.html")

            def _etiqueta(x):
                cuando = x["fecha"] + (f" {x['hora']}" if x["hora"] else "")
                # el número va DELANTE del nombre: es lo que decide si tienes que entrar
                marca = (" · cerrado" if x["cerrado"]
                         else (f" · {x['pend']} por decidir" if x["pend"] else ""))
                return f"{cuando} · {x['slug']}{marca}"

            TOPE = 5
            actual = next((x for x in hermanos if x["dir"] == plan.name), None)
            top = hermanos[:TOPE]
            if actual and actual not in top:      # el plan abierto SIEMPRE está en la lista corta
                top = [actual] + top[:TOPE - 1]
            opts = "".join(
                f'<option value="{_href(x["dir"])}"'
                f'{" selected" if x["dir"] == plan.name else ""}>{_etiqueta(x)}</option>'
                for x in top)
            resto = len(hermanos) - len(top)
            if resto > 0:
                opts += f'<option value="__mas__">— ver todos ({len(hermanos)})… —</option>'

            def _fila(x):
                marca = ("cerrado" if x["cerrado"]
                         else (f'<em>{x["pend"]} por decidir</em>' if x["pend"] else ""))
                cuando = x["fecha"] + (" · " + x["hora"] if x["hora"] else "")
                return (f'<li><a href="{_href(x["dir"])}" '
                        f'data-b="{x["dir"].lower()} {x["fecha"]} {x["hora"]}">'
                        f'<b>{x["slug"]}</b>'
                        f'<span>{cuando}{" · " + marca if marca else ""}</span></a></li>')

            filas = "".join(_fila(x) for x in hermanos)

            selector = (
                '<span class="selplan"><label for="selp">plan</label>'
                f'<select id="selp">{opts}</select></span>'
                '<div class="planmodal" id="planmodal" hidden><div class="pmbox" role="dialog" '
                'aria-modal="true" aria-label="Elegir plan">'
                '<div class="pmhead"><input id="pmq" type="search" placeholder="buscar por nombre, '
                'fecha u hora…" autocomplete="off"><button type="button" id="pmx" '
                'aria-label="Cerrar">&times;</button></div>'
                f'<ul class="pmlist">{filas}</ul>'
                '<p class="pmnone" hidden>Ningún plan coincide.</p>'
                '</div></div>')

    return (
        f"{BEGIN}\n{CSS}\n"
        f'<nav class="topnav"><div class="wrap">\n'
        f'  <span class="brand" title="{_html.escape(brand, quote=True)}">{_html.escape(brand)}</span>\n{links}\n{selector}\n'
        f"</div></nav>\n{NAV_JS}\n{NAV_GROUP_JS}\n{PLAN_JS}\n{END}"
    )


def apply(page: Path, block: str) -> str:
    html = page.read_text(encoding="utf-8")
    if BEGIN in html and END in html:
        # lambda y no el string: `re.sub` interpreta las barras del REEMPLAZO, y el bloque
        # lleva JS con `\s+`. Con el string plano reventaba con "bad escape".
        new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _m: block, html, flags=re.S)
        verb = "actualizada"
    else:
        m = re.search(r"<body[^>]*>", html)
        if not m:
            return f"SKIP {page}: sin <body> ni marcadores"
        new = html[: m.end()] + "\n" + block + html[m.end():]
        verb = "insertada (sin marcadores previos — añadidos)"
    if new != html:
        page.write_text(new, encoding="utf-8")
        return f"OK {page}: nav {verb}"
    return f"OK {page}: sin cambios"


def active_for(page: Path, nav: dict, plan: Path | None = None) -> str | None:
    name = page.name
    for i in nav["items"]:
        if Path(i["href"]).name == name:
            return i["id"]
    # Una página dentro de una carpeta que "pertenece" a un item (nav.json#owns_dir: `sources/` es
    # de Fuentes) marca ESE item como activo. Sin esto se abre un informe de `sources/` y el menú no
    # señala nada: el lector cree que se ha salido del informe. Cosechado de web-manager-coolify,
    # donde lo reportó el dueño navegando.
    if plan is not None:
        try:
            carpetas = set(page.relative_to(plan).parts[:-1])
        except ValueError:
            carpetas = set()
        for i in nav["items"]:
            if i.get("owns_dir") and i["owns_dir"] in carpetas:
                return i["id"]
    return None


def check(plan: Path, nav: dict, profile: str | None = None) -> int:
    """Comprueba que la topnav de un plan NAVEGA. Devuelve 0 si todo bien, 1 si no.

    Nace de un fallo que encontró el Usuario navegando y ningún script: los placeholders de
    subcarpeta (`feedback/personas.html`, `schemas/schemas.html`) salían sin marcadores de nav,
    así que al entrar en esa pestaña **desaparecía el menú**. Se comprueban las tres cosas que
    pueden fallar por separado, porque fallan por separado:
      1. la página existe          → si no, la pestaña da 404
      2. lleva la nav pintada      → si no, se entra y no se puede salir
      3. sus enlaces resuelven     → un prefijo `../` de más rompe la vuelta, y solo se ve al pulsar
    El 3 se comprueba en disco con resolve(), que recorta los `..` que se pasan de la raíz igual
    que hace el navegador (RFC 3986 §5.2.4) — que es lo que permite un solo juego de rutas para
    plan y core.
    """
    rpt = plan / "report.json"
    if not profile and rpt.exists():
        profile = load_json(rpt).get("meta", {}).get("profile")
    profile = profile or "proyecto"
    ids = nav.get("profiles", {}).get(profile)
    if ids is None:
        print(f"nav --check: perfil desconocido '{profile}'")
        return 1
    perm = set(nav.get("permanent", []))
    core = core_dir(plan)
    malas = 0
    print(f"nav --check {plan.name} · perfil {profile} · {len(ids)} pestañas")
    for i in nav["items"]:
        if i["id"] not in ids:
            continue
        base = core if i["id"] in perm else plan
        f = base / i["href"]
        if not f.exists():
            print(f"  ✗ FALTA    {i['label']:<24} {f}")
            malas += 1
            continue
        html = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"NAV:BEGIN -->(.*?)<!-- NAV:END", html, re.S)
        if not m:
            print(f"  ✗ SIN NAV  {i['label']:<24} {f}  (¿generada sin marcadores?)")
            malas += 1
            continue
        rotos = [h for h in re.findall(r'<a[^>]*href="([^"#?]+)"', m.group(1))
                 if not h.startswith("http") and not (f.parent / h).resolve().exists()]
        if rotos:
            print(f"  ✗ ENLACES  {i['label']:<24} rotos: {rotos[:3]}")
            malas += 1
        else:
            print(f"  ✓ {i['label']:<24} {i['href']}")
    print("nav --check: OK" if not malas else f"nav --check: {malas} pestaña(s) con problema")
    return 1 if malas else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="pagina.html o (con --all) el directorio del plan")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--nav", type=Path, default=DEFAULT_NAV)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--active", default=None)
    ap.add_argument("--depth", type=int, default=None)
    ap.add_argument("--brand", default=None)
    ap.add_argument("--check", action="store_true",
                    help="No escribe: comprueba que TODA pestaña del perfil existe, lleva nav y "
                         "que sus enlaces resuelven en disco. exit 1 si algo falla.")
    ap.add_argument("--scope", choices=("plan", "core"), default="plan",
                    help="plan: pinta la nav en el set del plan (default). "
                         "core: la pinta en .docs/core/, tomando <target> como el plan ACTIVO "
                         "al que apuntan las pestañas de plan (PV-3).")
    args = ap.parse_args()

    nav = cargar_nav(args.nav)
    target = Path(args.target)

    if args.check:
        sys.exit(check(target, nav, args.profile))

    if args.all:
        plan = target
        profile = args.profile
        brand = args.brand
        rpt = plan / "report.json"
        if rpt.exists():
            meta = load_json(rpt).get("meta", {})
            profile = profile or meta.get("profile")
            brand = brand or meta.get("title", plan.name)
        brand = brand or plan.name
        # Qué HTML de un plan lleva topnav. Dos guardas que atacan fallos DISTINTOS y por eso
        # van las dos:
        #   1) Carpetas que nunca son página del informe: un wireframe o un mockup se EMBEBE en un
        #      iframe desde `entregables.html`, así que inyectarle la nav le mete la barra dentro
        #      del marco. Se excluyen a cualquier profundidad y AUNQUE ya traigan marcadores —
        #      justo el caso de las que contaminó una pasada anterior de `--all`.
        #   2) Marcadores solo se AUTO-insertan en la raíz del plan y en sources/. A otra
        #      profundidad solo se refrescan páginas que YA los llevan: el rglob a ciegas inyectó
        #      la topnav en fixtures de material vendorizado (pruebas-kits/_material, caso PRU-9).
        NO_SON_PAGINAS = {".backups", "shots", "wireframes", "mockups", "prototipos",
                          "resources", "replays", "mensajes", "node_modules"}

        def _elegible(p, raiz):
            if NO_SON_PAGINAS & set(p.parts):
                return False
            rel = p.relative_to(raiz).parts
            if len(rel) == 1 or (len(rel) == 2 and rel[0] == "sources"):
                return True
            try:
                return "NAV:BEGIN" in p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return False

        # PV-3: con --scope core se pinta la MISMA nav en .docs/core/, que es donde viven las
        # páginas permanentes. `plan` sigue siendo el plan activo: es lo que decide a dónde
        # apuntan Dashboard/Flujo/Resultados desde una página del core.
        raiz = core_dir(plan) if args.scope == "core" else plan
        if not raiz.exists():
            print(f"nav: {raiz} no existe — nada que pintar")
            return
        perm = set(nav.get("permanent", []))
        if args.scope == "core":
            # SOLO las páginas permanentes declaradas. `.docs/core/index.html` es otro artefacto,
            # con su propio generador (scripts/gen_core.py) y su propia plantilla: meterle esta
            # topnav se la pisaría en la siguiente regeneración, y `active_for` lo confundiría
            # además con el «Resumen» del informe.
            nombres = {i["href"] for i in nav["items"] if i["id"] in perm}
            pages = sorted(p for p in raiz.glob("*.html") if p.name in nombres)
        else:
            pages = sorted(p for p in raiz.rglob("*.html") if _elegible(p, raiz))
        def _falta(i):
            base = core_dir(plan) if i["id"] in perm else plan
            return not (base / i["href"]).exists()
        omitidas = [i["id"] for i in nav["items"]
                    if (nav.get("profiles", {}).get(profile) is None or i["id"] in nav["profiles"][profile])
                    and _falta(i)]
        if omitidas:
            print("nav: omitidas (no existen todavía): " + ", ".join(omitidas))
        for p in pages:
            depth = len(p.relative_to(raiz).parts) - 1
            print(apply(p, nav_block(nav, profile, active_for(p, nav, plan), depth, brand, plan,
                                     scope=args.scope)))
        return

    depth = args.depth if args.depth is not None else 0
    active = args.active or active_for(target, nav)
    brand = args.brand or target.parent.name
    print(apply(target, nav_block(nav, args.profile, active, depth, brand)))


if __name__ == "__main__":
    main()
