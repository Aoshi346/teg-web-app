#!/usr/bin/env python3
"""Caracteres invisibles en lo que el agente va a LEER.

EL RIESGO. Un fichero puede llevar instrucciones que el humano no ve y el modelo sí:
espacios de ancho cero, marcas de dirección bidireccional, aisladores. Es el vector
de `rules/agent-security.md` §6 -- todo lo que el agente lee es contexto ejecutable --
y nos aplica de lleno porque vendorizamos repos ajenos en `resources/` y `.docs/`.

POR QUE UN SCRIPT Y NO EL GREP DE LA RULE. Hasta hoy §5 mandaba un `rg -nP` a mano.
Una comprobacion que depende de que alguien se acuerde no es una comprobacion
(`rules/layer-decision.md` pregunta 1). Portado de la unica pieza donde
`everything-claude-code` tenia mecanismo y nosotros prosa
(`scripts/ci/check-unicode-safety.js`), que ademas cubre DOS RANGOS que la receta
manual omitia: los aisladores 0x2066-0x2069 y los selectores de variacion.

QUE NO ES. No detecta ofuscacion (base64, homoglifos, texto en una imagen) ni
instrucciones escritas en claro. Caza lo invisible, que es una franja estrecha y
concreta: `agent-security.md` §10 ya declara que los patrones no son muros.

USO:
    python3 .claude/scripts/check_unicode_safety.py [ruta...]     # por defecto: resources/ y .docs/resources/
    python3 .claude/scripts/check_unicode_safety.py --all         # todo el repo
    python3 .claude/scripts/check_unicode_safety.py --json
Sale con 1 si encuentra algo.
"""
import argparse, json, sys, unicodedata
from pathlib import Path

# Rangos peligrosos. Los cuatro primeros venian del grep de la rule; los dos ultimos
# los aporta la referencia y son los que faltaban.
RANGOS = [
    (0x200B, 0x200D, "espacio de ancho cero"),
    (0x2060, 0x2060, "word joiner"),
    (0xFEFF, 0xFEFF, "BOM / espacio sin ruptura de ancho cero"),
    (0x202A, 0x202E, "marca bidireccional (override)"),
    (0x2066, 0x2069, "aislador bidireccional"),      # <- no estaba en la receta manual
]
# LOS SELECTORES DE VARIACION VAN APARTE, y es la regla de inversion en accion
# (`patterns/README.md` §2). La referencia los mete en el mismo saco; aqui, con nuestro
# corpus, eso da 4.670 hallazgos -- casi todos U+FE0F detras de un emoji, que es su uso
# normal en markdown. Una regla que marca 4.670 sitios legitimos no se activa: se acota.
# Quedan disponibles con --paranoid para auditar material recien vendorizado.
RANGOS_PARANOID = [
    (0xFE00, 0xFE0F, "selector de variacion"),
    (0xE0100, 0xE01EF, "selector de variacion suplementario"),
]
# El BOM al principio de un fichero es normal y no es un ataque: se exime SOLO ahi.
SALTAR_DIR = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
              ".mypy_cache", ".pytest_cache", "staticfiles", ".next", "coverage"}
EXT = {".md", ".txt", ".py", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".json", ".yaml",
       ".yml", ".sh", ".toml", ".html", ".cfg", ".ini", ".env", ".example"}
POR_DEFECTO = ["resources", ".docs/resources"]


def peligroso(cp: int, paranoid: bool = False):
    for a, b, nombre in (RANGOS + RANGOS_PARANOID if paranoid else RANGOS):
        if a <= cp <= b:
            return nombre
    return None


def revisa(f: Path, raiz: Path, hallazgos: list, paranoid: bool = False) -> None:
    try:
        src = f.read_text(encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        return
    for n_linea, linea in enumerate(src.splitlines(), 1):
        for col, ch in enumerate(linea, 1):
            cp = ord(ch)
            nombre = peligroso(cp, paranoid)
            if not nombre:
                continue
            if cp == 0xFEFF and n_linea == 1 and col == 1:
                continue                      # BOM inicial: legitimo
            try:
                oficial = unicodedata.name(ch)
            except ValueError:
                oficial = "?"
            hallazgos.append({
                "file": str(f.relative_to(raiz)), "line": n_linea, "col": col,
                "codepoint": f"U+{cp:04X}", "que": nombre, "unicode": oficial,
                "contexto": linea[max(0, col - 30):col + 30].replace(ch, "␦"),
            })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rutas", nargs="*")
    ap.add_argument("--all", action="store_true", help="todo el repo, no solo lo vendorizado")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--paranoid", action="store_true",
                    help="incluye selectores de variacion: ruidoso, para material recien vendorizado")
    a = ap.parse_args()

    raiz = Path(__file__).resolve().parents[2]
    objetivos = [Path(r) for r in a.rutas] or (
        [raiz] if a.all else [raiz / d for d in POR_DEFECTO])
    objetivos = [o if o.is_absolute() else (raiz / o) for o in objetivos if (
        o if o.is_absolute() else (raiz / o)).exists()]
    if not objetivos:
        print("nada que revisar (¿existe resources/?)", file=sys.stderr)
        return 0

    hallazgos, n_ficheros = [], 0
    for base in objetivos:
        for f in ([base] if base.is_file() else base.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in EXT:
                continue
            if any(p in SALTAR_DIR for p in f.parts):
                continue
            n_ficheros += 1
            revisa(f, raiz, hallazgos, a.paranoid)

    if a.json:
        print(json.dumps(hallazgos, ensure_ascii=False, indent=2))
        return 1 if hallazgos else 0

    ambito = ", ".join(str(o.relative_to(raiz)) if o != raiz else "." for o in objetivos)
    if not hallazgos:
        print(f"✓ sin caracteres invisibles · {n_ficheros} ficheros revisados en {ambito}")
        return 0
    print(f"⚠ {len(hallazgos)} carácter(es) invisible(s) en {n_ficheros} ficheros ({ambito})\n")
    for h in hallazgos[:40]:
        print(f"  {h['file']}:{h['line']}:{h['col']}  {h['codepoint']} — {h['que']}")
        print(f"      …{h['contexto']}…")
    if len(hallazgos) > 40:
        print(f"  … y {len(hallazgos) - 40} más (--json para verlos todos)")
    print("\nUn carácter invisible en un fichero que el agente LEE puede ser una instrucción")
    print("que tú no ves (agent-security.md §6). Míralo antes de usar ese material.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
