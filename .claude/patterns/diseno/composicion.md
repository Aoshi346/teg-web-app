# Composición — dónde va cada cosa, y dónde se gasta la audacia

> **Cuándo aplicar:** al decidir la **estructura visual** de una pantalla antes de escribirla: qué
> lleva el hero, cómo se separan las secciones, qué rejilla, dónde entra una forma o una textura
> que no es contenido. Es la doctrina de la fase **low-fi → high-fi** de `rules/motores-de-diseno.md` Parte F.
>
> **NO aplicar:** para decidir **qué pantallas** hacen falta (`skills/producto`) · para el **orden
> narrativo** de las secciones de una landing, que es `estructura-de-pagina.md` y el copy que lo
> sostiene (`skills/escribir-copy`) · para el **molde de ficheros** de una pantalla
> (`patterns/stack/frontend-nueva-pantalla.md`) · para **rejillas de datos** de un panel, que es un
> problema de tabla y no de composición.
>
> **Relacionado:** `patterns/diseno/README.md` (por qué esto no bloquea) · `tipografia.md` (qué va
> dentro del hueco que esto abre) · `textura-y-profundidad.md` (los tokens de sombra y grano que
> estas formas consumen) · `movimiento.md` (qué de esto se mueve) · `perfiles.yaml` ·
> `resources/referencias-diseno/`.

---

## T9 · Rejilla enmascarada + orbes difuminados

**Qué es.** El fondo del hero lleva dos capas que no son contenido: una **rejilla de líneas de
1 px** recortada con `mask-image` para que se desvanezca hacia los bordes, y **dos orbes** de
`radial-gradient` muy difuminados que flotan despacio.

```css
.hero-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
  background-size: 80px 80px;
  mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 20%, transparent 100%);
}
```
`resources/referencias-diseno/mal/attomo-digital.html:233-240`

**Los orbes**, en `mal/attomo-digital.html:210-227`: `radial-gradient(circle, rgba(255,92,0,.18) 0%,
transparent 70%)` y `rgba(255,140,58,.1)`, con `orbFloat` de 12 s y de 9 s en `reverse`. El marcado
son dos `<div>` vacíos (`:1071-1072`).

**La versión clara del mismo recurso**, sin máscara y sobre fondo pálido —
`bien/elevaiti-v53.html:51`:
```css
.hero::after{content:'';position:absolute;inset:0;
  background-image:linear-gradient(rgba(0,180,216,.04) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,180,216,.04) 1px,transparent 1px);
  background-size:60px 60px;pointer-events:none}
```

**Los tres números que separan esto de un fondo sucio:**

| | Valor medido | Si te pasas |
|---|---|---|
| Opacidad de la línea | **.025 – .04** | A .1 la rejilla compite con el texto y parece papel milimetrado |
| Paso de la rejilla | **60 – 80 px** | Por debajo de 40 px hace *moiré* al hacer scroll |
| Opacidad del orbe | **.1 – .18**, y `transparent` al 70 % | Sin la parada transparente se ve el borde del círculo |

**Qué NO arregla.** Un hero vacío. La rejilla y los orbes son **atmósfera**: si lo único que hay es
un titular corto centrado, se nota más el vacío, no menos. El diagnóstico está escrito en el propio
corpus: la crítica humana de `elevaiti-v2` en `proceso/RANKING.csv` es *«se ve un poco vacía»*, y
esa versión ya tenía tratamiento de fondo.

**Coste.** `pointer-events:none` es obligatorio (está en `bien/elevaiti-v53.html:51` y falta a
menudo): sin él, una capa a pantalla completa se come los clics de lo que hay debajo.
`mask-image` necesita el prefijo `-webkit-` para cobertura antigua; sin él, la rejilla sale entera y
llega hasta los bordes — degrada feo pero no rompe.

---

## T10 · Rejillas con filete: 1-2 px de `gap` sobre fondo teñido

**Qué es.** En vez de dibujar bordes en cada tarjeta, se pone el **contenedor** de un color y se
deja un `gap` de 1-2 px: el fondo se ve por las juntas y **produce** los filetes. Con
`overflow:hidden` y un radio, el bloque queda como una sola pieza.

```css
.metrics-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;
  background:rgba(255,255,255,.06);border-radius:var(--rxl);overflow:hidden}
```
`bien/elevaiti-v53.html:118`

**Por qué es mejor que `border` en cada celda**, y es una razón concreta y no de gusto: con bordes,
las celdas contiguas suman **2 px** en la junta y **1 px** en el perímetro, así que la rejilla sale
desigual y hay que ir apagando bordes con `:last-child`. Con `gap`, todas las juntas miden lo mismo
por construcción y no hay ningún selector de excepción.

**Uso medido:** `gap: 2px` aparece en cinco de las diez referencias
(`bien/kalinayoga-v4.html:590`, `bien/elevaiti-v7.html:1251`, `bien/yessmassage-v7.html:935` y
`:2265`, `bien/elevaiti-v53.html:118`). Es el recurso de composición más repetido del corpus.

**Límite.** Solo funciona si **todas** las celdas tienen fondo opaco. Una celda transparente deja
ver el fondo del contenedor entera y rompe la ilusión — y ese fallo solo se ve cuando los datos
reales dejan una celda vacía, no con datos de ejemplo.

---

## T7 · El número fantasma (y la marca de agua tipográfica)

**Qué es.** Una cifra grande en la **esquina de la tarjeta**, a contraste muy bajo, que numera sin
gritar. Y **no se puede seleccionar**: es gráfico, no contenido.

```css
.pillar-num { position:absolute; top:1.5rem; right:1.5rem;
              font-family:'DM Serif Display',serif; font-size:3.5rem;
              color:var(--arena); line-height:1; user-select:none; }
```
`resources/referencias-diseno/bien/kalinayoga-v6.html:582-591`

**Dos diseños distintos llegaron a la misma solución**, que es lo más cerca de un patrón que hay
aquí — `bien/dale-marketing-v4/styles.css:612-621`:

| | kalinayoga-v6 | dale-marketing-v4 |
|---|---|---|
| Posición | `top:1.5rem; right:1.5rem` | `top:1.5rem; right:1.75rem` |
| Tamaño | `3.5rem` | `3rem` |
| Color | `var(--arena)` (el tono más pálido) | `var(--border)` (literalmente el color de los bordes) |
| `line-height` | `1` | `1` |
| No seleccionable | `user-select:none` | `pointer-events:none` |

**Los tres detalles que lo hacen bien**, y los tres se olvidan:

1. **El color es un token de fondo o de borde**, no un gris inventado. `var(--border)` es la
   declaración más honesta posible de «esto está por debajo de todo lo demás».
2. **`line-height: 1`.** Una cifra a 3,5 rem con interlineado normal arrastra medio renglón de aire
   y descuadra la esquina.
3. **No seleccionable.** `user-select:none` o `pointer-events:none`: si al arrastrar el ratón por
   la tarjeta se selecciona un «03», el número dejó de ser gráfico.

### La variante fuerte: tipografía perfilada como marca de agua

El mismo recurso llevado a tamaño de titular, con solo el contorno:

```css
.hero-h1 .outline { -webkit-text-stroke: 1.5px var(--text); color: transparent; }
```
`mal/attomo-digital.html:282-284`, repetido en el título de sección en `:612-614`.

Es la aplicación literal de `frontend-design:21`: *«cuando el tipo se usa como titular o elemento
visual, usa el tratamiento tipográfico como parte activa del diseño, no como vehículo neutro del
contenido»*. Aparece en **un solo diseño** del corpus: es anécdota, no patrón.

> ⚠️ **Y aquí manda `frontend-design:30`, sin matices:** los marcadores numerados **solo** si el
> contenido es de verdad una secuencia. En `bien/consultorpro.html:1679` (`07 — La Oferta`) lo es
> —la página es un recorrido de venta con orden—; en una cuadrícula de servicios que se leen en
> cualquier orden, numerar es cromo. El propio `catalogo-diseno.yaml` lo marca como
> `conflicto_con` de T7.

**Los dos costes, y el segundo se olvida siempre:**

1. **Accesibilidad.** Un número fantasma **sigue siendo texto en el DOM**: lo lee un lector de
   pantalla. `user-select:none` no lo oculta. Si es puramente decorativo, va con `aria-hidden`; si
   numera de verdad, entonces es contenido y su contraste importa.
2. **`-webkit-text-stroke` no es estándar.** Sin soporte, el texto queda en `color: transparent`,
   es decir, **invisible**. Es el mismo modo de fallo que GD-01 —contenido que depende de que algo
   externo funcione— con otra cara.

---

## T19 · Formas orgánicas: blobs que mutan y divisores de onda

**Qué es.** Una forma sin geometría reconocible, hecha con un `border-radius` de ocho valores que
**cambia en bucle**, muy difuminada y de fondo.

```css
@keyframes blob-morph {
  0%  { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
  50% { border-radius: 50% 60% 30% 60% / 40% 30% 70% 50%; }
  100%{ border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
}
```
`bien/yessmassage-v7.html:538-545`, aplicado en `:521-536` a dos blobs de `38vw` y `32vw` con
`16s`/`20s`, `alternate` y `alternate-reverse`.

**Las tres decisiones que lo hacen legible** y no un adorno de plantilla:

- **Duraciones largas y distintas** (16 s y 20 s): al no ser múltiplos, las dos formas nunca
  vuelven a coincidir y el fondo no tiene «latido».
- **`alternate` / `alternate-reverse`**: ida y vuelta, sin salto al reiniciar.
- **El ciclo vuelve al valor inicial** (0 % y 100 % idénticos): sin eso, hay un corte visible.

**Cuándo aplica, y es estrecho.** Es el recurso de un sector **blando** —bienestar, salud,
cuidado—, y en el corpus aparece exactamente ahí (masaje). En una consultoría o un panel de datos
es ruido: la forma dice «relajación» y el contenido dice otra cosa.

**El coste que nadie mide:** un `border-radius` animado sobre un elemento de `38vw` **repinta
continuamente** y no se puede acelerar por GPU como un `transform`. En un portátil modesto con dos
blobs a pantalla completa se nota. Y si no hay bloque `prefers-reduced-motion`, es exactamente
GD-05 — que es un defecto conocido de dos referencias del corpus.

---

## Ritmo vertical y alternancia de fondos

### El ritmo: un valor, repetido

Lo medido es aburrido y por eso funciona: **un solo valor de padding vertical para todas las
secciones**, con excepciones deliberadas y contadas.

| Ancla | Valor |
|---|---|
| `bien/consultorpro.html:40` | `.section { padding: 80px 0; }` |
| `mal/attomo-digital.html:408`, `:596`, `:689` | `padding: 8rem …` |
| `mal/attomo-digital.html:524` | `padding: 6rem 0` — la excepción: es una banda de logos, más estrecha a propósito |

**La regla:** si el padding de sección aparece escrito con tres valores distintos en tres sitios,
no hay ritmo — hay tres decisiones sueltas. Un valor, un token, y las excepciones con nombre.

### La alternancia: un remapeo de tokens, no un fondo suelto

```css
.section          { padding: 80px 0; }
.section--white   { background: var(--bg-white); }
.section--dark    { background: var(--primary); color: #fff; }
.section--dark .section-label { color: #ff6b6b; }
.section--dark .lead          { color: #b0c4ce; }
.section--white .lead         { color: var(--text-light); }
```
`bien/consultorpro.html:40-42`, `:54`, `:75-76`

**Lo importante es lo de abajo, no lo de arriba.** Cambiar el fondo de una sección es trivial;
**lo que hace que se vea bien es que la etiqueta, el texto secundario y el acento se redefinen para
esa variante**. Sin ese remapeo aparece el fallo clásico: el gris de textos secundarios, elegido
sobre blanco, se vuelve ilegible sobre el fondo oscuro. Es exactamente el defecto que el corpus
tiene medido en `bien/yessmassage-v7.html:40` (`--text-muted:#e8e8e8` sobre crema), y que allí se
parcheó con dos bloques de `!important` llamados «CONTRAST FIXES» (`:2931`, `:2990`) — la semilla de
GD-03.

> **Regla:** una variante de fondo es **un conjunto de tokens**, no un color. Si la variante existe,
> tiene que declarar su texto, su texto secundario, su borde y su acento. Si eso es mucho trabajo,
> es señal de que sobran variantes — dos suelen bastar.

---

## Asimetría con intención

**Lo que el corpus hace de verdad, dicho sin adornos:** de las **75** rejillas de dos columnas
medidas, **55 son `1fr 1fr`** (73 %) y solo 20 son asimétricas.

```bash
grep -rhoE "grid-template-columns: *[0-9.]+fr +[0-9.]+fr" bien/ mal/ | sort | uniq -c | sort -rn
```

Es decir: **la asimetría NO es un patrón medido de esta casa. Es criterio declarado**, y conviene
decirlo antes de venderla como doctrina.

**El criterio, y por qué lo declaramos igual:** dos columnas iguales reparten el peso visual a
partes iguales, así que **no dicen cuál importa**. Cuando una columna lleva el argumento y la otra
el apoyo, la proporción debería decirlo. La asimetría más usada del corpus es la suave —
**`1fr 1.2fr`**, en `bien/kalinayoga-v6.html:730` y `:1058`, `bien/consultorpro.html:244`,
`bien/elevaiti-v5.html:968` — y esa proporción es un buen punto de partida: se nota que hay
jerarquía sin que parezca un error de maquetación.

**Cuándo `1fr 1fr` es lo correcto**, que es a menudo: comparar dos cosas del mismo rango (dos
planes, antes/después, dos testimonios). Ahí la simetría **es** la información.

**El límite honesto:** no tenemos ninguna medida de que nuestras composiciones asimétricas
funcionen mejor que las simétricas. Lo único medido es que las usamos poco.

---

## Gastar la audacia en un solo sitio

Es la regla que ordena todas las anteriores, y no es nuestra: `frontend-design:59` — *«Spend your
boldness in one place. Let one element be the memorable thing, keep everything around it quiet and
disciplined, and cut any decoration that does not serve the brief»*, con el consejo de Chanel de
quitarse un accesorio antes de salir.

Aplicado a esta ficha, en una tabla que se puede usar como checklist:

| Página | El elemento memorable | Lo que se calla alrededor |
|---|---|---|
| `bien/kalinayoga-v6.html` | El display de tres líneas con la itálica (`:1373-1377`) | Rejilla de tarjetas sobria, acento por tarjeta de 3 px (`:553`) |
| `bien/yessmassage-v7.html` | Los blobs que respiran (`:521-545`) | Tipografía del sistema, sin fuente remota (`:45-47`) |
| `mal/attomo-digital.html` | El texto perfilado (`:282-284`) | …**y aquí falla**: además hay rejilla enmascarada, dos orbes, grano, ruido animado y marquesina |

**attomo es el contraejemplo útil**: visualmente es de lo mejor del corpus y acumula **cinco**
recursos de atmósfera a la vez. Es también el único marcado como `mal/`, aunque por otra razón
(`initGSAP()` definido en `:1441` con **una sola aparición** en todo el fichero, así que nunca se
llama). Las dos cosas caben en la misma lectura: **acumular recursos es lo que hace difícil ver que
falta el que importa.**

**La prueba operativa, y se hace en treinta segundos:** quita el recurso y mira. Si la página sigue
funcionando igual, ese recurso no estaba trabajando.

---

## Qué cambia por perfil (`perfiles.yaml`)

| | **`web-cliente`** | **`producto-panel`** |
|---|---|---|
| Rejilla enmascarada y orbes (T9) | Sí, en el hero | **No**, salvo en la pantalla de acceso |
| Filete por `gap` (T10) | Sí | **Sí** — es el que mejor viaja: las tablas y las tarjetas de métricas son su caso natural |
| Marca de agua tipográfica (T7) | Sí, una | **No.** En un panel, el texto grande que no es dato compite con el dato |
| Formas orgánicas (T19) | Solo en sectores blandos | **No** |
| Alternancia de fondos | Sí, dos variantes | Normalmente **una sola superficie**; la jerarquía la da la elevación, no el color de fondo |
| Dónde se gasta la audacia | El hero | **El shell y el estado vacío.** Son las dos pantallas que se ven siempre y las dos que nadie diseña |

**El corpus solo tiene una referencia de perfil `producto-panel`** (`bien/consultorpro.html`), y ni
siquiera es un panel: es una landing de consultoría con paleta compartida con material impreso. Así
que **la columna derecha de esta tabla es criterio, no evidencia.** Cuando haya un panel de verdad
en el corpus, se vuelve a escribir.

---

## Anti-patterns

- ❌ Rejilla de fondo a pantalla completa **sin `pointer-events:none`** → se come los clics.
- ❌ Rejilla con paso < 40 px o línea a opacidad > .05 → *moiré* al hacer scroll, y compite con el
  texto.
- ❌ Un orbe de `radial-gradient` sin parada `transparent` → se ve el borde del círculo.
- ❌ Bordes en cada celda en vez de `gap` sobre fondo teñido → juntas de 2 px, perímetro de 1 px, y
  una cascada de `:last-child` para taparlo (T10).
- ❌ Rejilla con `gap` y alguna celda **sin fondo opaco** → se ve el contenedor a través, y solo
  aparece con datos reales.
- ❌ Número fantasma **seleccionable** → al arrastrar el ratón sale un «03» y deja de ser gráfico.
- ❌ Número fantasma con un gris inventado en vez de un token de fondo o de borde (T7).
- ❌ Texto perfilado (`-webkit-text-stroke` + `color:transparent`) **sin `aria-hidden`** y sin el
  contenido en otro sitio legible → invisible donde no hay soporte, y leído donde no toca.
- ❌ Numerar secciones que no son una secuencia (`frontend-design:30`).
- ❌ Blobs animados **sin `prefers-reduced-motion`** → es GD-05, y ya lo incumplen dos referencias.
- ❌ Blobs con duraciones múltiplos entre sí → el fondo late.
- ❌ Formas orgánicas en un panel de datos o una consultoría → la forma dice una cosa y el contenido
  otra.
- ❌ Tres valores distintos de padding de sección en tres sitios → eso no es ritmo, son tres
  decisiones sueltas.
- ❌ Una variante de fondo que **solo** cambia el `background` → el texto secundario se vuelve
  ilegible y acaba parcheado con `!important` (GD-03, `bien/yessmassage-v7.html:2931`).
- ❌ Asimetría porque sí, sin que una columna lleve más peso que la otra → es una simetría fallida.
- ❌ Presentar la asimetría como patrón de casa → 73 % de nuestras rejillas de dos columnas son
  `1fr 1fr`; es criterio declarado.
- ❌ Acumular cinco recursos de atmósfera en la misma página (`mal/attomo-digital.html`).
- ❌ Copiar la columna `producto-panel` como si estuviera medida → hay **una** referencia de ese
  perfil en el corpus y no es un panel.

---

_Versión 1.0 · 2026-09-18 · Ola 2. Anclas verificadas con `sed -n`/`grep -n` el 2026-09-18. Los
conteos de rejillas y de padding salen de los comandos escritos en el propio documento, para que
cualquiera pueda repetirlos._
