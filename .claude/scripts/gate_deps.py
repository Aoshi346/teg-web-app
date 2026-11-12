#!/usr/bin/env python3
"""gate_deps.py — G2: dependencias vulnerables, SBOM y cadena de suministro.

Sub-ola 2.23 de la revisión integral (SE-18, SE-34, SE-38, SE-60). Fuente: `sources/r3-ciberseguridad-harness.md`
§2.3 y §6 (G2). Hermano de G3 (`check_django_seguridad.py`), G4 (`gate_tenant.py`), G5 (`gate_agente_superficie.py`)
y de `gate_campana.py`: un script que sale con código ≠ 0 y que se engancha a `/deploy` y al CI. Un párrafo que
dice «actualiza las dependencias» no cierra nada; la medición, sí.

DOS MITADES, que se pueden pedir por separado con `--solo`:

  vulnerabilidades (SE-18)
    D1  una dependencia con una vulnerabilidad de gravedad ≥ HIGH (CVSS ≥ 7,0) que YA tiene versión arreglada
        → rojo. Lo que no tiene arreglo, o es de gravedad menor, va al informe y no bloquea.
    D2  un manifiesto sin lock (package.json sin lock, pyproject sin poetry.lock/uv.lock…): no hay versión
        concreta que medir y la instalación no es reproducible → rojo.
    D3  el SBOM pedido (`--sbom`) sale vacío o no es CycloneDX → no se pudo medir (2).
    D4  una excepción de `.claude/deps-excepciones.json` sin razón, sin fecha o CADUCADA → rojo (la vulnerabilidad
        vuelve a contar). Una excepción es una deuda con fecha, no un silencio.

  cadena de suministro (SE-34, SE-38, SE-60)
    S1  AVISO: `npx`/`uvx`/`bunx`/`pipx run`/`pnpm dlx` sin versión exacta, o con `@latest`/`@next`/un rango
        (superdesign y el MCP de Playwright se lanzaban así). Con `--estricto` el aviso es rojo.
    S2  una GitHub Action (`uses:`) sin fijar a un SHA de 40 caracteres, o un `uses: docker://` sin
        `@sha256:` → rojo (los `FROM` de un Dockerfile y los `container:` de un workflow NO se miran) (caso tj-actions, CVE-2025-30066: movieron las etiquetas a un commit malicioso).
    S3  un proyecto npm que ejecuta los scripts de instalación de sus dependencias: ni `ignore-scripts=true` en
        `.npmrc`, ni pnpm ≥ 10.26.0 (el 10.0-10.25 se podía saltar con una dependencia git: CVE-2025-69264), ni
        yarn berry con `enableScripts: false` → rojo (lección s1ngularity: un postinstall robó credenciales
        buscando CLIs de IA locales).
    S4  AVISO: `curl … | sh` en un workflow, Dockerfile o script: ejecuta lo que sirva el servidor en ese momento.

MOTOR. `osv-scanner scan source -r` (lee poetry.lock, package-lock, pnpm-lock, uv.lock… de una vez; es el único
de los dos que lee poetry.lock) y, si no está, `pip-audit -r` sobre los `requirements*.txt` (sin severidad en su
salida: ahí todo lo que tiene arreglo bloquea, y el informe lo dice). Hace falta red (consulta osv.dev / PyPI):
sin red, o sin motor, sale 2, nunca un verde. `--osv-json F` analiza una salida ya generada (la usa la autoprueba
y sirve para repetir un análisis sin repetir la consulta).

SBOM. `--sbom FICHERO` escribe CycloneDX 1.5 con osv-scanner (o `pip-audit -f cyclonedx-json`) y comprueba que es
CycloneDX y que no está vacío. Es el artefacto de release que pide el CRA (reporte de vulnerabilidades
explotadas desde el 11-09-2026).

    python3 .claude/scripts/gate_deps.py <proyecto> [--solo vulnerabilidades|cadena] [--sbom F] [--osv BIN]
                [--min-cvss 7.0] [--bloquea-desconocida] [--estricto] [--excepciones F] [--json]
    python3 .claude/scripts/gate_deps.py --autoprueba [--vivo --osv BIN]

SALIDA: 0 bien · 1 hallazgos (o la autoprueba no ve caer un sabotaje) · 2 no se pudo medir (sin proyecto, sin
motor, sin red, salida ilegible, SBOM vacío, manifiestos que ningún motor lee).

LÍMITES (declarados): osv-scanner respeta el `.gitignore` aunque no haya repositorio: lo ignorado no se mide, y el gate
lo dice (NO MEDIDO, salida 2) en vez de dar verde; `--no-ignore` de osv lo evita. pip-audit solo lee
`requirements*.txt`: con otro lockfile en el proyecto, sale 2. Sin motor, cualquier lockfile (npm, poetry, go, cargo…)
sale 2. Con osv-scanner, el SBOM lista todos los paquetes (`--all-packages`); con pip-audit solo si el único fichero es
un requirements, y va sin el bloque `vulnerabilities` de osv (no valida contra CycloneDX 1.5; un SBOM no es un VEX).
Un monorepo mide el lock de la raíz solo si la raíz declara `workspaces` (o hay `pnpm-workspace.yaml`). Un
`pyproject.toml` solo lo cubre un lock (poetry/uv/pdm/Pipfile), no un requirements suelto, y un requirements sin `==`
es rojo (D2). Los ficheros de versiones se reconocen por nombre (`*requirements*.txt`, `requirements/*.txt`, los lock
de npm, Python, Go, Rust, Ruby, PHP, Elixir, Swift, .NET, R…): uno con otro nombre no existe para el gate, y uno que
osv no reconoce (`requirements/prod.txt`) sale NO MEDIDO. `--osv-json` analiza una salida ya hecha y NO comprueba su
cobertura (es para repetir un análisis, no para dar un verde). No sigue enlaces simbólicos (osv tampoco) y no lee
`.yarnrc.yml` ni `.npmrc` de carpetas hermanas. S2 no ve `uses:` dentro de plantillas compuestas fuera de `.github/`.
Los `@latest` que lanza un plugin de nivel usuario desde su propio `.mcp.json` no se ven desde el repo. Mide lo que dicen los lockfiles, no lo que hay instalado en el servidor ni lo que cargan
los plugins de nivel usuario (`~/.claude/plugins`: lo que lance un plugin con `@latest` desde su propio `.mcp.json`
no se ve desde el repo). La gravedad es la que publica la base (CVSS máximo del grupo de alias; si falta, la
etiqueta GHSA); una vulnerabilidad sin ninguna de las dos es «desconocida» y no bloquea salvo `--bloquea-desconocida`
(pip-audit no publica gravedad: ahí bloquea siempre). Un CVE aún no publicado, o publicado hoy y no indexado, no
existe para este gate. «Arreglo disponible» es que la base traiga un evento `fixed` por versión (no por commit);
no comprueba que esa versión sea compatible con el proyecto. S1 lee texto: un `npx` montado dentro de un script
Python, o un fichero `.md` fuera de un bloque de código, no se ve. S3 solo lee el `.npmrc` del propio directorio y de
sus ancestros dentro del proyecto, no `~/.npmrc` ni `npm_config_ignore_scripts` del entorno de CI (si lo
exportas ahí, declara la excepción en el README del proyecto). Con `ignore-scripts=true` los paquetes que
necesitan compilar algo (esbuild, sharp, playwright, husky) exigen un `npm rebuild <paquete>` explícito: es el
precio de la medida. Ningún verde certifica que no haya vulnerabilidades: dice que las conocidas, con arreglo y
de gravedad alta, no están.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

EXCEPCIONES = ".claude/deps-excepciones.json"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build", ".tox", ".mypy_cache",
             "_archive", ".docs", "resources", "vendor", ".next", ".cache", "site-packages", ".worktrees",
             "worktrees", "knowledge"}
LOCKS_NPM = {"package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"}
LOCKS_OTROS = {"mix.lock", "Package.resolved", "packages.config", "pylock.toml", "renv.lock", "conan.lock",
               "build.gradle.lockfile", "Podfile.lock", "Cargo.lock", "Gemfile.lock", "composer.lock", "go.mod", "pubspec.lock", "gradle.lockfile",
               "packages.lock.json", "pom.xml", "Pipfile.lock"}
REQ = re.compile(r"^.*requirements.*\.txt$", re.I)
SIN_LOCK_OTROS = {"build.gradle": "gradle.lockfile", "build.gradle.kts": "gradle.lockfile","Cargo.toml": "Cargo.lock", "Gemfile": "Gemfile.lock", "composer.json": "composer.lock",
                  "Pipfile": "Pipfile.lock"}
LOCKS_PY = {"poetry.lock", "uv.lock", "pdm.lock", "Pipfile.lock"}
ETIQUETA_A_CVSS = {"CRITICAL": 9.0, "HIGH": 7.0, "MODERATE": 5.0, "MEDIUM": 5.0, "LOW": 3.0}
PNPM_MINIMO = (10, 26, 0)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
CODIGOS = ["D1", "D2", "D3", "D4", "S1", "S2", "S3", "S4"]
AVISO = ("Ningún verde certifica que no haya vulnerabilidades: dice que las conocidas, de gravedad alta y con "
         "arreglo, no están. Mide los lockfiles, no lo instalado ni los plugins de nivel usuario.")


@dataclass
class Hallazgo:
    codigo: str
    mensaje: str


@dataclass
class Resultado:
    hallazgos: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    informe: list = field(default_factory=list)
    medido: list = field(default_factory=list)       # lo que de verdad se miró (para no confundir 0 con «nada»)
    no_medido: list = field(default_factory=list)    # razones de un 2

    def h(self, codigo, msg):
        if not any(x.codigo == codigo and x.mensaje == msg for x in self.hallazgos):     # pip-audit repite filas
            self.hallazgos.append(Hallazgo(codigo, msg))

    def a(self, codigo, msg):
        if not any(x.codigo == codigo and x.mensaje == msg for x in self.avisos):
            self.avisos.append(Hallazgo(codigo, msg))


# ── utilidades ───────────────────────────────────────────────────────────────────────────
def _recorre(raiz: Path):
    """Recorre el proyecto saltando carpetas ajenas. Devuelve (dirpath, dirnames, filenames) ya filtrados."""
    for dp, dn, fn in os.walk(raiz):
        dn[:] = sorted(d for d in dn if d not in SKIP_DIRS)
        yield Path(dp), dn, sorted(fn)


def _rel(p: Path, raiz: Path) -> str:
    try:
        return str(p.relative_to(raiz))
    except ValueError:
        return str(p)


def _leer(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _clave(s: str):
    """Lista comparable de una versión: números y palabras, sin truncar (4.17.15.1, 1.0.0-rc.1, 0.0.0-2020…-hash)."""
    toks = re.findall(r"\d+|[A-Za-z]+", s or "")
    return [(1, int(x)) if x.isdigit() else (0, x.lower()) for x in toks] if any(x.isdigit() for x in toks) else None


def _mayor(a: str, b: str) -> bool:
    """¿a es estrictamente posterior a b? Una palabra detrás de la parte numérica común (rc, beta) es ANTERIOR."""
    ka, kb = _clave(a), _clave(b)
    if ka is None or kb is None:
        return True                       # no se puede comparar: se cuenta como arreglo (lo conservador)
    for x, y in zip(ka, kb):
        if x != y:
            return x > y
    if len(ka) == len(kb):
        return False
    largo, a_es_largo = (ka, True) if len(ka) > len(kb) else (kb, False)
    extra = largo[min(len(ka), len(kb))]
    return a_es_largo if extra[0] == 1 else not a_es_largo


def _nombre(s: str) -> str:
    return re.sub(r"[-_.]+", "-", (s or "").lower())


# ── motor: osv-scanner / pip-audit ───────────────────────────────────────────────────────
def buscar_binario(nombre: str, explicito: str | None, entorno: str) -> str | None:
    for c in (explicito, os.environ.get(entorno)):
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return str(c)
    return shutil.which(nombre)


def corre_osv(proy: Path, osv: str) -> dict:
    """Ejecuta osv-scanner y devuelve su JSON. Lanza RuntimeError si no se pudo medir.
    Códigos de osv-scanner: 0 limpio · 1 con vulnerabilidades · 128 sin paquetes · otro, fallo."""
    with tempfile.TemporaryDirectory(prefix="gate-deps-") as td:
        out = Path(td) / "osv.json"
        r = subprocess.run([osv, "scan", "source", "-r", "--all-packages", "--format", "json", "--output-file", str(out), str(proy)],
                           capture_output=True, text=True, timeout=600)
        if r.returncode == 128:
            return {"results": []}
        if r.returncode not in (0, 1):
            raise RuntimeError(f"osv-scanner terminó con código {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}")
        try:
            return json.loads(out.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise RuntimeError(f"la salida de osv-scanner no se pudo leer ({e})")


def corre_pip_audit(proy: Path, pa: str) -> dict:
    """pip-audit sobre cada requirements*.txt; lo normaliza al formato de osv-scanner (sin severidad)."""
    resultados, saltados = [], []
    for dp, _dn, fn in _recorre(proy):
        for f in fn:
            if re.match(r"^requirements.*\.txt$", f):
                r = subprocess.run([pa, "-r", str(dp / f), "--no-deps", "--disable-pip", "--format", "json",
                                    "--progress-spinner", "off"], capture_output=True, text=True, timeout=600)
                if r.returncode not in (0, 1):
                    raise RuntimeError(f"pip-audit terminó con código {r.returncode} en {f}: "
                                       f"{(r.stderr or r.stdout).strip()[-300:]}")
                try:
                    d = json.loads(r.stdout)
                except ValueError as e:
                    raise RuntimeError(f"la salida de pip-audit no se pudo leer ({e})")
                pk = []
                for dep in d.get("dependencies", []):
                    if dep.get("skip_reason"):
                        saltados.append(f"{dep.get('name')} ({dep['skip_reason']})")
                    vs = dep.get("vulns") or []
                    if not vs:
                        continue
                    vulns, grupos = [], []
                    for v in vs:
                        ev = [{"fixed": x} for x in v.get("fix_versions", [])]
                        vulns.append({"id": v["id"], "aliases": v.get("aliases", []),
                                      "affected": [{"package": {"name": dep["name"]},
                                                    "ranges": [{"type": "ECOSYSTEM", "events": ev}] if ev else []}]})
                        grupos.append({"ids": [v["id"]], "aliases": v.get("aliases", []), "max_severity": ""})
                    pk.append({"package": {"name": dep["name"], "version": dep.get("version", ""), "ecosystem": "PyPI"},
                               "vulnerabilities": vulns, "groups": grupos})
                resultados.append({"source": {"path": str(dp / f), "type": "lockfile"}, "packages": pk})
    return {"results": resultados, "_motor": "pip-audit", "_saltados": saltados}


def escribe_sbom(proy: Path, destino: Path, osv: str | None, pa: str | None) -> None:
    """Genera el SBOM CycloneDX. Lanza RuntimeError si no se pudo."""
    if osv:
        r = subprocess.run([osv, "scan", "source", "-r", "--all-packages", "--format", "cyclonedx-1-5", "--output-file", str(destino),
                            str(proy)], capture_output=True, text=True, timeout=600)
        if r.returncode not in (0, 1):
            raise RuntimeError(f"osv-scanner no generó el SBOM (código {r.returncode}): {(r.stderr or '').strip()[-300:]}")
        try:                       # el bloque `vulnerabilities` de osv no valida contra CycloneDX 1.5; un SBOM no es un VEX
            d = json.loads(destino.read_text(encoding="utf-8"))
            d.pop("vulnerabilities", None)
            destino.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
        except (OSError, ValueError) as e:
            raise RuntimeError(f"el SBOM de osv-scanner no se pudo leer para limpiarlo ({e})")
    elif pa:
        todos = ficheros_de_deps(proy)
        reqs = [f for f in todos if re.match(r"^requirements.*\.txt$", f.name)]
        if len(reqs) != 1 or len(todos) != 1:
            raise RuntimeError("sin osv-scanner, el SBOM solo se puede sacar de un proyecto cuyo único fichero de "
                               "dependencias es UN requirements*.txt (pip-audit no junta ficheros ni lee otros lockfiles)")
        r = subprocess.run([pa, "-r", str(reqs[0]), "--no-deps", "--disable-pip", "--format", "cyclonedx-json",
                            "--output", str(destino), "--progress-spinner", "off"], capture_output=True, text=True,
                           timeout=600)
        if r.returncode not in (0, 1):
            raise RuntimeError(f"pip-audit no generó el SBOM (código {r.returncode}): {(r.stderr or '').strip()[-300:]}")
    else:
        raise RuntimeError("sin osv-scanner ni pip-audit no se puede generar el SBOM")


def valida_sbom(p: Path) -> str | None:
    """None si el SBOM es CycloneDX y no está vacío; si no, el motivo."""
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return f"no se pudo leer ({e})"
    if not isinstance(d, dict) or d.get("bomFormat") != "CycloneDX":
        return "no es CycloneDX (falta bomFormat)"
    comp = d.get("components")
    if not isinstance(comp, list) or not comp:
        return "no lista ningún componente"
    return None


# ── análisis de la salida de osv ─────────────────────────────────────────────────────────
def _cvss(grupo: dict, vulns: list):
    """(número|None, de dónde). max_severity del grupo; si falta, la etiqueta GHSA de alguna vuln del grupo."""
    ms = grupo.get("max_severity")
    try:
        if ms not in (None, ""):
            f = float(ms)
            if math.isfinite(f):
                return f, "CVSS"
    except (TypeError, ValueError):
        if str(ms).upper() in ETIQUETA_A_CVSS:
            return ETIQUETA_A_CVSS[str(ms).upper()], "etiqueta"
    mejor = None
    for v in vulns:
        eti = str((v.get("database_specific") or {}).get("severity", "")).upper()
        if eti in ETIQUETA_A_CVSS:
            mejor = max(mejor or 0, ETIQUETA_A_CVSS[eti])
    return (mejor, "etiqueta") if mejor is not None else (None, "")


def _arreglos(vulns: list, paquete: str, version: str) -> list:
    """Versiones arregladas (eventos `fixed` de rangos por versión, no por commit) aplicables a `version`."""
    todas = []
    for v in vulns:
        for af in v.get("affected", []):
            nom = (af.get("package") or {}).get("name", "")
            if nom and _nombre(nom) != _nombre(paquete):
                continue
            for rg in af.get("ranges", []):
                if rg.get("type") not in ("ECOSYSTEM", "SEMVER"):
                    continue
                for ev in rg.get("events", []):
                    if isinstance(ev, dict) and ev.get("fixed"):
                        todas.append(str(ev["fixed"]))
    todas = [f for f in todas if _mayor(f, version)]
    return sorted(set(todas), key=lambda x: (_clave(x) or [(0, x)], x))


def lee_excepciones(proy: Path, fichero: str | None, hoy: datetime.date, res: Resultado) -> list:
    p = Path(fichero) if fichero else proy / EXCEPCIONES
    if not p.is_file():
        return []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        res.h("D4", f"{_rel(p, proy)} no es JSON válido ({e}): las excepciones no se aplican")
        return []
    vigentes = []
    lista = d.get("excepciones") if isinstance(d, dict) else None
    if not isinstance(lista, list):
        res.h("D4", f"{_rel(p, proy)}: falta la lista `excepciones`")
        return []
    for i, e in enumerate(lista):
        if not isinstance(e, dict) or not str(e.get("id", "")).strip():
            res.h("D4", f"{_rel(p, proy)}: la excepción nº {i + 1} no tiene `id`")
            continue
        if not str(e.get("razon", "")).strip():
            res.h("D4", f"excepción {e['id']}: sin `razon` (qué la hace aceptable y quién la decidió)")
            continue
        try:
            cad = datetime.date.fromisoformat(str(e.get("caduca", ""))[:10])
        except ValueError:
            res.h("D4", f"excepción {e['id']}: `caduca` falta o no es una fecha ISO (AAAA-MM-DD)")
            continue
        if cad > hoy + datetime.timedelta(days=400):
            res.h("D4", f"excepción {e['id']}: caduca el {cad.isoformat()}, a más de 400 días: una excepción es una deuda con "
                        f"fecha, no un silencio")
            continue
        if cad < hoy:
            res.h("D4", f"excepción {e['id']}: CADUCADA el {cad.isoformat()}; la vulnerabilidad vuelve a contar")
            continue
        vigentes.append(e)
    return vigentes


def analiza_osv(data: dict, res: Resultado, min_cvss: float, bloquea_desconocida: bool, excepciones: list,
                pip_audit: bool = False) -> int:
    """Rellena `res` con lo que dice la salida de osv. Devuelve cuántos paquetes con vulnerabilidades vio."""
    bloquea_desconocida = bloquea_desconocida or pip_audit
    ex_ids = {}
    for e in excepciones:
        ex_ids.setdefault(str(e["id"]).upper(), []).append(_nombre(str(e.get("paquete", ""))))
    paquetes = 0
    for r in data.get("results", []):
        if not isinstance(r, dict):
            raise ValueError("un elemento de `results` no es un objeto")
        for p in r.get("packages", []) or []:
            if not isinstance(p, dict):
                raise ValueError("un elemento de `packages` no es un objeto")
            pk = p.get("package", {})
            nombre, version, eco = pk.get("name", "?"), pk.get("version", "?"), pk.get("ecosystem", "?")
            vulns = {v.get("id"): v for v in p.get("vulnerabilities", []) if isinstance(v, dict)}
            if vulns:
                paquetes += 1
            cubiertos = {i for g in (p.get("groups") or []) if isinstance(g, dict) for i in g.get("ids", [])}
            grupos = [g for g in (p.get("groups") or []) if isinstance(g, dict)]
            for vid, v in vulns.items():              # vulnerabilidad que ningún grupo menciona: no se puede perder
                if vid not in cubiertos:
                    grupos.append({"ids": [vid], "aliases": v.get("aliases", []), "max_severity": "", "_implicito": True})
            for g in grupos:
                ids = [i for i in g.get("ids", []) if i in vulns] or list(g.get("ids", []))
                vs = [vulns[i] for i in ids if i in vulns]
                alias = {str(x).upper() for x in g.get("aliases", [])} | {str(i).upper() for i in ids}
                cv, origen = _cvss(g, vs)
                fix = _arreglos(vs, nombre, version)
                etiqueta = f"{nombre} {version} ({eco}): {ids[0] if ids else '?'}"
                if cv is not None:
                    etiqueta += f" · gravedad {cv:g} ({origen})"
                else:
                    etiqueta += " · gravedad desconocida"
                etiqueta += f" · arreglo: {', '.join(fix[:3])}" if fix else " · sin arreglo publicado"
                excusa = [a for a in alias if a in ex_ids and (not any(ex_ids[a]) or _nombre(nombre) in ex_ids[a])]
                alta = cv is not None and cv >= min_cvss
                desconocida = cv is None
                if g.get("_implicito"):           # salida malformada: lo que no se puede graduar se trata como grave
                    desconocida = True
                    etiqueta += " · sin grupo en la salida del motor"
                if (alta or (desconocida and (bloquea_desconocida or g.get("_implicito")))) and fix:
                    if excusa:
                        res.informe.append(f"EXCEPCIÓN vigente ({excusa[0]}): {etiqueta}")
                    else:
                        res.h("D1", etiqueta)
                elif etiqueta not in res.informe:
                    res.informe.append(etiqueta)
    return paquetes


# ── manifiestos sin lock (D2) ────────────────────────────────────────────────────────────
def _pyproject_tiene_deps(txt: str) -> bool:
    for m in re.finditer(r"^\[tool\.poetry\.(?:dependencies|(?:dev-dependencies)|group\.[\w-]+\.dependencies)\]\s*\n"
                         r"((?:[^\[\n].*\n?)*)", txt, re.M):
        # poetry siempre trae `python = ...`: solo cuenta si hay algo más
        if any(not l.strip().startswith("python") and "=" in l for l in m.group(1).splitlines()
               if l.strip() and not l.strip().startswith("#")):
            return True
    for m in re.finditer(r"^(?:dependencies|\w[\w-]*)\s*=\s*\[(.*?)\]", txt, re.M | re.S):
        if re.search(r"[\"'][A-Za-z]", m.group(1)) and "[project" in txt:
            return True
    return False


def _deps_npm(pj) -> dict:
    if not isinstance(pj, dict):
        return {}
    out = {}
    for k in ("dependencies", "devDependencies", "optionalDependencies"):
        if isinstance(pj.get(k), dict):
            out.update(pj[k])
    return out


def _workspaces(d: Path) -> bool:
    try:
        pj = json.loads(_leer(d / "package.json") or "{}")
    except ValueError:
        return False
    return isinstance(pj, dict) and bool(pj.get("workspaces"))


def _lock_en_padre(d: Path, raiz: Path) -> bool:
    """Monorepo: el lockfile de npm/pnpm/yarn de los workspaces vive en la raíz, no en cada paquete."""
    cur = d
    while cur != raiz and raiz in cur.parents:
        cur = cur.parent
        if any((cur / l).exists() for l in LOCKS_NPM) and (
                (cur / "pnpm-workspace.yaml").exists() or _workspaces(cur)):
            return True
    return False


def ficheros_de_deps(proy: Path) -> list:
    """Los ficheros cuyo contenido son versiones concretas de dependencias (los que un motor tiene que leer)."""
    out = []
    for dp, _dn, fn in _recorre(proy):
        for f in fn:
            if (f in LOCKS_NPM or f in LOCKS_PY or f in LOCKS_OTROS or REQ.match(f)
                    or (dp.name.lower() in ("requirements", "reqs") and f.endswith(".txt"))):
                out.append(dp / f)
    return out


def cobertura(ficheros: list, data: dict, motor: str, res: Resultado) -> None:
    """Anota como NO MEDIDO lo que el motor no leyó: un verde sobre la mitad del proyecto es un verde falso."""
    if motor == "pip-audit":
        for f in ficheros:
            if not re.match(r"^requirements.*\.txt$", f.name):
                res.no_medido.append(f"pip-audit solo lee requirements*.txt: no mide {f.name} ({f.parent.name or '.'}); "
                                     f"usa osv-scanner")
            elif re.search(r"^\s*(?:-r|-c|--requirement|--constraint)\b", _leer(f), re.M):
                res.no_medido.append(f"{f.name} incluye otro fichero con -r/-c y pip-audit no lo sigue: usa osv-scanner")
        for s in data.get("_saltados", []):
            res.no_medido.append(f"pip-audit se saltó {s}: no lo midió")
        return
    leidos = set()
    for r in data.get("results", []):
        src = (r or {}).get("source") if isinstance(r, dict) else None
        if isinstance(src, dict) and src.get("path"):
            leidos.add(str(Path(src["path"]).resolve()))
    for f in ficheros:
        if str(f.resolve()) not in leidos:
            res.no_medido.append(f"el motor no leyó {f} (¿está en un .gitignore, que osv respeta aunque no haya "
                                 f"repositorio? ¿está vacío o ilegible? ¿osv no lo reconoce, como requirements/prod.txt?): "
                                 f"lo que contiene no se ha medido")


def manifiestos(proy: Path, res: Resultado) -> int:
    """Devuelve cuántos manifiestos con dependencias hay; anota D2 donde falta el lock."""
    n = 0
    for dp, _dn, fn in _recorre(proy):
        nombres = set(fn)
        if "package.json" in nombres:
            try:
                pj = json.loads(_leer(dp / "package.json") or "{}")
            except ValueError:
                pj = {}
            deps = _deps_npm(pj)
            if deps:
                n += 1
                if not (nombres & LOCKS_NPM) and not _lock_en_padre(dp, proy):
                    res.h("D2", f"{_rel(dp / 'package.json', proy)}: tiene dependencias y ningún lockfile "
                                f"(package-lock.json, pnpm-lock.yaml, yarn.lock…): sin él no hay versión que medir")
        if "pyproject.toml" in nombres:
            txt = _leer(dp / "pyproject.toml")
            if _pyproject_tiene_deps(txt):
                n += 1
                if not (nombres & LOCKS_PY):
                    res.h("D2", f"{_rel(dp / 'pyproject.toml', proy)}: declara dependencias y no hay poetry.lock, "
                                f"uv.lock, pdm.lock ni Pipfile.lock (un requirements*.txt suelto no demuestra que sea "
                                f"lo mismo: osv no lee el pyproject)")
        for f in fn:
            if f in SIN_LOCK_OTROS:
                n += 1
                if SIN_LOCK_OTROS[f] not in nombres:
                    res.h("D2", f"{_rel(dp / f, proy)}: declara dependencias y falta {SIN_LOCK_OTROS[f]}")
            if re.match(r"^requirements.*\.txt$", f) or (REQ.match(f) and f.endswith(".txt")):
                n += 1
                sueltas = [l.strip() for l in _leer(dp / f).splitlines()
                           if l.strip() and not l.strip().startswith(("#", "-", "git+", "http"))
                           and not re.search(r"==\s*[\w.]+", l.split(";")[0]) and " @ " not in l]
                if sueltas:
                    res.h("D2", f"{_rel(dp / f, proy)}: {len(sueltas)} dependencia(s) sin `==` (p. ej. «{sueltas[0][:40]}»): "
                                f"no hay una versión que medir; fija con `==` (pip-compile, poetry export, uv pip compile)")
    return n


# ── cadena de suministro ─────────────────────────────────────────────────────────────────
RUNNERS = {"npx", "bunx", "uvx"}
RUNNER_TXT = re.compile(r"(?<![\w./-])(npx|bunx|uvx|pipx\s+run|pnpm\s+dlx|yarn\s+dlx|npm\s+exec)\b((?:\s+(?:-{1,2}[\w-]+(?:=\S+)?))*)\s+[\"']?([^\s\"'`|;&)>]+)")
PIPE_SH = re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:sudo(?:\s+-\S+)*\s+)?(?:ba|z|da)?sh\b|\b(?:ba|z|da)?sh\s+<\(\s*(?:curl|wget)\b")


def _pinned(spec: str) -> bool | None:
    """True si el paquete lleva versión EXACTA; False si no; None si no es un paquete (ruta, URL, flag)."""
    s = spec.strip().strip("\"'")
    if not s or s.startswith(("-", ".", "/", "~", "$", "{", "http", "git+", "file:", "<")) or "://" in s:
        return None
    if re.match(r"^(?:@[\w.-]+/)?[\w.-]+@\d+\.\d+\.\d+(?:[-+][\w.]+)?$", s):
        return True
    if re.match(r"^[\w.\[\]-]+==\d+(?:\.\d+)*(?:[-+.\w]*)?$", s):          # uvx pkg==1.2.3
        return True
    return False


def _s1_json(obj, ruta: str, res: Resultado):
    if isinstance(obj, dict):
        cmd, args = obj.get("command"), obj.get("args")
        if isinstance(cmd, str) and Path(cmd).name in RUNNERS | {"pipx"} and isinstance(args, list):
            a = [str(x) for x in args]
            if Path(cmd).name == "pipx" and a[:1] == ["run"]:
                a = a[1:]
            for x in a:
                if x.startswith("-"):
                    continue
                if _pinned(x) is False:
                    res.a("S1", f"{ruta}: `{cmd} {' '.join(a)}` sin versión exacta ({x}): cada sesión ejecuta lo último "
                                f"que haya publicado el paquete")
                break
        for v in obj.values():
            _s1_json(v, ruta, res)
    elif isinstance(obj, list):
        for v in obj:
            _s1_json(v, ruta, res)


def _s1_texto(txt: str, ruta: str, res: Resultado, solo_bloques: bool):
    dentro = False
    for n, linea in enumerate(txt.splitlines(), 1):
        if solo_bloques:
            if linea.lstrip().startswith("```"):
                dentro = not dentro
                continue
            if not dentro:
                continue
        if linea.lstrip().startswith("#") and not linea.lstrip().startswith("#!"):
            continue
        for m in RUNNER_TXT.finditer(linea):
            gestor = re.sub(r"\s+", " ", m.group(1))
            if gestor == "npm exec" and "--" in m.group(2):
                continue
            if _pinned(m.group(3)) is False:
                # `npx tsc` / `npx vitest` sin `-y` y sin `@`: el binario es el de node_modules/.bin del propio
                # proyecto, no una descarga. Descarga, y por tanto riesgo, cuando hay `-y/--yes`, una `@` (latest,
                # rango) o un gestor que siempre descarga (uvx, bunx, pipx run, pnpm/yarn dlx).
                local = gestor == "npx" and "@" not in m.group(3) and not re.search(r"(?:^|\s)(?:-y|--yes)\b", m.group(2))
                if not local:
                    res.a("S1", f"{ruta}:{n}: `{gestor} {m.group(3)}` sin versión exacta: cada ejecución usa lo último publicado")
        if PIPE_SH.search(linea) and "Bash(" not in linea:      # una regla `deny` que PROHÍBE curl | bash no es el patrón
            res.a("S4", f"{ruta}:{n}: descarga y ejecuta en un paso (`curl … | sh`): ejecuta lo que sirva el servidor ese día")


USES = re.compile(r"(?:^|[\s{,\[-])[\"']?uses[\"']?\s*:\s*[\"']?([^\s\"',}\]]+)", re.M)


def _s2(txt: str, ruta: str, res: Resultado):
    for m in USES.finditer(txt):
        ref = m.group(1).strip().strip("\"'")
        n = txt.count("\n", 0, m.start()) + 1
        if ref.startswith("./") or ref.startswith("${{"):
            continue
        if ref.startswith("docker://"):
            if not re.search(r"@sha256:[0-9a-f]{64}$", ref):
                res.h("S2", f"{ruta}:{n}: `uses: {ref}` sin digest `@sha256:`; una etiqueta de imagen se puede mover")
            continue
        _, _, version = ref.partition("@")
        if not HEX40.match(version.lower()):
            res.h("S2", f"{ruta}:{n}: `uses: {ref}` por etiqueta, no por SHA de commit (40 caracteres hex): "
                        f"una etiqueta se puede reescribir")


def _npmrc_ignora(d: Path, raiz: Path) -> bool | None:
    """True si algún .npmrc, de `d` hacia arriba hasta la raíz del proyecto, fija ignore-scripts=true;
    False si lo fija a false (gana el más cercano); None si no lo dice."""
    cur = d
    while True:
        m = re.findall(r"^\s*ignore-scripts\s*=\s*[\"']?(\w+)", _leer(cur / ".npmrc"), re.M | re.I)
        if m:                                              # npm aplica la ÚLTIMA línea
            return m[-1].lower() in ("true", "1", "yes")
        if cur == raiz or raiz not in cur.parents:
            return None
        cur = cur.parent


def _s3(proy: Path, res: Resultado):
    for dp, _dn, fn in _recorre(proy):
        if "package.json" not in fn:
            continue
        try:
            pj = json.loads(_leer(dp / "package.json") or "{}")
        except ValueError:
            continue
        if not _deps_npm(pj):
            continue
        ruta = _rel(dp / "package.json", proy)
        pm = str(pj.get("packageManager", ""))
        mpm = re.match(r"^(pnpm|yarn|npm|bun)@(\d+)\.(\d+)\.(\d+)", pm)
        npmrc = _npmrc_ignora(dp, proy)
        if npmrc is False:
            res.h("S3", f"{ruta}: `ignore-scripts=false` en .npmrc: los scripts de instalación de las dependencias corren")
            continue
        if npmrc:
            continue
        if mpm and mpm.group(1) == "pnpm":
            v = tuple(int(x) for x in mpm.groups()[1:])
            todo_permitido = (
                (pj.get("pnpm") or {}).get("dangerouslyAllowAllBuilds") is True
                or re.search(r"^dangerouslyAllowAllBuilds:\s*true", _leer(dp / "pnpm-workspace.yaml"), re.M)
                or re.search(r"^\s*dangerously-allow-all-builds\s*=\s*[\"']?true", _leer(dp / ".npmrc"), re.M | re.I))
            if v >= PNPM_MINIMO and todo_permitido:
                res.h("S3", f"{ruta}: pnpm {'.'.join(map(str, v))} con `dangerouslyAllowAllBuilds`: ejecuta los scripts de "
                            f"TODAS las dependencias, como si no hubiera protección")
                continue
            if v >= PNPM_MINIMO:
                continue
            if v[0] >= 10:
                res.h("S3", f"{ruta}: pnpm {'.'.join(map(str, v))} no ejecuta scripts de dependencias por defecto pero se "
                            f"podía saltar con una dependencia git (CVE-2025-69264, corregido en 10.26.0): sube a ≥ 10.26.0")
                continue
        if mpm and mpm.group(1) == "yarn" and (re.findall(r"^enableScripts:\s*(\w+)", _leer(dp / ".yarnrc.yml"), re.M) or ["true"])[-1] == "false":
            continue
        if (pj.get("pnpm") or {}).get("onlyBuiltDependencies") is not None and mpm and mpm.group(1) == "pnpm" \
                and tuple(int(x) for x in mpm.groups()[1:]) >= PNPM_MINIMO:
            continue
        if (mpm and mpm.group(1) == "bun" or (dp / "bun.lock").exists()) and not pj.get("trustedDependencies"):
            continue                                    # bun no ejecuta los scripts de las dependencias salvo las confiadas
        res.h("S3", f"{ruta}: instala dependencias ejecutando sus scripts (sin `ignore-scripts=true` en .npmrc, ni pnpm "
                    f"≥ 10.26.0, ni yarn con `enableScripts: false`): un postinstall malicioso corre con tus credenciales")


def cadena(proy: Path, res: Resultado):
    for dp, _dn, fn in _recorre(proy):
        for f in fn:
            p = dp / f
            ruta = _rel(p, proy)
            en_wf = ".github" in p.parts and ("workflows" in p.parts or "actions" in p.parts)
            if en_wf and re.search(r"\.ya?ml(\.example)?$", f):
                txt = _leer(p)
                _s2(txt, ruta, res)
                _s1_texto(txt, ruta, res, solo_bloques=False)
            elif f in (".mcp.json", "plugin.json") or re.match(r"^settings.*\.json$", f) or f == "package.json":
                try:
                    d = json.loads(_leer(p) or "{}")
                except ValueError:
                    continue
                if f == "package.json":
                    for k, v in (d.get("scripts") or {}).items() if isinstance(d, dict) else []:
                        _s1_texto(str(v), f"{ruta}[scripts.{k}]", res, solo_bloques=False)
                else:
                    _s1_json(d, ruta, res)
            elif f.startswith("Dockerfile") or f.endswith((".sh", "Makefile")) or f == "Makefile":
                _s1_texto(_leer(p), ruta, res, solo_bloques=False)
            elif f.endswith(".md"):
                _s1_texto(_leer(p), ruta, res, solo_bloques=True)
    _s3(proy, res)


# ── ejecución ────────────────────────────────────────────────────────────────────────────
def ejecuta(args) -> tuple[int, Resultado]:
    res = Resultado()
    proy = Path(args.proyecto).resolve() if args.proyecto else None
    if proy is None or not proy.is_dir():
        res.no_medido.append(f"no existe el proyecto «{args.proyecto}»")
        return 2, res
    hoy = datetime.date.fromisoformat(args.hoy) if args.hoy else datetime.date.today()
    hace_vuln = args.solo in (None, "vulnerabilidades")
    hace_cadena = args.solo in (None, "cadena")
    osv = buscar_binario("osv-scanner", args.osv, "GATE_DEPS_OSV")
    pa = buscar_binario("pip-audit", args.pip_audit, "GATE_DEPS_PIP_AUDIT")
    for opcion, ruta, hallado in (("--osv", args.osv, osv), ("--pip-audit", args.pip_audit, pa)):
        if ruta and not (hallado and Path(hallado).resolve() == Path(ruta).resolve()):
            res.no_medido.append(f"{opcion} {ruta}: no existe o no es ejecutable (no se cae en silencio a otro motor)")
    if args.sbom and not hace_vuln:
        res.no_medido.append("--sbom con --solo cadena: el SBOM lo genera la mitad de vulnerabilidades")

    if hace_vuln:
        n_man = manifiestos(proy, res)
        excepciones = lee_excepciones(proy, args.excepciones, hoy, res)
        ficheros = ficheros_de_deps(proy)
        data, motor = None, None
        try:
            if not args.osv_json and not ficheros and not n_man:
                pass                                         # nada que medir: no se arranca ningún motor
            elif args.osv_json:
                data, motor = json.loads(Path(args.osv_json).read_text(encoding="utf-8")), "osv-json"
            elif args.motor in ("auto", "osv") and osv:
                data, motor = corre_osv(proy, osv), "osv-scanner"
            elif args.motor in ("auto", "pip-audit") and pa:
                data, motor = corre_pip_audit(proy, pa), "pip-audit"
            else:
                res.no_medido.append("hay manifiestos y ningún motor (osv-scanner o pip-audit): instálalo o pasa --osv BIN")
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as e:
            res.no_medido.append(f"el motor no pudo medir: {e}")
        if data is not None and not isinstance(data, dict):
            res.no_medido.append("la salida del motor no es un objeto JSON")
            data = None
        if data is not None:
            if not isinstance(data, dict) or not isinstance(data.get("results"), list):
                res.no_medido.append("la salida del motor no tiene la forma esperada (falta `results`)")
            else:
                try:
                    pk = analiza_osv(data, res, args.min_cvss, args.bloquea_desconocida, excepciones,
                                     pip_audit=(data.get("_motor") == "pip-audit"))
                except (ValueError, TypeError, AttributeError, KeyError) as e:
                    res.no_medido.append(f"la salida del motor no tiene la forma esperada ({e})")
                    pk = 0
                if motor != "osv-json":
                    cobertura(ficheros, data, "pip-audit" if data.get("_motor") == "pip-audit" else "osv", res)
                elif ficheros and not data["results"]:
                    res.no_medido.append(f"hay {n_man} manifiesto(s) con dependencias y el motor no leyó ninguno")
                res.medido.append(f"vulnerabilidades: motor {motor}, {len(ficheros)} fichero(s) de versiones esperados, "
                                  f"{pk} paquete(s) con alguna vulnerabilidad, {n_man} manifiesto(s) con dependencias")
        elif not res.no_medido and not n_man and not ficheros:
            res.medido.append("vulnerabilidades: ningún manifiesto con dependencias (nada que medir)")
        if args.sbom:
            dest = Path(args.sbom)
            try:
                if args.osv_json:
                    raise RuntimeError("con --osv-json no hay proyecto que volcar: genera el SBOM sin él")
                escribe_sbom(proy, dest, osv, pa)
                motivo = valida_sbom(dest)
                if motivo:
                    res.no_medido.append(f"D3 el SBOM {dest} {motivo}")
                else:
                    res.medido.append(f"SBOM CycloneDX en {dest} ({len(json.loads(dest.read_text())['components'])} componentes)")
            except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as e:
                res.no_medido.append(f"D3 no se pudo generar el SBOM: {e}")
    if hace_cadena:
        cadena(proy, res)
        res.medido.append("cadena de suministro: S1-S4 sobre workflows, configs MCP, scripts, Dockerfiles, package.json y bloques de código de los .md")
    if args.estricto:
        for a in res.avisos:
            res.h(a.codigo, a.mensaje + " [--estricto]")
        res.avisos = []
    if res.no_medido:
        return 2, res
    return (1 if res.hallazgos else 0), res


def imprime(res: Resultado, rc: int, como_json: bool):
    if como_json:
        print(json.dumps({"salida": rc, "hallazgos": [vars(h) for h in res.hallazgos],
                          "avisos": [vars(h) for h in res.avisos], "informe": res.informe,
                          "medido": res.medido, "no_medido": res.no_medido}, ensure_ascii=False, indent=1))
        return
    for m in res.medido:
        print(f"  medido · {m}")
    for h in res.hallazgos:
        print(f"✗ {h.codigo}  {h.mensaje}")
    for a in res.avisos:
        print(f"⚠ {a.codigo}  {a.mensaje}")
    if res.informe:
        print(f"  informe (no bloquea): {len(res.informe)}")
        for i in res.informe[:15]:
            print(f"    - {i}")
        if len(res.informe) > 15:
            print(f"    … y {len(res.informe) - 15} más (--json las trae todas)")
    for n in res.no_medido:
        print(f"? NO MEDIDO  {n}")
    veredicto = {0: "✓ G2 en verde", 1: f"✗ G2 en rojo: {len(res.hallazgos)} hallazgo(s)", 2: "? G2 sin medir (no es un verde)"}[rc]
    print(f"{veredicto}\n  {AVISO}")


# ── autoprueba: cada sabotaje tiene que caer, cada control tiene que pasar ────────────────
def _osv(nombre="lodash", version="4.17.15", eco="npm", vid="GHSA-aaaa-bbbb-cccc", alias=("CVE-2020-0001",),
         max_sev="7.2", etiqueta=None, fixed=("4.17.21",), tipo="SEMVER"):
    ev = [{"introduced": "0"}] + [{"fixed": f} for f in fixed]
    v = {"id": vid, "aliases": list(alias), "affected": [{"package": {"name": nombre, "ecosystem": eco},
                                                         "ranges": [{"type": tipo, "events": ev}]}]}
    if etiqueta:
        v["database_specific"] = {"severity": etiqueta}
    return {"results": [{"source": {"path": "/x/package-lock.json", "type": "lockfile"},
                         "packages": [{"package": {"name": nombre, "version": version, "ecosystem": eco},
                                       "vulnerabilities": [v],
                                       "groups": [{"ids": [vid], "aliases": [vid, *alias], "max_severity": max_sev}]}]}]}


def _corre(argv: list) -> tuple[int, str]:
    p = crea_parser()
    a = p.parse_args(argv)
    buf = io.StringIO()
    guardado = {k: os.environ.pop(k) for k in ("GATE_DEPS_OSV", "GATE_DEPS_PIP_AUDIT") if k in os.environ}
    try:                                         # la autoprueba no depende de lo que haya exportado quien la corre
        with contextlib.redirect_stdout(buf):
            rc, res = ejecuta(a)
            imprime(res, rc, False)
    finally:
        os.environ.update(guardado)
    return rc, buf.getvalue()


def autoprueba(vivo: bool, osv_bin: str | None) -> int:
    fallos, n = [], 0
    with tempfile.TemporaryDirectory(prefix="gate-deps-auto-") as td:
        T = Path(td)

        def proyecto(nombre: str, ficheros: dict) -> Path:
            d = T / nombre
            for rel, txt in ficheros.items():
                f = d / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(txt, encoding="utf-8")
            if not ficheros:
                d.mkdir(parents=True, exist_ok=True)
            return d

        def caso(id_, desc, esperado, argv, contiene=None, no_contiene=None):
            nonlocal n
            n += 1
            rc, out = _corre(argv)
            mal = rc != esperado
            if contiene and contiene not in out:
                mal = True
            if no_contiene and no_contiene in out:
                mal = True
            print(f"  {'✗' if mal else '✓'} {id_}  {desc}  (salida {rc}, esperada {esperado})")
            if mal:
                fallos.append(id_)

        def osv_file(nombre: str, data) -> str:
            p = T / f"{nombre}.json"
            p.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
            return str(p)

        FUTURO = (datetime.date.today() + datetime.timedelta(days=100)).isoformat()
        PJ = '{"name":"x","version":"1.0.0","dependencies":{"lodash":"4.17.15"}}'
        vacio = proyecto("vacio", {})
        con_lock = proyecto("conlock", {"package.json": PJ, "package-lock.json": "{}", ".npmrc": "ignore-scripts=true\n"})
        base = ["--solo", "vulnerabilidades"]

        print("— G2 vulnerabilidades: sabotajes (tienen que dar 1) y controles —")
        caso("V-01", "SABOTAJE: CVE alta (7,2) con arreglo → rojo", 1,
             [str(con_lock), *base, "--osv-json", osv_file("v01", _osv())], contiene="D1")
        caso("V-02", "SABOTAJE: crítica (9,8) → rojo", 1,
             [str(con_lock), *base, "--osv-json", osv_file("v02", _osv(max_sev="9.8"))], contiene="D1")
        caso("V-03", "SABOTAJE: sin CVSS pero etiqueta HIGH → rojo", 1,
             [str(con_lock), *base, "--osv-json", osv_file("v03", _osv(max_sev="", etiqueta="HIGH"))], contiene="D1")
        caso("V-04", "CONTROL: media (5,3) con arreglo → verde", 0,
             [str(con_lock), *base, "--osv-json", osv_file("v04", _osv(max_sev="5.3"))], no_contiene="✗")
        caso("V-05", "CONTROL: alta pero SIN arreglo → verde, pero en el informe", 0,
             [str(con_lock), *base, "--osv-json", osv_file("v05", _osv(fixed=()))], contiene="sin arreglo publicado")
        caso("V-06", "CONTROL: el único «arreglo» es un commit git, no una versión → verde", 0,
             [str(con_lock), *base, "--osv-json", osv_file("v06", _osv(fixed=("9d5d7c49ea75133e52ab22a8e9e13173938e36ff",), tipo="GIT"))])
        caso("V-07", "gravedad desconocida con arreglo, sin la opción → verde con informe", 0,
             [str(con_lock), *base, "--osv-json", osv_file("v07", _osv(max_sev="", etiqueta=None))], contiene="desconocida")
        caso("V-08", "SABOTAJE: la misma, con --bloquea-desconocida → rojo", 1,
             [str(con_lock), *base, "--bloquea-desconocida", "--osv-json", osv_file("v08", _osv(max_sev="", etiqueta=None))])
        caso("V-09", "CONTROL: --min-cvss 9 deja pasar la de 7,2", 0,
             [str(con_lock), *base, "--min-cvss", "9", "--osv-json", osv_file("v09", _osv())])
        caso("V-10", "arreglo menor que lo instalado: no cuenta como arreglo (versión ya posterior) → se ignora el menor", 1,
             [str(con_lock), *base, "--osv-json", osv_file("v10", _osv(version="4.17.15", fixed=("4.17.12", "4.17.21")))],
             contiene="4.17.21")
        caso("V-11", "SABOTAJE: JSON sin `results` → no medido", 2,
             [str(con_lock), *base, "--osv-json", osv_file("v11", {"otra": 1})])
        caso("V-12", "SABOTAJE: salida basura → no medido", 2,
             [str(con_lock), *base, "--osv-json", osv_file("v12", "esto no es json")])
        caso("V-13", "SABOTAJE: proyecto que no existe → no medido", 2, [str(T / "nada"), *base])
        caso("V-14", "SABOTAJE: hay manifiestos y el motor leyó cero ficheros → no medido (no es un verde)", 2,
             [str(con_lock), *base, "--osv-json", osv_file("v14", {"results": []})])
        caso("V-15", "CONTROL: proyecto sin ningún manifiesto → verde, y lo dice", 0,
             [str(vacio), *base], contiene="nada que medir")

        print("— excepciones (D4) —")
        ex_ok = proyecto("ex_ok", {"package.json": PJ, "package-lock.json": "{}", ".npmrc": "ignore-scripts=true\n",
                                   ".claude/deps-excepciones.json": json.dumps({"excepciones": [{
                                       "id": "CVE-2020-0001", "razon": "no se usa la función afectada; decide Ana", "caduca": FUTURO}]})})
        ex_cad = proyecto("ex_cad", {"package.json": PJ, "package-lock.json": "{}", ".npmrc": "ignore-scripts=true\n",
                                     ".claude/deps-excepciones.json": json.dumps({"excepciones": [{
                                         "id": "CVE-2020-0001", "razon": "x", "caduca": "2020-01-01"}]})})
        ex_sin = proyecto("ex_sin", {"package.json": PJ, "package-lock.json": "{}", ".npmrc": "ignore-scripts=true\n",
                                     ".claude/deps-excepciones.json": json.dumps({"excepciones": [{
                                         "id": "CVE-2020-0001", "caduca": FUTURO}]})})
        ex_otro = proyecto("ex_otro", {"package.json": PJ, "package-lock.json": "{}", ".npmrc": "ignore-scripts=true\n",
                                       ".claude/deps-excepciones.json": json.dumps({"excepciones": [{
                                           "id": "CVE-2099-9999", "razon": "otra cosa", "caduca": FUTURO}]})})
        sab = osv_file("sab", _osv())
        caso("E-06", "SABOTAJE: excepción que caduca dentro de años (sin tope) → rojo", 1,
             [str(proyecto("ex_lej", {"package.json": PJ, "package-lock.json": "{}", ".npmrc": "ignore-scripts=true\n",
                                      ".claude/deps-excepciones.json": json.dumps({"excepciones": [{
                                          "id": "CVE-2020-0001", "razon": "x", "caduca": "9999-12-31"}]})})),
              *base, "--osv-json", sab], contiene="400 días")
        caso("E-01", "CONTROL: excepción vigente con razón → verde y consta en el informe", 0,
             [str(ex_ok), *base, "--osv-json", sab], contiene="EXCEPCIÓN vigente")
        caso("E-02", "SABOTAJE: excepción caducada → rojo (D4 y D1 vuelve)", 1,
             [str(ex_cad), *base, "--osv-json", sab], contiene="CADUCADA")
        caso("E-03", "SABOTAJE: excepción sin razón → rojo", 1, [str(ex_sin), *base, "--osv-json", sab], contiene="sin `razon`")
        caso("E-04", "SABOTAJE: una excepción de OTRA vulnerabilidad no tapa esta → rojo", 1,
             [str(ex_otro), *base, "--osv-json", sab], contiene="D1")
        caso("E-05", "la caducidad se mide con la fecha: la vigente caduca en el futuro (--hoy 2100-01-01) → rojo", 1,
             [str(ex_ok), *base, "--osv-json", sab, "--hoy", "2100-01-01"], contiene="CADUCADA")

        print("— manifiestos sin lock (D2) —")
        caso("M-01", "SABOTAJE: package.json con deps y sin lock → rojo", 1,
             [str(proyecto("m1", {"package.json": PJ, ".npmrc": "ignore-scripts=true\n"})), "--solo", "vulnerabilidades",
              "--osv-json", osv_file("m1", {"results": [{"source": {"path": "x"}, "packages": []}]})], contiene="D2")
        caso("M-02", "SABOTAJE: pyproject con deps y sin poetry.lock → rojo", 1,
             [str(proyecto("m2", {"pyproject.toml": '[project]\nname="x"\ndependencies=["requests>=2"]\n'})),
              "--solo", "vulnerabilidades", "--osv-json", osv_file("m2", {"results": [{"source": {"path": "x"}, "packages": []}]})],
             contiene="D2")
        caso("M-03", "CONTROL: pyproject con poetry.lock → sin D2", 0,
             [str(proyecto("m3", {"pyproject.toml": '[project]\nname="x"\ndependencies=["requests>=2"]\n', "poetry.lock": ""})),
              "--solo", "vulnerabilidades", "--osv-json", osv_file("m3", {"results": [{"source": {"path": "x"}, "packages": []}]})],
             no_contiene="D2")
        caso("M-04", "CONTROL: package.json sin dependencias (solo scripts) → sin D2", 0,
             [str(proyecto("m4", {"package.json": '{"name":"x","scripts":{"a":"echo"}}'})), "--solo", "vulnerabilidades"],
             no_contiene="D2")

        caso("M-05", "SABOTAJE: package.json de subcarpeta sin lock en ningún padre → D2", 1,
             [str(proyecto("m5", {"web/package.json": PJ, "web/.npmrc": "ignore-scripts=true\n"})), "--solo", "vulnerabilidades",
              "--osv-json", osv_file("m5", {"results": []})], contiene="D2")
        print("— cobertura del motor, formas raras de la salida y opciones —")
        def sin_grupos():
            d = _osv(max_sev="9.8")
            for r in d["results"]:
                for p in r["packages"]:
                    p["groups"] = []
            return d
        caso("O-01", "SABOTAJE: vulnerabilidad 9,8 con arreglo y SIN grupos en la salida → rojo (no se pierde)", 1,
             [str(con_lock), *base, "--osv-json", osv_file("o1", sin_grupos())], contiene="D1")
        caso("O-02", "SABOTAJE: `results: [null]` → no medido, sin traza de Python", 2,
             [str(con_lock), *base, "--osv-json", osv_file("o2", {"results": [None]})], no_contiene="Traceback")
        caso("O-03", "CONTROL: el único «arreglo» es 4.17.12 y está instalada la 4.17.15 → no es un arreglo (verde, informe)", 0,
             [str(con_lock), *base, "--osv-json", osv_file("o3", _osv(version="4.17.15", fixed=("4.17.12",)))],
             contiene="sin arreglo publicado")
        caso("O-04", "SABOTAJE: --osv a una ruta que no existe → no medido, no cae a otro motor", 2,
             [str(con_lock), *base, "--osv", str(T / "no_existe_osv")])
        caso("O-05", "SABOTAJE: --sbom con --solo cadena → no medido (no se ignora en silencio)", 2,
             [str(con_lock), "--solo", "cadena", "--sbom", str(T / "x.cdx.json")])
        caso("O-06", "CONTROL: monorepo con lock en la raíz y package.json de workspace sin lock → sin D2", 0,
             [str(proyecto("mono", {"package.json": '{"name":"r","workspaces":["p/*"],"dependencies":{"a":"1.0.0"}}',
                                    "package-lock.json": "{}", ".npmrc": "ignore-scripts=true\n",
                                    "p/a/package.json": '{"name":"a","dependencies":{"b":"1.0.0"}}'})),
              "--solo", "vulnerabilidades", "--osv-json", osv_file("o6", {"results": [{"source": {"path": str(T / "mono" / "package-lock.json")}, "packages": []}]})], no_contiene="D2")
        caso("O-07", "SABOTAJE: Cargo.toml sin Cargo.lock → D2", 1,
             [str(proyecto("cargo", {"Cargo.toml": "[package]\nname='x'\n"})), "--solo", "vulnerabilidades",
              "--osv-json", osv_file("o7", {"results": []})], contiene="Cargo.lock")
        n += 1
        m = Resultado()
        cobertura([T / "conlock" / "package-lock.json", T / "conlock" / "poetry.lock"],
                  {"results": [{"source": {"path": str(T / "conlock" / "package-lock.json")}, "packages": []}]}, "osv", m)
        ok = len(m.no_medido) == 1 and "poetry.lock" in m.no_medido[0]
        print(f"  {'✓' if ok else '✗'} O-08  SABOTAJE: osv leyó el package-lock y no el poetry.lock → el que falta queda NO MEDIDO")
        if not ok:
            fallos.append("O-08")
        n += 1
        m = Resultado()
        cobertura([T / "a" / "requirements.txt", T / "a" / "package-lock.json"], {"results": []}, "pip-audit", m)
        ok = len(m.no_medido) == 1 and "package-lock.json" in m.no_medido[0]
        print(f"  {'✓' if ok else '✗'} O-09  SABOTAJE: pip-audit no lee package-lock.json → NO MEDIDO (no un verde)")
        if not ok:
            fallos.append("O-09")
        n += 1
        m = Resultado()
        cobertura([T / "conlock" / "package-lock.json"],
                  {"results": [{"source": {"path": str(T / "conlock" / "package-lock.json")}, "packages": []}]}, "osv", m)
        ok = not m.no_medido
        print(f"  {'✓' if ok else '✗'} O-10  CONTROL: el motor leyó todo lo esperado (aunque no tenga vulnerabilidades) → sin NO MEDIDO")
        if not ok:
            fallos.append("O-10")

        print("— segunda verificación: ficheros de versiones, workspaces, pnpm, versiones, uses —")
        vacio_osv = osv_file("vacio_osv", {"results": []})
        caso("R-01", "SABOTAJE: dev-requirements.txt existe y el motor no lo leyó → NO MEDIDO (antes: 0 «nada que medir»)", 2,
             [str(proyecto("r1", {"dev-requirements.txt": "jinja2==2.4.1\n"})), *base, "--osv-json", vacio_osv])
        caso("R-02", "SABOTAJE: requirements/prod.txt (estructura habitual de Django) → NO MEDIDO si el motor no lo leyó", 2,
             [str(proyecto("r2", {"requirements/prod.txt": "jinja2==2.4.1\n"})), *base, "--osv-json", vacio_osv])
        caso("R-03", "SABOTAJE: mix.lock (Elixir) se reconoce como fichero de versiones → NO MEDIDO si no se leyó", 2,
             [str(proyecto("r3", {"mix.lock": "%{}\n"})), *base, "--osv-json", vacio_osv])
        caso("R-04", "SABOTAJE: raíz con lock SIN workspaces y frontend/package.json sin lock → D2", 1,
             [str(proyecto("r4", {"package.json": '{"name":"r","dependencies":{"a":"1.0.0"}}', "package-lock.json": "{}",
                                  ".npmrc": "ignore-scripts=true\n",
                                  "frontend/package.json": '{"name":"f","dependencies":{"lodash":"4.17.15"}}'})),
              *base, "--osv-json", osv_file("r4", {"results": [{"source": {"path": str(T / "r4" / "package-lock.json")},
                                                                "packages": []}]})], contiene="frontend/package.json")
        caso("R-05", "SABOTAJE: pyproject con dependencias + un requirements-dev.txt suelto no es un lock → D2", 1,
             [str(proyecto("r5", {"pyproject.toml": '[project]\nname="x"\ndependencies=["jinja2==2.4.1"]\n',
                                  "requirements-dev.txt": "six==1.17.0\n"})),
              *base, "--osv-json", osv_file("r5", {"results": [{"source": {"path": str(T / "r5" / "requirements-dev.txt")},
                                                                "packages": []}]})], contiene="pyproject.toml")
        caso("R-06", "SABOTAJE: requirements con rango (jinja2>=2.0,<2.5) → D2 rojo, no aviso", 1,
             [str(proyecto("r6", {"requirements.txt": "jinja2>=2.0,<2.5\n"})),
              *base, "--osv-json", osv_file("r6", {"results": [{"source": {"path": str(T / "r6" / "requirements.txt")},
                                                                "packages": []}]})], contiene="✗ D2")
        caso("R-07", "CONTROL: requirements con == y marcador de entorno → sin D2", 0,
             [str(proyecto("r7", {"requirements.txt": 'jinja2==3.1.6 ; python_version >= "3.8"\n'})),
              *base, "--osv-json", osv_file("r7", {"results": [{"source": {"path": str(T / "r7" / "requirements.txt")},
                                                                "packages": []}]})], no_contiene="D2")
        caso("R-08", "SABOTAJE: poetry con dependencias solo en el grupo dev y sin lock → D2", 1,
             [str(proyecto("r8", {"pyproject.toml": '[tool.poetry.group.dev.dependencies]\npytest = "^8"\n'})),
              *base, "--osv-json", vacio_osv], contiene="pyproject.toml")
        caso("R-09", "SABOTAJE: package.json con solo optionalDependencies y sin lock → D2", 1,
             [str(proyecto("r9", {"package.json": '{"optionalDependencies":{"a":"1.0.0"}}', ".npmrc": "ignore-scripts=true\n"})),
              *base, "--osv-json", vacio_osv], contiene="D2")
        caso("R-10", "SABOTAJE: build.gradle sin gradle.lockfile → D2", 1,
             [str(proyecto("r10", {"build.gradle": "dependencies { }\n"})), *base, "--osv-json", vacio_osv], contiene="gradle.lockfile")
        caso("R-11", "SABOTAJE: max_severity en texto «HIGH» con arreglo → rojo", 1,
             [str(con_lock), *base, "--osv-json", osv_file("r11", _osv(max_sev="HIGH"))], contiene="D1")
        n += 1
        pares = [("0.0.0-20201216223049-abc", "0.0.0-20200622213623-75b288015ac9", True),
                 ("1.0.0", "1.0.0-rc.1", True), ("1.0.0-rc.1", "1.0.0", False), ("4.17.15", "4.17.15", False),
                 ("4.17.15.1", "4.17.15", True), ("1.2.3.SP1", "1.2.3.Final", True), ("2.0.0", "2.0.0rc1", True),
                 ("4.17.12", "4.17.15", False), ("1:2.4-1", "1:2.3-1", True), ("2.7.2", "2.4.1", True)]
        malos = [p for p in pares if _mayor(p[0], p[1]) != p[2]]
        print(f"  {'✗' if malos else '✓'} R-12  comparador de versiones: {len(pares)} pares (pseudo-versión de Go, rc, 4 segmentos, época)"
              + (f" · MAL: {malos}" if malos else ""))
        if malos:
            fallos.append("R-12")
        for nombre_, cfg in (("pnpm-pj", {"package.json": '{"packageManager":"pnpm@10.26.0","pnpm":{"dangerouslyAllowAllBuilds":true},'
                                                        '"dependencies":{"a":"1.0.0"}}'}),
                             ("pnpm-ws", {"package.json": '{"packageManager":"pnpm@10.26.0","dependencies":{"a":"1.0.0"}}',
                                          "pnpm-workspace.yaml": "dangerouslyAllowAllBuilds: true\n"}),
                             ("pnpm-rc", {"package.json": '{"packageManager":"pnpm@10.26.0","dependencies":{"a":"1.0.0"}}',
                                          ".npmrc": "dangerously-allow-all-builds=true\n"})):
            caso("P-" + nombre_, f"SABOTAJE: pnpm 10.26.0 con dangerouslyAllowAllBuilds ({nombre_}) → rojo S3", 1,
                 [str(proyecto(nombre_, cfg)), "--solo", "cadena"], contiene="dangerouslyAllowAllBuilds")
        caso("U-01", "SABOTAJE: clave `\"uses\":` entre comillas con etiqueta → rojo", 1,
             [str(proyecto("u1", {".github/workflows/a.yml": 'steps:\n  - "uses": actions/checkout@v4\n'})), "--solo", "cadena"],
             contiene="S2")
        caso("U-02", "SABOTAJE: estilo flow `- {uses: actions/checkout@v4}` → rojo", 1,
             [str(proyecto("u2", {".github/workflows/a.yml": "steps:\n  - {uses: actions/checkout@v4}\n"})), "--solo", "cadena"],
             contiene="S2")
        caso("U-03", "CONTROL: SHA de 40 hex en mayúsculas → verde", 0,
             [str(proyecto("u3", {".github/workflows/a.yml": "steps:\n  - uses: actions/checkout@" + "A" * 40 + "\n"})),
              "--solo", "cadena"], no_contiene="✗")
        caso("U-04", "SABOTAJE: docker://imagen@sha256: con el digest vacío → rojo", 1,
             [str(proyecto("u4", {".github/workflows/a.yml": "steps:\n  - uses: docker://alpine:3.20@sha256:\n"})), "--solo", "cadena"],
             contiene="sha256")
        caso("U-05", "SABOTAJE: yarn con enableScripts false y luego true → rojo (manda la última)", 1,
             [str(proyecto("u5", {"package.json": '{"packageManager":"yarn@4.5.0","dependencies":{"a":"1.0.0"}}',
                                  ".yarnrc.yml": "enableScripts: false\nenableScripts: true\n"})), "--solo", "cadena"],
             contiene="S3")
        n += 2
        m = Resultado()
        pa_ = T / "pa"
        pa_.mkdir(exist_ok=True)
        (pa_ / "requirements.txt").write_text("six==1.17.0\n-r otro.txt\n")
        cobertura([pa_ / "requirements.txt"], {"results": [], "_saltados": ["raro (no está en PyPI)"]}, "pip-audit", m)
        ok = len(m.no_medido) == 2
        print(f"  {'✓' if ok else '✗'} U-06  SABOTAJE: pip-audit no sigue `-r` y se salta un paquete → los dos quedan NO MEDIDOS")
        if not ok:
            fallos.append("U-06")
        m = Resultado()
        cobertura([pa_ / "requirements.txt"], {"results": [], "_saltados": []}, "pip-audit", m)
        ok = len(m.no_medido) == 1
        print(f"  {'✓' if ok else '✗'} U-07  el `-r` solo (sin saltados) es 1 NO MEDIDO")
        if not ok:
            fallos.append("U-07")

        print("— SBOM (D3) —")
        sb_bueno = T / "sbom_ok.json"
        sb_bueno.write_text(json.dumps({"bomFormat": "CycloneDX", "specVersion": "1.5", "components": [{"name": "a"}]}))
        sb_vacio = T / "sbom_vacio.json"
        sb_vacio.write_text(json.dumps({"bomFormat": "CycloneDX", "specVersion": "1.5", "components": []}))
        sb_otro = T / "sbom_otro.json"
        sb_otro.write_text(json.dumps({"bomFormat": "SPDX", "components": [{"name": "a"}]}))
        n += 3
        for id_, ruta, esperado_none, desc in (("B-01", sb_bueno, True, "CONTROL: SBOM CycloneDX con componentes → válido"),
                                               ("B-02", sb_vacio, False, "SABOTAJE: SBOM sin componentes → inválido"),
                                               ("B-03", sb_otro, False, "SABOTAJE: SBOM que no es CycloneDX → inválido")):
            mal = (valida_sbom(ruta) is None) != esperado_none
            print(f"  {'✗' if mal else '✓'} {id_}  {desc}")
            if mal:
                fallos.append(id_)
        n += 1
        mal = valida_sbom(T / "no_existe.json") is None
        print(f"  {'✗' if mal else '✓'} B-04  SABOTAJE: SBOM que no existe → inválido")
        if mal:
            fallos.append("B-04")

        print("— cadena de suministro —")
        wf_malo = proyecto("wf_malo", {".github/workflows/ci.yml": "jobs:\n  a:\n    steps:\n      - uses: actions/checkout@v4\n"})
        wf_ok = proyecto("wf_ok", {".github/workflows/ci.yml": "jobs:\n  a:\n    steps:\n"
                                    "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0\n"
                                    "      - uses: ./.github/actions/local\n"})
        wf_rama = proyecto("wf_rama", {".github/workflows/ci.yml": "steps:\n  - uses: anthropics/claude-code-action@main\n"})
        wf_img = proyecto("wf_img", {".github/workflows/ci.yml": "steps:\n  - uses: docker://alpine:3.20\n"})
        wf_short = proyecto("wf_short", {".github/workflows/ci.yml": "steps:\n  - uses: actions/checkout@11d5960\n"})
        caso("A-01", "SABOTAJE: `actions/checkout@v4` por etiqueta → rojo", 1, [str(wf_malo), "--solo", "cadena"], contiene="S2")
        caso("A-02", "CONTROL: SHA de 40 hex con comentario y acción local → verde", 0, [str(wf_ok), "--solo", "cadena"], no_contiene="✗")
        caso("A-03", "SABOTAJE: `@main` → rojo", 1, [str(wf_rama), "--solo", "cadena"], contiene="S2")
        caso("A-04", "SABOTAJE: imagen docker por etiqueta → rojo", 1, [str(wf_img), "--solo", "cadena"], contiene="sha256")
        caso("A-05", "SABOTAJE: SHA abreviado (7 hex) no vale → rojo", 1, [str(wf_short), "--solo", "cadena"], contiene="S2")
        caso("A-06", "la plantilla .yml.example también se mira → rojo", 1,
             [str(proyecto("wf_ex", {".github/workflows/x.yml.example": "steps:\n  - uses: actions/checkout@v4\n"})),
              "--solo", "cadena"], contiene="S2")

        mcp_latest = proyecto("mcp_l", {".mcp.json": json.dumps({"mcpServers": {"playwright": {
            "command": "npx", "args": ["-y", "@playwright/mcp@latest"]}}})})
        mcp_sinver = proyecto("mcp_s", {".mcp.json": json.dumps({"mcpServers": {"p": {"command": "npx", "args": ["-y", "@playwright/mcp"]}}})})
        mcp_pin = proyecto("mcp_p", {".mcp.json": json.dumps({"mcpServers": {"playwright": {
            "command": "npx", "args": ["-y", "@playwright/mcp@0.0.83"]}}})})
        mcp_rango = proyecto("mcp_r", {".mcp.json": json.dumps({"mcpServers": {"p": {"command": "npx", "args": ["x@^1.2.0"]}}})})
        mcp_uvx = proyecto("mcp_u", {".mcp.json": json.dumps({"mcpServers": {"s": {"command": "uvx", "args": ["mcp-server-git"]}}})})
        mcp_uvx_ok = proyecto("mcp_uo", {".mcp.json": json.dumps({"mcpServers": {"s": {"command": "uvx", "args": ["mcp-server-git==0.6.2"]}}})})
        mcp_otro = proyecto("mcp_o", {".mcp.json": json.dumps({"mcpServers": {"s": {"command": "node", "args": ["server.js"]}}})})
        caso("L-01", "SABOTAJE: `@playwright/mcp@latest` plantado → AVISO (sale 0)", 0, [str(mcp_latest), "--solo", "cadena"], contiene="⚠ S1")
        caso("L-02", "SABOTAJE: el mismo con --estricto → rojo", 1, [str(mcp_latest), "--solo", "cadena", "--estricto"], contiene="✗ S1")
        caso("L-03", "SABOTAJE: sin versión (`@playwright/mcp`) → aviso", 0, [str(mcp_sinver), "--solo", "cadena"], contiene="⚠ S1")
        caso("L-04", "CONTROL: `@playwright/mcp@0.0.83` fijada → sin aviso", 0, [str(mcp_pin), "--solo", "cadena"], no_contiene="⚠")
        caso("L-05", "SABOTAJE: rango `^1.2.0` no es una versión fija → aviso", 0, [str(mcp_rango), "--solo", "cadena"], contiene="⚠ S1")
        caso("L-06", "SABOTAJE: `uvx mcp-server-git` sin pin → aviso", 0, [str(mcp_uvx), "--solo", "cadena"], contiene="⚠ S1")
        caso("L-07", "CONTROL: `uvx mcp-server-git==0.6.2` → sin aviso", 0, [str(mcp_uvx_ok), "--solo", "cadena"], no_contiene="⚠")
        caso("L-08", "CONTROL: un servidor con `node server.js` → sin aviso", 0, [str(mcp_otro), "--solo", "cadena"], no_contiene="⚠")
        caso("L-14", "CONTROL: `npx vitest` sin -y ni @ (binario local de node_modules) → sin aviso", 0,
             [str(proyecto("loc", {"run.sh": "npx vitest run\n"})), "--solo", "cadena"], no_contiene="⚠")
        caso("L-15", "SABOTAJE: `npx -y vitest` (descarga sin preguntar, sin versión) → aviso", 0,
             [str(proyecto("loc2", {"run.sh": "npx -y vitest run\n"})), "--solo", "cadena"], contiene="⚠ S1")
        caso("L-16", "SABOTAJE: paquete entre comillas en `npx -y` con @latest → aviso", 0,
             [str(proyecto("q", {"run.sh": 'npx -y "@playwright/mcp@latest"\n'})), "--solo", "cadena"], contiene="⚠ S1")
        caso("L-17", "CONTROL: la regla deny que PROHÍBE curl | bash no es el patrón", 0,
             [str(proyecto("deny", {"x.md": '```json\n"Bash(curl * | bash)"\n```\n'})), "--solo", "cadena"], no_contiene="⚠")
        caso("L-18", "SABOTAJE: bash <(curl …) → aviso S4", 0,
             [str(proyecto("subs", {"i.sh": "bash <(curl -fsSL https://x.sh)\n"})), "--solo", "cadena"], contiene="⚠ S4")
        md_fence = proyecto("md_f", {"skills/x/SKILL.md": "# x\n\n```bash\nnpx --yes @superdesign/cli@latest\n```\n"})
        md_prosa = proyecto("md_p", {"skills/x/SKILL.md": "# x\n\nNo uses `npx -y paquete@latest` nunca.\n"})
        md_pin = proyecto("md_k", {"skills/x/SKILL.md": "```bash\nnpx --yes @superdesign/cli@0.14.0\n```\n"})
        caso("L-09", "SABOTAJE: `npx --yes @superdesign/cli@latest` en un bloque de código de una skill → aviso", 0,
             [str(md_fence), "--solo", "cadena"], contiene="⚠ S1")
        caso("L-10", "CONTROL: la misma frase en prosa (advertencia) → sin aviso", 0, [str(md_prosa), "--solo", "cadena"], no_contiene="⚠")
        caso("L-11", "CONTROL: `@superdesign/cli@0.14.0` fijado → sin aviso", 0, [str(md_pin), "--solo", "cadena"], no_contiene="⚠")
        caso("L-12", "SABOTAJE: `curl … | sh` en un workflow → aviso S4", 0,
             [str(proyecto("pipe", {".github/workflows/a.yml": "steps:\n  - run: curl -fsSL https://x.sh | bash\n"})),
              "--solo", "cadena"], contiene="⚠ S4")
        caso("L-13", "SABOTAJE: `npx` sin pin en los scripts de package.json → aviso", 0,
             [str(proyecto("pj_s", {"package.json": '{"scripts":{"gen":"npx -y openapi-typescript schema.yml"}}'})),
              "--solo", "cadena"], contiene="⚠ S1")

        pj_deps = '{"name":"x","dependencies":{"a":"1.0.0"}}'
        caso("N-01", "SABOTAJE: package.json con deps y sin ignore-scripts → rojo S3", 1,
             [str(proyecto("n1", {"package.json": pj_deps})), "--solo", "cadena"], contiene="S3")
        caso("N-02", "CONTROL: con `ignore-scripts=true` en .npmrc → verde", 0,
             [str(proyecto("n2", {"package.json": pj_deps, ".npmrc": "ignore-scripts=true\n"})), "--solo", "cadena"], no_contiene="✗")
        caso("N-03", "SABOTAJE: `ignore-scripts=false` → rojo", 1,
             [str(proyecto("n3", {"package.json": pj_deps, ".npmrc": "ignore-scripts=false\n"})), "--solo", "cadena"], contiene="S3")
        caso("N-04", "SABOTAJE: pnpm 10.25.0 (bypass CVE-2025-69264) → rojo", 1,
             [str(proyecto("n4", {"package.json": '{"packageManager":"pnpm@10.25.0","dependencies":{"a":"1.0.0"}}'})),
              "--solo", "cadena"], contiene="10.26.0")
        caso("N-05", "CONTROL: pnpm 10.26.0 → verde", 0,
             [str(proyecto("n5", {"package.json": '{"packageManager":"pnpm@10.26.0","dependencies":{"a":"1.0.0"}}'})),
              "--solo", "cadena"], no_contiene="✗")
        caso("N-06", "CONTROL: pnpm 12.14.0 → verde", 0,
             [str(proyecto("n6", {"package.json": '{"packageManager":"pnpm@12.14.0","dependencies":{"a":"1.0.0"}}'})),
              "--solo", "cadena"], no_contiene="✗")
        caso("N-07", "SABOTAJE: pnpm 9.15.0 sin .npmrc → rojo (v9 sí ejecuta scripts)", 1,
             [str(proyecto("n7", {"package.json": '{"packageManager":"pnpm@9.15.0","dependencies":{"a":"1.0.0"}}'})),
              "--solo", "cadena"], contiene="S3")
        caso("N-08", "CONTROL: el .npmrc de la raíz cubre un package.json de subcarpeta → verde", 0,
             [str(proyecto("n8", {".npmrc": "ignore-scripts=true\n", "web/package.json": pj_deps})), "--solo", "cadena"],
             no_contiene="✗")
        caso("N-09", "CONTROL: package.json sin dependencias → no exige nada", 0,
             [str(proyecto("n9", {"package.json": '{"name":"x"}'})), "--solo", "cadena"], no_contiene="✗")
        caso("N-10", "CONTROL: yarn con enableScripts: false → verde", 0,
             [str(proyecto("n10", {"package.json": '{"packageManager":"yarn@4.5.0","dependencies":{"a":"1.0.0"}}',
                                   ".yarnrc.yml": "enableScripts: false\n"})), "--solo", "cadena"], no_contiene="✗")
        caso("N-11", "CONTROL: node_modules y _archive no se miran", 0,
             [str(proyecto("n11", {"node_modules/a/package.json": pj_deps, "_archive/x/package.json": pj_deps})),
              "--solo", "cadena"], no_contiene="✗")

        caso("N-12", "SABOTAJE: ignore-scripts=true y luego =false → rojo (npm aplica la última)", 1,
             [str(proyecto("n12", {"package.json": pj_deps, ".npmrc": "ignore-scripts=true\nignore-scripts=false\n"})),
              "--solo", "cadena"], contiene="S3")
        caso("N-13", "CONTROL: ignore-scripts entre comillas con valor true → verde", 0,
             [str(proyecto("n13", {"package.json": pj_deps, ".npmrc": 'ignore-scripts="true"\n'})), "--solo", "cadena"],
             no_contiene="✗")

        if vivo:
            print("— en vivo (red + osv-scanner real) —")
            osv = buscar_binario("osv-scanner", osv_bin, "GATE_DEPS_OSV")
            if not osv:
                print("  ✗ VIVO  pedido --vivo y no hay osv-scanner")
                fallos.append("VIVO")
            else:
                fx = proyecto("vivo", {"requirements.txt": "jinja2==2.4.1\nrequests==2.19.0\n"})
                caso("W-01", "SABOTAJE EN VIVO: jinja2 2.4.1 + requests 2.19.0 (CVE conocidas) → rojo", 1,
                     [str(fx), "--solo", "vulnerabilidades", "--osv", osv], contiene="D1")
                limpio = proyecto("vivo_limpio", {"requirements.txt": "six==1.17.0\n"})
                n += 1
                rc, out = _corre([str(limpio), "--solo", "vulnerabilidades", "--osv", osv])
                mal = rc not in (0, 1) or "NO MEDIDO" in out
                print(f"  {'✗' if mal else '✓'} W-04  proyecto limpio con osv real: se MIDE (0, o 1 si ya hay un CVE nuevo), nunca 2  (salida {rc})")
                if mal:
                    fallos.append("W-04")
                ign = proyecto("vivo_ign", {"requirements.txt": "six==1.17.0\n", ".gitignore": "legacy/\n",
                                            "legacy/package-lock.json": json.dumps({"lockfileVersion": 3, "packages": {
                                                "": {}, "node_modules/lodash": {"version": "4.17.15"}}})})
                caso("W-05", "SABOTAJE EN VIVO: un lock dentro de un .gitignore que osv no lee → NO MEDIDO, no verde", 2,
                     [str(ign), "--solo", "vulnerabilidades", "--osv", osv], contiene="no leyó")
                sb2 = T / "vivo_limpio.cdx.json"
                _corre([str(limpio), "--solo", "vulnerabilidades", "--osv", osv, "--sbom", str(sb2)])
                n += 1
                try:
                    nombres = [c.get("name") for c in json.loads(sb2.read_text())["components"]]
                except (OSError, ValueError, KeyError):
                    nombres = []
                mal = "six" not in nombres
                print(f"  {'✗' if mal else '✓'} W-06  el SBOM de un proyecto SIN vulnerabilidades lista sus componentes (six)")
                if mal:
                    fallos.append("W-06")
                fx2 = proyecto("vivo_sbom", {"requirements.txt": "jinja2==2.4.1\n"})
                sbom = T / "vivo.cdx.json"
                caso("W-02", "SBOM en vivo: CycloneDX con componentes", 1,
                     [str(fx2), "--solo", "vulnerabilidades", "--osv", osv, "--sbom", str(sbom)], contiene="SBOM CycloneDX")
                n += 1
                mal = valida_sbom(sbom) is not None or "vulnerabilities" in json.loads(sbom.read_text())
                print(f"  {'✗' if mal else '✓'} W-03  el fichero SBOM escrito valida y va sin el bloque `vulnerabilities` de osv")
                if mal:
                    fallos.append("W-03")
    print(f"\nautoprueba G2: {n - len(fallos)}/{n}" + (f" · FALLAN: {', '.join(fallos)}" if fallos else ""))
    return 1 if fallos else 0


def crea_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="G2: dependencias vulnerables, SBOM y cadena de suministro.")
    p.add_argument("proyecto", nargs="?", help="carpeta del proyecto")
    p.add_argument("--solo", choices=["vulnerabilidades", "cadena"], help="solo una mitad del gate")
    p.add_argument("--sbom", help="escribe aquí el SBOM CycloneDX y lo valida")
    p.add_argument("--osv", help="ruta al binario de osv-scanner (o $GATE_DEPS_OSV)")
    p.add_argument("--pip-audit", dest="pip_audit", help="ruta a pip-audit (o $GATE_DEPS_PIP_AUDIT)")
    p.add_argument("--motor", choices=["auto", "osv", "pip-audit"], default="auto")
    p.add_argument("--osv-json", help="analiza una salida de `osv-scanner --format json` ya generada")
    p.add_argument("--min-cvss", type=float, default=7.0, help="gravedad mínima que bloquea (7.0 = HIGH)")
    p.add_argument("--bloquea-desconocida", action="store_true", help="bloquea también las de gravedad desconocida")
    p.add_argument("--estricto", action="store_true", help="los avisos (S1, S4, D2 sin pin) son rojo")
    p.add_argument("--excepciones", help=f"fichero de excepciones (por defecto {EXCEPCIONES})")
    p.add_argument("--hoy", help="fecha ISO para medir las caducidades (pruebas)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--autoprueba", action="store_true")
    p.add_argument("--vivo", action="store_true", help="con --autoprueba: también contra osv-scanner real (red)")
    return p


def main(argv=None) -> int:
    a = crea_parser().parse_args(argv)
    if a.autoprueba:
        return autoprueba(a.vivo, a.osv)
    if not a.proyecto:
        print("falta la carpeta del proyecto (o --autoprueba)", file=sys.stderr)
        return 2
    rc, res = ejecuta(a)
    imprime(res, rc, a.json)
    return rc


if __name__ == "__main__":
    sys.exit(main())
