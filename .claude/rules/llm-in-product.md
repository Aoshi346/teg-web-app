---
paths:
  - "**/llm/**"
  - "**/*llm*.py"
  - "**/*llm*.ts"
  - "**/prompts/**"
  - "**/providers/**/*.py"
  - "**/adapters/**/*.py"
  - "**/extract*/**/*.py"
  - ".claude/patterns/stack/agente-modelo-y-coste.md"
  - ".claude/templates/bot-data/prompt_version.py"
---
# El LLM dentro del producto — por dónde entra, qué decide y qué se le manda

> **Cuándo aplicar:** cuando el PRODUCTO (no el harness) llama a un modelo de lenguaje, o consume lo
> que un modelo devolvió: clasificar un correo, extraer campos de un documento, redactar un texto a
> partir de números ya calculados, el turno de un bot. Define **cuántos puntos de entrada hay y dónde
> se declaran**, qué se le permite decidir al modelo, qué se comprueba antes de enseñar su respuesta,
> cuánto puede costar un lote y qué no sale hacia el proveedor.
>
> **NO aplicar:** a qué hacer cuando falta la clave o cae el proveedor, que es
> `external-provider-dependency.md` · a qué modelo elegir y qué rompe al cambiarlo
> (`patterns/stack/agente-modelo-y-coste.md`) · al reparto modelo/código **dentro** de un agente con
> tools (`patterns/stack/agente-determinismo.md`, más detallado para ese caso) · a la seguridad del
> harness que programa (`agent-security.md`) · a la base legal de mandar datos a un tercero (Priya;
> Sara si hay salud), que manda sobre esta.
>
> **Relacionado:** `agent-security.md` §6 (separar extracción de acción) · `agent-security-bots.md`
> (ASI01: el contenido es dato) · `verdict-contract.md` (veredicto de tres estados) ·
> `patterns/stack/agente-observabilidad.md` §1b (versión del prompt) · `mocks-externos.md` §9.
>
> Cosechada de accounting_AMC (`rules/llm-en-el-producto.md`, 11-09-2026), donde el LLM entra por
> **dos** puntos declarados y en ningún otro. Aquí va sin su dominio (gestoría, A3, DPA).

## 0. Los puntos de entrada se declaran, y son pocos

Un proyecto que dice dónde **no** entra el LLM («la conciliación es determinista») y no dice dónde
**sí** tiene un hueco con forma de permiso: la primera persona que necesite leer un PDF improvisa el
contrato. Por eso, en cuanto el producto tenga el primer punto:

1. **Una tabla en la rule de dominio del proyecto** (o en su `CLAUDE.md`): *«Entra aquí»* — cada
   punto con su tarea (clasificar, extraer, redactar) — y *«No entra en nada más»*, con las
   decisiones de negocio que quedan fuera (importes, cuadres, qué cliente es, qué se envía).
2. **Un solo módulo por el que pasan todas las llamadas** (`core/llm/`, o el adaptador de
   `external-provider-dependency.md` §1). Un `openai.chat.completions.create` suelto en una vista es un
   punto de entrada nuevo sin declarar.
3. **Añadir un punto es una decisión, no un commit**: se añade a la tabla con su porqué, y la tarea
   tiene que ser de **lectura con ambigüedad real** que acaba en una propuesta que mira alguien o que
   el código comprueba.

## 1. Lo que llega de fuera es DATO, nunca instrucción

Un PDF, un correo o una reseña es texto que escribió otro, y para el modelo no hay diferencia entre el
documento y una orden. No se filtra (no hay filtro que distinga uno preparado): **se acota el daño.**

- El documento va en su **propio bloque, marcado como dato**; nunca concatenado al prompt de sistema.
- **La llamada que lee contenido ajeno no tiene tools**: sin red, disco ni base de datos.
- **La salida es un formulario de campos tipados** (salida estructurada); lo que no cabe en un campo
  se descarta. Ningún campo «observaciones» por el que cuele prosa.
- **Nada de lo extraído decide qué se hace**: no elige rama, no nombra un fichero, no compone una
  consulta. Son datos que se comprueban (§3), nunca verbos.
- **Extracción y acción, en pasos distintos**, con la comprobación de §3 y una persona entre ellos.

## 2. Lo que no aparece es `null`, nunca un valor plausible

Un modelo completa: si el contrato exige un número que el documento no trae, pondrá uno verosímil e
indetectable aguas abajo.

- **Todo campo del contrato de extracción es opcional** (`T | None`), también los que «siempre vienen».
  Un campo obligatorio obliga al modelo a inventarlo: es un bug del esquema, no del modelo.
- `None` es una respuesta correcta: no cuenta como error ni dispara reintento.
- Prohibido el valor por defecto (`0`, `""`, la fecha de hoy, «el 21 % porque casi siempre es 21»), y
  derivar un campo de otro en silencio.
- En pantalla, **«no consta»**, nunca un blanco (se lee como cero).

## 3. El LLM propone, el código comprueba

Ninguna salida de un modelo llega a una pantalla, un fichero o un informe sin pasar por código
determinista: aritmética (`base + cuota = total`), formato (NIF, fecha), resolución de identidades por
código, no por el modelo. Lo que no se puede comprobar con código (una clasificación) lo mira una
persona antes de que tenga efecto.

- **El veredicto tiene tres estados**: `ok` · `descuadre` · `no comprobable`, y el tercero **nunca se
  pinta en verde** (`verdict-contract.md`).
- **El resultado es el desglose** de lo comprobado (qué, con qué números, cuánto se desvió), no un
  booleano.
- **`Decimal` para dinero**, nunca `float`.
- Si el LLM evalúa o puntúa, **la nota la calcula el código**: `patterns/stack/agente-juez-llm.md`.

## 4. Tope de gasto por lote, declarado antes de lanzarlo

- **En configuración y comprobado antes de empezar**: documentos, tokens y coste máximo del lote.
- **Al alcanzarlo, el lote PARA y lo dice**: ni modo degradado, ni recortar el documento, ni cambiar
  a un modelo más barato por su cuenta.
- **Un reintento y escala** (`parallelization.md` DEC-5).
- **El mismo documento no se procesa dos veces**: caché con clave `hash(documento) + versión del prompt
  + modelo`.
- **Se registra por lote**: documentos, tokens, coste, **modelo exacto** (snapshot, no alias) y
  **versión del prompt** (`agente-observabilidad.md` §1b). Son las dos preguntas que siempre llegan:
  «¿cuánto costó?» y «¿esto lo sacó el prompt viejo?».

## 5. Qué NO se manda al proveedor

El proveedor es un punto por el que los datos salen del servidor; cada llamada es donde la
minimización se puede demostrar, o no.

| Se manda | NO se manda |
|---|---|
| El documento o el fragmento que hace falta leer | Listas de clientes, el resto del expediente, el árbol de carpetas |
| Un prompt propio, versionado | Datos de otro cliente o de otro comercio |
| | Identificadores internos, rutas, credenciales, nombres de buzón |

- **Metadatos primero, contenido solo de lo que se va a procesar** (dos pasadas).
- **La región y el proveedor, por configuración** (`LLM_PROVIDER`), para que cambiarlos no sea un
  refactor. Si hay datos personales, la base legal y el subencargado van antes (Priya).
- **El log guarda qué se mandó, no el contenido**: hash, tamaño, tipo, modelo, tokens, resultado. Un log
  con el prompt entero es una segunda copia de los datos sin declarar.
- **Sin base legal no sale nada real**: se desarrolla contra simuladores (`mocks-externos.md`) y
  ninguna llamada de desarrollo lleva un documento real.

## Anti-patterns

- ❌ Una llamada al modelo fuera del módulo declarado → un punto de entrada que nadie sabe que existe.
- ❌ Meter el LLM en un importe o una decisión de negocio «porque el caso es ambiguo» → la ambigüedad
  se le enseña a una persona.
- ❌ Concatenar el documento al prompt de sistema, o darle tools a la llamada que lo lee.
- ❌ Un campo obligatorio en el esquema de extracción, o un hueco relleno con un valor plausible.
- ❌ Enseñar un número extraído sin pasarlo por la comprobación, o colapsar «no comprobable» con «ok».
- ❌ Lanzar un lote sin tope, o seguir en modo degradado al alcanzarlo.
- ❌ Registrar el coste sin el modelo exacto y la versión del prompt.
- ❌ Guardar el prompt completo en el log.

---

_Rule version: 1.0 · 2026-10-31 · sub-ola 3.26 de la revisión integral (CB-86). Generalizada de
accounting_AMC `rules/llm-en-el-producto.md` v1.0 (11-09-2026), sin su dominio._
