---
name: producto
description: >-
  Usar SIEMPRE que haya que crear pantallas nuevas (una, varias, un embudo o una webapp): 'necesito
  la pantalla de X', 'monta el funnel', 'diseña la webapp de Y', '/producto'. Recorre por capas y
  pregunta por cada pantalla quién la diseña. NO usar para: la forma de UNA pantalla ya especificada
  (disenar-pantalla), escribir el código (nueva-pantalla) ni configurar el harness (project-setup).
user-invocable: true
metadata:
  version: 1.1.0
  author: tech-lead-template
  category: producto
  updated: 2026-11-01
---

# /producto — de la idea a la pantalla, por capas

## Principio

> **Primero se diseña la experiencia completa, después las pantallas, después los componentes y
> finalmente el código.**

Pedir «créame una web con opt-in, demo y reserva de llamada» produce algo visualmente correcto y
comercialmente inconexo: páginas que no se hablan, lógica improvisada y conversiones débiles. No
porque el modelo sea malo, sino porque **se le pidió el último paso sin los ocho anteriores**.

Esta skill los recorre. No inventa piezas: encadena las que ya existen y **pregunta lo que solo tú
puedes contestar**.

## Cuándo activar / NO activar

| Activar | NO activar |
|---|---|
| Cualquier pantalla nueva — una o veinte | Cambiar un texto o un margen de una que ya existe |
| Un embudo, una webapp, un producto entero | Auditar lo ya construido (`/qa-loop`, `ux-reviewer`) |
| «no sé qué pantallas necesito» | La forma de UNA pantalla ya especificada (→ `disenar-pantalla`) |
| Rehacer un flujo que no convierte | Configurar el harness (→ `project-setup`) |

**Atajo legítimo:** si la pantalla es la cuarta igual que otras tres, las capas 1-5 ya están
contestadas en `.docs/core/producto/`. Léelas, dilo en una línea («el inventario ya cubre esto») y
salta a la capa 9. Repetir el proceso entero para una pantalla obvia es la forma más rápida de que
nadie lo vuelva a usar.

Disparadores: 'necesito la pantalla de X', 'quiero un embudo con landing y demo', 'diseña la webapp de Y', 'monta el funnel', 'hazme las pantallas de', 'varias pantallas', 'quiero una web para captar clientes', '/producto', 'design a funnel', 'build a webapp', 'new screens' · Capas: objetivo → recorrido → mapa de páginas → ficha por pantalla → wireframe → sistema visual → diseño → implementación → pruebas; por cada pantalla pregunta quién la diseña: el agente, a medias, o el Usuario en el canvas · Orquesta piezas que ya existen (disenar-pantalla, nueva-pantalla, design, /schema, /visual-map); no las reimplementa · NO confundir con disenar-pantalla (decide la forma de UNA pantalla ya especificada; esta decide QUÉ pantallas hacen falta y por qué), con nueva-pantalla (escribe el código), ni con project-setup (configura el harness, no el producto).

## Paso 0 — El reparto: ¿quién diseña qué?

**Es la primera pregunta y se hace POR PANTALLA, no de una vez para todo.** Sin esto, el agente
diseña lo que tú querías diseñar, o te hace dibujar veinte pantallas que le daban igual.

| Modo | Hace el agente | Haces tú |
|---|---|---|
| 🤖 **Agente** | Propone 2-3 variantes y las lleva a implementación | Eliges y pides ajustes |
| 🤝 **A medias** *(default)* | Monta el andamiaje y los estados; deja los bloques clave sin decidir | Colocas los bloques en el canvas |
| ✍️ **Tú** | Espera tu wireframe y lo respeta al pie de la letra | Dibujas |

Se guarda como columna en `03-screen-inventory.md`. Se puede cambiar en cualquier momento.

**Para dibujar hay tres vías, y todas valen:**

1. **Canvas `design`** *(recomendado)* — la skill `design` de Claude Code. Multi-artboard: el embudo
   entero en un lienzo, con editor visual (seleccionar, panel de propiedades, editar texto, deshacer)
   y guardado. Es lo que se usa en la capa 6.
2. **Papel o Excalidraw** — dibujas, me pasas la foto o el `.excalidraw`, y lo convierto en ficha +
   wireframe. Cero herramienta que aprender.
3. **Editar el HTML** — sobre el boceto de `disenar-pantalla`, si prefieres tocar código.

## Las 12 capas

| # | Capa | Quién | Sale en |
|---|---|---|---|
| 1 | **Objetivo comercial y métrica** | preguntas · `pol-product-advisor` si hay duda de producto | `01-product-brief.md` |
| 2 | **Usuarios y contexto** | preguntas · skill `/business-manager` si hay canon de negocio | `01-product-brief.md` |
| 3 | **Recorrido completo + bifurcaciones** | la skill | `02-user-flow.md` |
| 4 | **Mapa de páginas** | la skill | `03-screen-inventory.md` |
| 5 | **Ficha por pantalla** | la skill (`templates/screen-spec.md`) | `04-screen-specs.md` |
| 6 | **Wireframes de baja fidelidad** | **skill `design`** (o tu dibujo) | artboards |
| 7 | **Todos los estados** | la skill (checklist abajo) | `04-screen-specs.md` |
| 8 | **Sistema visual** | `marca` si no hay · `patterns/diseno/` (el canon de gusto) · `patterns/stack/frontend-design-system.md` · plugin `frontend-design` | `05-design-system.md` |
| 9 | **Diseño final** | **bifurca por perfil** (ver abajo): `direcciones-de-arte` o `disenar-pantalla` | bocetos |
| 10 | **Datos y eventos** | `/schema` · `/visual-map` | `06-data-model.md` · `07-events.md` |
| 11 | **Implementación** | **`nueva-pantalla`** | código |
| 12 | **Pruebas** | `ux-reviewer` · `/qa-loop` · `visual-regression` | evidencia |

### Capa 9 — la bifurcación por perfil, que es la decisión que más cambia el resultado

| Perfil (§0b de `design-system.md`) | Qué corre en la capa 9 | Por qué |
|---|---|---|
| **`web-cliente`** (landing, web de cliente) | **`direcciones-de-arte`** primero: 3 mundos visuales con NOMBRE, galería con thumbnails, **ranking del Usuario** y fusión. Después `disenar-pantalla` para las pantallas de dentro | Aquí el trabajo es **elegir un mundo**, y eso no se decide pantalla a pantalla. Es el paso que produjo los diseños buenos de esta casa, y el único que no se puede automatizar: **el ranking lo hace una persona** |
| **`producto-panel`** (producto, panel, web app) | **`disenar-pantalla`** directamente: 2-3 variantes que se diferencian en UNA decisión estructural | El mundo visual ya está decidido por el sistema; lo que se decide aquí es la forma de cada pantalla |

Saltarse esta bifurcación tiene un nombre y un coste medido: se diseña una landing de cliente como
si fuera un panel de administración —una sola propuesta, estructural, sin dirección de arte— y sale
correcta y olvidable.

### Capa 1-2 — qué hay que sacar, y qué NO se inventa

Objetivo comercial en una frase: **qué vendes · a quién · qué problema resuelves · qué quieres que
haga · qué necesita creer antes de comprar · qué objeciones tiene · cuánto sabe · de qué canal llega
· qué métrica define el éxito.**

**Lo que falte se marca `[PENDIENTE: …]`, no se rellena con algo plausible.** Un brief con datos
inventados produce un embudo entero construido sobre una suposición que nadie validó.

### Capa 3 — el recorrido, con sus desvíos

El camino feliz es la parte fácil. Lo que decide si el embudo funciona son **las bifurcaciones**:
deja los datos y no entra · entra y no interactúa · usa y no reserva · llega con el enlace caducado
· no encaja con el cliente ideal · quiere hablar con alguien ya.

Cada bifurcación **es una pantalla o un estado**. Si no está en el recorrido, no aparecerá en el
inventario, y se descubrirá en producción.

### Capa 4 — el inventario, separado por producto

Agrupa por **producto**, no por orden de aparición: la experiencia del prospecto y el backoffice
interno son dos cosas distintas y mezclarlas es el error clásico. Columnas: pantalla · objetivo ·
bloque · **quién la diseña** · estado.

### Capa 7 — los estados (el checklist que evita el camino feliz)

`disenar-pantalla` exige cuatro. En un producto real son estos, y **se marcan uno a uno**:

```
[ ] con datos      [ ] vacío (primera vez)   [ ] cargando       [ ] error
[ ] éxito          [ ] desactivado           [ ] seleccionado   [ ] completado
[ ] sin permisos   [ ] sin conexión          [ ] caducado       [ ] móvil
```

Los que no apliquen se marcan **N/A con su razón**, no se borran. «No aplica» es una decisión;
el silencio es un olvido.

## Se trabaja por bloques, y se revisa al cerrar cada uno

**adquisición → activación → experiencia principal → conversión → administración**

Al cerrar cada bloque: ¿las pantallas se hablan entre sí? ¿el usuario sabe siempre dónde está y qué
sigue? ¿algún dato aparece en dos sitios con formatos distintos? **La coherencia se revisa por
bloque, no al final** — al final ya hay veinte pantallas construidas sobre la base equivocada.

## Dónde viven los documentos

```
.docs/core/producto/                    ← lo ÚLTIMO (el presente del producto)
.docs/plans/<fecha>-<slug>/producto/    ← lo que se está trabajando ahora
```

Al cerrar el plan se **promueve** con el mecanismo que ya existe
(`python3 .claude/scripts/gen_core.py --promote <doc-id> <fichero>`), que sella con la fecha del
origen, no con la de hoy. Es el mismo patrón de `plan-docs-structure.md` para los esquemas.

**El mapa de pantallas baja al código** en un frontend React: los ids de la capa 4 (`C01`, `E03`…)
son las claves de `src/app/screens.ts` y las flechas del recorrido (capa 3) son el `DESIGNED_FLOW`
de `flow.ts`; la página `/pantallas` enseña cuáles faltan y si el flujo construido es el diseñado
(`templates/frontend-screens/`, sub-ola 3.67).

## Si el producto tiene bot

En la capa 3, cuando el recorrido incluya una conversación → **`disenar-conversacion`**. La
conversación se diseña, no se improvisa, y su golden set se escribe **antes** de construirla.

## Anti-patterns

- ❌ Empezar por el código. Es el paso 11 de 12.
- ❌ Diseñar pantallas antes de tener el recorrido: salen páginas que no se hablan.
- ❌ Rellenar un dato que falta con algo plausible en vez de `[PENDIENTE: …]`.
- ❌ Saltarse las bifurcaciones: son la mitad de las pantallas reales.
- ❌ Mezclar la experiencia del cliente con el backoffice en el mismo inventario.
- ❌ Diseñar solo el camino feliz — por eso el checklist de estados va marcado uno a uno.
- ❌ Decidir el reparto una vez para todo el embudo en vez de por pantalla.
- ❌ Revisar la coherencia al final.
- ❌ Correr las 12 capas para la cuarta pantalla igual que las otras tres.
- ❌ Dejar los documentos solo en el plan: caducan con él. Se promueven a `core/producto/`.
