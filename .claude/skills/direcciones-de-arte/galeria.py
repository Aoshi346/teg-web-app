#!/usr/bin/env python3
"""galeria.py — pone las direcciones de arte UNA AL LADO DE OTRA y prepara el ranking humano.

Uso:
    python3 galeria.py <carpeta-con-direcciones> [--puerto 8879] [--salida galeria.html]
                       [--ancho-miniatura 720] [--calidad 58]

Qué hace, y por qué cada parte:
  · Captura cada `*.html` de la carpeta a 1440 y a 390 (la mitad de las decisiones de
    composición solo se juzgan en móvil) con el Chrome del sistema.
  · Embebe las miniaturas en base64: la galería tiene que abrir OFFLINE, desde el móvil
    de quien decide, sin levantar nada (rules/html-output.md).
  · Lee las cinco decisiones de cada dirección de sus `<meta>`; si faltan, lo DICE en la
    tarjeta en vez de rellenarlas — una dirección sin sus cinco decisiones es un moodboard
    (patterns/diseno/catalogo-direcciones.md §2).
  · Escribe `RANKING.csv` con las columnas EXACTAS del ranking humano del corpus
    (resources/referencias-diseno/proceso/RANKING.csv) y la columna Ranking VACÍA.

Lo que NO hace, a propósito: ordenar. El corpus guarda la vez que un agente rankeó y el
humano eligió lo contrario — dos versiones que la IA había puesto en su último escalón
acabaron en producción (proceso/elevaiti-FINAL-RECOMMENDATION.md vs RANKING.csv).

Salida: 0 galería escrita · 2 no se pudo medir (sin ficheros, sin navegador, sin Pillow, puerto
ocupado, servidor que no arranca o una dirección que no responde 200).

`--puerto 8837` y `--puerto=8837` valen igual. Hasta la 2.17 solo valía la segunda: con espacio, el
puerto se ignoraba, el servidor fallaba en silencio contra el 8879 ocupado y la galería embebía el
404 de otro servidor (evolution, improvements #10; MO-24).

Doctrina: patterns/diseno/catalogo-direcciones.md · Skill: skills/direcciones-de-arte/SKILL.md
"""
import argparse
import base64
import html
import io
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

CAMPOS = [("direccion", "Dirección"), ("tipografia", "Tipografía"), ("paleta", "Paleta"),
          ("metafora", "Metáfora de movimiento"), ("imagen", "Imagen"), ("estructura", "Estructura")]


def meta(texto, nombre):
    m = re.search(r'<meta\s+name=["\']%s["\']\s+content=["\'](.*?)["\']' % nombre, texto, re.I | re.S)
    return m.group(1).strip() if m else ""


def titulo(texto, defecto):
    m = re.search(r"<title[^>]*>(.*?)</title>", texto, re.I | re.S)
    return m.group(1).strip() if m else defecto


def miniatura(png_bytes, ancho, calidad):
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if im.width > ancho:
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=calidad, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def no_se_pudo(motivo: str) -> None:
    print(f"NO SE PUDO MEDIR: {motivo}", file=sys.stderr)
    sys.exit(2)


def puerto_libre(puerto: int) -> bool:
    """¿Hay alguien ESCUCHANDO? Con SO_REUSEADDR, como el propio http.server: sin él, un puerto
    recién usado (conexiones en TIME_WAIT, ~60 s) salía «ocupado» sin estarlo."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", puerto))
        except OSError:
            return False
    return True


def _morir_con_el_padre() -> None:
    """En Linux, el hijo recibe SIGTERM cuando muere el padre, también por SIGKILL, que no deja
    correr ningún `finally` (prctl PR_SET_PDEATHSIG = 1). Fuera de Linux no hace nada."""
    try:
        import ctypes
        ctypes.CDLL("libc.so.6", use_errno=True).prctl(1, signal.SIGTERM)
    except (OSError, AttributeError):
        pass


def servir(carpeta: str, puerto: int, log) -> subprocess.Popen:
    """El http.server de la carpeta, y la prueba de que es EL NUESTRO el que contesta: el fichero
    centinela solo existe en esta carpeta. Si no responde en 10 s, o responde otro, exit 2."""
    centinela = f".galeria-{os.getpid()}.txt"
    try:
        with open(os.path.join(carpeta, centinela), "w", encoding="utf-8") as fh:
            fh.write(centinela)
    except OSError as e:
        no_se_pudo(f"no se puede escribir en {carpeta} ({type(e).__name__}): la galería y "
                   "RANKING.csv van ahí")
    srv = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(puerto), "--bind", "127.0.0.1"],
        cwd=carpeta, stdout=subprocess.DEVNULL, stderr=log, preexec_fn=_morir_con_el_padre)
    listo = False
    try:
        for _ in range(50):
            if srv.poll() is not None:
                break
            url = f"http://127.0.0.1:{puerto}/{centinela}"
            try:
                with urllib.request.urlopen(url, timeout=1) as r:
                    if r.read().decode() == centinela:
                        listo = True
                        return srv
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(0.2)
    finally:
        os.remove(os.path.join(carpeta, centinela))
        # Si se sale de aquí sin servidor listo —también por un SIGTERM a mitad de la espera—, el
        # hijo se para aquí: el `finally` de quien llama todavía no existe (medido: huérfano).
        if not listo:
            srv.terminate()
    log.seek(0)
    no_se_pudo(f"el servidor de la galería no contesta en 127.0.0.1:{puerto} "
               f"({(log.read().strip().splitlines() or ['sin mensaje'])[-1]})")


def main():
    ap = argparse.ArgumentParser(
        description="Galería de direcciones de arte para el ranking humano")
    ap.add_argument("carpeta")
    ap.add_argument("--puerto", type=int, default=8879)
    ap.add_argument("--salida")
    ap.add_argument("--ancho-miniatura", type=int, default=720)
    ap.add_argument("--calidad", type=int, default=58)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    a = ap.parse_args()
    carpeta = os.path.abspath(a.carpeta)
    puerto = a.puerto
    salida = a.salida or os.path.join(carpeta, "galeria.html")
    anchomin = a.ancho_miniatura
    calidad = a.calidad

    if not os.path.isdir(carpeta):
        no_se_pudo(f"{carpeta} no es una carpeta")
    ficheros = sorted(f for f in os.listdir(carpeta)
                      if f.endswith(".html") and f != os.path.basename(salida))
    if not ficheros:
        no_se_pudo(f"no hay ningún .html en {carpeta}")
    if not puerto_libre(puerto):
        no_se_pudo(f"el puerto {puerto} está ocupado en 127.0.0.1 — elige otro con --puerto N")

    chrome = (shutil.which("google-chrome") or shutil.which("google-chrome-stable")
              or shutil.which("chromium-browser") or shutil.which("chromium"))
    try:
        from PIL import Image  # noqa: F401
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        no_se_pudo(f"falta {e.name}")

    # 127.0.0.1 a propósito: nunca 0.0.0.0 (rules/security.md §Servir HTML)
    log = tempfile.TemporaryFile(mode="w+")
    # Un SIGTERM o un SIGHUP al padre (no al grupo) dejaba el http.server hijo huérfano y
    # escuchando: así corren los `finally` y el hijo se para (verificadores de la 2.17). Para
    # SIGKILL, que no se puede atrapar, está `_morir_con_el_padre`.
    for senal in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(senal, lambda *_: sys.exit(143))
    srv = servir(carpeta, puerto, log)
    tarjetas = []
    try:
        lanzar = {"headless": True, "args": ["--no-sandbox"]}
        if chrome:
            lanzar["executable_path"] = chrome
        with sync_playwright() as p:
            try:
                b = p.chromium.launch(**lanzar)
            except Exception as e:  # la caché de Playwright desaparece a mitad de sesión (AMC #6)
                # El error ENTERO (la causa va en sus «Browser logs»), y la pista de instalar solo
                # si es eso lo que falta: con una librería del sistema rota no arregla nada.
                lineas = [x for x in str(e).splitlines() if x.strip()][:20]
                pista = ("\n  → `playwright install chromium`, o instala chromium-browser"
                         if "Executable doesn't exist" in str(e) else "")
                no_se_pudo(f"no arranca el navegador ({type(e).__name__}):\n    "
                           + "\n    ".join(lineas) + pista)
            for f in ficheros:
                url = f"http://127.0.0.1:{puerto}/{urllib.parse.quote(f)}"  # «dir #2.html»
                try:
                    with open(os.path.join(carpeta, f), encoding="utf-8", errors="replace") as fh:
                        crudo = fh.read()
                except OSError as e:  # un enlace roto se lista y no se lee
                    no_se_pudo(f"no se puede leer {f} ({type(e).__name__})")
                pg = b.new_page(viewport={"width": 1440, "height": 900})
                resp = pg.goto(url, wait_until="load", timeout=45000)
                if resp is None or resp.status != 200:
                    no_se_pudo(f"{url} respondió HTTP {resp.status if resp else 'sin respuesta'} — "
                               "la miniatura sería la de ese error, no la dirección")
                pg.wait_for_timeout(2200)
                esc = miniatura(pg.screenshot(), anchomin, calidad)
                pg.close()
                pgm = b.new_page(viewport={"width": 390, "height": 844})
                pgm.goto(url, wait_until="load", timeout=45000)
                pgm.wait_for_timeout(1800)
                mov = miniatura(pgm.screenshot(), 300, calidad)
                pgm.close()
                ficha = {k: meta(crudo, k) for k, _ in CAMPOS}
                tarjetas.append({"fichero": f, "titulo": titulo(crudo, f),
                                 "nombre": ficha["direccion"] or titulo(crudo, f),
                                 "ficha": ficha, "esc": esc, "mov": mov,
                                 "faltan": [et for k, et in CAMPOS if not ficha[k]]})
            b.close()
    finally:
        srv.terminate()
        log.close()

    # ── RANKING.csv con las columnas del ranking humano real, y la 1ª vacía ──
    csv = os.path.join(carpeta, "RANKING.csv")
    if os.path.exists(csv):
        print(f"· {csv} ya existe — NO se pisa (puede llevar el ranking ya puesto)")
    else:
        with open(csv, "w", encoding="utf-8") as fh:
            fh.write("Ranking,Versión,Razón de negocio,Elementos destacados\n")
            for t in tarjetas:
                fh.write(f',"{t["nombre"]}","",""\n')
        print(f"· {csv} escrito, con la columna Ranking VACÍA — la rellena una persona")

    # ── La galería ──
    def tarjeta(t):
        filas = "".join(
            f"<tr><th>{html.escape(et)}</th><td>{html.escape(t['ficha'][k]) or '<em>sin declarar</em>'}</td></tr>"
            for k, et in CAMPOS if k != "direccion")
        aviso = (f'<p class="falta">Ficha incompleta: falta {", ".join(t["faltan"])}. '
                 f'Una dirección sin sus cinco decisiones es un moodboard, no una dirección.</p>'
                 if t["faltan"] else "")
        return f"""
    <article class="dir">
      <h2>{html.escape(t['nombre'])}</h2>
      <div class="shots">
        <a href="{html.escape(t['fichero'])}" target="_blank" title="abrir a tamaño completo">
          <img src="data:image/jpeg;base64,{t['esc']}" alt="{html.escape(t['nombre'])} en escritorio" loading="lazy"></a>
        <a href="{html.escape(t['fichero'])}" target="_blank" class="mov">
          <img src="data:image/jpeg;base64,{t['mov']}" alt="{html.escape(t['nombre'])} en móvil" loading="lazy"></a>
      </div>
      {aviso}
      <table>{filas}</table>
      <p class="abrir"><a href="{html.escape(t['fichero'])}" target="_blank">Abrir «{html.escape(t['nombre'])}» a tamaño completo →</a></p>
    </article>"""

    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Direcciones de arte — para ordenar</title>
<style>
  :root{{--tinta:#1c1b19;--papel:#faf8f5;--linea:#e2ddd5;--aviso:#8a3f1e}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--papel);color:var(--tinta);
       font:16px/1.65 -apple-system,"Segoe UI",Roboto,system-ui,sans-serif}}
  header{{max-width:1180px;margin:0 auto;padding:3rem 1.5rem 1rem}}
  h1{{font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.1;margin:0 0 .5rem}}
  .nota{{border-left:3px solid var(--aviso);padding:.9rem 1.1rem;background:#fff;margin:1.5rem 0}}
  .nota strong{{color:var(--aviso)}}
  .dirs{{max-width:1180px;margin:0 auto;padding:0 1.5rem 4rem;display:grid;gap:2.5rem}}
  .dir{{background:#fff;border:1px solid var(--linea);border-radius:10px;padding:1.5rem}}
  .dir h2{{margin:0 0 1rem;font-size:1.35rem}}
  .shots{{display:flex;gap:1rem;align-items:flex-start;flex-wrap:wrap}}
  .shots img{{display:block;width:100%;border:1px solid var(--linea);border-radius:6px}}
  .shots a{{flex:1 1 420px;min-width:0}}
  .shots a.mov{{flex:0 0 180px}}
  table{{border-collapse:collapse;width:100%;margin-top:1.2rem;font-size:.92rem}}
  th,td{{border-top:1px solid var(--linea);padding:.5rem .6rem;text-align:left;vertical-align:top}}
  th{{width:12rem;font-weight:600;color:#555}}
  .falta{{color:var(--aviso);font-size:.9rem;margin:1rem 0 0}}
  .abrir{{margin:1rem 0 0;font-size:.92rem}}
  a{{color:#24506e}}
  @media (max-width:640px){{.shots a.mov{{display:none}}th{{width:8rem}}}}
</style></head><body>
<header>
  <h1>{len(tarjetas)} direcciones de arte, para ordenar</h1>
  <p>Cada una es un mundo visual distinto, no una variación de la anterior. Ábrelas a tamaño
     completo, compáralas, y <strong>ordénalas tú</strong>.</p>
  <div class="nota">
    <p><strong>El agente no ordena estas direcciones, y es deliberado.</strong> En el corpus de la
       casa se conservan dos rankings de las mismas versiones: el de una IA y el de la persona que
       pagaba. Ordenaban distinto, y las dos versiones que llegaron a producción estaban en el
       <em>último</em> escalón del de la IA.</p>
    <p>Rellena la columna <code>Ranking</code> de <code>RANKING.csv</code> (está en esta misma
       carpeta) con <strong>razones de negocio</strong>, no de estética: «los productos se pierden»,
       «no deja claro el problema», «prima estética sobre conversión».</p>
    <p>La que gane <strong>no se entrega intacta</strong>: se fusiona con lo mejor de las descartadas.</p>
  </div>
</header>
<main class="dirs">{"".join(tarjeta(t) for t in tarjetas)}</main>
</body></html>"""
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(doc)
    kb = os.path.getsize(salida) // 1024
    incompletas = sum(1 for t in tarjetas if t["faltan"])
    print(f"· {salida} — {len(tarjetas)} direcciones · {kb} KB · autocontenida")
    if incompletas:
        print(f"⚠ {incompletas} de {len(tarjetas)} sin las cinco decisiones declaradas: "
              f"eso es un moodboard, no una dirección (catalogo-direcciones.md §2)")
    print("· falta lo único que el agente no hace: que una persona rellene RANKING.csv")


if __name__ == "__main__":
    main()
