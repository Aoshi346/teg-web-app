# Paso 3 de `marca` — medir la referencia, no describirla

## Principio

Una referencia descrita de memoria no sirve para nada: *«tipografía serif elegante, paleta cálida»*
describe a la vez cuatro webs que no se parecen en nada. Lo que se puede aplicar es **un número**:
`DM Serif Display · 128px · interlineado 0,95 · tracking −0,02em`, y eso no se lee mirando una
captura — se mide.

La skill existe porque el eslabón medido que separa un diseño de esta casa de uno genérico es
partir de **activos y referencias reales**, y hoy ese paso se hacía a ojo. `marca` §Contrato de
entrada pide *«2-3 referencias visuales (URLs) que le gusten»* y remite aquí precisamente porque
*«mide en vez de describir»* — hasta hoy ese remite apuntaba a una skill que no existía.

> **Y hay una mitad que no es estética y decide más que ninguna otra:** el color, las fotos, los
> servicios y los horarios del cliente **salen de su web y de su Instagram**, no de nuestro gusto.
> Es la palanca de mayor efecto del canon y la única que no depende de nosotros
> (`patterns/diseno/imagen.md` §1). Aquí se extrae; si no hay de dónde, **se dice** y se marca como
> propuesta, no como herencia.

## Por qué vive dentro de `marca` (31-10-2026, sub-ola 3.65, UX-10)

Hasta el 31-10 era la skill `referencias-visuales`. Se invocaba casi siempre desde el paso 3 de
`marca` y desde el paso 0 de `direcciones-de-arte`, con **1 uso** registrado y presente en solo 2
proyectos: dos entradas en el listado para un mismo procedimiento. Su propio criterio de retirada
decía *«se borra el `SKILL.md` y se conserva solo `medir_referencia.py`, citado desde `marca` §paso
3»*. Eso es lo que se hizo: el procedimiento sigue entero aquí, el script vive en
`skills/marca/medir_referencia.py` y los disparadores pasaron a la description de `marca`.

## Cuándo activar

- **Paso 3 de `marca`**, antes de proponer un solo color.
- **Paso 0 de `direcciones-de-arte`**: las fichas de referencia son su materia prima.
- El Usuario pega dos o tres enlaces y dice «algo así», «me gusta esta», «como esta pero…».
- Hay que sacar el color real del cliente de su web o de su Instagram.
- Una referencia del proyecto se quedó vieja y hay que volver a medirla (§Límites: caducan).

Disparadores: 'analiza estas webs que me gustan', 'mide esta referencia', 'qué tipografía usa esta página', 'sácame la paleta de esta web', 'extrae el ADN visual de', 'cógele los colores a su Instagram' · Abre cada URL con Playwright y MIDE —familias y tamaños reales, hex por superficie, radios, sombras, rejillas y qué se mueve al hacer scroll—; devuelve ficha por referencia con «qué tomamos» y «qué NO», moodboard autocontenido y 2-4 direcciones de arte con nombre · NO usar para: la identidad y el kit de marca (el resto de `marca`; 'moodboard' a secas empieza en su paso 1); generar y comparar las direcciones (`direcciones-de-arte`); vigilar cambios de competidores (`competitive-intel`); auditar NUESTRA web (`vera-art-director`, `conrado-cro-auditor`, `aitor-a11y-auditor`); ni SEO (`/seo-on-page`).

## Contrato de entrada

| Necesito | Si no lo tengo |
|---|---|
| **2-5 URLs** | **Pregunto.** Con una sola no hay contraste: lo que se busca es qué comparten y en qué se separan. Con más de cinco, la ficha deja de leerse |
| **Qué le gusta de cada una**, en sus palabras | **Pregunto, en la misma tanda.** Es el dato que más vale y el que nunca está en la página: «me gusta lo tranquila que es» y «me gusta lo cara que parece» llevan a direcciones opuestas |
| **La web o el Instagram del cliente** | **Pregunto.** Si no tiene, la paleta pasa a ser **propuesta**, y eso se escribe en la ficha en vez de disimularlo |
| El **perfil** (`web-cliente` / `producto-panel`) | Se lee de `.docs/core/design-system.md` §0b. Si no está, se asume `web-cliente` y **se dice en la ficha** |
| Si alguna URL pide login | Se mide lo que se ve sin entrar y **la ficha lo declara**: medir la pantalla de acceso y llamarlo «su web» es el fallo del instrumento que no llega al sujeto |

**Una sola tanda de preguntas, máximo cuatro.** Si contesta a medias, se mide igual y lo asumido se
escribe en la ficha, visible.

## Procedimiento

### 1. Medir — el comando

```bash
K=.claude/skills/marca
D=.docs/plans/<plan>/referencias        # o .docs/core/marca/referencias si no hay plan
mkdir -p "$D"
python3 $K/medir_referencia.py "https://ejemplo-del-cliente.com" "$D/01-cliente.json"
python3 $K/medir_referencia.py "https://referencia-que-le-gusta.com" "$D/02-referencia.json"
```

Salida: **0** medido · **2 NO SE PUDO MEDIR**. Un 2 **no es «no tiene nada»**: es que el
instrumento no llegó, y se reporta como tal (`rules/verification.md`). Si lo que cargó es un
**muro** —HTTP ≥ 400, página de reto de bot, página de error o de bloqueo que responde 200, un
formulario de contraseña que ocupa la primera pantalla, captcha en una página corta, o menos de 300
caracteres visibles—, el JSON se escribe igual con `"muro": "<qué se vio>"` y la salida es 2: lo
medido es el muro. Un captcha en el formulario de contacto de una web larga, o el acceso de la
cabecera, **no** lo son. Antes salía 0 midiendo el login de McMaster (MO-24, 2026-10-21; prueba en
`_archive/2026-10-20/medicion-2.17/`). Límite: un portfolio de verdad con menos de 300 caracteres
también sale como muro; su JSON está escrito y se puede usar sabiéndolo.

Y la captura, que es la mitad de la ficha:

```bash
python3 .claude/scripts/screenshot.py "https://referencia.com" "$D/02-referencia.png" 1440 900 3000
python3 .claude/scripts/screenshot.py "https://referencia.com" "$D/02-referencia-movil.png" 390 844 3000
```

### 2. Qué devuelve, y por qué cada campo

| Campo | Qué es | Por qué así y no de otra manera |
|---|---|---|
| `tipografia` | Los 25 nodos de texto de más **área**, con familia, tamaño, interlineado y tracking reales | Ordenar por área y no por etiqueta es lo que hace que salga el display **de verdad**, aunque sea un `<span>`, y no un `<h1>` escondido de 12px |
| `colores` | Los computados, **ponderados por superficie** | Un hex del CSS no dice cuánto se ve. Esto ordena por cuánta pantalla ocupa, que es lo que percibe una persona |
| `radios` · `sombras` | Contados, con su número de apariciones | Aquí se ve si la sombra va **teñida** con el oscuro de marca o es negro puro (T5) |
| `rejillas` · `anchos` | Columnas, gap y ancho de contenedor reales | Es el dato que no se puede sacar de una captura |
| `movimiento.animaciones` | **El nombre del `@keyframes` y su duración** | El dato más caro de todo el fichero: §3 |
| `movimiento.reduced_motion` | `true` · `false` · `"no medible (N hojas de otro origen)"` | Tres veredictos, nunca dos |
| `al_hacer_scroll` | Cuántos elementos cambian, y cuáles **siguen invisibles en pantalla** | Distingue un reveal que funciona de un CSS que lo declara y nunca dispara |
| `sin_js.caracteres_visibles` | Texto con el JavaScript apagado | T11b / GD-01 |

### 3. El nombre del `@keyframes` es el hallazgo, no un detalle

Es lo único de la medición que no se puede copiar de un catálogo, y sale gratis:

```
bien/yessmassage-v7.html  →  breathe · 3s   logo-breathe · 4s   hero-breathe   zen-breathe
bien/kalinayoga-v6.html   →  floatPlant · 8s   stripScroll · 25s
bien/elevaiti-v7.html     →  float   spin      ← genéricos: se mueve y no dice nada del negocio
```

*(medido el 2026-09-18 con este mismo script contra `resources/referencias-diseno/`)*

Un `breathe` en un sitio de masaje **es** la metáfora del sector escrita en el código. Un `float`
sirve para cualquier página del mundo. Cuando la referencia trae nombres propios, **ahí está su
dirección de arte**, y se copia a la ficha tal cual (`patterns/diseno/movimiento.md` §1, T18).

### 4. La ficha — y su mitad útil es «qué NO tomamos»

Una por referencia, en `$D/<n>-<slug>.md`. Se escribe **desde el JSON**, nunca de memoria:

```markdown
# 02 · nombre-de-la-referencia
url: https://…            medida: 2026-09-18            perfil: web-cliente
lo que dijo el Usuario: «me gusta lo tranquila que es, no me agobia»

| | Medido |
|---|---|
| Display | DM Serif Display · 128px · interlineado 0,95 · tracking −0,02em |
| Texto | DM Sans · 16px · interlineado 1,7 |
| Fondo dominante | #FDF9F3 · segundo #F5EDE0 |
| Acento | #C67B5C (198,123,92) |
| Radios | 50% ×36 · 50px ×25 · 8px ×19 |
| Sombra | rgba(46,40,32,.06) 0 4px 20px — **teñida**, no negra (T5) |
| Rejilla | 2×528 gap 80 · 4×266 gap 24 · 3×357 gap 32 · contenedor 1136 |
| Transición dominante | 0,8s · cubic-bezier(.25,.46,.45,.94) ×45 |
| @keyframes | `floatPlant 8s` · `stripScroll 25s` — **la metáfora está en el nombre** |
| reduced-motion | no medible (1 hoja de otro origen) |

**QUÉ TOMAMOS** — el contraste de escala display/texto y el tracking negativo del display ·
la sombra teñida · la métrica de la rejilla.

**QUÉ NO TOMAMOS** — la paleta crema + serif de alto contraste + terracota: es el *cluster 1*
del «look de IA» (`patterns/diseno/catalogo-direcciones.md` §4) y este cliente no es un estudio
de yoga mediterráneo. Tampoco el zoom de fondo de 12s.

⚠️ Sin `prefers-reduced-motion` comprobable: no se cita esta referencia por su accesibilidad.
```

**El «qué NO tomamos» no es cortesía.** Sin él, la referencia se copia entera —defectos incluidos—
y eso es exactamente cómo el sesgo de una web ajena entra en la nuestra sin que nadie lo decida.
Cada línea de «qué tomamos» tiene que poder sostenerse con un número de la tabla de arriba.

### 5. El moodboard — un HTML autocontenido

Las capturas de las N referencias, una al lado de otra, con su ficha debajo. Convención completa en
`rules/html-output.md`: **un solo fichero, imágenes en base64, cero red**, porque tiene que abrirse
desde el móvil de quien decide sin levantar nada.

Si ya has generado las direcciones, el moodboard **no lo escribes a mano**: lo hace
`skills/direcciones-de-arte/galeria.py`, que es el mismo trabajo con otra materia prima. Para las referencias sueltas
vale el mismo patrón de tarjeta.

### 6. Las 2-4 direcciones candidatas — se proponen, no se eligen

De lo medido salen **2-4 direcciones con NOMBRE**, deliberadamente distintas entre sí, cada una con
las cinco decisiones de `patterns/diseno/catalogo-direcciones.md` §2 (emparejamiento tipográfico ·
temperatura de paleta · metáfora de movimiento · tratamiento de imagen · estructura).

**Aquí se nombran y se paran.** Generarlas, ponerlas en galería y hacer que una persona las ordene
es `direcciones-de-arte`. Y el orden lo pone el Usuario, nunca el agente: el corpus guarda la vez
que una IA ordenó y el humano eligió lo contrario.

### 7. Escribir la §9 de `design-system.md`

Es el paso que hace que esto sirva dentro de tres meses:

| Columna | De dónde sale |
|---|---|
| URL · Fecha | del JSON (`url`, y la fecha de la medición) |
| Qué SÍ tomamos | de la ficha |
| Qué NO tomamos | de la ficha |

Y la línea de abajo, *«Set de referencias del proyecto (lo produce `skills/marca`, paso 3)»*,
se rellena con `$D`. Sin eso, las referencias se piden una vez al arrancar y se pierden.

## Salida

```
referencias:   <n> medidas · <n> no medibles (y por qué)
ficheros:      <D>/<n>-<slug>.json · .md · .png · -movil.png
moodboard:     <ruta>  (autocontenido, verificado offline)
activos del cliente: <hex reales | "no tiene web: la paleta será PROPUESTA">
direcciones candidatas: <nombre> · <nombre> · <nombre>
design-system: §9 rellenada  |  <no existe design-system.md todavía>
supuestos:     <lo asumido, o "ninguno">
siguiente:     direcciones-de-arte con estas fichas  |  marca paso 4 (bajar a tokens)
```

## Qué NO hace

| No hace | Lo hace |
|---|---|
| Decidir la identidad, la guía y el kit | el resto de `marca`: esto es su paso 3 |
| Generar las variantes y la galería para ordenar | `direcciones-de-arte` |
| Vigilar qué **cambia** en una web con el tiempo | `competitive-intel` (tiene coste recurrente y viene apagada) |
| Juzgar si NUESTRA web está bien | `vera-art-director` · `conrado-cro-auditor` · `aitor-a11y-auditor` |
| Decidir la forma de una pantalla | `disenar-pantalla` |
| Copiar la referencia | nadie: §4 «qué NO tomamos» existe para impedirlo |

## Límites honestos

- **Medir no es entender.** El script da familias, hex y duraciones; no dice si esa referencia
  encaja con este negocio. Eso es criterio, y lo pone quien lee la ficha.
- **`reduced_motion` sale «no medible» en cuanto hay una hoja de otro origen** — Google Fonts basta.
  Medido: de las cuatro referencias del corpus que probé, **dos** dieron «no medible» y no
  `false`. Es correcto, y es la diferencia entre «no lo tiene» y «no lo pude mirar».
- **Detrás de un login no se mide nada**, y la ficha tiene que decirlo. Un arnés que no puede entrar
  y devuelve «0 fallos» está midiendo la pantalla de acceso.
- **Las capturas caducan.** Una web viva cambia sin avisar: la ficha lleva fecha y, si hay que
  citarla línea a línea, el fragmento se copia al proyecto (`rules/html-output.md`,
  `patterns/diseno/README.md` §5).
- **El instrumento está calibrado contra un fixture, no contra el mundo.** Se probó contra el diseño
  **roto a propósito** del corpus (`mal/attomo-digital.html`) y cazó sus dos defectos declarados:
  `cursor:none` global (GD-06) y 8 bloques con texto en pantalla a opacidad 0 por un reveal que no
  dispara (GD-01). Sobre webs ajenas de verdad **no está medido**.
- **Cuesta un navegador por URL.** Cuenta doble en RAM (`rules/ram-pytest.md`): compruébalo antes
  con `bash .claude/hooks/check-ram.sh` y no lo solapes con `pytest`.

## Anti-patterns

- ❌ **Describir la referencia en vez de medirla** («serif elegante, paleta cálida») → describe a la
  vez cuatro webs que no se parecen, y no se puede aplicar.
- ❌ **Una ficha sin «qué NO tomamos»** → la referencia se copia entera, defectos incluidos.
- ❌ **Inventar la paleta del cliente** cuando no se pudo entrar en su web → se marca **propuesta**,
  con esa palabra.
- ❌ **Presentar el resultado de una URL que devolvió 2** como si fuera una medición.
- ❌ **Medir la pantalla de login y llamarlo «su web»**.
- ❌ **Una sola referencia** → sin contraste no hay nada que comparar, que es el trabajo.
- ❌ **Copiar la paleta crema + serif + terracota porque «queda bien»** → es el *cluster 1* del look
  de IA, aparece en dos de nuestras propias referencias, y sin justificación escrita es un default.
- ❌ **Ordenar tú las direcciones candidatas** (§6) → eso es del Usuario, y el corpus guarda por qué.
- ❌ **Rellenar §9 de `design-system.md` con «varias webs de yoga»** → una referencia se cita con
  URL y fecha o no se cita.
- ❌ **Correr esto para vigilar a un competidor** → es `competitive-intel`, que compara contra la
  ejecución anterior; aquí solo hay una foto.
- ❌ **Citar el corpus de la casa por su accesibilidad** → 6 de 9 quitan el `outline` sin reponer el
  foco. Se cita por su tipografía, su composición y su movimiento.

## Ejemplos

### Usuario: «mira estas tres, me gustan mucho: <url1> <url2> <url3>»
TL: pregunta **una vez** qué le gusta de cada una y si el cliente tiene web o Instagram → corre
`medir_referencia.py` sobre las cuatro URLs (las tres más la del cliente) → tres fichas con su
«qué NO tomamos» → moodboard → *«las tres comparten interlineado de display por debajo de 1 y
tracking negativo; se separan en la temperatura. Del cliente salen estos dos hex reales. Con esto
propongo tres direcciones: <nombre>, <nombre>, <nombre> — ¿las genero?»*

### Usuario: «es que el cliente no tiene web ni redes»
TL: se mide solo lo que hay. La ficha dice **paleta: PROPUESTA, no heredada**, y esa palabra viaja
hasta `design-system.md` §0b. No se rellena el hueco con un azul corporativo plausible.

### Usuario: «cógele los colores a nuestra web actual»
TL: una sola URL, y aquí sí es correcto tener una: no se busca contraste, se busca **documentar la
marca que ya existe**. Salida directa al paso 0 de `marca` («esto no es crear, es completar»).

## Related

- `skills/marca` — **donde vive**: es su paso 3. Si el Usuario pide «moodboard» o «manual de
  marca», el orden empieza en su paso 1, no aquí
- `skills/direcciones-de-arte` — **quien la consume**: su paso 0 son estas fichas
- `patterns/diseno/imagen.md` §1 — los activos reales del cliente: la palanca de mayor efecto
- `patterns/diseno/catalogo-direcciones.md` §2 y §4 — las cinco decisiones, y los clusters del
  «look de IA» que hay que saber reconocer antes de copiar una referencia
- `patterns/diseno/movimiento.md` §1 — por qué el nombre del `@keyframes` es el hallazgo
- `templates/core/design-system.md` §9 — lo que rellena el paso 7
- `resources/referencias-diseno/INDEX.json` — las referencias internas citables `fichero:línea`
- `rules/html-output.md` — la convención del moodboard autocontenido
- `rules/verification.md` — los tres veredictos del instrumento, de donde sale el exit 2
- `scripts/screenshot.py` — las capturas, con la detección de navegador de la casa
