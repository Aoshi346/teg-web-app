---
paths:
  - "**/conftest.py"
  - "**/pytest.ini"
  - "**/tox.ini"
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/tests/**/*.py"
  - ".claude/hooks/check-ram.sh"
  - ".claude/hooks/gate-ram-pytest.sh"
---
# RAM y pytest — límites duros del servidor

> **Cuándo aplicar:** SIEMPRE antes de correr cualquier test, lanzar agentes paralelos o abrir
> navegadores headless. Consolidada aquí desde CLAUDE.md (poda TPL-1, 2026-08-07) — el CLAUDE.md
> lleva el resumen; esta rule es el detalle; el **enforcement determinista es el hook
> `check-ram.sh`** (PreToolUse), no la prosa.

## Límites del servidor — la fuente es el hook, no esta prosa

⚠️ **Los números vivían en SEIS sitios hasta el 2026-09-11**: aquí, en `parallelization.md`,
`agent-teams.md`, `speckit-workflow.md`, `blackboard.md`, `loop-workflow.md`, `qa-loop.md` y
`CLAUDE.md` (las tres sueltas se fusionaron el 2026-10-20 en `parallelization.md` y
`goal-vs-loop.md`). Cambiar el umbral obligaba a tocarlos todos, y el que se olvidara dejaba escrita una
norma que ya no era cierta — que es el modo de fallo de `harness-gotchas.md` §"Una norma escrita no
es una norma aplicada". **Ahora la fuente única es `.claude/hooks/check-ram.sh`**, que los calcula para
la máquina en la que estés y los sabe decir:

```bash
bash .claude/hooks/check-ram.sh --explain    # los límites de ESTA máquina, ahora mismo
```

Esta rule conserva **el criterio y el porqué**; el resto del harness la cita a ella o al hook, y no
vuelve a escribir cifras.

| Recurso | Dónde está el valor (línea de `--explain`) | ¿Quién lo decide? |
|---|---|---|
| RAM total y RAM libre | «RAM total», «RAM libre ahora» | la máquina — **nunca se asume** |
| Reserva del sistema (umbral) | «Umbral»: un porcentaje del total con un suelo absoluto | el hook lo calcula |
| RAM por worktree / Tech Lead | «RAM por sesión» | criterio (una constante del hook) |
| Instancias simultáneas **en un repo** | «Tope de sesiones/repo»: **derivado** de la RAM libre por encima del umbral, mínimo 1 | el hook lo calcula |
| Agentes a la vez **dentro de una sesión** (subagentes, y aparte los de cada workflow) | «Agentes a la vez»: la RAM por sesión repartida a `MB_PER_AGENT`; va a los dos topes de concurrencia del `env` de `settings.json` | criterio (una constante del hook); `check_mechanisms.py` exige que el settings cuadre |
| Workers pytest | la línea de workers | criterio |
| Agentes con navegador (Playwright/Chrome) | cuentan **~doble**, con su propio tope, y NUNCA solapados con pytest | criterio: **esto NO se deriva** |

**Las cifras, quién las decidió y a qué sustituyeron** están en la cabecera de `check-ram.sh`, al lado
del código que las aplica: el umbral y el tope derivado son decisión del Usuario del 2026-09-11, y la
historia de los valores anteriores va con ellos. Aquí queda el porqué.

### El umbral (decisión del Usuario, 2026-09-11)

Un **porcentaje de la RAM total con un suelo absoluto**. El porcentaje escala con el hardware (el de
antes, más alto, apartaba en este servidor una reserva que no usaba nadie y bloqueaba trabajo en
paralelo legítimo); el suelo evita que en una máquina pequeña el porcentaje deje al sistema sin aire.

### El tope de instancias no es un número fijo (misma decisión)

El tope fijo de antes **venía de una máquina más pequeña, no de una medición**. Ahora sale de la RAM
que queda por encima del umbral, dividida por la RAM por sesión: cuántas caben **ahora** lo dice
`--explain`.

Dos cosas que hay que entender antes de "arreglar" la fórmula:

1. **Es auto-correctiva.** `free` *available* ya descuenta lo que consumen las sesiones vivas, así
   que el tope se estrecha solo conforme se llena la máquina. Por eso **no se le suman** las
   sesiones actuales: si se hiciera, el tope sería siempre mayor que la cuenta y no bloquearía nunca.
2. **El navegador sigue topado a mano.** El hook no puede saber qué sesión abre Chrome, así que
   esa parte es criterio humano y no se deriva de nada (el tope, en `--explain`).

> **Se ha visto fallar.** Los dos checks se probaron saboteándolos a propósito el 2026-09-11 (umbral
> imposible → bloquea por RAM; 5 sesiones con tope 2 → bloquea por concurrencia), y el 2026-10-20
> con procesos de juguete (`_archive/2026-10-20/medicion-2.04/`). Un gate que nunca has visto en rojo
> no es un gate (`verification.md`).

## Los topes que pone Claude Code: concurrencia sí, memoria todavía no (sub-ola 2.01, CL-7)

La regla nº 1 era prosa más el gate de pytest. Claude Code trae tres topes que la convierten en
mecanismo; medidos el 2026-10-21 con Claude Code 2.1.306 en un proyecto de juguete
(`_archive/2026-10-20/medicion-2.01/`):

- **`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` y `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`**, los dos a
  lo que da «Agentes a la vez» de `--explain`, en el `env` del `settings.json` del template (y de los
  derivados, vía `ensure_hooks.py`). Son **un tope por mecanismo**, no uno común: el primero cuenta los
  subagentes que corren en la sesión y el segundo, los agentes de **cada** workflow, que no entran en el
  de subagentes (doc `sub-agents` §Concurrent subagent limit: *"follow their own limits"*). Una sesión
  con subagentes y un workflow a la vez puede pasar de 8, y sus comandos se suman. Pasado el tope, el Agent
  tool rechaza el siguiente con *«Concurrent subagent limit reached. You can run 1 subagents at once.
  Do not retry»* (medido con tope 1; con 8, los dos se lanzan) y el workflow pone en cola (doc
  `env-vars`). Con ultracode el de subagentes no aplica (doc `sub-agents` §Concurrent subagent limit).
- **`CLAUDE_CODE_TOOL_MEMORY_LIMIT` NO está puesto, y no por olvido.** La doc lo describe como un tope
  por sesión, y en esta máquina **no lo es**:
  - el cgroup es **uno por usuario y máquina**: `/sys/fs/cgroup/user.slice/user-0.slice/claude-code-bash`.
    Dos `claude -p` a la vez, uno con `4G` y otro con `2G`, metieron sus comandos en ese mismo cgroup
    y su `memory.max` quedó en 2 GB para los dos: **la última sesión que arranca reescribe el tope de
    todas**;
  - **con swap, pasarse no mata: manda a swap.** Con tope de 300 MB, un `bytearray` de 600 MB terminó
    bien (`memory.events`: `max 5928`, `oom_kill 0`); solo se mata cuando ya no queda swap;
  - con `CLAUDE_CODE_TOOL_MEMORY_CGROUP_EXCLUDE` sin poner, la lista de procesos que entran en el tope
    la manda el servidor de Anthropic y puede cambiar; `all-new` deja solo Bash, PowerShell y Monitor.

  Consecuencia: un `4G` en el settings del proyecto (lo que pedía el item) sería un **fondo común de
  4 GB para los comandos de todas las sesiones de la máquina** que lo lleven, no 4 GB por Tech Lead.
  Como tope de máquina sí protege (un pytest desbocado se queda en su cgroup en vez de llevarse la RAM
  de los servicios), pero entonces su sitio es `~/.claude/settings.json`, uno por máquina, y su valor
  es otro. Queda pendiente del Usuario (informe de la sub-ola 2.01). Mientras tanto,
  `check_mechanisms.py` y `ensure_hooks.py` avisan si un proyecto lo fija.
- `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` se deja en su defecto (3 niveles). Si los subagentes
  anidados cuentan dentro del tope de concurrencia no lo dice la doc ni está medido (❔).

Verlo: `bash .claude/hooks/check-ram.sh --explain` (los valores) y, en una sesión de
`claude -p --debug-file <f>` con el tope puesto, la línea `tool cgroup: … limit=<bytes>` del debug.

## Antes de CUALQUIER pytest (PASO 1, siempre)

```bash
bash .claude/hooks/check-ram.sh && echo "vía libre"   # el gate real, con el umbral ya calculado
```

⚠️ **No cuentes instancias con `grep -c claude`**: engloba el daemon, los `bg-pty-host`/`bg-spare`,
los `tmux new … claude` y hasta shells cuyo path contiene `/root/.claude/`. Daba 13 "instancias"
donde había 3 y bloqueaba `pytest` siempre — un falso positivo que invita a saltarse el gate. El
hook reconoce una sesión **por el binario de Claude Code que corre** (no por la palabra «claude» en
la línea de comandos: así contaba también los workers de Vite/Vitest de `.claude/worktrees/`, MO-23),
con la RAM de una sesión de verdad, y **solo las de este repo**: bloquear por lo que hace otro
proyecto era el mismo falso positivo una capa más abajo (arreglado 2026-08-26).

**Lo dispara `gate-ram-pytest.sh` antes de cada comando que LANZA pytest**, y solo de esos: un
`echo`, un `grep pytest` o un mensaje de commit que nombra pytest no lo disparan; `.venv/bin/pytest`,
`python -m pytest`, `bash -c "… pytest …"`, `$R` con `R="… pytest …"` o un script que el comando
escribe o ejecuta **nombrando pytest**, sí. Lo que no ve: un script que corre pytest por dentro sin que
el comando diga «pytest» (`make test`, `bash backend/pt apps/x`) — para eso sigue el paso 1 de abajo, a
mano. Cuando bloquea, el motivo sale por stderr (la salida de `check-ram.sh`), que es lo que ve el agente.

## Pytest SIEMPRE en chunks

```bash
# ❌ PROHIBIDO — mata el servidor:
pytest                    # todo el proyecto
pytest tests/             # directorio completo
pytest -n auto            # auto workers
pytest --cov              # coverage = +RAM

# ✅ OBLIGATORIO:
pytest apps/MODULE/ -v --maxfail=3     # por módulo
pytest -k "test_name" -v               # test específico
pytest tests/file.py -v -x             # un archivo, para al primer fallo
pytest -n <N> tests/unit/algo/ -v      # N ≤ los workers de --explain
```

Muchos tests → chunks de ~20 con verificación de RAM entre cada uno:

```bash
pytest tests/unit/models/ -v --maxfail=3 && free -h | awk '/Mem:/{print $7}'
pytest tests/unit/views/ -v --maxfail=3
```

## Si ocurre OOM

1. Es **FALLO CRÍTICO** del Tech Lead — documentarlo en PROGRESS.log.
2. Reducir el scope de tests, esperar a que se libere RAM, reintentar con chunk más pequeño.

## Anti-patterns

- ❌ Correr pytest sin el `free -h` previo — la verificación de RAM es el paso 1, no opcional.
- ❌ Lanzar QA visual (3 personas con Chrome) en paralelo con pytest — revienta el límite.
- ❌ Confiar en que esta rule se leerá: el hook `check-ram.sh` es quien bloquea de verdad.
