#!/usr/bin/env python3
"""check_mechanisms.py — ¿las normas escritas se están APLICANDO de verdad?

Por qué existe (item TPL-21). Los tres fallos más caros encontrados auditando el template tienen
la misma forma, y ninguno de los tres fallaba haciendo ruido:

  · el gate de RAM contaba mal las instancias y bloqueaba `pytest` siempre
  · el `.gitignore` de las capturas usaba `*/screenshots/` donde tocaba `**` → capturaba 0 de 435
    ficheros, y se colaron 71 MB al repositorio
  · el comando de aviso de CLAUDE.md (`openclaw gateway wake`) no existe: el subcomando se llama
    de otra forma. Escrito en 50 ficheros y replicado a 6 proyectos

Los tres aparecieron por casualidad. Este script los busca a propósito. NO comprueba que las reglas
estén bien escritas —para eso están las propias reglas— sino que **el mecanismo que debía aplicarlas
puede disparar**: que el hook existe y es ejecutable, que el patrón de ignorar casa con algo, que el
comando que se manda ejecutar está instalado, y que las rutas que se citan existen.

Uso:
    python3 .claude/scripts/check_mechanisms.py            # informe legible, exit 1 si hay roto
    python3 .claude/scripts/check_mechanisms.py --json     # para otro agente o para CI
    python3 .claude/scripts/check_mechanisms.py --quiet    # solo lo roto
    python3 .claude/scripts/check_mechanisms.py --root <proyecto>   # mide OTRO proyecto
    python3 .claude/scripts/check_mechanisms.py --root /home        # mide TODOS los que cuelguen de /home

`--root` existe porque sin él este script mide SIEMPRE el repo donde vive (ROOT sale de __file__).
`pasos_de_actualizacion.py` lo lanzaba con cwd=<proyecto> creyendo que medía el proyecto, y medía
el template: en EvoPreven dio «ningún mecanismo roto» con dos hooks cuyo matcher no casaba nunca
(2026-10-14). Un instrumento que apunta a otro sitio da señal falsa con el signo bueno.

Límite honesto: esto caza mecanismos **ausentes o inejecutables**, no mecanismos que existen y
razonan mal. Un hook que corre y decide mal pasa este check — igual que el gate de RAM lo habría
pasado. Para eso hacen falta los fixtures de cada mecanismo, que es otro trabajo.
"""
import argparse
import glob as glob_mod
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CLAUDE = os.path.join(ROOT, ".claude")
# Órdenes que se mandan ejecutar en la documentación y que deben existir en el sistema. Se listan a
# mano a propósito: descubrirlas por regex trae medio diccionario y el ruido mata el check.
# `openclaw` estuvo aquí y se retiró el 2026-08-08: no estaba instalado y sus 15 citas fallaban
# en silencio. Si algún día se monta un canal de aviso real, se añade su binario a esta lista.
CLI_ESPERADOS = ["git", "python3"]


def rel(p):
    return os.path.relpath(p, ROOT)


def leer(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def hooks_de_settings(hallazgos):
    """Todo hook declarado en settings.json debe existir y ser ejecutable."""
    s = os.path.join(CLAUDE, "settings.json")
    if not os.path.exists(s):
        return
    try:
        cfg = json.loads(leer(s))
    except json.JSONDecodeError as e:
        hallazgos.append(("roto", "settings.json", f"no es JSON válido: {e}", "el harness no lo lee"))
        return
    declarados = set()
    for evento, grupos in (cfg.get("hooks") or {}).items():
        for g in grupos if isinstance(grupos, list) else []:
            for h in (g.get("hooks") or []):
                cmd = h.get("command", "")
                for m in re.finditer(r"[\w./$-]*hooks/([\w.-]+\.(?:sh|py))", cmd):
                    declarados.add((evento, m.group(1)))
    for evento, nombre in sorted(declarados):
        ruta = os.path.join(CLAUDE, "hooks", nombre)
        if not os.path.exists(ruta):
            hallazgos.append(("roto", f"hooks/{nombre}",
                              f"declarado en settings.json ({evento}) pero NO existe",
                              "el evento no dispara nada y nadie se entera"))
        elif not os.access(ruta, os.X_OK):
            hallazgos.append(("roto", f"hooks/{nombre}",
                              f"declarado en settings.json ({evento}) pero no es ejecutable",
                              "el harness no puede lanzarlo"))
    # y al revés: hooks que existen pero nadie declara
    hdir = os.path.join(CLAUDE, "hooks")
    if os.path.isdir(hdir):
        nombres = {n for _, n in declarados}
        for f in sorted(os.listdir(hdir)):
            if f.endswith((".sh", ".py")) and f not in nombres:
                hallazgos.append(("aviso", f"hooks/{f}", "existe pero settings.json no lo declara",
                                  "no dispara nunca; o se registra o se retira"))


def patrones_gitignore(hallazgos):
    """Un patrón que no casa con NADA suele estar mal escrito (el caso de los 71 MB)."""
    gi = os.path.join(ROOT, ".gitignore")
    if not os.path.exists(gi):
        return
    for n, linea in enumerate(leer(gi).splitlines(), 1):
        pat = linea.strip()
        if not pat or pat.startswith("#") or pat.startswith("!"):
            continue
        if not any(c in pat for c in "*?[") or pat.endswith("/"):
            continue          # rutas literales y directorios: no se puede juzgar por coincidencias
        if "/" not in pat:
            continue          # `*.pem`, `secrets.*`: son PREVENTIVOS. Que no casen con nada es la
                              # buena noticia, no un fallo. Solo se juzgan los patrones con ruta,
                              # que apuntan a algo concreto del repo y por eso pueden errar el tiro
        try:
            out = subprocess.run(["git", "ls-files", "--others", "--ignored",
                                  "--exclude", pat, "--directory"],
                                 cwd=ROOT, capture_output=True, text=True, timeout=45)
            casa = bool(out.stdout.strip())
        except (OSError, subprocess.SubprocessError):
            continue
        if not casa:
            hallazgos.append(("aviso", f".gitignore:{n}", f"el patrón `{pat}` no casa con ningún fichero",
                              "puede estar mal escrito (el `*` vs `**` que costó 71 MB) o ya no aplicar"))


def comandos_citados(hallazgos):
    """Los binarios que la documentación manda ejecutar tienen que estar instalados. Y para las
    órdenes de varias palabras se comprueba el SUBCOMANDO, que es donde falló openclaw."""
    for cli in CLI_ESPERADOS:
        if not shutil.which(cli):
            # OJO: no todo el que lo menciona lo MANDA usar. El registro de mejoras y este
            # mismo script lo nombran para AVISAR de que no existe, y contarlos inflaba la
            # cifra — un comprobador cuyo número no te puedes creer se deja de leer.
            _todos = subprocess.run(["grep", "-rl", cli, CLAUDE], capture_output=True,
                                    text=True).stdout.splitlines()
            _avisan = ("improvements_tl.md", "check_mechanisms.py")
            citas = len([f for f in _todos if not f.endswith(_avisan)])
            hallazgos.append(("roto", cli, f"lo MANDAN ejecutar {citas} ficheros de .claude/ "
                              f"({len(_todos) - citas} más lo mencionan para avisar) y NO está instalado",
                              "cada instrucción que lo use falla en silencio"))
    # subcomandos: `openclaw gateway wake` fue el caso real
    subs = set()
    for base, _, files in os.walk(CLAUDE):
        if any(x in base for x in ("/node_modules", "/.git", "/_retirad", "/_deprecated")):
            continue
        for f in files:
            if not f.endswith((".md", ".sh", ".json")):
                continue
            texto = leer(os.path.join(base, f))
            # Solo donde de verdad es una ORDEN: dentro de backticks o al principio de una línea de
            # shell. Sin esto, la prosa "openclaw no está instalado" se leía como el subcomando
            # `no est` — un falso positivo que enseña a ignorar el check, que es justo lo que
            # queremos evitar.
            for m in re.finditer(r"(?:`|^\s*|\$\s*)openclaw\s+([a-z][a-z-]{2,})\s+([a-z][a-z-]{2,})",
                                 texto, re.M):
                subs.add((m.group(1), m.group(2)))
    if shutil.which("openclaw"):
        for grupo, sub in sorted(subs):
            try:
                h = subprocess.run(["openclaw", grupo, "--help"], capture_output=True,
                                   text=True, timeout=25)
            except (OSError, subprocess.SubprocessError):
                continue
            texto = h.stdout + h.stderr
            if not texto.strip():
                continue
            if re.search(r"^\s*%s\b" % re.escape(sub), texto, re.M):
                continue
            if sub in ("--help", "help"):
                continue
            hallazgos.append(("roto", f"openclaw {grupo} {sub}",
                              f"la documentación manda ejecutarlo y `openclaw {grupo}` no lo lista",
                              "la orden falla y el hook la manda a /dev/null"))


# Lo que crea el USO, no el template: salidas de skills y hooks, ficheros que declara cada proyecto
# y directorios que monta Claude Code. Citarlos dice dónde va a quedar algo, no apunta a algo que
# falte; marcarlos era la mitad de los avisos de este check (MO-42, 2026-10-21) y el ruido enseña
# a ignorarlo. Cada entrada, con quién la crea. Casan por COMPONENTE de ruta (la entrada misma o lo
# que cuelga de ella, nunca `.claude/worktrees-otra-cosa`), y ninguna cubre un directorio que el
# template versione: `.claude/docs/reference/` o `.docs/feedback/qa-loop/` sí se comprueban.
SALIDAS_DEL_USO = (
    ".claude/worktrees",                         # Claude Code (`--worktree`, `isolation: worktree`)
    ".claude/PROGRESS.auto.log",                 # hook auto-progress-log (MO-37)
    ".claude/docs/html",                         # HTML sueltos de antes del 31-10 (derivados)
    ".docs/html",                                # HTML sueltos (output-choice.md, ORD-4)
    ".claude/docs/tests",                        # REPORT del tester no técnico
    ".claude/CHECKLIST.md",                      # tareas sin SpecKit (speckit-workflow.md)
    ".claude/puertos-publicos-declarados.json",  # lo declara cada proyecto (security.md)
    ".claude/gate-tenant.json",                  # configuración del gate de tenant, por proyecto
    # sub-ola 2.29: los cinco los crea cada proyecto (plantillas en templates/ cuando las hay)
    ".claude/gate-django.json",                  # excepciones de G3 (check_django_seguridad.py)
    ".claude/estado-datos-reales.json",          # el candado: lo firma una persona
    ".claude/proyecto-delicado.md",              # marcador (templates/proyecto-delicado.md)
    ".claude/envios-externos.json",              # lo que envían fuera sus skills vendorizadas
    ".claude/pii-capturas.json",                 # la guarda de capturas del proyecto
    ".docs/html",                                # informes sueltos (html-output.md)
    ".docs/arranque",                            # EXENCION.md: la escribe el Usuario
    ".docs/core/producto",                       # /arrancar fase 5 y skill marca: promoción al core
    ".docs/core/marca",
    ".docs/core/arquitectura.md",
    ".docs/core/privacidad.md",
    ".docs/core/seguridad.md",
    ".docs/negocio",                             # el canon de negocio de cada cliente
    ".docs/domain",                              # 3.57: domain.yaml y agents/ del proyecto
    ".docs/feedback/rita",                       # los informes en sombra de la guardiana del patrón
    ".docs/diseno",                              # direcciones de arte
)
# La cita misma dice que es de otro tiempo o de otro repo: no es una instrucción para aquí. Solo
# cuenta el marcador PEGADO a la cita —delante: «*Antes `x`*», «en el repo de elvion, `x`»; detrás:
# «`x` (archivado …)», «`x`, que no existe», «`x` del proyecto auditado»—, con formas completas.
# Mirar una ventana alrededor dejaba que una palabra corriente de la frase («archivo», «borrador»,
# «deprecado», «antes de cada commit», «en el proyecto») callara citas rotas de verdad: la primera
# versión (línea entera) calló 7 de 11; la segunda (60 caracteres), 16 de 24 (verificadores de la
# 2.17). Y nunca se excusa lo que va DETRÁS de «es ahora», «se fusionó en» o «sustituido por»: ese
# es el destino, y tiene que existir. La convención para citar lo que ya no está, por tanto: el
# marcador pegado a la ruta.
HISTORIA = (r"archivad[oa]s?|retirad[oa]s?|eliminad[oa]s?|borrad[oa]s?|fusionad[oa]s?|"
            r"absorbid[oa]s?|sustituid[oa]s?|deprecad[oa]s?|renombrad[oa]s?|jubilad[oa]s?|"
            r"movid[oa]s?|obsolet[oa]s?")
# «antes» solo al empezar la frase o tras «(», «*» o «;»: «*Antes `x`*» es historia, «Lee antes `x`»
# es una orden (verificador de la 2.17, segunda pasada).
HISTORIA_DELANTE = re.compile(
    r"((^|[(*_;:—–>]|\.\s)\s*antes|\bantigu[oa]s?|\bviv[íi]a en|\bestaba en|\beran?|\b(?:"
    + HISTORIA + r"))\W{0,3}$", re.I)
# Una lista de citas («`a`, `b` y `c` (archivados)») comparte el marcador: se salta el resto de la
# lista antes de mirarlo.
LISTA_DELANTE = re.compile(r"(`[^`]+`\s*(,|y|e|o)\s*)+$")
LISTA_DETRAS = re.compile(r"^(\s*(,|y|e|o)\s*`[^`]+`)+")
HISTORIA_DETRAS = re.compile(
    r"^\W{0,4}(que |y )?(ya |hoy )?(est[áa]n? |fue |fueron |se |qued[óa]n? )?"
    r"(" + HISTORIA + r"|archiv[óo]|retir[óo]|fusion[óo]|movi[óo]|no existen?\b|es ahora\b|"
    r"ahora es\b|en `_archive/)", re.I)
PROYECTO_DELANTE = re.compile(
    r"\b((en|de|del) (el )?repo de [\w-]+|(en|de) su repo|en el proyecto auditado)\W{0,3}$", re.I)
# Detrás, «del repo de X» solo entre paréntesis o en aposición: «copia `x` en el repo de destino»
# es una orden, «`x` (en el repo de elvion)» dice dónde vive.
PROYECTO_DETRAS = re.compile(
    r"^\W{0,4}(del proyecto auditado|del repo del proyecto|de su repo|en su repo|"
    r"si existe en el proyecto|si el proyecto lo tiene)\b|"
    r"^\s*[(,—–]\W{0,3}(del|en el) repo de [\w-]+", re.I)


def _es_salida(ruta: str) -> bool:
    return any(ruta == s or ruta.startswith(s + "/") for s in SALIDAS_DEL_USO)


def _cita_excusada(linea: str, ini: int, fin: int) -> bool:
    """¿La propia cita dice, pegado a ella, que es historia o de otro repo?"""
    delante = LISTA_DELANTE.sub("", linea[:ini])
    detras = LISTA_DETRAS.sub("", linea[fin:])[:45]
    return bool(HISTORIA_DELANTE.search(delante) or PROYECTO_DELANTE.search(delante)
                or HISTORIA_DETRAS.search(detras) or PROYECTO_DETRAS.search(detras))


def rutas_citadas(hallazgos):
    """Rutas del propio repo citadas en rules/, skills/, agents/, commands/, templates/ y patterns/
    que no existen."""
    # `resources/` cuelga de la RAÍZ, no de .claude/ (y `examples/` también colgaba de ahí hasta
    # que el 2026-10-19 se juntó con `.claude/examples/`); hasta el 2026-09-11 no se miraban: la
    # promesa de `examples/guard-secretos.sh` llevaba meses incumplida sin que el comprobador
    # pudiera decir nada. Las de una sola palabra (hooks/, patterns/, templates/)
    # se resuelven con el truco de las raíces de abajo.
    # Hasta la 2.17 no se miraban `rules/`, `skills/`, `agents/`, `commands/` ni `smoke/`, ni se
    # leían commands/, templates/ ni patterns/: así sobrevivieron `agents/director.md`,
    # `scripts/lidia-diff.py` o una rule de estadística que nunca existió: nadie lo vio romperse.
    # Lo que NO ve, dicho: rutas sin comillas invertidas, también las de un bloque de código.
    rx = re.compile(r"`(\.claude/[\w./-]+|\.docs/[\w./-]+|scripts/[\w./-]+"
                    r"|examples/[\w./-]+|resources/[\w./-]+"
                    r"|hooks/[\w./-]+|patterns/[\w./-]+|templates/[\w./-]+|workflows/[\w./-]+"
                    r"|rules/[\w./-]+|skills/[\w./-]+|agents/[\w./-]+|commands/[\w./-]+"
                    r"|smoke/[\w./-]+)`")
    vistos = set()
    for sub in ("rules", "skills", "agents", "commands", "templates", "patterns"):
        base = os.path.join(CLAUDE, sub)
        for dirpath, _, files in os.walk(base):
            if any(x in dirpath
                   for x in ("/_retirad", "/_deprecated", "/node_modules", "/_fixtures")):
                continue
            for f in files:
                if not f.endswith(".md"):
                    continue
                origen = os.path.join(dirpath, f)
                for linea in leer(origen).splitlines():
                    # ~~tachado~~ = retirado a propósito, y lo dice (mismas posiciones: se vacía)
                    sin_tachado = re.sub(r"~~.*?~~", lambda m: " " * len(m.group(0)), linea)
                    for m in rx.finditer(sin_tachado):
                        ruta = m.group(1).rstrip("/.,;:")
                        # las rutas con hueco (YYYY-MM-DD, <slug>, …) son PLANTILLAS, no rutas
                        # reales: marcarlas sería ruido garantizado, y el ruido enseña a ignorar
                        # el check
                        if any(c in ruta for c in "*<>[]") or ruta.endswith(("/", "…")):
                            continue
                        if re.search(r"YYYY|MM-DD|HH-|\.\.\.|<|\bN\b|\bID\b|PREFIJO|slug|"
                                     r"fecha|nombre", ruta):
                            continue
                        clave = (rel(origen), ruta)
                        if clave in vistos or _es_salida(ruta):
                            continue
                        # `scripts/<x>.py` en una rule suele querer decir
                        # `.claude/scripts/<x>.py`, y `templates/<x>` en un comando de SpecKit,
                        # `.specify/templates/<x>`: se prueban las tres raíces antes de darla por
                        # rota
                        if any(os.path.exists(os.path.join(base_dir, ruta))
                               for base_dir in (ROOT, CLAUDE, os.path.join(ROOT, ".specify"))):
                            continue
                        if _cita_excusada(linea, m.start(), m.end()):
                            continue
                        vistos.add(clave)
                        hallazgos.append(("aviso", rel(origen), f"cita `{ruta}`, que no existe",
                                          "quien siga la instrucción se estrella"))


# El check de citas se ve fallar a sí mismo en cada ejecución: si deja de cazar uno de estos casos,
# o empieza a marcar un control, es un mecanismo ROTO, no un aviso (rules/verification.md §TPL-4:
# «el validador comprueba sus propias reglas al arrancar»). Los V- son los del verificador de la
# 2.17.
AUTOPRUEBA_CITAS = (
    # (id, línea, ruta citada, ¿se tiene que marcar?, carpeta de .claude/ donde va la línea)
    ("V-01", "Corre `scripts/fantasma_control.py`.", "scripts/fantasma_control.py", True, "rules"),
    ("V-02", "Guarda cada archivo con `scripts/fantasma_archivo.py`.",
     "scripts/fantasma_archivo.py", True, "rules"),
    ("V-03", "Córrelo con `scripts/fantasma_proy.py` en el proyecto antes de cada merge.",
     "scripts/fantasma_proy.py", True, "rules"),
    ("V-04", "El borrador del PRD lo genera `scripts/fantasma_borrador.py`.",
     "scripts/fantasma_borrador.py", True, "rules"),
    ("V-05", "Si el informe no existe, créalo con `scripts/fantasma_noexiste.py`.",
     "scripts/fantasma_noexiste.py", True, "rules"),
    ("V-06", "Sustituye los tokens con `scripts/fantasma_sustituye.py`.",
     "scripts/fantasma_sustituye.py", True, "rules"),
    ("V-07", "Referencia completa: `.claude/docs/reference/fantasma-catalogo.md`.",
     ".claude/docs/reference/fantasma-catalogo.md", True, "rules"),
    ("V-08", "Lee `.claude/worktrees-fantasma.md`.",
     ".claude/worktrees-fantasma.md", True, "rules"),
    ("V-09", "~~`skills/vieja/SKILL.md`~~ y además `scripts/fantasma_tachado.py`.",
     "scripts/fantasma_tachado.py", True, "rules"),
    ("V-10", "Lee `rules/fantasma.md`, `skills/fantasma/SKILL.md` y `agents/fantasma.md`.",
     "skills/fantasma/SKILL.md", True, "rules"),
    ("V-12", "Edita el archivo `commands/fantasma.md` y retira lo que sobre.",
     "commands/fantasma.md", True, "rules"),
    # segunda pasada del verificador: palabras de la lista en su sentido corriente, y destinos
    ("W-01", "Corre los tests (antes de cada commit) con `scripts/w_antes_de.py`.",
     "scripts/w_antes_de.py", True, "rules"),
    ("W-02", "Para detectar código deprecado, usa `scripts/w_deprecado.py`.",
     "scripts/w_deprecado.py", True, "rules"),
    ("W-03", "Los registros eliminados se recuperan con `scripts/w_eliminados.py`.",
     "scripts/w_eliminados.py", True, "rules"),
    ("W-04", "Si un fichero fue renombrado, corre `scripts/w_renombrado.py`.",
     "scripts/w_renombrado.py", True, "rules"),
    ("W-05", "Lee antes `rules/w_lee_antes.md`.", "rules/w_lee_antes.md", True, "rules"),
    ("W-06", "La guía es ahora `skills/w_destino/SKILL.md`.", "skills/w_destino/SKILL.md", True,
     "rules"),
    ("W-07", "Se fusionó en `skills/w_fusion/SKILL.md`.",
     "skills/w_fusion/SKILL.md", True, "rules"),
    ("W-08", "Copia `scripts/w_destino.py` en el repo de destino.", "scripts/w_destino.py", True,
     "rules"),
    ("W-09", "Lo archivado se regenera con `scripts/w_cerca.py`.", "scripts/w_cerca.py", True,
     "rules"),
    ("W-10", "En los patrones: corre `scripts/w_patterns.py`.", "scripts/w_patterns.py", True,
     "patterns"),
    ("C-01", "Lo deja Claude Code en `.claude/worktrees`.", ".claude/worktrees", False, "rules"),
    ("C-02", "~~`skills/retirada/SKILL.md`~~ — se retiró.",
     "skills/retirada/SKILL.md", False, "rules"),
    ("C-03", "*Antes `rules/fusionada.md`.* Cuándo: siempre.",
     "rules/fusionada.md", False, "rules"),
    ("C-04", "`agents/viejo.md` (archivado el 2026-01-01).", "agents/viejo.md", False, "rules"),
    ("C-05", "Corre `scripts/del_cliente.py` del proyecto auditado.",
     "scripts/del_cliente.py", False, "rules"),
    ("C-06", "La skill `skills/existe/SKILL.md`.", "skills/existe/SKILL.md", False, "rules"),
    ("C-07", "`scripts/x_no.py`, que no existe en el template.", "scripts/x_no.py", False, "rules"),
    ("C-08", "EvoPreven lo separó en su repo, `rules/evo.md`.", "rules/evo.md", False, "rules"),
    ("C-09", "Los informes van a `.claude/docs/html/informe.html`.",
     ".claude/docs/html/informe.html", False, "rules"),
    ("C-10", "`agents/c_lista1.md` y `agents/c_lista2.md` (archivados).",
     "agents/c_lista1.md", False, "rules"),
    ("C-11", "(en el repo de elvion: `scripts/c_elvion1.py`, `scripts/c_elvion2.py`)",
     "scripts/c_elvion2.py", False, "rules"),
    ("C-12", "Hasta el 2026-10-19 estaba en `skills/c_estaba/SKILL.md`.",
     "skills/c_estaba/SKILL.md", False, "rules"),
    ("C-13", "`scripts/c_movido.py` (movido a `_archive/2026-10-20/`).",
     "scripts/c_movido.py", False, "patterns"),
)


def _autoprueba_citas() -> list[tuple[str, bool, bool]]:
    """(id, esperado, marcado) de cada caso: `rutas_citadas` sobre un proyecto de juguete."""
    import tempfile
    global ROOT, CLAUDE
    viejos = (ROOT, CLAUDE)
    with tempfile.TemporaryDirectory(prefix="autoprueba-citas-") as d:
        os.makedirs(os.path.join(d, ".claude", "rules"))
        os.makedirs(os.path.join(d, ".claude", "skills", "existe"))
        skill = os.path.join(d, ".claude", "skills", "existe", "SKILL.md")
        with open(skill, "w", encoding="utf-8") as fh:
            fh.write("# existe\n")
        rule = os.path.join(d, ".claude", "rules", "autoprueba.md")
        with open(rule, "w", encoding="utf-8") as fh:
            fh.write("\n".join(c[1] for c in AUTOPRUEBA_CITAS if c[4] == "rules") + "\n")
        os.makedirs(os.path.join(d, ".claude", "patterns"))
        patron = os.path.join(d, ".claude", "patterns", "autoprueba.md")
        with open(patron, "w", encoding="utf-8") as fh:
            fh.write("\n".join(c[1] for c in AUTOPRUEBA_CITAS if c[4] == "patterns") + "\n")
        hallazgos: list = []
        try:
            ROOT, CLAUDE = d, os.path.join(d, ".claude")
            rutas_citadas(hallazgos)
        finally:
            ROOT, CLAUDE = viejos
    marcadas = {re.search(r"`([^`]+)`", h[2]).group(1) for h in hallazgos}
    return [(cid, debe, ruta in marcadas) for cid, _, ruta, debe, _ in AUTOPRUEBA_CITAS]


def citas_se_ven_fallar(hallazgos):
    """Si el check de citas no caza sus sabotajes, o marca sus controles, está roto."""
    malos = [f"{cid} ({'no lo caza' if debe else 'marca un control'})"
             for cid, debe, marcado in _autoprueba_citas() if debe != marcado]
    if malos:
        hallazgos.append(("roto", "check_mechanisms.rutas_citadas",
                          f"no pasa su autoprueba: {', '.join(malos)}",
                          "un check de citas que no se ve fallar da «0 rutas rotas» con "
                          "buena cara"))


def cuestionario_sin_fantasmas(hallazgos):
    """El cuestionario de configuración declara patrones, agentes, rules y
    comprobadores. Si alguno se archiva o se renombra, el cuestionario sigue
    ofreciéndolo y configura algo que ya no está. Es el mismo fallo que este
    script caza en los hooks, un nivel más arriba."""
    import fnmatch, pathlib
    f = pathlib.Path(ROOT) / ".claude" / "templates" / "configuracion-de-proyecto.yaml"
    if not f.exists():
        return
    try:
        import yaml
        d = yaml.safe_load(leer(f)) or {}
    except Exception as e:                                      # noqa: BLE001
        hallazgos.append(("roto", rel(f), f"no se puede parsear: {e}",
                          "update-agent no puede preguntar la configuración"))
        return
    univ = {
        "patrones":      {x.stem for x in (pathlib.Path(ROOT) / ".claude/patterns/stack").glob("*.md")},
        # Un agente vive de DOS formas y las dos son legítimas: carpeta (con su memory.md) o
        # fichero `<nombre>.md` suelto. Mirando solo carpetas, los 30 agentes-fichero del template
        # salían como «declarado y no existe» — un falso positivo que no se apaga nunca y que
        # enseña a ignorar este comprobador entero. Se vio al propagar a risk-couple, donde su
        # configuracion-de-proyecto.yaml declara `nadia-chatbot-evaluator` (que es fichero) y el
        # check decía que no existía teniéndolo delante.
        "agentes":       ({x.name for x in (pathlib.Path(ROOT) / ".claude/agents").iterdir() if x.is_dir()}
                          | {x.stem for x in (pathlib.Path(ROOT) / ".claude/agents").glob("*.md")}),
        "rules":         {x.stem for x in (pathlib.Path(ROOT) / ".claude/rules").glob("*.md")},
        "comprobadores": {x.name for x in (pathlib.Path(ROOT) / ".claude/patterns/stack").glob("pattern_check_*.py")},
        # sub-ola 2.29 (SE-41): `datos_reales_desarrollo` instala skills y apaga hooks
        "skills":        {x.name for x in (pathlib.Path(ROOT) / ".claude/skills").iterdir() if x.is_dir()},
        "hooks":         {x.stem for x in (pathlib.Path(ROOT) / ".claude/hooks").glob("*.sh")},
        # sub-ola 3.57 (NE-12): `vertical` enciende paquetes de dominio; valen los del catálogo,
        # construidos o no (uno sin carpeta lo reporta `domain_packs.py` como «sin construir»)
        "domains":       set(((yaml.safe_load(leer(_cat)) or {}).get("sectors") or {})
                             if (_cat := pathlib.Path(ROOT) / ".claude/domains/catalog.yaml").exists()
                             else ()),
    }
    # Lo que el PROYECTO archivó a propósito no es un mecanismo roto: es una decisión suya. Antes
    # salía como «roto» y aquila-erp daba 24 rotos por su poda aprobada del 2026-09-30, que es la
    # forma más rápida de enseñar a ignorar este comprobador. Se distingue de lo que desapareció
    # sin más: lo podado sale como AVISO y dice qué hacer si un día se responde que sí.
    CEMENTERIOS = {"_archive", "_deprecated", "_retiradas", "_retirados", "_archivadas", "_archivo"}
    podado = set()
    for dirpath, dirnames, _ in os.walk(ROOT):
        dirnames[:] = [x for x in dirnames if x not in ("node_modules", ".git", ".venv")]
        for cem in [x for x in dirnames if x in CEMENTERIOS]:
            for x in (pathlib.Path(dirpath) / cem).rglob("*"):
                podado.add(x.stem if x.is_file() else x.name)
        dirnames[:] = [x for x in dirnames if x not in CEMENTERIOS]
    for q in d.get("preguntas", []):
        for op, cfg in (q.get("configura") or {}).items():
            cfg = cfg or {}
            # lo anidado (`con_agente_ia: {agentes: …}`, `desactiva: {hooks: …}`) también se valida
            planos = [cfg] + [v for k, v in cfg.items() if k in ("con_agente_ia", "desactiva")
                              and isinstance(v, dict)]
            for clave, existentes in univ.items():
                for v in [x for c in planos for x in (c.get(clave) or [])]:
                    casa = (any(fnmatch.fnmatch(u, v) for u in existentes)
                            if "*" in v else v in existentes)
                    archivado = (any(fnmatch.fnmatch(u, v) for u in podado)
                                 if "*" in v else v in podado)
                    if not casa and archivado:
                        hallazgos.append((
                            "aviso", f"configuracion-de-proyecto.yaml → {q.get('id')}.{op}.{clave}",
                            f"ofrece '{v}', que este proyecto PODÓ (está en su cementerio)",
                            "si se responde esta opción, des-archivarlo es decisión del Usuario"))
                        continue
                    if not casa:
                        hallazgos.append((
                            "roto", f"configuracion-de-proyecto.yaml → {q.get('id')}.{op}.{clave}",
                            f"declara '{v}' y no existe",
                            "el cuestionario configuraría algo que ya no está"))


def speckit_scripts(hallazgos):
    """Los comandos /speckit.* llaman a `scripts/bash/*.sh` relativos a `.specify/` (frontmatter
    `scripts:`). Sin esa carpeta, los 9 nacen rotos: elvion lo sufrió (#15, MO-28) y el 2026-10-27
    seis derivados tenían los comandos y 0 scripts (cold_calling_coach, develop, gencat, quirúrgicos,
    musa y webs)."""
    cmds = sorted(glob_mod.glob(os.path.join(CLAUDE, "commands", "speckit.*.md")))
    if not cmds:
        return
    missing = {}
    for c in cmds:
        for s in sorted(set(re.findall(r"scripts/bash/[A-Za-z0-9_.-]+\.sh", leer(c)))):
            if not os.path.isfile(os.path.join(ROOT, ".specify", s)):
                missing.setdefault(s, []).append(os.path.basename(c)[:-3])
    for s, callers in sorted(missing.items()):
        hallazgos.append(("roto", f".specify/{s}", f"no existe y lo llaman {', '.join(callers)}",
                          "esos /speckit.* fallan al primer uso; trae .specify/scripts/ del template "
                          "(propagar.py lo copia sin pisar lo adaptado)"))


def agentes_sin_frontera(hallazgos):
    """La `description` es lo UNICO que el modelo lee para decidir si activa un agente.
    Sin frontera negativa ("NO usar para X, eso es Y") el agente se dispara donde no
    toca y compite con el correcto — y el que si servia se queda sin usar.

    Medido el 2026-08-27: 2 de 29 agentes del template la tenian, y 0 de los 8 agentes
    propios de dos proyectos derivados. La regla existia en `skill-authoring` (cinco
    veces) pero solo para SKILLS: nunca se traslado a los agentes."""
    import re, pathlib as _p
    d = _p.Path(ROOT) / ".claude" / "agents"
    if not d.exists():
        return
    MARCAS = ("no usar para", "do not use for", "no confundir")
    for f in sorted(d.glob("*.md")):
        t = leer(f)
        m = re.search(r"^description: *(.+?)(?=\n[a-z_]+:|\n---)", t, re.S | re.M)
        if not m:
            continue
        # el `>-` de YAML pliega saltos de línea: «NO\n  usar para» cuenta
        plegada = re.sub(r"\s+", " ", m.group(1).lower())
        if not any(k in plegada for k in MARCAS):
            hallazgos.append(("aviso", rel(f), "la description no declara frontera negativa",
                              "el agente se activa donde no toca y compite con el correcto"))


def agentes_yaml(hallazgos):
    """El frontmatter de cada agente, leído con un parser YAML de verdad (MO-55).

    Una `description` sin comillas que lleva «algo: otra cosa» no es YAML válido. Claude Code lo
    lee de forma más tolerante y el agente sigue funcionando, así que nadie se entera — hasta que
    otra herramienta (un generador de catálogo, `check-agent`, PyYAML) lee el mismo fichero y no
    puede. En AMC había dos rotos así meses antes de verse (improvements_tl.md, 2026-08-27), y el
    2026-10-21 `especialista-ux-ui.md` de webs lo está. `claude plugin validate .claude/agents
    --strict` no lo caza: medido el 2026-10-21 (2.1.304), pasa en verde con `description: [sin cerrar`.

    Roto: el frontmatter no parsea, no es un mapa, o le falta `name` o `description` (los dos
    obligatorios). Aviso: un `.md` en agents/ sin frontmatter (puede ser documentación a propósito,
    pero Claude Code no lo carga como agente). README.md no cuenta. Solo el primer nivel de agents/:
    las subcarpetas son la memoria y el material de cada agente, no definiciones.
    """
    import re
    import pathlib as _p
    d = _p.Path(ROOT) / ".claude" / "agents"
    if not d.exists():
        return
    try:
        import yaml
    except ImportError:
        hallazgos.append(("aviso", rel(str(d)), "sin PyYAML no se valida el frontmatter de los agentes",
                          "instala PyYAML (pip install pyyaml) para que este check mire algo"))
        return
    for f in sorted(d.glob("*.md")):
        if f.name == "README.md":
            continue
        t = leer(f).lstrip("﻿").replace("\r\n", "\n")
        if not re.match(r"---[ \t]*\n", t):
            hallazgos.append(("aviso", rel(f), "en agents/ y sin frontmatter",
                              "Claude Code no lo carga como agente; si es documentación, sácalo de agents/"))
            continue
        # el cierre es una LÍNEA con ---, no un --- cualquiera: `description: "uno --- dos"` es YAML válido
        cierre = re.search(r"^---[ \t]*$", t[t.index("\n") + 1:], re.M)
        if not cierre:
            hallazgos.append(("roto", rel(f), "el frontmatter no se cierra con ---",
                              "el agente no se puede leer"))
            continue
        try:
            fm = yaml.safe_load(t[t.index("\n") + 1:][:cierre.start()])
        except yaml.YAMLError as e:
            motivo = str(e).splitlines()[0]
            hallazgos.append(("roto", rel(f), f"el frontmatter no es YAML válido ({motivo})",
                              "si la description lleva «: », ponla entre comillas o con `description: >-`; "
                              "Claude Code lo tolera y las herramientas que leen el agente, no"))
            continue
        if not isinstance(fm, dict):
            hallazgos.append(("roto", rel(f), "el frontmatter no es un mapa clave: valor",
                              "el agente no se puede leer"))
            continue
        faltan = [k for k in ("name", "description") if not fm.get(k)]
        if faltan:
            hallazgos.append(("roto", rel(f), f"al frontmatter le falta {', '.join(faltan)}",
                              "son obligatorios: sin ellos Claude Code no carga el agente"))


def matchers_de_hooks(hallazgos):
    """Un matcher de hook es una regex sobre el NOMBRE de la tool. `Bash(git push*)` no casa nunca.

    Es la sintaxis de `permissions`, no la de `hooks` (harness-gotchas.md §matchers). Medido: el
    gate de RAM del template y la prohibición de git de EvoPreven llevaban meses así, en silencio.
    """
    s = os.path.join(CLAUDE, "settings.json")
    if not os.path.exists(s):
        return
    try:
        cfg = json.loads(leer(s))
    except json.JSONDecodeError:
        return                                  # ya lo informa hooks_de_settings
    for evento, grupos in (cfg.get("hooks") or {}).items():
        for g in grupos if isinstance(grupos, list) else []:
            m = g.get("matcher") or ""
            if re.search(r"[A-Za-z]\(", m):
                cmds = ", ".join(os.path.basename(h.get("command", "").split()[-1]) for h in g.get("hooks") or [])
                hallazgos.append(("roto", f"settings.json · {evento}",
                                  f"matcher {m!r} usa sintaxis Tool(patrón) ({cmds})",
                                  "el matcher es regex sobre el nombre de la tool: NO casa nunca. Usa "
                                  "'Bash' y filtra el comando dentro del script (y bloquea con exit 2)"))


def _hooks_registrados(cfg):
    """[(evento, matcher, script, handler)] de cada hook de settings que apunta a un hooks/*.sh|py."""
    out = []
    for evento, grupos in (cfg.get("hooks") or {}).items():
        for g in grupos if isinstance(grupos, list) else []:
            for h in (g.get("hooks") or []):
                m = re.search(r"hooks/([\w.-]+\.(?:sh|py))", h.get("command", ""))
                if m:
                    out.append((evento, g.get("matcher") or "", m.group(1), h))
    return out


def _fecha_de(ts):
    return (ts or "")[:10]


def hooks_sin_efecto(hallazgos):
    """Un hook registrado que CORRE pero no produce lo que debía (TPL-21, harness-gotchas.md).

    `hooks_de_settings` solo mira que el fichero exista y sea ejecutable, y por eso daba «OK» con el
    registro de agentes sin escribir ni una línea automática (2026-10-17: 15 líneas, todas manuales,
    frente a 420 llamadas Agent en el audit-log). Aquí: si el audit-log (que sí funciona) ve
    llamadas Agent/Task DESPUÉS de que el hook y su registro quedaron como están, y el registro no
    tiene ni una línea automática desde entonces, el hook está muerto aunque exista.
    Los dos ficheros viven fuera del repo; se respetan CLAUDE_AUDIT_DIR y CLAUDE_REGISTRY_DIR.
    """
    s = os.path.join(CLAUDE, "settings.json")
    if not os.path.exists(s):
        return
    try:
        cfg = json.loads(leer(s))
    except json.JSONDecodeError:
        return
    reg = [r for r in _hooks_registrados(cfg) if r[2] == "agent-registry-log.sh"]
    if not reg:
        return
    slug = os.path.basename(ROOT)
    slugs = [slug]
    try:  # la clave del audit log es la raíz del repo principal (2.27); sin el script, la de antes
        sys.path.insert(0, os.path.join(CLAUDE, "scripts"))
        from audit_log import audit_file, key_root
        audit = str(audit_file(ROOT))
        # el hook usa la carpeta de la sesión: en un worktree puede ser la suya o la del repo principal
        slugs = list(dict.fromkeys([slug, key_root(ROOT).name]))
    except ImportError:
        audit = os.path.join(os.path.expanduser(os.environ.get("CLAUDE_AUDIT_DIR", "~/.claude/audit")),
                             re.sub(r"[^A-Za-z0-9_.-]", "-", slug) + ".jsonl")
    base_reg = os.path.expanduser(os.environ.get("CLAUDE_REGISTRY_DIR", "~/.claude/registry"))
    registros = [os.path.join(base_reg, s, "agentes.jsonl") for s in slugs]
    registro = " o ".join(registros)
    # Desde cuándo vale la evidencia: el más reciente entre el hook y el settings que lo registra.
    marcas = [os.path.getmtime(p) for p in (os.path.join(CLAUDE, "hooks", "agent-registry-log.sh"), s)
              if os.path.exists(p)]
    if not marcas or not os.path.exists(audit):
        return
    import datetime as _dt
    corte = _dt.datetime.fromtimestamp(max(marcas), _dt.timezone.utc).date().isoformat()
    llamadas = 0
    for ln in leer(audit).splitlines():
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if e.get("tool") in ("Agent", "Task") and _fecha_de(e.get("ts")) >= corte:
            llamadas += 1
    if not llamadas:
        return
    automaticas = 0
    for ln in "\n".join(leer(r) for r in registros).splitlines():
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if "automático" in str(e.get("trigger", "")) and str(e.get("fecha", "")) >= corte:
            automaticas += 1
    if not automaticas:
        hallazgos.append(("roto", "hooks/agent-registry-log.sh",
                          f"registrado, pero el audit-log ve {llamadas} llamada(s) Agent/Task desde {corte} "
                          f"y {registro} no tiene ni una línea automática",
                          "el hook corre y no escribe: agent_registry.py y harness-telemetry trabajan "
                          "con un registro vacío. Mira que lea tool_input.subagent_type (PostToolUse)"))


# Binarios que un hook puede invocar y que NO tienen por qué estar en la máquina. Se lista a mano (como
# CLI_ESPERADOS): descubrirlos por regex trae medio diccionario. Un `command -v X` en el script lo excusa.
BINARIOS_FANTASMA = ["openclaw", "notify-send", "telegram-send", "terminal-notifier"]


def hooks_con_fallos_repetidos(hallazgos):
    """Los cuatro fallos que se repiten en los hooks de los derivados (MO-36).

    1. matcher «Tool(patrón)»: lo cubre `matchers_de_hooks`.
    2. `exit 1` en un PreToolUse: solo el 2 bloquea; el 1 es «error no bloqueante» y la acción sigue.
    3. leer `CLAUDE_TOOL_*`: esas variables no existen (la entrada llega por stdin como JSON).
    4. invocar un binario ausente (openclaw): el hook sale en silencio sin hacer nada.
    """
    s = os.path.join(CLAUDE, "settings.json")
    if not os.path.exists(s):
        return
    try:
        cfg = json.loads(leer(s))
    except json.JSONDecodeError:
        return
    vistos = set()
    for evento, matcher, nombre, h in _hooks_registrados(cfg):
        ruta = os.path.join(CLAUDE, "hooks", nombre)
        if (nombre, evento) in vistos or not os.path.exists(ruta):
            continue
        vistos.add((nombre, evento))
        src = leer(ruta)
        codigo = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
        if evento == "PreToolUse" and re.search(r"(^|[;&{]\s*|\n\s*)exit\s+1\b", codigo) \
                and not re.search(r"\bexit\s+2\b", codigo) and h.get("onFailure") != "block":
            hallazgos.append(("roto", f"hooks/{nombre}",
                              "PreToolUse que sale con `exit 1` y nunca con `exit 2`: no bloquea nada",
                              "traduce el 1 a 2, o ponle onFailure: \"block\" si es un fallo del propio hook"))
        if re.search(r"CLAUDE_TOOL_\w+", codigo) and not re.search(r"sys\.stdin|cat\b|read\b|jq\b", codigo):
            hallazgos.append(("roto", f"hooks/{nombre}",
                              "lee CLAUDE_TOOL_*, variables que Claude Code no define",
                              "la entrada llega por stdin como JSON ({tool_name, tool_input})"))
        for b in BINARIOS_FANTASMA:
            if re.search(rf"(^|[\s;&|(`$]){re.escape(b)}\s", codigo) and not shutil.which(b) \
                    and not re.search(rf"(command -v|which|type)\s+{re.escape(b)}", codigo):
                hallazgos.append(("roto", f"hooks/{nombre}",
                                  f"llama a `{b}`, que no está instalado, sin comprobarlo",
                                  "el hook no hace nada y nadie se entera; usa el canal que exista "
                                  "(scripts/avisar.py) o guarda con `command -v`"))


# Desde qué versión de Claude Code existe cada clave que un settings puede usar (doc env-vars y
# settings-reference, 2026-10-21). Una clave que la instalación no conoce se ignora EN SILENCIO: el
# tope o el modo que creemos puesto no está.
VERSION_DE_LA_CLAVE = {
    "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": "2.1.217",
    "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "2.1.217",
    "CLAUDE_CODE_TOOL_MEMORY_LIMIT": "2.1.233",
    "CLAUDE_CODE_TOOL_MEMORY_CGROUP_EXCLUDE": "2.1.246",
    "CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS": "2.1.269",
}


def _version(texto):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", texto or "")
    return tuple(int(x) for x in m.groups()) if m else None


def version_y_topes(hallazgos):
    """La instalada conoce las claves que el settings usa, y los topes cuadran con check-ram.sh.

    Sub-ola 2.01 (CL-D3, CL-7, CL-D2). Cuatro cosas, todas sobre el `settings.json` del proyecto:
      · el Claude Code instalado ≥ la versión que exigen sus claves (VERSION_DE_LA_CLAVE): una clave
        más nueva que el binario se ignora sin avisar (roto). La versión mínima la dan las claves, no
        un `minimumVersion` en el settings: ese es el suelo del auto-update y uno de proyecto pisaría
        el del usuario. Si alguien lo declara por debajo de lo que piden las claves, aviso;
      · los dos topes de concurrencia = MB_PER_SESSION ÷ MB_PER_AGENT de `hooks/check-ram.sh`;
      · `CLAUDE_CODE_TOOL_MEMORY_LIMIT` en un settings de PROYECTO: el cgroup es uno por usuario y
        máquina (medido el 2026-10-21), así que su valor reescribe el tope de todas las sesiones;
      · `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` = "1": apagado por defecto (CL-D2).
    """
    s = os.path.join(CLAUDE, "settings.json")
    if not os.path.exists(s):
        return
    try:
        cfg = json.loads(leer(s))
    except json.JSONDecodeError:
        return                                  # ya lo informa hooks_de_settings
    env = cfg.get("env") or {}
    usadas = {k: v for k, v in VERSION_DE_LA_CLAVE.items() if k in env}
    if usadas:
        necesita = max(usadas.values(), key=_version)
        declarada = cfg.get("minimumVersion")
        if declarada and (_version(declarada) is None or _version(declarada) < _version(necesita)):
            hallazgos.append(("aviso", "settings.json · minimumVersion",
                              f"declara {declarada!r} y sus claves piden la {necesita}",
                              "el suelo del auto-update queda por debajo de lo que el fichero usa"))
        # TL_CLAUDE_VERSION: solo para la autoprueba (simular una instalación vieja sin tocar la real)
        texto = os.environ.get("TL_CLAUDE_VERSION")
        if texto is None:
            try:
                texto = subprocess.run(["claude", "--version"], capture_output=True, text=True,
                                       timeout=15).stdout
            except (OSError, subprocess.SubprocessError):
                texto = ""
        instalada = _version(texto)
        if instalada and instalada < _version(necesita):
            viejas = ", ".join(k for k, v in sorted(usadas.items()) if _version(v) > instalada)
            hallazgos.append(("roto", "settings.json · versión de Claude Code",
                              f"instalado {'.'.join(map(str, instalada))} y el settings usa claves de la "
                              f"{necesita} ({viejas})",
                              "esas claves se ignoran sin avisar: los topes que creemos puestos no están"))
    ram = leer(os.path.join(CLAUDE, "hooks", "check-ram.sh"))
    ms, ma = (re.search(rf"^{n}=(\d+)", ram, re.M) for n in ("MB_PER_SESSION", "MB_PER_AGENT"))
    if ms and ma:
        n = int(ms.group(1)) // int(ma.group(1))
        for k in ("CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS", "CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS"):
            if str(env.get(k)) != str(n):
                hallazgos.append(("aviso", f"settings.json · env.{k}",
                                  f"vale {env.get(k)!r} y check-ram.sh da {n} "
                                  f"({ms.group(1)} MB ÷ {ma.group(1)} MB)",
                                  "el tope de concurrencia no sale de la fuente única de límites"))
    if "CLAUDE_CODE_TOOL_MEMORY_LIMIT" in env:
        hallazgos.append(("aviso", "settings.json · env.CLAUDE_CODE_TOOL_MEMORY_LIMIT",
                          f"fijado en el settings del proyecto ({env['CLAUDE_CODE_TOOL_MEMORY_LIMIT']!r})",
                          "el cgroup es uno por usuario y máquina: la última sesión que arranca reescribe "
                          "el tope de todas (rules/ram-pytest.md §Los topes que pone Claude Code)"))
    if str(env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")) == "1":
        hallazgos.append(("aviso", "settings.json · env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS",
                          "agent teams encendido para todo el proyecto",
                          "cambia la delegación normal; apagado por defecto y encendido por sesión con "
                          "--settings (CL-D2, rules/parallelization.md §Agent Teams)"))


def presupuesto_instrucciones(hallazgos):
    """Las rules sin `paths:` se cargan en TODAS las sesiones (check_instrucciones.py)."""
    scr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_instrucciones.py")
    if not os.path.exists(scr):
        return
    r = subprocess.run([sys.executable, scr, ROOT, "--json", "--sin-anclas"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode == 2:
        return
    try:
        m = json.loads(r.stdout)
    except json.JSONDecodeError:
        hallazgos.append(("aviso", "check_instrucciones.py", "no devolvió JSON", "revísalo"))
        return
    if r.returncode == 1:
        top = sorted(m["siempre"], key=lambda x: -x["chars"])[:3]
        hallazgos.append(("roto", "instrucciones siempre cargadas",
                          f"{m['total_proyecto']:,} chars > presupuesto {m['presupuesto']:,} · más grandes: "
                          + ", ".join(f"{t['fichero']} ({t['chars']:,})" for t in top),
                          "cada sesión paga esas reglas aunque no las use; ponles paths: "
                          "(harness-gotchas.md §Instrucciones)"))


# Generadores con `--check` y el fichero que producen. Si el fichero no existe en el proyecto medido
# (un derivado sin `.docs/core/`, sin `documentation/`…), ese generador no aplica y no se corre.
GENERADORES = [
    ("gen_skill_index.py",  ".claude/skills/README.md"),
    ("gen_agent_index.py",  ".claude/agents/README.md"),
    ("gen_agent_system.py", ".claude/AGENT-SYSTEM.md"),
    ("gen_docs.py",         "documentation/estado.html"),
    ("gen_inventario.py",   ".claude/inventario.json"),
    ("progress_index.py",   ".docs/plans"),
    ("gen_core.py",         ".docs/core/core.json"),
    # Packs (sub-ola 1.08): 0 piezas sin pack ni en dos, perfiles en sus topes y el catálogo de
    # selection-criteria.md al día. Es de solo-template: en un derivado no existe y no se corre.
    ("gen_packs.py",        ".claude/packs/packs.yaml"),
    # Paquetes de dominio (3.57): catálogo, fichas y cuestionario coherentes (solo-template) y, en un
    # derivado con dominio, los ficheros de los auditores al día con su domain.yaml (NE-14).
    ("domain_packs.py",     ".claude/domains/catalog.yaml"),
    ("gen_agent_domain.py", ".docs/domain/domain.yaml"),
]


def generados_al_dia(hallazgos):
    """Un índice generado que nadie regenera miente igual que uno escrito a mano (LI-32).

    Corre el `--check` de cada generador del proyecto medido. Es un aviso y no un roto: el fichero
    sigue ahí y el arreglo es una línea (regenerar), pero un `--check` en rojo que nadie corre es
    el mismo fallo silencioso que este script existe para cazar.
    """
    sdir = os.path.join(CLAUDE, "scripts")
    for script, objetivo in GENERADORES:
        ruta = os.path.join(sdir, script)
        if not os.path.exists(ruta) or not os.path.exists(os.path.join(ROOT, objetivo)):
            continue
        try:
            r = subprocess.run([sys.executable, ruta, "--check"], capture_output=True, text=True,
                               timeout=120, cwd=ROOT)
        except (OSError, subprocess.SubprocessError) as e:
            hallazgos.append(("aviso", f"scripts/{script}", f"`--check` no se pudo correr: {e}",
                              "no se sabe si lo que genera está al día"))
            continue
        if r.returncode != 0:
            primera = next((l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip()),
                           f"exit {r.returncode}")
            hallazgos.append(("aviso", f"scripts/{script} --check", primera[:160],
                              f"`{objetivo}` no refleja el disco: regenéralo con `python3 .claude/scripts/{script}`"))


# Índices escritos a mano que el template mantiene (los generados los cubre generados_al_dia).
# `INDEX.md` es uno de los dos índices; los demás son los índices de carpeta a los que enruta.
INDICES_A_MANO = [".claude/INDEX.md", ".claude/workflows/README.md",
                  ".claude/templates/html/README.md", "documentation/README.md",
                  "resources/INFO-INDEX.md"]     # este lo lee create-agent para elegir skills
# Un contador de piezas escrito a mano. Una medida FECHADA en la misma línea es honesta por
# construcción (dice cuándo era verdad), así que no cuenta.
_CONTADOR = re.compile(r"\b\d+\s+(?:ficheros|skills|agentes|commands|comandos|slash-commands|"
                       r"workflows|hooks|rules|reglas|scripts|plantillas|auditores(?:-persona)?)\b")
_FECHA = re.compile(r"\b20\d\d-\d\d-\d\d\b")
# Skills que trae Claude Code (o un plugin oficial) y no viven en `.claude/skills/`.
SKILLS_INTEGRADAS = {"security-review", "simplify", "code-review", "init", "review", "loop",
                     "schedule", "frontend-design", "superdesign"}
_PREFIJOS = ("rules/", "skills/", "agents/", "commands/", "hooks/", "scripts/", "templates/",
             "workflows/", "patterns/", "examples/", "smoke/", "docs/", ".claude/", ".docs/",
             "documentation/", "resources/", "knowledge/", "_archive/")


def indices_sin_mentiras(hallazgos):
    """Lo que un índice escrito a mano puede decir mal sin que nadie lo note (LI-32, 2026-10-20):
    un contador que se queda viejo («501 ficheros» con 698), una ruta o una skill que ya no existe
    (CATALOG.md ofrecía `boris-plan-mode` meses después de archivarla) y, en los índices de carpeta,
    una pieza en disco que el índice no nombra (a `workflows/README.md` le faltaban cinco).

    Una ruta en una línea que habla de lo retirado (`archiv…`, `retir…`) se deja: nombrar lo que se
    fue, con su fecha, es justo lo que un índice honesto hace."""
    for relp in INDICES_A_MANO:
        f = os.path.join(ROOT, relp)
        if not os.path.exists(f):
            continue
        base_local = os.path.dirname(f)
        dentro = False
        for n, linea in enumerate(leer(f).splitlines(), 1):
            if linea.lstrip().startswith("```"):
                dentro = not dentro
                continue
            if dentro:
                continue
            if not _FECHA.search(linea):
                for m in _CONTADOR.finditer(linea):
                    if re.search(r"(?:más|menos) de\s*$|hasta\s*$|[<>≥≤]\s*$", linea[:m.start()]):
                        continue                    # un umbral («más de 25 agentes»), no un recuento
                    hallazgos.append(("aviso", f"{relp}:{n}", f"contador a mano «{m.group(0)}»",
                                      "se queda viejo en cuanto cambia el disco: cítalo del generado "
                                      "(AGENT-SYSTEM.md, estado.html) o fecha la medida"))
            if re.search(r"archiv|retir|antes `|hasta el", linea, re.I):
                continue
            for m in re.finditer(r"`([^`\s]+)`", linea):
                crudo = m.group(1).rstrip(".,;:)")
                tok = crudo.rstrip("/")
                if any(c in tok for c in "*<>{}[]$…|") or tok.startswith(("/", "-", "http")):
                    continue
                if tok.startswith(_PREFIJOS):
                    # `resources/` sin prefijo es la de la RAÍZ (convención de INDEX.md): la de dentro
                    # se cita entera, `.claude/resources/…`. Resolverla también contra .claude/ daba
                    # por buena una cita que, seguida al pie de la letra, no lleva a nada.
                    bases = (ROOT,) if tok.startswith("resources/") else (ROOT, CLAUDE, base_local)
                    if crudo.endswith("/") and any(os.path.isdir(os.path.join(b, os.path.dirname(tok)))
                                                   for b in bases):
                        continue                    # carpeta DESTINO («van a `x/`»): se crea al escribir
                    if not any(os.path.exists(os.path.join(b, tok)) for b in bases):
                        hallazgos.append(("aviso", f"{relp}:{n}", f"cita `{tok}`, que no existe",
                                          "el índice manda a leer algo que no está"))
            # «skill `x`», y cualquier `boris-…` (el nombre ya dice que es una skill), salvo tachada
            nombres = re.findall(r"\bskills?\s+\**`([a-z0-9][a-z0-9-]+)`", linea)
            nombres += re.findall(r"(?<![\w-])(boris-[a-z][a-z-]*[a-z])\b", re.sub(r"~~.*?~~", "", linea))
            for nombre in dict.fromkeys(nombres):
                if nombre in SKILLS_INTEGRADAS:
                    continue
                if not os.path.exists(os.path.join(CLAUDE, "skills", nombre, "SKILL.md")):
                    hallazgos.append(("aviso", f"{relp}:{n}", f"enruta a la skill `{nombre}`, que no existe",
                                      "una ruta de lectura hacia una pieza archivada o mal escrita"))
    # Cobertura de los índices de carpeta: cada pieza en disco, nombrada.
    for relp, patron, forma in ((".claude/workflows/README.md", "*.js", "`/{}`"),
                                (".claude/templates/html/README.md", "*.html", "`{}`")):
        f = os.path.join(ROOT, relp)
        if not os.path.exists(f):
            continue
        texto = leer(f)
        import glob as _glob
        for pieza in sorted(_glob.glob(os.path.join(os.path.dirname(f), patron))):
            nombre = os.path.basename(pieza)
            clave = forma.format(nombre[:-3] if patron == "*.js" else nombre)
            if clave not in texto:
                hallazgos.append(("aviso", relp, f"no nombra `{nombre}`, que está en disco",
                                  "nace invisible: quien lee el índice no sabe que existe"))
    # La plantilla config-builder ofrece skills y agentes por nombre: tienen que existir.
    cb = os.path.join(CLAUDE, "templates", "html", "config-builder.html")
    if os.path.exists(cb):
        txt = leer(cb)
        for lista in ("SKILLS_UNIV", "SKILLS_ROLE", "SKILLS_AUDIT"):
            m = re.search(r"const %s=\[(.*?)\];" % lista, txt)
            for nombre in re.findall(r'"([^"]+)"', m.group(1) if m else ""):
                if not (os.path.exists(os.path.join(CLAUDE, "skills", nombre, "SKILL.md"))
                        or os.path.exists(os.path.join(CLAUDE, "agents", nombre + ".md"))):
                    hallazgos.append(("aviso", "templates/html/config-builder.html",
                                      f"{lista} ofrece `{nombre}`, que no existe",
                                      "el prompt que genera pide a /create-agent una pieza archivada"))


# Los workflows que leen la web, y el lector que los pone en cuarentena (MO-74, sub-ola 2.18).
CUARENTENA = ("research-tecnico.js", "research-normativo.js", "plan-research.js")
_PARA_ACTUAR = {"Bash", "Edit", "Write", "NotebookEdit", "Agent", "Task"}


def workflows_en_cuarentena(hallazgos):
    """Cada `agent()` de un workflow que lee la web va con el lector de solo lectura, y el lector no
    tiene con qué actuar (MO-74, 2026-10-21).

    Una página web puede llevar instrucciones para un modelo, y los subagentes de un workflow corren en
    `acceptEdits` con el allowlist de la sesión (en el template, `Bash(*)`). La cuarentena es que el que
    lee no pueda actuar: `agentType: 'lector-web'` en TODOS los `agent()` de esos workflows (también la
    síntesis, que ve resúmenes de las páginas) y un `agents/lector-web.md` cuyo `tools` no tenga shell,
    escritura, subagentes ni MCP. Basta un `agent()` sin el lector, o una herramienta de más en el
    lector, para que la cadena vuelva a estar abierta, y nada lo diría. Se cuentan los `agent(` del
    código (sin comentarios) contra los `...LECTOR` que llevan; lo comprobó la sub-ola 2.18 quitando uno."""
    d = os.path.join(CLAUDE, "workflows")
    presentes = [w for w in CUARENTENA if os.path.exists(os.path.join(d, w))]
    if not presentes:
        return
    lector = os.path.join(CLAUDE, "agents", "lector-web.md")
    if not os.path.exists(lector):
        hallazgos.append(("roto", "agents/lector-web.md", "no existe y los workflows de research lo piden",
                          "agent() no encuentra el tipo: el research no arranca, o arranca sin cuarentena"))
    else:
        t = leer(lector)
        fm = t.split("---")[1] if t.lstrip().startswith("---") and t.count("---") >= 2 else ""
        m = re.search(r"^tools:[ \t]*(.+)$", fm, re.M)
        tools = {x.strip() for x in (m.group(1) if m else "").split(",") if x.strip()}
        de_mas = sorted(x for x in tools if x in _PARA_ACTUAR or x.startswith("mcp__"))
        if not m or de_mas:
            hallazgos.append(("roto", "agents/lector-web.md",
                              "sin `tools:` (hereda todas)" if not m else f"tiene {', '.join(de_mas)}",
                              "el lector en cuarentena puede actuar: una página con instrucciones llega a ejecutar"))
    for w in presentes:
        codigo = re.sub(r"/\*.*?\*/", "", leer(os.path.join(d, w)), flags=re.S)
        codigo = re.sub(r"^[ \t]*//.*$", "", codigo, flags=re.M)
        n_agent = len(re.findall(r"(?<![\w.$])agent\(", codigo))
        n_lector = len(re.findall(r"\.\.\.LECTOR\b", codigo))
        define = re.search(r"""const LECTOR = \{ ?agentType: ["']lector-web["'] ?\}""", codigo)
        # Un `agentType:` escrito DESPUÉS del `...LECTOR` lo pisa (`{ ...LECTOR, agentType: "x" }`):
        # el único `agentType` que puede haber es el de la definición (verificador de la 2.18).
        n_tipo = len(re.findall(r"\bagentType\s*:", codigo))
        if not define or n_agent != n_lector or n_tipo != 1:
            hallazgos.append(("roto", f"workflows/{w}",
                              "no define `LECTOR = { agentType: 'lector-web' }`" if not define
                              else f"{n_agent} agent() y solo {n_lector} con `...LECTOR`"
                              if n_agent != n_lector
                              else f"{n_tipo - 1} `agentType:` además del de LECTOR: lo pisan",
                              "un agente que lee contenido de fuera corre con todas las herramientas"))


def _proyectos_bajo(base, profundidad=3):
    """Directorios con .claude/settings.json bajo `base` (sin worktrees, venvs ni node_modules)."""
    out = []
    saltar = {"node_modules", ".git", ".venv", "venv", "worktrees", "__pycache__", "site-packages", "_archive"}
    base = os.path.abspath(base)
    for dirpath, dirnames, _ in os.walk(base):
        prof = dirpath[len(base):].count(os.sep)
        dirnames[:] = [d for d in dirnames if d not in saltar and not (d.startswith(".") and d != ".claude")]
        if os.path.isfile(os.path.join(dirpath, ".claude", "settings.json")):
            out.append(dirpath)
            dirnames[:] = []                       # no se baja dentro de un proyecto
        elif prof >= profundidad:
            dirnames[:] = []
    return sorted(out)


def _recorre_derivados(base, args):
    """`--root <carpeta que NO es un proyecto>`: mide cada proyecto que cuelgue de ella (MO-15).

    Sin esto había que lanzar el check a mano en cada derivado, y 12 proyectos no se revisan a mano.
    Cada uno se mide en su proceso (ROOT es global). Sale 1 si CUALQUIERA tiene un mecanismo roto.
    """
    proyectos = _proyectos_bajo(base)
    if not proyectos:
        print(f"{base}: ni es un proyecto (.claude/settings.json) ni contiene ninguno.")
        return 2
    total, resumen = 0, []
    for pr in proyectos:
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--root", pr, "--json"],
                           capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
        except ValueError:
            resumen.append((pr, None, None, [("el check no devolvió JSON", r.stderr.strip()[-120:])]))
            total += 1
            continue
        rotos = [(x["donde"], x["que"]) for x in d["rotos"]]
        total += len(rotos)
        resumen.append((pr, len(rotos), len(d["avisos"]), rotos))
    if args.json:
        print(json.dumps([{"proyecto": pr, "rotos": n, "avisos": a, "detalle": r}
                          for pr, n, a, r in resumen], ensure_ascii=False, indent=2))
        return 1 if total else 0
    for pr, n, a, rotos in resumen:
        print(f"{'✗' if rotos else '✓'} {pr}: {'?' if n is None else n} roto(s), {'?' if a is None else a} aviso(s)")
        for donde, que in rotos:
            print(f"      ✗ {donde}: {que}")
    print(f"\n{len(proyectos)} proyecto(s) · {total} mecanismo(s) roto(s) en total.")
    return 1 if total else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="solo lo roto")
    ap.add_argument("--root", help="proyecto a medir (por defecto, el repo donde vive este script); si es una carpeta SIN .claude/settings.json, mide cada proyecto que cuelgue de ella")
    ap.add_argument("--autoprueba-citas", action="store_true",
                    help="los sabotajes y controles del check de citas, uno por línea")
    args = ap.parse_args()
    if args.autoprueba_citas:
        res = _autoprueba_citas()
        for cid, debe, marcado in res:
            ok = debe == marcado
            print(f"  {'✓' if ok else '✗'} {cid}  {'rota' if debe else 'control'} → "
                  f"{'marcada' if marcado else 'callada'}")
        malos = sum(debe != marcado for _, debe, marcado in res)
        print(f"{len(res) - malos}/{len(res)} correctos")
        return 1 if malos else 0
    if args.root:
        global ROOT, CLAUDE
        ROOT = os.path.abspath(args.root)
        CLAUDE = os.path.join(ROOT, ".claude")
        if not os.path.isfile(os.path.join(CLAUDE, "settings.json")):
            return _recorre_derivados(ROOT, args)

    hallazgos = []
    for f in (hooks_de_settings, patrones_gitignore, comandos_citados, rutas_citadas,
              citas_se_ven_fallar,
              cuestionario_sin_fantasmas, speckit_scripts, agentes_sin_frontera, agentes_yaml, matchers_de_hooks,
              hooks_sin_efecto, hooks_con_fallos_repetidos, version_y_topes, presupuesto_instrucciones, generados_al_dia, indices_sin_mentiras,
              workflows_en_cuarentena):
        try:
            f(hallazgos)
        except Exception as e:                      # un check que revienta no debe tumbar el resto
            hallazgos.append(("aviso", f.__name__, f"el propio check falló: {e}", "revísalo"))

    rotos = [h for h in hallazgos if h[0] == "roto"]
    avisos = [h for h in hallazgos if h[0] == "aviso"]

    if args.json:
        print(json.dumps({"rotos": [dict(zip(("nivel", "donde", "que", "consecuencia"), h)) for h in rotos],
                          "avisos": [dict(zip(("nivel", "donde", "que", "consecuencia"), h)) for h in avisos]},
                         ensure_ascii=False, indent=2))
        return 1 if rotos else 0

    if rotos:
        print("MECANISMOS ROTOS — la norma está escrita y no se está aplicando:\n")
        for _, donde, que, cons in rotos:
            print(f"  ✗ {donde}\n      {que}\n      → {cons}\n")
    if avisos and not args.quiet:
        print("AVISOS — puede ser correcto, míralo:\n")
        for _, donde, que, cons in avisos:
            print(f"  · {donde}: {que}")
        print()
    if not rotos:
        print(f"OK: ningún mecanismo roto ({len(avisos)} aviso(s)).")
    else:
        print(f"{len(rotos)} mecanismo(s) roto(s) · {len(avisos)} aviso(s).")
    return 1 if rotos else 0


if __name__ == "__main__":
    sys.exit(main())
