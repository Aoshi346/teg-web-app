#!/usr/bin/env python3
"""Sella el objeto de una ronda de QA: lo que se SIRVE y lo que llega por la API, no solo el sha.

POR QUÉ (qa-loop.md §1b, MO-51; cosechado de elvion, `scripts/certifica_el_objeto.sh`):
  Un sha no describe lo que ven los auditores. En elvion, quince rondas se certificaron con el sha y
  el md5 de la plantilla; Vera reordenó las categorías del catálogo, lo que el cliente VE cambió por
  completo y el md5 de la plantilla no se movió, porque el cambio viajaba por la API. El bundle del
  widget estaba en `.gitignore`: su md5 no se puede reconstruir desde un sha. Y certificar son DOS
  medidas, al abrir y al cerrar la ronda: la de cierre cazó dos movimientos que la de apertura no
  podía ver. Si los dos sellos no coinciden, los auditores midieron objetos distintos y la ronda no
  se promedia.

USO
  # al ABRIR la ronda
  python3 .claude/scripts/certifica_objeto.py sellar --base http://127.0.0.1:8000 \\
      --pagina / --bundle /static/app.js --api /api/products/ \\
      --cabecera-env X-API-Key=CLAVE_QA --ignorar generated_at \\
      --git-ruta frontend/ --git-ruta backend/ \\
      --guardar .docs/feedback/qa-loop/<WAVE>/iter-<n>/sello/apertura --salida .../sello/apertura.txt
  # al CERRAR, lo mismo con --guardar .../sello/cierre y --salida .../sello/cierre.txt (OTRA carpeta:
  # con la misma, las copias del cierre pisan las de la apertura y no queda nada que comparar), y:
  python3 .claude/scripts/certifica_objeto.py comparar .../apertura.txt .../cierre.txt

  --pagina / --bundle   rutas cuyo cuerpo se sella tal cual (md5 de los bytes servidos)
  --quitar REGEX        quita de las páginas lo que cambia en cada petición (un token CSRF, un nonce)
  --api RUTA            respuestas JSON: se sellan canónicas (claves ordenadas) y se GUARDAN, para
                        que un `diff` diga qué cambió (un sello cuyo cambio no se puede atribuir es
                        peor que no tenerlo: o da falsas alarmas o esconde un cambio real)
  --ignorar CLAVE       claves que se quitan del JSON a cualquier profundidad (fechas de generación…)
  --cabecera "N: v"     cabecera para todas las peticiones; su VALOR nunca se imprime
  --cabecera-env N=VAR  igual, leyendo el valor de la variable de entorno VAR (para claves: así no
                        quedan en la línea de comandos ni en el historial)
  --git-ruta DIR        qué rutas cuentan para «sin commitear» (por defecto, el repo entero; las
                        carpetas de --guardar y de --salida no cuentan nunca, para que los propios
                        sellos no hagan «sucio» el árbol entre la apertura y el cierre)

SALE
  sellar:   0 sellado · 2 NO SE PUDO MEDIR (una ruta que no da 200 —tampoco se siguen las
            redirecciones: un 302 a /login sellaría la pantalla de login—, un JSON que no parsea,
            una variable de cabecera vacía). El instrumento que no puede medir aborta; no devuelve un
            sello a medias (`verification.md` §El instrumento que no puede medir).
  comparar: 0 el objeto no se movió · 1 se movió: LA RONDA NO VALE (dice qué líneas) · 2 falta un
            sello o no lo es.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CABECERA = "# sello del objeto · certifica_objeto.py"
NO_SE_COMPARAN = ("sellado_en", "copia")


def md5(datos: bytes) -> str:
    return hashlib.md5(datos).hexdigest()


class _SinRedirigir(urllib.request.HTTPRedirectHandler):
    """No sigue redirecciones: el 3xx vuelve como error y se trata como «no se pudo medir».
    Seguirlas sellaba la pantalla a la que redirige (un panel sin sesión → /login) y la ronda
    salía «se puede promediar» con el objeto cambiado (verificador de la 2.16)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_ABRIR = urllib.request.build_opener(_SinRedirigir)


def pedir(url: str, cabeceras: dict[str, str], timeout: float) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers=cabeceras)
    try:
        with _ABRIR.open(req, timeout=timeout) as r:
            return r.status, r.read(), ""
    except urllib.error.HTTPError as e:
        return e.code, b"", e.headers.get("Location", "") if e.headers else ""
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ConnectionError(str(getattr(e, "reason", e))) from e


def sin_claves(dato, ignorar: set[str]):
    if isinstance(dato, dict):
        return {k: sin_claves(v, ignorar) for k, v in dato.items() if k not in ignorar}
    if isinstance(dato, list):
        return [sin_claves(v, ignorar) for v in dato]
    return dato


def git(args: list[str], cwd: Path) -> str | None:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def nombre_copia(ruta: str) -> str:
    return "api_" + re.sub(r"[^A-Za-z0-9]+", "_", ruta).strip("_") + ".json"


def sellar(a: argparse.Namespace) -> int:
    cabeceras: dict[str, str] = {}
    for c in a.cabecera:
        if ":" not in c:
            # el argumento entero NO se repite: podría ser el valor de una clave mal escrito
            print("NO SE PUDO MEDIR: un --cabecera no lleva «:» (se espera «Nombre: valor»)",
                  file=sys.stderr)
            return 2
        n, v = c.split(":", 1)
        cabeceras[n.strip()] = v.strip()
    for c in a.cabecera_env:
        if "=" not in c:
            print(f"NO SE PUDO MEDIR: --cabecera-env espera NOMBRE=VARIABLE ({c})", file=sys.stderr)
            return 2
        n, var = c.split("=", 1)
        valor = os.environ.get(var, "")
        if not valor:
            print(f"NO SE PUDO MEDIR: la variable {var} (cabecera {n}) está vacía o no existe",
                  file=sys.stderr)
            return 2
        cabeceras[n.strip()] = valor
    if not (a.pagina or a.bundle or a.api):
        print("NO SE PUDO MEDIR: no hay nada que sellar (--pagina, --bundle o --api)", file=sys.stderr)
        return 2
    base = a.base.rstrip("/")
    ignorar = set(a.ignorar)
    lineas = [CABECERA, f"sellado_en     {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
              f"base           {base}"]

    repo = Path(a.repo)
    sha = git(["rev-parse", "--short", "HEAD"], repo)
    if sha is None:
        lineas.append("sha            sin-git   (el sha no describe nada aquí: lo dicen las líneas de abajo)")
    else:
        # Los propios sellos no cuentan como «sin commitear»: si se guardan dentro del repo, el
        # cierre vería la apertura como un fichero nuevo y la ronda saldría «no vale» sin que nada
        # se moviera (verificador de la 2.16). Se excluyen la carpeta de --guardar y la de --salida
        # (o solo el fichero, si --salida está en la raíz del repo).
        raiz = Path((git(["rev-parse", "--show-toplevel"], repo) or str(repo)).strip()).resolve()
        excluir = []
        for ruta, es_dir in ((a.guardar, True), (a.salida, False)):
            if not ruta:
                continue
            p = Path(ruta).resolve()
            objetivo = p if es_dir else (p.parent if p.parent != raiz else p)
            try:
                excluir.append(f":(exclude){objetivo.relative_to(raiz)}")
            except ValueError:
                pass                                    # fuera del repo: no hay nada que excluir
        sucio = git(["status", "--porcelain", "--", *(a.git_ruta or ["."]), *excluir], repo) or ""
        n = len([x for x in sucio.splitlines() if x.strip()])
        lineas.append(f"sha            {sha.strip()}")
        aviso = "   ⚠ el sha NO describe lo servido" if n else ""
        lineas.append(f"sin_commitear  {n}{aviso}")

    guardar = Path(a.guardar) if a.guardar else None
    if guardar and guardar.is_dir() and any(guardar.glob("api_*.json")) and a.api:
        print(f"AVISO: {guardar} ya tiene copias de otro sello y se van a sobrescribir: una carpeta "
              "por sello (…/apertura y …/cierre), o el diff de las dos copias no será posible",
              file=sys.stderr)
    if guardar:
        guardar.mkdir(parents=True, exist_ok=True)
    quitar = [re.compile(x) for x in a.quitar]
    for tipo, rutas in (("pagina", a.pagina), ("bundle", a.bundle), ("api", a.api)):
        for ruta in rutas:
            url = base + ruta
            try:
                status, cuerpo, destino = pedir(url, cabeceras, a.timeout)
            except ConnectionError as e:
                print(f"NO SE PUDO MEDIR: {tipo} {ruta} no responde ({e})", file=sys.stderr)
                return 2
            if status != 200:
                hacia = f" (redirige a {destino})" if destino else ""
                print(f"NO SE PUDO MEDIR: {tipo} {ruta} devuelve {status}{hacia}, no 200 — un "
                      "401/429 o una redirección a /login sellarían esa pantalla, no el objeto",
                      file=sys.stderr)
                return 2
            if tipo == "pagina" and quitar:
                texto = cuerpo.decode("utf-8", "replace")
                for rx in quitar:
                    texto = rx.sub("", texto)
                cuerpo = texto.encode("utf-8")
            if tipo == "api":
                try:
                    dato = sin_claves(json.loads(cuerpo), ignorar)
                except ValueError:
                    print(f"NO SE PUDO MEDIR: api {ruta} no devuelve JSON", file=sys.stderr)
                    return 2
                canon = json.dumps(dato, sort_keys=True, ensure_ascii=False, indent=1).encode()
                extra = f"   (sin: {', '.join(sorted(ignorar))})" if ignorar else ""
                lineas.append(f"api            {ruta}   md5 {md5(canon)}{extra}")
                if guardar:
                    copia = guardar / nombre_copia(ruta)
                    copia.write_bytes(canon)
                    lineas.append(f"copia          {copia}")
            else:
                lineas.append(f"{tipo:<14} {ruta}   md5 {md5(cuerpo)}   {len(cuerpo)} B")
    texto = "\n".join(lineas) + "\n"
    if a.salida:
        Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
        Path(a.salida).write_text(texto, encoding="utf-8")
    sys.stdout.write(texto)
    return 0


def leer_sello(ruta: str) -> list[str] | None:
    p = Path(ruta)
    if not p.is_file():
        return None
    lineas = p.read_text(encoding="utf-8").splitlines()
    if not lineas or lineas[0] != CABECERA:
        return None
    return [x for x in lineas[1:] if x.strip() and not x.startswith(NO_SE_COMPARAN)]


def comparar(a: argparse.Namespace) -> int:
    uno, otro = leer_sello(a.apertura), leer_sello(a.cierre)
    for nombre, s in ((a.apertura, uno), (a.cierre, otro)):
        if s is None:
            print(f"NO SE PUDO COMPARAR: {nombre} no existe o no es un sello de certifica_objeto.py",
                  file=sys.stderr)
            return 2
    if uno == otro:
        print("el objeto no se movió entre la apertura y el cierre: la ronda se puede promediar")
        return 0
    print("EL OBJETO SE MOVIÓ: LA RONDA NO VALE (qa-loop.md §1b) — se anota inválida en RESULT.md y "
          "se repite sobre el objeto nuevo")
    for x in uno:
        if x not in otro:
            print(f"  - apertura: {x}")
    for x in otro:
        if x not in uno:
            print(f"  + cierre:   {x}")
    print("  (si se movió una api, `diff` de las dos copias guardadas dice qué cambió)")
    return 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="orden", required=True)
    s = sub.add_parser("sellar", help="mide el objeto y escribe el sello")
    s.add_argument("--base", required=True, help="URL base, p. ej. http://127.0.0.1:8000")
    s.add_argument("--pagina", action="append", default=[])
    s.add_argument("--bundle", action="append", default=[])
    s.add_argument("--api", action="append", default=[])
    s.add_argument("--quitar", action="append", default=[])
    s.add_argument("--ignorar", action="append", default=[])
    s.add_argument("--cabecera", action="append", default=[])
    s.add_argument("--cabecera-env", dest="cabecera_env", action="append", default=[])
    s.add_argument("--git-ruta", dest="git_ruta", action="append", default=[])
    s.add_argument("--repo", default=".", help="raíz del repo para el sha (por defecto, el cwd)")
    s.add_argument("--guardar", help="carpeta donde guardar las copias de lo sellado por API")
    s.add_argument("--salida", help="fichero donde escribir el sello (además de la pantalla)")
    s.add_argument("--timeout", type=float, default=20.0)
    c = sub.add_parser("comparar", help="compara el sello de apertura con el de cierre")
    c.add_argument("apertura")
    c.add_argument("cierre")
    a = ap.parse_args(argv)
    return sellar(a) if a.orden == "sellar" else comparar(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
