#!/usr/bin/env python3
"""gen_diseno.py — la pestaña «Diseño»: todo el material visual de un plan, por fases (MO-76).

POR QUÉ EXISTE. Cosechado de webs (`e5a0775`, 2026-08-11): el Usuario pidió que *«todo debe estar
en el informe, que no se me escape nada disperso»*, y el material visual —wireframes, mockups,
capturas de referencia— acababa en carpetas sueltas del plan. En el template lo recogía
`gen_entregables.py` mezclado con mensajes, adjuntos y datasets, y sin orden: un wireframe y un
zip en la misma lista. Un proyecto con UI necesita verlo en el orden en que se decide
(`rules/motores-de-diseno.md` Parte F: referencias → marca → direcciones → low-fi → high-fi → mockup).

QUÉ RECOGE, por convención de carpetas dentro del plan (las mismas que escriben las skills):

    referencias/            0 · Referencias  (skill marca, paso 3: fichas y moodboard)
    arranque/12-kit-marca/  1 · Marca        (skill marca: paleta, tipografía, logo)
    direcciones/            1.5 · Direcciones (skill direcciones-de-arte)
    wireframes/             2 · Low-fi
    bocetos/                3 · High-fi      (skill disenar-pantalla: variantes con los 4 estados)
    mockups/ · prototipos/  4 · Mockup
    shots/                  capturas que NINGÚN item cita como evidencia (las que sí, en Resultados)

  · `.html` → embebido en un iframe navegable, con enlace a pantalla completa
  · imágenes → galería · `.md`/`.txt` → enlace con su primer encabezado · lo demás → listado

CUÁNDO SE ACTIVA. Si el perfil del plan lleva la pestaña `diseno` (`nav.json`: perfiles `proyecto`
y `diseño`), `build.py` lo llama solo. Sin material visual no escribe nada —y borra la página que
generó antes, si el material desapareció—: la pestaña la pone `gen_placeholders.py` diciendo cómo
se llena (regla 5b: el menú no cambia de un plan a otro).

NO DUPLICA. Con la pestaña activa, `gen_entregables.py` deja estas carpetas (y `shots/`) para
aquí y lo dice en su página. Las capturas que ya son evidencia de un item no salen: se ven en
Resultados, y aquí solo se cuentan con su enlace.

Los tokens NO se copian: se leen del bloque SHARED de `index.template.html` al generar, como en
`gen_entregables.py`. Así esta página no puede divergir del resto del set.

Uso:  python3 gen_diseno.py <dir-del-plan>
Luego: python3 ../../scripts/render_nav.py --all <dir-del-plan>   (build.py ya lo hace)
"""
import html
import pathlib
import sys
import urllib.parse

KIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
from gen_entregables import evidencias_referenciadas, humano, shared_css, titulo_de  # noqa: E402

MARCA = "<!-- GENERADO por gen_diseno.py"
IMG = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
TEXTO = {".md", ".txt"}

# (carpeta relativa al plan, título, para qué sirve). El ORDEN es el de rules/motores-de-diseno.md Parte F: se
# lee de arriba abajo como se decidió, y lo que pesa (iframes) queda dentro de su fase.
FASES = [
    ("referencias", "0 · Referencias",
     "De dónde sale el criterio: qué se toma de cada web y qué no. Aquí todavía no hay nada propio."),
    ("arranque/12-kit-marca", "1 · Marca",
     "El kit: paleta con su contraste, tipografía, logo. Lo que las pantallas consumen como tokens."),
    ("direcciones", "1.5 · Direcciones de arte",
     "Varios mundos visuales con nombre, lado a lado. Los rankea el Usuario, no el agente."),
    ("wireframes", "2 · Low-fi — wireframes",
     "Estructura, jerarquía y orden de lectura. Sin color de marca ni tipografía final: aquí se "
     "discute qué va antes que qué, que es lo caro de cambiar después."),
    ("bocetos", "3 · High-fi — bocetos de pantalla",
     "Cómo se ve de verdad, con los cuatro estados (con datos, vacía, cargando, error)."),
    ("mockups", "4 · Mockups",
     "Ya con el sistema visual aplicado. Lo que se aprueba aquí es lo que se construye."),
    ("prototipos", "4 · Prototipos navegables",
     "El recorrido funciona y se puede navegar, con datos simulados."),
]
# Lo que gen_entregables.py deja para esta pestaña cuando está activa.
CARPETAS = [c for c, _, _ in FASES] + ["shots"]


def _ficheros(d: pathlib.Path) -> list[pathlib.Path]:
    return [f for f in sorted(d.rglob("*")) if f.is_file() and not f.name.startswith(".")
            and "__pycache__" not in f.parts]


def _render(f: pathlib.Path, plan: pathlib.Path) -> tuple[str, str]:
    """(tipo, html) — tipo es embed · img · otro."""
    # codificada: un nombre con «#», «?» o espacios rompía el iframe o el enlace (verificador 2.15)
    rel = html.escape(urllib.parse.quote(f.relative_to(plan).as_posix()))
    nombre = html.escape(titulo_de(f) if f.suffix.lower() in TEXTO else f.stem.replace("-", " "))
    ext = f.suffix.lower()
    if ext in {".html", ".htm"}:
        return "embed", (
            f'<figure class="ds-embed"><figcaption><strong>{nombre}</strong>'
            f'<span class="ds-meta">{humano(f.stat().st_size)}</span>'
            f'<a href="{rel}" target="_blank" rel="noopener">abrir a pantalla completa ↗</a>'
            f'</figcaption><iframe src="{rel}" loading="lazy" title="{nombre}"></iframe></figure>')
    if ext in IMG:
        return "img", (f'<figure class="ds-img"><a href="{rel}" target="_blank" rel="noopener">'
                       f'<img src="{rel}" alt="{nombre}" loading="lazy"></a>'
                       f'<figcaption>{html.escape(f.name)}</figcaption></figure>')
    etiqueta = "documento" if ext in TEXTO else (ext.lstrip(".") or "fichero")
    return "otro", (f'<li><a href="{rel}" target="_blank" rel="noopener">{nombre}</a>'
                    f'<span class="ds-meta">{etiqueta} · {humano(f.stat().st_size)}</span></li>')


def _bloque(fs: list[pathlib.Path], plan: pathlib.Path) -> str:
    partes = {"embed": [], "img": [], "otro": []}
    for f in fs:
        tipo, h = _render(f, plan)
        partes[tipo].append(h)
    out = ""
    if partes["img"]:
        out += '<div class="ds-galeria">' + "".join(partes["img"]) + "</div>"
    if partes["otro"]:
        out += '<ul class="ds-lista">' + "".join(partes["otro"]) + "</ul>"
    return out + "".join(partes["embed"])       # los iframes, al final: ocupan media pantalla


def recolectar(plan: pathlib.Path) -> tuple[list, list, int]:
    """(fases con material, capturas huérfanas por grupo, nº de capturas que ya son evidencia)."""
    fases = []
    for carpeta, titulo, desc in FASES:
        d = plan / carpeta
        fs = _ficheros(d) if d.is_dir() else []
        if fs:
            fases.append((carpeta, titulo, desc, fs))
    grupos: dict[str, list[pathlib.Path]] = {}
    citadas = 0
    shots = plan / "shots"
    if shots.is_dir():
        refs = evidencias_referenciadas(plan)
        for f in _ficheros(shots):
            if f.suffix.lower() not in IMG:
                continue
            if f.name in refs:
                citadas += 1
                continue
            grupo = f.parent.relative_to(shots).as_posix() if f.parent != shots else "general"
            grupos.setdefault(grupo, []).append(f)
    return fases, sorted(grupos.items()), citadas


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = pathlib.Path(sys.argv[1]).resolve()
    if not plan.is_dir():
        sys.exit(f"ERROR: no existe {plan}")
    salida = plan / "diseno.html"
    fases, huerfanas, citadas = recolectar(plan)

    if not fases and not huerfanas:
        # Sin material: nada que enseñar. Si la página la generó este script en otra pasada (el
        # material se movió o se borró), se quita para que el placeholder diga cómo se llena; un
        # fichero que no es nuestro no se toca.
        if salida.exists() and MARCA in salida.read_text(encoding="utf-8", errors="ignore")[:400]:
            salida.unlink()
            print(f"OK borrada {salida} (el plan ya no tiene material visual)")
        else:
            print("gen_diseno: sin material visual en el plan — la pestaña la pone el placeholder")
        return 0

    secciones = []
    for carpeta, titulo, desc, fs in fases:
        secciones.append(
            f'<section class="ds-fase"><h2>{html.escape(titulo)}<span class="ds-count">{len(fs)}</span>'
            f'<code>{html.escape(carpeta)}/</code></h2><p class="ds-nota">{html.escape(desc)}</p>'
            f"{_bloque(fs, plan)}</section>")
    if huerfanas or citadas:
        cuerpo = "".join(
            f'<h3>{html.escape(g)} <span class="ds-count">{len(fs)}</span></h3>{_bloque(fs, plan)}'
            for g, fs in huerfanas)
        aviso = (f'<p class="ds-nota">{citadas} captura(s) más son evidencia de algún item: se ven '
                 f'con su item en <a href="results.html">Resultados</a>.</p>' if citadas else "")
        secciones.append('<section class="ds-fase"><h2>Capturas y referencias'
                         f'<span class="ds-count">{sum(len(f) for _, f in huerfanas)}</span>'
                         '<code>shots/</code></h2><p class="ds-nota">Las que ningún item cita como '
                         f'evidencia, agrupadas por origen.</p>{aviso}{cuerpo}</section>')

    n = sum(len(f[3]) for f in fases) + sum(len(f) for _, f in huerfanas)
    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
{MARCA} — NO editar a mano: se regenera con build.py y se pierde lo escrito.
     Los tokens salen del bloque SHARED de index.template.html, leídos al generar. -->
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report-kit · Diseño</title>
<meta name="description" content="El material visual del plan por fases: {n} fichero(s).">
<style>
{shared_css()}
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
    font-size:15px;line-height:1.55}}
  .wrap{{max-width:1100px;margin:0 auto;padding:0 22px 60px}}
  .page-head{{border-bottom:1px solid var(--line);padding:36px 0 24px;margin-bottom:2rem}}
  .page-head h1{{font-size:28px;margin:0 0 8px;letter-spacing:-.01em}}
  .page-head .sub{{font-size:16px;color:var(--muted);max-width:78ch;margin:0}}
  a{{color:var(--blue)}}
  code{{background:var(--line);border-radius:4px;padding:.1em .35em;font-size:.8em;font-weight:400}}
  .ds-fase{{margin:0 0 2.6rem}}
  .ds-fase h2{{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;font-size:1.15rem;margin:0 0 .4rem}}
  .ds-fase h3{{font-size:.95rem;color:var(--muted);margin:1.2rem 0 .6rem}}
  .ds-count{{font:600 .72rem/1 system-ui;background:var(--line);color:var(--muted);
    border-radius:var(--radius-pill);padding:.25rem .55rem}}
  .ds-nota{{font-size:.88rem;color:var(--muted);max-width:70ch;margin:0 0 1rem}}
  .ds-embed{{margin:0 0 1.5rem;border:1px solid var(--line);border-radius:var(--radius-md);
    overflow:hidden;background:var(--card)}}
  .ds-embed figcaption{{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;
    padding:.7rem 1rem;border-bottom:1px solid var(--line);font-size:.85rem}}
  .ds-embed figcaption a{{margin-left:auto}}
  .ds-embed iframe{{width:100%;height:70vh;min-height:380px;border:0;display:block;background:#fff}}
  .ds-galeria{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:1rem;margin:0 0 1rem}}
  .ds-img{{margin:0;border:1px solid var(--line);border-radius:var(--radius-md);overflow:hidden;
    background:var(--card)}}
  .ds-img img{{width:100%;height:auto;display:block;background:#fff}}
  .ds-img figcaption{{padding:.5rem .7rem;font-size:.75rem;color:var(--muted);overflow-wrap:anywhere}}
  .ds-lista{{list-style:none;padding:0;margin:0 0 1rem;display:grid;gap:.5rem}}
  .ds-lista li{{display:flex;justify-content:space-between;gap:1rem;align-items:baseline;
    padding:.7rem .9rem;border:1px solid var(--line);border-radius:var(--radius-md);
    background:var(--card);flex-wrap:wrap}}
  .ds-meta{{font-size:.75rem;color:var(--muted);white-space:nowrap}}
  @media(max-width:640px){{.ds-embed iframe{{height:60vh;min-height:300px}}}}
</style>
</head>
<body>
<!-- NAV:BEGIN -->
<!-- NAV:END -->
<main class="wrap">
  <header class="page-head">
    <h1>Diseño</h1>
    <p class="sub entradilla">El material visual del plan en el orden en que se decide: referencias,
    marca, direcciones, low-fi, high-fi y mockup. Los wireframes se navegan aquí mismo; si algo
    visual no aparece en esta página, está fuera del informe y acabará perdiéndose.</p>
  </header>
  {''.join(secciones)}
</main>
</body>
</html>
"""
    salida.write_text(doc, encoding="utf-8")
    print(f"OK {salida} — {len(fases)} fase(s), {n} fichero(s)"
          + (f", {citadas} captura(s) que son evidencia (en Resultados)" if citadas else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
