# Imagen — los activos reales primero, el tratamiento después

> **Cuándo aplicar:** al decidir **qué fotografía lleva una pantalla y cómo se trata**: el fondo de
> un hero, las tarjetas de un catálogo de servicios, el retrato de quien está detrás del negocio, o
> el momento de pedirle material al cliente. Cubre las dos mitades: de **dónde sale** la imagen
> (§1, la que decide el resultado) y **qué se le hace** una vez está (§2).
>
> **NO aplicar:** para el **color de marca** y cómo se declara (`skills/marca` y
> `patterns/stack/frontend-design-system.md`) · para el **grano, los orbes y las rejillas
> enmascaradas**, que son textura generada y no fotografía (`textura-y-profundidad.md`) · para la
> **animación** de esa imagen más allá del hover (`movimiento.md`) · para el **peso** de los
> ficheros y su efecto en Core Web Vitals, que es `bruno-perf-cop` · para el **texto alternativo**
> como criterio de accesibilidad, que es `aitor-a11y-auditor`.
>
> **Relacionado:** `catalogo-diseno.yaml` (T21, con sus precedentes) · `skills/marca` (de dónde sale
> la paleta que tiñe el overlay) · `resources/referencias-diseno/INDEX.json` ·
> `catalogo-direcciones.md` (cada dirección lleva su tratamiento de imagen) · `estructura-de-pagina.md`.

---

## 1. Los activos reales — la palanca que no depende de nosotros

**La regla, sin adornos: el color sale de la web o del Instagram del cliente, las fotos son suyas,
los servicios y los horarios son los que tiene, y el logo se redibuja de su JPG. Nada se inventa.**

No es una preferencia estética. Es la diferencia entre una página que es de alguien y una página
que podría ser de cualquiera. Todo lo demás de este canon —los tokens, el easing, la rejilla— sube
el **acabado**; esto sube la **pertenencia**, y sin ella el resultado es algo pulido y genérico, que
es exactamente el fallo que este canon existe para arreglar.

### Lo que dice la medición, incluido lo que nos deja mal

Contado el 2026-09-18 sobre los diez ficheros del corpus:

```bash
cd .claude/resources/referencias-diseno
for f in bien/*.html bien/dale-marketing-v4/index.html mal/*.html; do
  printf "%-40s stock=%-4s propias=%s\n" "$f" "$(grep -c unsplash "$f")" \
    "$(grep -oE 'src="[^"h][^"]*\.(jpg|png|webp|avif|jpeg)"' "$f" | wc -l)"
done
```

| Fichero | Fotos de banco | Fotos propias |
|---|---:|---:|
| `bien/yessmassage-v7.html` | 0 | **7** |
| `bien/kalinayoga-v6.html` | **21** | 0 |
| `bien/kalinayoga-v4.html` | **15** | 0 |
| Los otros siete | 0 | 0 |

**Uno de diez.** `yessmassage-v7` es el único diseño del corpus con fotografía real del cliente:
seis servicios (`img/svc-*.jpg`) y un retrato (`img/gaby.jpg`). Los dos de yoga tiran de **36 fotos
de banco** entre los dos, y los siete restantes **no tienen fotografía en absoluto** — resuelven con
degradados, SVG, grano y formas.

Esa tabla es el argumento entero de este apartado, y hay que leerla en las dos direcciones:

1. **A favor de la regla:** el único diseño que consiguió activos reales es también el único que
   tiene un retrato de la persona del negocio, y eso no se puede fingir con un banco de imágenes.
2. **En contra de nuestra disciplina:** la regla **no se cumplió en nueve de diez casos**. Así que
   esto no es «así trabajamos», es «esto es lo que falta», y conviene decirlo así en vez de
   presentarlo como una costumbre de la casa que no existe.

### Qué se pide, cuándo y cómo

Se pide **al arrancar** —en la fase de marca, antes de maquetar nada—, porque conseguir material
tarda días y el diseño no puede esperar a la segunda ronda para descubrir que no hay fotos.

| Qué se pide | Para qué | Si no lo hay |
|---|---|---|
| **Su web o su Instagram actual** | De ahí salen el color y el tono reales. Es lo más barato de conseguir y lo que más cambia el resultado | Se pregunta por dos o tres marcas que le gusten y se declara que el color es **propuesta**, no herencia |
| **Fotos del sitio, del equipo y del trabajo** | Son las que nadie más tiene | §2b: composición sin fotografía, **no** banco de imágenes por defecto |
| **Un retrato de quien está detrás** | §3. En un negocio pequeño, es la prueba social | Se deja el hueco **declarado y vacío** en el diseño, con su medida, para que entre después sin rehacer nada |
| **Servicios, precios y horarios reales** | Es contenido, y el contenido decide cuánto espacio necesita cada bloque | Se marca **«sin datos»** (`rules/plan-gates.md` Gate E), nunca un precio plausible |
| **El logo en la mejor calidad que tenga**, aunque sea un JPG | Se **redibuja** en vector a partir de él | Se propone marca denominativa con la tipografía de la dirección elegida, y se dice que es provisional |

**Lo que no se hace nunca**, y esto sí es no negociable: **inventar un dato del negocio para que el
diseño quede bien.** Un precio de ejemplo, un horario verosímil, un testimonio redactado por
nosotros o un contador de plazas que no cuenta nada (GD-08,
`resources/referencias-diseno/anti-patrones.yaml`) dejan de ser una maqueta en el momento en que
alguien los aprueba sin leerlos, y acaban publicados.

---

## 2. El tratamiento (T21) — cuatro decisiones, en este orden

Cuando ya hay foto —propia o, con su aviso, de banco—, el tratamiento del corpus es consistente y
se reduce a cuatro cosas.

### 2.1 Overlay teñido con el color de marca, no con negro

```css
/* resources/referencias-diseno/bien/kalinayoga-v6.html:261-268 — el hero */
.hero-bg::after {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg,
    rgba(46,40,32,0.62) 0%,      /* su oscuro de marca, no #000 */
    rgba(91,143,168,0.25) 60%,   /* y su azul, que reaparece aquí */
    …);
}
```

```css
/* resources/referencias-diseno/bien/kalinayoga-v6.html:641-646 — la tarjeta */
.service-img-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(46,40,32,0.5) 0%, transparent 60%);
}
```

Dos usos distintos y la misma idea: **el velo lleva el color de la marca dentro**. Un
`rgba(0,0,0,.5)` apaga la foto y la ensucia; el oscuro de marca la **funde con el resto de la
página**. Es exactamente el mismo criterio que hace que las sombras vayan teñidas (T5,
`textura-y-profundidad.md`) y por la misma razón.

El de la tarjeta tiene además una decisión que conviene copiar: va **de abajo a arriba y se disuelve
al 60 %**, así que oscurece solo donde va el texto y deja la imagen limpia arriba.

### 2.2 `aspect-ratio` fijo, siempre

Nunca se deja que la foto decida el alto de su caja. Las proporciones medidas en el corpus, con su
uso:

| Proporción | Para qué | Dónde |
|---|---|---|
| **3/4** vertical | Retrato, imagen principal de un bloque «sobre mí» | `bien/kalinayoga-v6.html:437` · `bien/kalinayoga-v4.html:710` |
| **4/5** vertical | Retrato de persona, algo menos alargado | `bien/yessmassage-v7.html:3669` |
| **4/3** apaisado | Imagen de apoyo, secundaria | `bien/kalinayoga-v6.html:454` |
| **16/9** y **16/10** | Bloques anchos, galería | `bien/kalinayoga-v6.html:634,745,847` |
| **1/1** | Rejilla de miniaturas | `bien/kalinayoga-v6.html:750` · `bien/kalinayoga-v4.html:831` |

Y el acompañamiento obligatorio, que es de una línea y evita el 90 % de los problemas:

```css
/* resources/referencias-diseno/bien/kalinayoga-v4.html:35 */
img { display: block; width: 100%; object-fit: cover; }
```

`object-fit: cover` es lo que permite fijar la proporción sin deformar a nadie. Sin él, `aspect-ratio`
estira las caras.

### 2.3 Zoom contenido al hover

**Entre 1,03 y 1,06. Nunca 1,1.** Medido en las siete apariciones del corpus:

| Escala | Elemento | Duración | Dónde |
|---|---|---|---|
| `1.03` | Imagen del hero | — | `bien/kalinayoga-v4.html:307` |
| `1.04` | Imagen de «sobre mí» | 0,8 s | `bien/kalinayoga-v4.html:517` · `bien/kalinayoga-v6.html:445-447` |
| `1.06` | Tarjeta de servicio | 0,7 s | `bien/kalinayoga-v4.html:622` · `bien/kalinayoga-v6.html:638-639` |

La duración larga (0,7-0,8 s) es deliberada y es la excepción declarada del §10 de `movimiento.md`:
un zoom de foto a 200 ms se siente brusco; a 700 ms se siente caro. Por encima de `1.06` el recorte
empieza a comerse la composición y se nota que la caja no cambia de tamaño.

**El caso aparte es el zoom lento de fondo:** `bien/kalinayoga-v6.html:258-259` deja el hero en
`scale(1.05)` con `transition: transform 12s ease`. Eso ya no responde a nadie: es ambiente, y le
aplica lo del §7 de `movimiento.md` — una sola cosa así por página, y apagada con reduced-motion.

### 2.4 Composición solapada: dos imágenes que se pisan

La única técnica de este documento que **compensa la falta de una foto espectacular con
composición**, y por eso es la más útil cuando el material es normalito:

```css
/* resources/referencias-diseno/bien/kalinayoga-v6.html:435-460 */
.about-img-main   { width: 75%; aspect-ratio: 3/4; overflow: hidden; }
.about-img-accent { position: absolute; bottom: -2rem; right: 0;
                    width: 50%; aspect-ratio: 4/3;
                    border: 5px solid var(--cotton);        /* el borde la despega */
                    box-shadow: 0 12px 40px rgba(46,40,32,0.15); }
```

Las tres decisiones que la hacen funcionar: **proporciones distintas** (3/4 contra 4/3, para que no
parezcan dos versiones de lo mismo), **anchos que no suman 100 %** (75 % + 50 % = solape real), y un
**borde del color del fondo** en la de encima, que es lo que la separa de la de debajo sin necesidad
de sombra dura.

---

## 2b. Cuando no hay fotos: componer, no rellenar con banco de imágenes

**Es el caso mayoritario, y el corpus lo demuestra: siete de diez diseños no tienen ni una
fotografía.** Y son buenos. Así que la respuesta por defecto a «no hay fotos» no es Unsplash: es
resolver la página sin fotografía, que además es más barato y envejece mejor.

Lo que usan esos siete, cada uno con su ficha en otro documento:

| En vez de foto | Qué es | Dónde está su ficha |
|---|---|---|
| Rejilla enmascarada + orbes difuminados | Profundidad de hero sin imagen (T9) | `composicion.md` |
| Grano con `feTurbulence` en un data-uri | Textura, cero peticiones (T8) | `textura-y-profundidad.md` |
| SVG propio del negocio | La carretera de DALE, el mapa de Europa de su red | `movimiento.md` §1 |
| La demo del producto | Para B2B, gana a cualquier ilustración (T22) | `demo-de-producto.md` |
| Formas orgánicas y ondas | Blobs que mutan (T19) | `composicion.md` |

**Si aun así hay que usar banco de imágenes**, se hace con las tres condiciones que hacen que no
cante: **una sola fuente y un solo tratamiento** (el mismo overlay teñido en todas), **nada de
personas sonriendo a cámara en una oficina**, y **se declara en la entrega** que esas fotos son
provisionales y a cambiar. Declararlo es lo que impide que se queden tres años.

---

## 3. El retrato de quien está detrás

En un negocio pequeño es el activo de mayor efecto y el más fácil de conseguir: lo tiene el cliente
en el móvil.

```html
<!-- resources/referencias-diseno/bien/yessmassage-v7.html:3669-3670 -->
<div class="about-image" style="border-radius:20px;overflow:hidden;aspect-ratio:4/5">
  <img src="img/gaby.jpg" alt="Gaby - Yess Massage"
       style="width:100%;height:100%;object-fit:cover;display:block" loading="lazy"/>
</div>
```

Cuatro cosas bien hechas en dos líneas: **proporción fija 4/5**, **`object-fit:cover`**,
**`loading="lazy"`** (está por debajo del pliegue) y un **`alt` con el nombre real de la persona y
del negocio** — no «foto del equipo».

**Dónde va:** en el bloque «quién soy / sobre nosotros», que en las dos estructuras del corpus cae
a media página (`estructura-de-pagina.md`). No en el hero: un retrato en el hero sustituye a la
propuesta de valor, y la propuesta de valor va primero.

> **El hueco declarado:** de los diez diseños, **uno** tiene retrato. Es la carencia más repetida y
> la más barata de arreglar, y por eso está aquí en vez de en una lista de deseos.

---

## 4. Límites honestos

- **Las fotos del corpus no viajan.** El `README.md` de `resources/referencias-diseno/` lo dice: se
  vendorizó solo HTML/CSS/JS. Abiertos en un navegador, estos ficheros salen **sin imágenes**. Se
  citan por **cómo tratan** la imagen —proporción, overlay, zoom, composición—, nunca por cómo se
  ven las fotos, que no están.
- **Nada de esto se puede comprobar hoy.** Que una foto sea del cliente y no de un banco no lo puede
  decidir ningún script: `grep unsplash` caza el caso fácil y no caza un JPG de banco descargado a
  `img/`. Es **criterio**, y lo verifica una persona al entregar.
- **Lo único mecánico es el recuento de arriba**, y solo distingue «de banco enlazado» de «local».
- **La regla de los activos reales no está medida en nuestro favor** (§1). Se escribe porque es la
  palanca, no porque la cumplamos.

---

## Anti-patterns

- ❌ **Inventar un dato del negocio** —un precio, un horario, un testimonio, un contador de plazas—
  para que el diseño quede completo. Acaba publicado. Lo que falta se marca **«sin datos»**.
- ❌ **Ir a un banco de imágenes por defecto** cuando no hay fotos → siete de diez referencias
  resuelven sin ninguna fotografía y son buenas (§2b).
- ❌ **Mezclar fotos de banco con fotos del cliente sin unificar el tratamiento** → se ve el corte a
  la primera, y lo que canta es la diferencia de temperatura, no la calidad.
- ❌ **Overlay con `rgba(0,0,0,.5)`** → apaga y ensucia. El velo lleva el oscuro de marca dentro.
- ❌ **Foto sin `aspect-ratio`** → el alto de la caja lo decide el fichero, y el bloque salta cuando
  el cliente cambia la imagen. Además es desplazamiento de diseño y lo penaliza `bruno-perf-cop`.
- ❌ **`aspect-ratio` sin `object-fit: cover`** → estira las caras.
- ❌ **Zoom al hover de 1,1 o más** → el recorte se come la composición. El corpus va de 1,03 a 1,06.
- ❌ **Dos imágenes solapadas con la misma proporción** → parecen dos versiones de la misma foto en
  vez de una composición.
- ❌ **Retrato del fundador en el hero**, desplazando la propuesta de valor.
- ❌ **`alt` decorativo** («imagen», «foto del equipo») en una foto que lleva información. Si la
  imagen es puro adorno, `alt=""` y `aria-hidden` — como hace el corpus con sus SVG de fondo.
- ❌ **Citar estas referencias por sus fotos** → las fotos no están en el corpus (§4).

---

_Doc version: 1.0 · 2026-09-18 · Ola 2. Canon **declarado**, no medido en este repo, y que **no
bloquea** (precedente GAP-1 de `patterns/README.md` §1). §1 se escribe sabiendo que el propio corpus
la incumple en nueve de diez casos: es la palanca que falta, no la costumbre que hay._
