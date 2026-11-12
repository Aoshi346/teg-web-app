#!/usr/bin/env python3
"""gen_entregables.py — la pestaña donde acaba TODO lo que el plan produce y no tiene otra casa.

EL PRINCIPIO, que es lo que de verdad importa aquí:

    Un entregable que no aparece en el informe NO está entregado.

El kit tenía trece pestañas y ninguna para el material que un plan genera por el camino:
wireframes, mockups, mensajes redactados para el cliente, evidencias de calibración de agentes,
adjuntos. Todo eso acababa en carpetas sueltas del plan — invisible desde el informe, que es
exactamente lo que el informe existe para evitar. Se detectó cuando un wireframe de portada quedó
fuera y hubo que reclamarlo.

POR QUÉ UNA PESTAÑA GENÉRICA Y NO UNA POR TIPO
Una pestaña "Diseño" resuelve el wireframe y dentro de un mes hace falta otra para los mensajes, y
luego otra para los replays. Trece pestañas ya son muchas; veinte no las mira nadie, y `nav.json`
acabaría siendo una lista de excepciones. Esta recoge por EXCLUSIÓN: todo lo que no tenga pestaña
propia entra aquí sin que haya que tocar código cuando aparezca un tipo de material nuevo.

El precio, dicho claro: un cajón de sastre se llena de basura si nadie lo cura. La contención es
que se agrupa por carpeta y se ordena, no que se filtre.

CÓMO RECOGE
    wireframes/ · mockups/   → HTML embebido en iframe navegable + enlace a pantalla completa
    *.md · *.txt             → enlazados con su primer encabezado como título
    imágenes                 → galería, agrupada por carpeta de origen
    lo demás                 → listado con su tamaño (zips, PDFs, datasets: NO se embeben)

    shots/  → SOLO las capturas HUÉRFANAS: las que ningún item referencia en `evidence[]`. Las que
              ya son evidencia de un item se ven en Resultados y duplicarlas aquí sería ruido. Las
              huérfanas, en cambio, son justo el material que hoy se pierde.

NO RECOGE (ya tienen pestaña propia; duplicarlas sería el ruido que esto intenta evitar):
    sources/ → fuentes.html   ·   schemas/ → schemas.html   ·   feedback/ → personas.html
    feedback-audit/ · speckit/ · .backups/ · los .html y .json del propio kit
    Y si el perfil del plan lleva la pestaña Diseño (MO-76, sub-ola 2.15): el material visual
    —referencias/, arranque/12-kit-marca/, direcciones/, wireframes/, bocetos/, mockups/,
    prototipos/ y las capturas huérfanas de shots/— va a diseno.html (`gen_diseno.py`), y esta
    página lo dice arriba. Sin la pestaña (perfil `incidencia`), se recoge aquí como siempre.

Los tokens visuales NO se copian: se extraen en tiempo de generación del bloque SHARED de
`index.template.html`. Así esta página no puede divergir del resto del set — que es el fallo que
`check_shared_block.py` existe para cazar, y que aquí se hace imposible por construcción.

Uso:  python3 gen_entregables.py <dir-del-plan>
Luego: python3 render_nav.py --all <dir-del-plan>
"""
import html
import json
import pathlib
import re
import sys

KIT = pathlib.Path(__file__).parent

# Carpetas con pestaña propia. Editar esto es lo ÚNICO que hace falta cuando una carpeta pase a
# tener su propia sección — no hay lista de inclusión que mantener.
RESERVADAS = {
    "sources", "schemas", "feedback", "feedback-audit", "speckit",
    ".backups", "shots", "__pycache__", "replays_cache",
    # 3.09: lo de Pilar y Roberto sale en informe.html (secciones 7 y 8); sus fotos no se publican
    "impacto", "codigo",
}
IMG = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
EMBEBIBLE = {"wireframes", "mockups", "prototipos"}
TEXTO = {".md", ".txt"}


def humano(n: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} GB"


def titulo_de(p: pathlib.Path) -> str:
    """El primer encabezado markdown, o el nombre del fichero si no lo tiene."""
    if p.suffix.lower() in TEXTO:
        try:
            for linea in p.read_text(encoding="utf-8", errors="ignore").splitlines()[:40]:
                m = re.match(r"#{1,3}\s+(.+)", linea.strip())
                if m:
                    return m.group(1).strip()
        except OSError:
            pass
    return p.name


def evidencias_referenciadas(plan: pathlib.Path) -> set[str]:
    """Rutas que YA se ven en Resultados como evidencia de un item."""
    rj = plan / "report.json"
    if not rj.exists():
        return set()
    try:
        doc = json.loads(rj.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    refs: set[str] = set()
    for it in doc.get("items", []):
        for ev in it.get("evidence", []) or []:
            src = ev.get("src") or ev.get("path") or ev.get("file") if isinstance(ev, dict) else ev
            if isinstance(src, str) and src.strip():
                refs.add(pathlib.PurePosixPath(src.strip()).name)
    return refs


def shared_css() -> str:
    """Extrae el bloque de tokens del set. No se copia: se lee, para que no pueda divergir."""
    tpl = (KIT / "index.template.html").read_text(encoding="utf-8")
    m = re.search(r"/\* SHARED:BEGIN \*/(.*?)/\* SHARED:END \*/", tpl, re.S)
    return m.group(1) if m else ""


def con_pestana_diseno(plan: pathlib.Path) -> bool:
    """¿El perfil del plan lleva la pestaña Diseño? Entonces el material visual es de ella."""
    perfil = "proyecto"
    rj = plan / "report.json"
    if rj.exists():
        try:
            perfil = json.loads(rj.read_text(encoding="utf-8")).get("meta", {}).get("profile") or perfil
        except (OSError, ValueError):
            pass
    sys.path.insert(0, str(KIT.parent.parent / "scripts"))
    try:
        from render_nav import cargar_nav
    except ImportError:                     # render_nav.py anterior a la 2.15: solo el del kit
        def cargar_nav(p):
            return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    return "diseno" in cargar_nav(KIT / "nav.json").get("profiles", {}).get(perfil, [])


def recolectar(plan: pathlib.Path, diseno: bool = False) -> tuple[dict, list]:
    """Devuelve (grupos, huérfanas). grupos: carpeta → lista de ficheros.

    Con `diseno`, lo visual se deja para `gen_diseno.py` (sus CARPETAS, `shots/` incluida)."""
    visuales: set[str] = set()
    if diseno:
        from gen_diseno import CARPETAS
        visuales = set(CARPETAS)
    grupos: dict[str, list[pathlib.Path]] = {}
    for hijo in sorted(plan.iterdir()):
        if not hijo.is_dir() or hijo.name in RESERVADAS or hijo.name.startswith("."):
            continue
        if hijo.name in visuales:
            continue
        ficheros = [f for f in sorted(hijo.rglob("*")) if f.is_file() and not f.name.startswith(".")
                    and not any(f.relative_to(plan).as_posix().startswith(v + "/")
                                for v in visuales if "/" in v)]
        if ficheros:
            grupos[hijo.name] = ficheros

    huerfanas: list[pathlib.Path] = []
    shots = plan / "shots"
    if shots.is_dir() and "shots" not in visuales:
        refs = evidencias_referenciadas(plan)
        huerfanas = [f for f in sorted(shots.rglob("*"))
                     if f.is_file() and f.suffix.lower() in IMG and f.name not in refs]
    return grupos, huerfanas


def render_fichero(f: pathlib.Path, plan: pathlib.Path, carpeta: str) -> str:
    rel = f.relative_to(plan).as_posix()
    href = html.escape(rel)
    nombre = html.escape(titulo_de(f))
    ext = f.suffix.lower()

    if carpeta in EMBEBIBLE and ext in {".html", ".htm"}:
        return (f'<figure class="ent-embed"><figcaption><strong>{nombre}</strong>'
                f'<a href="{href}" target="_blank" rel="noopener">abrir a pantalla completa ↗</a>'
                f"</figcaption>"
                f'<iframe src="{href}" loading="lazy" title="{nombre}"></iframe></figure>')
    if ext in IMG:
        return (f'<figure class="ent-img"><a href="{href}" target="_blank" rel="noopener">'
                f'<img src="{href}" alt="{nombre}" loading="lazy"></a>'
                f"<figcaption>{html.escape(f.name)}</figcaption></figure>")
    try:
        size = humano(f.stat().st_size)
    except OSError:
        size = "?"
    etiqueta = "documento" if ext in TEXTO else ext.lstrip(".") or "fichero"
    return (f'<li><a href="{href}" target="_blank" rel="noopener">{nombre}</a>'
            f'<span class="ent-meta">{etiqueta} · {size}</span></li>')


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("uso: gen_entregables.py <dir-del-plan>")
    plan = pathlib.Path(sys.argv[1]).resolve()
    if not plan.is_dir():
        sys.exit(f"ERROR: no existe {plan}")

    diseno = con_pestana_diseno(plan)
    grupos, huerfanas = recolectar(plan, diseno)
    titulo = "Entregables"
    partes: list[str] = []
    if diseno:
        partes.append(
            '<p class="ent-nota">El material <strong>visual</strong> —referencias, marca, '
            'direcciones, wireframes, bocetos, mockups y capturas sueltas— está en la pestaña '
            '<a href="diseno.html">Diseño</a>, ordenado por fases. Aquí queda todo lo demás.</p>')

    # Los grupos con material EMBEBIDO van al final: un iframe ocupa media pantalla y empujaría
    # fuera de vista todo lo que viniera detrás. Lo ligero (listas, galerías) se escanea primero.
    grupos = dict(sorted(grupos.items(), key=lambda kv: kv[0] in EMBEBIBLE))

    for carpeta, ficheros in grupos.items():
        imgs = [f for f in ficheros if f.suffix.lower() in IMG]
        emb = [f for f in ficheros
               if carpeta in EMBEBIBLE and f.suffix.lower() in {".html", ".htm"}]
        otros = [f for f in ficheros if f not in imgs and f not in emb]
        cuerpo = "".join(render_fichero(f, plan, carpeta) for f in emb)
        if imgs:
            cuerpo += ('<div class="ent-galeria">'
                       + "".join(render_fichero(f, plan, carpeta) for f in imgs) + "</div>")
        if otros:
            cuerpo += ('<ul class="ent-lista">'
                       + "".join(render_fichero(f, plan, carpeta) for f in otros) + "</ul>")
        partes.append(f'<section class="ent-grupo"><h2>{html.escape(carpeta)}'
                      f'<span class="ent-count">{len(ficheros)}</span></h2>{cuerpo}</section>')

    if huerfanas:
        gal = "".join(render_fichero(f, plan, "shots") for f in huerfanas)
        partes.append(
            '<section class="ent-grupo"><h2>Capturas sueltas'
            f'<span class="ent-count">{len(huerfanas)}</span></h2>'
            "<p class=\"ent-nota\">No las referencia ningún item como evidencia, así que no salen en "
            "Resultados. Están aquí para que no se pierdan — si alguna prueba algo, enlázala desde "
            "su item y desaparecerá de esta lista.</p>"
            f'<div class="ent-galeria">{gal}</div></section>')

    if not grupos and not huerfanas:
        partes.append(
            '<section class="ent-vacio"><h2>Todavía no hay entregables sueltos</h2>'
            "<p>Esta pestaña recoge lo que el plan produce y no encaja en otra sección: wireframes y "
            "mockups (<code>wireframes/</code>, <code>mockups/</code>), mensajes, adjuntos y capturas "
            "que ningún item referencia. Crea la carpeta dentro del plan y vuelve a generar.</p>"
            "<p class=\"ent-nota\">Se enseña vacía a propósito: decir que no hay nada es información; "
            "omitir la pestaña haría creer que el material no existe.</p></section>")

    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<!-- GENERADO por gen_entregables.py — NO editar a mano: se regenera y se pierde lo escrito.
     Los tokens salen del bloque SHARED de index.template.html, leídos al generar. -->
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report-kit · {titulo}</title>
<style>
{shared_css()}
  /* Base común del set. Los VALORES salen todos de los tokens de arriba, así que lo único que
     vive aquí es el layout — que es estable y no diverge. Los colores no se repiten nunca. */
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
    font-size:15px;line-height:1.55}}
  .wrap{{max-width:1100px;margin:0 auto;padding:0 22px 60px}}
  .page-head{{border-bottom:1px solid var(--line);padding:36px 0 24px;margin-bottom:2rem}}
  .page-head h1{{font-size:28px;margin:0 0 8px;letter-spacing:-.01em}}
  .page-head .sub{{font-size:16px;color:var(--muted);max-width:78ch;margin:0}}
  a{{color:var(--blue)}}
  code{{background:var(--line);border-radius:4px;padding:.1em .35em;font-size:.9em}}
  .ent-grupo{{margin:0 0 2.5rem}}
  .ent-grupo h2{{display:flex;align-items:center;gap:.6rem;font-size:1.15rem;margin:0 0 1rem}}
  .ent-count{{font:600 .72rem/1 system-ui;background:var(--line);color:var(--muted);
    border-radius:var(--radius-pill);padding:.25rem .55rem}}
  .ent-embed{{margin:0 0 1.5rem;border:1px solid var(--line);border-radius:var(--radius-md);
    overflow:hidden;background:var(--card)}}
  .ent-embed figcaption{{display:flex;justify-content:space-between;align-items:center;gap:1rem;
    padding:.7rem 1rem;border-bottom:1px solid var(--line);font-size:.85rem;flex-wrap:wrap}}
  .ent-embed iframe{{width:100%;height:56vh;min-height:380px;border:0;display:block;background:#fff}}
  .ent-galeria{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:1rem}}
  .ent-img{{margin:0;border:1px solid var(--line);border-radius:var(--radius-md);overflow:hidden;
    background:var(--card)}}
  .ent-img img{{width:100%;height:170px;object-fit:cover;display:block}}
  .ent-img figcaption{{padding:.5rem .7rem;font-size:.75rem;color:var(--muted);
    overflow-wrap:anywhere}}
  .ent-lista{{list-style:none;padding:0;margin:0;display:grid;gap:.5rem}}
  .ent-lista li{{display:flex;justify-content:space-between;gap:1rem;align-items:baseline;
    padding:.7rem .9rem;border:1px solid var(--line);border-radius:var(--radius-md);
    background:var(--card);flex-wrap:wrap}}
  .ent-meta{{font-size:.75rem;color:var(--muted);white-space:nowrap}}
  .ent-nota{{font-size:.85rem;color:var(--muted);max-width:60ch}}
  .ent-vacio{{border:1px dashed var(--line);border-radius:var(--radius);padding:2rem;
    background:var(--card)}}
</style>
</head>
<body>
<!-- NAV:BEGIN -->
<!-- NAV:END -->
<main class="wrap">
  <header class="page-head">
    <h1>{titulo}</h1>
    <p class="sub">Todo lo que este plan ha producido y no encaja en otra pestaña. Un entregable
    que no aparece en el informe no está entregado.</p>
  </header>
  {''.join(partes)}
</main>
</body>
</html>
"""
    salida = plan / "entregables.html"
    salida.write_text(doc, encoding="utf-8")
    n = sum(len(v) for v in grupos.values()) + len(huerfanas)
    print(f"OK {salida} — {len(grupos)} carpeta(s), {n} fichero(s)"
          + (f", {len(huerfanas)} captura(s) huérfana(s)" if huerfanas else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
