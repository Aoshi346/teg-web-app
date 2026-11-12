# Estructura de página — en qué orden van los bloques, y por qué ese orden convence

> **Cuándo aplicar:** al decidir **qué bloques lleva una página y en qué orden**, antes de maquetar
> nada: una web de cliente nueva, un rediseño que no convierte, o el momento de decidir si sobra una
> sección. También al revisar una página existente que «está bien hecha» y no funciona — casi
> siempre es el orden.
>
> **NO aplicar:** para **escribir el texto** de esos bloques — titular, subtítulo, llamada a la
> acción, la oferta que los sostiene: eso es la skill **`escribir-copy`**, que es la dueña del texto,
> y este documento no la duplica ni la contradice · para **cómo se ve** cada bloque
> (`catalogo-direcciones.md`, `composicion.md`) · para **qué pantallas** necesita el producto, que es
> una decisión anterior (`skills/producto`) · para **puntuar** la conversión de algo ya construido
> (`conrado-cro-auditor`) · para el **flujo entre pantallas** de una aplicación (`/visual-map`).
>
> **Relacionado:** `skills/escribir-copy` (el texto y la oferta) ·
> `resources/referencias-diseno/proceso/RANKING.csv` (el veredicto humano, que es la mejor evidencia
> de este documento) · `demo-de-producto.md` (qué va en el hero de un B2B) · `imagen.md` §3 (dónde
> va el retrato) · `catalogo-direcciones.md` · `conrado-cro-auditor`.

---

## 1. El orden es un argumento, no un índice

Una página no es una lista de secciones: es **una conversación en la que solo habla uno**. Cada
bloque tiene que contestar la pregunta que el anterior dejó abierta en la cabeza de quien lee. Si el
orden se rompe, el texto puede ser perfecto y la página no convence.

**La prueba de que esto no es teoría está en el corpus**, y no la escribimos nosotros: la escribió
el cliente al ordenar nueve versiones de su propia web
(`resources/referencias-diseno/proceso/RANKING.csv`). Sus razones, literales:

| Puesto | Versión | Lo que dijo |
|---|---|---|
| **2.º** | V2 | *«Construye un recorrido lógico de venta (**problema → solución → prueba → acción**), lo cual es clave para convertir»* |
| 6.º | V1 | *«Visualmente potente y llamativa 👉 Pero falla en negocio: los productos se pierden, **no conecta problema → solución**»* |
| 5.º | Home | *«Se entiende qué se vende 👉 Pero: **no deja claro el problema** → reduce conversión»* |
| 8.º | V3 | *«Diseño muy potente y diferencial 👉 Pero: **prima estética sobre conversión**»* |

Cuatro de nueve juicios hablan del **orden**, y los tres que bajan de puesto lo hacen por lo mismo:
la página no monta el problema antes de vender la solución. La versión visualmente más potente
quedó **sexta**. Eso es lo más cerca de una medición que hay en este canon sobre estructura, y la
tomó quien paga.

> ⚠️ **Y el matiz que impide leerlo como una fórmula:** la que ganó (**V5**) fue elegida por
> *«claridad de la oferta… **no tiene un storytelling**, pero comunica bien el producto»*. O sea: el
> recorrido narrativo es lo que rescató al segundo puesto, **no** lo que dio el primero. El primero
> lo dio **enseñar el producto funcionando** (`demo-de-producto.md`). El orden importa; no es lo
> único que importa.

---

## 2. Los tres marcos, en cristiano

No son tres cosas distintas: son tres formas de ordenar la misma conversación. Se elige **uno** y se
respeta; mezclarlos produce una página que repite la misma promesa cuatro veces.

| Marco | El recorrido | Cuándo encaja |
|---|---|---|
| **AIDA** | Atención → Interés → Deseo → Acción | Quien llega ya sabe que tiene el problema y está comparando. Lo más común en servicios locales |
| **PAS** (o **PAIDA**) | **Problema → Agitación → Solución** | Quien llega **no sabe** que tiene un problema, o no sabe lo que le cuesta. Es el marco de la V2 del ranking |
| **StoryBrand** | El cliente es el héroe; nosotros somos el guía que le da un plan | Servicios profesionales y consultoría, donde lo que se compra es confianza en una persona |

**La regla de elección, que es la única que hace falta recordar:**

> **¿Quien llega sabe ya que tiene este problema?**
> Sí → **AIDA**: vas directo a la oferta y a la prueba.
> No → **PAS**: primero le enseñas el problema, y hasta que no lo vea no le vendes nada.

**La «agitación» de PAS no es dramatizar.** Es poner números y consecuencias concretas a un problema
que la persona ya tiene pero no ha contado nunca. Si hay que exagerar para que duela, el marco
equivocado es PAS: esa persona no tiene el problema.

---

## 3. Los dos recorridos medidos en el corpus

Sacados con un comando sobre los ficheros, no de memoria:

```bash
cd .claude/resources/referencias-diseno
grep -noE '<section[^>]*(id|class)="[^"]*"' bien/yessmassage-v7.html
```

### 3.1 Bienestar / servicio local (B2C) — `yessmassage-v7`

`hero` :3105 → `experience` :3236 → `services` :3407 → `stats` :3633 → `about` :3664 →
`zen-garden` :3802 → `testimonials` :3858 → `gallery` :4043 → `blog` :4197 → **`booking` :4274**

Lo que hace bien y conviene copiar:

- **La sensación va antes que el catálogo.** `experience` precede a `services`: primero se cuenta
  cómo se va a sentir, después qué se compra. En bienestar se vende lo primero.
- **El retrato está a media página** (`about` :3664, con `gaby.jpg` en :3670 — `imagen.md` §3), justo
  después de los números y justo antes de los testimonios. Es donde la confianza se convierte en
  persona.
- **La acción está al final y es una sola**: reservar. No hay tres llamadas distintas compitiendo.
- **`gallery` y `blog` son opcionales y van después de la prueba social**: si se quitan, la página
  sigue funcionando. Ese es el test de un bloque opcional.

### 3.2 B2B / servicios profesionales — `elevaiti-v53` y `elevaiti-v7`

El más limpio, seis bloques (`bien/elevaiti-v53.html`):

`hero` :261 → `servicios` :306 → **`resultados` :337** → `casos` :362 → `proceso` :404 → `contacto` :468

El completo, diez (`bien/elevaiti-v7.html`):

`hero` :1749 → `servicios` :1859 → `soluciones` :2013 → `resultados` :2241 → `proceso` :2345 →
`precios` :2395 → `clientes` :2505 → `tech` :2667 → `faq` :2694 → `contacto` :2812

Y el de agencia con el mismo esqueleto (`bien/dale-marketing-v4/index.html`):

`hero` :81 → `quienes` :197 → `servicios` :229 → `casos` :342 → `red` :472 → `proceso` :629 →
`testimonios` :691 → `nosotros` :742 → `faq` :792 → `contacto` :893

**La forma común de los tres**, que es el patrón real:

```
hero → qué hacemos → PRUEBA (números · casos · clientes) → CÓMO trabajamos → precio → objeciones → acción
```

Dos decisiones que se repiten en los tres y que no son obvias:

1. **La prueba va antes que el proceso.** Primero *«funciona»*, después *«así lo hacemos»*. Al revés
   se está explicando el método a alguien que aún no cree en el resultado.
2. **El FAQ es el bloque de objeciones y va justo antes de la acción** (`elevaiti-v7:2694` antes de
   `:2812`; `dale:792` antes de `:893`). No es documentación: es el sitio donde se responde lo que
   frena a alguien que ya está casi convencido.

### 3.3 El caso largo — `consultorpro`

Trece bloques, y es el único del corpus con recorrido **PAS explícito**:

`hero` :1207 → `quien-soy` :1245 → **`problema` :1302 → `solucion` :1345** → `director` :1436 →
`roi` :1489 → `proceso` :1554 → `oferta` :1677 → `garantia` :1837 → `escasez` :1887 →
`testimonios` :1938 → `faq` :2005 → `contacto` :2044

Aporta tres bloques que los demás no tienen y que valen para cualquier oferta de ticket alto:
**`roi`** (qué recupera), **`garantia`** (qué pasa si no funciona) y **`oferta`** separada del
precio (:1677, con el desglose *«Setup + Sistema + Formación + Soporte»*).

> ⚠️ **Y su bloque `escasez` (:1887) es el aviso.** GD-08 de
> `resources/referencias-diseno/anti-patrones.yaml` lo marca: *«solo 7 plazas» es aceptable
> **únicamente si es verdad***. Un bloque de escasez con un contador que se reinicia al recargar es
> mentir en la página del cliente, y se nota en dos cargas.

---

## 4. Qué hace cada bloque, y cuál se puede quitar

| Bloque | La pregunta que contesta | ¿Prescindible? |
|---|---|---|
| **Hero** | ¿Qué es esto y es para mí? | Nunca |
| **Problema / agitación** | ¿Esto me pasa a mí? | Solo si quien llega ya lo sabe (§2) |
| **Servicios / solución** | ¿Qué vendes exactamente? | Nunca |
| **Prueba** (números · casos · clientes) | ¿Le ha funcionado a alguien? | Nunca. Es lo que más se salta y lo que más pesa |
| **Cómo trabajamos** | ¿Qué me va a pasar si digo que sí? | Se puede fundir con servicios si el proceso es simple |
| **Quién está detrás** | ¿Me fío de esta persona? | En negocio pequeño y en consultoría, **no** |
| **Precio / oferta** | ¿Cuánto? | Ocultarlo **cuesta conversión**: el 3.º del ranking cayó, entre otras cosas, por apoyarse en el resultado sin construir contexto |
| **Garantía** | ¿Qué pasa si sale mal? | Sí, salvo ticket alto |
| **Objeciones (FAQ)** | Sí, pero… | Sí, y entonces esas objeciones hay que responderlas en otro sitio |
| **Acción** | ¿Y ahora qué hago? | Nunca. **Una sola**, y repetida, no cinco distintas |
| **Galería / blog** | — | Sí. Van después de la prueba y se caen sin que se note |

**El test de un bloque:** tápalo y lee la página seguida. Si no se echa de menos, sobra. Si el salto
chirría, ese bloque estaba contestando algo.

---

## 5. Perfil `producto-panel` — el app-shell, declarado y **sin precedente**

Aquí hay que parar y decirlo antes de dar ninguna recomendación:

```bash
cd .claude/resources/referencias-diseno
grep -rn 'class="sidebar\|<aside' bien/ mal/ | wc -l    # → 0
```

**Cero.** No hay ni un `<aside>` ni una barra lateral en las diez referencias. La única entrada que
`INDEX.json` marca como `producto-panel` es `consultorpro`, y su estructura (§3.3) es una página de
venta larga, no una aplicación. **Este canon no tiene evidencia sobre paneles.** Lo que sigue es
criterio de casa y se lee como tal.

| Zona | Qué lleva |
|---|---|
| **Navegación** | Lateral cuando hay más de ~5 destinos, superior cuando hay menos. **Siempre visible dónde estoy** |
| **Cabecera de contenido** | Dónde estoy · la acción principal de esta pantalla, arriba a la derecha · el filtro que se usa siempre |
| **Cuerpo** | **Densidad alta**: en una herramienta de trabajo, menos espacio en blanco que en una web. Se usa ocho horas al día, no ocho segundos |
| **Estado vacío** | **Una invitación a actuar, nunca un «no hay datos»** |

Dos cosas que no se heredan de la web de cliente y son las que más se equivocan:

- **El espaciado generoso de una landing es un defecto en un panel.** Una tabla de 40 filas con el
  aire de un hero obliga a desplazarse para ver diez.
- **Movimiento nivel 0** (`movimiento.md` §2): solo lo que responde a una acción. Sin reveals al
  bajar, sin scroll suavizado, sin cursor propio — los tres están prohibidos en este perfil.

**El estado vacío es el bloque con más retorno de un panel**, y lo dice también el skill oficial
`frontend-design`: *«An empty screen is an invitation to act»*. Lleva tres cosas: qué va a aparecer
aquí, por qué está vacío ahora, y **el botón que lo llena**. Lo audita `lidia-naive-tester`.

---

## 6. Límites honestos

- **La evidencia de este documento es el orden de secciones de cinco ficheros y un CSV de nueve
  filas.** Es la mejor que hay y es poca. El CSV, además, es de **un solo cliente ordenando su
  propia web**: vale mucho como criterio de negocio y nada como estadística.
- **Sobre `producto-panel` no hay ninguna evidencia** (§5). Está escrito como criterio y marcado.
- **Nada de esto se puede comprobar con un script.** El orden correcto depende de a quién le hablas,
  y eso no está en el HTML. Lo audita `conrado-cro-auditor`, que puntúa; este documento decide.
- **El texto no es de aquí.** Si al escribir un bloque aparece la duda de *qué decir*, el documento
  es `skills/escribir-copy` y la lista de palabras prohibidas es
  `templates/anti-ai-writing-style.md`. Un buen orden con texto de relleno no convence a nadie.

---

## Anti-patterns

- ❌ **Vender la solución antes de que la persona vea el problema** → es la razón literal por la que
  dos versiones bajaron de puesto en el ranking humano.
- ❌ **Mezclar AIDA, PAS y StoryBrand** en la misma página → la promesa se repite cuatro veces con
  palabras distintas y la página se hace larga sin avanzar.
- ❌ **Poner el proceso antes que la prueba** → explicas el método a quien todavía no cree en el
  resultado.
- ❌ **Cinco llamadas a la acción distintas** («reserva», «escríbenos», «descarga», «suscríbete»,
  «pide presupuesto») → cada una divide la atención. Una, repetida.
- ❌ **Esconder el precio** por defecto. Si no se puede publicar, se publica el **rango** o el
  criterio; el silencio se lee como «caro y opaco».
- ❌ **Un bloque de escasez que no es verdad** (GD-08) → se cae en dos recargas y se lleva la
  credibilidad de la página entera.
- ❌ **Retrato del fundador en el hero**, desplazando la propuesta de valor (`imagen.md` §3).
- ❌ **Añadir secciones porque la página «se ve corta»** → el test es taparlas, no medirlas.
- ❌ **Tratar el FAQ como documentación** en vez de como el bloque de objeciones que va antes de la
  acción.
- ❌ **Llevar el espaciado de una landing a un panel** → 40 filas con aire de hero se convierten en
  diez visibles.
- ❌ **Un estado vacío que dice «no hay datos»** y nada más.
- ❌ **Presentar el app-shell del §5 como patrón de la casa** → no hay ni un panel en el corpus.
- ❌ **Escribir el copy aquí** en vez de en `skills/escribir-copy`.

---

_Doc version: 1.0 · 2026-09-18 · Ola 2. Canon **declarado**, no medido en este repo y que **no
bloquea** (GAP-1). Su evidencia más fuerte no es código: es `proceso/RANKING.csv`, el orden que hizo
un cliente sobre nueve versiones de su propia web, con sus razones escritas._
