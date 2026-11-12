# Catálogo de direcciones de arte — una baraja de arranque, no un menú

> **Cuándo aplicar:** al **abrir** el diseño de un proyecto, cuando hay que proponer tres o cuatro
> mundos visuales distintos antes de que nadie elija uno. Da las direcciones con nombre que esta casa
> ya ha llevado a producción, cada una descompuesta en sus cinco decisiones, para **no empezar en
> blanco**.
>
> **NO aplicar:** como lista de la que se copia una fila. Eso es exactamente lo que este documento
> existe para evitar (§1) · para **decidir los valores** del sistema de diseño del proyecto, que es
> `skills/marca` y `patterns/stack/frontend-design-system.md` · para la **mecánica** de cada
> técnica, que vive en `tipografia.md`, `composicion.md`, `textura-y-profundidad.md`, `movimiento.md`
> e `imagen.md` · para **auditar** una dirección ya construida (`vera-art-director`).
>
> **Relacionado:** `resources/referencias-diseno/INDEX.json` (la dirección de arte de cada entrada) ·
> `resources/referencias-diseno/proceso/galeria-designs.html` (las fichas originales) ·
> `resources/referencias-diseno/proceso/RANKING.csv` (el orden que puso un humano) ·
> `catalogo-diseno.yaml` · `movimiento.md` §1 (la metáfora nace aquí y se ejecuta allí).

---

## 1. Esto es una baraja, y la diferencia importa

**Una baraja de arranque sirve para no quedarse en blanco y para tener con qué contrastar. Un menú
sirve para elegir sin pensar.** Si estas nueve fichas se usan como menú, el resultado es peor que no
tenerlas: se copia la más parecida al sector, se entrega, y el cliente recibe la web de otro.

La razón no es filosófica, está medida y es lo primero que dice el `README.md` del corpus:

> *«La calidad de aquel workspace **no venía de su skill de diseño** —cuyo motor eran enlaces
> simbólicos rotos y nunca pudo ejecutarse— sino del **proceso**: varias direcciones de arte con
> nombre, comparadas en una galería, rankeadas por un humano con razones de negocio, y fusionadas
> después.»*

O sea: lo que produjo estos diseños **no fue una lista de estilos**. Fue generar varias direcciones,
ponerlas una al lado de otra y hacer que alguien las ordenara con razones de negocio. Esta baraja es
el material de partida de ese proceso, no su sustituto.

**Cómo se usa, en cuatro pasos:**

1. **Tres o cuatro direcciones con nombre**, deliberadamente distintas entre sí. Dos variaciones de
   lo mismo no son una comparación. El mejor argumento de esto está en el propio corpus: `kalinayoga`
   tiene **dos entradas** —*Boho Chic Mediterráneo* y *Luxury Editorial*— para el **mismo cliente**,
   y las dos funcionan (`INDEX.json`: *«prueba que el MISMO cliente admite dos mundos visuales
   distintos y coherentes»*).
2. **Una galería que las enseñe juntas** (`proceso/galeria-designs.html`). Enseñarlas de una en una
   por correo no es comparar: es pedir aprobación tres veces.
3. **Que las ordene una persona, con razones de negocio.** No el agente (§4).
4. **Fusionar.** La elegida se lleva lo mejor de las descartadas. Ninguna de las que llegaron a
   producción es una de las propuestas intacta.

---

## 2. Las cinco decisiones de una dirección

Una dirección de arte no es un estado de ánimo: son **cinco decisiones que tienen que sostenerse
entre sí**. Si una no encaja con las otras cuatro, no hay dirección, hay un moodboard.

| # | Decisión | Dónde está su mecánica |
|---|---|---|
| 1 | **Emparejamiento tipográfico** — qué dos familias y qué papel tiene cada una | `tipografia.md` (T1-T4) |
| 2 | **Temperatura de la paleta** — cálida, fría o neutra, y de dónde sale | `skills/marca` · `imagen.md` §1 |
| 3 | **Metáfora de movimiento** — la frase «esta página se mueve como ___» | `movimiento.md` §1 (T18) |
| 4 | **Tratamiento de imagen** — qué se hace con la foto, o qué la sustituye | `imagen.md` (T21 · §2b) |
| 5 | **Estructura** — el marco narrativo y el orden de bloques | `estructura-de-pagina.md` |

---

## 3. La baraja

### 3a. Con fichero en el corpus — se pueden citar línea a línea

| Dirección | Tipografía | Paleta | Metáfora de movimiento | Imagen | Estructura |
|---|---|---|---|---|---|
| **Zen · Awwwards Edition**<br>`bien/yessmassage-v7.html` | Serif de sistema (Georgia/Palatino) para display + sans de sistema (`:46-48`) | Cálida terrosa: crema `#FDFAF6`, salvia, terracota, arena (`:18-33`) | **Respiración.** `@keyframes breathe` a 3 s (`:228`) + blobs que mutan 16-20 s (`:527,535`) | **Fotos reales del cliente** — la única del corpus (7 ficheros en `img/`) | B2C bienestar: sensación → catálogo → prueba → reserva |
| **Boho Chic Mediterráneo**<br>`bien/kalinayoga-v6.html` | DM Serif Display + DM Sans, con la itálica del display en juego | Cálida costera: terracota `#C67B5C`, arena `#E8D5B7`, azul `#5B8FA8` (`:16-22`) | **La planta que se mece.** `@keyframes floatPlant`, ±2° (`:285`) | Overlay teñido de marca + zoom 1,04-1,06 + composición solapada (`:435-460`, `:641-646`) | Igual que la anterior, con acento por tarjeta (`:553-565`) |
| **Luxury Editorial**<br>`bien/kalinayoga-v4.html` | **Cormorant Garamond + Montserrat** — el contraste más editorial del corpus | Marfil `#FFFFF0`, oro `#C9A96E`, carbón `#2C2C2C`, blush `#E8C4B8` (`:14-23`) | Contenida: zoom lento de fondo, nada más | `aspect-ratio` 3/4 y 1/1, `object-fit:cover` global (`:35`) | Editorial: la imagen manda y el texto la acompaña |
| **Minimal**<br>`bien/elevaiti-v53.html` | Space Grotesk + Inter | Fría sobria: medianoche `#0D1B2A`, blanco `#F8F9FA`, eléctrico | **Aparecer sin ruido.** Es la referencia del motor de reveal (`:92-95`, `:526-527`) | **Sin fotografía.** Rejilla con filete | B2B seis bloques: hero → servicios → resultados → casos → proceso → acción |
| **Premium Minimal**<br>`bien/elevaiti-v2.html` | **Playfair Display + Lato** — serif de alto contraste sobre sans ligera | Blanco `#FAFAFA`, negro `#111`, oro `#C9A84C` (`:22-28`) | Barrido de relleno en los botones (`:300`) + marquesina 30 s (`:599`) | Sin fotografía | **PAS**: problema → solución → prueba → acción. **2.ª del ranking humano** |
| **AI Experience**<br>`bien/elevaiti-v5.html` | Inter + Space Grotesk | Oscura fría: base `#040810`, cian `#00e5ff`, púrpura `#a855f7` (`:23-35`) | **La máquina pensando.** Indicador de escritura, 1,2 s (`:759-768`) | Grano + orbes + rejilla enmascarada (`:335`) | **1.ª del ranking humano.** Demo de producto en el hero (`demo-de-producto.md`) |
| **Interactive Showcase**<br>`bien/elevaiti-v7.html` | **Sora + Inter** | Fría con acentos por tarjeta | **Manipular.** Tarjetas que giran, `perspective:1200px` + `rotateY(180deg)` (`:565-576`) | Sin fotografía | **3.ª del ranking.** Diez bloques con precios y FAQ |
| **DALE · carretera**<br>`bien/dale-marketing-v4/` | Display + sans, con micro-etiqueta muy espaciada (`styles.css:71`) | Oscura con menta | **La carretera.** El nombre del cliente hecho movimiento: líneas que se dibujan desde el horizonte (`script.js:178-181`) y se desplazan al bajar (`:509-511`) | SVG propio (mapa de su red), sin foto | Agencia: hero → quiénes → servicios → casos → red → proceso → prueba → FAQ → acción |
| **Editorial numerada**<br>`bien/consultorpro.html` | Inter en todos los pesos, jerarquía por escala | Pizarra `#223843` + oxblood `#A00505` sobre `#EFF1F3` (`:13-18`) | Mínima. La página convence con estructura, no con movimiento | Sin fotografía | **PAS largo, 13 bloques** con ROI, oferta, garantía y escasez (`estructura-de-pagina.md` §3.3) |
| **Dark editorial** ⚠️<br>`mal/attomo-digital.html` | **Syne + DM Sans** | Negro `#0a0a0a` + naranja `#ff5c00` (`:26-32`) | Nivel premium entero: GSAP, parallax con scrub, cursor propio, botón magnético | Grano + orbes | ⚠️ **Está roto y desplegado**: `initGSAP()` definido y nunca llamado (`:1441`). Se cita por su dirección, **nunca como ejemplo a copiar** |

### 3b. Solo con ficha de galería — nombre y una línea, sin código

No están vendorizadas, así que **no se pueden citar línea a línea**. Sirven como cartas de la baraja,
no como referencia de implementación:

| Dirección | Lo que dice su ficha | Dónde |
|---|---|---|
| **Luxury Spa Premium** | *«Negro · Dorado — Experiencia ultra-premium con partículas doradas»* | `proceso/galeria-designs.html:423` |
| **Dark Tech** | *«Negro + Cyan + Púrpura — Futurista, glassmorphism, neón»* · Space Grotesk | `proceso/galeria-designs.html:607` |
| **Storytelling Journey** | *«Crimson → Navy → Purple → Green — Cinematic narrative, GSAP ScrollTrigger»* · Playfair Display | `proceso/galeria-designs.html:663` |

---

## 4. El aviso que hace falta antes de usar ninguna de estas cartas

**Al menos tres de las diez referencias caen en un *cluster* del «look de IA»** que el skill oficial
`frontend-design` lista como señal de página generada. No es una sospecha: se ve en los tokens.

| Referencia | *Cluster* | La evidencia |
|---|---|---|
| `bien/kalinayoga-v6.html` | **1** — *«warm cream background … high-contrast serif display … terracotta accent (often near #D97757)»* | `--terracotta: #C67B5C` (`:16`) + DM Serif Display + arena `#E8D5B7` |
| `bien/kalinayoga-v4.html` | **1** (variante) | Marfil `#FFFFF0` + Cormorant Garamond + oro `#C9A96E` (`:14-23`) |
| `mal/attomo-digital.html` | **2** — *«near-black background with a single bright acid-green or vermilion accent»* | `--bg:#0a0a0a` + `--accent:#ff5c00` (`:26-30`) |
| `bien/elevaiti-v5.html` | el look de IA, marcado por el propio corpus | `INDEX.json → defectos_conocidos`: *«paleta cian/púrpura, que es de los clusters de "look de IA"»* |

**Cómo se lee esto sin sacar la conclusión equivocada.** El skill oficial lo dice él mismo: *«All
traits are legitimate for some briefs, but they are **defaults rather than choices**, and they appear
regardless of subject»*. Una paleta crema-serif-terracota **para un estudio de yoga mediterráneo es
una decisión defendible**; la misma paleta para una asesoría fiscal es un default que se coló.

**La regla operativa, que ya está en `catalogo-diseno.yaml` (T4) y aquí se aplica a la dirección
entera:**

> **Máximo dos rasgos de los cinco clusters por página, y cada uno justificado por escrito en la
> ficha de la dirección.** Si no puedes escribir por qué este brief pide crema y terracota, es que
> no lo pide.

Y el corolario incómodo: **esta baraja tiene el sesgo dentro.** Son diez diseños de un equipo hechos
con las herramientas de 2026, y arrastran los defaults de su época. Usarla como menú es coger ese
sesgo tal cual.

---

## 5. Quién ordena las direcciones — y quién no

El corpus conserva **a propósito** dos rankings de las mismas versiones, y ordenan distinto:

| Fichero | Quién lo hizo | Qué pasó |
|---|---|---|
| `proceso/RANKING.csv` | **El cliente**, con razones de negocio | Es el que se aplicó |
| `proceso/elevaiti-FINAL-RECOMMENDATION.md` | **La IA**, sobre las mismas versiones | El humano **lo ignoró**: eligió para producción dos versiones que la IA había puesto en su último escalón |

Se conservan los dos porque juntos dicen algo que por separado no se ve: **el auto-ranking de un
agente no sustituye al criterio de quien paga.** El agente genera las direcciones y las enseña; la
que gana la elige una persona, y sus razones son de negocio, no de estética —basta leer el CSV:
*«los productos se pierden»*, *«no deja claro el problema»*, *«prima estética sobre conversión»*—.

Corolario práctico para cualquier agente que use este documento: **propón varias, no recomiendes
una.** Y si te piden una recomendación, dala **con su razón de negocio**, que es lo que se puede
contrastar.

---

## 6. Límites honestos

- **Diez diseños de un equipo y de tres clientes no son un catálogo de direcciones de arte.** Son las
  que hemos hecho. Faltan sectores enteros —industrial, salud, educación, público— y no hay ni una
  dirección para `producto-panel` (`estructura-de-pagina.md` §5).
- **Tres de las nueve cartas no tienen fichero** (§3b): solo nombre y una línea. No se pueden citar
  ni verificar.
- **Los ficheros del corpus tienen defectos reales**, listados en `INDEX.json → defectos_conocidos`.
  Se citan por su tipografía, su paleta y su movimiento; **no por su accesibilidad** — 6 de 9 quitan
  el `outline` sin reponer el foco (GD-12) y solo 2 de 10 tienen bloque de reduced-motion.
- **Las fotos no viajaron con el corpus**: abrir estos ficheros en un navegador los enseña sin
  imágenes (`imagen.md` §4).
- **Nada de esto bloquea nada.** Es canon declarado, medido en un corpus ajeno a este repo, con el
  trato del precedente GAP-1 de `patterns/README.md` §1.

---

## Anti-patterns

- ❌ **Usar esto como menú**: elegir la fila cuyo sector coincide y entregarla → el cliente recibe la
  web de otro, y encima con el sesgo de 2026 dentro (§4).
- ❌ **Proponer una sola dirección** → no hay comparación, así que no hay decisión: hay aprobación.
- ❌ **Proponer tres variaciones de la misma idea** y llamarlas tres direcciones.
- ❌ **Que el agente ordene las direcciones y presente la ganadora** → el corpus guarda la vez que eso
  se hizo y el humano eligió lo contrario (§5).
- ❌ **Entregar la dirección elegida intacta** → la que llega a producción se fusiona con lo mejor de
  las descartadas.
- ❌ **Una dirección cuyas cinco decisiones no se sostienen entre sí** (§2) → eso es un moodboard.
- ❌ **Crema + serif de alto contraste + terracota «porque queda bien»** → es el cluster 1, aparece en
  dos de nuestras propias referencias, y sin justificación escrita es un default, no una elección.
- ❌ **Copiar la dirección de `mal/attomo-digital.html` como ejemplo de implementación** → su
  dirección es buena y su código está roto y desplegado (`movimiento.md` §3.2).
- ❌ **Citar una carta del §3b como si tuviera código detrás** → no lo tiene.
- ❌ **Elegir la dirección antes de tener los activos reales del cliente** → la paleta sale de su web
  o su Instagram, no de esta tabla (`imagen.md` §1).

---

_Doc version: 1.0 · 2026-09-18 · Ola 2. Canon **declarado** (GAP-1): no bloquea. Los nombres salen de
`INDEX.json` y de `proceso/galeria-designs.html`; el §4 mide cuántas de nuestras propias referencias
caen en un cluster del «look de IA», que es la razón de que esto sea una baraja y no un menú._
