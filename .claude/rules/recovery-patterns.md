---
paths:
  - ".claude/rules/recovery-patterns.md"
  - ".claude/smoke/kill-switch.md"
  - ".claude/hooks/guard-pkill.sh"
---
# Recovery Patterns — Recuperación de Sesiones Rotas

> **Cuándo aplicar:** Cuando una sesión termina mal, el contexto se corrompe, git queda en estado inconsistente, o el agente perdió el hilo.

---

## 🛑 Kill switch — PARAR al agente (esto va antes que recuperar)

Los 5 patrones de abajo **recuperan git**. No **detienen al agente**. Son cosas distintas y en una
emergencia hace falta primero la segunda: corremos varios TLs simultáneos (el tope lo deriva
`check-ram.sh` de la RAM libre — aquí son 9, no los 3 de antes), workflows en background
y agent-teams. Ctrl+C sirve para la sesión que tienes delante; no sirve para lo que corre en otra
terminal, en background o por cron.

**El kill real, desde OTRO shell:**

```bash
pgrep -ax claude                # qué va a caer: las sesiones de Claude Code (CLI, -p, cron, extensión)
pkill -x claude                 # las para todas
ps aux | grep '[c]laude'        # verificar que no queda nada colgando (servidores MCP, hijos)
```

> ⚠️ **Hasta el 2026-10-21 aquí ponía `pkill -f claude-code` y `pkill -f 'claude .*--print'`, y
> fallaba por los dos lados** (MO-53, medido en esta máquina con 2.1.304). (1) **No las paraba
> todas**: `claude-code` solo sale en la ruta de la extensión del editor
> (`…/anthropic.claude-code-…/native-binary/claude`); una sesión de terminal es `claude …` sobre
> `~/.local/share/claude/versions/<v>`, y de 10 sesiones vivas, `pgrep -f '[c]laude-code'` veía 9.
> Una `claude -p` lleva `-p`, no `--print`. `pgrep -x claude` (el nombre del proceso, no la línea)
> veía las 10. (2) **Lanzado por un agente, se mata a sí mismo**: el patrón está en la línea de
> órdenes de la shell que lo corre (§Parar un proceso). Con Claude Code instalado por npm el proceso
> se llama `node`: mira antes con `pgrep -af '[c]laude-code/cli'` (sin probar aquí: esta máquina usa
> el binario nativo).

Si el agente estaba a mitad de una escritura, **para primero y diagnostica después** — el estado
del working tree se arregla con los patrones de abajo; una acción destructiva en vuelo, no.

Orden de actuación en incidente:

1. `pkill -x claude` (parar la hemorragia).
2. `git status && git stash list` (ver qué quedó a medias) — **sin tocar nada todavía**.
3. Si tocó infra/producción: revisar antes que git (`terraform state list`, consola del cloud).
4. Elegir patrón de recuperación con el Decision Framework de abajo.
5. Registrar qué pasó en `PROGRESS.log` y, si fue un fallo del harness, en `.claude/improvements_tl.md`.

### Drill trimestral (obligatorio, ~5 minutos)

Un kill switch que nadie ha probado no es un kill switch. **Cada trimestre**: lanzar una tarea larga
de prueba, matarla desde otro shell y cronometrar. **Objetivo: <30 segundos** desde que decides
parar hasta que no queda ningún proceso.

Spec ejecutable y registro de resultados: **`.claude/smoke/kill-switch.md`**.
Contexto de por qué existe (ASI10 rogue agents, ASI08 cascading failures): `rules/agent-security.md`.

---

## 🔪 Parar un proceso sin matarte a ti mismo — nunca `pkill -f` con un patrón que está en tu comando

El Bash de Claude Code lanza cada comando como `/bin/bash -c "… eval '<el comando>' …"`: **el texto
del comando está en la línea de órdenes de esa shell** (`tr '\0' ' ' < /proc/$$/cmdline`).
`pkill -f <patrón>` mira la línea de órdenes de todos los procesos y se excluye a sí mismo, **pero no
a la shell que lo lanzó**, donde el patrón aparece literal. Esa shell muere (exit 144 en Claude
Code), lo que iba detrás no corre y nadie avisa. Lo mismo `kill $(pgrep -f X)` y
`pgrep -f X | xargs kill`.

No es raro: en los transcripts de esta máquina (sin EvoPreven ni gencat), **40 de 52** comandos con
`pkill -f` de las sesiones principales acabaron en exit 144, y 99 de 118 contando los de los subagentes. En EvoPreven dejó un worker parado sin aviso, dos veces (25-09); en
evolution quedó la memoria «matar por PID, no pkill -f». Y le pasó a la sub-ola que escribió esto.

| Para parar… | Así | No así |
|---|---|---|
| algo que lanzaste tú | por **PID**: `cmd & echo $! > .run/x.pid` … `kill "$(cat .run/x.pid)"`, o un `start/stop` que lo guarde | `pkill -f "http.server 8897"` |
| por nombre de proceso | `pkill -x <nombre>` — el nombre exacto, no la línea entera | `pkill -f <nombre>` |
| por línea de órdenes, si no hay más remedio | un patrón que **no case consigo mismo**: anclado al binario, `pkill -f '^/ruta/.venv/bin/celery '` (la shell empieza por `/bin/bash`); o con corchete, `pkill -f '[h]ttp.server 8897'`, que vale **solo si el patrón tampoco sale en el envoltorio** del Bash (`~/.claude/shell-snapshots/…`, los `export` de los plugins: `'[c]laude'` o `'[c]odex'` matan la shell) | el patrón tal cual |

Antes de matar, mira tu propia línea (`tr '\0' ' ' < /proc/$$/cmdline`) y qué caería con el mismo
patrón: `pgrep -af '[h]ttp.server 8897'`.

**Lo hace cumplir un hook, no esta tabla**: `hooks/guard-pkill.sh` (PreToolUse · Bash) bloquea con
exit 2 el `pkill -f`, el `kill` que recibe los PID de un `pgrep -f` (en `$( )`, por una variable, un `for`,
un `while read` o `| … | xargs kill`) cuyo patrón casa con el
propio comando o con lo que se sabe del envoltorio (también detrás de `if`/`then`/`do`/`!`, de
`sudo`/`timeout`/`env`/`nohup` con sus opciones, dentro de `$( )` o de comillas invertidas, y en un
`bash -c`), y dice qué usar. Deja pasar el anclado, `pkill` sin `-f`, `pkill -f -x`, `kill <PID>`,
`kill -0`, `-P`/`--parent` y `-u`/`-U` de otro usuario (no incluyen a la shell), lo que va en un heredoc o un
comentario y el patrón que llega en una variable. No ve los
`export` que los plugins meten en el envoltorio: cambian de una máquina a otra. Medido el 2026-10-21 en
`_archive/2026-10-20/medicion-2.13/` (`demo_pkill.sh` lo reproduce sobre un proceso de juguete;
`casos_pkill.py`, 93 casos y la cosecha).
Si el hook no arranca, deja pasar: no lleva `onFailure: "block"`. Medido en la 2.10 (PV-70): `onFailure: "block"` sí frena
cuando el script no existe (el `echo` benigno se deniega; sin él, pasa) y NO frena un hook que revienta por dentro y sale 0
(`rules/agent-security.md` §5b). `guard-pkill` queda así hasta la 2.12 (MO-12), que decide el `onFailure` de cada gate.

---

## Los 5 Patrones

### Patrón 1: Code-Only Recovery

**Cuándo:** Los cambios de código son correctos pero el contexto de la sesión se perdió.

```bash
# 1. Ver qué cambió (no depende del contexto de la sesión)
git diff HEAD~1

# 2. Leer PROGRESS.log para contexto
tail -30 .claude/PROGRESS.log

# 3. Leer PROGRESS.json para saber dónde quedó
cat PROGRESS.json | jq '.checklist[] | select(.done == false)'

# 4. Lanzar nueva sesión con contexto explícito
# "Continúa desde el paso [N]. Ya está hecho: [X, Y]. Falta: [Z]."
```

**Costo:** Bajo. El código está bien, solo hay que re-orientar al agente.

---

### Patrón 2: Conv-Only Recovery

**Cuándo:** La conversación se desvió o el agente tomó una dirección incorrecta, pero el código aún no se tocó (o se puede descartar).

```bash
# 1. Descartar cambios no commiteados
git checkout -- .   # solo si estás seguro

# 2. Volver al último commit limpio
git log --oneline -5
# git reset --soft HEAD~1  # si necesitas deshacer el último commit

# 3. Iniciar sesión nueva con el prompt más preciso
# Incluir: qué intentaste antes, por qué no funcionó, qué quieres exactamente
```

**Costo:** Bajo. Se pierde trabajo no commiteado, pero la base está limpia.

---

### Patrón 3: Full Recovery

**Cuándo:** Código roto + contexto perdido + git en estado incierto.

```bash
# 1. Diagnóstico primero — no toques nada todavía
git status
git log --oneline -10
git stash list

# 2. Identificar el último commit bueno
git log --oneline | head -20
# Busca el commit donde las cosas funcionaban

# 3. Crear branch de rescate desde ese punto
git checkout -b rescue/$(date +%Y%m%d-%H%M)
git reset --hard <hash-del-commit-bueno>

# 4. Cherry-pick commits que quieras salvar (si los hay)
git log main..rescue/broken --oneline
# git cherry-pick <hash>

# 5. Tests para validar que la base está limpia
pytest backend/apps/[module]/ -v

# 6. Re-implementar lo que faltaba con nueva sesión
```

**Costo:** Medio. Se puede perder trabajo pero garantiza base limpia.

---

### Patrón 4: Checkpoints + Git

**Cuándo:** Tarea larga, mejor prevenir que curar.

**Protocolo de checkpoints:**

```bash
# El agente DEBE hacer un commit al completar cada tarea de tasks.md
# No esperar al final de la wave

# Formato de commit de checkpoint:
git commit -m "checkpoint(wave-2): [tarea completada] — tests OK"

# Si algo sale mal después, el checkpoint es el punto de restauración
git log --oneline | grep checkpoint
git reset --hard <hash-checkpoint>
```

**En tasks.md, añadir después de cada tarea:**
```markdown
- [x] Implementar endpoint /api/ai-office/agent-hook/
  - checkpoint: `git commit -m "checkpoint(wave-2): agent-hook endpoint"`
```

**Costo:** Cero si se hace bien desde el principio.

---

### Patrón 5: Framework Recovery (Context Engineering)

**Cuándo:** El agente tiene el contexto correcto pero el output es consistentemente malo (alucinaciones, loops infinitos, scope creep).

El problema no es el estado del código — es el prompt/context.

```bash
# 1. Hacer /compact manual antes de continuar
# (evita context pollution de la sesión rota)

# 2. Re-leer los archivos críticos explícitamente
# .ai/memory.md — estado de sesión
# PROGRESS.json — qué está hecho
# .specify/sessions/[ID]/tasks.md — qué falta

# 3. Usar prompt-contracts antes de continuar
# GOAL: [exactamente qué lograr]
# CONSTRAINTS: [qué NO tocar]
# FORMAT: [qué archivos crear/modificar]
# FAILURE CONDITIONS: [qué no debe pasar]

# 4. Si hay alucinaciones de API/modelos:
# → Usar context7 MCP para verificar la documentación real
# → Añadir a .ai/mistakes.md para que no se repita
```

**Costo:** Medio. Requiere re-orientación pero no pérdida de código.

---

## Cuando lo roto es la configuración — arrancar en `--safe-mode` (CL-22, 2026-10-21)

**Cuándo:** la sesión no arranca o no se puede usar por algo del harness, no del código: un hook que
bloquea todos los turnos, un `settings.json` que dejó a la sesión sin herramientas, un plugin, un mod o
un MCP que cuelga el arranque, un `CLAUDE.md` que la desvía.

```bash
claude --safe-mode          # o CLAUDE_CODE_SAFE_MODE=1: sin CLAUDE.md, skills, plugins, hooks,
                            # MCP, comandos ni agentes propios; los permisos y las tools de serie, igual
```

Medido el 2026-10-21 (2.1.306, `claude -p` en un juguete): 0 hooks en vez de 3, el `CLAUDE.md` no se
cargó y las 29 tools de serie siguieron. Desde ahí se arregla el fichero culpable con las tools de
siempre y se vuelve a arrancar normal. **No** es un modo de trabajo: sin hooks no hay gate de RAM ni
aviso de fin. Para averiguar cuál es el culpable antes de rescatar, el orden de diagnóstico de
`harness-gotchas.md` §«Claude no hace lo que le dije» (`--safe-mode` es su último escalón). Las
políticas gestionadas (managed) siguen aplicando también aquí.

---

## Decision Framework — Qué patrón usar

```
¿El código commiteado está bien?
├── Sí → Patrón 1 (Code-Only)
└── No → ¿El código no commiteado se puede descartar?
    ├── Sí → Patrón 2 (Conv-Only)
    └── No → ¿Git está en estado incierto?
        ├── Sí → Patrón 3 (Full Recovery)
        └── No → ¿El problema es el prompt/contexto?
            ├── Sí → Patrón 5 (Framework)
            └── Tarea larga en curso → Patrón 4 (Checkpoints)
```

---

## Prevención — Lo que evita tener que recuperar

| Práctica | Qué previene |
|----------|--------------|
| Commits frecuentes (por tarea en tasks.md) | Patrón 3 |
| PROGRESS.json actualizado en cada paso | Patrón 1 |
| `/compact` antes de waves largas | Patrón 5 |
| `auto-progress-log.sh` hook | Perder rastro de qué tocó el agente |
| `.ai/mistakes.md` actualizado | Repetir el mismo error |
| RAM check antes de tests | OOM que mata la sesión |

---

## Comandos de diagnóstico rápido

```bash
# Estado completo en <10 segundos
git status && git log --oneline -5 && cat PROGRESS.json | jq '{task,status}' && tail -5 .claude/PROGRESS.log

# Ver todos los worktrees y su estado
git worktree list && ls worktrees/ 2>/dev/null

# Ver RAM disponible
free -h | awk '/Mem:/ {print "RAM libre:", $7}'

# Ver qué Tech Leads están corriendo
ps aux | grep claude | grep -v grep | wc -l
```

---

_Rule version: 1.1 · 2026-10-21 · +§Cuando lo roto es la configuración (`--safe-mode`, CL-22, sub-ola 2.01) · v1.0 - 2026-04-12_
