---
name: incident-review
description: >-
  Usar DESPUÉS de un incidente con personas o datos reales para el postmortem sin culpa:
  'postmortem', 'revisión del incidente', 'qué pasó ayer en producción', 'se expuso una clave'.
  Timeline, causas, detección, acciones con dueño y caso de eval. NO usar para: un working tree
  roto (recovery-patterns.md), la retro (/retro), auditar seguridad (sofia-pentester) ni un bug.
user-invocable: true
metadata:
  version: 1.0.0
  author: tech-lead-template
  category: workflow
  updated: 2026-10-31
  origin: cold_calling_coach/.claude/skills/incident-review (AN-24, sub-ola 3.20)
---

# Revisión de incidente — sin culpa, con dueño, y que no vuelva a pasar callado

> **Cuándo es un incidente y no un bug:** cuando afectó a una persona real, a datos reales o a la
> confianza en el sistema. Un test en rojo no es un incidente. Un informe que alguien leyó con un
> dato de otro cliente dentro, sí.

## Lo que se escribe

`.docs/incidents/<AAAA-MM-DD>-<slug>/POSTMORTEM.md`, el mismo día o el siguiente (después el
timeline ya no se reconstruye):

```markdown
# Incidente — <qué pasó en una línea, no quién>

| | |
|---|---|
| **Detectado** | <fecha y hora> · **por**: <alerta / usuario / casualidad> |
| **Resuelto** | <fecha y hora> |
| **Impacto** | <a quién afectó, haciendo qué, con qué resultado: concreto> |
| **Severidad** | <y por qué esa> |

## Timeline
<hora> — <hecho observable, no interpretación>

## Causas contribuyentes
<varias. Si solo hay una, no se ha terminado de mirar>

## Cómo se detectó, y por qué no antes
<qué alerta, test o runbook debería haber saltado, y por qué no saltó>

## Acciones
| Qué | Dueño | Fecha | Cómo se verifica |
|---|---|---|---|

## Lo que NO vamos a hacer
<y por qué: evita que se reabra en tres meses>
```

## Las reglas

1. **Sin culpa.** Se escribe qué falló en el sistema, no quién se equivocó. Que una persona pueda
   tirar el sistema con un clic es un problema de diseño.
2. **Causas en plural.** Buscar «la» causa cierra la investigación antes de tiempo.
3. **La pregunta que más enseña es la de detección**: no «por qué pasó», sino «por qué no nos
   enteramos antes». Si nos enteramos por un usuario, esa es la acción número uno.
4. **Toda acción lleva dueño, fecha y cómo se verifica.** Una acción sin verificación es un deseo.
   Si la acción es «un sensor que lo cace», va con su sabotaje: `scripts/sabotage.py` demuestra que
   el test nuevo se pone en rojo con el fallo plantado (`rules/self-improvement-loop.md`).
5. **El incidente se convierte en caso de eval.** Si lo causó un diff o se arregló con un revert:
   `python3 .claude/scripts/incident_cases.py add --sha <commit> --marca <fichero>:<línea>`, y el
   auditor de código tiene que cazarlo la próxima vez (`rules/audit-team.md` §7).
6. **Si tocó datos personales**, el postmortem no decide si se notifica: eso es de una persona
   (`priya-privacy-auditor`, `sara-salud-datos` si son de salud). Contención primero, evidencia
   después.

## Antes de que pase: qué se preserva primero

Cada proyecto escribe su tabla en su `CLAUDE.md` o en una rule propia; esta es la forma, con los
casos que se repiten en casa:

| Incidente | Qué se preserva primero |
|---|---|
| Un proveedor externo se degrada | Métricas de latencia y el estado del feature flag |
| Cola bloqueada o DLQ creciendo | El contenido de la DLQ, antes de reintentar nada |
| Posible fuga entre tenants o exposición de datos | Contención; luego el rastro completo (logs, consultas, quién vio qué) |
| Clave de proveedor expuesta | Rotar antes de investigar |
| El bot prometió algo que no podía (precio, plazo) | La conversación entera y la versión del prompt y del catálogo |

## Anti-patterns

- ❌ Un postmortem con una sola causa y un nombre propio dentro.
- ❌ Acciones sin dueño ni fecha: no se hacen.
- ❌ Saltarse la pregunta de detección porque la causa ya está clara.
- ❌ Reintentar la cola antes de guardar lo que había en la DLQ.
- ❌ Un sensor nuevo que nadie ha visto fallar: `sabotage.py` antes de darlo por puesto.
- ❌ Decidir por tu cuenta si un incidente con datos personales se notifica.
