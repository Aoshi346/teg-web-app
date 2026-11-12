---
name: pattern-gate
description: >-
  Usar al cerrar una wave o un PR para el juicio de consistencia de patrón: corre pattern-check.sh y
  lanza a Rita (rita-pattern-keeper) sobre los candidatos: 'pattern gate', '¿esto sigue el patrón?',
  '/pattern-gate'. NO usar para: arreglar reuso (/simplify) ni bugs y seguridad (/review-branch,
  donde entra como dimensión 'patterns').
user-invocable: true
metadata:
  version: 1.0.0
  author: tech-lead-template
  category: qa
  updated: 2026-08-07
---

# pattern-gate — Tier 0 + Rita sobre el diff

## Cuándo se activa (detalle)

Disparadores: 'pattern gate', 'gate de patrones', 'revisa el patrón antes del merge', '¿esto sigue
el patrón?', '/pattern-gate'. Corre pattern-check.sh sobre lo cambiado y lanza a Rita
(rita-pattern-keeper) a juzgar SOLO los candidatos que salgan. · NO confundir con /simplify (arregla
reuso; Rita lo detecta) ni /review-branch (bugs/seguridad; este gate entra ahí como dimensión
'patterns'). Rita está en MODO SOMBRA: reporta, no comenta en el PR.

## Principio
La capa barata detecta; Rita juzga; nadie más que el hook determinista bloquea. Es el reparto que
la evidencia sostiene (F1 6% del LLM buscando vs 94-98% FP eliminados como validador — RESEARCH.md
del plan de Rita).

## Procedimiento
1. **Tier 0**: `.claude/hooks/pattern-check.sh` (modo changed). Exit 1 = violaciones ACTIVAS → se
   arreglan ANTES de seguir (eso no es de Rita, es mecánico).
2. **Candidatos a juicio**: los avisos DÉBILES + los ejes no-deterministas del diff (léxico,
   contratos, reuso). Pásaselos a `rita-pattern-keeper` como lote (≤5) con el diff.
3. Rita emite hallazgos (🔎/📐/📊/🔧, ≥2 precedentes + diff o silencio) → en SOMBRA van a
   `.docs/feedback/rita/<fecha>/REPORT.md`, no al PR.
4. Registrar desenlaces en `.claude/patterns/telemetry.jsonl` cuando se conozcan.
5. Si Rita detectó 3 veces el mismo tipo → ella propone la regla determinista nueva (catálogo) y
   se autoexcluye de ese patrón.

## Anti-patterns
- ❌ Lanzar a Rita sin correr el Tier 0 antes (le estás pidiendo que busque — su peor modo).
- ❌ Dejar que Rita bloquee el cierre — no es reproducible; bloquea solo pattern-check.sh.
- ❌ Comentar deuda del baseline en un PR que no la toca.
- ❌ Saltarse la telemetría: sin desenlaces no hay retirada automática y el ruido crece.

## Related
`.claude/patterns/` · `hooks/pattern-check.sh` · `agents/rita-pattern-keeper.md` · `rules/verdict-contract.md`
· `agents/roberto-clean-code.md` — aplica el criterio de Rita como «lente patrones» en su informe, sin cambiarlo
