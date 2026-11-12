#!/usr/bin/env python3
"""medir_catalogo.py — rellena el `catalog.yaml` de un proyecto MIDIENDO su código, no declarándolo.

Por qué existe
--------------
`sembrar_v0.py` deja el catálogo de un proyecto en `patterns: []` con la nota «se mide cuando haya
código», y no había nada que lo midiera después. aiatech-web y aquila-erp llevaban semanas con
código y con el catálogo vacío (2026-10-03): Rita no tenía reglas que citar y el gate de patrones,
aunque se instalara, no tenía nada que vigilar.

Qué hace (el protocolo de `patterns/stack/_catalog-entries-*.yaml` §3, para un repo CON código)
  a. Siembra las reglas de casa de cada capa que el proyecto tiene (backend Django, frontend React).
  b. Mide: corre el comprobador de la capa sobre el código DEL PROYECTO (nunca sobre `.claude/`).
  c. Escribe por regla cuántas veces se incumple y en cuántos ficheros, y una PROPUESTA de estado.

Qué NO hace, a propósito
  · No promueve nada. Toda regla queda en `sombra`: pasar a `activo` lo firma un humano
    (`rules/refactor-progresivo.md` §4.5). La `propuesta:` es eso, una propuesta.
  · No congela baseline: eso es `pattern_baseline.py freeze`, que ya existe.

Los tres desenlaces (`rules/verification.md`): 0 medido · 1 medido y nada que medir (sin código de
ninguna capa) · 2 NO se pudo medir (comprobador roto, JSON ilegible, proyecto sin .claude).

Uso:
    python3 medir_catalogo.py <proyecto>              # informe, sin escribir
    python3 medir_catalogo.py <proyecto> --escribir   # escribe <proyecto>/.claude/patterns/catalog.yaml
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

TPL = Path(os.environ.get("TL_TEMPLATE_DIR") or Path(__file__).resolve().parents[2])
SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".claude",
        ".mypy_cache", ".pytest_cache", "migrations", "coverage"}

# Regla de inversión del README de patterns: si una regla marcaría medio repo, la mala es la regla.
MINORIA_FICHEROS = 0.15
MINORIA_SITIOS = 25


# Reglas que solo tienen sentido si el proyecto usa cierta librería. Con 0 incumplimientos y sin la
# librería, «0» no significa «se cumple»: significa «no hay nada que mirar». Antes ambas cosas salían
# como «activo — 0 incumplimientos», y en aiatech-web (Astro con islas, sin react-query, zod,
# react-router ni MSW) 25 de 38 reglas se proponían para activar sin aplicar (2026-10-03).
REQUIERE = {
    "fe-mutacion-invalida-cache": ("@tanstack/react-query",), "fe-servidor-fuera-del-store": ("@tanstack/react-query",),
    "fe-sin-fetch-en-useeffect": ("@tanstack/react-query",), "fe-tres-estados": ("@tanstack/react-query",),
    "fe-estado-vacio": ("@tanstack/react-query",),
    "fe-store-sin-react": ("zustand", "redux", "@reduxjs/toolkit", "jotai", "valtio"),
    "fe-esquema-unico": ("zod",), "fe-submit-bloqueado": ("react-hook-form",),
    "fe-errores-de-campo-del-backend": ("react-hook-form",),
    "fe-enlace-interno-con-link": ("react-router", "react-router-dom"),
    "fe-error-boundary-de-ruta": ("react-router", "react-router-dom"),
    "fe-rutas-en-un-sitio": ("react-router", "react-router-dom"),
    "fe-red-en-el-boundary": ("msw",),
    "fe-nivel-del-test": ("@testing-library/react", "vitest", "jest"),
    "fe-consulta-por-rol": ("@testing-library/react",), "fe-sin-snapshot-de-componente": ("vitest", "jest"),
    "fe-sin-espera-por-tiempo": ("@testing-library/react",),
    "fe-target-size-habilitado": ("axe-core", "@axe-core/playwright", "jest-axe", "vitest-axe"),
    "fe-iconos-tree-shakeable": ("lucide-react",),
    "fe-escala-de-tailwind": ("tailwindcss",), "fe-apply-con-reference": ("tailwindcss",),
    "be-celery-delay-en-transaccion": ("celery",), "be-celery-serializer-json": ("celery",),
    "be-celery-timeouts": ("celery",), "be-celery-retry-io": ("celery",), "be-celery-ackslate-idempotente": ("celery",),
    "be-cache-ttl-infinito": ("django-redis", "redis"), "be-cache-key-prefix": ("django-redis", "redis"),
    "be-cache-key-helper": ("django-redis", "redis"), "be-cache-sin-invalidacion": ("django-redis", "redis"),
    "be-mq-dlx": ("pika", "kombu", "aio-pika"),
}


def dependencias(capa: str, raiz: Path) -> set[str]:
    """Las librerías que el proyecto DECLARA (package.json o requirements*/pyproject), en minúsculas."""
    deps: set[str] = set()
    if capa == "frontend":
        try:
            pkg = json.loads((raiz.parent / "package.json").read_text(encoding="utf-8"))
            deps |= {k.lower() for k in {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}}
        except (OSError, json.JSONDecodeError):
            pass
    else:
        import re
        for f in list(raiz.glob("requirements*.txt")) + list(raiz.glob("pyproject.toml")):
            for linea in f.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"\s*\"?([A-Za-z0-9_.\-]+)", linea)
                if m and not linea.strip().startswith(("#", "[")):
                    deps.add(m.group(1).lower())
    return deps


def ficheros(raiz: Path, exts: tuple[str, ...]) -> list[Path]:
    out = []
    for d, dirs, fs in os.walk(raiz):
        dirs[:] = [x for x in dirs if x not in SKIP]
        out += [Path(d) / f for f in fs if f.endswith(exts)]
    return out


def detectar_capas(proy: Path) -> dict[str, Path]:
    """Dónde está el código de cada capa. Se MIRA el disco, no se supone por el nombre."""
    capas: dict[str, Path] = {}
    for d, dirs, fs in os.walk(proy):
        dirs[:] = [x for x in dirs if x not in SKIP]
        if "manage.py" in fs and "backend" not in capas:
            capas["backend"] = Path(d)
        if "package.json" in fs and "frontend" not in capas:
            try:
                pkg = json.loads((Path(d) / "package.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "react" in deps and (Path(d) / "src").is_dir():
                capas["frontend"] = Path(d) / "src"
    return capas


def medir(proy: Path, capa: str, raiz: Path) -> list[dict]:
    chk = proy / ".claude" / "patterns" / "stack" / f"pattern_check_{capa}.py"
    if not chk.exists():
        raise RuntimeError(f"falta {chk.relative_to(proy)}")
    cmd = [sys.executable, str(chk), "--json"] + (["--all", str(raiz)] if capa == "frontend" else [str(raiz)])
    r = subprocess.run(cmd, cwd=proy, capture_output=True, text=True, timeout=600)
    try:
        d = json.loads(r.stdout or "null")
    except json.JSONDecodeError:
        raise RuntimeError(f"{chk.name} no devolvió JSON (exit {r.returncode}): {r.stderr.strip()[:200]}")
    if d is None:
        raise RuntimeError(f"{chk.name} no devolvió nada (exit {r.returncode}): {r.stderr.strip()[:200]}")
    h = d if isinstance(d, list) else d.get("hallazgos", d.get("findings", []))
    # Solo el código del proyecto: un hallazgo dentro del harness es ruido del barrido
    # («677 de 813 ficheros no eran nuestros», verification.md).
    # Los dos comprobadores no hablan igual: backend da `rule`/`path`, frontend `id`/`file`. Se
    # normaliza aquí; sin esto cada hallazgo del frontend caía en la regla «?» y TODAS sus reglas
    # salían con 0 incumplimientos y propuesta «activo» (visto al medir aquila-erp, 2026-10-03).
    norm = [{"rule": x.get("rule") or x.get("id") or x.get("regla"),
             "path": x.get("path") or x.get("file"), "line": x.get("line")} for x in h]
    if any(not x["rule"] or not x["path"] for x in norm):
        raise RuntimeError(f"{chk.name}: hallazgos sin regla o sin fichero — formato desconocido")
    return [x for x in norm if not str(x["path"]).startswith(".claude/")]


def propuesta(n: int, f: int, total: int) -> str:
    if n == 0:
        return "activo — 0 incumplimientos (o aún no hay código en su ámbito): nada que congelar"
    if total and f / total <= MINORIA_FICHEROS and n <= MINORIA_SITIOS:
        return f"activo tras congelar baseline — minoría ({n} sitios en {f} de {total} ficheros)"
    return (f"debil — marcaría {f} de {total} ficheros ({n} sitios): por la regla de inversión, "
            "antes de exigirla hay que preguntarse si la mala es la regla")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    proy = Path(args[0]).resolve()
    cat = proy / ".claude" / "patterns" / "catalog.yaml"
    if not (proy / ".claude").is_dir():
        print(f"✗ {proy} no tiene .claude/: no es un proyecto con el harness", file=sys.stderr)
        return 2
    capas = detectar_capas(proy)
    if not capas:
        print(f"{proy.name}: ni backend Django (manage.py) ni frontend React (package.json + src/): nada que medir")
        return 1

    filas, resumen = [], []
    for capa, raiz in capas.items():
        entradas = TPL / ".claude" / "patterns" / "stack" / f"_catalog-entries-{capa}.yaml"
        if not entradas.exists():
            print(f"✗ no encuentro {entradas}", file=sys.stderr)
            return 2
        reglas = yaml.safe_load(entradas.read_text(encoding="utf-8")).get("patterns", [])
        try:
            hall = medir(proy, capa, raiz)
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            print(f"✗ NO SE PUDO MEDIR {capa}: {e}", file=sys.stderr)
            return 2
        exts = (".py",) if capa == "backend" else (".ts", ".tsx")
        deps = dependencias(capa, raiz)
        total = len(ficheros(raiz, exts))
        por_regla: dict[str, list[dict]] = {}
        for x in hall:
            por_regla.setdefault(x["rule"], []).append(x)
        conocidas = {r["id"] for r in reglas}
        for r in reglas:
            hs = por_regla.get(r["id"], [])
            fs = {x.get("path") for x in hs}
            fila = {k: v for k, v in r.items() if k not in ("estado", "dominancia", "baseline")}
            fila["capa_medida"] = capa
            fila["dominancia"] = (f"{total - len(fs)}/{total} ficheros cumplen "
                                  f"({100 * (total - len(fs)) // total if total else 100}%) · {len(hs)} sitios")
            fila["estado"] = "sombra"
            libs = REQUIERE.get(r["id"])
            if not hs and libs and not any(l in deps for l in libs):
                fila["propuesta"] = f"no aplica — el proyecto no usa {' / '.join(libs)}: 0 no es «se cumple»"
            else:
                fila["propuesta"] = propuesta(len(hs), len(fs), total)
            if hs:
                fila["ejemplos"] = [f"{x.get('path')}:{x.get('line')}" for x in hs[:3]]
            filas.append(fila)
        huerfanas = sorted(set(por_regla) - conocidas)
        # Una regla que el comprobador aplica y el catálogo de casa no declara no se tira: se mide
        # igual y se marca, para que alguien la declare (o la quite del comprobador).
        for rid in huerfanas:
            hs = por_regla[rid]
            fs = {x["path"] for x in hs}
            filas.append({"id": rid, "capa_medida": capa,
                          "enunciado": "(sin entrada en _catalog-entries-%s.yaml: declararla en el template)" % capa,
                          "dominancia": f"{total - len(fs)}/{total} ficheros cumplen · {len(hs)} sitios",
                          "estado": "sombra", "propuesta": propuesta(len(hs), len(fs), total),
                          "ejemplos": [f"{x['path']}:{x['line']}" for x in hs[:3]]})
        resumen.append((capa, raiz.relative_to(proy), total, len(hall), huerfanas))

    hoy = dt.date.today().isoformat()
    for capa, raiz, total, n, huerf in resumen:
        print(f"{capa:9} {str(raiz):22} {total:4} ficheros · {n:3} incumplimientos"
              + (f" · reglas sin entrada en el catálogo: {', '.join(huerf)}" if huerf else ""))
    activas = [f for f in filas if f["propuesta"].startswith("activo")]
    noaplica = [f for f in filas if f["propuesta"].startswith("no aplica")]
    print(f"{len(filas)} reglas medidas · {len(activas)} con propuesta 'activo' · {len(noaplica)} no aplican"
          " · todas quedan en 'sombra'")

    if "--escribir" in sys.argv:
        # Volver a medir NO deshace una firma. Lo que un humano promovió (`estado` distinto de
        # sombra, con `firmado:`) se conserva tal cual; solo se refrescan las cifras.
        previas = {}
        if cat.exists():
            try:
                previas = {p["id"]: p for p in (yaml.safe_load(cat.read_text(encoding="utf-8")) or {})
                           .get("patterns") or [] if p.get("firmado")}
            except yaml.YAMLError as e:
                print(f"✗ el catalog.yaml actual no se puede leer ({e}): no lo piso", file=sys.stderr)
                return 2
        for f in filas:
            if f["id"] in previas:
                f["estado"] = previas[f["id"]]["estado"]
                f["firmado"] = previas[f["id"]]["firmado"]
        cabecera = []
        if cat.exists():
            for linea in cat.read_text(encoding="utf-8").splitlines():
                if not linea.startswith("#"):
                    break
                cabecera.append(linea)
        cuerpo = {
            "project": proy.name,
            "measured": {"fecha": hoy, "por": "scripts/medir_catalogo.py",
                         "capas": {c: {"raiz": str(r), "ficheros": t, "incumplimientos": n}
                                   for c, r, t, n, _ in resumen}},
            "nota": ("Todas las reglas en 'sombra': promover a 'activo' lo firma un humano "
                     "(rules/refactor-progresivo.md §4.5). 'propuesta' es la recomendación medida."),
            "patterns": filas,
        }
        cat.parent.mkdir(parents=True, exist_ok=True)
        cat.write_text("\n".join(cabecera) + "\n\n"
                       + yaml.safe_dump(cuerpo, allow_unicode=True, sort_keys=False, width=110),
                       encoding="utf-8")
        print(f"✓ {cat.relative_to(proy)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
