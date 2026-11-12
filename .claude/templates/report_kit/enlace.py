#!/usr/bin/env python3
"""enlace.py — el enlace que se le da al Usuario, comprobado ANTES de dárselo (MO-26).

Petición del Usuario (evolution, 17-10-2026): *«siempre que pongas algo que tengo que mirar que sea
en localhost»*. Antes se le daban rutas de fichero o `127.0.0.1` y tenía que montar la URL él; y
alguna vez el enlace no abría porque el servidor ya no estaba. La regla: el enlace es
`http://localhost:<puerto>/<ruta>`, servido en 127.0.0.1, y se comprueba con `curl` antes de darlo.

    python3 enlace.py <puerto> [ruta ...]        # por defecto, index.html
    python3 enlace.py 8880 dashboard.html sources/plan-ejecucion.html

Imprime una línea por enlace (`✓ 200 http://localhost:8880/dashboard.html`) y el túnel SSH para
llegar desde fuera. Sale 1 si alguno no da 200 —ese enlace no se da— y 2 si el puerto escucha en
TODAS las interfaces (0.0.0.0 / [::]): eso no es un enlace a localhost, es el directorio publicado
en internet (`rules/security.md` §Servir HTML), y se para antes de seguir.

Usa `curl` si está (es lo que pidió el Usuario, y es lo que él mismo puede repetir) y `urllib` si no.
"""
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


def codigo(url: str) -> str:
    if shutil.which("curl"):
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "8",
                            url], capture_output=True, text=True)
        return r.stdout.strip() or "000"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except (urllib.error.URLError, OSError):
        return "000"


def expuesto(puerto: int) -> bool:
    """¿Escucha el puerto en todas las interfaces? (sin `ss`, no se puede saber: no se afirma)."""
    if not shutil.which("ss"):
        return False
    out = subprocess.run(["ss", "-Htln", f"sport = :{puerto}"], capture_output=True, text=True).stdout
    return any(t.split()[3].startswith(("0.0.0.0:", "*:", "[::]:")) for t in out.splitlines()
               if len(t.split()) > 3)


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        sys.exit(__doc__)
    puerto = int(sys.argv[1])
    rutas = sys.argv[2:] or ["index.html"]
    if expuesto(puerto):
        print(f"✗ el puerto {puerto} escucha en TODAS las interfaces: no se da ningún enlace. "
              f"Páralo y vuelve a servir con --bind 127.0.0.1 (rules/security.md).")
        return 2
    malos = 0
    for ruta in rutas:
        url = f"http://localhost:{puerto}/{ruta.lstrip('/')}"
        c = codigo(url)
        ok = c == "200"
        malos += not ok
        print(f"{'✓' if ok else '✗'} {c} {url}")
    print(f"  desde fuera:  ssh -N -L {puerto}:127.0.0.1:{puerto} <usuario>@<servidor>")
    if malos:
        print(f"✗ {malos} enlace(s) no dan 200: no se dan hasta que respondan.")
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
