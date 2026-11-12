#!/usr/bin/env python3
"""template_diff.py — diff determinista template ↔ proyecto derivado (motor de update-agent).

Compara el `.claude/` del template con el de un proyecto y clasifica cada asset en:
  MISSING  en el template, ausente en el proyecto            → candidato a copiar
  STALE    en ambos, DISTINTO, y la versión del proyecto es  → se actualiza (es solo vieja)
           una versión VIEJA del template (git lo sabe)
  SOLO FRONTMATTER  igual que STALE, pero el cuerpo es el     → se actualiza; no hace falta leer el
           mismo y solo cambia la cabecera (`paths:`…)          diff (era el ruido de T-109)
  LOCAL POSTERIOR  distinto, el template NUNCA tuvo esa       → NO se pisa: es un arreglo del
           versión, y el proyecto SÍ tuvo la actual del        proyecto más nuevo (elvion #17)
           template y la cambió (sin git en el proyecto: lo
           escribió después del último cambio del template)
  DIVERGENTE  distinto, versión que el template nunca tuvo,  → NO se pisa: merge a mano
           y el proyecto nunca tuvo la actual del template
  DELIBERADA  declarada en `DIVERGENCIAS-DELIBERADAS.md` (en el .claude/ del proyecto), también
           si el proyecto lo BORRÓ                           → NO se pisa ni se vuelve a crear
  SIN HISTORIA  distinto, y el template no tiene git         → NO se pisa: no se puede saber
  LOCAL    solo en el proyecto                               → informativo, NUNCA se toca

Las de en medio son la sub-ola 1.09 (MO-11, MO-57): hasta entonces todo lo distinto era
STALE, y el propagador del template lo copiaba encima. Así se perdió en elvion el arreglo #17
(`hooks/auto-progress-log.sh` leyendo stdin, 2026-08-08): la sincronización del 2026-08-10 lo pisó
con la versión del template, que leía variables que no existen, y el registro `[AUTO]` se cortó.

Cubre TODAS las categorías (el bug histórico de update-agent era mirar solo skills/agents/
commands/hooks y por tanto no propagar jamás templates/, scripts/, rules/ ni workflows/ — TPL-11):
  skills/ agents/ commands/ hooks/ templates/ scripts/ rules/ workflows/ patterns/
  output-styles/ template/   (MO-57: dos carpetas de EvoPreven que el diff no veía)
y lista como SIN INVENTARIAR cualquier otra carpeta de `.claude/` que no mire.

Personalización local (se EXCLUYE de STALE — divergir ahí es legítimo, no deuda):
  agents/*/memory.md · agents/*/trend.json · agents/*/suggestions.jsonl · improvements_tl.md
  patterns/** (dominancia medida POR proyecto) · settings.json (se mergea, no se compara)
Y lo propio de una rule va en `rules/<rule>-<proyecto>.md` (MO-58), con la del template intacta:
el diff lo reconoce como PERSONALIZACIÓN y, para una rule con cambios propios, lo propone.

Solo lee: el git del proyecto se consulta con `GIT_OPTIONAL_LOCKS=0` y sin `git status`, así que
ni siquiera refresca su índice.

Uso:
  python3 template_diff.py <proyecto>            # tabla humana (proyecto = raíz o su .claude/)
  python3 template_diff.py <proyecto> --json     # salida máquina para update-agent
  python3 template_diff.py <proyecto> --core     # solo el bloque CORE TPL-1 + ¿CORE_VERSION al día?
  python3 template_diff.py --core-hash           # hash del CORE del template (para CORE_VERSION)
  [--template DIR]   # default: $TL_TEMPLATE_DIR o el repo donde vive este script

CORE TPL-1 (decisión Usuario 2026-08-07, G1): ver CORE_SPEC abajo. Al aplicar el CORE en un
proyecto, update-agent escribe `<target>/.claude/CORE_VERSION` con el hash de --core-hash;
check-agent (dimensión 10) lo compara para responder "¿está Y está al día?" (TPL-13).
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import time

# `patterns` FALTABA aquí hasta el 2026-08-25, y era el fallo de raíz de todo lo demás.
# inventory() solo recorre estas carpetas, así que ningún fichero de patterns/ llegaba nunca a
# in_core() ni a is_personal(): la línea "patterns/" de CORE_SPEC era DECORATIVA y el CORE no
# propagó un solo patrón en su vida. Se descubrió al auditar un proyecto Django real que había
# nacido sin los 14 documentos de patrón de backend — y que por tanto se escribió entero sin el
# patrón de casa y sin su gate. No fue un despiste de quien montó el harness: la herramienta que
# debía avisar era ciega a esa carpeta.
#
# `output-styles` y `template` (MO-57, 2026-10-20) son el mismo fallo en pequeño: EvoPreven/develop
# tiene un output-style propio («Visual y explicativo») y `template/report-template.html`, y el diff
# no los listaba ni como LOCAL — piezas propias invisibles a cualquier cosecha. `output-styles/` es
# además una carpeta que Claude Code lee: el día que el template tenga uno, viajará.
CATEGORIES = ["skills", "agents", "commands", "hooks", "templates", "scripts", "rules", "workflows",
              "patterns", "output-styles", "template"]

# Carpetas de `.claude/` que no son piezas: generadas, efímeras, de consulta del template o el
# cementerio. Cualquier OTRA que el diff no recorra sale como SIN INVENTARIAR (MO-57), para que la
# próxima `output-styles/` se vea el primer día y no a la tercera auditoría.
CARPETAS_NO_PIEZA = {"_archive", "_deprecated", "_retirados", "sessions", "docs", "smoke",
                     "memory", "examples", "plan", "worktrees", "resources", "packs",
                     # 3.57: los paquetes de dominio no viajan como piezas; los instala
                     # `domain_packs.py` solo en el proyecto que declara su sector
                     "domains",
                     "__pycache__", ".backups", "node_modules", ".git"}

# `patterns/` tiene DOS mitades y hasta 2026-08-25 se trataban como una sola, con consecuencias.
#
#   · MEDIDO (personal): `catalog.yaml` con su dominancia, `baseline/` con la deuda aceptada,
#     `telemetry.jsonl`, `ownership.yaml` y los `<id>.md` — todo eso sale de MEDIR ESE repo. Imponer
#     el catálogo del template a un proyecto es afirmar una dominancia que nadie ha medido allí.
#   · DECLARADO (viaja): `stack/` — el estilo con el que se escribe aquí CUANDO TODAVÍA NO HAY
#     CÓDIGO del que deducirlo. Su propio README lo dice: «es la rama proyecto NUEVO». Más
#     `ownership_check.py` y `README.md`, que son herramienta y documentación, no medición.
#
# Meterlo todo en `is_personal` dejaba `patterns/stack/` fuera del radar de STALE, y la prosa de
# `create-agent` («su canon patterns/ NO se copia») llevó además a no copiarlo. Medido el
# 2026-08-25 en un proyecto real: 104 ficheros de patrón en el template, 22 en el proyecto — los
# 14 documentos de backend y sus comprobadores nunca llegaron. Cuando se copiaron, el comprobador
# encontró 22 violaciones activas, tres serias (Celery aceptando pickle, Celery sin límite de
# tiempo, SECRET_KEY literal en un settings versionado). Ninguna la habría visto una review leyendo
# el diff, y el proyecto ya estaba desplegado.
_PATTERNS_VIAJAN = ("patterns/stack/",)
_PATTERNS_PERSONALES = ("patterns/baseline/",)
# `ownership.yaml` NO entra aquí, y la distinción la hace su propia cabecera: los patrones de
# `catalog.yaml` se MIDEN (dominancia sobre ese repo); las reglas de `ownership.yaml` se DECLARAN
# («cada zona del repo declara POR ESCRITO qué le pertenece»). Un contrato declarado se adopta y
# se ESTRECHA —es literalmente su regla de herencia vertical—, no se re-mide. Y si no viajara,
# `ownership_check.py` viajaría solo para leer un fichero que no existe. Lo corrigió la sesión que
# sincroniza /home/webs, midiendo que sus 9 scopes reales existen y que sus reglas son genéricas.
_PATTERNS_PERSONALES_FILE = {
    "patterns/catalog.yaml", "patterns/telemetry.jsonl",
}


# relpaths (dentro de .claude/) que son personalización local → jamás STALE, jamás sobrescribir
def is_personal(rel: str) -> bool:
    parts = rel.split("/")
    if rel == "improvements_tl.md" or rel == "settings.json":
        return True
    if parts[0] == "patterns":
        if rel.startswith(_PATTERNS_VIAJAN):
            return False          # el patrón DECLARADO: viaja y puede quedarse viejo
        if rel.startswith(_PATTERNS_PERSONALES) or rel in _PATTERNS_PERSONALES_FILE:
            return True
        # `<id>.md` en la raíz de patterns/ es un patrón medido EN ESTE repo → personal.
        # `README.md` y `ownership_check.py` son doc y herramienta → viajan.
        return not (len(parts) == 2 and parts[1] in ("README.md", "ownership_check.py"))
    if parts[0] == "agents" and parts[-1] in ("memory.md", "trend.json", "suggestions.jsonl"):
        return True
    return False

SKIP_DIRS = {"__pycache__", ".backups", "node_modules", ".git"}
# El cementerio no se propaga. Sin esto, el template proponía COPIAR `agents/_deprecated/` a
# cada proyecto derivado: exactamente lo contrario de haberlo jubilado, y el fallo simétrico
# del que arregla `retiradas()` más abajo.
SKIP_DIRS = set(SKIP_DIRS) | {"_archive", "_deprecated"}
# Cementerios de un PROYECTO (D-12, improvements #21): lo que él archivó a propósito.
CEMENTERIOS = {"_archive", "_deprecated", "_retiradas", "_retirados", "_archivadas", "_archivo"}
SKIP_DIRS |= CEMENTERIOS
SKIP_FILES = {".DS_Store"}
# generados/efímeros — no son assets a propagar
SKIP_REL_PREFIX = ("sessions/", "docs/", "smoke/", "memory/", "examples/", "plan/")
SKIP_REL = {"PROGRESS.log", "PROGRESS.auto.log", "audit.jsonl", "CORE_VERSION", "CLAUDE.local.md"}

# El bloque CORE TPL-1 (create-agent SKILL.md §"CORE TPL-1" — mantener AMBOS en sincronía).
# Rita entra como agente+hook+skill. De su canon viaja `patterns/stack/` (el patrón
# DECLARADO, para proyecto nuevo); lo MEDIDO (catalog/baseline/telemetry) se genera por
# proyecto y `is_personal()` lo protege. Ver el bloque de arriba.
CORE_SPEC = [
    "templates/report_kit/",
    "skills/otto/", "agents/otto-copilot/",
    "agents/pol-product-advisor.md", "agents/pol-product-advisor/",
    "agents/rita-pattern-keeper.md", "agents/rita-pattern-keeper/",
    "hooks/otto-briefing.sh", "hooks/pattern-check.sh",
    # El registro de peticiones es estructural, no opcional: sin él, lo que el Usuario pide entre
    # veinte tareas se pierde. Va en el CORE para que ningún proyecto derivado nazca sin él.
    "hooks/capture-task.sh", "hooks/dispatch-hint.sh",
    "scripts/tasks_registry.py", "scripts/ensure_hooks.py",
    # U.06: sin estos dos, audit-log/auto-progress-log escriben [REDACTED:no-redactor] y
    # tasks_registry no registra (los tres hooks del núcleo los importan)
    "scripts/redactar.py", "scripts/scan_secretos_diff.py",
    # Meta-estructural: lo que decide QUÉ actualizar y comprueba que el harness no miente. Va en
    # el CORE porque un proyecto que no lo tenga no puede ni saber qué le falta. (La skill
    # `mapear-sistema` salió del CORE en la 1.10: LI-8 la puso en solo-template —se usa desde el
    # template, con su ruta— y con propagación por packs no llega a ningún derivado; el que la
    # tenga la conserva, porque propagar no borra.)
    "scripts/audit_sistema_ia.py",
    "scripts/gen_harness_graph.py", "scripts/check_mechanisms.py",
    "scripts/graphify_to_dataset.py", "scripts/settings_profile.py",
    # El patrón de casa: lo que hace que el código nuevo se escriba como se escribe aquí.
    "patterns/",
    "scripts/gen_agent_system.py", "scripts/items_to_speckit.py",
    # PV-5: el panel no basta con copiarlo, hay que poder arrancarlo. Va en el CORE por
    # el mismo motivo que el registro de peticiones: sin él, la pieza llega y no corre.
    "scripts/abrir_panel.py", "scripts/agent_registry.py", "hooks/agent-registry-log.sh",
    "scripts/render_nav.py", "scripts/check_shared_block.py", "scripts/gen_skill_index.py",
    "scripts/template_diff.py",
    "rules/report-kit.md", "rules/verdict-contract.md",
    "skills/pattern-gate/",
    # La guía para quien NO conoce los comandos (T-240, 2026-09-14): mide el proceso con el mismo
    # gen_proceso.py del kit y dice qué teclear. Sin esto, un derivado tiene el tablero y nadie sabe
    # que existe. Lo imprime al arrancar hooks/otto-briefing.sh (antes hooks/siguiente-paso.sh,
    # fusionado en él el 2026-10-19, LI-25), que ensure_hooks.py registra (SessionStart).
    "scripts/siguiente_paso.py", "commands/siguiente.md",
]


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def claude_dir(root: str) -> str:
    root = os.path.abspath(root)
    return root if os.path.basename(root) == ".claude" else os.path.join(root, ".claude")


def inventory(cdir: str) -> dict:
    """relpath (desde .claude/) → sha256, solo dentro de CATEGORIES."""
    out = {}
    for cat in CATEGORIES:
        base = os.path.join(cdir, cat)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if fn in SKIP_FILES:
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, cdir).replace(os.sep, "/")
                if rel in SKIP_REL or any(rel.startswith(p) for p in SKIP_REL_PREFIX):
                    continue
                out[rel] = sha(full)
    return out


# ── Lo que NO se siembra ─────────────────────────────────────────────────────
# `is_personal()` protege de sobrescribir. No protege de SEMBRAR: el bucle de MISSING no lo
# consulta, así que un fichero personal AUSENTE se copia igual. Para la mayoría está bien —un
# proyecto nuevo agradece la semilla— pero hay una clase donde es activamente dañino: la que
# contiene MEDICIONES de este repo.
#
# El caso que lo destapó (2026-08-25, sesión de /home/webs): al traer `rita-pattern-keeper` como
# pieza del CORE se copió su `memory.md`, que lleva dentro la dominancia medida AQUÍ —73% (16/22
# rules), 100% (60/60 skills)— y un `trend.json` que dice `"app": "tech-lead-template"`. El
# proyecto receptor tenía 41 rules y 67 skills. O sea: **la guardiana del patrón nace en cada
# proyecto creyéndose los números de otro repo**, y los cita como si los hubiera medido allí.
# Es el mismo fallo que `patterns/catalog.yaml`, un nivel más abajo y más difícil de ver.
#
# Estos ficheros se reportan aparte y se crean VACÍOS en destino, nunca copiados.
def no_se_siembra(rel: str) -> bool:
    parts = rel.split("/")
    if parts[0] == "agents" and parts[-1] in ("memory.md", "trend.json", "suggestions.jsonl"):
        return True
    if parts[0] == "patterns":
        if rel in ("patterns/catalog.yaml", "patterns/telemetry.jsonl"):
            return True
        if rel.startswith("patterns/baseline/") and rel.endswith(".json"):
            return True
        # `<id>.md` en la raíz: patrones medidos sobre ESTE repo, con la cifra en el título
        return len(parts) == 2 and parts[1] not in ("README.md", "ownership_check.py",
                                                    "ownership.yaml")
    return False


# Lo que una carpeta de CORE_SPEC cubre y NO es del CORE (sub-ola 1.10, AN-10). `patterns/` entra
# entero, pero los patrones `stack/agente-*` y su comprobador son del pack conversacional (LI-1; tres de
# ellos, opcionales del núcleo desde el 22-10, PATRONES-AGENTE: solo con `extra:`): un
# Django+React sin bot no los recibe, y con ellos dentro su CORE_VERSION no podría escribirse nunca.
# `gen_packs.py --check` falla si un fichero del CORE es de una pieza que no viaja con todo perfil.
CORE_FUERA = ("patterns/stack/agente-", "patterns/stack/pattern_check_agente.py",
              "patterns/stack/catalogo-modelo.md",  # 3.32: del pack conversacional, como los agente-*
              "patterns/stack/campaigns.md",  # 3.51: con el gate de campañas, en el mismo pack
              "patterns/stack/analytics-commerce.md",  # 3.54: del pack negocio, con su skill y su gate
              "patterns/stack/chat-ui-comercio.md",  # 3.68: del pack conversacional, con probar-widget
              "patterns/stack/conocimiento-con-evidencia.md",  # 3.55: del pack conversacional
              "patterns/stack/web-measurement.md",  # 3.55: del pack marketing-web, con su kit
              "patterns/stack/langfuse-autoalojado.md")  # 3.28: del pack conversacional


def in_core(rel: str) -> bool:
    if rel.startswith(CORE_FUERA):
        return False
    return any(rel == c or (c.endswith("/") and rel.startswith(c)) for c in CORE_SPEC)


def core_hash(tpl_inv: dict) -> str:
    """Hash del CORE — SIN lo personal, o el marcador da falsas alarmas.

    Medido el 2026-08-25: 6 de los 59 ficheros del CORE eran personales (`memory.md`,
    `trend.json`, `suggestions.jsonl` de Otto, Pol y Rita). Como esas memorias cambian
    constantemente en el template, el hash cambiaba con ellas y **el CORE_VERSION de todos los
    proyectos derivados caducaba sin que ninguna pieza del CORE se hubiera movido**. Un marcador
    que avisa cuando no pasa nada se aprende a ignorar, y entonces no avisa cuando sí pasa — la
    misma avería que este fichero existe para evitar.
    """
    h = hashlib.sha256()
    for rel in sorted(r for r in tpl_inv if in_core(r) and not is_personal(r)):
        h.update(f"{rel}:{tpl_inv[rel]}\n".encode())
    return h.hexdigest()[:12]



def unit_of(rel: str) -> str:
    """Unidad de reporte: la skill/plantilla entera, no cada fichero interno."""
    p = rel.split("/")
    if p[0] in ("skills", "templates") and len(p) > 2:
        return f"{p[0]}/{p[1]}/"
    if p[0] == "agents" and len(p) > 2:
        return f"agents/{p[1]}/"
    return rel


def retiradas(tpl_root):
    """Lo que el template TUVO y ya no tiene: `_archive/` y `_deprecated/`.

    POR QUÉ HACE FALTA. Sin esto, una pieza que jubilamos a propósito aparece en el proyecto como
    `LOCAL — solo del proyecto (no se toca)`, que es exactamente la conclusión contraria: no es una
    adaptación suya, es nuestra y con fecha de baja. Medido sobre un proyecto real: **25 de sus 47
    «adaptaciones locales» eran piezas retiradas**, y el informe las presentaba como intocables.

    Retirado ≠ nuestro-nunca. La acción correcta es retirarlo allí también —o conservarlo a
    sabiendas—, jamás traerlo de vuelta ni darlo por local. Mismo criterio que
    `audit_sistema_ia.py`, que ya lo hacía para el otro lado del cruce."""
    fuera = set()
    for base in (os.path.join(tpl_root, "..", "_archive"), os.path.join(tpl_root, "_archive"),
                 os.path.join(tpl_root, "agents", "_deprecated"),
                 os.path.join(tpl_root, "skills", "_deprecated")):
        base = os.path.abspath(base)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            # Los PLANES archivados (`_archive/<fecha>/planes-*/`, LI-30 2026-10-19) no son piezas del
            # harness: traen server.py, tasks.md, kits enteros… y cada nombre entraría como «retirado»,
            # con lo que una pieza propia de un derivado que se llamara igual dejaría de verse como local.
            dirnames[:] = [d for d in dirnames if not d.startswith("planes-")]
            for d in dirnames:
                fuera.add(d)
            for f in filenames:
                stem, ext = os.path.splitext(f)
                if ext in (".md", ".py", ".js", ".sh"):
                    fuera.add(stem)
    return {x for x in fuera if x.lower() not in ("readme", "_archive")}


# ── ¿Versión vieja del template, o arreglo del proyecto? (MO-11, sub-ola 1.09) ─────────────────
# El sha256 dice que dos ficheros son distintos; no dice cuál de los dos es el bueno. Hasta la 1.09
# todo lo distinto era STALE y el propagador lo pisaba. Medido en elvion: su arreglo #17 (commit
# 1855d82, 2026-08-08) lo deshizo la sincronización del 2026-08-10 con la versión que el template
# tenía desde el 2026-04-19. Ninguna fecha ni ningún commit se consultaron.
#
# La pregunta que decide es de HISTORIA, no de fechas: ¿la versión del proyecto la tuvo alguna vez
# el template? Si sí, el proyecto solo se quedó atrás y actualizar no pierde nada. Si no, alguien la
# escribió allí, y la segunda pregunta también es de historia: ¿el proyecto tuvo alguna vez la
# versión ACTUAL del template? Si sí, lo suyo vino después → arreglo local más nuevo (elvion #17); si
# no, los dos se movieron → merge a mano. Solo sin git en el proyecto se mira la fecha. Y sin git en
# el template no se sabe nada: tampoco se pisa (verificador de la 1.09).
_GIT_ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0")   # ni el refresco del índice de `git status`


def blob_id(path: str) -> str:
    """El id que git daría al fichero (`git hash-object`), sin llamar a git."""
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _git(base: str, *args: str) -> str | None:
    try:
        # core.quotePath=false: sin él, `log --raw` y `ls-tree` entrecomillan los nombres con acentos
        # («diseño.md») y la ruta no casaría con la del disco.
        r = subprocess.run(["git", "-C", base, "-c", "core.quotePath=false", *args],
                           capture_output=True, text=True, errors="surrogateescape",
                           env=_GIT_ENV, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


class Historia:
    """Lo que git sabe de una carpeta (`.claude/`, `.specify/`…): cada versión que tuvo cada
    fichero, cuándo se escribió cada una y qué hay en HEAD. Solo lee (`git log`, `git ls-tree`)."""

    def __init__(self, base: str):
        self.base = os.path.abspath(base)
        self.versiones: dict[str, set[str]] = {}
        self.cuando: dict[tuple[str, str], int] = {}      # (rel, blob) → epoch en que se escribió
        self.head: dict[str, str] = {}
        prefijo = (_git(self.base, "rev-parse", "--show-prefix")
                   if os.path.isdir(self.base) else None)
        self.git = prefijo is not None
        if not self.git:
            return
        prefijo = prefijo.strip()
        # -m: también el blob que deja un merge; --no-renames: renombrar es baja + alta por ruta.
        log = _git(self.base, "log", "-m", "--no-renames", "--raw", "--no-abbrev",
                   "--format=C %ct %P", "--", ".") or ""
        ct, merge = 0, False
        en_merge: dict[tuple[str, str], int] = {}
        for linea in log.splitlines():
            if linea.startswith("C "):
                campos = linea[2:].split()
                ct, merge = int(campos[0] if campos else 0), len(campos) > 2
                continue
            if not linea.startswith(":") or "\t" not in linea:
                continue
            meta, ruta = linea.split("\t", 1)
            if not ruta.startswith(prefijo):
                continue
            rel, nuevo = ruta[len(prefijo):], meta.split()[3]
            if not nuevo.strip("0"):
                continue
            self.versiones.setdefault(rel, set()).add(nuevo)
            # La fecha de una versión es la del commit normal que la escribió (el último, por si se
            # volvió a ella con un revert), no la del merge que la trajo a la rama: medido por el
            # verificador, con `-m` 144 ficheros del template tenían la fecha de un merge.
            destino = en_merge if merge else self.cuando
            destino[(rel, nuevo)] = max(destino.get((rel, nuevo), 0), ct)
        for clave, fecha in en_merge.items():            # versión nacida en un merge (conflicto)
            self.cuando.setdefault(clave, fecha)
        arbol = _git(self.base, "ls-tree", "-r", "--full-name", "HEAD", "--", ".") or ""
        for linea in arbol.splitlines():
            if "\t" in linea:
                meta, ruta = linea.split("\t", 1)
                if ruta.startswith(prefijo):
                    self.head[ruta[len(prefijo):]] = meta.split()[2]

    def fecha(self, rel: str, full: str) -> tuple[float, str]:
        """Cuándo se escribió la versión que hay en disco: el commit que la escribió si el disco es
        lo de HEAD; si está sin commitear (o no hay git), su mtime."""
        b = self.head.get(rel)
        if self.git and b and b == blob_id(full) and (rel, b) in self.cuando:
            return float(self.cuando[(rel, b)]), "commit"
        return os.path.getmtime(full), ("sin commitear" if self.git else "mtime, sin git")


def _partir_frontmatter(texto: str) -> tuple[str, str]:
    if texto.startswith("---\n"):
        fin = texto.find("\n---", 4)
        if fin != -1:
            salto = texto.find("\n", fin + 4)
            return texto[:fin + 4], ("" if salto == -1 else texto[salto + 1:])
    return "", texto


def solo_frontmatter(a: str, b: str) -> bool:
    """Mismo cuerpo, distinta cabecera YAML (o una de las dos sin cabecera). Es el ruido de T-109:
    medido el 17-10, 33-37 de unas 40 rules STALE por proyecto eran solo el `paths:` añadido."""
    try:
        with open(a, encoding="utf-8") as fa, open(b, encoding="utf-8") as fb:
            ta, tb = fa.read(), fb.read()
    except (OSError, UnicodeDecodeError):
        return False
    (cab_a, cuerpo_a), (cab_b, cuerpo_b) = _partir_frontmatter(ta), _partir_frontmatter(tb)
    return cab_a != cab_b and cuerpo_a.strip("\n").rstrip() == cuerpo_b.strip("\n").rstrip()


def _dia(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def clasificar(rel_tpl: str, tpl_full: str, h_tpl: Historia,
               rel_tgt: str, tgt_full: str, h_tgt: Historia) -> dict:
    """Un fichero que difiere entre template y proyecto → qué es y si se puede pisar.

    tipo: `atrasado` (versión vieja del template: se actualiza, y es lo ÚNICO que se pisa) ·
    `local_posterior` (el proyecto tuvo la versión actual del template y la cambió después: arreglo
    local más nuevo) · `divergente` (cambios propios y el proyecto nunca tuvo la versión actual del
    template: merge a mano) · `sin_historia` (el template no tiene git: no se puede saber si es un
    arreglo). Sin git en el proyecto, posterior/divergente se decide por fecha (mtime)."""
    b_tgt, b_tpl = blob_id(tgt_full), blob_id(tpl_full)
    f_tpl, o_tpl = h_tpl.fecha(rel_tpl, tpl_full)
    f_loc, o_loc = h_tgt.fecha(rel_tgt, tgt_full)
    propias = h_tgt.versiones.get(rel_tgt)
    if not h_tpl.git:
        tipo = "sin_historia"
    elif b_tgt in h_tpl.versiones.get(rel_tpl, set()):
        tipo = "atrasado"
    elif propias:                                     # el proyecto tiene historia de ese fichero
        tipo = "local_posterior" if b_tpl in propias else "divergente"
    else:
        tipo = "local_posterior" if f_loc > f_tpl else "divergente"
    return {"tipo": tipo, "solo_frontmatter": solo_frontmatter(tgt_full, tpl_full),
            "local": f"{_dia(f_loc)} ({o_loc})", "template": f"{_dia(f_tpl)} ({o_tpl})",
            "pisable": tipo == "atrasado"}


# ── DIVERGENCIAS-DELIBERADAS.md (MO-57) ─────────────────────────────────────────────────────────
# webs lo mantiene desde el 2026-08-25: una tabla con lo que diverge A PROPÓSITO y por qué. El diff
# no lo leía y lo seguía marcando STALE en cada pasada, con lo que la decisión se perdía en cada
# sincronización («perder la personalización dos veces», dice el propio fichero). Formato: filas de
# tabla Markdown cuya PRIMERA celda lleva la ruta entre comillas invertidas, relativa a `.claude/`;
# vale `{a,b}`, un comodín, una carpeta acabada en `/` o la ruta sin su categoría (`create-agent/
# SKILL.md` → `skills/create-agent/SKILL.md`).
DIVERGENCIAS = "DIVERGENCIAS-DELIBERADAS.md"


def _llaves(tok: str) -> list[str]:
    m = re.search(r"\{([^{}]*)\}", tok)
    if not m:
        return [tok]
    antes, despues = tok[:m.start()], tok[m.end():]
    return [x for alt in m.group(1).split(",") for x in _llaves(antes + alt + despues)]


def _casar(patron: str, conocidas: set[str]) -> set[str]:
    patron = patron.strip().removeprefix("./").removeprefix(".claude/")
    for cand in [patron] + [f"{c}/{patron}" for c in CATEGORIES]:
        if any(ch in cand for ch in "*?["):
            hit = {r for r in conocidas if fnmatch.fnmatchcase(r, cand)}
        elif cand.endswith("/"):
            hit = {r for r in conocidas if r.startswith(cand)}
        else:
            hit = {r for r in conocidas if r == cand or r.startswith(cand + "/")}
        if hit:
            return hit
    return set()


def divergencias_deliberadas(tgt: str, conocidas: set[str]) -> dict:
    """{'fichero', 'fecha', 'rutas': {rel: qué cambia}, 'filas': {token: [rels]},
    'sin_casar': [tokens]} o {} si el proyecto no tiene el fichero."""
    path = os.path.join(tgt, DIVERGENCIAS)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    titulo = next((l for l in texto.splitlines() if l.startswith("#")), "")
    m = re.search(r"\d{4}-\d{2}-\d{2}", titulo)
    rutas, filas, exactas, sin_casar = {}, {}, set(), []
    for linea in texto.splitlines():
        if not linea.lstrip().startswith("|"):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        previo = ""
        for tok in re.findall(r"`([^`]+)`", celdas[0] if celdas else ""):
            hit = set()
            alts: list[str] = []
            if "/" not in tok and "/" in previo:
                # `a/{x,y}/memory.md` · `trend.json`: el nombre suelto hereda la carpeta de antes
                # (y se prueba primero: si no, `README.md` casaría con el primero de cualquier sitio)
                alts = _llaves(previo.rsplit("/", 1)[0] + "/" + tok)
                for alt in alts:
                    hit |= _casar(alt, conocidas)
            if not hit:
                alts = _llaves(tok)
                for alt in alts:
                    hit |= _casar(alt, conocidas)
            # Nombrado EXACTO (no por carpeta ni comodín): solo así un fichero que falta en el
            # proyecto cuenta como borrado a propósito sin mirar su historia.
            for alt in alts:
                limpio = alt.strip().removeprefix("./").removeprefix(".claude/")
                exactas |= hit & ({limpio} | {f"{c}/{limpio}" for c in CATEGORIES})
            previo = tok if "/" in tok else previo
            if not hit:
                sin_casar.append(tok)
            filas.setdefault(tok, set()).update(hit)
            for rel in hit:
                rutas.setdefault(rel, (celdas[1] if len(celdas) > 1 else "")[:160])
    fecha = m.group(0) if m else time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(path)))
    return {"fichero": path, "fecha": fecha, "rutas": rutas, "exactas": exactas,
            "filas": {t: sorted(r) for t, r in filas.items()}, "sin_casar": sin_casar}


# ── Personalizar una rule en fichero aparte (MO-58) ─────────────────────────────────────────────
# EvoPreven/develop separó lo suyo en `rules/seguridad-evo.md` (con su `paths:`) y dejó
# `security.md` idéntica al template, que así «se actualiza sin merge». El resto del mismo
# proyecto son 16 piezas que se mergean a mano en cada actualización. La convención: lo propio en
# `rules/<rule>-<proyecto>.md`, o con otro nombre y `extiende: <rule>.md` en su frontmatter.
def proyecto_de(tgt: str) -> str:
    raiz = os.path.dirname(os.path.abspath(tgt)) if os.path.basename(tgt) == ".claude" else tgt
    nombre = os.path.basename(os.path.abspath(raiz)).lower()
    return re.sub(r"[^a-z0-9]+", "-", nombre).strip("-") or "proyecto"


def personaliza_a(rel: str, full: str, reglas_tpl: set[str]) -> str | None:
    """Si `rules/x-y.md` (LOCAL) personaliza una rule del template, cuál."""
    if not (rel.startswith("rules/") and rel.endswith(".md")):
        return None
    try:
        with open(full, encoding="utf-8") as f:
            cab, _ = _partir_frontmatter(f.read(8192))
    except (OSError, UnicodeDecodeError):
        cab = ""
    m = re.search(r"^extiende:\s*[\"']?([\w./-]+?)[\"']?\s*$", cab, re.M)
    if m:
        dest = m.group(1).removeprefix(".claude/")
        dest = dest if dest.startswith("rules/") else f"rules/{dest}"
        return dest if dest in reglas_tpl else None
    stem = rel[len("rules/"):-3]
    candidatos = [r for r in reglas_tpl if stem.startswith(r[len("rules/"):-3] + "-")]
    return max(candidatos, key=len) if candidatos else None


def sin_inventariar(tgt: str) -> list[str]:
    try:
        return sorted(d + "/" for d in os.listdir(tgt) if os.path.isdir(os.path.join(tgt, d))
                      and d not in CATEGORIES and d not in CARPETAS_NO_PIEZA)
    except OSError:
        return []


def podadas(tgt_root):
    """Lo que el PROYECTO archivó a propósito: su cementerio, no el nuestro (improvements #21).

    POR QUÉ HACE FALTA. `retiradas()` solo conoce las bajas del template. Las del proyecto eran
    invisibles, así que una pieza podada allí con aprobación del Usuario salía como MISSING y el
    flujo canónico proponía reinstalarla: deshacer su decisión. Medido dos veces: elvion
    (2026-08-23, 25 de 107 «missing») y aquila-erp (2026-10-03, 20 de 23 «missing antiguos» eran
    su poda del 2026-09-30).

    Devuelve (unidades, nombres): la unidad exacta cuando el cementerio conserva la estructura
    (`_archive/2026-09-30-poda/agents/x.md` → `agents/x.md`), y el nombre como respaldo para los
    cementerios planos (`skills/_retiradas/x/`)."""
    unidades, nombres = set(), set()
    raices = []
    for dirpath, dirnames, _ in os.walk(tgt_root):
        rel = os.path.relpath(dirpath, tgt_root)
        if rel.split(os.sep)[0] in ("node_modules", ".git"):
            dirnames[:] = []
            continue
        for d in list(dirnames):
            if d in CEMENTERIOS:
                raices.append(os.path.join(dirpath, d))
                dirnames.remove(d)
    for raiz in raices:
        for dirpath, dirnames, filenames in os.walk(raiz):
            for d in dirnames:
                nombres.add(d)
            for f in filenames:
                full = os.path.relpath(os.path.join(dirpath, f), raiz).split(os.sep)
                stem, ext = os.path.splitext(f)
                if ext in (".md", ".py", ".js", ".sh", ".yaml", ".json") and stem.lower() != "readme":
                    nombres.add(stem)
                # la ruta a partir de la primera carpeta-categoría que aparezca dentro
                for i, parte in enumerate(full[:-1]):
                    if parte in CATEGORIES:
                        unidades.add(unit_of("/".join(full[i:])))
                        break
    return unidades, {n for n in nombres if len(n) > 4}


def analizar(tpl: str, tgt: str, only_core: bool = False) -> dict:
    """Todo lo que `--json` imprime. El propagador del template lo importa: una sola
    clasificación para medir y para copiar."""
    tpl_inv, tgt_inv = inventory(tpl), inventory(tgt)
    div = divergencias_deliberadas(tgt, set(tpl_inv) | set(tgt_inv))
    declaradas = div.get("rutas", {})
    fin_declaracion = (time.mktime(time.strptime(div["fecha"], "%Y-%m-%d")) + 86400) if div else 0
    missing, stale, frontm, posterior, divergente, deliberada, semilla = {}, {}, {}, {}, {}, {}, {}
    sin_hist: dict = {}
    detalle, ya_iguales = {}, []
    hist: dict[str, Historia] = {}

    def h(cual: str) -> Historia:                    # git solo si hay algo distinto que juzgar
        if cual not in hist:
            hist[cual] = Historia(tpl if cual == "tpl" else tgt)
        return hist[cual]

    for rel, sha_tpl in tpl_inv.items():
        if only_core and not in_core(rel):
            continue
        falta = rel not in tgt_inv
        if not falta and (tgt_inv[rel] == sha_tpl or is_personal(rel)):
            continue
        # También un BORRADO declarado (sin esto, la fila casaba y el fichero volvía como MISSING),
        # pero solo si la fila lo nombra o el proyecto lo tuvo: un fichero NUEVO del template dentro
        # de una carpeta declarada no se borró, nunca llegó (verificador de la 1.09, 2.ª pasada).
        borrado = falta and (rel in div.get("exactas", set()) or bool(h("tgt").versiones.get(rel)))
        if rel in declaradas and (not falta or borrado) and not (falta and no_se_siembra(rel)):
            f_tpl, _ = h("tpl").fecha(rel, os.path.join(tpl, rel))
            detalle[rel] = {"tipo": "deliberada", "pisable": False,
                            "que": declaradas[rel] + (" [borrado en el proyecto]" if falta else ""),
                            "template": _dia(f_tpl), "declarada": div["fecha"],
                            "revisar": f_tpl > fin_declaracion}
            deliberada.setdefault(unit_of(rel), []).append(rel)
            continue
        if falta:
            destino = semilla if no_se_siembra(rel) else missing
            destino.setdefault(unit_of(rel), []).append(rel)
            continue
        c = clasificar(rel, os.path.join(tpl, rel), h("tpl"), rel, os.path.join(tgt, rel), h("tgt"))
        detalle[rel] = c
        if c["pisable"]:
            destino = frontm if c["solo_frontmatter"] else stale
        else:
            destino = {"local_posterior": posterior, "divergente": divergente}.get(c["tipo"], sin_hist)
        destino.setdefault(unit_of(rel), []).append(rel)

    # Una fila sobra cuando TODO lo que declara ya es igual al template (no basta un fichero: una
    # carpeta declarada con 16 iguales y 2 distintos sigue haciendo falta).
    for tok, rels in (div.get("filas") or {}).items():
        comparables = [r for r in rels if r in tpl_inv and r in tgt_inv and not is_personal(r)]
        if comparables and all(tpl_inv[r] == tgt_inv[r] for r in comparables):
            ya_iguales.append(tok)

    # Lo que el proyecto podó NO es «missing» (D-12): sale aparte para que nadie lo reinstale.
    pod_unid, pod_nombres = podadas(os.path.dirname(os.path.abspath(tgt)))
    podado = {}
    for bolsa in (missing, semilla):
        for u in list(bolsa):
            nombre = os.path.splitext(os.path.basename(u.rstrip("/")))[0]
            if u in pod_unid or nombre in pod_nombres:
                podado.setdefault(u, []).extend(bolsa.pop(u))
    podados = {rel for rels in podado.values() for rel in rels}

    fuera = retiradas(tpl)
    local, retirado = {}, {}
    for rel in tgt_inv:
        if rel not in tpl_inv and not is_personal(rel) and not only_core:
            u = unit_of(rel)
            # el nombre de la unidad (agents/x.md -> x · skills/x/ -> x) contra lo archivado
            nombre = os.path.splitext(os.path.basename(u.rstrip("/")))[0]
            destino = retirado if (nombre in fuera and len(nombre) > 4) else local
            destino.setdefault(u, []).append(rel)

    # MO-58: una rule con cambios propios → proponer el fichero aparte; uno aparte → reconocerlo
    proyecto = proyecto_de(tgt)
    aparte = {rel: f"rules/{rel[len('rules/'):-3]}-{proyecto}.md"
              for grupo in (posterior, divergente, deliberada) for fs in grupo.values() for rel in fs
              if rel.startswith("rules/") and rel.endswith(".md") and rel in tgt_inv}
    reglas_tpl = {r for r in tpl_inv if r.startswith("rules/") and r.endswith(".md")}
    personalizaciones = {}
    for fs in local.values():
        for rel in fs:
            base = personaliza_a(rel, os.path.join(tgt, rel), reglas_tpl)
            if base:
                personalizaciones[rel] = base

    ch = core_hash(tpl_inv)
    cv_path = os.path.join(tgt, "CORE_VERSION")
    cv = open(cv_path).read().strip() if os.path.exists(cv_path) else None
    # el estado NO se fía solo del marcador: contrasta con los ficheros reales (un CORE_VERSION
    # correcto con ficheros core ausentes/stale es un marcador mentiroso, no un estado). Una
    # divergencia DELIBERADA no es un hueco: es una decisión escrita del proyecto.
    # Lo que el proyecto PODÓ no es core que falte (D-19): contarlo dejaba a un proyecto podado
    # «INCOMPLETO» para siempre (aquila-erp, 10 patrones archivados el 2026-09-30).
    core_gap = sum(1 for rel in tpl_inv if in_core(rel) and rel not in tgt_inv
                   and rel not in declaradas and rel not in podados) \
        + sum(1 for rel, sha_tpl in tpl_inv.items() if in_core(rel)
              and tgt_inv.get(rel) not in (None, sha_tpl)
              and not is_personal(rel) and rel not in declaradas)
    core_delib = sum(1 for rel in detalle if in_core(rel) and detalle[rel]["tipo"] == "deliberada")
    if cv == ch and core_gap == 0:
        core_state = "al día"
    elif core_gap:
        core_state = f"INCOMPLETO/STALE ({core_gap} ficheros core difieren del template)" + ("" if cv == ch else f" · CORE_VERSION={cv or 'ausente'}")
    else:
        core_state = "desactualizado (CORE_VERSION=%s ≠ %s)" % (cv, ch) if cv else "sin CORE_VERSION (pre-TPL-1 o nunca sincronizado)"
    if core_delib:
        core_state += f" · {core_delib} divergencia(s) deliberada(s) en el CORE"

    return {"template": tpl, "target": tgt, "core_hash": ch, "core_state": core_state,
            "missing": missing, "stale": stale, "solo_frontmatter": frontm,
            "local_posterior": posterior, "divergente": divergente, "deliberada": deliberada,
            "sin_historia": sin_hist,
            "local": local, "retirado": retirado, "semilla": semilla, "podado": podado,
            "sin_inventariar": [] if only_core else sin_inventariar(tgt),
            "detalle": detalle,
            "divergencias": ({k: div[k] for k in ("fichero", "fecha", "filas", "sin_casar")}
                             | {"ya_iguales": sorted(ya_iguales)}) if div else {},
            "personalizar_aparte": aparte, "personalizaciones": personalizaciones,
            "historia": {k: v.git for k, v in (("template", hist.get("tpl")),
                                               ("proyecto", hist.get("tgt"))) if v}}


def main():
    args = sys.argv[1:]
    tpl_root = os.environ.get("TL_TEMPLATE_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    positional, flags, i = [], set(), 0
    while i < len(args):
        if args[i] == "--template" and i + 1 < len(args):
            tpl_root = args[i + 1]
            i += 2
        elif args[i].startswith("--"):
            flags.add(args[i])
            i += 1
        else:
            positional.append(args[i])
            i += 1
    tpl = claude_dir(tpl_root)
    if not os.path.isdir(tpl):
        print(f"ERROR: template no encontrado en {tpl} — pasa --template o TL_TEMPLATE_DIR", file=sys.stderr)
        sys.exit(2)

    if "--core-hash" in flags:
        print(core_hash(inventory(tpl)))
        return

    targets = positional
    if not targets:
        sys.exit(__doc__)
    tgt = claude_dir(targets[0])
    if not os.path.isdir(tgt):
        sys.exit(f"ERROR: {tgt} no existe (¿es un proyecto con .claude/?)")
    # El instrumento que no puede medir ABORTA (rules/verification.md). Sin --template ni
    # TL_TEMPLATE_DIR, el template por defecto es el repo donde vive ESTE script — y en un proyecto
    # derivado eso es el propio proyecto: se comparaba consigo mismo y decía «CORE: al día», exit 0.
    # Medido el 2026-09-28 en aiatech-web.
    if os.path.realpath(tpl) == os.path.realpath(tgt):
        print(f"ERROR: template y proyecto son el MISMO directorio ({os.path.realpath(tgt)}).\n"
              "  Compararlo consigo mismo siempre sale «al día»: eso no es un resultado.\n"
              "  Pasa --template <ruta-del-template> o exporta TL_TEMPLATE_DIR.", file=sys.stderr)
        sys.exit(2)

    only_core = "--core" in flags
    d = analizar(tpl, tgt, only_core)
    if "--json" in flags:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return

    def show(title, units, mark, fechas=False):
        print(f"\n{title} ({len(units)} unidades)")
        for u in sorted(units):
            fs = units[u]
            print(f"  {mark} {u}" + (f"  ({len(fs)} ficheros)" if u.endswith("/") and len(fs) > 1 else ""))
            if not fechas:
                continue
            for rel in sorted(fs):
                c = d["detalle"][rel]
                if c["tipo"] == "deliberada":
                    aviso = (f"  ⚠ el template lo cambió el {c['template']}, después de "
                             f"declararla ({c['declarada']}): re-aplica la divergencia a mano"
                             ) if c["revisar"] else ""
                    print(f"      {rel}: {c['que'][:90]}{aviso}")
                else:
                    fm = " · solo frontmatter" if c["solo_frontmatter"] else ""
                    print(f"      {rel}: proyecto {c['local']} · template {c['template']}{fm}")
                if rel in d["personalizar_aparte"]:
                    print(f"        → MO-58: deja {rel} como el template y pasa lo propio a "
                          f"{d['personalizar_aparte'][rel]} (con su paths:)")

    print(f"template: {tpl}\ntarget:   {tgt}\nCORE:     {d['core_state']}")
    show("MISSING — en template, falta en el proyecto", d["missing"], "+")
    show("STALE — el proyecto tiene una versión VIEJA del template, sin tocar: se actualiza",
         d["stale"], "≠")
    show("SOLO FRONTMATTER — mismo cuerpo, solo cambia la cabecera (paths:…): se actualiza sin "
         "leer el cuerpo", d["solo_frontmatter"], "≈")
    if d["podado"]:
        show("PODADO — el proyecto lo archivó a propósito: NO se copia (mira su _archive/…/README.md; "
             "traerlo de vuelta es deshacer una decisión suya)", d["podado"], "⊘")
    if d["local_posterior"]:
        show("LOCAL POSTERIOR — arreglo del proyecto MÁS NUEVO que el template, que nunca tuvo "
             "esa versión: NO se pisa (candidato a cosechar en improvements_tl.md)",
             d["local_posterior"], "▲", True)
    if d["divergente"]:
        show("DIVERGENTE — cambios propios y el template se movió después: NO se pisa, "
             "merge a mano", d["divergente"], "⇄", True)
    if d["deliberada"]:
        show(f"DELIBERADA — declarada en {DIVERGENCIAS}: NO se pisa", d["deliberada"], "◆", True)
    if d["sin_historia"]:
        show("SIN HISTORIA — el template no tiene git y no se puede saber si es un arreglo del "
             "proyecto: NO se pisa (propaga desde un template con git)", d["sin_historia"], "?", True)
    dv = d["divergencias"]
    if dv.get("sin_casar"):
        print(f"  ⚠ filas de {DIVERGENCIAS} que no casan con ningún fichero: "
              + ", ".join(f"`{t}`" for t in dv["sin_casar"]))
    if dv.get("ya_iguales"):
        print(f"  ⚠ filas declaradas que ya son IGUALES al template (bórralas con fecha y motivo): "
              + ", ".join(f"`{t}`" for t in dv["ya_iguales"]))
    if d["semilla"]:
        show("NO SE SIEMBRA — falta, y se crea VACÍO en destino: NO se copia del template "
             "(lleva mediciones de ESTE repo y serían falsas allí)", d["semilla"], "○")
    if not only_core:
        show("LOCAL — solo del proyecto (no se toca)", d["local"], "·")
        for rel, base in sorted(d["personalizaciones"].items()):
            print(f"      {rel}: personalización de {base} (MO-58) — la del template se "
                  f"actualiza sin merge")
        show("RETIRADO — el template lo jubiló y este proyecto lo conserva "
             "(NO es local: mira _archive/<fecha>/README.md y decide si se retira aquí también)",
             d["retirado"], "✗")
        if d["sin_inventariar"]:
            print(f"\nSIN INVENTARIAR — carpetas de .claude/ que este diff no mira ni compara "
                  f"({len(d['sin_inventariar'])}): " + " ".join(d["sin_inventariar"]))
    if d["historia"] and not all(d["historia"].values()):
        sin = [k for k, v in d["historia"].items() if not v]
        print(f"\n⚠ sin historia git en: {', '.join(sin)} — lo distinto se juzga solo por "
              f"fecha (mtime)")
    if d["semilla"]:
        print("\nLos ○ se crean vacíos, con su cabecera, y los rellena el proyecto al medirse.")
    print("\nPara un STALE: diff -ru <target>/.claude/<unidad> <template>/.claude/<unidad>")
    print("Al aplicar el CORE completo: echo %s > <target>/.claude/CORE_VERSION" % d["core_hash"])


if __name__ == "__main__":
    main()
