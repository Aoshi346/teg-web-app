---
paths:
  - ".docs/adr/**"
  - ".claude/templates/adr-template.md"
---
# ADR — Architecture Decision Records

> **Cuándo aplicar:** cuando una tarea grande **cambia la arquitectura**: elección de tecnología
> estructural (BD, cola, framework, proveedor cloud), cambio de **schema** con impacto, cambio de
> **contrato de API**, límites de módulo/servicio, monolito↔servicios, o cualquier decisión que sea
> **cara de revertir**. El gate está en `plan-gates.md` (Gate D).
>
> **NO aplicar:** features dentro de una arquitectura ya decidida, bugfixes, refactors internos que
> no cambian contratos, elección de una librería auxiliar sustituible en una tarde. Si dudas: ¿en un
> año alguien preguntará "¿por qué se hizo así?" → ADR. ¿Nadie lo preguntará → no.
>
> **Relacionado:** `plan-gates.md` (el gate que lo dispara), `templates/adr-template.md` (la
> plantilla), `plan-docs-structure.md` (dónde vive), `memory.md` (dónde acaba viviendo la decisión)
> y la skill `auto-dream-memory` (quien la sube allí)
> (los ADRs se consolidan en `MEMORY.md`).

---

## Qué es

Un ADR es **un documento corto de una página** que captura una decisión de arquitectura junto con su
**contexto** y sus **consecuencias**. Tres partes, y las tres son obligatorias:

| Parte | Responde a | Por qué importa |
|---|---|---|
| **Contexto** | ¿Qué problema había? ¿Qué restricciones aplicaban entonces? | Sin él, la decisión parece arbitraria un año después |
| **Decisión** | ¿Qué se eligió, y qué se **descartó** y por qué | git dice QUÉ cambió; nunca por qué se descartó lo otro |
| **Consecuencias** | ¿Qué ganamos y qué aceptamos perder? | Convierte la decisión en algo **evaluable** después |

## Las 5 razones para registrarlos

1. **Claridad en la toma de decisiones** — obliga a formular las alternativas en voz alta.
2. **Comunicación** — el resto del equipo entiende el porqué sin reunión.
3. **Transferencia de conocimiento** — quien entra en seis meses no arqueologiza.
4. **Consistencia y reusabilidad** — las decisiones siguientes se apoyan en las anteriores.
5. **Fundamento para revisiones y cambios** — *"entender las decisiones originales permite evaluar
   si esas decisiones siguen siendo válidas"*.

La 5 es la que paga el coste: sin ADR, cuando alguien propone cambiar X dentro de un año, la
discusión empieza de cero o se cambia sin saber qué se rompe.

---

## Cuándo se emite (el gate)

`plan-gates.md` → **Gate D**: una tarea **grande** que toca arquitectura, schema o contrato de API
**no cierra el plan sin su ADR**. El ADR se escribe con la decisión **fresca**, durante el plan o
justo al tomarla — nunca en arqueología posterior, que es cuando ya nadie recuerda las alternativas.

**El riesgo real es la ceremonia.** Si se pide ADR para todo, no se escribe ninguno. Por eso el
disparador está acotado a arquitectura/schema/contrato, no a "toda tarea grande".

## Dónde vive y cómo se nombra

```
.docs/adr/
├── README.md                      # índice: id · título · estado · fecha
├── 0001-postgres-sobre-mongo.md
├── 0002-celery-para-tareas-largas.md
└── 0003-api-versionada-por-url.md   ← supersedes 0001 si aplica
```

- **Numeración secuencial de 4 dígitos**, nunca se reutiliza ni se renumera.
- Un ADR **no se borra ni se reescribe**: si la decisión cambia, se crea uno nuevo con estado
  `Aceptado` que marca al viejo como `Reemplazado por ADR-XXXX`.
- Si la decisión nace dentro de un plan, deja el ADR en `.docs/adr/` y **enlázalo** desde el
  `index.html` del plan (`plan-docs-structure.md`) — el plan caduca, el ADR no.
- Al consolidar memoria (`auto-dream-memory`), la línea de una frase del ADR sube a `MEMORY.md`; el
  documento completo se queda en `.docs/adr/`.

## Estados

`Propuesto` → `Aceptado` → (`Reemplazado por ADR-XXXX` | `Obsoleto`). Un ADR `Rechazado` también se
guarda: saber qué se consideró y se descartó vale tanto como saber qué se eligió.

## Cómo se escribe (con el agente)

```bash
cp .claude/templates/adr-template.md .docs/adr/0004-<slug>.md
```

Reglas de redacción:
- **Una página.** Si no cabe, la decisión son dos decisiones: pártela.
- **Mínimo 2 alternativas descartadas**, cada una con la razón concreta de descarte. Un ADR con una
  sola opción no es una decisión, es un anuncio.
- **Consecuencias negativas obligatorias.** Toda decisión de arquitectura tiene un coste; si no lo
  encuentras, no has terminado de pensarla.
- Fechado y con autor. El contexto de 2026 no es el de 2028.
- Hay plantillas de dominio público por tipo de decisión (cloud provider, BD, monorepo vs multirepo,
  microservicios vs monolito) en `adr.github.io` — **adáptalas, no las reinventes**.

---

## Anti-patterns

- ❌ Tomar la decisión en la conversación y no dejar rastro → seis meses después se rediscute desde cero.
- ❌ Pedir ADR para cualquier tarea grande → ceremonia, y entonces no se escribe ninguno.
- ❌ ADR sin alternativas descartadas (no es una decisión, es un comunicado).
- ❌ ADR sin consecuencias negativas (nadie se lo cree).
- ❌ Editar un ADR viejo para "actualizarlo" → se pierde la historia; crea uno nuevo que lo reemplace.
- ❌ Escribirlo semanas después "para documentar" → el contexto y las alternativas ya se olvidaron.
- ❌ Confundirlo con la doc de arquitectura: el ADR registra **una decisión**, no describe el sistema
  (eso es `/visual-map` y `/schema`).

---

_Rule version: 1.0 · SPEC-4, aprobado 2026-08-07_
