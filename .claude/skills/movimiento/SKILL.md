---
name: "movimiento"
description: >-
  Usar cuando hay que decidir e implementar qué se mueve en una interfaz: 'la web está muerta',
  'añade animaciones', 'micro-interacciones', 'esto marea', 'reduced motion', '/movimiento'. NO usar
  para: la dirección de arte (direcciones-de-arte), gráficos (dataviz), la forma de una pantalla
  (disenar-pantalla), el baseline (visual-regression) ni puntuar lo construido (vera-art-director,
  /qa-loop).
user-invocable: true
metadata:
  version: 1.0.0
  author: tech-lead-template
  category: workflow
  updated: 2026-09-18
  verificado: 2026-09-18
---

# movimiento — la metáfora primero, el mecanismo después

## Principio

La doctrina de movimiento de esta casa eran **dos frases y seis penalizaciones**, y las seis son
topes de contención: *salto de opacidad > 0,3* · *micro-interacción > 500 ms* · *más de 3 secciones
a la vez* · *borde girando en < 4 s* · *brillo > 25 %* · *insignia pulsando > 1,05*. **Ninguna premia
nada.** Un sistema que solo sabe restar produce exactamente lo que produjo: páginas correctas y
quietas. Y el agente que sabía de esto se retiró, así que el hueco no era una opinión: no había
nadie.

Esta skill **no deroga** esas seis filas —siguen mandando al puntuar—. Contesta la otra pregunta,
que no la contestaba nadie: **qué se hace al diseñar.**

> **La regla que ordena todo lo demás:** antes de escribir una sola animación, termina la frase
> *«esta página se mueve como ___»*. Si no puedes terminarla, lo que pongas va a ser relleno. Es lo
> único del movimiento que no se puede copiar de un catálogo (`patterns/diseno/movimiento.md` §1).

## Filtro de existencia — por qué es una skill y no una sección de otra

`patterns/diseno/movimiento.md` ya tiene la doctrina entera, así que la pregunta es legítima. Los
tres criterios de `skill-authoring`:

| | |
|---|---|
| **(a) restricciones exigibles** | Sí: nombra la metáfora o para · nivel declarado aunque sea 0 · 3-6 efectos con nombre · `opacity:0` colgando de `body.js-ready` · reduced-motion en CSS **y** en JS · cierre con `comprobar_movimiento.py` en verde |
| **(b) estructura idéntica** | Sí, los siete pasos de abajo, en ese orden, cada vez |
| **(c) sin que el Usuario explique el caso** | Sí: con el perfil y la URL arranca; lo que falta se hereda del proyecto o se declara |

**Y la razón por la que no vive dentro de `direcciones-de-arte`:** porque hace falta **sin** rehacer
la dirección de arte. El caso más común no es un proyecto nuevo — es **un producto que ya existe y
al que hay que darle vida**, con su tipografía y su paleta ya decididas e intocables. Meterlo dentro
de la skill que rehace el mundo visual entero obligaría a rehacerlo para mover un botón.

**Regla de tres:** cada web de cliente (perfil `web-cliente`, nivel 1 por defecto) más cada vez que
alguien dice que algo «está muerto». Muy por encima de tres al trimestre.

**Criterio de retirada:** si a los tres meses tiene **0 invocaciones**, se retira el `SKILL.md` y se
conserva `comprobar_movimiento.py` enganchado a `/qa-loop` como gate. La doctrina se queda donde ya
está: `patterns/diseno/movimiento.md`.

## Cuándo activar

- El Usuario dice que la web está muerta, sosa, plana, o «le falta algo».
- Después de `direcciones-de-arte`: la dirección ganadora **nombró** la metáfora y hay que hacerla.
- Al montar una pantalla nueva en un proyecto con §4c de `design-system.md` ya rellena.
- **Cuando algo se mueve mal**: marea, se dispara tarde, o un bloque no aparece nunca.
- Al cerrar una wave con UI, como paso previo a `/qa-loop`.

Disparadores: 'la web está muerta', 'añade animaciones', 'anima el hero', 'micro-interacciones',
'que el logo respire', 'esto marea', 'reduced motion', 'nivel de movimiento', 'el reveal no se
dispara', '/movimiento'. Nombra la metáfora del sector, elige nivel 0/1/2 según el perfil, lista 3-6
efectos CON NOMBRE, escribe los tokens en §4c de design-system.md, implementa desde
templates/diseno/motor-reveal.html y cierra con evidencia medida: captura y comprobación de que el
contenido se ve con el JavaScript apagado. · NO usar para: la dirección de arte entera
(`direcciones-de-arte`, que nombra la metáfora); gráficos de datos (`dataviz`); la forma de una
pantalla (`disenar-pantalla`); comparar contra baseline (`visual-regression`, que corre con las
animaciones apagadas); ni puntuar movimiento ya construido (`vera-art-director`, `/qa-loop`,
`gate_diseno.py`).

## Contrato de entrada

| Necesito | Si no lo tengo |
|---|---|
| **El perfil** (`web-cliente` / `producto-panel`) | Se lee de §0b. **Si no está, pregunto**: decide el nivel por defecto y prohíbe tres técnicas enteras |
| **La metáfora del sector**, en una frase | Se lee de §0b o de `11-guia-marca.md`. **Si no existe, la propongo y la confirmo — no animo sin ella.** Es el paso 1, no un adorno |
| **El nivel** (0/1/2) | Se propone desde el perfil (§2) y se declara. **Un 0 decidido es una decisión; un hueco es un accidente** |
| **De dónde salen los tokens** | §4c de `.docs/core/design-system.md`. Si no hay, se crean ahí — **nunca una duración suelta en un componente** |
| **Una URL donde ver la página corriendo** | **Sin ella no hay cierre.** Se puede implementar, pero el paso 6 queda `no medido`, y eso se dice |

## Procedimiento

### 1. Nombrar la metáfora — antes de tocar nada

Termina la frase. Los tres casos reales del corpus, con el nombre del `@keyframes` como prueba de
que la metáfora llegó hasta el código:

| Sector | La metáfora | Cómo se hizo |
|---|---|---|
| Masaje | **respiración** | `@keyframes breathe`, escala 0,9→1,1→0,9 en 3 s · `logo-breathe` · `hero-breathe` |
| Yoga | **la planta que se mece** | `floatPlant`: `translateY` con ±2° de rotación, 8 s |
| Agencia llamada **DALE** | **la carretera** | Las líneas de una perspectiva SVG se dibujan desde el horizonte (`strokeDashoffset: 600 → 0`) y se desplazan al bajar |

El de DALE es el más instructivo: la metáfora no sale del sector sino **del nombre del cliente**
—«dale» → arrancar → carretera— y el mismo objeto sostiene el hero y el parallax.

**El contraejemplo está dentro del corpus:** `bien/elevaiti-v7.html:321` define un `@keyframes
float`. Se mueve. No dice nada del negocio. Un `float` sirve para cualquier página del mundo, y esa
es la definición operativa de relleno.

> ⚠️ **Límite honesto, dicho antes de exigirlo:** T18 está declarada como patrón con dos
> precedentes, y aun así **la mayoría de los nueve diseños buenos del corpus no nombra ninguna
> metáfora**. Es una aspiración medida en los mejores, no una descripción de lo normal.

### 2. Elegir el nivel — y escribirlo

| Nivel | Qué lleva | Coste | Cuándo |
|---|---|---|---|
| **0 · Responde** | Solo lo que contesta a una acción: hover, foco, abrir, confirmar. **Cero movimiento no pedido** | ~0, es CSS | **El default de `producto-panel`.** Cualquier cosa que se use ocho horas al día |
| **1 · Revela** | Nivel 0 + un reveal al entrar en pantalla + micro-interacciones + **una** metáfora ambiental | Bajo: `IntersectionObserver` + CSS, sin dependencias | **El default de `web-cliente`.** Cubre el 90 % |
| **2 · Premium** | Nivel 1 + timeline de entrada orquestada, parallax con `scrub`, revelado por palabras, cursor propio | Alto: GSAP + ScrollTrigger (~50 KB) y **sube el riesgo** | Portada de marca, agencia, lanzamiento. Cuando la página **es** el producto |

**La pregunta que decide:** ¿el movimiento es parte de lo que se vende, o decoración sobre lo que se
vende? Una agencia creativa vende su movimiento. Un panel de facturación, no.

> ⚠️ **El dial `movimiento:` de `perfiles.yaml` es un TECHO, no el default**, y conviene leerlo así
> para que no parezca que se contradice con esta tabla. `web-cliente` lleva `movimiento: 2` —«nivel
> premium **permitido** si la metáfora del sector lo pide»— y su default sigue siendo **1**;
> `producto-panel` lleva `movimiento: 1` como tope y su default es **0**
> (`patterns/diseno/movimiento.md` §2 y §9). Subir hasta el techo se decide y se escribe; no se
> hereda por estar permitido.

**El nivel 2 exige el nivel 0 hecho.** El único diseño roto del corpus compró nivel 2 sin pagar el
suelo, y hoy está desplegado y **no se ve**.

`producto-panel` **prohíbe** tres técnicas enteras, y no es estética: scroll suavizado (secuestra el
scroll del sistema, rompe `Ctrl+F` y el teclado), cursor propio, y botón magnético (un objetivo que
se mueve es más difícil de pulsar — choca con el *target size* de WCAG 2.2).

### 3. Los 3-6 efectos, con nombre

Cada uno con: **qué se mueve · qué lo dispara · cuánto dura**. Sin nombre no es movimiento, es
relleno — y el nombre acaba siendo el del `@keyframes`, que es como se comprueba después (§6).

Vocabulario medido, y su regla de lectura: **lo que responde a una persona es rápido; lo que ocurre
solo es lento.** Invertirlo es lo que hace que una página se sienta pesada al usarla y nerviosa al
mirarla.

| Qué | Duración | Curva | Escalonado |
|---|---|---|---|
| Hover / micro-interacción | **0,25-0,4 s** | la del sistema | — |
| Reveal al entrar | 0,7-0,9 s | `power3.out` / `cubic-bezier(.16,1,.3,1)` | — |
| Palabras de un titular | 0,75 s | `power4.out` | **0,06 s** |
| Tarjetas de una rejilla | 0,5-0,8 s | `power3.out` | **0,1-0,15 s** |
| Trazo que se dibuja | 2 s | `power2.out` | 0,08 s |
| Ambiente en bucle | 3-20 s | `ease-inout` o `linear` | — |
| Marquesina | 30 s | `linear` | — |

El escalonado tiene techo: **ocho tarjetas a 0,15 s** dejan la última entrando 1,2 s después de la
primera, y para entonces ya han bajado. Con rejillas grandes se escalona **por filas**.

### 4. Los tokens — el easing no se escribe a mano

Van a **§4c de `.docs/core/design-system.md`**, y de ahí al `@theme` o al `:root` del proyecto.
**Tres, no ocho**, si se arranca de cero:

```css
--ease-out:   cubic-bezier(.16, 1, .3, 1);    /* sale rápido y frena largo */
--ease-inout: cubic-bezier(.65, 0, .35, 1);
--dur-fast:   .35s;   /* hover, foco          */
--dur-base:   .7s;    /* abrir, cerrar        */
--dur-reveal: 1.2s;   /* entrada al bajar     */
```

> `cubic-bezier(.16,1,.3,1)` aparece en **dos diseños distintos** del corpus sin que se hablaran. Con
> diez ficheros de un solo equipo eso no es dominancia, pero es la coincidencia más fuerte que hay:
> es la curva que hace que un reveal parezca intencionado en vez de mecánico.

### 5. Implementar — se pega, no se reinventa

```bash
cat .claude/templates/diseno/motor-reveal.html     # el motor por defecto, con la regla dura dentro
cat .claude/templates/diseno/grano.html            # textura sin peticiones, si la dirección la pide
```

**La regla dura, y es la única que no se puede tocar:** el `opacity:0` cuelga de **`body.js-ready`**,
nunca del elemento.

```css
.reveal        { transition: opacity var(--dur-reveal) var(--ease-out), transform …; }
body.js-ready .reveal          { opacity:0; transform: translateY(28px); }   /* ← solo si hay JS */
body.js-ready .reveal.visible  { opacity:1; transform: none; }
```

Sin JS esa clase nunca se añade, la regla nunca aplica y **el contenido se ve, sin más**. La
animación es lo que se **añade** cuando hay JS, no lo que hay que rescatar cuando no lo hay.

⚠️ **Recordatorio, repetido a propósito porque es justo donde se deriva:** aunque el reveal te
parezca trivial, **no escribas `opacity:0` en el elemento**. Hay una página real, nuestra, publicada
y **invisible** por exactamente esto: declaraba `.reveal{opacity:0}` sin condición y definía
`initGSAP()` **sin llamarla nunca**. No la cazó ningún test, porque todas nuestras capturas se sacan
con JS activado — el instrumento no podía ver el fallo.

Y el motor, con los tres rasgos que dos diseños del corpus alcanzaron por separado: **umbral bajo**
(~0,1), **margen inferior negativo** (`0px 0px -60px 0px`) y **`unobserve` al primer disparo** —
re-animar al subir marea.

### 5b. `prefers-reduced-motion`: en CSS **y** en JS

El bloque de CSS **no basta** cuando el movimiento lo pone JavaScript: GSAP escribe estilos en
línea y un `transition-duration: 0.01ms` no detiene una timeline.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration:.01ms !important; transition-duration:.01ms !important; }
  .reveal { opacity:1 !important; transform:none !important; }   /* ← sin esta línea, invisible */
}
```
```js
const menosMovimiento = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (menosMovimiento) { /* salida temprana: no se registra nada en GSAP, no se monta el parallax */ }
```

**Fíjate en `.reveal{opacity:1!important}`:** sin ella, un `transition-duration` de 0,01 ms deja el
elemento en su estado inicial —invisible— instantáneamente. Apagar la animación sin reponer el
estado final es la forma más común de dejar la página en blanco a quien pidió menos movimiento.

### 6. Cerrar con evidencia — no hay DONE sin esto

```bash
cd <carpeta> && python3 -m http.server 8899 --bind 127.0.0.1 &
python3 .claude/skills/movimiento/comprobar_movimiento.py "http://127.0.0.1:8899/" --json=/tmp/mov.json
python3 .claude/scripts/screenshot.py "http://127.0.0.1:8899/" /tmp/mov.png 1440 900 3000
python3 .claude/scripts/screenshot.py "http://127.0.0.1:8899/" /tmp/mov-movil.png 390 844 3000
```

`comprobar_movimiento.py` mira las cinco cosas que **sí** se pueden medir sin juicio y devuelve
**0 sin hallazgos · 1 hay hallazgos · 2 NO SE PUDO MEDIR**. Un 2 no es «está bien»: es que no se
pudo mirar, y hay que arreglarlo antes de creerse nada.

| Comprueba | Regla |
|---|---|
| Caracteres visibles **con el JS apagado** | GD-01 / T11b |
| Bloques **con texto, en pantalla y en opacidad 0** con el JS corriendo | GD-01 — un reveal que no dispara |
| `prefers-reduced-motion` en CSS **y** en JS (lee los scripts servidos) | GD-05 |
| `cursor:none` global | GD-06 |
| `@keyframes` con nombre propio **frente a** genéricos (`float`, `fadeIn`, `pulse`…) | T18 |

**Se ha visto fallar, que es lo que lo convierte en gate** (medido el 2026-09-18 contra el corpus):

| | `dale-marketing-v4` | `attomo-digital` (roto a propósito) |
|---|---|---|
| reduced-motion | CSS ✅ · JS ✅ | CSS no medible · JS ❌ |
| `cursor:none` global | no | **sí** (GD-06) |
| Bloques mudos en pantalla | 0 | **8**, incluido `h2.reveal — "Soluciones que transforman"` |
| **Salida** | **0 · sin hallazgos** | **1 · tres hallazgos** |

### 7. Anotarlo donde lo lea la pantalla siguiente

§4c de `design-system.md`: el **nivel**, los **efectos con nombre** y los **tokens**. Más
`reviewed:` con la fecha. Si no queda escrito, la pantalla número once vuelve a discutir el reveal
que ya se acordó en la tercera.

## Salida

```
metafora:     «esta página se mueve como …»   | <propuesta y pendiente de confirmar>
nivel:        <0|1|2> · perfil <web-cliente|producto-panel>
efectos:      <n> con nombre — <nombre> · <nombre> · <nombre>
tokens:       §4c rellenada · <n> tokens (ease/dur)   | <ya existían>
implementado: <ficheros tocados>
comprobacion: exit=<0|1|2> · sin JS <n> car. · reduced-motion CSS=<> JS=<>
              · cursor:none=<> · keyframes propios=<n> genéricos=<n>
capturas:     /tmp/mov.png · /tmp/mov-movil.png · consola=<limpia>
hallazgos:    <ninguno | lista>
siguiente:    </qa-loop | pendiente de que el Usuario confirme la metáfora>
```

## Qué NO hace

| No hace | Lo hace |
|---|---|
| Elegir la dirección de arte entera | `direcciones-de-arte` — **nombra** la metáfora; esta la implementa |
| Decidir la identidad y la paleta | `marca` |
| Animar gráficos y visualizaciones | `dataviz` |
| Decidir la forma de una pantalla | `disenar-pantalla` |
| Comparar capturas contra baseline | `visual-regression` — y corre **con las animaciones apagadas**, a propósito |
| **Puntuar** el movimiento de algo construido | `vera-art-director` · `/qa-loop` · `scripts/gate_diseno.py` |

## Límites honestos

- **El movimiento casi no se puede auditar.** Todas las capturas del harness son **estáticas** y
  `visual-regression` corre con las animaciones apagadas para que el diff sea estable. Ningún gate
  nuestro puede ver si el movimiento es **bueno** — solo si está **roto**, que es lo que mide §6.
- **Lo que es juicio y no va a ser medible:** si la metáfora es la correcta, si el momento
  orquestado está donde toca, y si al quitar un reveal la página pierde algo. Eso lo contesta una
  persona, y su respuesta no es un número.
- **Hay un conflicto declarado con el skill oficial `frontend-design`**, y no se disuelve diciendo
  que los dos tienen razón. Él dice que *«fade-and-slide-up entrances on each section […] read as
  AI-generated»*, y **tiene razón en la CANTIDAD**: un momento orquestado por página. Nosotros
  mandamos en el **mecanismo** (mejora progresiva, easing largo), porque tenemos una página
  publicada e invisible por no hacerlo. Lo que salva un reveal de ser relleno es T18. Para
  `producto-panel`, su recomendación gana sin discusión y el default es nivel 0.
- **Y otro con la tabla de los auditores (A2)**, que penaliza micro-interacción > 500 ms: los
  reveals del corpus duran 0,7-0,9 s. La frontera: **micro-interacción ≤ 400 ms** (A2 aplica
  entero) · **reveal 0,7-0,9 s** (A2 no aplica) · **ambiente 3-30 s** (aplica A4). Excepción con
  nombre: **transformaciones de imagen al hover, hasta 0,8 s** — a 200 ms se siente brusco, a 700 ms
  se siente caro. Esto es **criterio escrito, no mecanismo**: el auditor sigue aplicando su número.
- **`comprobar_movimiento.py` está calibrado contra el corpus, no contra el mundo.** Su check de
  bloques mudos tuvo que acotarse al viewport y excluir lo oculto a propósito (`.hidden`,
  `aria-hidden`) porque la primera versión daba **60 en el diseño bueno y 25 en el roto** — no
  discriminaba. Tras acotarlo: **8 en el roto, 0 en tres buenos**.
- **Diez diseños de un equipo no son dominancia.** Puede ser simplemente nuestro gusto, y por eso
  nada de esto bloquea nada (precedente GAP-1 de `patterns/README.md` §1).

## Anti-patterns

- ❌ **Animar sin haber terminado la frase «esta página se mueve como ___»** → sale un `@keyframes
  float` que serviría para cualquier web del mundo, y eso es relleno.
- ❌ **`opacity:0` sin condición en el CSS** → si el JS no corre, no se ve nada. Cuelga siempre de
  `body.js-ready`.
- ❌ **Definir la función que arranca la animación y no llamarla** → pasó de verdad, está publicado, y
  ningún test nuestro lo cazaba.
- ❌ **Bloque de `prefers-reduced-motion` solo en CSS cuando el movimiento lo pone JavaScript** → la
  timeline sigue corriendo: escribe estilos en línea y se los salta.
- ❌ **Apagar la animación sin reponer el estado final** → `transition-duration:.01ms` deja el
  elemento invisible para siempre. Hace falta `.reveal{opacity:1!important}`.
- ❌ **Un reveal en cada sección más un hover en cada tarjeta** → es el default genérico y se
  reconoce a distancia. Un momento orquestado por página.
- ❌ **Sumar la timeline de entrada al reveal en el hero** → se paga el efecto dos veces y se ve.
- ❌ **Escalonar ocho tarjetas a 0,15 s** → 1,2 s hasta la última; escalona por filas.
- ❌ **Invertir los tiempos**: lento lo que responde a una persona, rápido lo que ocurre solo.
- ❌ **`cursor:none` global** → si el JS falla, no hay puntero en toda la página. Solo bajo
  `@media (hover:hover)`, y nunca en un panel.
- ❌ **Scroll suavizado o botón magnético en un `producto-panel`** → son herramientas de trabajo, no
  portadas.
- ❌ **Loader que retrasa el contenido «para que se vea la animación»** → es cobrarle tiempo al
  visitante por nuestro gusto. El corpus tiene dos, de 3,2 s y 1,6 s, y los dos son deuda.
- ❌ **Easing y duraciones sueltas por el CSS** en vez de tokens → salen ocho curvas distintas.
- ❌ **Nivel 2 sin el nivel 0 hecho** → es exactamente cómo se rompió el único diseño roto del corpus.
- ❌ **Dar el trabajo por cerrado sin correr `comprobar_movimiento.py`**, o tomar un **2** por un
  aprobado → un 2 es «no se pudo mirar».
- ❌ **Dejar §4c en blanco porque el nivel es 0** → un cero declarado es una decisión; un hueco es un
  accidente, y el default acaba siendo «apágalo», que es la causa medida de que los diseños salieran
  correctos y muertos.

## Ejemplos

### Usuario: «la web está muy muerta, ponle algo de vida»
TL: **no empieza por el CSS.** Pregunta el sector y el nombre del negocio, propone la metáfora en
una frase, la confirma, y de ahí salen 3-6 efectos con nombre. Después: nivel 1, tokens en §4c,
motor pegado de la plantilla, y cierre con `comprobar_movimiento.py` + captura a 1440 y 390.

### Usuario: «un bloque no aparece nunca al bajar»
TL: es el caso de §5. `comprobar_movimiento.py` lo nombra literalmente —«N bloques con texto están
en pantalla y en opacidad 0»— con la clase y el texto del bloque. Arreglo: colgar el estado inicial
de `body.js-ready` y comprobar que la función que lo dispara **se llama**.

### Usuario: «añade animaciones al panel de administración»
TL: lo dice y propone lo correcto: *«el perfil es `producto-panel`, así que el default es nivel 0:
solo lo que responde a una acción y dice qué cambió. Scroll suavizado, cursor propio y botón
magnético están prohibidos aquí — en una herramienta que se usa ocho horas al día estorban. Lo que
sí puedo hacer es que cada acción diga qué cambió: transición de estado en las filas, foco visible,
y el esqueleto de carga.»*

### Usuario: «que se mueva como en esta web que me gusta»
TL: no lo copia a ojo — lo **mide**. El paso 3 de `marca` (`medir_referencia.py`) sobre esa URL devuelve los nombres de
sus `@keyframes` y sus duraciones reales; si sus nombres son propios, ahí está su metáfora, y la
conversación pasa a ser cuál es **la nuestra**, no cómo copiar la suya.

## Related

- `patterns/diseno/movimiento.md` — **la doctrina entera**: §1 la metáfora · §2 los niveles · §3 el
  motor y T11b · §5 el vocabulario medido · §8 reduced-motion · §9 y §10 los dos conflictos
  declarados
- `patterns/diseno/perfiles.yaml` — qué nivel y qué técnicas prohíbe cada perfil
- `templates/diseno/motor-reveal.html` — el motor, con la regla dura dentro · `grano.html`
- `templates/core/design-system.md` §4c — lo que rellena el paso 7
- `skills/direcciones-de-arte` — **nombra** la metáfora; esta la implementa
- `skills/marca` paso 3 (`references-visual.md`) — mide el movimiento de una referencia (sus `@keyframes` reales)
- `resources/referencias-diseno/anti-patrones.yaml` — GD-01 · GD-02 · GD-05 · GD-06, las semillas
  que `comprobar_movimiento.py` comprueba, todas en `sombra`
- `agents/shared/calibration-v2.md` §3 (A1-A6) — las seis penalizaciones que siguen mandando al
  puntuar · `rules/qa-loop.md` · `vera-art-director`
- `rules/verification.md` — los tres veredictos del instrumento, de donde sale el exit 2
- `visual-regression` — corre **con las animaciones apagadas**: no juzga movimiento, y es correcto
- `review-animations` · `animation-performance` · `mobile-native` · `break-ui` (Emil Kowalski, vendorizadas
  y a mano, 3.66) — revisan **cómo** se ejecuta lo que esta skill decidió; si chocan, manda esta
