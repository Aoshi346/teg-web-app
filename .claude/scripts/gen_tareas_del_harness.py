#!/usr/bin/env python3
"""Qué tiene que HACER un proyecto para cumplir con el harness que se le acaba de configurar.

EL HUECO QUE CIERRA
-------------------
`update-agent` copia ficheros y termina. El proyecto se queda con patrones, comprobadores y hooks
nuevos **y sin saber que tiene que hacer algo con ellos**. Medido el 2026-08-27 en
`elvion-autoparte-demo`: recibio los 43 documentos del molde y los 3 comprobadores, y tenia UN
solo baseline — o sea, dos de los tres comprobadores no se habian corrido nunca. Tener el patron
no es cumplirlo.

Peticion del Usuario: *"cuando se actualiza un sistema de agentes de un proyecto, deberia haber un
.md con todas las tareas que tiene que ejecutar el proyecto para que cumpla con todo lo que se ha
configurado"*.

POR QUE ES UN SCRIPT Y NO UN PASO ESCRITO EN LA SKILL
-----------------------------------------------------
`rules/layer-decision.md` pregunta 1: si el coste de que se ignore es alto, baja de capa. Un paso
en la skill se olvida; un script se ejecuta. Y lo que detecta esta MEDIDO en el proyecto, no
declarado en una lista que envejece.

USO
    python3 gen_tareas_del_harness.py <ruta-del-proyecto> [--escribir] [--sondear]

Sin `--escribir` solo informa. Con `--escribir` genera `.docs/TAREAS-DEL-HARNESS.md` y anade las
tareas al `pending-tasks.md` del plan activo, que es lo que el hook reinyecta cada turno. Con
`--sondear`, la tarea de trazas pregunta ademas a la URL LOCAL declarada si responde (sin claves).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path


class Tarea:
    def __init__(self, ident: str, titulo: str, porque: str, como: str, aprueba: bool = False):
        self.id, self.titulo, self.porque, self.como, self.aprueba = ident, titulo, porque, como, aprueba


def _lee(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _entradas_de_mejoras(texto: str) -> int:
    """Entradas de `improvements_tl.md`: secciones `## ` y filas de tabla que empiezan por fecha."""
    return (len(re.findall(r"^## ", texto, re.M))
            + len(re.findall(r"^\|\s*\d{4}-\d{2}-\d{2}\b", texto, re.M)))


def _registrados(cl: Path, hooks: set[str], settings: str) -> set[str]:
    """Los hooks que salen en el `command` de algun hook de settings.json / settings.local.json.

    No vale que el nombre salga en cualquier parte del fichero: un `_comment` que lo declara «no
    registrado a proposito» no lo hace correr, y lo que el lance no esta envuelto por nadie. Si el
    JSON no se puede leer, se cae a buscar el nombre en el texto (lo de antes)."""
    comandos = []
    for nombre in ("settings.json", "settings.local.json"):
        texto = _lee(cl / nombre)
        if not texto:
            continue
        try:
            d = json.loads(texto)
        except ValueError:
            return {h for h in hooks if h in settings}
        for grupos in (d.get("hooks") or {}).values():
            for g in grupos if isinstance(grupos, list) else []:
                for h in (g.get("hooks") or []) if isinstance(g, dict) else []:
                    if isinstance(h, dict):
                        comandos.append(" ".join([str(h.get("command", ""))] + [str(x) for x in h.get("args") or []]))
    return {h for h in hooks if any(h in c for c in comandos)}


def _envueltos(cl: Path, hooks: set[str], registrados: set[str]) -> set[str]:
    """Los hooks que otro hook registrado LANZA: estan registrados a traves de su envoltorio.

    En develop, `check-ram.sh` salia «sin registrar» y lo invoca `gate-ram-pytest.sh`, que si lo
    esta (es su envoltorio: filtra el comando y traduce el exit 1 a 2). Lo mismo en el template.
    Cuenta solo una invocacion de verdad: el hook es la palabra que se ejecuta (`"$DIR/…/x.sh"`,
    tambien dentro de `$( … )` o detras de `if`/`!`) o el argumento de `bash`/`sh`/`source`/`.`/
    `exec`, en una linea que no es comentario; y lo mismo a traves de una variable
    (`H=…/x.sh; bash "$H"`). No cuenta que el nombre salga en un texto: un `echo`/`printf`, un
    `[ -f …/x.sh ]` o el `--explain` de check-ram.sh, que nombra pre-write-guard.sh, no lo lanzan.
    Se sigue la cadena (un envuelto que a su vez lanza otro).
    """
    LANZA = {"bash", "sh", "source", ".", "exec", "zsh", "dash"}
    NO_LANZA = {"echo", "printf", "test", "[", "[[", "grep", "cat", "ls", "chmod", "cp", "mv", "sed", "rm"}

    def trozos(linea: str) -> list[list[str]]:
        """Los comandos simples de una linea, como palabras (sin comillas)."""
        try:
            lex = shlex.shlex(linea, posix=True, punctuation_chars=";&|(){}")
            lex.whitespace_split = True
            lex.commenters = ""
            toks = list(lex)
        except ValueError:
            toks = linea.split()
        out, seg = [], []
        for t in toks:
            if t and set(t) <= set(";&|(){}"):
                out.append(seg)
                seg = []
            else:
                seg.append(t)
        out.append(seg)
        return [x for x in out if x]

    ENVOLTORIOS = {"timeout", "nohup", "sudo", "env", "nice", "exec", "command", "setsid", "stdbuf"}

    def nucleo(seg: list[str]) -> tuple[list[str], dict]:
        """Quita palabras reservadas, asignaciones y envoltorios (`timeout 5`, `nohup`, `sudo -u x`…);
        devuelve lo que se ejecuta y las asignaciones."""
        asig = {}
        while seg:
            m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", seg[0])
            if seg[0] in ("if", "then", "else", "elif", "do", "while", "until", "!", "$", "time") or m:
                if m:
                    asig[m.group(1)] = m.group(2)
                seg = seg[1:]
            elif os.path.basename(seg[0]) in ENVOLTORIOS:
                seg = seg[1:]
                while seg and (seg[0].startswith("-") or re.fullmatch(r"[\d.]+[smhd]?", seg[0])
                               or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", seg[0])):
                    seg = seg[1:]
            else:
                break
        return seg, asig

    def sin_heredocs(lineas: list[str]) -> list[str]:
        """El cuerpo de un heredoc es texto (una ayuda que dice «bash …/x.sh» no lo lanza)."""
        out, fin = [], None
        for linea in lineas:
            if fin is not None:
                if linea.strip() == fin:
                    fin = None
                continue
            out.append(linea)
            m = re.search(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", linea)
            if m:
                fin = m.group(2)
        return out

    def lanzados(nombre: str) -> set[str]:
        codigo = [l for l in sin_heredocs(_lee(cl / "hooks" / nombre).splitlines())
                  if not l.lstrip().startswith("#")]
        variables: dict[str, str] = {}
        ejecutado: list[str] = []          # las palabras que se ejecutan como fichero
        for linea in codigo:
            for seg in trozos(linea.replace("$(", " $ ( ").replace("`", " ")):
                seg, asig = nucleo(seg)
                variables.update(asig)
                if not seg or os.path.basename(seg[0]) in NO_LANZA:
                    continue
                prog = os.path.basename(seg[0])
                if prog in LANZA:
                    args = [a for a in seg[1:] if not a.startswith("-")]
                    if args:
                        ejecutado.append(args[0])
                else:
                    ejecutado.append(seg[0])
        def expande(palabra: str) -> str:
            return re.sub(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", lambda m: variables.get(m.group(1), m.group(0)),
                          palabra)
        rutas = [expande(expande(p)) for p in ejecutado]
        return {h for h in hooks if h != nombre and any(r == h or r.endswith("/" + h) for r in rutas)}

    vistos: set[str] = set()
    pendientes = sorted(registrados)
    while pendientes:
        for h in lanzados(pendientes.pop()):
            if h not in vistos and h not in registrados:
                vistos.add(h)
                pendientes.append(h)
    return vistos


# --- Trazas: ¿la plataforma ENVÍA, o solo está nombrada? (MO-66, sub-ola 2.20) ---------------
#
# Antes bastaba con que «langfuse» saliera en las dependencias O en el código: un `LANGFUSE_HOST`
# en settings (risk-couple, sin ningún SDK) daba la tarea por cumplida, y un import de la v2
# (`langfuse.callback`, que con el SDK ≥3 no existe) también. Ahora se mira qué hay de verdad: SDK
# declarado, import que existe, variable buena y alguien que compruebe que la plataforma responde.
_FUERA = {".claude", ".docs", ".venv", "venv", "node_modules", "__pycache__", ".git",
          "site-packages", "dist", "build", "worktrees", "_archive"}
# La v2 del SDK: `langfuse.callback` (el handler de LangChain) y `langfuse.decorators` (`observe`,
# `langfuse_context`); en el SDK ≥3 no existen y el import falla o no traza.
_IMPORT_V2 = re.compile(r"^\s*(?:from\s+langfuse\.(?:callback|decorators)\s+import|"
                        r"import\s+langfuse\.(?:callback|decorators))", re.M)
_APAGADA = re.compile(r"AGENT_TRACING['\"]?\s*(?:[=:]|,\s*default\s*=)\s*['\"]?off\b", re.I)
_IMPORT_OK = re.compile(r"^\s*from\s+langfuse(?:\.langchain)?\s+import\s+[^\n]*"
                        r"(?:CallbackHandler|get_client|Langfuse|observe)", re.M)
_SALUD = re.compile(r"auth_check\s*\(|/api/public/health|langfuse_health")
_URL = re.compile(r"LANGFUSE_(?:BASE_URL|HOST)['\"]?\s*[,=:]\s*"
                  r"(?:[A-Za-z_.]+\([^)]*?default\s*=\s*)?['\"]?(https?://[^'\"\s),]+)")
_COMPROBAR = (
    'python -c "from langfuse import get_client; assert get_client().auth_check()"  # claves\n'
    '   curl -fsS "$LANGFUSE_BASE_URL/api/public/health"                      # responde')


def _ficheros(raiz: Path, nombres: tuple[str, ...] = (), sufijos: tuple[str, ...] = (),
              hondo: int = 6):
    """Recorre podando `_FUERA` (rglob no poda: en un repo con node_modules tardaba segundos).
    Un nombre que acaba en «-» es un prefijo (`requirements-` casa con `requirements-obs.txt`)."""
    prefijos = tuple(x for x in nombres if x.endswith("-"))
    for dirpath, dirnames, filenames in os.walk(raiz):
        nivel = len(Path(dirpath).relative_to(raiz).parts)
        dirnames[:] = [] if nivel >= hondo else [d for d in dirnames if d not in _FUERA]
        for n in filenames:
            if n in nombres or Path(n).suffix in sufijos or (prefijos and n.startswith(prefijos)):
                yield Path(dirpath) / n


_CI_DIRS = {".github", ".gitlab", ".circleci", "ci", ".buildkite"}
_CI_NOMBRES = {".gitlab-ci.yml", "bitbucket-pipelines.yml", "azure-pipelines.yml", ".travis.yml",
               "Jenkinsfile", ".drone.yml"}


def _de_ci(f: Path, raiz: Path) -> bool:
    """¿Es configuración de CI o de tests (no de la aplicación)?"""
    return (any(c in _CI_DIRS for c in f.relative_to(raiz).parts[:-1]) or f.name in _CI_NOMBRES
            or bool(re.search(r"(^|[._-])(ci|tests?|testing)([._-]|$)", f.name.lower())))


def diagnostico_trazas(raiz: Path, sondear: bool = False) -> dict:
    """Lo medido sobre trazas: SDK, imports, variables, comprobación de salud y, con `sondear`, si
    la URL LOCAL declarada contesta (`/api/public/health`, sin claves). Nunca lee `.env`."""
    deps = list(_ficheros(raiz, ("pyproject.toml", "Pipfile", "package.json", "requirements.txt",
                                 "requirements-", "setup.py", "setup.cfg"), (), 3))
    deps += [f for f in _ficheros(raiz, (), (".txt", ".in"), 4) if f.parent.name == "requirements"]

    def declarada(pl: str) -> list[str]:
        return sorted({str(f.relative_to(raiz)) for f in deps
                       if re.search(rf"(^|[\s\"'@/]){pl}\b", _lee(f), re.I | re.M)})

    sdk = {pl: declarada(pl) for pl in ("langfuse", "langsmith")}
    # langsmith llega como dependencia de langchain-core: con langchain declarado, el SDK está.
    langchain = declarada("langchain") + declarada("langchain-core") + declarada("langgraph")
    codigo, config = [], []
    sufijos = (".py", ".ts", ".js", ".yml", ".yaml")
    for f in _ficheros(raiz, (".env.example", ".env.sample"), sufijos):
        if any(t in f.parts for t in ("tests", "test")) or f.name.startswith(("test_", "conftest")):
            continue  # los conftest APAGAN las trazas: contarlos daba «hay trazas»
        t = _lee(f)
        if any(x in t for x in ("LANGFUSE", "LANGSMITH", "LANGCHAIN_TRACING", "langfuse",
                                "AGENT_TRACING")):
            (codigo if f.suffix in (".py", ".ts", ".js") else config).append((f, t))

    def rel(pares: list) -> list[str]:
        return sorted({str(f.relative_to(raiz)) for f, _ in pares})

    todo = codigo + config
    if not sdk["langsmith"] and langchain and any(
            re.search(r"LANGCHAIN_TRACING|LANGSMITH_TRACING", t) for _, t in todo):
        sdk["langsmith"] = [f"{x} (vía langchain)" for x in sorted(set(langchain))]
    d = {
        "sdk": sdk,
        # Solo cuenta lo que configura la aplicación: un `AGENT_TRACING: off` del CI o de un
        # compose de tests no apaga las trazas de producción (verificador 2.20, N9).
        "apagada": rel([x for x in todo if _APAGADA.search(x[1]) and not _de_ci(x[0], raiz)]),
        "nombrada_en": rel([x for x in todo
                            if re.search(r"LANGFUSE_|LANGSMITH_|LANGCHAIN_TRACING", x[1])]),
        "import_v2": rel([x for x in codigo if _IMPORT_V2.search(x[1])]),
        "import_ok": rel([x for x in codigo if _IMPORT_OK.search(x[1])]),
        "var_host": rel([x for x in todo if "LANGFUSE_HOST" in x[1]]),
        "var_base": rel([x for x in todo if "LANGFUSE_BASE_URL" in x[1]]),
        "salud": rel([x for x in codigo if _SALUD.search(x[1])]),
        "url": next((m.group(1) for _, t in todo for m in [_URL.search(t)] if m), None),
        "sondeo": None,
    }
    if sondear and d["url"] and re.match(r"https?://(127\.0\.0\.1|localhost)[:/]", d["url"]):
        import urllib.request
        salud = d["url"].rstrip("/") + "/api/public/health"
        try:
            with urllib.request.urlopen(salud, timeout=3) as r:
                d["sondeo"] = f"{salud} → {r.status} {r.read(120).decode(errors='replace')}"
        except OSError as e:
            d["sondeo"] = f"{salud} → sin respuesta ({e})"
    return d


def _tareas_trazas(raiz: Path, cl: Path, sondear: bool) -> list[Tarea]:
    d = diagnostico_trazas(raiz, sondear)
    hay_sdk = bool(d["sdk"]["langfuse"] or d["sdk"]["langsmith"])
    sondeo = f"\n   Sondeo: {d['sondeo']}" if d["sondeo"] else ""
    if not hay_sdk and d["apagada"]:
        return []  # `AGENT_TRACING=off` declarado: «off es un valor válido» (patrón §4)
    if d["nombrada_en"] and not hay_sdk:
        return [Tarea(
            "HAR-TRAZAS-MUDO",
            "Trazas configuradas pero SIN envío: hay variables de Langfuse/LangSmith y ningún SDK",
            f"Se nombran en {', '.join(d['nombrada_en'][:4])} y ningún fichero de dependencias "
            "declara langfuse ni langsmith: un destino configurado al que nadie manda nada. Pasaba "
            "el check anterior porque buscaba la palabra en el código.",
            "O se declara `AGENT_TRACING=off` (y, si se quiere, se quita la configuración), o se "
            "instala el SDK y se comprueba que envía (§4 de "
            "`patterns/stack/agente-observabilidad.md`):\n   " + _COMPROBAR + sondeo,
            aprueba=True)]
    if hay_sdk and d["sdk"]["langfuse"]:
        fallos = []
        if d["import_v2"]:
            fallos.append(f"import de la v2 (`langfuse.callback` o `langfuse.decorators`, que no "
                          f"existen en el SDK ≥3) en "
                          f"{', '.join(d['import_v2'][:4])}: el handler no se crea y no sale "
                          "ninguna traza")
        if d["var_host"] and not d["var_base"]:
            fallos.append(f"solo `LANGFUSE_HOST` ({', '.join(d['var_host'][:3])}); la variable "
                          "del SDK actual es `LANGFUSE_BASE_URL`")
        if not d["salud"]:
            fallos.append("nadie comprueba al arrancar que la plataforma responde (ni "
                          "`auth_check()` ni `/api/public/health`): con una clave mala se pierden "
                          "trazas en silencio")
        if fallos:
            return [Tarea(
                "HAR-TRAZAS-ENVIO",
                f"El SDK de trazas está, pero {len(fallos)} cosa(s) impiden saber que envía",
                " · ".join(fallos),
                "Arreglar lo de arriba y comprobarlo con:\n   " + _COMPROBAR + sondeo)]
        return []
    if not hay_sdk and (cl / "patterns" / "stack" / "agente-observabilidad.md").is_file():
        return [Tarea(
            "HAR-TRAZAS",
            "Montar la plataforma de trazas (Langfuse / LangSmith)",
            "El patron `agente-observabilidad.md` esta en el proyecto y no hay ni langfuse ni "
            "langsmith, ni en dependencias ni configurados. La traza propia cubre 'que hizo'; "
            "falta 'cuanto costo' y poder mirar la conversacion de ayer sin abrir un log.",
            "El reparto y la variable `AGENT_TRACING` estan en el §4 del patron. Se declara "
            "cual esta activa, NUNCA se deduce de si hay API key.",
            aprueba=True)]
    return []

def detecta(raiz: Path, sondear: bool = False) -> list[Tarea]:
    """Lo que el proyecto TIENE configurado y todavia no ha ejecutado. Todo medido en disco."""
    t: list[Tarea] = []
    cl = raiz / ".claude"
    if not cl.is_dir():
        return t

    # 1. Comprobadores presentes sin baseline congelado
    comprobadores = sorted((cl / "patterns" / "stack").glob("pattern_check_*.py"))
    baselines = {p.stem for p in (cl / "patterns" / "baseline").glob("*.json")}
    # OJO: el baseline se llama por REGLA (`ag-tool-sin-schema`), no por comprobador
    # (`pattern_check_agente`). Buscar el nombre del comprobador dentro del nombre del
    # baseline no casa NUNCA, asi que decia "sin baseline" con 13 congelados delante.
    # El puente es el prefijo de dos letras que usan las reglas de cada capa.
    PREFIJO = {"agente": "ag-", "backend": "be-", "frontend": "fe-"}
    sin_correr = [c for c in comprobadores
                  if not any(b.startswith(PREFIJO.get(c.stem.replace("pattern_check_", ""), "\0"))
                             for b in baselines)]
    if sin_correr:
        nombres = ", ".join(c.name for c in sin_correr)
        t.append(Tarea(
            "HAR-BASELINE",
            f"Correr {len(sin_correr)} comprobador(es) y congelar su baseline",
            f"Estan en disco y no hay baseline suyo: {nombres}. Tener el patron no es cumplirlo, "
            f"y sin medirlo no se sabe cuanta deuda hay.",
            "python3 .claude/patterns/stack/<comprobador>.py --all --json > /tmp/m.json && "
            "python3 .claude/scripts/pattern_baseline.py freeze --from /tmp/m.json\n"
            "   ⚠️ CONGELA ANTES DE EXIGIR NADA (rules/refactor-progresivo.md §4): con el gate "
            "encendido y sin baseline salen cientos de avisos sobre codigo que funciona, y se "
            "aprende a ignorarlos — peor que no tener gate.",
        ))

    # 2. Trazas: que la plataforma ENVÍE, no que la palabra salga en el código (MO-66)
    t.extend(_tareas_trazas(raiz, cl, sondear))

    # 3. Hooks copiados y no registrados en settings.json
    #
    # ⚠️ NO todos los .sh de hooks/ son hooks de Claude Code: algunos se enganchan a GIT
    # (`ln -s .claude/hooks/pattern-check.sh .git/hooks/pre-push`). Marcarlos como "sin
    # registrar" es un falso positivo — medido el 2026-08-27 en elvion-autoparte-demo, donde
    # los 2 unicos "sin registrar" eran justo esos dos. Se excluyen por dos vias: el nombre
    # conocido, y que el propio fichero o la doc mencionen `.git/hooks`.
    DE_GIT = ("pattern-check.sh", "pre-commit-check.sh", "pre-push.sh", "commit-msg.sh")
    hooks = {p.name for p in (cl / "hooks").glob("*.sh")}
    settings = _lee(cl / "settings.json") + _lee(cl / "settings.local.json")

    def es_de_git(nombre: str) -> bool:
        if nombre in DE_GIT:
            return True
        return ".git/hooks" in _lee(cl / "hooks" / nombre)

    # Un nombre que sale en settings.json cuenta (registrado, o declarado en un `_comment` como
    # no registrado a proposito); y tambien el que lanza un hook registrado (`_envueltos`).
    envueltos = _envueltos(cl, hooks, _registrados(cl, hooks, settings))
    sin_registrar = sorted(h for h in hooks
                           if h not in settings and h not in envueltos and not es_de_git(h))
    if sin_registrar:
        t.append(Tarea(
            "HAR-HOOKS",
            f"Registrar {len(sin_registrar)} hook(s) que estan en disco y no en settings.json",
            f"Un hook sin registrar no corre nunca, y nadie se entera: {', '.join(sin_registrar[:6])}"
            + (" …" if len(sin_registrar) > 6 else ""),
            "Anadirlos al bloque `hooks` de `.claude/settings.json`, en su evento.\n"
            "   ⚠️ Tocar settings.json es aprobacion del Usuario (governance.md §2).",
            aprueba=True,
        ))

    # 4. El canal de mejoras, vacio
    #
    # Una entrada puede ser una seccion («## …») o una FILA de tabla con su fecha
    # («| 2026-08-24 | … |»). Contando solo las secciones, AMC salia «vacio» con 12 filas
    # dentro (su improvements_tl.md del 2026-08-28 es una tabla). La cabecera y el separador
    # de la tabla no empiezan por fecha, asi que no cuentan.
    imp = cl / "improvements_tl.md"
    if imp.is_file() and _entradas_de_mejoras(_lee(imp)) == 0:
        t.append(Tarea(
            "HAR-MEJORAS",
            "El canal `improvements_tl.md` esta vacio",
            "Es por donde el proyecto devuelve aprendizajes al template. Vacio significa que el "
            "bucle de mejora no esta corriendo en este proyecto.",
            "Al encontrar un gotcha del harness, anotarlo ahi con: que paso · impacto · cambio "
            "propuesto · estado. Lo cosecha `/consolidate-agent-learnings`.",
        ))

    # 5. Agentes sin memoria
    agentes = {p.stem for p in (cl / "agents").glob("*.md") if p.stem != "README"}
    sin_memoria = sorted(a for a in agentes if not (cl / "agents" / a / "memory.md").is_file())
    if sin_memoria:
        t.append(Tarea(
            "HAR-MEMORIA",
            f"{len(sin_memoria)} agente(s) sin `memory.md`",
            f"`rules/agent-autonomy-ladder.md` §7: un agente sin memoria esta en fase 1. Un agente "
            f"declarado en fase 3 o 4 sin ella es una contradiccion: {', '.join(sin_memoria[:5])}"
            + (" …" if len(sin_memoria) > 5 else ""),
            "Crear su `memory.md` con lo que ya se sabe del proyecto — no vacia: una memoria vacia "
            "cumple el checklist y no aporta nada.",
        ))
    return t


def render(raiz: Path, tareas: list[Tarea]) -> str:
    from datetime import date
    cab = f"""# Tareas del harness — lo que este proyecto tiene que EJECUTAR

> Generado por `gen_tareas_del_harness.py` el {date.today().isoformat()}, midiendo el disco.
> **No es documentacion: es trabajo pendiente.** El harness se configuro y estas piezas estan
> puestas y sin usar. Tener el patron no es cumplirlo.
>
> Se regenera: `python3 .claude/scripts/gen_tareas_del_harness.py . --escribir`

"""
    if not tareas:
        return cab + "## ✅ Nada pendiente\n\nTodo lo configurado esta ejecutado. Se vuelve a medir al proximo `update-agent`.\n"
    cuerpo = [cab, f"## {len(tareas)} tarea(s)\n"]
    for x in tareas:
        cuerpo.append(f"### `{x.id}` · {x.titulo}\n")
        cuerpo.append(f"**Por que:** {x.porque}\n")
        cuerpo.append(f"**Como:**\n```\n{x.como}\n```\n")
        if x.aprueba:
            cuerpo.append("> ⚠️ **Requiere aprobacion del Usuario** (`rules/governance.md` §2).\n")
        cuerpo.append("")
    return "\n".join(cuerpo)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto")
    ap.add_argument("--escribir", action="store_true", help="genera el .md y anade al pending-tasks del plan activo")
    ap.add_argument("--sondear", action="store_true",
                    help="pregunta a la URL local de trazas si responde (/api/public/health)")
    a = ap.parse_args()
    raiz = Path(a.proyecto).resolve()
    if not (raiz / ".claude").is_dir():
        print(f"✗ {raiz} no tiene .claude/", file=sys.stderr)
        return 1

    tareas = detecta(raiz, a.sondear)
    print(f"{raiz.name}: {len(tareas)} tarea(s) pendientes del harness")
    for x in tareas:
        print(f"  · {x.id:<14} {x.titulo}{'  [aprueba el Usuario]' if x.aprueba else ''}")
    if not a.escribir:
        print("\n→ para escribirlo:  --escribir")
        return 0

    destino = raiz / ".docs" / "TAREAS-DEL-HARNESS.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(render(raiz, tareas), encoding="utf-8")
    print(f"\n✓ {destino.relative_to(raiz)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
