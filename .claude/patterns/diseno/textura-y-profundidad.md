# Textura y profundidad — la capa semántica, las sombras teñidas y el grano

> **Cuándo aplicar:** al montar el sistema de tokens de un proyecto (fase 1 de
> `rules/motores-de-diseno.md` Parte F, skill `marca`) y cada vez que haya que decidir **cómo se separa un
> elemento de su fondo**: borde, sombra, elevación, textura. Es la capa que hace que dos pantallas
> hechas por personas distintas parezcan del mismo producto.
>
> **NO aplicar:** para **dónde viven** los tokens, qué preguntas responde el documento fundacional
> y qué comprueba el linter — eso es `patterns/stack/frontend-design-system.md` y manda él · para
> **contraste y accesibilidad** (`aitor-a11y-auditor`, y GD-12 en
> `resources/referencias-diseno/anti-patrones.yaml`) · para **qué se mueve y cuándo**
> (`movimiento.md`) · para el **tratamiento de fotografía** (`imagen.md`).
>
> **Relacionado:** `patterns/diseno/README.md` (por qué esto no bloquea) ·
> `patterns/stack/frontend-design-system.md` (el molde) · `composicion.md` (las formas que
> consumen estos tokens) · `agents/shared/red-flags.sh` §R4 · `resources/referencias-diseno/`.

---

## La capa semántica de tokens — el suelo de todo lo demás

**Qué es.** Los tokens van en **dos niveles**: los valores crudos con nombre de color, y encima una
capa que los nombra **por su papel**. Los componentes consumen **solo** la segunda.

```css
/* 1. crudos — el nombre dice qué color es */
--terracotta:   #C5A55A;
--dark:         #2D2420;

/* 2. semánticos — el nombre dice para qué sirve */
--surface:      var(--cream);
--text-primary: var(--dark);
--accent:       var(--terracotta);
--accent-hover: var(--terracotta-dk);
```
`resources/referencias-diseno/bien/yessmassage-v7.html:18-43` (crudos `:19-34`, semánticos `:36-43`)

**Por qué los dos niveles y no uno.** Con un solo nivel, cambiar el color de acento obliga a buscar
`--terracotta` por todo el proyecto y decidir caso por caso si esa aparición es «el acento» o «ese
color concreto». Con la capa semántica, se cambia **una línea**. Y el segundo beneficio es el que
de verdad se nota con más de una persona: `--accent` no se puede usar mal, porque su nombre dice
para qué es.

Esta capa **no tiene número de técnica** a propósito: su procedimiento —dónde vive el
documento fundacional, qué preguntas responde, qué comprueba el linter— es de
`patterns/stack/frontend-design-system.md`, y manda él. Aquí está solo porque es el suelo sobre el
que se apoyan T5, T5b, T6 y T8.

El corpus lo hace con **seis familias de token** (`bien/yessmassage-v7.html:18-81`), y es una buena
lista de comprobación de qué falta en un sistema a medias:

| Familia | Anclas | Qué pasa si falta |
|---|---|---|
| Color crudo | `:19-34` | Nada: es lo único que nunca falta |
| **Color semántico** | `:36-43` | Cada componente elige su gris y salen cuatro grises distintos |
| Tipografía | `:46-48` | Familias escritas a mano en cada componente |
| Espaciado | `:51-58` (4 → 128 px) | Aparecen un 13, un 14 y un 15 en tres pantallas |
| Radios | `:61-65` (8/16/28/48/full) | Salen ocho radios donde debía haber tres |
| **Sombras** | `:68-72` | Ver abajo — es la que más se improvisa |
| **Easing y duración** | `:75-80` | Ver abajo |

> ⚠️ **Y el corpus enseña también cómo se rompe esto.** En ese mismo fichero: `:28` declara
> `--rose: #5a922d`, que **es un verde** (el nombre miente sobre el valor, semilla de **GD-04**);
> `:37` declara `--bg: var(--beige)` y **`--beige:` no se define en ninguna parte**; y `:40` pone
> `--text-muted: #e8e8e8` —casi blanco— sobre fondo crema, que después hubo que parchear con dos
> bloques de `!important` llamados «CONTRAST FIXES» (`:2931`, `:2990`, semilla de **GD-03**).
>
> **La lección no es «los tokens son buenos».** Es que **una capa semántica con nombres mentirosos
> es peor que no tenerla**: propaga el error a todos los componentes de golpe y lo hace ilegible
> de leer. Un token de color se comprueba contra su valor cuando se escribe, no cuando se parchea.

---

## T5 · Las sombras se tiñen con el oscuro de marca, nunca con negro puro

**La regla.** El color de la sombra es el **oscuro de la marca** con opacidad baja, no `rgba(0,0,0,…)`.

```css
--shadow-sm:   0 2px 12px  rgba(45,36,32,0.06);   /* 45,36,32 = --dark: #2D2420 */
--shadow-md:   0 8px 32px  rgba(45,36,32,0.10);
--shadow-lg:   0 20px 60px rgba(45,36,32,0.12);
--shadow-warm: 0 8px 40px  rgba(197,165,90,0.20); /* sombra de acento, para lo destacado */
```
`bien/yessmassage-v7.html:68-72`

**Por qué**, y es una razón física, no de gusto: una sombra negra sobre un fondo cálido introduce un
color que **no está en la paleta**, así que la sombra **ensucia** el fondo — se ve gris sucio bajo
crema. Teñida con el oscuro de marca, la sombra **es** el fondo en oscuro, así que se funde con él.
El mismo elemento parece mejor recortado con menos opacidad.

**Tres proyectos, tres tintes distintos, la misma regla** — y cada uno tiñe con SU oscuro:

| Ancla | Sombra | Teñida con |
|---|---|---|
| `bien/yessmassage-v7.html:69` | `0 8px 32px rgba(45,36,32,0.10)` | `--dark: #2D2420`, su marrón |
| `bien/elevaiti-v53.html:71` | `0 4px 20px rgba(13,27,42,.06)` | su azul medianoche |
| `bien/consultorpro.html:96` | `0 4px 20px rgba(160,5,5,0.35)` | su rojo *oxblood* |

Que el tercero use **0.35** de opacidad y los otros 0.06-0.10 no es incoherencia: un tinte rojo
saturado necesita menos luz para leerse que uno neutro. Lo que se mantiene es **de dónde sale el
color**, no el número.

**Y está medido en el conjunto**, que es lo que le da peso:

```bash
# 10 ficheros del corpus: total de box-shadow vs. los que usan negro puro
grep -c "box-shadow" <fichero>
grep -cE "box-shadow:[^;]*(rgba\( *0 *, *0 *, *0|#000\b)" <fichero>
```

> **134 declaraciones de `box-shadow` · 7 en negro puro → 94,8 % teñidas.**

Las siete excepciones están en cuatro ficheros (`elevaiti-v5`, `elevaiti-v7`, `yessmassage-v7` ×3,
`dale-marketing-v4/styles.css`, `attomo-digital`); ninguna es una decisión declarada, todas parecen
descuidos sueltos.

**Ya está cableado como red flag:** `agents/shared/red-flags.sh:115` —
`── [R4] Sombra en negro puro (debería teñirse con el oscuro de marca) ──`. Y lleva escrito arriba
(`:104-113`) por qué esa regla **decía lo contrario** hasta el 2026-09-18: pedía sombras de ≥2
capas, que es literalmente el kit de tarjeta SaaS que `frontend-design:42` lista como señal de IA.
*«Un red flag que empuja hacia lo genérico no es un red flag.»*

**Límite honesto:** 94,8 % sobre **nuestro** corpus no es dominancia en el sentido de
`patterns/README.md` §1 — son diez ficheros de un solo equipo. Es una regla **declarada**
(`README.md` §2), y por eso R4 avisa y no bloquea.

**Dónde no aplica:** en modo oscuro una sombra teñida con el oscuro de marca es invisible sobre el
fondo. Ahí la separación la da el **borde** o un cambio de superficie, no la sombra — y eso lleva a
la sección de abajo.

---

## T5b · Easing y duración también son tokens

Es la familia que casi nadie declara, y la que más deriva: cada componente acaba con su propia
curva y su propio tiempo, así que la app se mueve de seis maneras.

```css
--ease-out:   cubic-bezier(0.16, 1, 0.3, 1);        /* salida rápida, frenada larga */
--ease-inout: cubic-bezier(0.65, 0, 0.35, 1);       /* simétrica: ida y vuelta */
--ease-zen:   cubic-bezier(0.25, 0.46, 0.45, 0.94); /* la de este proyecto: muy suave */
--dur-slow:   1.2s;
--dur-med:    0.7s;
--dur-fast:   0.35s;
```
`bien/yessmassage-v7.html:75-80`

> **Su ficha es `movimiento.md`, no esta.** El catálogo (`catalogo-diseno.yaml`, T5b) enruta T5b
> allí, y con razón: aquí se declara que **son tokens**; allí se decide **qué se mueve y cuándo**.
> Si los dos documentos dijeran cosas distintas, manda `movimiento.md`.

**El dato que lo convierte en patrón y no en gusto:** **dos diseños sin relación llegaron al mismo
valor** — `cubic-bezier(.16, 1, .3, 1)` en `bien/yessmassage-v7.html:75` y en
`bien/dale-marketing-v4/styles.css:31`. Es lo más parecido a dominancia que hay en este corpus. El
tercero declara los suyos igual pero distintos (`bien/elevaiti-v53.html:22`:
`--ease:cubic-bezier(0.4,0,0.2,1);--t:0.28s`), que es exactamente lo que debe pasar: **lo común es
declararlos; el valor es de cada proyecto.**

**Lo que enseña este bloque concreto:** `--ease-zen` **tiene nombre de proyecto**, no de función.
Es correcto y es la idea entera de T5 aplicada al movimiento — el proyecto declara *su* curva y
todo el producto se mueve con ella. Un sistema que solo tiene `ease` y `ease-in-out` no ha decidido
cómo se mueve: ha aceptado los valores por defecto del navegador.

**Los tres tiempos bastan**, y la escala del corpus (0.35 / 0.7 / 1.2 s) es una buena referencia:
lo rápido es respuesta a un clic, lo medio es un cambio de estado, lo lento es atmósfera. Cuatro
duraciones ya es una más de las que nadie recuerda.

**Qué NO arregla:** declarar los tokens no hace que se usen. `movimiento.md` cubre el otro lado —y
el bloque `prefers-reduced-motion` no es opcional: sin él es **GD-05**, que dos referencias del
corpus incumplen.

---

## T6 · Acento por tarjeta vía custom property *(anécdota: 1 solo diseño)*

**Qué es.** Una sola clase de tarjeta, y el color lo inyecta el **contenedor** con una custom
property. Nada de `.card--azul`, `.card--olive`, `.card--arena`.

```css
.pillar-card::before { background: var(--pillar-color, var(--terracotta)); height: 3px;
                       transform: scaleX(0); transform-origin: left; }
.pillar-card:hover::before { transform: scaleX(1); }

.pillar-card:nth-child(1) { --pillar-color: var(--terracotta); }
.pillar-card:nth-child(2) { --pillar-color: var(--azul); }
.pillar-card:nth-child(3) { --pillar-color: var(--olive); }
.pillar-card:nth-child(4) { --pillar-color: var(--arena); }
```
`bien/kalinayoga-v6.html:550-564`

> **Estado en el catálogo: `anecdota`**, con **un único precedente**
> (`bien/kalinayoga-v6.html:553`). Eso no lo invalida —la técnica es buena y el razonamiento de
> abajo se sostiene solo— pero sí prohíbe presentarla como «así se hace en esta casa». Un diseño no
> es un patrón, y `scripts/verificar_precedentes.py` lo comprueba.

**Las tres cosas que lo hacen bueno:**

1. **El valor por defecto va en el `var()`** — `var(--pillar-color, var(--terracotta))`. Una tarjeta
   sin color asignado **no se queda sin filete**: cae al acento de marca. Es lo contrario del fallo
   habitual, donde la quinta tarjeta aparece sin adorno y nadie sabe por qué.
2. **Una sola regla de estilo, N colores.** Añadir una tarjeta es añadir un `nth-child`, no una
   clase modificadora con su bloque.
3. **Los colores vienen de la paleta**, no son literales: `var(--azul)`, `var(--olive)`. La custom
   property es un canal, no un sitio donde escribir un color nuevo.

**El detalle que casi siempre se hace mal:** la sombra del hover de esa misma tarjeta
(`:558`) es `rgba(46,40,32,0.1)` — **teñida**, coherente con la regla de arriba, dentro del mismo
componente. La incoherencia típica es un acento cuidadísimo con una sombra negra debajo.

**Coste.** `nth-child` ata el color **al orden del marcado**. Si las tarjetas se reordenan o se
filtran, los colores bailan. Cuando el orden puede cambiar, la propiedad se pone en el elemento
(`style="--pillar-color:var(--azul)"`) o desde el dato, no con `nth-child`.

---

## T8 · El grano

**Qué es.** Una capa fija a pantalla completa con ruido generado por SVG en `data:` URI, a opacidad
muy baja. Quita el aspecto «plano de pantalla» de los fondos grandes de color sólido.

```css
.grain::after {
  content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 9998;
  background: url("data:image/svg+xml,…%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E…opacity='0.04'…");
}
```
`mal/attomo-digital.html:117-123`

**No es cosa de un solo fichero**, y conviene decirlo porque el ancla más vistosa está en el
diseño marcado como `mal/`: el mismo grano en `data:` URI aparece en
`bien/elevaiti-v5.html:200` y en `bien/dale-marketing-v4/styles.css:351`, los tres con el mismo
`viewBox='0 0 256 256'`. Tres diseños distintos: es patrón, no anécdota.

Y la variante **animada**, solo en attomo: `mal/attomo-digital.html:97` define `.noise` con
`opacity:.028`, `baseFrequency='0.75'`, `inset:-50%` a `200%` de tamaño, y la desplaza con
`@keyframes noiseAnim` en `steps(10)` cada 8 s (`:100-112`).

**Los cuatro valores que importan:**

| | Medido | Si te pasas |
|---|---|---|
| Opacidad | **.028 – .04** | Por encima de .06 se ve el ruido y parece un JPEG malo |
| `baseFrequency` | **0.75 – 0.9** | Por debajo de 0.4 salen manchas, no grano |
| `pointer-events` | **`none`**, obligatorio | Una capa fija a pantalla completa se come todos los clics |
| `z-index` | 9998-9999 | Va encima de todo, por eso el punto anterior no es opcional |

**Por qué SVG inline y no una imagen:** no hay petición de red, no hay fichero que se pierda al
copiar el proyecto, y **escala sin pesar** — la textura se genera en el cliente. Es la misma razón
por la que los informes del harness van autocontenidos (`rules/html-output.md`).

**Cuándo NO usarlo.** Sobre fondo claro casi no se ve y el coste no se paga; sobre fotografía se
suma al ruido de la foto. Su caso es el **fondo oscuro grande y liso**, que es donde está medido.

**El coste que no se ve en el diseño:** la variante **animada** (`.noise`) repinta una capa del
doble del viewport diez veces por ciclo, indefinidamente. En un portátil modesto es ventilador. La
versión estática (`.grain::after`) da el 90 % del efecto por el 0 % del coste; usa la animada solo
si el movimiento del grano **es** la idea, y entonces lleva `prefers-reduced-motion` como todo lo
demás.

---

## Cuándo borde y cuándo sombra

La pregunta se hace mal casi siempre: no es «¿cuál queda mejor?», es **«¿qué estoy diciendo?»**.

| Estoy diciendo… | Recurso | Ancla |
|---|---|---|
| Esto está **delante** de lo otro: se ha levantado (menú abierto, diálogo, tarjeta arrastrada) | **Sombra**, y el tamaño de la sombra dice cuánto se ha levantado | `bien/yessmassage-v7.html:68-70` (12 → 32 → 60 px de desenfoque) |
| Esto es **otra cosa** que lo de al lado: hay un límite, no una altura | **Borde** de 1 px | `bien/elevaiti-v53.html:71` (`border:1px solid var(--gray-100)`) |
| Estas celdas son **piezas de una misma tabla** | **Ni borde ni sombra**: `gap` sobre fondo teñido | `bien/elevaiti-v53.html:118` (`composicion.md` T10) |
| Esto **reacciona** a que lo señales | Sombra que **cambia**, no que aparece | `bien/kalinayoga-v6.html:558` |

**Tres reglas prácticas que salen de ahí:**

1. **Una escala de sombra, tres escalones.** `sm`/`md`/`lg` con desenfoque creciente y opacidad
   creciente (`:68-70`: 0.06 → 0.10 → 0.12). Si hacen falta cinco, es que la sombra está haciendo
   trabajo que le toca al espaciado.
2. **Borde y sombra a la vez es casi siempre un descuido.** Está diciendo dos cosas —«soy otra
   cosa» y «estoy levantado»— y normalmente solo una es verdad. La excepción legítima es el modo
   oscuro, donde la sombra no se ve y el borde es lo único que separa.
3. **La misma sombra idéntica bajo cada tarjeta es el kit SaaS** que `frontend-design:42` lista
   como señal de IA: *«content chopped into identical rounded cards, one border-radius on
   everything regardless of hierarchy, the same soft grey shadow under each»*. Si todo lleva la
   misma sombra, la sombra ya no informa de nada — es papel pintado. Que la jerarquía elija el
   escalón.

---

## Anti-patterns

- ❌ Sombra en `rgba(0,0,0,…)` o `#000` → ensucia el fondo; se tiñe con el oscuro de marca
  (`agents/shared/red-flags.sh:115`, R4).
- ❌ Sombras multicapa «premium» bajo cada tarjeta → es el kit SaaS de `frontend-design:42`, y es
  justo lo que R4 **dejó de premiar** el 2026-09-18.
- ❌ La misma sombra bajo todo → deja de informar de jerarquía.
- ❌ Borde **y** sombra en el mismo elemento fuera de modo oscuro → dos afirmaciones, una falsa.
- ❌ Un token de color cuyo **nombre miente** sobre su valor (`--rose: #5a922d`, GD-04) → la capa
  semántica propaga el error a todo el producto de golpe.
- ❌ Un token semántico que apunta a otro **que no existe** (`--bg: var(--beige)`,
  `bien/yessmassage-v7.html:37`) → falla en silencio, cae al valor heredado.
- ❌ Arreglar un token mal elegido con un bloque de `!important` llamado «CONTRAST FIXES»
  (`:2931`, `:2990`) → es GD-03, y el problema estaba tres capas más arriba.
- ❌ Componentes que consumen tokens **crudos** (`var(--terracotta)`) en vez de semánticos
  (`var(--accent)`) → cambiar el acento vuelve a ser buscar y reemplazar.
- ❌ No declarar tokens de easing ni de duración → cada componente inventa su curva y la app se
  mueve de seis maneras.
- ❌ Más de tres duraciones o más de tres escalones de sombra → nadie los recuerda y se eligen a
  ojo.
- ❌ Acento por tarjeta con clases modificadoras (`.card--azul`) en vez de una custom property.
- ❌ Custom property de acento **sin valor por defecto** en el `var()` → la tarjeta que nadie
  asignó sale sin filete y parece un bug.
- ❌ Atar el color al `nth-child` cuando las tarjetas se pueden **reordenar o filtrar** → los
  colores bailan.
- ❌ Grano a opacidad > .06 → se ve el ruido y parece un JPEG malo.
- ❌ Capa de grano o de ruido **sin `pointer-events:none`** → se come todos los clics de la página.
- ❌ Grano **animado** por defecto → repinta el doble del viewport en bucle; la versión estática da
  casi todo el efecto sin coste.
- ❌ Grano sobre fondo claro o sobre fotografía → no se ve, o se suma al ruido de la foto.

---

_Versión 1.0 · 2026-09-18 · Ola 2. Anclas verificadas con `grep -n` contra
`resources/referencias-diseno/` el 2026-09-18. El 94,8 % de sombras teñidas sale de los dos
comandos escritos en el documento, sobre los 10 ficheros del corpus (134 declaraciones, 7 en negro
puro)._
