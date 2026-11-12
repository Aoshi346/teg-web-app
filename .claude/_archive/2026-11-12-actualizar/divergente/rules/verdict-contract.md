---
paths:
  - ".docs/feedback/**"
---

# Contrato de veredicto — verificación estructurada con doble evidencia

> **Cuándo aplicar:** siempre que un agente **verifica si algo está hecho** contra una fuente de
> verdad (un item de feedback contra producción, un criterio de aceptación contra el código, un
> finding de QA). Define un **esquema de salida único** para que el veredicto sea comparable,
> agregable y trazable — y un **formato de nota anti-alucinación** que obliga a citar evidencia de
> código *y* de ejecución en vivo antes de afirmar "hecho".
>
> **NO aplicar:** para generar copy, planear, o tareas sin un "¿está hecho?" que verificar.
>
> **Relacionado:** `verification.md` (gate de 4 niveles), `qa-loop.md`, `e2e-stability.md`,
> comando `speckit.specify` (escribe los criterios en Gherkin que esta rule verifica), skill
> `feedback-audit` (lo usa como `schema` de su workflow), `verification-loops`, `ux-reviewer`,
> `code-review-gate`; agentes auditores (`rita-pattern-keeper`, `ignacio-roig`, `sofia-pentester`…).

---

## El esquema (salida estructurada por item)

```
id            string         identificador del item verificado
verdict       enum           done | partial | notdone | blocked | review
confidence    enum           alta | media | baja
precision_pct int 0..100     nivel de cumplimiento/confianza (si falta → mapeo desde confidence:
                             alta=95 · media=80 · baja=50)
interpretacion string        qué pide el item, parafraseado (qué se considera "hecho")
why           string         evidencia que sustenta el verdict (con file:line y/o DOM/screenshot)
howto         string         qué falta para llegar a "done" (vacío si done)
anchor_type   enum           text | selector | scroll_pct   (dónde está la evidencia en la página)
anchor_value  string         el texto/selector/% concreto
viewport      enum           desktop | mobile

— extensión SBI-I (QA-4), opcional pero recomendada en hallazgos de auditoría —
impact        string         consecuencia CONCRETA del hallazgo (a quién afecta y en qué), no la severidad
intent        enum|string    deliberate | unknown | accident  (+ la razón si es deliberate)
```

Este es el **JSON Schema** que un workflow pasa como `schema` a cada agente verificador
(StructuredOutput → validado en la capa de tool-call, sin parseo manual). Es agregable: contar
`verdict` por página/epic da el avance; `precision_pct` da el termómetro.

## El formato de nota — **doble evidencia** (anti-alucinación)

El campo `why`/`note` de un item verificado **debe** separar lo que se vio en el código de lo que se
vio en vivo. Afirmar "hecho" sin **ambas** es un anti-pattern (el código puede tener algo que no se
renderiza, o el DOM puede mostrar algo que no está en el repo):

```
🔎 Código:  <verdict> — <hallazgo con file:line>
👁 En vivo:  <verdict> — <hallazgo con DOM/screenshot>
➡️ Qué falta: <gap concreto hacia "done">
📋 Instrucción: <acción reproducible para cerrarlo>
```

Ejemplo real (de una auditoría):
```
🔎 Código: partial — functions.php:536-588 define los redirect maps; las URLs del nav son válidas
👁 En vivo: partial — menú con toggles "#" (esperado) + links reales; auditoría 200 de TODOS pendiente
➡️ Qué falta: verificar status HTTP de CTAs/footer/descargas
📋 Instrucción: correr capture_pages.py --audit-links y revisar _links_audit.json
```

## Reglas

1. **`done` exige doble evidencia coincidente** (🔎 y 👁 ambos ≥ done). Si solo una lo confirma →
   `partial` con `howto` explicando qué falta verificar.
2. **`review`** = el agente no puede decidir (ambigüedad o falta de contexto), NO "casi hecho".
   `blocked` = depende de un input externo (asset/decisión/servicio).
3. **No inventar**: `why` cita evidencia concreta (file:line, texto del DOM, nombre de screenshot).
   Sin cita → `confidence: baja`.
4. **Trazabilidad al origen**: si el item viene de una cita textual (feedback de cliente, criterio
   de un doc), conserva la cita **verbatim** (`texto_original`) para CTRL+F — no la parafrasees como
   si fuera la fuente.

## Extensión SBI-I — Impact, Intent y "solo lo observado" (QA-4)

SBI-I es el contrato de feedback de liderazgo técnico (Situation · Behavior · Impact · **+ Intent**)
aplicado aquí a un auditor automático. El esquema de arriba ya cubre **Situation** (`anchor_*`,
`viewport`: dónde exactamente) y **Behavior** (`why`: qué se observó). Faltaban las dos piezas que
convierten un hallazgo en algo accionable y justo — y la regla dura que impide inventarlo.

### 1. Impact — la consecuencia narrada, no la severidad

`severity: P1` dice **cuánto corre prisa**; no dice **qué pasa si no se arregla**. Un humano prioriza
con lo segundo. El campo `impact` responde: **¿a quién afecta, haciendo qué, y con qué resultado?**

| ❌ Sin Impact (solo severidad) | ✅ Con Impact |
|---|---|
| `P1 — falta validación en el formulario de alta` | `P1 — impact: un usuario que envía el alta sin NIF ve un 500 en blanco y pierde lo escrito; soporte recibe ~3 tickets/semana por esto` |
| `P2 — contraste 3.1:1 en los botones secundarios` | `P2 — impact: con sol directa en móvil el botón "Cancelar" es ilegible; falla WCAG AA y es el patrón usado en 14 pantallas` |

Regla: si no sabes decir la consecuencia, **no has terminado de verificar**. Un `impact` de relleno
("es una mala práctica") equivale a no tenerlo.

### 2. Intent — preguntar POR QUÉ está así antes de condenar

**El antídoto del falso positivo.** El código raro suele ser deliberado: alguien ya se encontró con
el caso que tú acabas de "descubrir". Antes de emitir `notdone`/`partial` sobre algo que parece un
error, el verificador **busca la intención** y la registra:

```
intent: deliberate — "// workaround: la API de Stripe devuelve 200 con body vacío en reintentos (#412)"
→ el hallazgo NO se reporta como defecto; a lo sumo como "documentar mejor"
```

Dónde buscar el intent, en este orden (todo es barato y verificable):

1. **Comentario en el propio código** — la lista que `/simplify` ya respeta y que aquí se
   generaliza a cualquier auditor:
   `// defensive: reason` · `// workaround: issue #N` · `// historical: reason` ·
   validaciones en boundaries de sistemas externos · tests aparentemente redundantes que cubren un
   edge case documentado.
2. **`git log -L` / `git blame` de esas líneas** — el mensaje de commit suele contener el porqué.
3. **`.claude/patterns/`, ADRs, `MEMORY.md`, rules del proyecto** — si es patrón del repo, no es
   defecto (es el eje de Rita).
4. **Si tras eso sigue sin explicación** → `intent: unknown` y el hallazgo **se reporta como
   pregunta, no como sentencia**: "¿es deliberado? Si lo es, márcalo con `// defensive:`".

```bash
# El intent de una línea concreta, en dos comandos
git log -L 120,135:src/payments/checkout.py --oneline | head -20
git log --oneline -S "retry_on_empty_body" -- src/payments/
```

> Consecuencia operativa: un hallazgo con `intent: deliberate` **baja de severidad o desaparece**.
> Esto es lo que separa a un auditor útil de uno al que se deja de leer.

### 3. Solo comportamientos observados directamente — nunca de oídas

**Regla dura, no negociable:** un verificador reporta **únicamente lo que ha visto él mismo** — el
fichero que abrió, el DOM que capturó, el comando que ejecutó. Nunca lo que le contó otro agente,
lo que dice un informe previo, ni lo que "suele pasar en proyectos así".

Aplica muy en particular al **fan-out de subagentes**: cuando un agente sintetiza los informes de
otros tres, esos informes son **fuentes de segunda mano**. Se citan como tales
(`según el informe de <agente>`) y **no pueden sustentar un `done`** — el sintetizador que quiera
afirmar `done` re-verifica. La lección `fix-declarado-no-verificado` del QA de TPL-1 es exactamente
este fallo: dos fixes declarados que nadie había visto renderizados.

| Formulación | Veredicto permitido |
|---|---|
| "Abrí `checkout.py:88` y la validación existe" + screenshot del render | `done` |
| "El informe de la ronda anterior dice que se arregló" | como mucho `review`, y citando la fuente |
| "Esto normalmente falla en Safari" | no es un hallazgo — o lo pruebas, o no existe |

### Formato de nota extendido (sustituye al de arriba en hallazgos de auditoría)

```
🔎 Código:  <verdict> — <hallazgo con file:line>
👁 En vivo:  <verdict> — <hallazgo con DOM/screenshot>
💥 Impact:   <a quién afecta, haciendo qué, con qué resultado>
🤔 Intent:   <deliberate|unknown|accident> — <evidencia: comentario, commit, patrón>
➡️ Qué falta: <gap concreto hacia "done">
📋 Instrucción: <acción reproducible para cerrarlo>
```

## Criterios en Gherkin → verificación mecánica (SPEC-3)

**Gherkin, en cinco palabras: lenguaje estructurado para criterios de aceptación.** Se escribe
`Dado que [contexto] / cuando [acción] / entonces [resultado]`. El formato lo define
`speckit.specify`; aquí importa **por qué** ese formato: un criterio en Gherkin **ya trae dentro el
plan de su propia verificación**, y esta rule solo tiene que ejecutarlo.

| Cláusula Gherkin | Qué es al verificar | Campo del esquema |
|---|---|---|
| **Dado que** [contexto] | el estado inicial que hay que montar (seed, login, datos) | precondición del test — ver `e2e-stability.md` §1 |
| **Cuando** [acción] | el paso reproducible que ejecuta el verificador | `howto` / `📋 Instrucción` |
| **Entonces** [resultado] | la aserción observable → decide el `verdict` | `why` (con la evidencia 🔎/👁) |

Ejemplo completo, de criterio a veredicto:

```gherkin
Dado que soy un usuario autenticado con el carrito vacío
cuando añado un producto agotado
entonces veo el aviso "Sin stock" y el botón de pagar sigue deshabilitado
```

```
id: AC-14
interpretacion: con stock 0, el CTA de pago no se habilita y se muestra el aviso
🔎 Código: done — cart/views.py:212 marca out_of_stock; CheckoutButton.tsx:38 lo usa como `disabled`
👁 En vivo: done — con seed de stock 0 aparece "Sin stock" (data-testid="stock-warning") y
            [data-testid="checkout-submit"] tiene el atributo disabled (screenshot cart-oos.png)
💥 Impact:  n/a — criterio cumplido
🤔 Intent:  n/a
verdict: done · confidence: alta · anchor_type: selector · anchor_value: [data-testid="stock-warning"]
```

Lo que gana el ciclo: el "Entonces" es **una sola aserción observable**, así que el verdict no
admite interpretación. Si un criterio no se puede escribir así (su "entonces" no es observable), el
criterio está mal escrito — devuélvelo a la spec en vez de verificarlo a ojo.

## Mapeo verdict → status del dashboard (puente, no colisión)

El `verdict` (eje "¿está hecho?") y el `status` Kanban del dashboard (`speckit_dashboard/`, eje "¿en
qué fase del flujo está?": `backlog/doing/review/done/blocked`) comparten 3 palabras. **No son lo
mismo** — son ejes distintos — pero hay un puente directo, el que aplica `reconcile.py` (`V2STATUS`):

| verdict | → status | por qué |
|---------|----------|---------|
| `done` | `done` | verificado con doble evidencia ⇒ justifica la columna Done |
| `partial` / `notdone` | `backlog` | falta trabajo ⇒ vuelve al flujo |
| `blocked` | `blocked` | misma semántica en ambos ejes (input externo) |
| `review` | `review` | **ambos significan "un humano debe mirarlo"** (ver aviso) |

> ⚠️ **`review` es el solape a vigilar.** Aquí el verdict `review` = *"el verificador NO puede
> decidir"* (incertidumbre). En el dashboard, el status `review` suele leerse como *"casi listo,
> pendiente de aprobar"* (progreso positivo). El **puente es legítimo** porque la acción coincide (lo
> mira un humano), pero **no asumas que el verdict `review` significa "casi hecho"**: significa "no sé".
> Si lo que quieres decir es "casi hecho", el verdict correcto es `partial`.

## Anti-patterns
- ❌ Afirmar `done` con solo evidencia de código (no se verificó el render) o solo en vivo (no se
  ubicó en el repo) → es `partial`.
- ❌ Usar `review` como "parcial" → distorsiona los conteos de avance.
- ❌ `why` genérico ("parece estar bien") sin file:line ni DOM → equivale a no verificar.
- ❌ Parafrasear la cita del cliente y perder el `texto_original` verbatim.
- ❌ Reportar un defecto sin haber buscado el **Intent** → falso positivo sobre código deliberado
  (`// defensive:`, `// workaround: #N`, `// historical:`) que quema la credibilidad del auditor.
- ❌ Confundir **severidad** con **Impact**: `P1` no explica qué le pasa al usuario.
- ❌ Sustentar un `done` en el informe de otro agente en vez de en observación propia (de oídas).
- ❌ Verificar a ojo un criterio cuyo "entonces" no es observable → devuélvelo a la spec.

---

_Rule version: 1.1 · adaptado de un harness de auditoría en producción (bcnlip) ·
v1.1 (2026-08-08): extensión SBI-I (Impact · Intent · solo-lo-observado, QA-4) y puente
Gherkin→verificación (SPEC-3)_
