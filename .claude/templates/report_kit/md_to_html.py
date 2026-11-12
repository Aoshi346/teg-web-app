#!/usr/bin/env python3
"""md_to_html.py — convierte un informe markdown en una página HTML autocontenida del report-kit.

Por qué existe: los informes de `sources/` se enlazaban en crudo (.md) y el navegador los servía
como texto plano — una tabla de 137 filas en markdown sin renderizar no se lee. Nuestra propia
convención dice que un informe se entrega en HTML (`rules/html-output.md`).

Sin dependencias A PROPÓSITO: `markdown`/`mistune` no están instalados y meter una dependencia en
`build.py` obligaría a instalarla en cada uno de los proyectos derivados. Cubre exactamente lo que
usan nuestros informes (medido sobre los 17 de este plan): encabezados, tablas, listas anidadas,
listas numeradas, citas, bloques de código, negrita/cursiva, código en línea, enlaces y reglas.
Lo que no reconoce sale como párrafo — degrada a texto legible, nunca a página rota.

Uso:  python3 md_to_html.py entrada.md salida.html "Título" [--css ruta_plantilla]
"""
import html
import re
import sys

INLINE_CODE = "\x00CODE%d\x00"
INLINE_EM = "\x00EM%d\x00"


def _inline(text: str) -> str:
    """Formato dentro de una línea. El código en línea se aparta ANTES de escapar y se repone al
    final: si no, un `<div>` dentro de backticks se procesaría como negrita o como etiqueta."""
    stash: list[str] = []

    def keep(m):
        stash.append(m.group(1))
        return INLINE_CODE % (len(stash) - 1)

    text = re.sub(r"`([^`]+)`", keep, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  lambda m: '<a href="%s" target="_blank" rel="noopener">%s</a>'
                            % (html.escape(m.group(2), quote=True), m.group(1)), text)
    # Énfasis, de lo más específico a lo más general. El orden importa: una regla de negrita
    # no-greedy que admita `*` dentro cierra las etiquetas cruzadas (<strong>…<em></strong></em>),
    # así que la cursiva anidada se resuelve con su propio patrón y la negrita se queda estricta.
    text = re.sub(r"\*\*\*([^*]+)\*\*\*", r"<strong><em>\1</em></strong>", text)   # ***ambas***
    text = re.sub(r"\*\*([^*]*)\*([^*]+)\*\*\*", r"<strong>\1<em>\2</em></strong>", text)  # **a *b***
    # Las cursivas se apartan ANTES de la negrita, igual que el código. Motivo: una cursiva EN MEDIO
    # de una negrita (`**a *b* c**`) dejaba un `*` suelto dentro, la negrita estricta [^*]+ no
    # casaba y los asteriscos salían impresos. Apartadas, el contenido de la negrita queda limpio.
    ems: list[str] = []

    def keep_em(m):
        ems.append(m.group(1))
        return INLINE_EM % (len(ems) - 1)

    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", keep_em, text)
    text = re.sub(r"(?<![\w_])_([^_\n]+)_(?![\w_])", keep_em, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)               # **negrita**
    for i, em in enumerate(ems):
        text = text.replace(INLINE_EM % i, "<em>%s</em>" % em)
    for i, code in enumerate(stash):
        text = text.replace(INLINE_CODE % i, "<code>%s</code>" % html.escape(code, quote=False))
    return text


def _split_row(row: str) -> list[str]:
    """Parte una fila por las tuberías NO escapadas. Un `\\|` dentro de una celda es una tubería
    literal —aparece en celdas que citan comandos con pipe (`curl … \\| bash`)— y partir por él
    rompía la celda en dos, dejando a medias el `código en línea` que la envolvía."""
    return [c.replace(r"\|", "|").strip() for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]


def _table(rows: list[str]) -> str:
    cells = [_split_row(r) for r in rows]
    if len(cells) >= 2 and all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells[1]):
        head, body = cells[0], cells[2:]
    else:
        head, body = None, cells
    out = ['<div class="tw"><table>']
    if head:
        out.append("<thead><tr>" + "".join("<th>%s</th>" % _inline(c) for c in head) + "</tr></thead>")
    out.append("<tbody>")
    for row in body:
        out.append("<tr>" + "".join("<td>%s</td>" % _inline(c) for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def convert(md: str) -> str:
    md = md.replace("\r\n", "\n")
    # el frontmatter YAML de una rule (`paths:`) es metadato de carga, no contenido: no se pinta
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    para: list[str] = []
    # pila de listas abiertas: (indentación, etiqueta)
    stack: list[tuple[int, str]] = []
    # último <li> emitido: su posición en `out` y su markdown CRUDO, para poder re-renderizarlo
    # entero cuando llegue una línea de continuación (ver más abajo)
    li_at: int | None = None
    li_raw = ""

    def flush_para():
        nonlocal li_at
        if para:
            out.append("<p>%s</p>" % _inline(" ".join(para)))
            para.clear()
            li_at = None

    def close_lists(to_indent=-1):
        nonlocal li_at
        while stack and stack[-1][0] > to_indent:
            out.append("</%s>" % stack.pop()[1])
            li_at = None

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para(); close_lists()
            lang = stripped[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append('<pre%s><code>%s</code></pre>'
                       % (' data-lang="%s"' % html.escape(lang, quote=True) if lang else "",
                          html.escape("\n".join(buf), quote=False)))
            continue

        # Un comentario HTML en su propia línea es un marcador para quien genera el .md (el bloque
        # ESTADO de actualizar_informe.py, p.ej.), no contenido: se pintaba como texto literal
        # («<!-- ESTADO:BEGIN … -->» en mitad de la página). Dentro de un bloque de código, arriba,
        # sí se enseña: allí es un ejemplo.
        if re.fullmatch(r"<!--(?:(?!-->).)*-->", stripped):
            flush_para()
            i += 1
            continue

        if not stripped:
            flush_para(); close_lists()
            li_at = None
            i += 1
            continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush_para(); close_lists()
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"(#{1,6})\s+(.*)", stripped)
        if m:
            flush_para(); close_lists()
            # +1: el h1 de la página es el título de la cabecera. Un informe con diez `# ` sueltos
            # (los hay) pintaría diez titulares del mismo rango que el de la página.
            lvl = min(6, len(m.group(1)) + 1)
            txt = _inline(m.group(2))
            anchor = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", m.group(2)).lower()).strip("-")[:60]
            out.append('<h%d id="%s">%s</h%d>' % (lvl, anchor, txt, lvl))
            i += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_para(); close_lists()
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i]); i += 1
            out.append(_table(rows))
            continue

        if stripped.startswith(">"):
            flush_para(); close_lists()
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append("<blockquote>%s</blockquote>" % _inline(" ".join(buf)))
            continue

        m = re.match(r"( *)([-*+]|\d{1,3}[.)])\s+(.*)", line)
        if m:
            flush_para()
            indent = len(m.group(1))
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            close_lists(indent)
            if not stack or stack[-1][0] < indent:
                stack.append((indent, tag))
                out.append("<%s>" % tag)
            elif stack[-1][1] != tag:
                out.append("</%s>" % stack.pop()[1])
                stack.append((indent, tag))
                out.append("<%s>" % tag)
            li_raw = m.group(3)
            li_at = len(out)
            out.append("<li>%s</li>" % _inline(li_raw))
            i += 1
            continue

        # continuación "perezosa" de un item de lista: en markdown, una línea suelta debajo de un
        # `- …` pertenece a ese item. Tratarla como párrafo aparte parte por la mitad una negrita
        # que cruza el salto de línea (`**scope ASGI\nentero**`) y deja los asteriscos a la vista.
        # Se re-renderiza el item entero desde su markdown crudo, no desde el HTML ya generado.
        if stack and not para and li_at is not None:
            li_raw += " " + stripped
            out[li_at] = "<li>%s</li>" % _inline(li_raw)
            i += 1
            continue

        para.append(stripped)
        i += 1

    flush_para(); close_lists()
    return "\n".join(out)


CSS = """
/* SHARED:BEGIN — copiado de index.template.html; check_shared_block.py lo verifica */
  :root{
    --ink:#1b1b1f;--muted:#6b6b76;--faint:#6c6c78;--paper:#f6f4ef;--card:#fff;--line:#e4e0d7;
    --navy:#1b2a4a;--accent:#c2410c;--green:#15803d;--amber:#b45309;--blue:#1d4ed8;--red:#b42318;
    --radius-sm:6px;--radius-md:10px;--radius:14px;--radius-pill:999px;
    --shadow-modal:0 20px 60px rgba(27,27,31,.28);
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --s-backlog:#6b6b76;--s-doing:#b45309;--s-review:#1d4ed8;--s-done:#15803d;--s-blocked:#b42318;
    --d-aprobar:#15803d;--d-modificar:#1d4ed8;--d-aplazar:#b45309;--d-descartar:#b42318;
  }
  *{box-sizing:border-box}
  h1{font-size:clamp(24px,3.6vw,38px);margin:0 0 10px;letter-spacing:-.02em;color:var(--ink)}
  h1 em{font-style:italic;color:var(--navy)}
  .eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0 0 10px}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px}
  .kpi b{display:block;font-size:28px;font-weight:700;letter-spacing:-.02em;color:var(--navy);line-height:1.15}
  .kpi span{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
  .kpi.warn b{color:var(--red)}
  .badge{display:inline-block;font-size:11px;font-weight:700;padding:3px 10px;border-radius:var(--radius-pill);color:#fff;text-transform:uppercase;letter-spacing:.04em}
  .nodata{max-width:560px;margin:80px auto;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:28px 32px;text-align:center}
  .nodata code{font-family:var(--mono);font-size:.9em;background:#efece4;color:var(--navy);padding:2px 6px;border-radius:6px}
  .icon{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;vertical-align:-2px}
  .demo-banner{display:flex;align-items:center;gap:8px;background:#fdf3e3;border:1px solid #eed9b0;border-radius:var(--radius-sm);padding:8px 14px;margin:14px 0 0;font-size:12.5px;color:#78350f}
  .demo-banner .icon{flex:none}
  .demo-banner[hidden]{display:none}  /* [hidden] pierde ante .demo-banner{display:flex} — sin esto el banner de demo sale SIEMPRE */
  .audience-note{display:flex;align-items:center;gap:8px;background:#eef1f5;border:1px solid #d7dee8;border-radius:var(--radius-sm);padding:8px 14px;margin:12px 0 0;font-size:12.5px;color:var(--navy)}
  .audience-note .icon{flex:none}
  .scroll-hint{display:none;font-size:11px;color:var(--faint);text-align:right;margin:0 0 6px}
  @media(max-width:767px){.scroll-hint{display:block}}
  /* nav responsive: la gestiona el bloque que inyecta render_nav.py (fuente única) */
  /* SHARED:END */
*{box-sizing:border-box}
html,body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15.5px;line-height:1.62}
.wrap{max-width:960px;margin:0 auto;padding:0 22px}
header.hero{border-bottom:1px solid var(--line);padding:26px 0 18px;margin-bottom:26px;background:var(--card)}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint);margin:0 0 6px}
header.hero h1{margin:0;font-size:25px;letter-spacing:-.02em;color:var(--navy)}
.back{display:inline-block;margin-top:12px;font-size:13px;font-weight:600;text-decoration:none;color:var(--navy);
 border:1px solid var(--navy);border-radius:9px;padding:5px 11px;background:var(--card)}
.back:hover{background:var(--navy);color:#fff}
main{padding-bottom:64px}
h1,h2,h3,h4{color:var(--navy);letter-spacing:-.01em;line-height:1.28}
h2{font-size:21px;margin:34px 0 12px;padding-bottom:7px;border-bottom:1px solid var(--line)}
h3{font-size:17px;margin:26px 0 9px} h4{font-size:15px;margin:20px 0 7px}
p{margin:0 0 13px} li{margin:0 0 6px} ul,ol{margin:0 0 14px;padding-left:24px}
a{color:var(--navy)} code{font-family:var(--mono);font-size:.88em;background:#f1ede4;border:1px solid var(--line);
 border-radius:5px;padding:1px 5px;overflow-wrap:anywhere}
pre{background:var(--navy);color:#e9e6df;border-radius:var(--radius);padding:14px 16px;overflow-x:auto;margin:0 0 16px}
pre code{background:none;border:0;color:inherit;padding:0;font-size:12.8px;line-height:1.5}
blockquote{margin:0 0 16px;padding:11px 16px;background:var(--card);border:1px solid var(--line);
 border-left:3px solid var(--navy);border-radius:var(--radius);color:var(--ink)}
.tw{overflow-x:auto;margin:0 0 18px;border:1px solid var(--line);border-radius:var(--radius);background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:13.6px}
th,td{text-align:left;padding:8px 11px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f4f1ea;color:var(--navy);font-weight:650;white-space:nowrap}
tr:last-child td{border-bottom:0}
hr{border:0;border-top:1px solid var(--line);margin:26px 0}
/* SIN bloque `prefers-color-scheme:dark`, y es deliberado. El resto del kit no tiene modo oscuro y
   la topnav que inyecta render_nav.py es de color FIJO claro (`.topnav{background:rgba(246,244,239,.93)}`).
   Con el bloque puesto, en un navegador en oscuro la página salía #16161a con una barra crema
   pegada encima — medido en web-manager-coolify, no supuesto. Si algún día el kit entero adopta
   modo oscuro, este bloque vuelve A LA VEZ que el de la topnav, nunca antes. */
@media(max-width:640px){body{font-size:15px}th,td{padding:7px 9px}}
"""

SHELL = """<!doctype html>
<html lang="es">
<!-- Generado por report_kit/md_to_html.py desde {src} — NO editar a mano: se regenera con build.py -->
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{resumen}">
<style>{css}</style>
</head>
<body>
<header class="hero"><div class="wrap">
  <p class="eyebrow">Informe de investigación · fuente del plan</p>
  <h1>{title}</h1>
  <a class="back" href="../fuentes.html">← volver a Fuentes</a>
</div></header>
<main class="wrap">
{body}
</main>
</body>
</html>
"""


def recortar(txt: str, limite: int = 240) -> str:
    """Corta un resumen por la última palabra entera antes de `limite`, con «…»."""
    if len(txt) <= limite:
        return txt
    corte = txt.rfind(" ", 0, limite)
    return txt[:corte if corte > 160 else limite].rstrip(" ,;:") + "…"


def cabecera_md(md: str) -> tuple[str, str]:
    """(título, resumen) de un informe markdown, para la pestaña Fuentes y para la
    `<meta name="description">` de la página que genera este script.

    Título: el `# ` de arriba del todo. Si el informe no lleva ninguno (los hay), el primero que
    aparece puede estar enterrado a mitad del documento y no lo describe —pasó: un informe salió
    titulado con la ruta de un fichero de su §1—. De ahí el límite de líneas; quien llama pone el
    respaldo desde el nombre del fichero.
    Resumen: la primera línea de contenido, como texto plano (sin **negrita**, `código`, enlaces ni
    la viñeta de lista). Vivía en `build.py`; aquí para que las dos cosas digan lo mismo (MO-40).
    """
    titulo, leidas = "", 0
    for line in md.splitlines():
        line = line.strip()
        if not line or line.startswith(("<!--", "-->", ">", "---", "***", "|", "!")):
            continue
        leidas += 1
        if line.startswith("# ") and not titulo and leidas <= 3:
            titulo = line[2:].strip()
            continue
        if not line.startswith("#"):
            txt = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
            txt = re.sub(r"(\*\*|__|[*_`])", "", txt).strip()
            txt = re.sub(r"^(?:[-+]\s+|\d+[.)]\s+)", "", txt)      # la viñeta no es contenido
            return titulo, recortar(txt)
    return titulo, ""


def render_file(src_md: str, out_html: str, title: str) -> None:
    md = open(src_md, encoding="utf-8").read()
    _, resumen = cabecera_md(md)
    md = re.sub(r"^<!--.*?-->\s*", "", md, flags=re.S)  # la nota de cabecera es metadato, no contenido
    # el `# Título` del markdown ya se pinta en la cabecera de la página: dejarlo sale duplicado
    md = re.sub(r"^\s*#\s+.*?\n", "", md, count=1)
    # La <meta name="description"> lleva el resumen: así una página generada desde un .md que NO
    # vive en sources/ (y que Fuentes lista como «página propia») se describe sola (MO-40).
    open(out_html, "w", encoding="utf-8").write(
        SHELL.format(title=html.escape(title, quote=False), css=CSS,
                     resumen=html.escape(resumen, quote=True),
                     body=convert(md), src=html.escape(src_md.split("/")[-1], quote=False)))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    render_file(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[1])
    print("OK %s" % sys.argv[2])
