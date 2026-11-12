# Plantilla de ticket rico — los 10 componentes

> **El problema que resuelve:** nuestros `tasks.md` son casillas con estado. Una línea con una
> casilla no dice **cuándo está hecha**, ni por qué se hace, ni qué pasa si no se hace. El resultado
> es que quien la coge tres semanas después reconstruye el contexto de memoria — o lo inventa.
>
> **Cuándo usarla:** trabajo que va a coger otra persona (u otra sesión), que dura más de medio día,
> o que tiene criterio de aceptación discutible. **Cuándo NO:** una casilla dentro de una wave que
> estás ejecutando ahora mismo — ahí la línea de `tasks.md` basta y añadir ceremonia la ralentiza.
>
> **Relacionado:** `rules/report-kit.md` (el esquema de item — **este documento se pliega a él, no
> lo sustituye**) · `rules/speckit-workflow.md` §SpecKit Progress Tracking (las casillas en vivo) ·
> `rules/verdict-contract.md` §Gherkin (por qué los criterios se escriben así) ·
> `templates/prd-template.md` (el nivel de arriba).

---

## ⚠️ Esto NO es un esquema nuevo

`rules/report-kit.md` regla 1 es explícita: **está prohibido inventar el quinto esquema de item.**
Antes convivían cuatro incompatibles y fue un problema real.

Así que esta plantilla **no crea campos**: es la versión legible para humanos de los campos que ya
existen. La tabla de correspondencia es parte de la plantilla, no un apéndice:

| # | Componente del ticket | Dónde vive ya |
|---|---|---|
| 1 | Identificador y título | `id` + `title` · línea de `tasks.md` |
| 2 | Tipo | prefijo del título (ver §2) |
| 3 | Contexto y justificación (4 bloques) | `desc` |
| 4 | Objetivo observable | `goal` · línea `goal:` |
| 5 | Criterios de aceptación | `manual_test` · líneas `test:` / `case:` |
| 6 | Fuera de alcance | bloque `⚠️ AVISO` de `desc` |
| 7 | Dependencias | `blocks:` |
| 8 | Prioridad y esfuerzo | `severity` + `effort` · `[P0/M]` |
| 9 | Evidencia y definición de terminado | `evidence[]` + `verdict` |
| 10 | Referencias | `refs[]` |

**Si te falta un campo, se propone en `item.schema.json` — no se improvisa aquí.**

---

## La plantilla

```markdown
- [ ] `<ID>` [<P0|P1|P2|P3>/<S|M|L|XL>] <feature|bug|spike|chore>: <título en imperativo>
  goal: <el resultado observable, en una línea>
  blocks: <IDs que no pueden empezar hasta que esto esté>
  prereq: <lo que tiene que estar levantado para probarlo>
  test: <Dado que… cuando… entonces…>
  refs: <enlaces>
```

Y el cuerpo largo (el campo `desc`), con **estos cuatro rótulos exactos y en este orden** — el
dashboard los detecta y los separa en párrafos:

```markdown
📍 Cómo está ahora — <qué hay hoy y qué duele, con el fichero o el dato concreto>
🎯 Qué queremos conseguir — <el resultado observable, no la tarea>
🔧 Cómo se haría — <el mecanismo: qué se crea o se toca, con qué herramienta>
🧭 Por qué así y no de otra manera — <la alternativa obvia y por qué pierde. Límites honestos>
⚠️ AVISO — <opcional: qué cuesta, qué puede salir mal, o qué NO cubre → aquí va el fuera de alcance>
```

---

## Los 10 componentes, uno a uno

### 1 · Identificador y título
`ID` estable con prefijo de módulo (`API-1`, `UI-3`). **No se reutiliza nunca**, ni aunque el ticket
se cancele. El título, en imperativo y describiendo el **resultado**: "Endpoint de alta de cliente
devuelve 201", no "Trabajar en el alta".

### 2 · Tipo — y por qué el *spike* va separado

| Tipo | Qué es | Cómo se cierra |
|---|---|---|
| `feature` | Capacidad nueva | El criterio de aceptación se cumple |
| `bug` | Algo que ya debería funcionar y no funciona | Un test que **falla antes y pasa después** |
| `spike` | **Investigación**: no sabemos aún qué hay que construir | Con una **decisión escrita**, no con código |
| `chore` | Mantenimiento sin cambio de comportamiento | Los tests siguen verdes y el diff está acotado |

> **El spike se separa del ticket de implementación a propósito.** Cuando la investigación va
> escondida dentro del ticket de construir, pasan dos cosas malas: la estimación es mentira (nadie
> sabe cuánto tarda averiguar algo) y la decisión no queda escrita en ningún sitio, así que dentro
> de seis meses se vuelve a investigar lo mismo.
>
> **Reglas del spike, y son duras:**
> - Lleva **límite de tiempo** (`timebox`) en el propio ticket: *"4 horas; si al acabar no hay
>   respuesta, la respuesta es «no lo sabemos» y se decide con eso"*.
> - Su entregable es **una recomendación con alternativas descartadas**, no una rama.
> - **Puede terminar en «no hacerlo»**, y eso es un éxito del spike.
> - Si la decisión es cara de revertir (arquitectura, esquema, contrato de API), el entregable es
>   directamente un **ADR** (`rules/adr.md`).
> - Se cierra **antes** de estimar el ticket de implementación que depende de él (`blocks:`).
>
> Este tipo conecta además con el eje de confianza de `rules/plan-gates.md` §1b: con baja confianza
> en el enfoque, lo correcto es un spike, no un contrato detallado sobre una suposición.

### 3 · Contexto y justificación — los 4 bloques
Escritos **para alguien que no conoce la jerga**. Cada término técnico se explica la primera vez con
un ejemplo concreto, y se dice el coste, no solo el beneficio. Es la parte que más se incumple y la
que más valor tiene. El estándar completo, con su tabla de mal/bien, está en `rules/report-kit.md`
§"Cómo se escribe un item".

**La prueba de que está bien escrito:** que alguien ajeno al proyecto entienda, leyendo solo el
ticket, qué se gana y qué se arriesga.

### 4 · Objetivo observable
Una línea, en `goal:`. **Resultado, no tarea:** "POST /api/clientes devuelve 201 y persiste", no
"implementar el endpoint". Si no sabes escribirlo como algo observable, todavía no sabes qué pides.

### 5 · Criterios de aceptación (Gherkin)
```gherkin
Dado que <el estado inicial que hay que montar>
cuando <la acción reproducible>
entonces <UNA aserción observable>
```
Cada cláusula tiene un destino en la verificación: el *dado que* es la precondición del test, el
*cuando* es el paso reproducible y el *entonces* decide el veredicto
(`rules/verdict-contract.md`). Sin criterio escrito, el manual de pruebas sale **derivado y
genérico** — y eso ya es el aviso de que el ticket no tenía criterio de verdad.

### 6 · Fuera de alcance
Lo que alguien va a asumir que entra y **no entra**. Va en el bloque `⚠️ AVISO`. Dos líneas aquí
ahorran una discusión en la revisión.

### 7 · Dependencias
`blocks: <IDs>` — una sola línea, y esa es toda la intención: **mientras declarar una dependencia
costara editar JSON a mano, nadie lo hacía** y el diagrama de tiempos salía plano. Declara solo las
que importan de verdad; el resto se deriva del esfuerzo.

Si el ticket depende de algo **externo** (un dato, un acceso, una decisión del cliente), no es una
dependencia: es un **bloqueo**. Casilla `[!]` y la razón escrita al lado
(`rules/speckit-workflow.md` §SpecKit Progress Tracking).

### 8 · Prioridad y esfuerzo
`[P0/M]`. Prioridad: `P0` imprescindible · `P1` importante · `P2` deseable · `P3` algún día.
Esfuerzo: `S`=1 · `M`=3 · `L`=5 · `XL`=10 días (la escala de la casa; de ahí sale el calendario
orientativo del report-kit).

> Un ticket `XL` casi nunca es un ticket: son cuatro. Pártelo
> (`rules/trunk-based-flow.md` §3), porque un `XL` es también una rama que va a vivir demasiado.

### 9 · Evidencia y definición de terminado
Qué hay que **enseñar** para cerrarlo, decidido al abrirlo y no al cerrarlo:

```
[ ] Tests del módulo en verde (salida pegada)
[ ] Endpoint llamado de verdad si lo hay (rules/verification.md §Smoke testing)
[ ] Captura si toca interfaz · vídeo si es un flujo (rules/trunk-based-flow.md §4)
[ ] Sin errores en la consola del navegador
```

### 10 · Referencias
`refs[]`: PRD, ADR, conversación con el cliente, incidencia de origen. ⚠️ Una referencia a un fichero
**fuera de la carpeta del plan no se enlaza, se copia** — un enlace relativo da 404 al servir el
informe (`rules/report-kit.md` regla 6c).

---

## Ejemplo completo

```markdown
- [ ] `API-7` [P1/M] feature: El alta de cliente rechaza NIF duplicado
  goal: POST /api/clientes con un NIF que ya existe devuelve 409 y no crea nada
  blocks: UI-4
  prereq: backend en :8000 con la migración 0012 aplicada
  test: Dado que existe un cliente con NIF 12345678Z, cuando envío un POST con ese mismo NIF,
        entonces recibo 409 y el total de clientes no cambia
  refs: .docs/plans/2026-08-10-altas/prd.md#F-3
```

```markdown
📍 Cómo está ahora — `clientes/serializers.py:41` no valida unicidad de NIF. Se han colado 14
   duplicados en el último mes y hay que fusionarlos a mano; cada fusión son ~20 minutos.
🎯 Qué queremos conseguir — Que sea imposible crear dos clientes con el mismo NIF, y que quien lo
   intenta reciba un mensaje que le diga qué pasa, no un error genérico.
🔧 Cómo se haría — Restricción de unicidad en el modelo + migración, y validación en el serializer
   que devuelve 409 con el id del cliente existente para que la interfaz pueda ofrecer "ir a ese".
🧭 Por qué así y no de otra manera — La alternativa es validar solo en el formulario del frontend;
   funciona hasta que alguien llama a la API directamente, que es justo como entraron 9 de los 14.
   La restricción en base de datos es la única que no se puede saltar.
⚠️ AVISO — La migración falla si ya hay duplicados: hay que fusionar los 14 existentes ANTES.
   No cubre NIFs escritos con formato distinto (con guion, minúsculas) — eso es API-8.
```

---

## Anti-patterns

- ❌ Inventar campos nuevos en vez de proponerlos en `item.schema.json` → el quinto esquema.
- ❌ Ticket sin criterio de aceptación observable → el manual de pruebas sale genérico, y eso ya te
  está avisando de que nadie sabe cuándo está hecho.
- ❌ Meter la investigación dentro del ticket de implementación → estimación falsa y decisión que no
  queda escrita. Eso es un `spike`.
- ❌ `spike` sin límite de tiempo → investigación infinita.
- ❌ Los cuatro bloques rellenos con jerga → el ticket lo tiene que entender alguien de fuera.
- ❌ Escribir "🧭 es más limpio y escalable" → el porqué es una comparación con la alternativa, no
  un adjetivo.
- ❌ Ticket `XL` sin partir → es una rama que va a vivir una semana.
- ❌ Aplicar esta plantilla a **todas** las casillas de una wave → ceremonia, y entonces no se
  rellena ninguna bien.
- ❌ Decidir la evidencia al cerrar en vez de al abrir → siempre sale "los tests pasan" y ya.

---

_Template version: 1.0 · PRO-3, aprobado 2026-08-08. SPEC-5 (la capa de producto completa sobre
SpecKit) fue **descartada**: esta plantilla va suelta y se pliega al esquema de item existente._
