#!/usr/bin/env python3
"""Graba en vídeo un recorrido del navegador para adjuntarlo a un PR con interfaz.

Uso:
    python3 .claude/scripts/pr_video.py <url> <out.webm> [--steps '<json>'] [--width N]
                                        [--height N] [--wait-ms N] [--slow-mo N]

Por qué existe: una captura demuestra que una pantalla EXISTE; no demuestra que el flujo
funciona. No se ve el clic, ni la transición, ni el error que aparece a mitad de camino.
Playwright graba vídeo de forma nativa, así que el coste real no es grabarlo — es el peso del
fichero. Ver `rules/trunk-based-flow.md` §4.1: el vídeo se exige SOLO en PRs con un flujo de
varios pasos, y el .webm NO se commitea (se adjunta al PR).

Comparte la detección de binario con `screenshot.py`: los snippets suelen hardcodear
`/usr/bin/chromium-browser`, que en algunos servidores no existe.

--steps recibe un JSON con una lista de acciones que se ejecutan en orden. Cada acción es un
objeto con UNA clave:

    {"goto":     "<url>"}          navega
    {"click":    "<selector>"}     clic (prefiere data-testid — `rules/verification.md` §E2E-2)
    {"fill":     ["<sel>", "<v>"]} escribe en un campo
    {"press":    "<tecla>"}        p.ej. "Enter"
    {"wait_for": "<selector>"}     espera a que sea visible  ← preferido
    {"wait_ms":  500}              espera fija               ← último recurso

Ejemplo:
    python3 .claude/scripts/pr_video.py "http://127.0.0.1:8000/login" /tmp/pr-42.webm --steps '[
      {"fill": ["[data-testid=\\"login-email\\"]", "demo@example.test"]},
      {"click": "[data-testid=\\"login-submit\\"]"},
      {"wait_for": "[data-testid=\\"dashboard\\"]"}
    ]'

Sin --steps graba la carga de la página y espera --wait-ms; sirve para una animación de entrada,
pero para eso casi siempre basta una captura.

Nota: `file://` suele estar bloqueado. Para HTML local, sirve la carpeta con
`python3 -m http.server` y pasa `http://127.0.0.1:<puerto>/...`.
"""
import argparse
import json
import os
import shutil
import sys

# Espera por CONDICIÓN, no por tiempo (`rules/verification.md` §E2E-3). Con ThreadingHTTPServer
# hay que usar wait_until="load" y NUNCA "networkidle" (`rules/harness-gotchas.md`).
GOTO_KWARGS = {"wait_until": "load", "timeout": 30000}


def find_chrome():
    """Devuelve el path del primer navegador disponible, o None (Playwright usa el suyo)."""
    for name in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def run_step(pg, step, default_timeout):
    """Ejecuta UNA acción del guion. Devuelve su descripción para el log."""
    if not isinstance(step, dict) or len(step) != 1:
        raise ValueError(f"cada paso debe ser un objeto con UNA clave, recibido: {step!r}")
    (action, value), = step.items()

    if action == "goto":
        pg.goto(value, **GOTO_KWARGS)
    elif action == "click":
        pg.click(value, timeout=default_timeout)
    elif action == "fill":
        selector, text = value
        pg.fill(selector, text, timeout=default_timeout)
    elif action == "press":
        pg.keyboard.press(value)
    elif action == "wait_for":
        pg.wait_for_selector(value, state="visible", timeout=default_timeout)
    elif action == "wait_ms":
        pg.wait_for_timeout(int(value))
    else:
        raise ValueError(f"acción desconocida: {action!r} (ver el docstring)")
    return f"{action}: {value!r}"


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("out", help="fichero de salida .webm")
    ap.add_argument("--steps", default="[]", help="JSON con la lista de acciones (ver docstring)")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--wait-ms", type=int, default=1500,
                    help="espera final antes de cerrar, para que el vídeo no corte en seco")
    ap.add_argument("--slow-mo", type=int, default=250,
                    help="ms de pausa entre acciones; sin esto el vídeo es ilegible para un humano")
    ap.add_argument("--timeout", type=int, default=15000, help="timeout por acción, en ms")
    args = ap.parse_args()

    try:
        steps = json.loads(args.steps)
    except json.JSONDecodeError as e:
        sys.exit(f"[pr_video] --steps no es JSON válido: {e}")
    if not isinstance(steps, list):
        sys.exit("[pr_video] --steps debe ser una LISTA de acciones")

    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)

    from playwright.sync_api import sync_playwright

    chrome = find_chrome()
    launch_kwargs = {"headless": True, "args": ["--no-sandbox"], "slow_mo": args.slow_mo}
    if chrome:
        launch_kwargs["executable_path"] = chrome
        print(f"[pr_video] usando {chrome}")
    else:
        print("[pr_video] sin Chrome del sistema; usando el Chromium de Playwright")

    viewport = {"width": args.width, "height": args.height}
    failed_at = None

    with sync_playwright() as p:
        b = p.chromium.launch(**launch_kwargs)
        # Playwright decide él el nombre del .webm dentro de record_video_dir; se renombra al
        # cerrar el contexto, que es cuando el fichero queda cerrado y completo.
        ctx = b.new_context(viewport=viewport,
                            record_video_dir=out_dir,
                            record_video_size=viewport)
        pg = ctx.new_page()
        try:
            pg.goto(args.url, **GOTO_KWARGS)
            for i, step in enumerate(steps, 1):
                print(f"[pr_video] paso {i}/{len(steps)} · {run_step(pg, step, args.timeout)}")
            pg.wait_for_timeout(args.wait_ms)
        except Exception as e:
            # No abortamos: el vídeo del intento fallido es justo la evidencia que hace falta.
            failed_at = f"{type(e).__name__}: {e}"
            print(f"[pr_video] FALLO en el recorrido -> {failed_at}", file=sys.stderr)
            pg.wait_for_timeout(1000)

        tmp_path = pg.video.path() if pg.video else None
        ctx.close()   # cierra y vuelca el .webm
        b.close()

    if not tmp_path or not os.path.exists(tmp_path):
        sys.exit("[pr_video] Playwright no produjo vídeo (¿el contexto se cerró antes de tiempo?)")

    os.replace(tmp_path, args.out)
    size_mb = os.path.getsize(args.out) / 1_048_576
    print(f"[pr_video] guardado en {args.out} ({size_mb:.1f} MB)")
    if size_mb > 10:
        print("[pr_video] AVISO: >10 MB. Recorta el recorrido o baja --width/--height; "
              "un vídeo que nadie abre no es evidencia.", file=sys.stderr)
    print("[pr_video] adjúntalo al PR — NO lo commitees (rules/trunk-based-flow.md §4.1)")

    if failed_at:
        sys.exit(f"[pr_video] el recorrido falló ({failed_at}); el vídeo muestra hasta dónde llegó")


if __name__ == "__main__":
    main()
