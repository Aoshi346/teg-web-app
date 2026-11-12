---
paths:
  - ".claude/settings.json"
  - ".claude/settings.local.json"
  - ".claude/hooks/**"
  - "CLAUDE.md"
  - ".claude/CLAUDE.md"
  - "CLAUDE.local.md"
  - "**/run-job.sh"
---
# Gotchas del harness de Claude Code

> **Cuándo aplicar:** al operar el propio Claude Code (plan mode, caché, sesiones). Errores caros
> ya cometidos o documentados, consolidados desde CLAUDE.md (poda TPL-1, 2026-08-07).
>
> **Repasada el 2026-10-28 contra Claude Code 2.1.310** (MO-71): cada sección dice con qué versión se
> midió. Recomprobado ese día en el binario o en `claude --help` de la 2.1.310: `--autocompact`,
> `/simplify` («Quality only»), `/fork` · `/subtask` · `/branch` · `/cd` · `/btw` · `/recap` ·
> `/focus` · `/skill-doctor` · `/reload-skills`, `--bg`, `--worktree`/`--tmux`, las tres banderas del
> desatendido, el aviso de instrucciones y `/doctor prompt-audit`; y medida de nuevo la fila 6 del
> desatendido. Lo que no se re-midió lo dice su sección.

## EnterPlanMode / ExitPlanMode son HERRAMIENTAS, no comandos de sesión

```
# ✅ Correcto — dentro de la MISMA sesión:
EnterPlanMode → explorar → diseñar → ExitPlanMode → ejecutar

# ❌ Incorrecto: cerrar Claude y abrir sesión nueva "para entrar en plan mode"
#    → la sesión nueva empieza sin el contexto de la anterior y sin su caché (el «5-10x» que se
#      citaba aquí no tenía fuente; corregido 2026-10-20)
```

No se pierde contexto ni caché usándolos como tools.

## Caché TTL y CLAUDE.md — una edición a mitad de sesión NO se aplica

> ⚠️ **Corregido el 2026-10-20** (sub-ola 2.06) contra `code.claude.com/docs/en/prompt-caching`
> §Editing CLAUDE.md mid-session: *"Editing them mid-session does not invalidate the cache, but the
> edit also doesn't apply… The new content loads on the next `/clear`, `/compact`, or restart."*
> Esta sección decía que editarlo **rompía** el caché (TTL fijo de 5 min, coste «5-10x»): era falso,
> y el «5-10x» no tenía fuente. El TTL de la conversación principal es de **1 h** con suscripción
> dentro del plan y de 5 min con API key, créditos o proveedor cloud (misma página, §Which TTL each
> request gets). Comprobado de nuevo el 2026-10-28 (2.1.310): sin cambios.

**Regla (la conducta no cambia, cambia la razón):** edita CLAUDE.md solo al **inicio de sesión**,
porque lo que escribas a mitad no rige hasta `/clear`, `/compact` o reiniciar. Si surge algo urgente a
mitad, anótalo en `.ai/memory.md` (o en la memoria del proyecto) y aplica el cambio en la próxima
sesión. Coste de ignorarlo: seguir trabajando con la versión vieja creyendo que la nueva ya rige.

### Qué lo rompe y qué lo preserva — la lista entera

Heredado de `rules/memory.md` (la skill se archivó el 2026-08-22) (archivada 2026-08-22, CAP-BORISMEMORY). El `README.md` del
archivo daba esta mecánica por absorbida aquí, y **estaba a medias**: de los cinco rompedores que
traía la skill, esta rule solo listaba tres, y ninguno de los dos preservadores. Medido antes de
escribirlo:

```bash
# Anclado a HEAD a propósito: contra el fichero de trabajo daría 5 en cuanto esta tabla existe,
# y el comando pasaría a mentir. Contra el commit anterior sigue siendo reproducible.
git show HEAD:.claude/rules/harness-gotchas.md \
  | sed -n '/^## Caché TTL/,/^## /p' | grep -ci 'plan mode\|MCP'   # 0
```

| Rompe el caché | Lo preserva |
|---|---|
| Cambiar de modelo (cada modelo tiene su caché) | **Compactar** en vez de `/clear` (`/clear` resetea el prefijo entero) |
| Cambiar el effort, en la mayoría de modelos (no en Opus/Sonnet/Haiku 5.5 ni Fable 5.1 con suscripción o API key) | `/cd` — mueve la sesión de directorio **sin** reconstruir el prompt de sistema ❓ |
| Inactividad más larga que el TTL (1 h con suscripción, 5 min con API key) | Trabajar en bloques seguidos, sin ratos muertos |
| Que cambie el conjunto de tools cargadas (un MCP a mitad de sesión **sin** tool search) | Editar `CLAUDE.md` (no se aplica hasta `/clear`/`/compact`) · plan mode y cargar una skill (van como mensajes) |

**El principio que ordena la tabla** (doc `prompt-caching`): lo que rompe el caché es **cambiar el
prefijo** — el system prompt con las tools, o el modelo. `CLAUDE.md` va en el contexto del proyecto,
que solo se rehace al empezar, con `/clear` o con `/compact`; por eso editarlo no lo rompe… ni se aplica.

❓ **Lo que NO se ha podido comprobar, dicho como tal.** El TTL, el plan mode, el effort y los MCP
de la tabla ya salen de la doc `prompt-caching` (2026-10-20). Siguen sin comprobar el efecto de `/cd`
(la única fila marcada) y cualquier ahorro porcentual: son comportamiento del servidor, no del
binario. Trátalos como orden de magnitud, nunca como dato citable. Y editar ficheros del repo **no**
rompe el caché: su contenido entra en el contexto solo cuando Claude los lee (misma página, §Editing
files in your repository).

Lo que **sí** está medido en la instalación (v2.1.240, recomprobado en la 2.1.310) es que compactar es un mecanismo de primera
clase y no un apaño:

```bash
claude --version                                   # 2.1.310 (Claude Code), 2026-10-28
claude --help | grep -o -- '--autocompact[^ ]*'    # --autocompact
```

## CLAUDE.md — cómo se escribe y se mantiene (lo mínimo, para los proyectos)

> Lo que daba la skill `boris-claude-md` a cada proyecto, que se retiró el 2026-10-20 (sub-ola 2.08).
> Fuentes: `code.claude.com/docs/en/memory` y `best-practices` (2026-10-20). En el template, el
> detalle con fuentes y comprobación es la skill `claude-code-referencia` §1.

- **Capas, de lo más amplio a lo más cercano**: gestionada (`/etc/claude-code/CLAUDE.md`), usuario
  (`~/.claude/CLAUDE.md`), proyecto (`./CLAUDE.md` o `./.claude/CLAUDE.md`, versionado: contexto de
  **equipo**) y local (`./CLAUDE.local.md`, al `.gitignore`). Se **concatenan**; lo último que se lee es
  lo más cercano. Los `CLAUDE.md` de un subdirectorio entran cuando Claude toca ficheros de ahí.
- **`CLAUDE.local.md`** es para lo tuyo de este proyecto (URLs y puertos de tu sandbox, datos de
  prueba, rutas de tu máquina): nunca en el del equipo. En un worktree no existe: o lo copias con
  `.worktreeinclude`, o lo sacas a tu home y lo importas con `@~/.claude/<fichero>.md` (un import de
  fuera del proyecto pide aprobación la primera vez).
- **Corto**: la doc pide menos de 200 líneas por fichero; el techo de casa se mide en caracteres (§Otros).
  Lo que solo vale para una parte del código va a una rule con `paths:`; un procedimiento, a una skill.
  Partir con imports `@ruta` organiza, pero no ahorra contexto.
- **Qué va**: los comandos de build y test, las convenciones, lo que nunca se hace y un «What NOT to
  Change» (código defensivo que no se simplifica). **Qué no**: lo que Claude deduce del código
  (árbol de carpetas, dependencias, arquitectura); `/doctor` propone recortarlo.
- **Énfasis**: `IMPORTANT` en la línea que se salta, y solo en esa; si todo es importante, nada destaca.
- **Mantenerlo**: cuando Claude repite un error o tecleas la misma corrección otra vez, pídele que
  actualice el `CLAUDE.md` para que no vuelva a pasar, revisa la regla que propone y commitéala (`@claude`
  en un PR hace lo mismo con lo aprendido en ese PR). Lo que tiene que pasar sí o sí no va aquí: va en un
  hook o un permiso (§CLAUDE.md es ADVISORY).
- Una edición a mitad de sesión no rige hasta `/clear`, `/compact` o reiniciar (§Caché).

## CLAUDE.md es ADVISORY

La doc oficial es explícita: *"CLAUDE.md instructions are advisory — Claude is allowed to ignore
them"*. Lo crítico-si-se-ignora no vive en prosa: vive en **hooks** (deterministas) o **scripts
gate** (exit≠0). Ejemplos en casa: `check-ram.sh` (RAM), `task_progress.py --gate` (cierre de
wave), `spec_lint.py` (estructura de spec). CLAUDE.md queda para intención y routing.

## Una norma escrita no es una norma aplicada — compruébalo (TPL-21)

Tres fallos del propio template compartían forma: **la norma estaba escrita y era correcta, el
mecanismo que debía aplicarla estaba roto por un detalle, y ninguno fallaba haciendo ruido.** El
gate de RAM contaba mal las instancias; el `.gitignore` de las capturas usaba `*` donde tocaba `**`
y dejó entrar 71 MB; el comando de aviso de `CLAUDE.md` no existía y llevó meses tragándose el error
(desde el 2026-10-21 avisa `hooks/notify-telegram.sh`, que dice cuándo el aviso no llega).

Los tres se encontraron por casualidad. Para buscarlos a propósito:

```bash
python3 .claude/scripts/check_mechanisms.py       # exit 1 si hay un mecanismo roto
```

Comprueba que los hooks declarados existen y son ejecutables, que los patrones de `.gitignore` con
ruta casan con algo, que los comandos (y subcomandos) que la documentación manda ejecutar existen, y
que las rutas citadas en rules/skills/agents no son fantasmas. **Correrlo antes de propagar el
template a otro proyecto**: un mecanismo roto aquí se multiplica por cada copia.

Su límite, dicho en su propia cabecera: caza mecanismos **ausentes o inejecutables**, no mecanismos
que corren y razonan mal — el gate de RAM habría pasado este check.

## Los comandos del harness: lo que hay que saber, no el catálogo

**El catálogo NO vive aquí ni en ninguna rule** — se genera (`AGENT-SYSTEM.md`) o lo tienes delante
en la sesión. Lo que sí necesita estar escrito es lo que **contradice a algo que este repo ya
afirma**, porque eso no se descubre solo (retirado de esta misma sección (su contenido se rescató aquí el 2026-08-22), 2026-08-22 — el
porqué completo en `_archive/2026-08-22/README.md`).

- **`/simplify` no corre tests y no busca bugs.** `CLAUDE.md` lo pone como gate pre-PR obligatorio y
  no dice qué NO cubre. La descripción del propio comando en el build instalado (v2.1.240 y 2.1.310) lo dice
  con todas las letras: *"Quality only — it does not hunt for bugs; use `/code-review` for that"*.
  Y **no ejecuta tests**, así que no es la red de seguridad de nada: el verde lo sigue dando
  `pytest` y el gate de bugs es `/code-review`.
- **`/loop` no «expira a los 3 días» ni es el plugin `ralph-loop` — resuelto el 2026-10-21 (MO-30).**
  El template lo repitió como hecho en cinco sitios (`goal-vs-loop.md` y sus secciones de
  `/loop` y modo noche, `agent-security.md` §ASI10) sin fuente: no sale en el changelog. La doc de
  hoy (`code.claude.com/docs/en/scheduled-tasks`, descargada el 2026-10-20 a las 23:29 UTC) dice
  otra cosa, y es la que vale: `/loop` es una **skill integrada** que programa el prompt con las
  tools de cron de la sesión, y **las tareas recurrentes caducan a los 7 días** (disparan una última
  vez y se borran), con un máximo de 50 por sesión y solo con la sesión abierta y ociosa. El plugin
  `ralph-loop` es otra cosa —un Stop hook que re-inyecta el mismo prompt— y **ese** no tiene ningún
  tope de tiempo:

  ```bash
  P=~/.claude/plugins/cache/claude-plugins-official/ralph-loop/1.0.0
  find $P -type f -not -path '*/.in_use/*' | wc -l   # → 9 (manifiesto, README, LICENSE, hooks, script, 3 comandos; 2026-10-21)
  grep -rniE 'day|hour|expir|timeout' $P ; echo "exit=$?"   # → exit=1 : CERO coincidencias
  ```

  Consecuencia práctica: **no cuentes con que un `/loop` se pare solo antes de 7 días** ni con que
  `ralph-loop` se pare nunca sin `--max-iterations`. El criterio de parada explícito que exige
  `goal-vs-loop.md` (y su §N4, modo noche) es el mecanismo real. Hay **dos** mecanismos con nombres
  parecidos y nada en común: `/loop` (por reloj, muere con la terminal salvo que mandes la sesión al fondo con `/background` o `←`) y
  `/ralph-loop:ralph-loop` (por fin de turno). Detalle con fuentes: `goal-vs-loop.md` §`/loop` en
  detalle y, en el template, la skill `claude-code-referencia` §12.
- **Soltar una tarea en segundo plano: siete mecanismos distintos, y el nombre confunde.**
  Heredado de `rules/parallelization.md` §file claims (absorbió su §7) (archivada 2026-08-22), pero **re-medido** contra el
  build instalado — porque su propia corrección de agosto ya se había quedado vieja:

  | Quiero… | Mecanismo | Comprobado |
  |---|---|---|
  | Arrancar **esta** sesión ya en segundo plano | `claude --bg` / `--background` | `claude --help` → *"Start the session as a background agent"* |
  | Vigilar lo que quedó corriendo | `claude agents` | `claude --help` → *"Manage background agents"* |
  | Un **comando de shell** largo sin bloquear el turno | el parámetro `run_in_background` de la tool **Bash** | esquema de la propia tool |
  | Saltar entre local y web | `claude --teleport [session]` | `claude --help` |
  | **Copiar** esta conversación a una sesión de fondo y **seguir aquí** | `/fork` | binario v2.1.240 y 2.1.310: *"Copy this conversation into a new background session and keep working here"* |
  | Encargar una tarea lateral **con mi contexto** cuyo resultado **vuelve aquí** | `/subtask` | binario v2.1.240 y 2.1.310: *"Send a subagent off with your full context; its result comes back here"* |
  | **Bifurcar** la conversación en este punto y seguir por la otra rama | `/branch` | binario v2.1.240 y 2.1.310: *"Create a branch of the current conversation at this point"* |

  Los tres comandos en sesión (`/fork`, `/subtask`, `/branch`) **no salen en `claude --help`** —es
  una lista de flags de CLI, no de comandos— y por eso se dieron por muertos al re-medir. Están
  registrados en el binario y se comprueban así:

  ```bash
  BIN=$(readlink -f "$(command -v claude)")
  strings "$BIN" | grep -oE 'name:"(subtask|fork|branch)",description:"[^"]*"' | sort -u
  # → las 3 líneas, con su description literal (v2.1.240; en la 2.1.310 /fork trae además
  #   «Spawn a background agent that inherits the full conversation»)
  ```

  La diferencia entre los tres es **dónde acaba el trabajo**, y es lo único que hay que recordar:
  `/subtask` **vuelve** a esta conversación · `/fork` se va a una sesión aparte y **tú te quedas
  aquí** · `/branch` **te lleva** a ti a la rama nueva.

  Dos avisos: **`--run-in-background` no existe** (`claude --help | grep -c -- --run-in-background`
  → `0` en v2.1.240 y en la 2.1.310) — la confusión venía de que `run_in_background` es parámetro de una *tool*, no
  flag de la CLI; y **`--bg` sí existe hoy**, aunque la nota de 2026-08-08 que traía la skill decía
  que no había flag para eso. Moraleja aplicable a cualquier nota sobre el harness: **lleva fecha y
  se recomprueba**, no se hereda.
- **Los worktrees también tienen flag propio:** `claude -w, --worktree [name]` crea el worktree para
  la sesión y `--tmux` le monta la sesión de tmux (`claude --help`, v2.1.240 y 2.1.310). El detalle de dónde
  se crean y qué pide aprobación está en `parallelization.md` §3 (y, en el template, en la skill
  `claude-code-referencia` §4). El comando **en sesión**
  `/worktree` aparece en las cadenas del binario (`worktree switch`,
  `tengu_worktree_entered_existing`) pero **no he podido verificar su lista de subcomandos**: eso
  queda sin comprobar, no como hecho.
- **Un comando y una skill son la misma cosa desde hace tiempo:** `commands/<x>.md` y
  `skills/<x>/SKILL.md` crean el mismo `/<x>`. Los `commands/` existentes siguen
  valiendo; lo que añade la skill es carpeta propia, frontmatter y carga automática. Corolario ya
  escrito en `research-driven-planning.md` §"Coste oculto 2": **escribir "corre `/simplify`" dentro
  de una skill no ejecuta nada**.

## «Claude no hace lo que le dije» — el orden de diagnóstico (CL-27, 2026-10-20)

Antes de reescribir nada, mira qué cargó de verdad, de lo barato a lo caro:

```
/context → /memory · /skills · /hooks · /mcp · /permissions → /status → /doctor (o `claude doctor`)
        → /debug [qué pasa] → claude --debug[=hooks,mcp] → claude --safe-mode
```

Si el fichero cargó y Claude no lo sigue, el problema es cómo está escrito: `/doctor prompt-audit`.
Lo que tiene que pasar sí o sí no se arregla con prosa: hook o permiso (`layer-decision.md`). En
`/status`, la línea *Setting sources* dice qué ficheros de settings cargaron; la precedencia es
managed › `--settings` › `settings.local.json` › `settings.json` › `~/.claude/settings.json`.
Fuentes, tabla síntoma → causa y comprobación: skill `claude-code-referencia` §6 (en el template); en
la doc, `code.claude.com/docs/en/debug-your-config`.

## Higiene de contexto — tarea nueva, sesión nueva; rewind antes que corregir (CL-28, 2026-10-20)

| Situación | Qué usar |
|---|---|
| Empiezas una tarea nueva | Sesión nueva (`/clear`) |
| Claude tomó un camino equivocado | Rewind (`Esc` dos veces o `/rewind`) y volver a pedir con lo aprendido; con más de dos correcciones sobre lo mismo, `/clear` y un prompt mejor |
| La ventana se llenó a media tarea | `/compact <pista>` antes de que salte solo: compactando, el modelo está en su peor momento |
| Solo vas a necesitar la conclusión | Un subagente |
| Una duda sobre lo ya hablado | `/btw` (no entra en el historial y no usa tools) |
| Leer desde el móvil | `/recap` · `/focus` (con `/tui fullscreen`) · `/output-style concise` |
| Entender una explicación viendo un diagrama | `/output-style` → «Visual y explicativo» (diagrama al final; `rules/output-choice.md` §5) |

Fuentes (doc `best-practices`, `checkpointing`, `interactive-mode` y la guía de Thariq Shihipar del
15-04-2026) y límites del rewind (no deshace lo que cambió un Bash): skill `claude-code-referencia` §7.

## `claude -p` desatendido — siete gotchas medidos en producción (cosecha de Xera, 2026-09-05)

Medidos en un sistema de agentes residente con ~59 jobs de systemd que invocan `claude -p` sin
nadie delante (`/home/download/repos/agents.git`, `bin/run-job.sh` de 785 líneas, verificado contra
Claude Code 2.1.227). Antes de esta sección, **ninguno de los siete estaba escrito en el template**
(`grep -c` de `MAX_ARG_STRLEN`, `strict-mcp-config`, `bypassPermissions`, `additionalDirectories`,
`dontAsk`, `output-format json` sobre este fichero → 0). Dos sistemas los pagaron por separado.

| # | Gotcha | Cómo se descubrió | Qué hacer |
|---|---|---|---|
| 1 | **El prompt por argv tiene techo: 131.072 B** (`MAX_ARG_STRLEN`). Por encima, `execve` da `E2BIG` y el job muere **antes de llamar al modelo** | Un job con 512 KB de contexto recolectado murió en el primer segundo. Medido: `/bin/true` pasa con 131.000 B, falla con 200.000 | El prompt **por stdin**, nunca como argumento |
| 2 | Con `--output-format json`, **el error viaja por STDOUT y stderr queda vacío** | Tres caídas por cuota seguidas con el log diciendo «salió con código 1 tras 2s:» y detrás, nada | Al fallar, leer stdout además de stderr |
| 3 | `--strict-mcp-config` **sin** `--mcp-config` = **cero** servidores MCP | Es la forma canónica de invocar sin arrastrar plugins ni MCP de usuario | Úsalo a propósito en jobs; no lo esperes en interactivo |
| 4 | **`bypassPermissions` como modo de settings lo rechaza Claude Code corriendo como root — y engaña**: a mano funciona (`IS_SANDBOX=1` en terminal interactiva, ausente bajo systemd). **`dontAsk` deja correr Bash pero deniega la escritura en silencio**: el job sale «ok» sin haber guardado nada. `auto` no se cobra aparte en Pro, Max y Team (la cifra «10-15 % de tokens de más» que había aquí no tenía fuente: `code.claude.com/docs/en/auto-mode-classifier-billing`, corregido el 2026-10-20) | Jobs que «terminaban bien» y no dejaban fichero | Para jobs desatendidos, **`acceptEdits`** es el modo que funciona |
| 5 | **Orden de permisos: `deny` → `ask` → `allow`, gana el PRIMER match, la especificidad NO cuenta.** Un `Bash(*)` en `allow` no anula nada de arriba | Verificado contra la doc de permisos y contra el comportamiento real | Escribe el `deny` sabiendo que no admite excepciones |
| 6 | **Solo `Edit(ruta)` y `Read(ruta)` se evalúan contra ficheros.** `Write()`, `Glob()`, `Grep()` **se ignoran con aviso** — y una denegación ignorada es peor que no tenerla, porque parece que protege. Corolario de agosto (**ya no vale en la 2.1.310**, ver el aviso de abajo): `Read(secrets/**)` en `deny` no impedía `cat secrets/x` con `Bash(cat*)` en `allow`; hoy lo impide, pero no frena un script que abre el fichero | Una sesión real leyó `secrets/telegram.env` con el deny puesto (18-ago-2026); y el 2026-09-05 se midió el mismo agujero en `/home/agents` | Lo que falla caro va en un **hook** (`PreToolUse` con ruta **y** verbo lector); el `deny` es la segunda capa |
| 7 | **`additionalDirectories` es una verja aparte, no una lista de reglas**: `Read(**)` no la abre, ni `acceptEdits`. Y **`mcp__*` genérico en `allow` se ignora con warning**: los glob solo valen después de un `mcp__<servidor>__` literal; un `deny` de `mcp__*` deja la sesión sin ningún MCP | El 20-ago dejó la sesión del canal colgada dos veces en un diálogo de permiso | El default-deny de MCP va en la **admisión** (`enableAllProjectMcpServers: false`), no en `permissions.deny` |

Y el que parecía ordenar los otros seis, medido el 18-ago-2026 en Xera: *«en un workspace que todavía
no ha pasado el diálogo de confianza, Claude Code IGNORA las entradas de permisos; los hooks sí se
ejecutan»*. **Estaba mal generalizado** (SE-30, re-medido el 22-oct-2026 en 2.1.307) y son tres casos,
no uno: en **`claude -p`/SDK** sin confianza los **hooks corren**, el **`allow` del repo se ignora**
(stderr: *«Ignoring … permissions.allow entry … this workspace has not been trusted»*) y el **`deny`
se aplica** (un `Read` de `.env` con `deny Read(**/.env*)` salió *«denied by your permission
settings»*); en **interactivo** sin aceptar el diálogo, los hooks se **retienen** hasta aceptar y
`deny`/`ask` **no se ven afectados** (doc `permissions` §Project allow rules and workspace trust; no
se puede medir desde `-p`). La conclusión práctica de abajo sigue en pie —lo que falla caro va en un
hook, el `deny` es la segunda capa porque no cubre un `grep` ni un script—, pero ya **no** se apoya en
«los permisos se ignoran». Tabla y medición: `security.md` §Un `deny` no se aplica siempre.

> ⚠️ **Fila 6 re-medida el 2026-10-28 en la 2.1.310 (MO-71): el corolario del `cat` ya no vale.** Los
> `deny` de `Read`/`Edit` cubren también los comandos de fichero que Claude Code reconoce en Bash
> (`cat`, `head`, `tail`, `sed`, `tee`; doc `permissions` §Read and Edit y `claude-code-referencia`
> §8.4-8.5). Medido con `claude -p --model haiku --permission-mode acceptEdits --allowedTools 'Bash(cat *)'`
> y `deny: ["Read(./secreto.txt)"]`: `cat secreto.txt` salió en `permission_denials` y el modelo no vio el
> contenido; el control `cat libre.txt` pasó. Lo que sigue sin cubrir es **un script que abre el fichero
> por su cuenta** (`python3 x.py`): por eso lo caro sigue yendo en un hook y el `deny` es la segunda
> capa. Lo de agosto fue de otra versión.

### La receta del desatendido: modo en la orden, directorio limpio y tres banderas (sub-ola 2.01)

Medido el 2026-10-21 con Claude Code 2.1.306, `claude -p --model haiku` por suscripción, en proyectos
de juguete del scratchpad (`_archive/2026-10-20/medicion-2.01/`).

**1. El modo va en la orden (CL-D1).** Desde el 2026-10-21 el `settings.json` del template **no fija
`defaultMode`**: una sesión interactiva arranca en `auto` (visto en una sesión nueva: *«⏵⏵ auto mode on»*;
con el settings de antes, *«⏵⏵ accept edits on»*). Un `claude -p` sin modo arranca en **Manual** y
deniega lo que preguntaría: con el settings nuevo y sin bandera, un `Write` y un `Bash` salieron
`permission_denied` y el job terminó «success» sin hacer nada. Así que todo desatendido lleva:

```bash
claude -p --permission-mode acceptEdits --strict-mcp-config --output-format json …   # prompt por stdin (fila 1)
```

Y lo que `acceptEdits` no aprueba aunque el `allow` diga `Edit(**)`: las **rutas protegidas**
(`.claude/`, `.git`, `.mcp.json`…, salvo `.claude/worktrees/`; `claude-code-referencia` §8.7). Medido por el
verificador: la receta de `auto-dream-memory` escribió `MEMORY.md` y `.ai/memory.md` y se le denegó
`.claude/memory.json`, también con `--allowedTools`. Un desatendido que tiene que escribir en `.claude/` va en
`--permission-mode auto` (decide el clasificador) o deja ese paso para una sesión con alguien delante.

Y ojo con la confianza: en una carpeta que nunca pasó el diálogo, **los `allow` del repo no se usan**
(stderr: *«Ignoring 6 permissions.allow entries from .claude/settings.json: this workspace has not been
trusted»*). Medido: en `acceptEdits` el `Write` pasó y el `Bash` (un `echo` con variables) no; con
`--allowedTools Bash` en la orden, los dos. Para un cron: que el Usuario abra `claude` una vez en esa
carpeta y acepte, o las tools en la orden. Nunca `hasTrustDialogAccepted` a mano en `~/.claude.json`.

**2. Fuera del repo cuando no hace falta el repo (CL-18).** `claude -p` lanzado dentro de un proyecto
carga su harness entero: `CLAUDE.md`, rules, la lista de skills y agentes, y lo que inyectan sus
hooks de `SessionStart`. cold_calling_coach lo midió con su juez (`backend/core/providers/judge_claude_code.py`,
2026-08-26, antes de las `paths:` de T-109): **162.345 tokens dentro del repo y 12.504 en un directorio
limpio** con system prompt propio. Repetido hoy en un clon del template (ya con `paths:`), tokens de
entrada por llamada a «Responde solo: ok», dos veces cada uno:

| Cómo se lanza | Dentro del repo | Directorio vacío |
|---|---|---|
| Por defecto | 57.318 | 33.655 |
| Receta de juez: `--tools "" --disable-slash-commands --system-prompt "…" --exclude-dynamic-system-prompt-sections` | 14.235 | **897** |

Con el system prompt por defecto, el suelo (las tools y las skills de la cuenta) se come la
diferencia: 1,7×. Con la receta de juez, lo que queda es justo el harness: **×16**. Para un juez, un
clasificador o cualquier `-p` que no necesita el proyecto: `cwd` en un directorio vacío propio
(`mkdir -m 700`, no un `/tmp` compartido) y la receta de juez. Las cifras dependen del entorno (las
skills y plugins de la cuenta, las variables heredadas): el verificador de la sub-ola, en un entorno
limpio (`env -i`), midió 52.322 → 20.046 por defecto (×2,6) y 14.085 → 608 con la receta (×23). El
orden de magnitud no cambia.

**3. Tres banderas para desatendidos y rescate (CL-22)** (las tres en `claude --help` de la 2.1.306 y de la 2.1.310):

| Bandera | Desde | Qué hace (medido) | Para qué |
|---|---|---|---|
| `--permission-prompts none` | 2.1.259 | Deniega lo que preguntaría, sin esperar a nadie; el modo sigue decidiendo el resto (doc `headless` §Turn off permission prompts in unattended runs). En un `-p` a secas no cambia nada visible: desde la 2.1.302 ya se deniega | Un anfitrión de permisos (SDK o `--permission-prompt-tool`) que no debe quedarse esperando |
| `--restricted` | 2.1.248 | Quita Bash, Monitor, WebFetch, CronCreate, RemoteTrigger y Workflow (29 → 25 tools, con Glob y Grep), ignora los settings de usuario, proyecto y local (0 hooks) y no cargó el `CLAUDE.md` del juguete | El harness que prueba un chatbot o una skill: el modelo bajo prueba no puede ejecutar nada |
| `--safe-mode` | 2.1.169 | Apaga las personalizaciones: 0 hooks y sin `CLAUDE.md` (la palabra clave del juguete, desconocida); las 29 tools de serie siguen | Rescate cuando la configuración rompe la sesión (`recovery-patterns.md` §Cuando lo roto es la configuración) |

## Los matchers de hook son regex sobre el NOMBRE de la tool, no `Tool(patrón)` (medido 2.1.261; sin re-medir en la 2.1.310, `check_mechanisms.py` lo vigila)

Un `"matcher"` de hook se evalúa como **regex contra el nombre de la tool** («Bash», «Write|Edit»),
NO con la sintaxis `Tool(patrón)` que usan `permissions`. Consecuencia medida (sesión anidada, Claude
Code 2.1.261, por la sesión `panel` el 2026-09-06): `"matcher": "Bash(pytest*)"` **no casa nunca** —
la regex pide «Bash» seguido de «pytes…» y el nombre de la tool es solo «Bash». El `check-ram.sh` del
template llevaba así **desde que se escribió**: el gate anti-OOM era un cartel, no una puerta. Lo mismo
con `"Bash(git push --force*)"` → echo (redundante además con `permissions.deny`, que sí entiende esa
sintaxis).

**Y un segundo fallo encima:** un PreToolUse solo bloquea con **exit 2**; el 1 es «error no
bloqueante». `check-ram.sh` sale con 1, así que aunque el matcher hubiera casado, no habría frenado el
pytest.

**El patrón correcto** (implementado: `hooks/gate-ram-pytest.sh`): matcher **`Bash`**, el script lee
`tool_input.command` del stdin JSON, **filtra** (aquí, pytest), llama al comprobador canónico
(`check-ram.sh` verbatim) y **traduce su exit 1→2**. Cualquier otro comando: exit 0 en milisegundos.
Todos los gates de Bash de un settings van así, no con `Bash(docker compose*)` / `Bash(*makemigrations*)`.

**Filtrar es decidir si el comando LANZA la herramienta, no si la nombra** (MO-23, 2026-10-20). La
regex de antes casaba «pytest» detrás de cualquier espacio: bloqueaba un `grep pytest`, un mensaje de
commit o el encargo a otro agente que decía «no ejecutes pytest», y no veía `.venv/bin/pytest` ni
`bash -c "… pytest …"`. Ahora el gate trocea el comando como la shell (posición de comando, comillas,
heredocs, `$( )`, variables del propio comando) y lo prueba `_archive/2026-10-20/medicion-2.04/` contra
comandos reales. Lo que sigue sin ver: un script que corre pytest sin que el comando lo nombre
(`make test`, `bash backend/pt apps/x`): el camino rápido ni arranca el detector. **Y el
motivo, por stderr**: con exit 2, Claude Code le pasa al modelo el stderr y no el stdout; un gate que
bloquea sin decir por qué se acaba rodeando.

✅ Desde el 2026-10-14 `check_mechanisms.py` **sí lo caza** (`matchers_de_hooks`): un matcher con
`Tool(...)` es mecanismo roto. Se vio fallar sobre EvoPreven, donde la prohibición de commit/push y el
gate de RAM llevaban meses sin disparar. Y ojo con `--root`: sin él el script mide el template, no
el proyecto que le pasas por `cwd`.

## Instrucciones: Claude Code carga TODAS las rules salvo las que llevan `paths:` (medido 2.1.299; el aviso sigue en el binario de la 2.1.310)

El template creyó durante meses que las rules se leían «a demanda vía INDEX.md». **Falso.** Al
arrancar se cargan `CLAUDE.md`, `CLAUDE.local.md`, `.claude/CLAUDE.md` y **toda**
`.claude/rules/**/*.md` sin frontmatter `paths:`. Con 44 rules eran **547k caracteres (~135k tokens)
en cada sesión**, y salía este aviso:

```
45 instruction files add up to 547.2k chars, over the 150.0k-char total limit · /memory to free up context
```

- **Es un aviso de rendimiento, no un truncado.** Límite por fichero = `max(40k, 5 % de la ventana ×
  chars/token)`; límite total = `max(120k, límite por fichero)` → 150k con 1M de contexto.
- **`paths:` es la palanca.** Lista de globs estilo gitignore, relativos a la raíz del proyecto (acepta
  lista YAML, comas y llaves). La rule se inyecta cuando se toca (Read/Edit/Write) un fichero que casa,
  una vez por sesión (`load_reason: path_glob_match` en el hook `InstructionsLoaded`). `paths: "**"`
  cuenta como incondicional.
- **Las skills con `paths:` son más estrictas que las rules** (medido el 2026-10-28 en la 2.1.310,
  con una skill de juguete y `claude -p --model haiku`): hasta que se lee un fichero que case, la
  skill no sale en el listado (`¿ves la skill zeta?` → NO) y `/zeta` responde que no está instalada;
  tras leer `app/models.py`, sí. El binario la guarda aparte («conditional skills stored, activated
  when matching files are touched»). **Y un subagente que la precarga con `skills: [zeta]` tampoco la
  recibe** (respondió `SIN-SKILL`; el control sin `paths:`, la palabra clave). Úsalo solo en skills
  que siempre empiezan tocando ficheros de su stack, que no se piden de palabra ni las precarga ningún
  agente: en el template, solo `django-orm` (CL-23, 2.19).
- **Una rule sin fichero propio se ancla a sí misma** (`paths: [".claude/rules/<ella>.md"]`) y se
  abre desde `INDEX.md` o desde lo que inyecta `dispatch-hint.sh`.
- **El otro fallo silencioso:** una rule cuyos globs no casan con ningún fichero del proyecto no se
  carga nunca y no avisa. `check_instrucciones.py` lo lista como «sin ancla viva».
- **`claudeMdExcludes`** (settings) excluye ficheros por glob, también rules; no se usa aquí porque
  apaga también la carga condicional.

- **El listado de skills es el otro coste fijo** (AN-3, 3.18): el cuerpo de una skill no carga, su
  `description` sí, y el listado tiene un presupuesto del 1 % de la ventana; al pasarse, las menos
  usadas se quedan solo con el nombre. El mismo script lo mide (descriptions de skills, comandos y
  agentes del repo; sin plugins ni integradas, así que es cota inferior) y avisa; `--strict-listing`
  lo convierte en exit 1. Un `CLAUDE.md` de más de 40.000 caracteres da exit 1 aunque el total quepa.

```bash
python3 .claude/scripts/check_instrucciones.py [<proyecto>]   # exit 1 si se pasa del presupuesto (60k)
python3 .claude/scripts/check_instrucciones.py . --window 200000 --strict-listing   # con ventana de 200k
```

## Otros

- Un CLAUDE.md hinchado hace que Claude ignore las instrucciones reales (doc oficial). Techo del
  template **en caracteres**, no en líneas: lo fijo (CLAUDE.md + rules sin `paths:`) lo mide
  `check_instrucciones.py` contra su presupuesto (las líneas engañan: EvoPreven cabe con 401); el detalle vive en `rules/`, que **solo** sale del contexto si
  lleva `paths:` (§Instrucciones — sin él, mover texto de CLAUDE.md a una rule no ahorra nada).
- `file://` suele estar bloqueado para Playwright — sirve con `python3 -m http.server --bind 127.0.0.1` y navega a
  `http://127.0.0.1:<puerto>/...`.
- No hardcodees `/usr/bin/chromium-browser`: usa `scripts/screenshot.py`, que detecta el binario
  (google-chrome → chromium-browser → chromium → Chromium de Playwright). El python del sistema no
  trae playwright: `scripts/preparar_navegador.sh` crea o reutiliza el venv y lo prueba con una captura.
- ❌ **`/clear` por rutina.** Resetea el prefijo entero y con él el caché; para hacer sitio,
  compactar. `/clear` es para empezar algo que de verdad no tiene que ver con lo anterior.
- ❌ **Archivar una pieza dando su contenido "por absorbido" sin comprobar que llegó.** Pasó con la
  mecánica del caché de `boris-memory`: el `README.md` del archivo decía *"ya estaba en
  `harness-gotchas.md` §Caché — no se duplicó otra vez"* y allí faltaban dos rompedores y los dos
  preservadores. Al retirar algo, **grep en el destino** antes de escribir que ya está.
