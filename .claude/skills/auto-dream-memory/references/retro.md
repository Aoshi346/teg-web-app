# retro — Retrospectiva semanal

> **§C de la skill `auto-dream-memory`.** Era la skill `retro`, fusionada aquí el 2026-10-19 (LI-9,
> `_archive/2026-10-19/README.md` §Sub-ola 1.04). Se entra por `auto-dream-memory`: `/retro` ya no
> es un comando propio.

Adaptación del skill `retro` de gstack al template tech-lead. Sin infra de
gstack (`~/.gstack/projects/`, telemetry) — sólo el patrón de análisis.

## Cuándo usar

- Cada viernes al cerrar la semana (preferentemente automatizado por cron).
- Al cerrar un sprint o wave grande.
- Cuando el agente lleva >50 commits sin reflexión consolidada.

## Output

Markdown estructurado en (path configurable, recomendados):
- Local agente: `.claude/memory/retros/YYYY-WW.md`
- Largo plazo: la línea de una frase sube a `MEMORY.md` de la raíz (capa 3 de `rules/memory.md`);
  el informe entero se queda en local.

## Estructura del informe

```markdown
# Retrospectiva semana YYYY-WW (<fecha inicio> – <fecha fin>)

## Headline (1 frase)
<lo más importante de la semana en una frase honesta>

## Métricas

| Métrica | Valor | vs semana anterior |
|---|---|---|
| Commits | N | ±N |
| PRs mergeados | N | ±N |
| Tareas completadas | N | ±N |
| Bloqueos >15min | N | ±N |
| Tests añadidos | N | ±N |

## Qué fue bien

- <evento concreto 1>
- <evento concreto 2>

## Qué no fue bien

- <fricción real, con commit/path como evidencia>
- <decisión que en retrospectiva fue mala>

## Aprendizajes (append a memory)

- <aprendizaje 1: situación → decisión → resultado → aplica si...>
- <aprendizaje 2>

## Decisiones tomadas

- <ADR ligero: contexto → decisión → consecuencia>

## Para la próxima semana

- <acción concreta 1>
- <experimento a probar>

## Bloqueos pendientes

- <qué necesito de fuera>
```

## Cómo se genera

```bash
# 1. Recopilar commits de la semana
WEEK_START=$(date -d "monday last week" +%Y-%m-%d)
WEEK_END=$(date +%Y-%m-%d)
git log --since="$WEEK_START" --until="$WEEK_END" --oneline > /tmp/retro-commits.txt

# 2. Tareas completadas (si usas TaskCreate runtime)
# Listar tasks completadas en el rango (depende del backend de tasks).

# 3. Bloqueos: leer .claude/PROGRESS.log buscando "BLOQUEADO"
grep "BLOQUEADO\|BLOCKED" .claude/PROGRESS.log | tail -20

# 4. Aprendizajes nuevos: lo que cambió esta semana donde de verdad se escriben (rules/memory.md).
#    Antes leía .claude/memory/learnings.md, que no escribe nadie, con el stderr a /dev/null:
#    siempre «sin aprendizajes» (MO-42, 2026-10-21).
git log --since="$WEEK_START" -p -- .ai/memory.md MEMORY.md .claude/improvements_tl.md

# 5. Generar el .md final con la estructura de arriba.
```

## Voz del retro

- **Honesto**, no marketing speech. Si la semana fue mala, decirlo. "Esta semana fallé el OOM check 2 veces" beats "se identificaron oportunidades".
- **Concreto**, con paths/commits/números. "Refactor module X tardó 3 días" vs "tomó tiempo".
- **Sin emojis decorativos** ni "delivered great value".
- **Apunta a acción**, no a auto-felicitación. "Repetir patrón Y" > "Equipo motivado".

## Anti-patterns

- ❌ Retro sin métricas: opinión sin hechos.
- ❌ Lista de tareas hechas sin reflexión sobre **calidad**.
- ❌ "Todo bien" — siempre hay una fricción real, encontrarla.
- ❌ Aprendizajes vacíos del tipo "comunicarse mejor". Ser específico.
- ❌ Sobre-reaccionar a una semana mala con cambios estructurales — ver tendencia (3+ semanas).

## Salida HTML (opcional)

Si se pide la retro "visual" o para compartir con el equipo, emítela como artefacto HTML Tier-1
(métricas + chart + timeline) con la skill `html-suelto` además del `.md`. Ver
`.claude/rules/html-output.md`. El `.md` sigue siendo la fuente para memoria/append.

## Automatización (opcional)

Para que la retro salga sola cada viernes, la capa que toca es el **cron del harness** (skill
`/schedule`), no un orquestador externo.

> ⚠️ Aquí había un programador externo que no está instalado en este servidor; la carpeta que
> documentaba sus comandos se archivó el 2026-08-22 (el porqué, en `_archive/2026-08-22/README.md`).
> Para avisar de que la retro está lista: `python3 .claude/scripts/avisar.py "DONE …"` (Telegram).

## Versión

`v1.0` — refactor 03-05-2026 W1, adaptado de la skill `retro` de gstack (lightweight; gstack no se versiona en el template: `resources/gstack.LEEME.md`).
