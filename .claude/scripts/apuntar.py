#!/usr/bin/env python3
"""Apunta una cosa en el informe de un plan, en un comando y sin excusas.

POR QUÉ. Apuntar en el informe de un plan tiene que costar menos que saltárselo; si no, se salta.
(Nació junto a un Stop hook que bloqueaba el fin de turno con el plan sin apuntar; ese hook se
archivó el 2026-10-19 —MO-D1, `_archive/2026-10-19/README.md`— y el informe se exigirá al cerrar
el issue. Esto se queda: lo usa `arrancar`.) Así que apuntar cuesta diez segundos: elige el
siguiente id libre de la wave, escribe los cuatro bloques que exige `rules/report-kit.md` y deja el
hueco donde falte contenido de verdad.

NO sustituye a escribir bien el item. Un item con los cuatro bloques vacíos pasa cualquier gate que
mire ficheros y no sirve para nada: un gate así mira ficheros, no criterio. Esto pone el andamio;
el porqué lo escribes tú.

USO
    python3 .claude/scripts/apuntar.py .docs/plans/2026-08-11-web-miller "Lo que ha pedido"
    python3 .claude/scripts/apuntar.py <plan> "Titulo" --wave "Wave 9 — v5" --pri P1 --esf M \\
        --goal "cómo sabremos que está hecho" --ahora "qué pasa hoy" --como "cómo se haría" \\
        --porque "por qué así y no de otra" --aviso "lo que puede salir mal" \\
        --rec "duda — la decisión es del Usuario" --nocturno "no — decisión de producto"
"""
import argparse
import pathlib
import re
import sys


def siguiente_id(texto: str, prefijo: str) -> str:
    """El primer número libre del prefijo. No reutiliza: los ids son la clave de las decisiones."""
    usados = [int(n) for n in re.findall(rf"`{re.escape(prefijo)}-(\d+)`", texto)]
    return f"{prefijo}-{max(usados) + 1 if usados else 1}"


def ultima_wave(texto: str) -> str:
    waves = re.findall(r"^## (.+)$", texto, re.M)
    return waves[-1] if waves else "Wave 1"


def prefijo_de(texto: str, wave: str) -> str:
    """El prefijo que ya usa esa wave; si es nueva, se deriva de su título."""
    trozo = texto.split(f"## {wave}", 1)[-1].split("\n## ", 1)[0]
    ids = re.findall(r"`([A-Z0-9]+)-\d+`", trozo)
    if ids:
        return ids[0]
    letras = "".join(p[0] for p in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", wave)[:2]).upper()
    return letras or "X"


def main() -> int:
    p = argparse.ArgumentParser(description="Apunta un item en el tasks.md de un plan")
    p.add_argument("plan")
    p.add_argument("titulo")
    p.add_argument("--wave", default=None, help="por defecto, la última wave del fichero")
    p.add_argument("--pri", default="P1", choices=["P0", "P1", "P2"])
    p.add_argument("--esf", default="M", choices=["S", "M", "L", "XL"])
    p.add_argument("--goal", default="")
    p.add_argument("--ahora", default="", help="📍 Cómo está ahora")
    p.add_argument("--que", default="", help="🎯 Qué queremos conseguir")
    p.add_argument("--como", default="", help="🔧 Cómo se haría")
    p.add_argument("--porque", default="", help="🧭 Por qué así y no de otra manera")
    p.add_argument("--aviso", default="")
    p.add_argument("--rec", default="duda — pendiente de escribir el porqué")
    p.add_argument("--nocturno", default="")
    a = p.parse_args()

    tasks = pathlib.Path(a.plan) / "tasks.md"
    if not tasks.exists():
        print(f"✗ no existe {tasks}", file=sys.stderr)
        return 1

    s = tasks.read_text(encoding="utf-8")
    wave = a.wave or ultima_wave(s)
    if f"## {wave}" not in s:
        s = s.rstrip() + f"\n\n## {wave}\n"
    ident = siguiente_id(s, prefijo_de(s, wave))

    P = "  (PENDIENTE de escribir — no lo dejes así)"
    item = [
        f"\n- [ ] `{ident}` [{a.pri}/{a.esf}] {a.titulo}",
        f"  goal: {a.goal or 'PENDIENTE: cómo sabremos que está hecho'}",
        f"  desc: 📍 Cómo está ahora — {a.ahora or P}",
        "",
        f"  🎯 Qué queremos conseguir — {a.que or P}",
        "",
        f"  🔧 Cómo se haría — {a.como or P}",
        "",
        f"  🧭 Por qué así y no de otra manera — {a.porque or P}",
    ]
    if a.aviso:
        item += ["", f"  ⚠️ AVISO — {a.aviso}"]
    item += [f"  rec: {a.rec}"]
    if a.nocturno:
        item += [f"  nocturno: {a.nocturno}"]

    # Se inserta al final de su wave, no al final del fichero
    bloque = "\n".join(item) + "\n"
    if a.wave and f"## {wave}" in s:
        cabeceras = [m.start() for m in re.finditer(r"^## ", s, re.M)]
        i = s.index(f"## {wave}")
        fin = next((c for c in cabeceras if c > i), len(s))
        s = s[:fin].rstrip() + "\n" + bloque + "\n" + s[fin:]
    else:
        s = s.rstrip() + "\n" + bloque

    tasks.write_text(s, encoding="utf-8")
    print(f"  ✓ {ident} apuntado en «{wave}» de {tasks}")
    if not (a.ahora and a.como and a.porque):
        print("  ⚠ quedan bloques PENDIENTE: un item sin porqué no se puede decidir")
    print("  ahora regenera:  python3 .claude/templates/report_kit/tasks_to_items.py "
          f"{a.plan} --profile diseño  &&  python3 .claude/templates/report_kit/build.py {a.plan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
