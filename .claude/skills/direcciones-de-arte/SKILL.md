---
name: "direcciones-de-arte"
description: >-
  Usar para proponer VARIOS MUNDOS VISUALES y que una persona elija: 'enséñame varias
  direcciones', 'propón 3 estilos distintos', 'no sé qué estilo quiero', 'dirección de arte'. NO
  usar para: UNA pantalla (disenar-pantalla), la identidad (marca), medir referencias
  (marca, paso 3), qué pantallas (/producto), el código (nueva-pantalla) ni auditar
  (vera-art-director, /qa-loop).
user-invocable: true
metadata:
  version: 1.1.0
  author: tech-lead-template
  category: workflow
  updated: 2026-11-01
  verificado: 2026-09-18
---

# direcciones-de-arte — varias, con nombre, y ordena una persona

## Principio

**La calidad de los diseños buenos de esta casa no vino de un skill de diseño: vino de este
proceso.** Está medido sobre 53 commits y escrito en el `README.md` del corpus — el skill de diseño
de aquel workspace *«tenía por motor enlaces simbólicos rotos y nunca pudo ejecutarse»*. Lo que sí
ocurrió fue: **varias direcciones de arte con nombre → una galería → un humano las ordena con
razones de negocio → se fusiona lo mejor de varias.**

Esta skill es ese proceso, y su decisión más importante es **lo que NO hace**: no ordena. El corpus
conserva a propósito dos rankings de las mismas versiones —`proceso/RANKING.csv` (el cliente) y
`proceso/elevaiti-FINAL-RECOMMENDATION.md` (la IA)— y ordenan distinto. Las **dos** versiones que
llegaron a producción estaban en el **último escalón** del ranking de la IA.

> **Una dirección de arte no es un estado de ánimo: son cinco decisiones que se sostienen entre sí**
> (`patterns/diseno/catalogo-direcciones.md` §2). Si una no encaja con las otras cuatro, no hay
> dirección: hay un moodboard.

## Filtro de existencia — por qué esto es una skill y no un párrafo

| Criterio de `skill-authoring` | Contestado |
|---|---|
| **(a) restricciones exigibles** | Sí, y son duras: N direcciones deliberadamente distintas · las cinco decisiones declaradas en cada una · presupuesto del perfil · el agente **no** rankea · la ganadora **no** se entrega intacta |
| **(b) estructura idéntica cada vez** | Sí: brief → efectos con nombre → N direcciones → galería → parada → fusión → tokens |
| **(c) sin que el Usuario explique el caso** | Sí: con las fichas del paso 3 de `marca` y su brief arranca sola |

**Regla de tres:** una vez por proyecto de cliente con web, y esta casa hace landings y webs de
cliente como trabajo habitual (decisión de Miller, 2026-09-18: *«hacemos landings, webs de
clientes, productos, paneles y web apps»*).

**Criterio de retirada:** si a los tres meses tiene **0 invocaciones**, se retira el `SKILL.md`, se
conserva `galeria.py` como comando suelto y el proceso queda **solo** como documento en
`patterns/diseno/catalogo-direcciones.md` §1 — que es donde ya está descrito.

## Cuándo activar

- Después de `marca` (identidad y guía) y de el paso 3 de `marca` (las fichas medidas).
- El Usuario dice que no sabe qué estilo quiere, o pide ver opciones antes de decidir.
- **Perfil `web-cliente` y §0b de `design-system.md` sin dirección elegida** — entonces esto va
  antes que cualquier `disenar-pantalla`.
- Hay que rehacer la dirección de un proyecto que ya existe porque «parece una plantilla».
- Disparadores: 'enséñame varias direcciones', 'propón 3 estilos distintos', 'no sé qué estilo
  quiero', 'haz varias versiones de la home', 'dirección de arte', 'móntame una galería para
  elegir', 'coge lo mejor de la 1 y de la 3', '/direcciones-de-arte'. Genera N direcciones CON
  NOMBRE (3 por defecto, máx 5), cada una en un fichero único con CSS a mano y cero red, las pone en
  una galería con miniaturas y PARA: el ranking lo hace el Usuario con razones de negocio, nunca el
  agente. Después fusiona lo mejor y rellena §0b y §3-§4e de design-system.md.
- NO usar para: la forma de UNA pantalla en un sistema ya elegido (`disenar-pantalla`); la
  identidad y el kit (`marca`, que va antes); medir las referencias (el paso 3 de `marca`);
  decidir qué pantallas hacen falta (`/producto`); escribir el código (`nueva-pantalla`); ni auditar
  (`vera-art-director`, `/qa-loop`).

### Cuándo NO, y es la mitad del trabajo de esta sección

| Situación | Qué toca |
|---|---|
| **Perfil `producto-panel`** | Casi siempre **no aplica**. Su dial de variación es **bajo**: se hereda **una** dirección del proyecto y lo que se compara son **2 variantes estructurales** de una pantalla (tabla/lista/tarjetas) → eso es `disenar-pantalla`. Correr esto en un panel produce tres mundos visuales para una herramienta que alguien va a usar ocho horas al día |
| Ya hay dirección elegida en §0b | Se respeta. Reabrirla es rehacer el proyecto, no diseñar una pantalla |
| Solo hace falta decidir una pantalla | `disenar-pantalla` — minutos, un fichero, una decisión estructural |
| No hay identidad ni guía todavía | `marca` primero: sin saber qué transmite, las tres direcciones salen de tu gusto |

## Contrato de entrada

| Necesito | Si no lo tengo |
|---|---|
| **Identidad y guía** (`10-identidad.md`, `11-guia-marca.md`) | **Paro y mando a `marca`.** Generar mundos visuales sin saber qué transmite el negocio es proponer tu gusto tres veces |
| **Fichas de referencia medidas** | **Corro el paso 3 de `marca` antes.** Partir de una impresión en vez de una medición es lo que esta cadena existe para evitar |
| **El perfil** (§0b) | **Pregunto.** Decide los diales, el presupuesto y la rúbrica; no es una etiqueta (`patterns/diseno/perfiles.yaml`) |
| **Activos reales**: fotos, servicios, precios, logo, colores del cliente | **Se piden, y si no llegan se DICE.** Sin ellos el resultado será pulido y genérico por construcción, y ninguna de las N direcciones lo arregla |
| **Cuántas direcciones** | Por defecto **3**. Máximo **5**: por encima, nadie las compara, se miran las dos primeras |
| **Quién va a ordenarlas, y cuándo** | **Pregunto explícitamente.** Si no hay nadie, la skill entrega N sin ganadora — §5 |

## Procedimiento

### 0. Leer, no volver a preguntar

```bash
cat <plan>/arranque/10-identidad.md <plan>/arranque/11-guia-marca.md 2>/dev/null
ls .docs/plans/<plan>/referencias/*.md          # las fichas del paso 3 de marca
sed -n '/## 0b/,/## 1/p' .docs/core/design-system.md   # ¿hay perfil? ¿hay dirección ya?
python3 -c "import yaml;d=yaml.safe_load(open('.claude/patterns/diseno/perfiles.yaml'));
print([ (p['id'], p['dials'], p['presupuesto']) for p in d['perfiles'] ])"
```

Y la baraja de arranque, que existe para **no empezar en blanco**:
`patterns/diseno/catalogo-direcciones.md` §3 — nueve direcciones que esta casa ya llevó a
producción, con sus cinco decisiones cada una.

⚠️ **Es una baraja, no un menú.** Elegir la fila cuyo sector coincide y entregarla es cómo el
cliente acaba recibiendo la web de otro, y encima con el sesgo de 2026 dentro (§4 de ese documento:
**tres de las diez referencias caen en un *cluster* del «look de IA»**).

### 1. Traducir la sensación a EFECTOS CON NOMBRE

Es el paso que más cambia el resultado y el que más se salta. El Usuario no dice «quiero
`cubic-bezier(.16,1,.3,1)`»: dice **«animaciones relajantes, como un masaje»**. Eso no se puede
implementar. Lo que sí:

| Lo que dijo | Lo que se escribe |
|---|---|
| «relajante, como un masaje» | el **logo respira** (escala 0,98→1,02 en 4s) · **partículas de incienso** que suben lentas · **onda de agua** al pulsar el botón |
| «que parezca que la empresa se mueve» | la **carretera** que se dibuja desde el horizonte al entrar y se desplaza al bajar |
| «serio pero no antiguo» | **nada se desliza**: todo aparece, y el único movimiento es el que responde a una acción |

**La regla, literal:** antes de escribir una sola animación, termina la frase *«esta página se mueve
como ___»*. Si no puedes terminarla, lo que pongas va a ser relleno — y se nota, porque sale un
`@keyframes float` que serviría para cualquier web del mundo
(`patterns/diseno/movimiento.md` §1, T18).

Los efectos con nombre son **3-6 por dirección** y van en su ficha. Quien los **implementa** es la
skill `movimiento`; aquí se nombran.

### 2. Nombrar las direcciones — distintas de verdad

**Tres, por defecto. Deliberadamente distintas entre sí.** Dos variaciones de lo mismo no son una
comparación: son una, dos veces, y se le pide al Usuario que elija con el estómago.

El mejor argumento de que un mismo cliente admite mundos opuestos está en el propio corpus:
`kalinayoga` tiene **dos entradas** para el **mismo cliente** —*Boho Chic Mediterráneo* y *Luxury
Editorial*— y las dos funcionan.

Cada dirección se declara **en sus propios `<meta>`**, que es de donde los lee la galería:

```html
<meta name="direccion"  content="Boho Chic Mediterráneo">
<meta name="tipografia" content="DM Serif Display + DM Sans">
<meta name="paleta"     content="cálida costera: terracota, arena, azul">
<meta name="metafora"   content="la planta que se mece">
<meta name="imagen"     content="overlay teñido de marca + zoom 1,04">
<meta name="estructura" content="B2C bienestar: sensación → catálogo → prueba → reserva">
```

Las seis, siempre. `galeria.py` marca en rojo la que falte y lo dice con todas las letras: *una
dirección sin sus cinco decisiones es un moodboard*.

### 3. Generar cada dirección — el presupuesto NO es capricho

Para `web-cliente`, medido en el corpus (`patterns/diseno/perfiles.yaml`):

| | |
|---|---|
| **Ficheros** | **1** — un `.html` autocontenido |
| **CSS** | **2.500-5.000 líneas escritas a mano** |
| **Dependencias de red** | **0** — ni CDN, ni fuentes remotas salvo la tipografía de la dirección, con su fallback |

> **Por qué ese número.** Las versiones que gustaron tienen 2.500-5.000 líneas de CSS a mano en un
> fichero único. Las que un modelo barato generó en uno o dos minutos —170 a 990 líneas— **no fueron
> las elegidas por el humano ni una sola vez**. El presupuesto es la diferencia medida entre una
> dirección de arte y un boceto.

Contenido **real** del cliente, no relleno: sus servicios, sus precios, sus fotos, su logo
redibujado de su JPG. Lo que falte se marca **«sin datos»**, nunca con un precio plausible
(`patterns/diseno/imagen.md` §1). Y `T11b` **se cumple desde la primera línea**: el `opacity:0`
cuelga de `body.js-ready`, o la dirección puede acabar publicada e invisible — le pasó a una de
verdad. Se pega de `templates/diseno/motor-reveal.html`.

```bash
mkdir -p .docs/plans/<plan>/direcciones
# una por fichero, con su nombre en el nombre del fichero
#   a-boho-chic.html · b-luxury-editorial.html · c-minimal
```

### 4. La galería — verlas juntas es el trabajo

```bash
python3 .claude/skills/direcciones-de-arte/galeria.py .docs/plans/<plan>/direcciones --puerto 8879
```

`--puerto 8879` y `--puerto=8879` valen igual. Si el puerto está ocupado, el servidor no contesta o
una dirección no responde 200, sale con **2** y lo dice: hasta el 2026-10-21 la forma con espacio
ignoraba el puerto y la galería embebía el 404 de otro servidor (MO-24).

Captura cada dirección a 1440 y a 390, embebe las miniaturas en base64, lee las seis `<meta>` y
escribe `galeria.html` **autocontenida** más un `RANKING.csv` con la columna `Ranking` **vacía**.
Salida: 0 escrita · 2 no se pudo medir. Nunca pisa un `RANKING.csv` que ya exista.

**Enseñarlas de una en una por correo no es comparar: es pedir aprobación tres veces.**

Verificar la galería antes de enseñarla (`rules/html-output.md`):

```bash
cd .docs/plans/<plan>/direcciones && python3 -m http.server 8899 --bind 127.0.0.1 &
python3 .claude/scripts/screenshot.py "http://127.0.0.1:8899/galeria.html" /tmp/galeria.png 1440 900
grep -c 'stylesheet\|https://' galeria.html    # debe dar 0: autocontenida
```

#### 4b. Si ya hay producto construido: su piel con cada dirección (sub-ola 3.67)

Cuando el proyecto **ya tiene producto** (se rehace la dirección porque «parece una plantilla»), la
galería enseña mundos genéricos y el Usuario no ve SU producto. Antes de parar, ofrécele también esto:

```bash
python3 .claude/scripts/previsualizar_tokens.py http://127.0.0.1:<PUERTO> --rutas / /clientes \
  --direccion a=<dir>/a.html --direccion b=<dir>/b.html --parejas <dir>/parejas.json \
  --salida <dir>/previa --guardar-dom
```

Inyecta los tokens de cada dirección en el `:root` del producto real y captura por ruta y ancho
(`previa/index.html`, lado a lado con `actual`). Sale con **2** si una dirección no cambia ningún
token del producto (falta `--parejas`), si la URL no es local o si una ruta no responde 2xx.
**Solo enseña la piel**, no la estructura: complementa a la galería, no la sustituye. Con
`--guardar-dom`, `gate_diseno.py --dom <dir>/previa/<x>/dom` mide la página pintada.

### 5. PARAR. El ranking lo pone el Usuario

⚠️ **Recordatorio, repetido a propósito porque es justo donde se deriva:** aunque una dirección te
parezca obviamente la buena, **no la recomiendes como ganadora**. Que te lo parezca es exactamente
el caso que el corpus registró y en el que el humano eligió lo contrario.

Lo que se entrega:

```
Tienes 3 direcciones en <ruta>/galeria.html — ábrela y compáralas.
Ordénalas en RANKING.csv (misma carpeta) con razones de NEGOCIO, no de estética.
Del ranking real de la casa: «los productos se pierden» · «no deja claro el problema»
· «prima estética sobre conversión». Eso es lo que sirve; «me gusta más el azul», no.
```

**Si nadie ordena, la skill entrega N direcciones sin ganadora, y eso es lo correcto, no un
fallo.** Se cierra con `estado: sin ordenar — esperando al Usuario` y no se elige por defecto. Una
ganadora que nadie eligió es una decisión que nadie tomó.

Si te piden una recomendación, dala **con su razón de negocio** —que es lo que se puede
contrastar— y déjala marcada como recomendación, en el mensaje, nunca dentro del `RANKING.csv`.

### 6. Fusionar — la ganadora no se entrega intacta

Ninguna de las direcciones del corpus que llegó a producción es una propuesta intacta. La fusión
produce una **versión nueva**, con la tabla de qué vino de dónde:

| Bloque | Viene de | Por qué |
|---|---|---|
| Hero y escala tipográfica | A · Boho Chic | El contraste display/texto es el que el Usuario señaló |
| Bloque de precios | C · Editorial numerada | «ayuda a decidir»: razón de negocio del ranking |
| Metáfora de movimiento | A | Las otras dos no tenían ninguna declarada |

Esa tabla se guarda: es lo que explica, dentro de seis meses, por qué la web es como es. Y las
descartadas **se conservan** con su razón — sin eso, dentro de dos meses alguien propone otra vez
la que ya se descartó.

### 7. Bajar a `design-system.md`

Es el paso que hace que lo anterior sirva para algo:

| Sección | Qué se rellena |
|---|---|
| **§0b** | **Perfil · nombre de la dirección · metáfora de sector · «qué NO debe parecer nunca» · ruta a su ficha** |
| §3 Tipografía · §2 Color · §4b Rejilla | Los valores de la dirección fusionada |
| §4c Movimiento | El **nivel** y los efectos con nombre del paso 1 → los implementa `movimiento` |
| §4e Imagen | El tratamiento, y **de dónde salen las fotos** |
| §7 Decisiones ya tomadas | Lo que se descartó y por qué |

Y `reviewed:` con la fecha de hoy. Sin ella, el índice del core lo marca en rojo — con razón: nadie
ha confirmado que siga siendo cierto.

## Salida

```
direcciones:   <n> generadas · <nombre> · <nombre> · <nombre>
fichas:        6/6 metas declaradas en <n> de <n>   | faltan: <cuáles>
presupuesto:   <líneas de CSS por dirección> · dependencias de red: <n>
galeria:       <ruta> · <KB> · autocontenida=<sí> · verificada a 1440 y 390
ranking:       <esperando al Usuario | recibido: 1=<x> 2=<y> 3=<z>>
fusion:        <no procede todavía | <ruta> + tabla de procedencia>
design-system: §0b <rellenada|pendiente> · §4c <nivel> · reviewed=<fecha>
activos reales: <qué entregó el cliente | qué falta y se marcó «sin datos»>
estado:        <sin ordenar — esperando al Usuario | fusionada y bajada a tokens>
```

## Qué NO hace

| No hace | Lo hace |
|---|---|
| **Ordenar las direcciones** | Una persona, con razones de negocio (§5) |
| Decidir la identidad y la guía | `marca`, antes |
| Medir las webs de referencia | el paso 3 de `marca`, antes |
| Decidir la forma de una pantalla concreta | `disenar-pantalla`, después y dentro de la dirección ganadora |
| Implementar el movimiento | `movimiento` |
| Escribir el código del producto | `nueva-pantalla` |
| Auditar el resultado | `vera-art-director` · `ignacio-roig` · `/qa-loop` |

## Límites honestos

- **Esto no garantiza un buen diseño.** Garantiza que hay **con qué comparar** y que la elección la
  toma quien paga. Tres direcciones mediocres siguen siendo tres direcciones mediocres.
- **Cuesta horas, no minutos.** Tres direcciones a 2.500-5.000 líneas de CSS son tres diseños, no
  tres bocetos. Si lo que hace falta es decidir una pantalla, `disenar-pantalla` cuesta minutos y es
  la herramienta correcta.
- **La baraja de arranque tiene el sesgo dentro.** Son diez diseños de un equipo con las
  herramientas de 2026: tres de ellos caen en un *cluster* del «look de IA». Usarla como menú es
  coger ese sesgo tal cual.
- **El presupuesto de 2.500-5.000 líneas es EXCLUSIVO de `web-cliente`.** Filtrarlo a
  `producto-panel` rompe el molde de 10 ficheros y el origen único de tokens, que son justo lo que
  hace mantenible un panel. Es un anti-pattern declarado, no un matiz.
- **`galeria.py` no juzga**: captura, embebe y tabula. Que una miniatura se vea bien no dice nada de
  si la dirección es la correcta.
- **Nada de esto bloquea nada.** `patterns/diseno/` es canon **declarado**, no medido en este repo,
  con el trato del precedente GAP-1.

## Anti-patterns

- ❌ **Que el agente ordene las direcciones y presente la ganadora** → el corpus guarda la vez que
  eso se hizo y el humano eligió lo contrario (§5).
- ❌ **Proponer una sola dirección** → no hay comparación, así que no hay decisión: hay aprobación.
- ❌ **Tres variaciones de la misma idea** y llamarlas tres direcciones → es una, en tres tallas.
- ❌ **Usar la baraja de `catalogo-direcciones.md` como menú**: elegir la fila cuyo sector coincide y
  entregarla → el cliente recibe la web de otro.
- ❌ **Una dirección sin sus cinco decisiones declaradas** → es un moodboard, y `galeria.py` lo dice.
- ❌ **Cinco direcciones «para dar más donde elegir»** → se miran las dos primeras.
- ❌ **Generar en dos minutos 300 líneas de CSS y llamarlo dirección** → medido: de esas no se eligió
  ninguna, nunca (§3).
- ❌ **Entregar la ganadora intacta** → la que llega a producción se fusiona (§6).
- ❌ **Tirar las descartadas sin escribir por qué** → dentro de dos meses alguien propone la misma.
- ❌ **Elegir la dirección antes de tener los activos reales del cliente** → la paleta sale de su web
  o su Instagram, no de una tabla.
- ❌ **Inventar un precio, un horario o un testimonio** para que la dirección se vea completa → acaba
  publicado. Lo que falta se marca **«sin datos»**.
- ❌ **Declarar `opacity:0` sin colgarlo de `body.js-ready`** → una de las referencias reales está
  publicada e invisible por exactamente esto.
- ❌ **Correr esto en un `producto-panel`** → tres mundos visuales para una herramienta de trabajo;
  lo que ahí se compara son dos variantes estructurales, y eso es `disenar-pantalla`.
- ❌ **Escribir la recomendación del agente dentro de `RANKING.csv`** → ese fichero es del Usuario;
  mezclarlas borra quién dijo qué (es la misma frontera que `tl_rec` vs `decision` del report-kit).

## Ejemplos

### Usuario: «no sé qué estilo quiero para la web del centro de masajes»
TL: comprueba identidad y guía (`marca`) y las fichas medidas (el paso 3 de `marca`) → traduce
«relajante como un masaje» a tres efectos con nombre → genera **tres** direcciones distintas de
verdad (Zen · Luxury Editorial · Minimal cálido), cada una con sus seis `<meta>` → `galeria.py` →
*«están en galeria.html; ordénalas en RANKING.csv con razones de negocio»* → **para**.

### Usuario: «me gusta la 1 pero el bloque de precios de la 3»
TL: eso es exactamente la fusión (§6). Versión nueva con la tabla de procedencia, las descartadas
conservadas con su razón, y de ahí a §0b y §3-§4e de `design-system.md`.

### Usuario: «hazme tres versiones del panel de administración»
TL: lo dice y propone lo correcto: *«el perfil es `producto-panel`, y ahí no se comparan mundos
visuales: se hereda la dirección del proyecto y se comparan dos variantes estructurales de la
pantalla — tabla, lista+detalle o tarjetas. Eso es `disenar-pantalla` y cuesta minutos. Si lo que
quieres es replantear el aspecto del producto entero, eso sí es esta skill, pero es otra tarea.»*

### Usuario: «genera las tres y elige tú la mejor, no tengo tiempo»
TL: genera las tres, monta la galería y **entrega sin ganadora**, con una recomendación **fuera**
del CSV y con su razón de negocio: *«recomiendo la B porque construye el recorrido problema →
solución → prueba → acción, que es lo que convierte; pero la elección es tuya y el fichero está
listo para que la marques en dos minutos.»*

## Related

- `patterns/diseno/catalogo-direcciones.md` — **la doctrina**: §1 por qué es una baraja y no un
  menú · §2 las cinco decisiones · §3 las nueve cartas · §4 los clusters del «look de IA» · §5
  quién ordena
- `patterns/diseno/perfiles.yaml` — los diales y el presupuesto por perfil
- `patterns/diseno/movimiento.md` §1 — la metáfora, que es el paso 1 de aquí
- `patterns/diseno/imagen.md` §1 — los activos reales, sin los cuales las N direcciones son N
  plantillas
- `resources/referencias-diseno/proceso/RANKING.csv` — **el formato exacto** que replica `galeria.py`
- `resources/referencias-diseno/proceso/elevaiti-FINAL-RECOMMENDATION.md` — el ranking de la IA que
  el humano ignoró; se conserva por eso
- `templates/diseno/motor-reveal.html` — el motor de entrada, con T11b dentro
- `skills/marca` (con su paso 3, la medición de referencias) — va **antes**
- `skills/movimiento` — implementa los efectos que aquí se nombran
- `skills/disenar-pantalla` — va **después**, dentro de la dirección ganadora
- `templates/core/design-system.md` §0b y §3-§4e — lo que rellena el paso 7
- `rules/motores-de-diseno.md` Parte F — el orden de las fases · `rules/html-output.md` — la galería autocontenida
