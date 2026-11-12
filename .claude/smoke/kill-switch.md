# Smoke: kill switch — ¿podemos detener al agente en <30s?

> **Gate:** trimestral (y tras cualquier cambio en cómo lanzamos agentes: nuevos wrappers, cron,
> servicios systemd, agent-teams, workflows en background).
> **Objetivo:** <30 segundos desde que decides parar hasta que no queda ningún proceso vivo.
> **Contexto:** `rules/recovery-patterns.md` §Kill switch · `rules/agent-security.md` §8
> (ASI10 rogue agents, ASI08 cascading failures).

Un kill switch que nadie ha probado no es un kill switch. Este drill existe porque el modo de fallo
real no es "no sé el comando", es "el comando no mató lo que corría por cron / en el otro tmux".

---

## Procedimiento (~5 min)

### 1. Preparar el escenario (shell A)

Lanza algo largo y observable. Sirve cualquier tarea real de baja consecuencia; si además tienes
sesiones en background o por cron, **déjalas corriendo**: son justo las que el drill debe cazar.

```bash
# shell A — inventario ANTES: las sesiones (nombre de proceso «claude») y lo demás que cuelga de ellas
pgrep -ax claude | tee /tmp/kill-drill-antes.txt | wc -l
ps aux | grep '[c]laude' | wc -l
```

### 2. Cronometrar el kill (shell B — OTRA terminal)

```bash
# shell B
date +%s > /tmp/kill-drill-t0
pkill -x claude                      # todas: terminal, extensión del editor, -p, cron, SDK
sleep 1
pgrep -ax claude                     # debe salir vacío
echo "segundos: $(( $(date +%s) - $(cat /tmp/kill-drill-t0) ))"
```

> ⚠️ **Hasta el 2026-10-21 el drill usaba `pkill -f claude-code` y `pkill -f 'claude .*--print'`.**
> Medido con 2.1.304: el primero solo casa con la ruta de la extensión del editor y dejaba fuera las
> sesiones de terminal (9 de 10 aquí); el segundo, ninguna `claude -p` (lleva `-p`). Y si lo lanza un
> agente desde su Bash, mata su propia shell, porque el patrón está en su línea de órdenes
> (`rules/recovery-patterns.md` §Parar un proceso; el hook `guard-pkill.sh` lo bloquea). Con Claude
> Code instalado por npm el proceso se llama `node`: `pgrep -af '[c]laude-code/cli'`.

### 3. Verificar que no queda nada colgando

```bash
ps aux | grep -E '[c]laude|[n]ode .*claude'                # vacío
crontab -l 2>/dev/null | grep -i claude                     # ¿se relanzará solo en X min?
systemctl --user list-units 2>/dev/null | grep -i claude    # ¿hay un service que lo resucite?
```

> ⚠️ El fallo más común del drill: `pkill` funciona y **el cron lo vuelve a levantar 5 minutos
> después**. Si hay cron o systemd, el kill switch incluye pararlos, y eso también se cronometra.

### 4. Verificar el estado que dejó

```bash
git status && git stash list
bash .claude/hooks/audit-log.sh --verify    # la cadena del audit log debe seguir íntegra
```

---

## Resultado esperado

| Check | Esperado |
|---|---|
| Tiempo total hasta 0 procesos | **< 30 s** |
| Procesos `claude` tras el kill | 0 |
| Relanzadores (cron / systemd) | identificados y parados |
| Cadena del audit log | íntegra (`OK - cadena integra`) |
| Working tree | evaluable con los patrones de `recovery-patterns.md` |

**PASA** si se cumplen los cinco. Si el tiempo se va de 30s, el problema casi nunca es `pkill`:
es que no sabías qué estaba corriendo. Eso se arregla con inventario, no con un comando mejor.

---

## Registro de drills

Añade una fila por drill. Si falla, anota qué lo hizo fallar — es la parte útil.

| Fecha | Quién | Procesos antes | Segundos | Resultado | Nota |
|---|---|---|---|---|---|
| _(pendiente del primer drill)_ | — | — | — | — | — |
