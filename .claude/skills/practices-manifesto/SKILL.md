---
name: "practices-manifesto"
description: >-
  Usar para EVALUAR el diseño de un repo contra sus propios estándares: manifiesto de buenas
  prácticas sacado del código (Antes/Después reales) y puntuación por principio. 'evalúa la calidad
  del código', 'informe de deuda de diseño', '/practices-manifesto'. NO usar para: consistencia PR a
  PR (rita-pattern-keeper), el gate de un diff (code-review-gate) ni el CLAUDE.md
  (codebase-onboarding).
user-invocable: true
metadata:
  version: 1.0.0
  author: Tech Lead Template
  category: qa
  updated: 2026-08-08
---

# practices-manifesto — la rúbrica sale del código, y el código se puntúa contra ella

## Principio

Evaluar un repo contra un manifiesto genérico de SOLID/DDD no sirve: la salida es un ensayo de
libro de texto que no toca este proyecto. La técnica que sí funciona tiene dos movimientos:

1. **Generar la rúbrica desde el propio código** — cada principio ilustrado con un **Antes/Después
   real extraído del repo**, no con el ejemplo canónico de la Wikipedia.
2. **Puntuar el proyecto contra esa rúbrica**, con salida estructurada
   **Observación / Recomendación / Mejora propuesta** por principio.

El manifiesto tiene sentido porque es **la vara de medir**, no porque sea documentación.

## ⚠️ El manifiesto NO es contexto del día a día

**Regla dura, y es la razón por la que esta skill existe con este alcance.** Para que un agente
escriba código como se escribe aquí, **no le pases el manifiesto**: pásale **los dos o tres ficheros
precedentes** (los controllers, los serializers, el componente equivalente que ya existe). Es más
barato en contexto, más concreto y no se queda obsoleto.

> *"Contexto excesivo, [la] carpeta backend es mucho. **Pasarle los controllers que ya existen para
> que siga los mismos patrones.** Crear el manifiesto es mucho trabajo, no es necesario."*

Esa crítica —hecha por un instructor externo a una solución que proponía el manifiesto como
contexto— es **validación independiente de la tesis de Rita**: precedentes concretos > documento
normativo. Así que el reparto queda así y no se mezcla:

| Necesito… | Herramienta | Por qué |
|---|---|---|
| Que el código nuevo salga con el patrón del repo | **pasar los ficheros precedentes** (2-3) | concreto, barato, siempre al día |
| Vigilar consistencia de patrón PR a PR | **`.claude/patterns/` + `pattern-gate`/Rita** | dominancia medida, ≥2 precedentes, determinista primero |
| Bloquear problemas antes de mergear un diff | **`code-review-gate`** | gate, no informe |
| **Medir en qué estado de diseño está el proyecto y qué mejorar primero** | **esta skill** | rúbrica + puntuación, una vez cada varios meses |

## Cuándo activar

- Arranque de proyecto o **auditoría periódica** (trimestral, fin de un hito grande).
- Llega un repo heredado y hay que decidir **por dónde empezar** el saneamiento.
- Se quiere un informe de **deuda de diseño** priorizada para el Usuario o para Pol.
- Onboarding de alguien (humano o agente) que pregunta *"¿cuáles son los estándares aquí?"*.

**NO la actives**: antes de cada PR (es caro y no es un gate), ni para justificar un refactor ya
decidido, ni en un repo de <10 ficheros (léelos y ya).

Disparadores: 'evalúa la calidad del código', 'manifiesto de buenas prácticas', 'auditoría de diseño', '¿seguimos SOLID/DDD aquí?', 'informe de deuda de diseño', 'onboarding: cuáles son nuestros estándares', '/practices-manifesto' · Salida: Observación / Recomendación / Mejora propuesta por principio · NO confundir con rita-pattern-keeper (juzga consistencia de patrón PR a PR con dominancia medida), con code-review-gate (gate pre-merge de un diff) ni con codebase-onboarding (genera CLAUDE.md).

## Procedimiento

### Fase 0 — Acotar el ámbito (obligatorio)

Un manifiesto de "todo el repo" es ruido. Elige **una capa coherente**: `backend/apps/`, el paquete
de dominio, `frontend/src/components/`. Si el proyecto es Django+React, son **dos manifiestos**, no
uno: los principios no son los mismos.

```bash
# Tamaño del ámbito — si pasa de ~150 ficheros, acota más
find backend/apps -name "*.py" -not -path "*/migrations/*" | wc -l
```

### Fase 1 — Generar el manifiesto desde el código real

Da una **plantilla con los huecos vacíos** y pide que los rellene con ejemplos extraídos del repo.
La plantilla es lo que impide que la salida sea un ensayo genérico.

Principios sugeridos (ajusta al stack; 6-10 como máximo, o nadie lo lee):

- **Modelo de dominio**: entidades vs value objects vs agregados; dónde vive la regla de negocio.
- **SRP** — una razón para cambiar por clase/módulo.
- **Inversión de dependencias** — el dominio no importa el ORM/el cliente HTTP concreto.
- **DRY con criterio** — qué se extrae y qué se deja duplicado a propósito.
- **Manejo de errores** — excepciones de dominio vs errores de transporte.
- **Fronteras de capa** — qué puede importar qué (vista → servicio → repositorio).
- **Nombrado** — el vocabulario del negocio en el código.
- **Tests** — qué se considera unitario aquí y qué se mockea.

Prompt de generación (rellena `<ÁMBITO>`):

```
Te doy una plantilla con secciones vacías. Rellena cada hueco con ejemplos REALES extraídos de
<ÁMBITO>, citando `file:line`. Para cada principio:
  - Enunciado en una frase, en el vocabulario de este proyecto.
  - ✅ Ejemplo BUENO del repo (código literal + file:line) y por qué lo es.
  - ❌ Ejemplo del repo que NO lo cumple (código literal + file:line) y el Después propuesto.
  - Cómo se detecta una violación (grep, regla de lint o "requiere criterio humano").
Reglas: no inventes código; si un principio NO tiene ejemplo en el repo, escribe
"sin precedentes en <ÁMBITO>" y NO lo ilustres con un ejemplo de libro. Máximo 2 ejemplos por
principio.
```

Salida → `.docs/manifiesto-practicas-<ámbito>.md`. Con `<!-- generado: YYYY-MM-DD · commit <sha> -->`
en la cabecera: un manifiesto sin fecha ni commit es un manifiesto en el que no se puede confiar.

**Gate de calidad de la fase 1** — si no lo pasa, el manifiesto no sirve como rúbrica:

```
[ ] Cada principio tiene al menos un ejemplo con file:line que existe de verdad
[ ] Los ejemplos ❌ son de este repo, no inventados
[ ] Los principios sin precedentes están marcados como tal (y no se puntuarán en la fase 2)
[ ] Ningún ejemplo es genérico de internet
```

```bash
# Verificación barata: que los file:line citados existan
grep -oE '[A-Za-z0-9_./-]+\.(py|ts|tsx|js):[0-9]+' .docs/manifiesto-practicas-*.md \
  | sort -u | while IFS=: read -r f l; do
      [ -f "$f" ] && [ "$(wc -l < "$f")" -ge "$l" ] || echo "REFERENCIA ROTA: $f:$l"
    done
```

### Fase 2 — Evaluar el proyecto contra el manifiesto

```
Basándote en el manifiesto @.docs/manifiesto-practicas-<ámbito>.md, evalúa <ÁMBITO>.
Para CADA principio del manifiesto devuelve exactamente:
  - Observación: qué hace hoy el código, con file:line. Solo lo que has leído: nada de oídas.
  - Recomendación: qué debería cambiar y por qué (consecuencia concreta, no "es mala práctica").
  - Mejora propuesta: el diff o el fragmento Después, aplicable.
  - Cumplimiento: alto | medio | bajo  +  Esfuerzo: S | M | L
Si un principio se cumple, dilo y no propongas nada. Antes de marcar algo como incumplimiento,
busca si es deliberado (`// defensive:`, `// workaround: #N`, `// historical:`, git log -L).
```

Ese último párrafo es el **Intent** de `rules/verdict-contract.md`: sin él, la evaluación produce
falsos positivos sobre código que alguien escribió así a propósito, y el informe pierde credibilidad
entero por dos hallazgos malos.

Salida → `.docs/practices-eval/<YYYY-MM-DD>-<ámbito>.md`. Si la evaluación se hace dentro de un plan,
va en la carpeta del plan; si sale con muchos items y hay que **decidir** sobre ellos (aprobar /
aplazar / descartar), vuélcala al **report-kit** (`rules/report-kit.md`) en vez de a un markdown de
400 líneas.

### Fase 3 — Convertir hallazgos en trabajo (si no, no ha servido de nada)

1. Los hallazgos **alto impacto / esfuerzo S** → items de `tasks.md`, ya.
2. Los que son **regla repetible y medible** (no una opinión) → candidatos a fila de
   `.claude/patterns/catalog.yaml`, con su dominancia medida. Ahí los recoge Rita y dejan de
   depender de que alguien vuelva a lanzar esta skill.
3. El resto → backlog, con la fecha de la evaluación para poder medir la evolución.

**Multi-ronda**: al repetir la evaluación (meses después) conserva la anterior y compara principio a
principio. La tendencia (¿sube el cumplimiento?) vale más que la foto.

## Anti-patterns

- ❌ **Pasar el manifiesto como contexto de generación en el día a día** — el error que esta skill
  existe para evitar. Pasa los ficheros precedentes.
- ❌ Manifiesto con ejemplos de libro en vez de código del repo → rúbrica que no mide este proyecto.
- ❌ Puntuar un principio que el manifiesto marcó como "sin precedentes".
- ❌ Evaluar sin buscar el Intent → falsos positivos sobre código deliberado.
- ❌ Un manifiesto por repo entero mezclando backend y frontend.
- ❌ Regenerarlo en cada sesión: es caro y no cambia en dos semanas. Fecha + commit en la cabecera.
- ❌ Terminar en el informe: sin la fase 3 es un documento que nadie vuelve a abrir.
- ❌ Duplicar en el manifiesto reglas que ya están en `.claude/patterns/` con mecanismo determinista
  (ahí ya se comprueban solas y gratis).

## Ejemplos

### User: "acabamos de heredar este backend, ¿está bien hecho? ¿por dónde empezamos?"
TL: acota a `backend/apps/` (fase 0) → genera el manifiesto con Antes/Después reales y verifica que
los `file:line` existen (fase 1) → evalúa y entrega la tabla Observación/Recomendación/Mejora con
cumplimiento y esfuerzo (fase 2) → propone los tres de esfuerzo S y alto impacto como primeros
items, y sugiere subir dos reglas a `catalog.yaml` (fase 3).

### User: "quiero que el agente escriba los endpoints nuevos con nuestro estilo"
TL: **no** lanza esta skill. Le pasa `apps/orders/views.py` y `apps/orders/serializers.py` como
precedentes y, si el objetivo es vigilarlo de forma continua, propone añadir la regla a
`.claude/patterns/` para que la juzgue Rita.

## Related

- `rita-pattern-keeper` (agente) + `pattern-gate` + `.claude/patterns/` — consistencia de patrón
  continua y barata; esta skill es la foto periódica, Rita es la vigilancia
- `codebase-onboarding` — genera el CLAUDE.md del repo; se lanza antes que esta skill
- `code-review-gate` — gate de un diff concreto (esta skill no es un gate)
- `rules/verdict-contract.md` — el Intent y la regla "solo lo observado" que usa la fase 2
- `pol-product-advisor` (agente) — consume el informe para priorizar
- `rules/report-kit.md` — si la evaluación necesita decisiones persistentes en vez de un markdown
