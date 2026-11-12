---
name: "disenar-pantalla"
description: >-
  Usar para DECIDIR CÓMO VA A SER una pantalla antes de programarla: 'diseñemos la pantalla de
  pedidos', 'no sé cómo debería verse esto', 'hazme un boceto de X', 'maqueta la pantalla'. NO usar
  para: escribirla (nueva-pantalla), auditar lo construido (ux-reviewer, vera-art-director,
  lidia-naive-tester), los tokens (frontend-design-system.md) ni un informe de plan (report-kit).
user-invocable: true
metadata:
  version: 1.1.0
  author: tech-lead-template
  category: workflow
  updated: 2026-08-22
  verificado: 2026-08-08
---

# disenar-pantalla — decidir la pantalla antes de construirla

## Principio

`nueva-pantalla` **construye**; esta skill **decide qué construir**. Son dos trabajos y hoy solo
estaba escrito el segundo, así que la primera decisión —qué campos, qué columnas, qué pasa cuando no
hay datos, qué dice el error— se tomaba **sobre la marcha, dentro del generador, por el agente y sin
que nadie la viera**. Cuando el Usuario por fin ve la pantalla, ya son diez ficheros de código: el
coste de cambiar de opinión pasó de cero a una tarde.

El boceto le devuelve a esa conversación su sitio natural, que es **antes**. Un HTML desechable
cuesta minutos, se mira en el navegador, se discute señalando con el dedo y se tira. Lo caro no es
maquetar dos veces: es programar dos veces.

> **Boceto**, aquí, significa exactamente esto: un fichero `.html` que se abre haciendo doble clic,
> que **no** se conecta a nada, que **no** se versiona con el producto y que **se borra cuando la
> pantalla existe de verdad**. No es un prototipo, no es documentación y no es el primer commit del
> frontend. Si acaba en `src/`, esta skill se usó mal.

## Cuándo activar

> **Antes que nada: ¿es UNA pantalla o varias?** Si son ≥2 relacionadas, un embudo o una webapp,
> **primero va `/producto`** — decide qué pantallas hacen falta, en qué orden y con qué objetivo.
> Esta skill entra después, en la capa 9, con la ficha de pantalla ya escrita. Y el **reparto**
> (quién diseña cada pantalla) se lee de `03-screen-inventory.md`, no se vuelve a preguntar.

- «diseñemos la pantalla de <X>» · «hazme un boceto de <X>» · «maqueta la pantalla de <X>»
- «no sé cómo debería verse esto» · «enséñame opciones antes de montarlo» · «¿cómo lo plantearías?»
- Al arrancar una tarea de un plan que dice «pantalla de X» **y nadie ha decidido aún su forma**.
- **Obligatorio antes de `/nueva-pantalla`** cuando la pantalla no tiene precedente en el proyecto
  (no hay otra igual de la que copiar la forma).
- Más disparadores: 'quiero ver cómo quedaría', 'hazme un boceto de la pantalla de X',
  '/disenar-pantalla'. Genera UN html autocontenido con 2-3 variantes lado a lado que se diferencian
  en una decisión estructural nombrada, cada una mostrando los cuatro estados (con datos, vacía,
  cargando, error), y un botón que copia de vuelta la elección ya con el formato de entrada de
  /nueva-pantalla.
- NO usar para: ESCRIBIR la pantalla una vez decidida (eso es nueva-pantalla, que rellena el molde
  de 10 ficheros), auditar una pantalla ya construida (ux-reviewer, vera-art-director,
  lidia-naive-tester), definir el sistema de tokens del proyecto
  (patterns/stack/frontend-design-system.md), ni para un informe o dashboard de decisiones de un
  plan (report-kit).

**Cuándo saltársela, y decirlo:** si el proyecto ya tiene tres pantallas del mismo tipo y esta es la
cuarta, la forma **ya está decidida** — el precedente manda. Ve directo a `/nueva-pantalla` y no
gastes una ronda de bocetos en reabrir algo que el repo ya resolvió.

## Input contract

| Dato | Ejemplo | Si falta |
|---|---|---|
| **qué pantalla** y para quién | «pedidos, la ve el administrativo cada mañana» | **Pregunta.** Sin esto no hay nada que bocetar |
| **qué tiene que poder hacer ahí** (2-4 acciones) | ver los del día · dar de alta · marcar como enviado | **Pregunta.** Es lo que decide la estructura |
| **qué datos hay** | el endpoint, o el `schema.yml`, o una lista de campos a ojo | Léelo de `schema.yml` si existe; si no, **asume y márcalo** |
| **origen de tokens** del proyecto | `.docs/core/design-system.md` | Búscalo. **Si no hay, no inventes colores** — ver paso 2 |
| **dirección de arte y perfil** | §0b de `design-system.md`: «Boho Chic Mediterráneo», perfil `web-cliente` | Si el perfil es `web-cliente` y **no hay dirección elegida**, esto no es un boceto de pantalla: es `direcciones-de-arte`, y va antes. En `producto-panel` se hereda del proyecto y ya está |
| **nivel de movimiento** | §4c: 0, 1 o 2 + los efectos con nombre | Hereda el del proyecto. Si §4c está vacía, el boceto sale sin movimiento y **lo dice** en la propia página |
| **cuántas variantes** | 2 o 3 | Por defecto **3** sin precedente, **2** si ya hay una pantalla parecida |

Una **sola** ronda de preguntas, todas juntas, máximo cuatro. Si el Usuario contesta a medias, tira
con los defaults, **escribe en el boceto qué asumiste** (visible en la propia página, no en el chat)
y sigue. Una skill que interroga tres veces no se vuelve a usar.

## Procedimiento

### 1. Mirar lo que ya hay antes de proponer nada

Tres sitios, en este orden, y ninguno es opcional:

```bash
ls .docs/core/design-system.md .claude/patterns/stack/frontend-design-system.md 2>/dev/null
sed -n '/## Patrones fijados/,/^## /p' .docs/core/ux.md 2>/dev/null  # ¿ya se decidió esto?
ls src/features/*/components/*List.tsx 2>/dev/null | head          # ¿hay precedente?
grep -n "<recurso>" src/types/api.d.ts 2>/dev/null | head          # ¿existe el contrato?
```

**Si `ux.md` ya fija el patrón que ibas a bocetar, no lo reabras**: propón el que el proyecto usa y
abre el debate solo si esta pantalla tiene una razón concreta para ser distinta. El precedente en
código dice cómo se hizo; `ux.md` dice **qué se decidió y por qué**, que es lo que hace falta para
saber si aquella razón sigue valiendo aquí.

Si hay una pantalla parecida, **el boceto parte de ella**: la variante A es «como la que ya
tenemos», siempre. Proponer tres formas nuevas cuando el repo ya tiene una es cómo un proyecto
acaba con tres maneras de listar una tabla — el antipatrón que
`patterns/stack/frontend-nueva-pantalla.md` documenta al final.

### 1b. Dos fidelidades, y no es lo mismo el color que la fase

Este boceto es **alta fidelidad**: usa los tokens reales del proyecto. Antes va la **baja
fidelidad**, que contesta otra pregunta y por eso no se puede saltar por comodidad:

| | `--lowfi` | normal (high-fi) |
|---|---|---|
| Contesta | ¿está bien **organizado**? | ¿está bien **resuelto**? |
| Usa | cajas, **texto real**, jerarquía por tamaño | los tokens, los 4 estados |
| Prohibido | el color de marca, la tipografía final, iconos decorados | inventar un color que no esté en `design-system.md` |
| Dura | minutos, y se tira | una o dos rondas |

**Se puede saltar el low-fi cuando hay precedente** — otra pantalla del mismo tipo ya resuelta en el
proyecto: la estructura ya se decidió y copiarla es lo correcto. Saltarlo por prisa, no: si enseñas
un boceto con colores, nadie habla de la estructura, y la estructura es lo caro de cambiar después.

En `--lowfi` las variantes siguen diferenciándose en **una decisión estructural nombrada** (paso 4) —
es justamente lo único que se está decidiendo. Orden completo: `rules/motores-de-diseno.md` Parte F.

### 2. Los colores salen del proyecto o no salen

Si el proyecto declara origen de tokens, **el boceto usa esos valores**, copiados literalmente en un
bloque `:root` al principio del HTML. Si **no** hay origen declarado, el boceto se pinta en **grises
neutros** y lleva un aviso visible arriba: *«sin sistema de tokens declarado — este boceto no
representa el color final»*.

⚠️ **No inventes la marca.** Un boceto con colores bonitos que el código no puede reproducir vende
algo que no existe: se aprueba, se programa, y la pantalla real sale distinta. El decepcionado
tendrá razón. Si falta el origen de tokens, eso **es un hallazgo** y se dice — el procedimiento para
declararlo está en `patterns/stack/frontend-design-system.md` — pero si lo que falta
es la marca ENTERA (no hay identidad, ni paleta, ni nada que declarar), ese documento
no ayuda: solo explica cómo declarar tokens que alguien ya decidió. La salida es la
skill **`marca`**, que los decide. Hasta el 2026-09-12 no existía, y por eso este aviso
era un callejón sin salida: se detectaba el problema y no había dónde mandarlo.

### 3. Escribir UN html con las variantes lado a lado

Convención completa en `rules/html-output.md` (es de obligado cumplimiento, no un consejo). Lo que
esta skill añade encima:

| Requisito | Por qué |
|---|---|
| **Un solo fichero**, CSS y JS inline, **cero CDN, cero `fetch`** | Se abre offline, desde el móvil del Usuario, sin levantar nada |
| **La tipografía de la marca SÍ puede cargarse** (excepción acotada, ver abajo) | Un boceto que enseña la estructura con otra letra no enseña el diseño |
| **Variantes en columnas**, visibles a la vez sin hacer scroll horizontal | Comparar es el trabajo; si hay que ir y volver, no se compara |
| **Cada variante lleva su decisión escrita en la cabecera** | Ver §«las variantes se diferencian en UNA cosa» |
| **Selector de estado** (con datos · vacía · cargando · error) que afecta a todas a la vez | Ver §«los cuatro estados» |
| **Datos de ejemplo realistas**, no `lorem ipsum` ni `Item 1` | Una tabla con nombres reales revela que la columna no cabe; `Item 1` no |

> **La excepción de tipografía, con sus dos condiciones** (`rules/html-output.md` §2 ·
> `rules/motores-de-diseno.md` §F5, decisión del 2026-09-12). Hasta el 2026-09-18 esta skill prohibía
> **toda** fuente remota, y eso hacía imposible lo único que un boceto de alta fidelidad tiene que
> hacer: enseñar cómo se va a ver de verdad. Marca y bocetos pueden cargar la tipografía real
> siempre que: **(1)** la pila lleve su fallback declarado, para que sin red se siga leyendo, y
> **(2)** la página avise de que esa fuente es de la marca y no del sistema. Todo lo demás del
> harness —informes, dashboards, report-kit— sigue con tipografía del sistema, porque tiene que
> abrir offline.
>
> El **low-fi no la carga**: ahí el trabajo es la estructura, y una letra bonita tapa esa
> conversación (`rules/motores-de-diseno.md` §F2).
| **Botón «copiar para construir»** que copia el bloque de traspaso | Cierra el bucle Usuario→agente (`html-output.md` §3) |
| **Bloque «lo que asumí»** visible al pie | Lo que no se dijo, dicho |

Tokens en HSL: usa `hsl(var(--x))`, nunca `var(--x)` directo como color — el gotcha §7 de
`rules/html-output.md`, que produce texto blanco sobre blanco y cuesta media hora encontrarlo.

### 4. Las variantes se diferencian en UNA decisión estructural, y está nombrada

Esta es la regla que hace que el boceto sirva de algo. Cada variante lleva un título que **nombra la
decisión y su consecuencia**, no un adjetivo:

| ❌ Variantes que no deciden nada | ✅ Variantes que deciden |
|---|---|
| «Opción A» · «Opción B» · «Opción C» | **A — tabla con todo a la vista**: cabe todo, se lee mal en móvil |
| «versión limpia» / «versión moderna» | **B — lista + panel de detalle**: móvil bien, dos clics para ver un dato |
| tres veces lo mismo con otro color | **C — tarjetas agrupadas por estado**: se ve el cuello de botella, se pierde el orden por fecha |

Si las tres variantes se distinguen por el color de un botón, no has hecho tres variantes: has hecho
una, tres veces, y le has pedido al Usuario que elija con el estómago. **Dos variantes que deciden
algo valen más que cinco que no.**

### 5. Los cuatro estados, en todas las variantes

Un boceto que solo enseña la pantalla llena es el fallo clásico: se aprueba, se programa, y nadie
había decidido qué pone cuando no hay nada. Cada variante muestra los cuatro:

| Estado | Qué hay que decidir ahí | A dónde va después |
|---|---|---|
| **Con datos** | columnas, orden, qué acción es la principal | ⑤ `<Recurso>List.tsx` — las columnas |
| **Vacía** | el texto y si hay un botón de «crea el primero» | `<Asincrono vacio={…}>` |
| **Cargando** | esqueleto o spinner, y cuántas filas | `<Asincrono cargando={…}>` |
| **Error** | qué dice y si se puede reintentar | `<Asincrono error={…}>` |

No es celo de diseñador: son **literalmente los tres huecos que `<Asincrono>` obliga a rellenar** en
el molde (`patterns/stack/frontend-a-prueba-de-errores.md`). Hoy los rellena el agente inventándose
el texto en el momento de generar. Decidirlos aquí cuesta un minuto y son los textos que el cliente
acaba leyendo.

### 6. Iterar — máximo 3 rondas

Se abre en el navegador, el Usuario mira y responde. Cada ronda: se aplica el comentario, se sube el
número de versión del fichero (`-v2`, `-v3`) y **se conserva el anterior** hasta que la pantalla esté
aprobada — poder volver a la v1 es medio valor de iterar.

⚠️ Recordatorio (repetido a propósito): **no pases a `/nueva-pantalla` sin una elección explícita del
Usuario**, aunque una variante te parezca obviamente la buena. Que te lo parezca es justo cuando más
falla: la variante obvia para quien la dibujó no es la obvia para quien la va a usar cada mañana.

**Si en la ronda 3 no hay convergencia, para.** No es un problema de maquetación: es que el
requisito no está decidido, o que hay dos personas queriendo cosas distintas. Dilo con el formato de
parada de `rules/agent-autonomy-ladder.md` §5.2 (duda · propuesta · alternativa · qué necesitas) y
devuélvelo a quien pueda decidir. Seguir bocetando es gastar rondas en una discusión que no es de
diseño.

### 7. El traspaso — qué recibe `nueva-pantalla`

Aprobada la variante, el botón **«copiar para construir»** copia exactamente esto. **No es un
resumen bonito: es el `Input contract` de `/nueva-pantalla` ya relleno**, más las tres cosas que el
molde no sabe inventarse.

```
pantalla:        Pedidos — la usa el administrativo cada mañana
variante:        B (lista + panel de detalle) · aprobada por el Usuario el 2026-08-08
boceto:          .docs/plans/2026-08-08-pedidos/bocetos/boceto-pedidos-v2.html

recurso:         order / orders
endpoint:        /orders/                        ← confirmado contra schema.yml
ruta app:        /orders
campos:          reference (texto, obligatorio) · amount (número, >0, obligatorio)
                 · delivery_date (fecha, opcional)
columnas:        reference · amount · delivery_date · estado
accion principal: dar de alta

textos:          titulo   = "Pedidos"
                 vacio    = "Aún no hay pedidos. Crea el primero."
                 error    = "No se han podido cargar los pedidos. Reintentar."
                 cargando = esqueleto de 5 filas

supuestos:       delivery_date opcional — no se confirmó, se asumió
fuera del molde: nada        ← o: "el panel de detalle no es CRUD, se escribe a mano"
```

Con ese bloque, `/nueva-pantalla` no pregunta nada: su input contract está entero. Ese es el punto
de unión entre las dos skills y **la única razón por la que esta existe como skill y no como
conversación**.

### 8. Verificar el propio boceto (sí, también esto)

```bash
cd <carpeta del boceto> && python3 -m http.server 8899 --bind 127.0.0.1 &
python3 .claude/scripts/screenshot.py "http://127.0.0.1:8899/boceto-<x>-v<n>.html" /tmp/boceto.png
grep -L 'stylesheet' *.html      # debe listar el boceto: no enlaza CSS externo
```

Mira el screenshot **a 390px de ancho** además de en escritorio: la mitad de las decisiones de
estructura (tabla vs. lista) solo se pueden juzgar en móvil, y es donde una tabla de seis columnas
se cae. Consola del navegador limpia.

### 9. Anotar la decisión donde la lea la pantalla siguiente

El boceto se borra (§siguiente). **La decisión no puede borrarse con él**: si no queda escrita, la
pantalla número once vuelve a discutir el estado vacío que ya se acordó en la tercera, y así es como
un producto acaba con cinco maneras de mostrar lo mismo.

Aprobada la variante, **una línea en `.docs/core/ux.md`** §Patrones fijados — la capa 4 del core
(`rules/plan-docs-structure.md`), que ya trae la tabla hecha y a la que apunta el paso 1:

| Patrón | Cómo se resuelve aquí | Dónde se ve |
|---|---|---|
| Listado de una entidad | lista + panel de detalle: móvil bien, dos clics para ver un dato | Pedidos |

Se toca también `reviewed:` del fichero: sin esa fecha el índice del core lo marca en rojo, y con
razón — nadie ha confirmado que lo escrito siga siendo cierto.

Dos cosas más, cortas y las que más ahorran:

- **Lo rechazado, con su porqué** — «se probaron tarjetas y se descartaron: se pierde el orden por
  fecha» — va a §Decisiones de UX que ya se tomaron. Vale tanto como lo aceptado: evita que dentro
  de dos meses alguien vuelva a proponer lo mismo, y evita que otro lo "arregle" sin saber que fue
  deliberado.
- **Lo que dijo el Usuario, dicho por él y no deducido** («las tablas densas me marean») cambia
  todos los bocetos siguientes. Si no se anota, se pierde con la conversación.

**Lo que NO va ahí:** valores del sistema de diseño (paleta, escala, tipografía). Eso vive en
`.docs/core/design-system.md` y se añade **al origen** con el procedimiento del paso 4 de
`patterns/stack/frontend-design-system.md`. En `ux.md` solo van decisiones de patrón e interacción.

## Dónde vive el boceto (y cuándo se borra)

| Situación | Ruta |
|---|---|
| La pantalla pertenece a un plan | `.docs/plans/<YYYY-MM-DD-slug>/bocetos/boceto-<pantalla>-v<N>.html` |
| Suelta, sin plan | `.docs/html/boceto-<pantalla>-<YYYY-MM-DD>.html` |

**Nunca en `src/`, nunca en la raíz del repo.**

**Ciclo de vida, explícito:** el boceto muere cuando la pantalla existe. Al cerrar la tarea, o se
borra o se archiva junto al plan que lo originó — pero **deja de estar donde alguien lo confunda con
la pantalla real**. Un boceto viejo que sobrevive es peor que ninguno: dentro de tres meses alguien
lo abre, ve una pantalla que nunca se construyó así, y lo toma por documentación. Es el mismo
principio de frescura que `rules/plan-docs-structure.md` aplica a `.docs/core/`: **lo que no se puede
mantener al día, se fecha o se retira.**

## Formato de salida (campos, no prosa)

```
pantalla:      <nombre>
boceto:        <ruta del .html> · v<N>
variantes:     <n> — <decisión de cada una en 4 palabras>
estados:       4/4 en todas las variantes  |  <cuáles faltan y por qué>
tokens:        <del proyecto | grises neutros: no hay origen declarado>
ronda:         <n> de 3
verificación:  screenshot=<ok> · 390px=<ok> · consola=<limpia> · self-contained=<sí>
supuestos:     <lo asumido, o "ninguno">
estado:        <esperando elección del Usuario | aprobada variante <X> | sin converger tras 3 rondas>
siguiente:     <"/nueva-pantalla con el bloque de traspaso" | "decisión de producto pendiente">
```

## Reparto con `nueva-pantalla` (leer antes de tocar cualquiera de las dos)

| | **disenar-pantalla** (esta) | **nueva-pantalla** |
|---|---|---|
| Responde a | ¿cómo debería ser? | ¿cómo se escribe? |
| Produce | 1 html desechable con variantes | 10 ficheros `.tsx`/`.ts` reales |
| Dura | hasta que se decide | hasta que se borre la pantalla |
| Quien decide | **el Usuario**, señalando | el molde, ya decidido |
| Si falta el endpoint | **sigue igual** — se boceta sin backend | **para**: no inventa contratos |
| Termina cuando | hay bloque de traspaso aprobado | pasan comprobador + `tsc` + test |

La frontera es dura en un sentido concreto: **esta skill no escribe ni una línea en `src/`, y
`nueva-pantalla` no vuelve a preguntar por la forma.** Si al construir aparece una decisión de forma
que el boceto no cubrió, no se improvisa dentro del generador — vuelve aquí, media ronda.

## Anti-patterns

- ❌ Escribir el boceto directamente en `src/` «para aprovecharlo luego» → deja de ser desechable, y
  entonces nadie se atreve a tirarlo ni a cambiarlo.
- ❌ Tres variantes que se diferencian en el color → el Usuario elige con el estómago y no se ha
  decidido nada (§4).
- ❌ Enseñar solo la pantalla con datos → el estado vacío se acaba inventando en el generador, que es
  exactamente lo que esta skill existe para evitar (§5).
- ❌ Inventar colores de marca porque el proyecto no tiene tokens → prometes algo que el código no
  puede cumplir (§2).
- ❌ Un CDN de JS o un `fetch` a la API → el boceto deja de abrir offline y el Usuario ve una página
  rota (`rules/html-output.md`). La **tipografía de la marca sí** se carga, con su fallback y su
  aviso (§3); prohibirla entera era impedir que el boceto enseñara el diseño.
- ❌ Cargar la tipografía real **sin fallback** → sin red el boceto cambia de letra y de medidas, y
  lo que el Usuario aprueba no es lo que verá.
- ❌ Pasar a construir sin elección explícita del Usuario, «porque la B es claramente mejor» (§6).
- ❌ Seguir bocetando en la ronda 4, 5, 6 → el problema ya no es el diseño (§6).
- ❌ Bocetar la cuarta pantalla igual que las tres que ya existen → el precedente ya decidió (§Cuándo).
- ❌ Aprobar la variante y no anotarla en `.docs/core/ux.md` → la decisión se va con el boceto, y la
  pantalla siguiente la vuelve a discutir desde cero (§9).
- ❌ Dejar el boceto vivo después de construir la pantalla → dentro de tres meses alguien lo lee como
  documentación de algo que nunca se hizo así.
- ❌ Usar esto para juzgar una pantalla **ya construida** → eso es `ux-reviewer` / `vera-art-director`
  / `lidia-naive-tester`, que miran el producto real, no un dibujo.

## Ejemplos

### User: «necesito la pantalla de pedidos pero no sé cómo plantearla»
TL: pregunta **una vez** (¿quién la usa y cuándo? ¿qué tiene que poder hacer? ¿hay endpoint?) → mira
si hay precedente y si hay tokens → escribe `boceto-pedidos-v1.html` con **3** variantes (tabla ·
lista+detalle · tarjetas por estado), cada una con los 4 estados y datos de pedidos realistas →
screenshot a 1440 y 390 → «está en `.docs/plans/…/bocetos/`, ábrelo y dime cuál; el botón de arriba
te copia lo que necesito para construirla».

### User: «la B, pero el importe que se vea antes que la referencia»
TL: v2 con ese cambio, conserva la v1 → confirma → el Usuario pulsa **copiar para construir** y pega
el bloque → TL invoca `/nueva-pantalla` con ese bloque como input, **sin volver a preguntar nada**.

### User: «monta el panel de control con las ventas del mes, las alertas y el gráfico»
TL: **sí boceta** (aquí el diseño es justo lo difícil: son tres orígenes de datos y hay que decidir
qué manda), y en el traspaso escribe `fuera del molde: no es CRUD sobre una entidad`. Al terminar
**no** llama a `/nueva-pantalla`: se escribe a mano siguiendo el catálogo capa por capa, reutilizando
`<Asincrono>` en cada bloque para que ninguno se quede sin estado de error.

### User: «la pantalla de clientes» (y ya existen pedidos, facturas y albaranes, las tres iguales)
TL: **no boceta** y lo dice: «hay tres pantallas con la misma forma; la cuarta debería salir igual.
Voy directo a `/nueva-pantalla` copiando la estructura de pedidos. Si quieres replantear la forma de
las cuatro, eso sí es un boceto — pero es otra tarea.»

## Related

- `nueva-pantalla` — **el par de esta skill**: recibe el bloque de traspaso y escribe los 10 ficheros
- `.claude/patterns/stack/frontend-nueva-pantalla.md` — el molde, y su límite escrito
- `.claude/patterns/stack/frontend-a-prueba-de-errores.md` — `<Asincrono>`: por qué los 4 estados
- `.claude/patterns/stack/frontend-design-system.md` · `.docs/core/design-system.md` — de dónde salen
  los colores del paso 2
- `rules/html-output.md` — la convención del HTML autocontenido y el gotcha de los tokens HSL
- `rules/plan-docs-structure.md` — dónde vive lo del plan, y por qué lo que no se mantiene se retira
- `.docs/core/ux.md` (plantilla en `.claude/templates/core/ux.md`) — donde se anota la decisión del
  paso 9, y de donde se lee en el paso 1
- `rules/agent-autonomy-ladder.md` §5.2 — el formato de parada cuando la ronda 3 no converge
- `ux-reviewer` · `vera-art-director` · `lidia-naive-tester` — juzgan la pantalla **construida**
- `html-suelto` — la skill genérica de artefactos HTML; esta es su caso especializado en pantallas
