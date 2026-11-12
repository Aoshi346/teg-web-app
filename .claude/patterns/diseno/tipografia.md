# Tipografía — el titular que carga la personalidad, y los emparejamientos que la sostienen

> **Cuándo aplicar:** al elegir las familias de un proyecto (fase 1 de `rules/motores-de-diseno.md` Parte F,
> skill `marca`), al resolver el titular de una portada o de una sección hero
> (`disenar-pantalla`), y al revisar por qué un texto «se lee bien pero no dice nada».
>
> **NO aplicar:** para **dónde se declaran** los tokens de tipografía y qué comprueba el linter —
> eso es `patterns/stack/frontend-design-system.md` y manda él · para el **contenido** del texto
> (`skills/escribir-copy`, y la lista de palabras prohibidas vive en
> `templates/anti-ai-writing-style.md`) · para **contraste y foco** (`aitor-a11y-auditor`) · para
> tipografía de **informes del report-kit**, que va por `rules/html-output.md` §2 y usa fuentes del
> sistema.
>
> **Relacionado:** `patterns/diseno/README.md` (por qué esto no bloquea) ·
> `resources/referencias-diseno/` (la evidencia) · `composicion.md` (dónde va el titular) ·
> `textura-y-profundidad.md` (los tokens que rodean a estos) · `rules/html-output.md` §2 (la
> excepción de fuente para marca y bocetos) · el skill oficial `frontend-design` (§5, el conflicto).

---

## T1 · El titular display de tres líneas con una en itálica

**Qué es.** El titular de portada se parte en **tres líneas cortas** con saltos explícitos, y **una
de las tres** —la que lleva el núcleo semántico de la promesa— cambia de corte a **itálica** dentro
de la misma familia display.

```html
<h1 class="h-display hero-title">
  Encuentra<br>
  <span class="italic-line">tu calma</span><br>
  interior
</h1>
```

**Anclas.** `resources/referencias-diseno/bien/kalinayoga-v6.html:1373-1377` (el marcado) ·
`:326-329` (`.hero-title .italic-line{font-style:italic;color:var(--arena)}`) · `:55-59`
(`.h-display{font-size:clamp(3.5rem,9vw,8rem);line-height:.95;letter-spacing:-.02em}`).

**La variante entera**, que es la más limpia: no se acentúa una línea, **el display completo va en
itálica** y el contraste lo pone el peso, no el corte —
`bien/kalinayoga-v4.html:39-47`: `Cormorant Garamond`, `font-style: italic`, `font-weight: 300`,
`clamp(4rem, 10vw, 9rem)`, `line-height: 0.92`.

**Los tres números que hacen que funcione**, y sin ellos es un titular grande y ya está:

| Valor | Rango medido en el corpus | Por qué |
|---|---|---|
| `line-height` | **0.92 – 0.95** | Por debajo de 1 las tres líneas se leen como **un bloque**, que es la forma; a 1.4 se leen como tres frases sueltas |
| `letter-spacing` | **-0.02em** (los dos) | A tamaño display el tracking normal abre huecos; se cierra, y solo en display |
| `font-size` | `clamp()` de 3.5→8rem y de 4→9rem | El salto es lo que lo convierte en elemento visual y no en texto grande |

**Qué NO arregla.** Nada de contenido. Un titular de tres líneas con la del medio en itálica y sin
nada que decir sigue sin decir nada — y se nota más, porque la composición promete peso semántico
donde no lo hay. Si la línea itálica no es la que elegirías si solo pudieras decir dos palabras,
el titular está mal partido, no mal maquetado.

**Coste.** El salto de línea explícito **no se adapta solo**: a 390 px de ancho, tres líneas
pensadas para escritorio pueden salir seis. Se comprueba a 390 antes de darlo por bueno.

> ⚠️ Esta técnica **choca de frente** con el skill oficial `frontend-design`. El conflicto está
> resuelto por escrito en **§5**, y no a nuestro favor por defecto. Léelo antes de usarla.

---

## T2 · Emparejamientos por sector — y la regla de las dos familias

**La regla, en una frase:** un proyecto declara **dos familias con papeles distintos** —una
display, una de texto— y el contraste entre ellas es **visible a 3 metros**. Una sola familia es
una decisión legítima, pero es una decisión, no el punto de partida.

**Lo medido en el corpus** (`grep -n 'fonts.googleapis.com/css' bien/*.html mal/*.html`):

| Display | Texto | Sector · dirección de arte | Ancla |
|---|---|---|---|
| **DM Serif Display** | DM Sans | bienestar · yoga — *Boho Chic Mediterráneo* | `bien/kalinayoga-v6.html:9` |
| **Cormorant Garamond** | Montserrat | bienestar · yoga — *Luxury Editorial* | `bien/kalinayoga-v4.html:9` |
| **Playfair Display** | Lato | agencia IA B2B — *Premium Minimal* | `bien/elevaiti-v2.html:10` |
| **Space Grotesk** | Inter | agencia IA B2B — *Minimal* | `bien/elevaiti-v53.html:11` |
| **Space Grotesk** | Inter | agencia de marketing — *carretera* | `bien/dale-marketing-v4/index.html:11` |
| **Sora** | Inter | agencia IA B2B — *Interactive Showcase* | `bien/elevaiti-v7.html:9` |
| **Syne** | DM Sans | agencia digital — *Dark editorial* | `mal/attomo-digital.html:12` |
| Georgia *(sistema)* | Segoe UI *(sistema)* | bienestar · masaje — *Zen* | `bien/yessmassage-v7.html:46-48` |

**Lo que dice de verdad esta tabla**, y es más útil que las parejas concretas:

- **El sector manda sobre la familia.** Los cuatro proyectos de bienestar llevan **serif** —
  humanista o editorial—; los cinco de agencia/tecnología llevan **grotesca de carácter** (Space
  Grotesk, Sora, Syne) y nunca una serif de lujo. No es casualidad: es lo que
  `frontend-design:13` llama *«el sector, sus materiales y su vernáculo son de donde salen las
  decisiones visuales distintivas»*.
- **La display es la que se elige; la de texto casi siempre es la neutra.** Inter aparece como
  familia de texto en cuatro de las nueve. Eso está bien: el trabajo lo hace la display.
- **No hay tres familias en ningún fichero del corpus.** Coincide con `frontend-design:19`:
  *«use one family or two, and if two, make them clearly distinct»*.

### «Inter nunca va sola» — con su contraejemplo, que está dentro del corpus

**En perfil `web-cliente`: 9 de 9 declaran dos familias con papeles distintos.** Incluido
yessmassage, que no carga ninguna fuente remota y lo resuelve con dos pilas del sistema
(`bien/yessmassage-v7.html:46-48`: `--font-serif`/`--font-display` sobre Georgia, `--font-sans`
sobre Segoe UI).

**El único fichero del corpus con una sola familia es el único de perfil `producto-panel`:**
`bien/consultorpro.html:8` carga solo `Inter`, y `:26` la declara sobre la pila del sistema. **Y es
correcto.** En un panel, la tipografía no tiene que cargar la personalidad de la marca: tiene que
desaparecer para que se lea el dato. Ahí una sola neutra bien escalada es la decisión buena, y
meterle una display editorial es decoración que estorba.

> **Regla operativa:** en `web-cliente`, si tu propuesta es «Inter para todo», no has elegido
> tipografía — has aceptado el valor por defecto. En `producto-panel`, una sola neutra es la
> respuesta esperada y hay que justificar lo contrario.

**Límite honesto:** estas ocho parejas son **nuestro gusto medido en nuestro corpus**, no un
catálogo de lo que funciona. Copiar una fila porque el sector coincide es exactamente la
«plantilla» que `frontend-design:45` avisa de no aplicar: *«donde el brief deja un eje libre, no
gastes esa libertad en uno de estos valores por defecto»*. La tabla sirve para ver **qué clase de
contraste** ha funcionado en cada sector, no para elegir sin mirar el brief.

---

## T3 · Escala fluida con `clamp()` y micro-etiquetas con tracking abierto

### La escala fluida

Todo el corpus escala los titulares con `clamp(mínimo, vw, máximo)` y **ningún fichero usa
media queries para el tamaño del display**. Los dos extremos medidos:

```css
.h-display   { font-size: clamp(3.5rem, 9vw,  8rem); }  /* bien/kalinayoga-v6.html:56 */
.editorial-h1{ font-size: clamp(4rem,  10vw,  9rem); }  /* bien/kalinayoga-v4.html:43 */
.section-title{font-size: clamp(28px, 3.5vw, 44px); }   /* bien/elevaiti-v53.html:89 */
```

**El patrón, no los números:** el **ratio** entre mínimo y máximo es de ~2,3× en el display y de
~1,6× en los títulos de sección. Un display que solo crece un 20 % entre móvil y escritorio no está
escalando: está siendo tímido en los dos sitios a la vez.

### Las micro-etiquetas

El contrapunto del display es una etiqueta diminuta con el tracking muy abierto:

```css
.section-label{font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase}
```
`bien/elevaiti-v53.html:88`

**Rango medido de tracking** (`grep -rhoE "letter-spacing: *[0-9.]+em"`): **de 0.2em a 0.28em** en
las etiquetas, y **negativo (-0.02em / -0.03em) en el display**. Los valores intermedios (.05–.15em)
son para texto normal y no son micro-etiquetas. Anclas: `bien/kalinayoga-v4.html:75` (0.25em) ·
`bien/kalinayoga-v6.html:71` · `bien/elevaiti-v2.html:145` (0.2em).

> La técnica es **la inversión**: el elemento grande cierra el tracking, el pequeño lo abre. Un
> proyecto donde ambos llevan el tracking por defecto no tiene jerarquía tipográfica, tiene dos
> tamaños.

⚠️ **Y aquí está el segundo choque con `frontend-design:27`** (*«Using all caps for labels»*) y con
su cluster 5 (`:43`). Resuelto en §5.

---

## T4 · El eyebrow con filete, y la sección numerada

**El eyebrow con filete.** Una línea corta centrada entre dos filetes de 1 px que se estiran a
ambos lados, hecha con `::before`/`::after` y `flex:1`:

```css
.ornament { display:flex; align-items:center; gap:16px; font-family:'Cormorant Garamond',serif; }
.ornament::before, .ornament::after { content:''; flex:1; height:1px; background:var(--gold-light); }
```
`bien/kalinayoga-v4.html:98-111`

Es **mejor** que el eyebrow en versalitas suelto por una razón concreta: el filete **ocupa el ancho
sobrante**, así que la etiqueta queda medida por la columna en vez de flotando. Y no necesita
mayúsculas para señalarse.

**La sección numerada.** `bien/consultorpro.html:1679`:
`<div class="section-label">07 — La Oferta</div>`

**Solo si el contenido es de verdad una secuencia.** Es literal de `frontend-design:30`: *«muchos
diseños genéricos usan marcadores numerados (01/02/03), pero eso solo es apropiado si el contenido
realmente es una secuencia»*. Numerar siete secciones de una landing que se pueden leer en
cualquier orden es cromo, no información. En consultorpro funciona porque la página **es** un
recorrido de venta con orden; en un panel de métricas sería ruido.

---

## Cómo se escribe bien un `font-family` — el fallo que no avisa

**El `;` dentro del valor corta la declaración y el resto se pierde en silencio.** Es la semilla
**GD-10** de `resources/referencias-diseno/anti-patrones.yaml`, marcada ahí como *«determinista y
con falso positivo cero»*:

```css
font-family:'Space Grotesk',system-ui;sans-serif;   /* ❌ el navegador lee hasta system-ui */
font-family:'Space Grotesk',system-ui,sans-serif;   /* ✅ */
```

**Y el primo del mismo fallo, dentro de una referencia marcada como buena** —
`bien/yessmassage-v7.html:46-48`:

```css
--font-serif:   'Georgia','Palatino Linotype','Book Antiqua',serif,Georgia,serif;
--font-display: 'Georgia','Times New Roman','Palatino',serif,Georgia,serif;
--font-sans:    'Segoe UI','Helvetica Neue',Arial,sans-serif,system-ui,sans-serif;
```

El genérico (`serif`, `sans-serif`) **va el último y va una sola vez**: lo que viene detrás es
inalcanzable. No rompe nada visible, y por eso lleva meses ahí — es exactamente la clase de defecto
que un corpus sin columna de defectos convierte en doctrina.

**Tres reglas y ya:** comas entre familias y `;` solo al final · el genérico una vez y al final ·
los nombres con espacios entre comillas.

---

## Medida de línea

`frontend-design:23` fija el criterio: **menos de 80 caracteres**, las serif admiten algo más, y el
texto serif pide algo más de interlineado que el sans.

Lo que el corpus hace, que es coherente y más fácil de aplicar: **acotar el ancho del párrafo en
píxeles**, no contar caracteres.

| Ancla | Valor |
|---|---|
| `bien/kalinayoga-v6.html:331-332` | `.hero-subtitle{max-width:520px}` |
| `bien/elevaiti-v53.html:90` | `.section-sub{...line-height:1.7;max-width:560px}` |
| `mal/attomo-digital.html:286-290` | `.hero-sub{...max-width:520px;line-height:1.7}` |

**Rango de casa: 520–560 px con `line-height` 1.6–1.7.** Un párrafo que hereda el ancho del
contenedor en una pantalla de 1440 px sale a más de 100 caracteres por línea y se lee mal aunque
todo lo demás esté bien.

---

## La excepción de fuente para marca y bocetos

`rules/html-output.md` §2 manda tipografía **del sistema** en el HTML que genera el harness, porque
sus informes tienen que abrir sin red. **La excepción, acotada y escrita allí:** `brand.html` de la
skill `marca` y los bocetos de `disenar-pantalla` **sí** pueden cargar la tipografía real — su
trabajo es precisamente enseñar cómo se va a ver.

Dos condiciones, y son de la propia rule: **fallback declarado siempre** (sin red se sigue
leyendo) y **aviso en la página** de que esa fuente es de la marca. Todo lo demás —report-kit,
dashboards, informes— sigue con fuentes del sistema.

---

## 5. El conflicto con `frontend-design`, resuelto por escrito

El skill oficial de Anthropic `frontend-design` lista como **señales de página generada**:

| Línea | Lo que dice | Choca con |
|---|---|---|
| `:26` | *«Accenting just a single word or phrase in a headline, like putting one word in italic/bold or a different color»* | **T1** |
| `:27` | *«Using all caps for labels»* | **T3** (micro-etiquetas) |
| `:28` | *«Adding unnecessary typographic labels above content»* | **T4** (eyebrow) |
| `:43` | cluster 5 — *«template chrome that appears whatever the subject: a tracked-out ALL-CAPS eyebrow label above every heading»* | **T3 + T4** |

**No lo escondemos y no lo contradecimos.** Las cuatro observaciones son correctas, y nuestro T1
cae dentro de `:26` sin trampa: `tu calma` **es** una frase dentro de un titular, puesta en
itálica.

### La diferencia real, que está en la propia línea 43

La palabra que hace el trabajo es **`whatever the subject`**. Lo que `frontend-design` describe es
**cromo de plantilla**: un adorno que aparece *sea cual sea el tema*, porque es lo que se pone
siempre. Y el propio skill lo dice explícitamente dos líneas después (`:45`): *«todos estos rasgos
son legítimos para algún brief, pero son valores por defecto en vez de decisiones»*.

Nuestro T1, cuando está bien hecho, no es un adorno:

- La línea itálica **carga el núcleo semántico** («Encuentra *tu calma* interior»), así que la
  tipografía está haciendo trabajo de significado, no de decoración.
- Es **una línea de tres**, dentro de un display partido a propósito, no una palabra suelta a
  color dentro de un párrafo-titular.
- Cambia de **corte dentro de la misma familia** (la itálica de DM Serif Display), no de familia ni
  de color de acento.

Y cuando está mal hecho —la itálica cae en la palabra que sobra, o el eyebrow aparece encima de
las once secciones— **es exactamente lo que el skill describe**, y hay que llamarlo por su nombre.

### La regla operativa, que es lo único medible de esta sección

> **Como mucho 2 rasgos de los 5 clusters de `frontend-design:39-43` por página, y cada uno
> justificado en una línea escrita en la ficha de la dirección de arte.**

- Se cuenta por **página**, no por componente.
- «Justificado» significa una frase que solo valga para **este** brief. *«Queda elegante»* no
  cuenta; *«el eyebrow con filete separa las seis fases del método, que sí son una secuencia»*, sí.
- Si no puedes escribir la línea, el rasgo sobra. Es la misma prueba que el propio skill propone
  en `:53`: pásale el brief a otra ejecución y mira si llegas al mismo sitio.
- Va en la misma dirección que `frontend-design:59` (*«spend your boldness in one place»*), que es
  además el eje de `composicion.md`.

### Y quién manda si seguimos en desacuerdo

> **Manda `frontend-design`** en todo lo que sea *«¿esto parece hecho por IA?»*.

El motivo no es jerárquico, es de muestra: está calibrado contra un conjunto muchísimo mayor que
nuestros diez diseños de un solo equipo, y nuestro propio corpus lo admite — `INDEX.json` anota
sobre `elevaiti-v5` que su *«paleta cian/púrpura … es de los clusters de "look de IA" que lista
frontend-design»*, en una entrada marcada como buena.

**Nosotros mandamos** en lo específico de esta casa que aquel skill no puede saber: qué
emparejamiento ha funcionado en qué sector nuestro, qué valores concretos de `line-height` y
tracking usamos, y qué defectos conocidos arrastran nuestras referencias.

---

## Anti-patterns

- ❌ Poner la itálica en una palabra **decorativa** del titular → eso es literalmente
  `frontend-design:26`, y sin núcleo semántico T1 no se sostiene.
- ❌ Un titular de tres líneas con `line-height: 1.4` → se leen como tres frases sueltas; el bloque
  es la forma (0.92–0.95).
- ❌ Tracking por defecto en el display **y** en la etiqueta → no hay jerarquía, hay dos tamaños.
- ❌ Eyebrow en versalitas **encima de cada sección** → cromo de plantilla (`frontend-design:43`),
  y ya van más de 2 rasgos.
- ❌ Numerar secciones que **no son una secuencia** (`frontend-design:30`).
- ❌ Tres familias tipográficas → ninguna de las 10 referencias lo hace, y `frontend-design:19` lo
  desaconseja.
- ❌ «Inter para todo» en una web de cliente → no es una elección, es el valor por defecto (T2).
- ❌ Meter una display editorial en un panel → ahí la tipografía debe desaparecer (T2, contraejemplo
  `consultorpro`).
- ❌ Un `;` dentro del valor de `font-family` → corta la declaración **en silencio** (GD-10).
- ❌ Repetir el genérico (`serif`, `sans-serif`) en medio de la pila → lo que va detrás es
  inalcanzable (`bien/yessmassage-v7.html:46-48`).
- ❌ Párrafos que heredan el ancho del contenedor → 100+ caracteres por línea (520–560 px).
- ❌ Copiar una fila de la tabla T2 porque el sector coincide, sin leer el brief → es la plantilla
  que `frontend-design:45` avisa de no aplicar.
- ❌ Cargar fuente remota en un informe del report-kit → rompe el offline; la excepción es solo
  para marca y bocetos.
- ❌ Dar por bueno un display partido en tres **sin verlo a 390 px**.

---

_Versión 1.0 · 2026-09-18 · Ola 2. Todas las anclas verificadas con `sed -n`/`grep -n` contra
`resources/referencias-diseno/` el 2026-09-18. El §5 nace de una contradicción real entre este
canon y el skill oficial `frontend-design`, y se resuelve a favor del skill en lo suyo._
