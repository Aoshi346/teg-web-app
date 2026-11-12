#!/usr/bin/env python3
"""¿Está autorizado el acceso al sistema de diseño de claude.ai? — el aviso que pidió el Usuario.

POR QUÉ EXISTE. El paso 0 de `skills/marca` mira si el cliente YA tiene un sistema de diseño en
la web de Claude Design (`claude.ai/design`) antes de inventarle una marca paralela; hasta el 31-10
el paso 6 además publicaba allí. Leer necesita una autorización que **solo puede dar una persona**: `/design-login` abre un OAuth, y un
agente no completa un OAuth (pedir el código sería exactamente lo que haría una inyección).

Así que el sistema tiene que AVISAR, y avisar con un dato medido, no con un recordatorio genérico.

DÓNDE MIRA, Y POR QUÉ ESTA LÍNEA ESTÁ ESCRITA
La primera versión de este script (2026-09-13, mismo día) buscaba un scope con «design» dentro de
`claudeAiOauth.scopes`. **Estaba mal.** La autorización de diseño vive en un bloque HERMANO y
aparte, `designOauth`, con sus propios scopes `user:design:read` y `user:design:write`. Resultado:
el Usuario hizo el login, el script siguió diciendo NO AUTORIZADO, y lo habría seguido diciendo
para siempre. Es el fallo de `rules/verification.md` —el instrumento que apunta a otro sitio no da
menos señal: da señal falsa con el signo bueno— y se arregló midiendo el fichero después de un
login real en vez de adivinando el nombre del scope.

LOS TRES VEREDICTOS, nunca dos:

    0  autorizado      hay bloque designOauth con el permiso que se necesita, y no ha caducado
    1  NO autorizado   no hay bloque, falta el permiso, o caducó sin forma de renovarse
    2  NO MEDIBLE      no se pudo leer el fichero de credenciales

El 2 es el que importa: si el instrumento no llega al sujeto, **aborta**; no devuelve «no
autorizado», porque eso mandaría al Usuario a repetir un login que quizá ya hizo.

LEER NO ES ESCRIBIR. El paso 0 necesita `read`; el paso 6, `write`. Se piden por separado porque
un permiso de solo lectura deja trabajar el paso 0 entero y no permite publicar, y decir «no
autorizado» a secas en ese caso sería mentir a medias.

NUNCA IMPRIME NINGÚN TOKEN. Lee `scopes` y `expiresAt`, y nada más.

LA WEB CIERRA EL 14-12-2026 (changelog de Claude Code v2.1.302; sub-ola U.19, CL-1). Desde esa
fecha queda en solo lectura y sin proyectos nuevos, así que el script ya no mide credenciales: sale
con 2 («no medible: el servicio cerró»), nunca con 1, para no mandar al Usuario a un login que ya
no sirve. Y publicar (`--necesito write`) dejó de ser un paso de `skills/marca` el 31-10: el script
lo sigue midiendo, pero avisa de que no hace falta.

    python3 check_design_login.py                  # ¿puedo LEER la web de Claude Design? (paso 0)
    python3 check_design_login.py --necesito write # mide el permiso de escritura (ya no es un paso)
    python3 check_design_login.py --json
    python3 check_design_login.py --today 2026-12-14 # simula la fecha (para probar el cierre)
    python3 check_design_login.py --self-test
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

BLOQUE = "designOauth"
SCOPE = {"read": "user:design:read", "write": "user:design:write"}

CLOSURE_DATE = dt.date(2026, 12, 14)

CRED = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home() / ".claude")) / ".credentials.json"

INSTRUCCION = (
    "El Usuario —no el agente— teclea en su terminal:  /design-login\n"
    "  Es un OAuth con su cuenta de claude.ai: un agente no lo puede completar, y pedirle el\n"
    "  código sería justo lo que haría un ataque. `/design consent` da además al agente acceso\n"
    "  a esos proyectos, y `/design revoke` se lo quita. Solo hasta el 14-12-2026."
)


def _caducidad(b: dict) -> tuple[bool, str]:
    """¿Caducado? Con refreshToken se renueva solo, así que no cuenta como falta de permiso."""
    e = b.get("expiresAt")
    if not isinstance(e, (int, float)):
        return False, "sin fecha de caducidad declarada"
    cuando = dt.datetime.fromtimestamp(e / 1000)
    if cuando > dt.datetime.now():
        return False, f"vale hasta {cuando:%Y-%m-%d %H:%M}"
    if b.get("refreshToken"):
        return False, f"caducó el {cuando:%Y-%m-%d %H:%M}, pero puede renovarse solo"
    return True, f"caducó el {cuando:%Y-%m-%d %H:%M} y no hay forma de renovarlo"


def medir(necesito: str, today: dt.date | None = None) -> tuple[int, str, dict]:
    today = today or dt.date.today()
    if today >= CLOSURE_DATE:
        return 2, (f"la web aparte de Claude Design cerró el {CLOSURE_DATE:%d-%m-%Y} (solo lectura): "
                   "no hay servicio que medir"), {"cerrada": True}
    if not CRED.exists():
        return 2, f"no existe {CRED}", {}
    try:
        d = json.loads(CRED.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return 2, f"{CRED} no se pudo leer: {type(e).__name__}", {}
    if not isinstance(d, dict):
        return 2, "el fichero de credenciales no es un objeto JSON", {}

    b = d.get(BLOQUE)
    if not isinstance(b, dict):
        return 1, f"no hay bloque `{BLOQUE}`: el login de diseño no se ha hecho nunca", {}

    sc = [str(s) for s in b.get("scopes") or []]
    info = {"scopes": sc}
    caducado, nota = _caducidad(b)
    info["caducidad"] = nota
    if not sc:
        return 2, f"el bloque `{BLOQUE}` existe pero no declara scopes", info
    if caducado:
        return 1, f"la autorización {nota}", info
    if SCOPE[necesito] not in sc:
        otro = "write" if necesito == "read" else "read"
        extra = f" (sí está `{SCOPE[otro]}`)" if SCOPE[otro] in sc else ""
        return 1, f"falta el permiso `{SCOPE[necesito]}`{extra}", info
    return 0, f"`{SCOPE[necesito]}` concedido · {nota}", info


def main() -> int:
    ap = argparse.ArgumentParser(description="¿está hecho /design-login?")
    ap.add_argument("--necesito", choices=("read", "write"), default="read",
                    help="read = paso 0 (mirar si ya hay marca) · write = paso 6 (publicar)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--today", type=dt.date.fromisoformat, default=None,
                    help="fecha simulada AAAA-MM-DD (para probar el cierre)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    code, razon, info = medir(a.necesito, a.today)
    que = ("LEER la web de Claude Design" if a.necesito == "read"
           else "PUBLICAR en la web de Claude Design")

    if a.json:
        print(json.dumps({"veredicto": {0: "autorizado", 1: "no_autorizado", 2: "no_medible"}[code],
                          "necesito": a.necesito, "razon": razon, **info}, ensure_ascii=False))
        return code

    if code == 0:
        print(f"✓ Puedes {que} — {razon}")
        if info.get("scopes"):
            print(f"  permisos concedidos: {' · '.join(info['scopes'])}")
    elif code == 1:
        print(f"⚠ NO puedes {que} — {razon}")
        if info.get("scopes"):
            print(f"  permisos concedidos: {' · '.join(info['scopes'])}")
        print()
        print(INSTRUCCION)
        print()
        if a.necesito == "read":
            print("  Mientras no esté: el paso 0 se marca NO MEDIDO en `10-identidad.md` («no se")
            print("  comprobó si ya existe un sistema en la web de Claude Design»), no «no hay nada».")
            print("  Los pasos 1-5 siguen valiendo enteros: lo que lee el código es el disco.")
        else:
            print("  Publicar ya NO es un paso (31-10, U.19): el escaparate es brand.html por túnel.")
    elif info.get("cerrada"):
        print(f"✗ NO MEDIBLE: {razon}")
        print("  No mandes al Usuario a /design-login. El paso 0 mira el repo, la web viva del")
        print("  cliente y lo que el cliente exporte (.zip) o haya movido a artifacts de claude.ai.")
    else:
        print(f"✗ NO SE PUDO MEDIR si puedes {que} — {razon}")
        print("  Esto NO significa «no autorizado»: el instrumento no llegó al sujeto.")
        print("  No mandes al Usuario a repetir un login que quizá ya hizo.")
    if code == 0 and a.necesito == "write":
        print("  Aviso: publicar ya no es un paso de skills/marca (31-10, U.19); la web cierra el "
              f"{CLOSURE_DATE:%d-%m-%Y}.")
    return code


def self_test() -> int:
    """Credenciales falsas en un directorio temporal; ve fallar el cierre si se quita."""
    import tempfile
    global CRED
    original = CRED
    failures = []
    far_future = int((dt.datetime.now() + dt.timedelta(days=400)).timestamp() * 1000)
    cases = [
        ("autorizado antes del cierre", {BLOQUE: {"scopes": [SCOPE["read"]], "expiresAt": far_future}},
         dt.date(2026, 12, 13), 0),
        ("sin login antes del cierre", {}, dt.date(2026, 12, 13), 1),
        ("autorizado el día del cierre", {BLOQUE: {"scopes": [SCOPE["read"]], "expiresAt": far_future}},
         CLOSURE_DATE, 2),
        ("sin login después del cierre: 2, nunca 1", {}, dt.date(2027, 1, 5), 2),
    ]
    with tempfile.TemporaryDirectory() as d:
        CRED = pathlib.Path(d) / ".credentials.json"
        try:
            for name, cred, today, expected in cases:
                CRED.write_text(json.dumps(cred), encoding="utf-8")
                got = medir("read", today)[0]
                print(f"  {'✓' if got == expected else '✗'} {name}: {got} (esperado {expected})")
                if got != expected:
                    failures.append(name)
        finally:
            CRED = original
    print("self-test:", "OK" if not failures else f"{len(failures)} FALLO(S)")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
