# Movimiento — la metáfora primero, el mecanismo después

> **Cuándo aplicar:** al decidir **qué se mueve en una pantalla y por qué**: el hero de una web de
> cliente, el reveal al bajar, la micro-interacción de un botón, el ambiente de fondo, o cuando hay
> que decidir si esta página merece GSAP o le sobra. Cubre la capa que va **antes** del código:
> qué metáfora expresa el movimiento, qué nivel se compra, qué motor se usa y qué se apaga cuando
> alguien pide que se apague.
>
> **NO aplicar:** para el **tratamiento de la foto** que ese movimiento anima (`imagen.md`) · para
> el **orden de los bloques** de la página (`estructura-de-pagina.md`) · para las **formas** que se
> mueven —blobs, marquesinas, rejillas, grano— que son composición y textura y viven en
> `composicion.md` y `textura-y-profundidad.md` · para la **animación de una demo de producto**,
> que tiene requisitos propios de accesibilidad en `demo-de-producto.md` · para **puntuar** el
> movimiento de algo ya construido, que es `agents/shared/calibration-v2.md` §3 y `rules/qa-loop.md`.
>
> **Relacionado:** `catalogo-diseno.yaml` (T5b · T11 · T11b · T12-T18 · T23 — el id, su estado y sus
> precedentes verificados) · `resources/referencias-diseno/` (el corpus y su `INDEX.json`) ·
> `resources/referencias-diseno/anti-patrones.yaml` (GD-01 · GD-02 · GD-05 · GD-06) ·
> `patterns/stack/frontend-design-system.md` §tokens (dónde se declaran `--dur-*` y `--ease-*`) ·
> `catalogo-direcciones.md` (la metáfora nace ahí, no aquí) · `rules/qa-loop.md`.

---

## 0. Por qué existe este documento

Medido el 2026-09-18 sobre `.claude/`: la doctrina de movimiento de esta casa eran **dos frases**
—«solo se anima `transform` y `opacity`» y «apágalo con `prefers-reduced-motion`»— y **seis
penalizaciones**. Las seis filas de animación de la tabla compartida de los auditores
(`agents/shared/calibration-v2.md:76-81`) son **todas topes de contención**:

| | Qué castiga | Penalización |
|---|---|---|
| A1 | salto de opacidad al hover > 0,3 | −0,5 |
| A2 | micro-interacción > 500 ms · > 1000 ms | −0,5 · −1,0 |
| A3 | más de 3 secciones animándose a la vez | −1,0 |
| A4 | borde degradado girando en < 4 s | −1,0 |
| A5 | barrido de brillo con opacidad > 25 % | −0,5 |
| A6 | insignia de urgencia pulsando > 1,05 | −0,5 |

**Ninguna premia nada.** Un sistema que solo sabe restar produce exactamente lo que produjo: páginas
correctas y quietas. Y el agente que sabía de esto —`especialista-animaciones`— se retiró, así que
el hueco no era una opinión: no había nadie.

Esto no deroga esas seis filas. Las seis siguen mandando al **puntuar**. Este documento dice qué se
hace al **diseñar**, que es otra pregunta y no la contestaba nadie.

---

## 1. La metáfora del sector — se nombra antes de animar nada (T18)

Es lo primero porque es lo único que de verdad separa una página de esta casa de una generada. Todo
lo demás —el easing, la duración, el `IntersectionObserver`— se puede copiar de un catálogo. Esto no.

**La regla, en una frase:** *antes de escribir una sola animación, escribe la frase «esta página se
mueve como ___».* Si no puedes terminarla, el movimiento que pongas va a ser relleno.

Los dos casos del corpus, con el nombre del `@keyframes` como prueba:

| Sector | La metáfora | Cómo se hizo | Dónde |
|---|---|---|---|
| Masaje | **respiración** | Un `@keyframes` llamado `breathe` que escala 0,9→1,1→0,9 en 3 s | `resources/referencias-diseno/bien/yessmassage-v7.html:228` |
| Yoga | **la planta que se mece** | `floatPlant`: `translateY(-50%)→(-52%)` con ±2° de rotación | `resources/referencias-diseno/bien/kalinayoga-v6.html:285` |
| Agencia llamada **DALE** | **la carretera** | Las líneas de una perspectiva en SVG se dibujan desde el horizonte con `strokeDashoffset: 600 → 0` | `resources/referencias-diseno/bien/dale-marketing-v4/script.js:178-181` |

El caso de DALE es el más instructivo porque la metáfora no sale del sector sino **del nombre del
cliente**: «dale» → arrancar → carretera. Y no se queda en una ilustración: la carretera **se
dibuja** al entrar (`script.js:178`) y **se desplaza con el scroll** (`script.js:509-511`). El mismo
objeto sostiene el hero y el parallax.

**El contraejemplo está dentro del corpus, y es el que enseña la diferencia:**
`resources/referencias-diseno/bien/elevaiti-v7.html:321` define un `@keyframes float` genérico. Se
mueve. No dice nada del negocio. Un `float` sirve para cualquier página del mundo, y eso es
justamente el problema — es la definición operativa de relleno.

**Cómo se elige la metáfora.** No aquí: en la ficha de la dirección de arte
(`catalogo-direcciones.md`), que es donde ya están la tipografía, la temperatura de la paleta y el
tratamiento de imagen. Una metáfora de movimiento que no case con esas tres no es una metáfora, es
un efecto suelto.

> ⚠️ **Límite honesto:** T18 está declarada como **patrón** con dos precedentes
> (`catalogo-diseno.yaml`), y aun así el corpus tiene nueve diseños buenos de los que **la mayoría
> no nombra ninguna metáfora**. Esto es una aspiración medida en los mejores, no una descripción de
> lo normal. Se escribe como regla porque es la palanca, no porque ya se cumpla.

---

## 2. Los tres niveles — y lo que cuesta cada uno

El nivel se **elige y se escribe** al arrancar la pantalla, no emerge. Subir de nivel a mitad es
como acaban las páginas con efectos sueltos que no se hablan entre sí.

| Nivel | Qué lleva | Coste real | Cuándo |
|---|---|---|---|
| **0 · Responde** | Solo lo que contesta a una acción de la persona: hover, foco, abrir, confirmar. Cero movimiento no pedido | ~0. Es CSS | Paneles, herramientas internas, cualquier cosa que se use ocho horas al día |
| **1 · Revela** | Nivel 0 + un reveal al entrar en pantalla (§3) + micro-interacciones (§6) + **una** metáfora ambiental | Bajo: `IntersectionObserver` + transiciones CSS. Sin dependencias | **El default de una web de cliente.** Cubre el 90 % de lo que hacemos |
| **2 · Premium** | Nivel 1 + timeline de entrada orquestada, parallax con `scrub`, revelado por palabras, cursor propio (§7) | Alto: GSAP + ScrollTrigger (~50 KB), y **sube el riesgo** — el único diseño roto del corpus está roto por esta vía | Portada de marca, agencia, lanzamiento. Cuando la página **es** el producto |

**La pregunta que decide:** ¿el movimiento es parte de lo que se vende, o es decoración sobre lo que
se vende? Una agencia creativa vende su movimiento. Un panel de facturación no.

> **El nivel 2 exige el nivel 0 hecho.** `mal/attomo-digital.html` es de lo mejor del corpus
> visualmente y compró nivel 2 sin pagar el suelo: hoy está desplegado y **no se ve** (§3.2).

---

## 3. El motor por defecto (T11) y la regla que lo sostiene (T11b)

### 3.1 El motor: `IntersectionObserver` + transición CSS larga

**Dos diseños distintos del corpus llegaron a la misma forma sin hablarse**, y por eso esto es el
default y no una preferencia:

| | Umbral | Margen | ¿Deja de observar al disparar? |
|---|---|---|---|
| `bien/elevaiti-v53.html:558-561` | `threshold: .1` | `0px 0px -60px 0px` | **sí** (`fo.unobserve`) |
| `bien/elevaiti-v2.html:2519-2528` | `threshold: 0.12` | `0px 0px -40px 0px` | **sí** (`revealObserver.unobserve`) |

Los tres rasgos que comparten y que hay que copiar: **umbral bajo** (~0,1: dispara en cuanto asoma),
**margen inferior negativo** (espera a que el bloque entre de verdad, no a que roce el borde) y
**`unobserve` al primer disparo** (la animación ocurre una vez; re-animar al subir marea).

El hero es la excepción y también está resuelta igual: no espera al observador, se revela solo, en
cascada — `bien/elevaiti-v53.html:564` recorre `.hero .fade-up` con `setTimeout(…, i*120)`.

### 3.2 La regla dura: ningún contenido depende del JS para ser visible

**El patrón entero, transcrito del corpus.** Son cuatro líneas y hay que leer el orden:

```css
/* resources/referencias-diseno/bien/elevaiti-v53.html:92-95 */
.fade-up{transition:opacity .6s var(--ease),transform .6s var(--ease)}
body.js-ready .fade-up{opacity:0;transform:translateY(28px)}
body.js-ready .fade-up.visible{opacity:1;transform:translateY(0)}
```

```js
// resources/referencias-diseno/bien/elevaiti-v53.html:526-527
// Progressive enhancement
document.body.classList.add('js-ready');
```

**Lo que hace que funcione: el `opacity:0` cuelga de `body.js-ready`.** Sin JS, esa clase nunca se
añade, la regla nunca aplica y **el contenido se ve, sin más**. La animación es lo que se añade
cuando hay JS, no lo que hay que rescatar cuando no lo hay.

**El contraejemplo es real, es nuestro, y está publicado así.** En
`resources/referencias-diseno/mal/attomo-digital.html`:

- `:1006` declara `.reveal { opacity: 0; transform: translateY(40px); }` — **sin ninguna condición**.
- `:1441` define `async function initGSAP() {` … y esa es **su única aparición en todo el fichero**:
  ```bash
  grep -n "initGSAP" resources/referencias-diseno/mal/attomo-digital.html   # → una sola línea: 1441
  ```

Se define y no se llama nunca. Resultado: todo lo que lleva `.reveal` se queda invisible, y la
página está desplegada así. No la cazó ningún test nuestro — todas nuestras capturas se sacan con
JS activado, así que el instrumento no podía ver el fallo (`rules/verification.md` §el instrumento
que no puede medir). Es la semilla de **GD-01** y la razón de que T11b sea `regla` y no `anécdota`
pese a tener un solo precedente.

**Se comprueba en un comando**, y esto sí es barato:

```bash
# El texto visible con el JS apagado. Si cae a cero, el contenido depende del JS.
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,args=['--no-sandbox'])
    pg=b.new_context(java_script_enabled=False).new_page()
    pg.goto('URL',wait_until='load'); print(len(pg.inner_text('body'))); b.close()"
```

---

## 4. Tokens de movimiento (T5b) — el easing no se escribe a mano

Las duraciones y las curvas son **tokens del sistema de diseño**, igual que los colores: se declaran
una vez y los componentes las consumen. Dónde viven y cómo se declaran lo manda
`patterns/stack/frontend-design-system.md` §4 (documento fundacional en `.docs/core/design-system.md`,
valores en el bloque `@theme` de `src/app.css`). Aquí solo va **qué tokens** y con qué valores.

El juego más completo del corpus, copiado literal:

```css
/* resources/referencias-diseno/bien/yessmassage-v7.html:75-80 */
--ease-out:   cubic-bezier(0.16, 1, 0.3, 1);
--ease-inout: cubic-bezier(0.65, 0, 0.35, 1);
--ease-zen:   cubic-bezier(0.25, 0.46, 0.45, 0.94);
--dur-slow:   1.2s;
--dur-med:    0.7s;
--dur-fast:   0.35s;
```

Y el mínimo viable, que cabe en una línea y sostiene una página entera:

```css
/* resources/referencias-diseno/bien/elevaiti-v53.html:22 */
--ease:cubic-bezier(0.4,0,0.2,1);--t:0.28s;
```

> **El dato que más pesa de este apartado:** `cubic-bezier(.16,1,.3,1)` aparece en **dos diseños
> distintos** del corpus (`catalogo-diseno.yaml` T5b). Con diez ficheros de un solo equipo eso no es
> dominancia —y el corpus lo dice de sí mismo—, pero es la coincidencia más fuerte que hay aquí: es
> la curva que sale rápido y frena largo, y es la que hace que un reveal parezca intencionado en vez
> de mecánico.

**Tres tokens, no seis**, si el proyecto arranca de cero: uno de salida (`--ease-out`), uno
simétrico (`--ease-inout`) y tres duraciones. Cuando nadie lo decide salen ocho, que es el mismo
fallo que con las sombras y los radios.

---

## 5. El vocabulario medido — qué duración lleva cada cosa

Contado sobre los dos ficheros del corpus que usan GSAP
(`bien/dale-marketing-v4/script.js` y `mal/attomo-digital.html`):

```bash
grep -rhoE "ease: *'[a-zA-Z0-9.()]+'" bien/dale-marketing-v4/script.js mal/attomo-digital.html \
  | sort | uniq -c | sort -rn
#  11 power3.out · 6 power2.out · 5 none · 3 power2.inOut · 2 power1.out
#   1 sine.inOut · 1 power4.out · 1 back.out(2) · 1 back.out(1.4)
```

| Qué | Duración | Curva | Escalonado | Evidencia |
|---|---|---|---|---|
| **Reveal al entrar** | 0,7-0,9 s | `power3.out` | — | `dale/script.js:199-205` (0.8 · power3.out) · `attomo:1468-1469` (.9 · power3.out) |
| **Palabras de un titular** | 0,75 s | `power4.out` | **0,06 s** | `dale/script.js:166-170` |
| **Tarjetas de una rejilla** | 0,5-0,8 s | `power3.out` | **0,1-0,15 s** | `dale/script.js` (staggers medidos: .06 · .08 ×2 · .1 ×2 · .12 · .15) |
| **Hover / micro-interacción** | 0,25-0,4 s | la curva por defecto del sistema | — | `elevaiti-v53.html:22` (`--t:0.28s`) · `kalinayoga-v6.html:556` (0.4s) |
| **Trazo que se dibuja** | 2 s | `power2.out` | 0,08 s | `dale/script.js:178-181` |
| **Ambiente en bucle** | 3-20 s | `ease-inout` o `linear` | — | `yessmassage:228` (breathe 3s) · `:527,535` (blob-morph 16s y 20s) |
| **Marquesina** | 30 s | `linear` | — | `elevaiti-v2.html:599` (`ticker 30s linear infinite`) — la técnica es T20, y vive en `composicion.md` |

**La regla de lectura de esta tabla:** lo que **responde a una persona** es rápido (0,25-0,4 s) y lo
que **ocurre solo** es lento (0,7 s arriba). Invertirlo es lo que hace que una página se sienta
pesada al usarla y nerviosa al mirarla.

**El escalonado tiene un techo práctico:** 0,06 s entre palabras y 0,1-0,15 s entre tarjetas. Con
ocho tarjetas a 0,15 s el último elemento entra 1,2 s después del primero, y para entonces quien
mira ya ha bajado. Si la rejilla es grande, se escalona **por filas**, no por elemento.

---

## 6. Micro-interacciones (T17) — lo que responde a una persona

Es el nivel 0 y es lo que nunca se apaga: el movimiento que contesta a una acción **muestra qué
cambió**, así que es información, no decoración. Lo dice el skill oficial y lo firmamos entero:
*«Motion that answers a person's action (opening, expanding, confirming) is welcome when it shows
what changed»*.

| Micro-interacción | Cómo | Dónde |
|---|---|---|
| **Barrido de relleno** | `::before` con `left:-100%` que entra al hover | `bien/elevaiti-v2.html:300-305` |
| **Barrido de brillo** | `::before` con `inset:0`, gradiente blanco al 12 %, `translateX(-100%)` | `bien/yessmassage-v7.html:717-722` |
| **Empujón de la flecha** | La flecha es un `<span>` propio y se mueve 3 px | `bien/elevaiti-v53.html:65-66` |
| **Elevación con sombra teñida** | `translateY(-2px)` + sombra **del color de marca** | `bien/elevaiti-v53.html:62` |
| **Acento que se dibuja** | `scaleX(0)→1` con `transform-origin:left`, color por tarjeta | `bien/kalinayoga-v6.html:548-565` |

Dos cosas que hacen que esto no caiga en las penalizaciones del §0:

- **El brillo del barrido va al 12 %**, no al 40 % (`yessmassage:721`). A5 castiga por encima del
  25 %, y con razón: un destello fuerte lee como anuncio.
- **La sombra de la elevación va teñida con el color de marca**, `rgba(0,180,216,.35)` en
  `elevaiti-v53:62`, no negro puro. Es T5 (`textura-y-profundidad.md`), y aquí importa porque la
  sombra negra bajo una tarjeta redondeada es el cuarto *cluster* del look de IA.

---

## 7. Nivel premium — cada técnica con su «cuándo no»

Todas exigen **T11b cumplido** (§3.2) antes de entrar. El precedente de cada una está en
`catalogo-diseno.yaml`; aquí va el criterio.

| Técnica | Qué compra | Cuándo **NO** |
|---|---|---|
| **Timeline de entrada** (T12) | Un momento orquestado: los elementos del hero entran en un orden que alguien decidió, con solapes negativos (`'-=0.3'`) | Si la página ya tiene reveals por toda la pantalla → estarías comprando el efecto dos veces. **El timeline sustituye al reveal en el hero, no se suma** |
| **Parallax con `scrub`** (T12) | Que el fondo responda al scroll en vez de a un reloj. Valores medidos: `scrub: 1` · `1.5` · `2` (`dale/script.js:494,505,517`) | En móvil: `dale/script.js:12` declara `isMobile()` a ≤768 px por algo. Y nunca sobre el texto que se está leyendo |
| **Revelado por palabras** (T13) | Un titular que se compone solo. Se parte **a mano** en `<span class="word">`, sin SplitText — que es de pago y añade una dependencia por un efecto | Titulares de más de ~8 palabras (el escalonado se hace largo) y cualquier texto que no sea **el** titular. Es **anécdota**: un solo diseño |
| **Scroll suavizado** (T14) | Inercia continua al bajar | **Prohibido en `producto-panel`.** Secuestra el scroll del sistema operativo, rompe `Ctrl+F`, rompe el teclado y marea a quien no lo pidió. En una herramienta de trabajo es un fallo, no un lujo |
| **Cursor propio** (T15) | Un puntero con retardo (`cx += (mx-cx)*0.15`, `attomo:1408-1409`) | **Prohibido en `producto-panel`.** Y **nunca** con `cursor:none` global — `attomo:48` y `:315` lo hacen y es GD-06: si el JS falla, no hay puntero en toda la página. Solo bajo `@media (hover:hover)` |
| **Botón magnético** (T16) | El botón persigue al ratón dentro de su caja (`x*0.25`, `attomo:1576-1578`) | **Prohibido en `producto-panel`.** Es **anécdota**: un solo diseño, y el roto. Un objetivo que se mueve es más difícil de pulsar — choca con el *target size* de WCAG 2.2 |

**Marquesinas (T20), blobs y ondas (T19)** se mueven pero son **forma**, no movimiento: su ficha
está en `composicion.md`. Aquí solo el dato de tiempo, que sí es de este documento: 30 s lineales
para una marquesina (`elevaiti-v2.html:599`), 16-20 s para un blob (`yessmassage:527,535`).

---

## 8. `prefers-reduced-motion` — en CSS **y** en JS

Una de las dos frases que ya teníamos, con lo que le faltaba: **el bloque de CSS no basta cuando el
movimiento lo pone JavaScript.** GSAP escribe estilos en línea; un `transition-duration: 0.01ms` no
detiene una timeline.

La única referencia del corpus que lo hace bien lo hace **en los dos sitios**:

```css
/* resources/referencias-diseno/bien/dale-marketing-v4/styles.css:1423-1429 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
  .reveal { opacity: 1 !important; transform: none !important; }
}
```

```js
/* resources/referencias-diseno/bien/dale-marketing-v4/script.js:11 */
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
```

Y lo **usa** en los tres sitios donde hace falta, que es la parte que se olvida:

| Dónde | Qué hace | Línea |
|---|---|---|
| Pantalla de carga | La salta entera | `script.js:25-29` |
| Reveals | Fuerza `opacity:1` y `transform:none` y **sale sin registrar nada en GSAP** | `script.js:186-191` |
| Parallax | No lo monta | `script.js` (mismo patrón de salida temprana) |

**Fíjate en la línea `.reveal { opacity: 1 !important }` del CSS:** sin ella, un `transition-duration`
de 0,01 ms deja el elemento en su estado inicial —invisible— instantáneamente. Apagar la animación
sin reponer el estado final es la forma más común de dejar la página en blanco a quien pidió menos
movimiento. Es GD-05 con una vuelta de tuerca.

> **Medido:** de las 10 referencias, **dos** tienen bloque de reduced-motion. `kalinayoga-v6` y
> `attomo` no tienen ninguno (`anti-patrones.yaml` GD-05). Otra vez: este corpus se cita por su
> tipografía y su movimiento, **no** por su accesibilidad.

---

## 9. Conflicto declarado con `frontend-design` — y cómo se resuelve

El skill oficial (`plugins/claude-plugins-official/frontend-design`, 71 líneas) dice, literal:

> *«Use non-user-triggered motion sparingly and deliberately, only to draw attention. **A single
> orchestrated moment — one page-load sequence or one reveal — lands better than scattered effects;
> fade-and-slide-up entrances on each section and hover transitions on every card are the generic
> default and read as AI-generated.** Motion that answers a person's action (opening, expanding,
> confirming) is welcome when it shows what changed.»*

Eso choca de frente con hacer de T11 —un fade-and-slide-up— **el motor por defecto**. El conflicto
es real y no se disuelve diciendo que los dos tienen razón. Se reparte:

| Eje | Quién manda | Por qué |
|---|---|---|
| **Cantidad** | **`frontend-design`** | Tiene razón entera. Un reveal en cada sección más un hover en cada tarjeta es el default genérico, y se reconoce a distancia |
| **Mecanismo** | **Nosotros** | Cuando SÍ hay un reveal, se hace con mejora progresiva (§3.2) y easing largo. Eso no es una preferencia estética: el corpus tiene una página publicada e invisible por no hacerlo |
| **Qué lo salva de ser relleno** | **T18** | Un reveal que expresa la metáfora del sector no es el default genérico. Uno que no la expresa, sí — da igual lo bien hecho que esté |

**La regla operativa, que es lo que hay que recordar:**

> **Un momento orquestado por página**, en el hero, con la metáfora dentro. **Los demás bloques
> entran con el reveal por defecto, discreto y corto**, y solo si el contenido gana algo por entrar
> en vez de estar. Si al quitar el reveal de una sección la página no pierde nada, ese reveal
> sobraba — y el skill oficial tenía razón sobre esa sección.

Corolario incómodo y honesto: **el nivel 1 del §2 es más movimiento del que recomienda
`frontend-design`.** Se elige a sabiendas, para un perfil `web-cliente` con metáfora nombrada. Para
`producto-panel` la recomendación del skill gana sin discusión y el default es nivel 0.

---

## 10. Conflicto declarado con la tabla de los auditores (A2)

Menos vistoso que el anterior y más probable en el día a día. `calibration-v2.md:77` penaliza
**«micro-interaction duration > 500 ms»** con −0,5. Los reveals medidos en el corpus duran **0,7-0,9 s**
(§5), y el zoom de una foto al hover dura **0,7-0,8 s** (`kalinayoga-v6.html:638`, `:445`).

**La frontera, que no estaba escrita en ninguna parte:**

| | Es | Techo |
|---|---|---|
| **Micro-interacción** | Lo que responde a una acción y tiene que sentirse **instantáneo**: hover de botón, foco, abrir un desplegable | **≤ 400 ms.** A2 aplica entero |
| **Reveal / entrada** | Lo que ocurre **solo**, una vez, y no bloquea a nadie | 0,7-0,9 s. **A2 no aplica** |
| **Ambiente en bucle** | Blobs, respiración, marquesinas | 3-30 s. **A2 no aplica**; lo que aplica es A4 |

El zoom de imagen al hover cae justo en el filo: **responde a una acción** (luego es
micro-interacción) pero **0,7 s es lo que lo hace parecer caro** en vez de brusco. Queda declarado
como excepción con nombre: **transformaciones de imagen al hover, hasta 0,8 s**. Fuera de ahí, 400 ms.

⚠️ Esto es **criterio escrito, no mecanismo**: A2 sigue siendo el número que aplica el auditor. Si
al puntuar una página aparece un −0,5 por un reveal de 0,8 s, el hallazgo es **de esta frontera**, no
del diseño, y lo que toca es corregir `calibration-v2.md` — que es un fichero compartido por los tres
auditores y cambiarlo los cambia a los tres a la vez.

---

## 11. Límites honestos

- **El movimiento no se puede auditar hoy.** Todas las capturas del harness son **estáticas**
  (`scripts/screenshot.py`) y `visual-regression` corre **con las animaciones apagadas**, a propósito,
  para que el diff sea estable. O sea: ningún gate nuestro puede ver si el movimiento es bueno, ni
  si existe. Lo que sí es medible sin ejecutar nada es lo de abajo.
- **Lo que se mide** (estático, barato): que existe bloque de `prefers-reduced-motion` en CSS y la
  comprobación equivalente en JS (GD-05) · que no hay `cursor:none` global (GD-06) · que no hay
  loader forzado (GD-02) · que el texto sigue visible con el JS apagado (GD-01) · las duraciones y
  curvas declaradas como tokens (T5b). **Las cinco están en `sombra`**: cuentan, no avisan, no
  bloquean.
- **Lo que es juicio y no se va a poder medir:** si la metáfora es la correcta, si el momento
  orquestado está en el sitio que toca, y si al quitar un reveal la página pierde algo. Eso lo
  contesta `vera-art-director` o una persona, y su respuesta no es un número.
- **Diez diseños de un equipo no son dominancia** (`patterns/README.md` §1, precedente GAP-1). Puede
  ser simplemente nuestro gusto. Por eso **nada de este documento bloquea nada**.

---

## Anti-patterns

- ❌ **Animar sin haber terminado la frase «esta página se mueve como ___»** → sale un `@keyframes
  float` que serviría para cualquier web del mundo (`elevaiti-v7.html:321`), y eso es relleno.
- ❌ **`opacity:0` sin condición en el CSS** → si el JS no corre, no se ve nada. Cuelga siempre de
  `body.js-ready` (§3.2).
- ❌ **Definir la función que arranca la animación y no llamarla** → `attomo:1441`. Una página real,
  publicada, invisible, y ningún test nuestro la cazaba.
- ❌ **Bloque de `prefers-reduced-motion` solo en CSS cuando el movimiento lo pone GSAP** → la
  timeline sigue corriendo; escribe estilos en línea y se los salta.
- ❌ **Apagar la animación sin reponer el estado final** → `transition-duration:0.01ms` deja el
  elemento invisible para siempre. Hace falta la línea `.reveal{opacity:1!important}`.
- ❌ **Un reveal en cada sección más un hover en cada tarjeta** → es el default genérico, lo dice el
  skill oficial y tiene razón (§9). Un momento orquestado por página.
- ❌ **Sumar la timeline de entrada al reveal en el hero** → se paga el efecto dos veces y se ve.
- ❌ **Escalonar ocho tarjetas a 0,15 s** → 1,2 s hasta la última; para entonces ya han bajado.
  Escalona por filas.
- ❌ **Invertir los tiempos**: lento lo que responde a una persona, rápido lo que ocurre solo.
- ❌ **`cursor:none` global** (GD-06) · **scroll suavizado o botón magnético en un panel** → son
  herramientas de trabajo, no portadas.
- ❌ **Loader forzado** (GD-02): 3,2 s en `yessmassage:4636-4637`, 1,6 s en `dale`. Retrasar el
  contenido para enseñar una animación de carga es cobrarle tiempo al visitante por nuestro gusto.
- ❌ **Easing y duraciones sueltas por el CSS** en vez de tokens (§4) → salen ocho curvas distintas.
- ❌ **Copiar el brillo del barrido al 40 %** → A5 lo penaliza por encima del 25 %, y el corpus lo
  pone al 12 %.
- ❌ **Citar este corpus por su accesibilidad** → 6 de 9 quitan el `outline` sin reponer el foco
  (GD-12) y solo 2 de 10 tienen reduced-motion. Se cita por su tipografía y su movimiento.

---

_Doc version: 1.0 · 2026-09-18 · Ola 2. Canon **declarado**: medido en `resources/referencias-diseno`,
un corpus ajeno a este repo, con el trato de GAP-1. No bloquea. Las técnicas, su estado y sus
precedentes verificados están en `catalogo-diseno.yaml`; aquí va el criterio._
