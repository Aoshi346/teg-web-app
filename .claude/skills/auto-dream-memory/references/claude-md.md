# /weekly-review — Revisión semanal → actualizar CLAUDE.md

> **§D de la skill `auto-dream-memory`.** Era la skill `weekly-review`, fusionada aquí el 2026-10-19
> (LI-9, `_archive/2026-10-19/README.md` §Sub-ola 1.04). Se entra por `auto-dream-memory`:
> `/weekly-review` ya no es un comando propio.

Revisa toda la memoria acumulada durante la semana y propone qué añadir, actualizar o eliminar de `CLAUDE.md` para mantenerlo útil y sin ruido.

## Qué hace

1. Lee todas las fuentes de memoria del proyecto
2. Identifica qué información es estable y duradera (candidata a CLAUDE.md)
3. Propone cambios concretos con diff claro
4. Aplica los cambios tras confirmación del usuario

## Cuándo NO usar esta skill

| Lo que quieres | La pieza que toca |
|---|---|
| Un **informe** de la semana (qué se hizo, bloqueos, aprendizajes) | §C de `auto-dream-memory` (`references/retro.md`, antes `retro`) — mismas fuentes, otro entregable |
| Ponerte al día al **retomar** trabajo, sin tocar `CLAUDE.md` | §A de `auto-dream-memory` |
| Consolidar **ADRs y decisiones** en el `MEMORY.md` de largo plazo | §B de `auto-dream-memory` |
| Entender **cómo está montada** la memoria (las capas) | `rules/memory.md` |
| Decidir qué **sobra del harness** (skills, rules, agentes que no disparan) | `rules/self-improvement-loop.md` §5 (criterio 30/60) |

## Pasos de ejecución

### 1. Recopilar toda la memoria

Carpeta de auto memory del proyecto: `/root/.claude/projects/<slug>/memory/` (donde `<slug>` = path del proyecto con `/` reemplazado por `-`).

```bash
PROJECT_SLUG=$(echo "$CLAUDE_PROJECT_DIR" | sed 's|/|-|g')
AUTO_MEM_DIR="/root/.claude/projects/${PROJECT_SLUG}/memory"

# Auto memory de Claude Code
cat "${AUTO_MEM_DIR}/MEMORY.md"
ls "${AUTO_MEM_DIR}"/*.md | grep -v MEMORY.md | xargs cat

# Context local del proyecto
cat "$CLAUDE_PROJECT_DIR/.ai/memory.md" 2>/dev/null
cat "$CLAUDE_PROJECT_DIR/MEMORY.md" 2>/dev/null

# CLAUDE.md actual (para ver qué ya está documentado)
cat "$CLAUDE_PROJECT_DIR/.claude/CLAUDE.md"
```

### 2. Revisar actividad de la semana

```bash
cd "$CLAUDE_PROJECT_DIR"
git log --oneline --since="7 days ago"
git diff --stat HEAD~20 HEAD 2>/dev/null | tail -20
```

### 3. Analizar qué merece ir en CLAUDE.md

Criterios para incluir en CLAUDE.md:
- **Reglas técnicas recurrentes** — patrones que aparecen en múltiples sesiones
- **Gotchas confirmados** — problemas que se repiten y tienen workaround probado
- **Decisiones arquitectónicas firmes** — no especulativas, ya implementadas
- **Comandos críticos** — que Claude debe conocer para no romper cosas

Criterios para NO incluir:
- Contexto efímero de una sola sesión (va en `.ai/memory.md`)
- Decisiones pendientes o en evaluación (van en MEMORY.md)
- Código o implementaciones concretas (están en el repo)
- Información ya obsoleta

### 4. Proponer cambios

Presenta los cambios propuestos en formato diff claro:

```
AÑADIR a sección "Gotchas conocidos":
  > - El modelo X tiene una relación circular con Y — siempre usar select_related('y__z')

ACTUALIZAR en sección "Comandos":
  Antes: pytest backend/apps/ -v
  Después: pytest backend/apps/MODULE/ -v (nunca el directorio completo)

ELIMINAR de sección "Estado actual":
  > - Wave 3 de FEAT-AI-1 en progreso (ya completada)
```

### 5. Confirmar y aplicar

Pregunta al usuario: "¿Aplico estos cambios a CLAUDE.md?"

Si confirma, edita `$CLAUDE_PROJECT_DIR/.claude/CLAUDE.md` con los cambios acordados.

> ⚠️ **Editar `CLAUDE.md` a mitad de sesión no se aplica** hasta `/clear`, `/compact` o reiniciar (no
> rompe el caché: doc `prompt-caching`, 2026-10-20): `rules/harness-gotchas.md` manda tocarlo **al
> inicio de sesión**, no a mitad. Si esta revisión cae en medio de una sesión larga,
> deja el diff escrito y aplícalo al arrancar la siguiente — es exactamente el caso que esa rule
> describe. Y recuerda que `CLAUDE.md` es **advisory**: si lo que ibas a añadir duele cuando se
> ignora, no es una línea de `CLAUDE.md`, es un hook (`rules/layer-decision.md`).

### 6. Limpiar memoria efímera

Tras actualizar CLAUDE.md, opcionalmente:
- Resetear `.ai/memory.md` si el contexto ya está obsoleto
- Podar `MEMORY.md` si supera 150 líneas (eliminar ADRs de features ya eliminadas)

## Frecuencia recomendada

- **Semanal** — cada lunes antes de empezar la semana
- **Post SpecKit session** — al completar una sesión entera
- **Cuando CLAUDE.md >200 líneas** — señal de que necesita poda

## Notas

- Siempre mostrar el diff propuesto ANTES de aplicar — nunca editar CLAUDE.md sin confirmación
- Si no hay nada relevante que añadir, decirlo explícitamente (no forzar cambios)
- CLAUDE.md es el contrato del proyecto — cada línea debe ganarse su lugar

## Related

- `auto-dream-memory` (`SKILL.md`) — §A traer al retomar · §B consolidación reflexiva después de N sesiones
- `rules/memory.md` — la arquitectura de memoria del proyecto (único sitio)
- §C `references/retro.md` (antes `retro`) — el informe de la semana (mismas fuentes, otro entregable)
- `rules/self-improvement-loop.md` §5 — el criterio de poda del harness (30/60) y por qué el bucle también resta
- `rules/harness-gotchas.md` — el caché de `CLAUDE.md` y por qué es advisory
- `rules/layer-decision.md` — si la norma duele cuando se ignora, va a hook, no a `CLAUDE.md`
