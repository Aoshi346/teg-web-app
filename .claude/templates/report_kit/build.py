#!/usr/bin/env python3
"""build.py — materializa el set de informe del report-kit en un plan.

Uso:
    python3 build.py <plan-dir> [--pages index,structure,dashboard,results,pruebas,otto] [--embed]

- Copia cada plantilla `<pagina>.template.html` de esta carpeta a `<plan-dir>/<pagina>.html`
  inyectando el JSON en el placeholder `const DB = /*__DATA__*/null;` (patrón heredado de
  speckit_dashboard/build.py, archivado en _archive/2026-10-19/templates/). Con --embed usa report.embedded.json (imágenes base64) si existe.
- structure.html se inyecta desde `<plan-dir>/graph-dataset.json` (contrato skills/code-graph).
- patron.html    se inyecta desde `<plan-dir>/pattern-dataset.json` (gen_patron_dataset.py).
  Si ese fichero NO existe, o existe pero su `meta.source` dice FIXTURE, la página NO se genera
  (y se borra la que hubiera): un informe no enseña datos inventados. Para la demo, explícito:
  `--pages structure`.
- Tras inyectar, ejecuta render_nav.py --all para materializar la topnav según meta.profile.

Idempotente: re-correr regenera las páginas; las decisiones viven en report.json (server) o
localStorage (estático), nunca en el HTML.
"""
import collections
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md_to_html  # noqa: E402 - vecino del script, hay que fijar el path antes

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "..", "scripts"))
sys.path.insert(1, SCRIPTS)
try:
    from render_nav import cargar_nav, dir_local  # noqa: E402 - nav del kit + la del proyecto (MO-34)
except ImportError:
    # Un proyecto con un render_nav.py anterior a la 2.15 (o divergente) no puede tumbar el build:
    # se sigue con el nav.json del kit, sin las pestañas locales, y se dice.
    print("aviso: render_nav.py no trae cargar_nav (es anterior a la sub-ola 2.15) — se usa solo el "
          "nav.json del kit; propaga render_nav.py junto con el kit", file=sys.stderr)

    def cargar_nav(nav_path):
        return json.load(open(nav_path, encoding="utf-8"))

    def dir_local(nav_path):
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(nav_path))),
                            "report_kit_local")

# Lo PROPIO de un proyecto vive al lado del kit, no dentro (MO-34): `templates/report_kit_local/`.
# Sus `gen_*.py` se corren aquí, tras los generadores del kit y antes de los placeholders y la nav;
# sus pestañas se declaran en su `nav.json` (lo suma `cargar_nav`). Así la copia del kit de cada
# proyecto puede ser IDÉNTICA a la del template y `propagar.py` la pone al día sin pisar nada.
LOCAL = str(dir_local(os.path.join(HERE, "nav.json")))
DEFAULT_PAGES = ["index", "stack", "codigo", "structure", "patron", "entregas", "dashboard", "results", "pruebas", "otto"]


# Campos de item que PESAN. Medido sobre el plan ai4dev (208 items, report.json de 610 KB):
# desc 237 KB · tl_rec 50 · why 40 · refs 34 · goal 26 · manual_test 20. El resto, migajas.
# Ese JSON se inyectaba ENTERO en las 7 páginas → 7 × 610 KB, y el hook de pre-commit bloqueaba
# el plan por tamaño (T-048). Pero solo el dashboard lee `desc`; otto, fuentes y auditoría no
# leen NINGÚN campo de item.
CAMPOS_GORDOS = ("desc", "tl_rec", "why", "refs", "goal", "manual_test", "history", "howto")


def _proyectar(data, tpl):
    """Quita de los items los campos gordos que ESTA plantilla no menciona.

    La decisión se toma leyendo la plantilla, no de una tabla escrita a mano: una tabla se
    queda vieja en cuanto alguien añade `it.refs` a una página y entonces el campo desaparece
    en silencio, que es el peor fallo posible. Así se mantiene sola.

    El criterio es «el nombre del campo no aparece como PALABRA en el fichero». El límite de
    palabra es lo que hace útil la prueba: sin él, `desc` casaba dentro de `description` y de
    la clase CSS `.desc-box`, así que el campo más gordo —237 KB de los 610— se conservaba en
    las siete páginas y no se ahorraba nada.

    Con `\b` sigue siendo seguro porque cualquier uso REAL casa: `it.desc`, `it["desc"]`,
    `{desc}`, `desc:`. Lo único que se le escaparía es una clave construida a mano
    (`it["de"+"sc"]`), que no existe en ninguna plantilla —comprobado— y que además sería
    ilegible por otras razones.
    """
    sobran = [c for c in CAMPOS_GORDOS if not re.search(rf"\b{c}\b", tpl)]
    if not sobran or not isinstance(data, dict) or "items" not in data:
        return data
    fuera = set(sobran)
    d = dict(data)
    d["items"] = [{k: v for k, v in it.items() if k not in fuera} for it in data["items"]]
    return d


def _texto(fragmento):
    """HTML → una línea de texto plano."""
    import html as _h
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", "", fragmento))).strip()


def _cabecera_html(texto):
    """(título, resumen) de una página PROPIA de `sources/` (HTML sin `.md` hermano) — MO-40.

    Antes se leían los primeros 8 KB. La topnav que `render_nav.py` inyecta tras `<body>` ocupa
    13-15 KB, así que al RECONSTRUIR el informe la entradilla quedaba fuera y Fuentes listaba la
    página sin resumen (medido el 21-10: 6 de las 14 páginas propias de la revisión integral). El
    apaño era copiar la entradilla en un comentario del `<head>`, y dependía de que cada autor se
    acordara. Ahora se lee el fichero entero y se quita lo que no es contenido —la nav, los
    comentarios, `<style>` y `<script>`— antes de buscar. Por orden:
      1. la entradilla visible del cuerpo: `<p class="…entradilla…">`;
      2. `<meta name="description" content="…">` (la pone md_to_html.py);
      3. `<!-- entradilla: … -->`, el apaño viejo, que sigue valiendo;
      4. el primer `<p>` del cuerpo que no sea un `eyebrow` (la etiqueta de sección de md_to_html).
    Sin ninguno, el resumen queda vacío: no se inventa uno.
    """
    sin_nav = re.sub(r"<!-- NAV:BEGIN -->.*?<!-- NAV:END -->", "", texto, flags=re.S)
    titulo = ""
    m = re.search(r"<title>(.*?)</title>", sin_nav, re.S | re.I)
    if m:
        titulo = _texto(m.group(1))
    comentario = re.search(r"<!--\s*entradilla:\s*(.*?)-->", sin_nav, re.S | re.I)
    # la <meta name="description">, con las comillas que traiga (una «'» dentro de "…" no la corta)
    etiqueta = next((t for t in re.findall(r"<meta\b[^>]*>", sin_nav, re.I)
                     if re.search(r"""name\s*=\s*["']description["']""", t, re.I)), "")
    meta = re.search(r"""content\s*=\s*(?:"([^"]*)"|'([^']*)')""", etiqueta, re.I)
    meta_txt = (meta.group(1) if meta.group(1) is not None else meta.group(2)) if meta else ""
    limpio = re.sub(r"<!--.*?-->", "", sin_nav, flags=re.S)
    limpio = re.sub(r"<(style|script)\b[^>]*>.*?</\1\s*>", "", limpio, flags=re.S | re.I)
    entradilla = re.search(r'<p[^>]*class="[^"]*entradilla[^"]*"[^>]*>(.*?)</p>', limpio, re.S | re.I)
    primero = next((p for p in re.finditer(r"<p(\s[^>]*)?>(.*?)</p>", limpio, re.S | re.I)
                    if "eyebrow" not in (p.group(1) or "") and _texto(p.group(2))), None)
    for cand in ((entradilla and entradilla.group(1)), meta_txt,
                 (comentario and comentario.group(1)), (primero and primero.group(2))):
        txt = _texto(cand or "")
        if txt:
            return titulo, md_to_html.recortar(txt)
    return titulo, ""


def inject(template_path, data, out_path, meta=None):
    tpl = open(template_path, encoding="utf-8").read()
    # «<» como \u003c: el JSON va dentro de un <script>, y un `desc` que cite «</script>» lo cerraba
    # (la página reventaba, o ejecutaba lo que viniera detrás). Dentro de una cadena de JS, \u003c es
    # «<»: el dato no cambia. Lo encontró el verificador de la 2.15; venía de antes.
    payload = json.dumps(_proyectar(data, tpl), ensure_ascii=False).replace("<", "\\u003c")
    html = tpl.replace("/*__DATA__*/null", payload)
    if html == tpl:
        print(f"aviso: {os.path.basename(template_path)} no tiene placeholder /*__DATA__*/null")
    # META adicional para páginas cuyo DB no es el report (p.ej. structure ← graph-dataset):
    # así el eyebrow/branding sale de report.meta igualmente (QA iter-2 F6).
    if "/*__META__*/null" in html:
        html = html.replace("/*__META__*/null",
                            json.dumps(meta or {}, ensure_ascii=False).replace("<", "\\u003c"))
    open(out_path, "w", encoding="utf-8").write(html)
    print(f"OK {out_path}")


def _cerrojo(plan):
    """CERROJO — dos `build.py` a la vez sobre el mismo plan se pisan.

    Medido el 2026-08-26 lanzando un build completo en segundo plano y otro con
    `--pages` encima: el segundo reescribió las páginas mientras `render_nav.py`
    del primero las estaba leyendo, y las DOCE páginas quedaron con los marcadores
    de nav puestos y el bloque vacío. El informe se queda sin menú, `--check` no
    llega a correr, y no hay ningún error por ninguna parte: falla en silencio.

    Un fichero de bloqueo cuesta cuatro líneas y lo hace imposible. Si el proceso
    murió sin limpiarlo, se avisa y se sigue: un cerrojo huérfano que bloquee para
    siempre es peor que la carrera que evita."""
    import errno
    lock = os.path.join(plan, ".build.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return lock
    except OSError as e:
        if e.errno != errno.EEXIST:
            return None
        try:
            viejo = open(lock).read().strip()
            os.kill(int(viejo), 0)          # ¿sigue vivo?
            print(f"ERROR: ya hay un build corriendo sobre este plan (pid {viejo}).\n"
                  f"       Dos a la vez dejan la nav VACÍA en todas las páginas. Espera a que "
                  f"termine.", file=sys.stderr)
            sys.exit(2)
        except (ValueError, ProcessLookupError, FileNotFoundError):
            print(f"aviso: cerrojo huérfano en {lock} — el build anterior murió. Continúo.")
            return lock


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = os.path.abspath(sys.argv[1])
    # Lo PRIMERO, antes de leer nada: dos builds a la vez dejan la nav vacía en todas
    # las páginas y no dan ningún error. Ver el docstring de _cerrojo.
    lock = _cerrojo(plan)
    if lock:
        import atexit
        atexit.register(lambda: os.path.exists(lock) and os.remove(lock))
    pages = DEFAULT_PAGES
    embed = "--embed" in sys.argv
    for i, a in enumerate(sys.argv):
        if a == "--pages" and i + 1 < len(sys.argv):
            pages = [p.strip() for p in sys.argv[i + 1].split(",") if p.strip()]

    report_path = os.path.join(plan, "report.embedded.json" if embed else "report.json")
    if embed and not os.path.exists(report_path):
        print("aviso: no hay report.embedded.json (corre embed.py antes) — uso report.json")
        report_path = os.path.join(plan, "report.json")
    if not os.path.exists(report_path):
        sys.exit(f"ERROR: no existe {report_path} (genera primero con tasks_to_items.py)")
    report = json.load(open(report_path, encoding="utf-8"))
    # ruta real del plan para el "?" del chip de modo (comando copiable de server.py). Relativa al
    # cwd si el plan cuelga de él (caso normal: .docs/plans/<slug>), absoluta si no. NO se escribe a
    # report.json: es solo para el HTML — la deriva desde location.pathname daba `cd "."`.
    try:
        rel = os.path.relpath(plan, os.getcwd())
        report["meta"]["plan_dir"] = plan if rel.startswith("..") else rel
    except ValueError:
        report["meta"]["plan_dir"] = plan

    # sources/ — los informes de investigación que hay detrás de los items. Se descubren en cada
    # build (nunca se guardan en report.json: quedarían obsoletos). El mapeo informe→épicas es
    # opcional y vive en meta.sources_map; sin él la página lista igual el informe.
    sdir = os.path.join(plan, "sources")
    smap = report.get("meta", {}).get("sources_map", {})
    by_epic = collections.Counter(i.get("epic") for i in report.get("items", []))
    sources = []
    if os.path.isdir(sdir):
        for fn in sorted(f for f in os.listdir(sdir) if f.endswith(".md")):
            path = os.path.join(sdir, fn)
            # Título y resumen: md_to_html.cabecera_md, la misma función que pone la
            # <meta name="description"> de la página generada (antes vivía aquí, copiada).
            titulo, resumen = md_to_html.cabecera_md(open(path, encoding="utf-8").read())
            if not titulo:   # sin encabezado propio: se deriva del nombre, que sí es descriptivo
                titulo = fn[:-3].replace("-", " ").replace("_", " ")
                titulo = titulo[0].upper() + titulo[1:]
            # se renderiza a HTML: enlazar el .md crudo servía texto plano y una tabla de 137 filas
            # en markdown sin renderizar no se lee (y contradice rules/html-output.md)
            page = fn[:-3] + ".html"
            try:
                md_to_html.render_file(path, os.path.join(sdir, page), titulo)
            except Exception as exc:                      # nunca romper el build por un informe
                print(f"aviso: no se pudo renderizar {fn} ({exc}) — se enlaza el .md")
                page = fn
            eps = smap.get(fn, [])
            sources.append({"file": fn, "page": page, "titulo": titulo, "resumen": resumen, "epics": eps,
                            "items": sum(by_epic.get(e, 0) for e in eps),
                            "kb": max(1, os.path.getsize(path) // 1024)})
        # HTML autor-escrito: un `.html` en sources/ SIN `.md` hermano. Lo pide la regla 5g de
        # `rules/report-kit.md` («se lista igual, con la etiqueta *página propia*»), que estaba
        # escrita y no implementada — el barrido de arriba solo mira `.md`, así que una página
        # técnica escrita a mano recibía la topnav y luego no aparecía en Fuentes: existía y no
        # se podía llegar a ella desde ninguna parte.
        #
        # Su `<style>` NO se toca, y ese es justamente el motivo de que se escriban a mano:
        # suelen ser diagramas o comparaciones donde la maquetación ES el contenido.
        renderizados = {s_["page"] for s_ in sources}
        for fn in sorted(f for f in os.listdir(sdir) if f.endswith(".html")):
            if fn in renderizados:
                continue                      # ya salió de su .md
            path = os.path.join(sdir, fn)
            titulo, resumen = "", ""
            try:
                titulo, resumen = _cabecera_html(open(path, encoding="utf-8", errors="replace").read())
            except Exception as exc:                  # nunca romper el build por una página
                print(f"aviso: no se pudo leer {fn} ({exc})")
            if not titulo:
                titulo = fn[:-5].replace("-", " ").replace("_", " ")
                titulo = titulo[0].upper() + titulo[1:]
            eps = smap.get(fn, [])
            sources.append({"file": fn, "page": fn, "titulo": titulo, "resumen": resumen,
                            "epics": eps, "propia": True,
                            "items": sum(by_epic.get(e, 0) for e in eps),
                            "kb": max(1, os.path.getsize(path) // 1024)})
        sources.sort(key=lambda s_: s_["file"])

    report["meta"]["sources"] = sources
    if sources and "fuentes" not in pages:
        pages = pages + ["fuentes"]

    # auditoría del propio repo: pestaña aparte del plan de trabajo. Se genera solo si el plan
    # declara qué prefijos de item son "salud del repo" (meta.audit_prefixes) y hay alguno.
    ap = report.get("meta", {}).get("audit_prefixes") or []
    if ap and any(str(i.get("id", "")).rsplit("-", 1)[0] in ap for i in report.get("items", [])) \
            and "auditoria" not in pages:
        pages = pages + ["auditoria"]

    # páginas opcionales: index enlazaba las 5 siempre ("si este plan las incluye"), así que en un
    # plan normal eran 5 enlaces a 404. Se inyectan solo las que existen.
    nav_json = cargar_nav(os.path.join(HERE, "nav.json"))
    report["meta"]["optional_present"] = [
        o for o in nav_json.get("optional_pages", {}).get("pages", [])
        if os.path.exists(os.path.join(plan, o["href"]))]

    # structure.html SOLO si hay grafo real. Con el fixture se publicaba una pestaña "Estructura"
    # que enseñaba un proyecto Django inventado (apps/clients/api.py…) en el informe de un repo que
    # no es ese — un banner de "datos de demostración" no arregla que la pestaña no aporte nada y
    # confunda. Para verla igualmente: `--pages structure` explícito.
    # Se mira el CONTENIDO, no solo si el fichero está: `graph_reduce.py --fixture <plan>/
    # graph-dataset.json` es un comando documentado, y así fue como los dos planes de 2026-08-07
    # acabaron publicando el Django inventado con el nombre del dataset real. Un guard que solo
    # comprueba os.path.exists() da por bueno justo el caso que originó GRF-4.
    graph_path = os.path.join(plan, "graph-dataset.json")
    pedido_explicito = "--pages" in sys.argv
    motivo = None
    if not os.path.exists(graph_path):
        motivo = "sin graph-dataset.json"
    elif re.search(r"fixture", str(json.load(open(graph_path, encoding="utf-8"))
                                  .get("meta", {}).get("source", "")), re.I):
        motivo = "graph-dataset.json es el FIXTURE sintético, no este proyecto"
    if motivo:
        if "structure" in pages and not pedido_explicito:
            print(f"aviso: {motivo} — NO se genera structure.html (corre /code-graph "
                  "para el grafo real, o fuerza la demo con --pages structure)")
            pages = [p for p in pages if p != "structure"]
            obsoleta = os.path.join(plan, "structure.html")
            if os.path.exists(obsoleta):
                os.remove(obsoleta)
                print(f"OK borrada {obsoleta} (mostraba el fixture, no este proyecto)")
        graph_path = os.path.join(HERE, "fixture.graph-dataset.json")
    graph = json.load(open(graph_path, encoding="utf-8"))

    # patron.html: mismo criterio que structure — una pestaña sin sus datos no se rellena con
    # una demostración, se omite diciendo cómo se consigue. Aquí no hay fixture que valga: el
    # patrón de OTRO repo no dice nada del tuyo.
    stack_path = os.path.join(plan, "stack-dataset.json")
    stack = None
    if os.path.exists(stack_path):
        stack = json.load(open(stack_path, encoding="utf-8"))
    elif "stack" in pages:
        print("aviso: sin stack-dataset.json — NO se genera stack.html "
              "(python3 .claude/templates/report_kit/gen_stack_dataset.py <plan>)")
        pages = [p for p in pages if p != "stack"]
        obsoleta = os.path.join(plan, "stack.html")
        if os.path.exists(obsoleta):
            os.remove(obsoleta)

    entregas_path = os.path.join(plan, "entregas-dataset.json")
    entregas = None
    if os.path.exists(entregas_path):
        entregas = json.load(open(entregas_path, encoding="utf-8"))
    elif "entregas" in pages:
        print("aviso: sin entregas-dataset.json — NO se genera entregas.html "
              "(python3 .claude/templates/report_kit/gen_entregas_dataset.py <plan>)")
        pages = [p for p in pages if p != "entregas"]
        obsoleta = os.path.join(plan, "entregas.html")
        if os.path.exists(obsoleta):
            os.remove(obsoleta)
            print(f"OK borrada {obsoleta} (sus datos ya no están)")

    codigo_path = os.path.join(plan, "codigo-dataset.json")
    codigo = None
    if os.path.exists(codigo_path):
        codigo = json.load(open(codigo_path, encoding="utf-8"))
    elif "codigo" in pages:
        print("aviso: sin codigo-dataset.json — NO se genera codigo.html "
              "(python3 .claude/templates/report_kit/gen_codigo_dataset.py <plan>)")
        pages = [p for p in pages if p != "codigo"]
        obsoleta = os.path.join(plan, "codigo.html")
        if os.path.exists(obsoleta):
            os.remove(obsoleta)
            print(f"OK borrada {obsoleta} (sus datos ya no están)")

    patron_path = os.path.join(plan, "pattern-dataset.json")
    patron = None
    if os.path.exists(patron_path):
        patron = json.load(open(patron_path, encoding="utf-8"))
    elif "patron" in pages:
        print("aviso: sin pattern-dataset.json — NO se genera patron.html "
              "(python3 .claude/templates/report_kit/gen_patron_dataset.py <plan>)")
        pages = [p for p in pages if p != "patron"]
        obsoleta = os.path.join(plan, "patron.html")
        if os.path.exists(obsoleta):
            os.remove(obsoleta)
            print(f"OK borrada {obsoleta} (sus datos ya no están)")

    profile = report.get("meta", {}).get("profile", "proyecto")
    nav_profiles = nav_json["profiles"]
    wanted = [p for p in pages if p in nav_profiles.get(profile, pages)] or pages

    for page in wanted:
        tpl = os.path.join(HERE, f"{page}.template.html")
        if not os.path.exists(tpl):
            print(f"aviso: falta plantilla {tpl} — salto {page}")
            continue
        data = {"structure": graph, "patron": patron, "codigo": codigo,
                "entregas": entregas, "stack": stack}.get(page, report)
        inject(tpl, data, os.path.join(plan, f"{page}.html"), meta=report.get("meta"))

    # server.py para el modo con backend (decisiones a disco). Se REEMPLAZA si cambió: es código
    # generado (su cabecera lo dice) y dejarlo viejo es cómo un plan se queda sin el montaje /core/
    # o sin un endpoint nuevo, fallando en silencio y pareciendo que el informe está roto.
    server_src = os.path.join(HERE, "server.py")
    server_dst = os.path.join(plan, "server.py")
    if os.path.exists(server_src):
        nuevo_txt = open(server_src, encoding="utf-8").read()
        viejo_txt = open(server_dst, encoding="utf-8").read() if os.path.exists(server_dst) else None
        if viejo_txt != nuevo_txt:
            shutil.copy(server_src, server_dst)
            print(f"OK {server_dst} ({'actualizado' if viejo_txt else 'modo backend: python3 server.py'})")

    # El Core ANTES que la nav del plan, y no al revés: el filtro de existencia omite la pestaña
    # cuyo fichero no está, así que pintar la nav primero dejaba el plan sin enlaces al Core la
    # primera vez que se genera. Fallaba en silencio — la barra salía correcta, solo que más corta.
    _core(plan, report)

    # «Flujo de acción» — la pestaña del ORDEN de ejecución. Hasta el 2026-09-12 `gen_flujo.py`
    # existía y NO LO LLAMABA NADIE: de los 10 `flujo.html` del repo, 9 eran el placeholder que
    # dice «aún no hay datos» y uno solo era real. Un generador huérfano es indistinguible de una
    # pestaña vacía, y este además es el sitio donde se enseña que el flujo se está siguiendo.
    # Fuente: el `dashboard.md` del plan (el mismo que alimenta report.json), y si no está, el
    # `tasks.md` de la sesión SpecKit. Si no hay ninguno, no se genera y el placeholder explica cómo.
    _flujo_src = next((os.path.join(plan, f) for f in ("dashboard.md", "tasks.md")
                       if os.path.exists(os.path.join(plan, f))), None)
    if _flujo_src:
        subprocess.run([sys.executable, os.path.join(HERE, "gen_flujo.py"), plan, _flujo_src],
                       check=False)

    # El proceso como máquina de estados, con cada estado clicable. Se genera SIEMPRE: aunque
    # no haya ni un artefacto, la página dice qué falta y con qué comando se consigue — que es
    # más útil que una pestaña ausente.
    subprocess.run([sys.executable, os.path.join(HERE, "gen_proceso.py"), plan], check=False)

    # Recorridos: el viaje del dato. Si no hay trazas.json real, deja la semilla y NO
    # publica — un informe no enseña un ejemplo inventado (rules/report-kit.md).
    subprocess.run([sys.executable, os.path.join(HERE, "gen_trazas.py"), plan], check=False)

    # Requisitos: los 11 apartados y la máquina de estados de uso. Sin requisitos.json
    # real no publica nada (rules/report-kit.md: un informe no enseña un ejemplo).
    subprocess.run([sys.executable, os.path.join(HERE, "gen_requisitos.py"), plan], check=False)

    # Sesiones: el reparto del plan en frentes paralelos (sesiones.json), con el comando exacto
    # de cada una. Se genera SIEMPRE: sin reparto, la página lo dice y enseña cómo declararlo.
    subprocess.run([sys.executable, os.path.join(HERE, "gen_sesiones.py"), plan], check=False)

    # Diseño (MO-76): el material visual del plan por fases —referencias, direcciones, bocetos,
    # wireframes, mockups y las capturas que no son evidencia de nadie—, cosechado de webs. Solo si
    # el perfil lleva la pestaña; sin material no escribe nada y la pestaña la pone el placeholder.
    if "diseno" in nav_profiles.get(profile, []):
        subprocess.run([sys.executable, os.path.join(HERE, "gen_diseno.py"), plan], check=False)

    # Módulos (WA-19, cosechado de AMC): página opcional, solo si el plan trae modulos.json.
    if os.path.isfile(os.path.join(plan, "modulos.json")):
        subprocess.run([sys.executable, os.path.join(HERE, "gen_modulos.py"), plan], check=False)

    # Informe del issue (AN-6, 3.09): página del perfil «issue», solo si el plan trae informe.json.
    if os.path.isfile(os.path.join(plan, "informe.json")):
        subprocess.run([sys.executable, os.path.join(HERE, "gen_informe.py"), plan], check=False)

    # Extensiones del proyecto (MO-34): `report_kit_local/gen_*.py`, por orden alfabético.
    if os.path.isdir(LOCAL):
        for gen in sorted(f for f in os.listdir(LOCAL) if f.startswith("gen_") and f.endswith(".py")):
            print(f"extensión del proyecto: report_kit_local/{gen}")
            subprocess.run([sys.executable, os.path.join(LOCAL, gen), plan], check=False)

    # T-047 · las pestañas del perfil que este plan no puede llenar todavía se generan diciendo
    # QUÉ falta y CON QUÉ COMANDO se consigue. Antes desaparecían del menú, y eso hacía que el
    # menú cambiara de un plan a otro — imposible saber si falta algo o si el informe es de otro
    # tipo. Va antes de la nav: si se hiciera después, el filtro de existencia las omitiría igual.
    subprocess.run([sys.executable, os.path.join(HERE, "gen_placeholders.py"), plan], check=False)

    # nav única
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "render_nav.py"), "--all", plan], check=False)
    # Y se COMPRUEBA que la barra navega de verdad. No es paranoia: los placeholders de subcarpeta
    # salieron 16 veces sin marcadores de nav —el menú desaparecía al entrar en Personas o
    # Esquemas— y lo encontró el Usuario navegando, no el generador. Avisa, no rompe el build:
    # un informe con una pestaña coja sigue siendo mejor que ninguno.
    if subprocess.run([sys.executable, os.path.join(SCRIPTS, "render_nav.py"),
                       "--check", plan], check=False).returncode:
        print("⚠️  build: la topnav tiene pestañas con problema (ver arriba) — arréglalo antes de publicar")


def _plan_activo(repo):
    """Qué plan alimenta el Core. MISMA regla que tasks_registry.py y por el mismo motivo:
    continuidad primero, fecha DEL NOMBRE después, y jamás el mtime — regenerar el informe de un
    plan viejo lo convertiría en «el más reciente» y el Core pasaría a describir el pasado."""
    planes = os.path.join(repo, ".docs", "plans")
    if not os.path.isdir(planes):
        return None
    dirs = sorted(d for d in os.listdir(planes) if os.path.isdir(os.path.join(planes, d)))
    for marca in ("pending-tasks.md", "report.json"):
        con = [d for d in dirs if os.path.exists(os.path.join(planes, d, marca))]
        if con:
            return os.path.join(planes, sorted(con)[-1])
    return None


def _core(plan, report):
    """PV-3 · las páginas PERMANENTES se escriben en .docs/core/, no en el plan.

    El informe de un plan es el registro de lo que se decidió entonces y se congela con él; el
    Core dice lo que el proyecto ES hoy, así que no puede vivir dentro de algo que se cierra.
    Sale del plan ACTIVO — y solo de ese: reconstruir un informe viejo NO debe reescribir el Core
    con datos de hace tres meses."""
    repo = subprocess.run(["git", "-C", plan, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip()
    if not repo:
        return
    activo = _plan_activo(repo)
    if activo is None or os.path.abspath(activo) != os.path.abspath(plan):
        print(f"core: {os.path.basename(plan)} no es el plan activo "
              f"({os.path.basename(activo) if activo else 'ninguno'}) — el Core no se toca")
        return
    core = os.path.join(repo, ".docs", "core")
    os.makedirs(core, exist_ok=True)
    for gen in ("gen_core_capas.py", "gen_equipo.py", "gen_core_patrones.py",
                "gen_core_arranque.py", "gen_core_levels.py",
                "gen_core_hub.py"):   # el hub, el último
        # (gen_core_hub.py se llamaba gen_core.py, como scripts/gen_core.py: renombrado en LI-11)
        r = subprocess.run([sys.executable, os.path.join(HERE, gen), plan, "--out", core],
                           capture_output=True, text=True)
        if r.returncode:
            print(f"core: {gen} falló — {(r.stderr or r.stdout).strip().splitlines()[-1:]}")
    # El Manual está en el perfil `proyecto` de nav.json y vive en el Core, pero ningún generador
    # de arriba lo escribía: el primer build de un proyecto nuevo salía con «✗ FALTA Manual» en
    # `nav --check` (medido montando fitapp, 2026-09-29). No depende del plan: se escribe si falta.
    manual = os.path.join(core, "manual.html")
    if not os.path.exists(manual):
        subprocess.run([sys.executable, os.path.join(HERE, "gen_manual.py"), manual],
                       capture_output=True, text=True)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "render_nav.py"),
                    "--all", plan, "--scope", "core"], check=False)
    print(f"OK {core} (Core permanente, desde el plan activo {os.path.basename(plan)})")


if __name__ == "__main__":
    main()
