# Sistema de diseño — el procedimiento (los valores son del proyecto)

> **Lee primero el reparto, porque es lo que hace útil este documento:**
> el **template pone el molde y la comprobación**; el **proyecto rellena el molde**. Aquí no hay
> ninguna paleta, ninguna escala y ninguna tipografía de casa — esas decisiones son de cada
> proyecto y no se heredan. Lo que sí es de casa es *cómo* se declaran, *dónde* viven, *cómo* las
> consumen los componentes y *qué se hace cuando falta un valor*.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only estilos --all <src>`.

## La regla (una frase)

Cada proyecto declara su sistema de diseño en **un documento fundacional** y sus valores en **un
único origen de tokens**; ningún componente escribe un color, un espaciado o una tipografía a mano,
y cuando falta un valor **se añade al origen, nunca al componente**.

## Implementación de referencia — el procedimiento, paso a paso

**Qué es un token.** Un valor del sistema de diseño con **nombre propio**: "el color de fondo de una
tarjeta" en vez de un código de color suelto. Sirve para poder cambiarlo en un sitio y que cambie en
toda la app — y, más importante, para que dos personas que necesitan "el gris de los textos
secundarios" acaben usando el mismo gris en lugar de dos parecidos.

Un sistema de diseño vive en **dos artefactos, con dos públicos distintos**. Los dos son
obligatorios y ninguno sustituye al otro:

| Artefacto | Para quién | Qué contiene | Dónde |
|---|---|---|---|
| **El documento fundacional** | personas (diseño, producto, quien entra nuevo, el agente al planificar) | las **decisiones** y el porqué: qué escala, cuántos grises y para qué sirve cada uno, qué se puede y qué no | `.docs/core/design-system.md` |
| **El origen de tokens** | la máquina (Tailwind, el navegador, el comprobador) | los **valores**, en un solo bloque `@theme` | `src/app.css` (o el CSS de entrada del proyecto) |

### Paso 1 — el documento fundacional

Va en **`.docs/core/design-system.md`** y tiene el mismo peso que la `constitution.md` de SpecKit:
es un documento del que el resto depende, no una nota. Por eso vive en la documentación **core** del
proyecto —el punto de entrada único de `rules/plan-docs-structure.md`— y no en un rincón del
frontend: quien decide una paleta no suele ser quien escribe los componentes.

Como es un documento **escrito** (no generado del código), le aplica la regla del core: lleva
`reviewed: YYYY-MM-DD` en el frontmatter, y sin esa fecha el índice lo marca en rojo. No es
burocracia: un sistema de diseño que nadie ha confirmado en dos años ya no describe el producto.

**Las preguntas que el documento tiene que responder** (esta lista sí es de casa; las respuestas, no):

1. **Color** — ¿cuántos colores de marca y qué significa cada uno? ¿Cuántos niveles de gris y para
   qué sirve cada uno (texto principal, texto secundario, borde, fondo)? ¿Hay modo oscuro?
2. **Espaciado** — ¿qué escala? La pregunta real es "¿qué saltos existen y cuáles no", porque es lo
   que evita que aparezcan un 13, un 14 y un 15 en tres pantallas.
3. **Tipografía** — familias, tamaños con su uso (¿cuál es el de un título de sección?), pesos.
4. **Radios, bordes y sombras** — cuántos hay. Suelen ser dos o tres; cuando nadie lo decide, salen ocho.
5. **Estados** — cómo se ve algo deshabilitado, con error, cargando o con el foco puesto.
6. **Lo que NO se hace** — la sección más útil y la que siempre falta: "no usamos sombras para
   jerarquía", "no hay más de dos pesos por pantalla".
7. **Quién decide** — el nombre de quien aprueba un token nuevo, y por dónde se le pide.

**La plantilla no se copia de aquí: se copia del molde del core**, que es el único y trae además el
mínimo innegociable (§0), la tabla de intocables y el apartado de decisiones ya tomadas:

```bash
cp .claude/templates/core/design-system.md .docs/core/design-system.md
```

Que la plantilla viva en **un** sitio no es manía de orden: es la misma regla que este documento
defiende para los tokens, aplicada a sí mismo. Dos moldes parecidos divergen en el primer proyecto
que rellene el que no toca, y entonces hay dos formas de describir un sistema de diseño y ninguna
manda. Aquí quedan **las preguntas**; allí, **el formulario**.

Al terminarlo, `reviewed:` con la fecha de hoy y `reviewed_by:` con quién firma — sin eso el índice
del core lo pinta en rojo, y con razón.

### Paso 2 — el origen de tokens, enchufado a Tailwind

Los valores que decidió el documento se escriben **una vez**, en el bloque `@theme` del CSS de
entrada. En Tailwind 4 la configuración es CSS y no hace falta `tailwind.config.js`. Lo que hace que
esto funcione: **cada token declarado genera su utilidad**, así que declarar `--color-card` te da
`bg-card`, `text-card` y `border-card` sin escribir nada más.

```css
/* src/app.css — EL origen. Los valores salen del documento fundacional, no de aquí. */
@import "tailwindcss";

@theme {
  --color-fg:     <valor del documento>;
  --color-card:   <valor del documento>;
  --color-border: <valor del documento>;
  --radius-card:  <valor del documento>;
}
```

Ese "una vez" es literal: **si hay dos bloques `@theme` en el proyecto, hay dos orígenes**, y a
partir de ahí cambiar un color exige acordarse de los dos. La comprobación lo detecta.

### Paso 2b — los tokens de diseño que Tailwind NO namespacea

El `@theme` cubre color, tipografía, espaciado y radios. Cuando el proyecto declara además
movimiento, imagen y textura (`design-system.md` §4c, §4d, §4e), **parte de esos valores sí tienen
namespace y parte no**, y conviene saber cuáles antes de escribirlos:

| Token | ¿Genera utilidad? | Va en |
|---|---|---|
| `--ease-*` | **Sí** → `ease-soft` | `@theme` |
| `--tracking-*` | **Sí** → `tracking-label` | `@theme` |
| `--aspect-*` | **Sí** → `aspect-retrato` | `@theme` |
| `--shadow-*` | **Sí** → `shadow-1` | `@theme` |
| `--animate-*` | **Sí** → `animate-respirar` | `@theme` |
| **`--dur-*`** | **NO existe ese namespace en Tailwind 4** | `:root` hermano, en el MISMO fichero |
| El grano, y cualquier `url(data:…)` | No | idem |

```css
/* src/app.css — sigue habiendo UN solo fichero que tocar. */
@theme {
  --ease-soft:  cubic-bezier(.25,.46,.45,.94);
  --shadow-1:   0 8px 32px color-mix(in oklab, var(--color-tinta) 12%, transparent);
  --tracking-label: .28em;     /* el máximo MEDIDO en el corpus es .28em, no .45em */
  --aspect-retrato: 3 / 4;
}

/* Lo que no tiene namespace va JUSTO DEBAJO, en el mismo fichero: un :root hermano no cuenta
   como segundo origen para el comprobador, y así no se rompe la regla de «un solo sitio». */
:root {
  --dur-fast: 180ms; --dur-base: 400ms; --dur-reveal: 1400ms;
  --grano: url("data:image/svg+xml,…feTurbulence…");
}
```

> ⚠️ **El punto de erosión, dicho antes de que ocurra.** Como `--dur-*` no genera utilidad, no hay
> una clase obvia que usar, y el primer componente con prisa escribirá `transition: .3s` a mano.
> Ahí empieza la deriva. Dos formas de taparlo, las dos legítimas: declarar los pares completos en
> `--animate-*` (que sí genera utilidad y lleva la duración dentro), o dejar la duración escrita en
> las clases de componente del propio `app.css`. Lo que no vale es fingir que el problema no está.
>
> Comprobado contra la documentación de Tailwind 4 el 2026-09-18: `--ease-*`, `--tracking-*`,
> `--aspect-*`, `--shadow-*` y `--animate-*` son namespaces reales; **`--duration-*` no aparece**.

### Paso 3 — el componente consume, nunca declara

```tsx
// ✅ consume el token por su utilidad
<article className="rounded-card border border-border bg-card p-4 text-fg">

// ✅ cuando de verdad hace falta CSS, la variable — sigue siendo el mismo origen
<div style={{ borderColor: 'var(--color-border)' }} />

// ❌ los tres declaran valor en el componente: se salen del sistema
<div style={{ color: '#6b7280' }} />
<div style={{ background: 'rgb(107, 114, 128)' }} />
<div className="p-[13px]" />
```

### Paso 4 — qué se hace cuando falta un valor (el paso que nadie escribe)

Es el momento en el que un sistema de diseño se rompe, siempre igual: alguien necesita un gris que
no está, tiene prisa, lo escribe en el componente, y a partir de ahí el sistema es una sugerencia.
El procedimiento es corto **a propósito**, porque un procedimiento largo se salta:

1. **Mira si ya existe** algo que sirva. La mayoría de las veces sí: lo que falta no es el valor, es
   saber cuál de los cuatro grises era el de los textos secundarios — y eso lo responde la columna
   "cuándo se usa" del documento.
2. **Si de verdad no existe**, se pide a quien figura como `owner`. No es una ceremonia: es la única
   forma de que la respuesta sea "usa el que ya hay" cuando esa es la respuesta correcta.
3. **Se añade al origen**: fila en el documento (token, valor, cuándo se usa) y línea en el
   `@theme`. En ese orden — el documento primero, porque la fila que explica *cuándo se usa* es lo
   que evita el siguiente token duplicado.
4. **Solo entonces** se usa en el componente.
5. **Si hay que entregar hoy** y no hay a quién preguntar: se escribe el valor en el componente
   **con la exención puesta y con fecha**, y eso deja rastro. Un valor suelto sin marca es
   invisible; uno con `pattern-exempt` sale en la próxima búsqueda y se puede saldar.

## Gotcha: un token con triplete HSL no es un color (P0 en elvion)

Si el token guarda tres números sueltos, el formato de shadcn (`--primary: 215 28% 17%;`), **solo
vale dentro de `hsl()`**. Usado a pelo —`style={{ color: 'var(--primary)' }}` o `color: var(--primary)`—
la declaración es inválida, el navegador la descarta **sin error en consola** y el color sale
transparente o heredado. Lo detectaron Vera e Ignacio a la vez en elvion (`improvements_tl.md:73-82`).

```tsx
<p style={{ color: 'var(--primary)' }}>…</p>        // ❌ transparente
<p style={{ color: 'hsl(var(--primary))' }}>…</p>   // ✅
```

Lo marca `gate_diseno.py` (GD-13, en sombra) en CSS, `style=""` y objetos `style` de JSX, leyendo el
valor del token en todo el barrido. Si el proyecto guarda los tokens como color entero (`oklch()`,
`#hex`, el `@theme` de Tailwind 4), el problema no existe.

## El antipatrón que sustituye

```tsx
// ❌ src/components/UserCard.tsx
<div style={{ background: '#fafafa', border: '1px solid #e5e5e5', padding: 13 }}>
  <span style={{ color: 'rgb(153, 153, 153)', fontSize: 13 }}>Hace 2 horas</span>
</div>
```

```css
/* ❌ y en otro sitio del repo, un segundo origen */
/* src/styles/theme.css */
@theme { --color-border: #e0e0e0; }
```

- **El gris de `#999`** no es *el* gris de los textos secundarios: es uno parecido. Al lado de una
  tarjeta que usa el bueno, se ve. Y cuando se ajuste el sistema, este no se entera.
- **`padding: 13`** no encaja con ningún otro espacio de la app. Nadie sabe si el 13 era una
  decisión o el resultado de mover el número hasta que "se veía bien", así que nadie se atreve a
  tocarlo.
- **Los dos orígenes con dos bordes distintos** son el fallo caro: el cambio de marca se aplica en
  uno, el otro se queda, y la incoherencia aparece semanas después en una pantalla que nadie tocó.
- **Y el problema de fondo**: aquí no hay sistema que romper porque nunca se escribió cuál era. Sin
  el documento, "usa el token" no es una instrucción — es un reproche.

## Cómo se comprueba

```bash
# La regla de proyecto necesita ver el árbol entero: va con --all
python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src --only estilos
python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src --only componentes
```

| id | estado | ámbito | qué detecta |
|---|---|---|---|
| `fe-color-por-token` | activo | fichero | color literal en un componente: `#hex`, `rgb()`, `rgba()`, `hsl()`, `hsla()` con números |
| `fe-escala-de-tailwind` | débil | fichero | valor arbitrario en px/rem donde hay escala (`p-*`, `m-*`, `gap-*`, `text-*`, `rounded-*`, `leading-*`) |
| `fe-origen-de-tokens` | débil | **proyecto** | que exista **un** bloque `@theme` (ni cero ni dos) y que exista `.docs/core/design-system.md` |

`fe-color-por-token` **no marca `rgb(var(--color-brand))`**: eso es consumir el token, que es
justo lo que se pide. Solo marca la función con números literales dentro. Los ficheros de tokens y
tema están excluidos por ruta — es donde los valores *deben* estar.

**`fe-origen-de-tokens` avisa, no falla en seco**, y su mensaje dice **qué crear**:

```
⚠ [débil] <raíz>:1 — el proyecto no tiene un origen de tokens único y declarado
   no hay ningún bloque @theme en el árbol escaneado — CREA src/app.css con
   `@import "tailwindcss";` y un bloque `@theme { … }` con los tokens del proyecto
   fix: … describe el sistema en .docs/core/design-system.md (plantilla en
        stack/frontend-design-system.md)
```

Es la única regla del catálogo frontend que **no juzga un fichero sino el conjunto**, y por eso solo
corre con `--all`: desde un diff de dos ficheros no se puede afirmar que al proyecto le falta algo,
y hacerlo daría un aviso falso en cada commit hasta que alguien desactivara la regla.

**Lo que NO se comprueba, y conviene decirlo porque es bastante:**

- **Que los valores del `@theme` sean los del documento.** Habría que parsear la tabla en markdown y
  cruzarla con el CSS. Es factible y no está hecho; hoy la coherencia entre los dos artefactos es
  responsabilidad de quien añade el token siguiendo el paso 4.
- **Que el documento esté relleno.** La regla comprueba que el fichero **existe**, no que tenga
  contenido: un `design-system.md` con la plantilla en blanco pasa. Quien mira eso es el índice del
  core, que lo marcará `sin fecha` en rojo si nadie puso `reviewed:`.
- **Si un gris nuevo es realmente distinto del que ya había.** Es criterio, no sintaxis, y es
  exactamente el trabajo del `owner` en el paso 4.
- **El contraste de lo que se pinta de verdad.** Las parejas declaradas sí se miden sin navegador
  (`scripts/contraste.py --tokens design-system.md`, y GD-14 cuando una regla declara texto y fondo);
  lo heredado y lo compuesto encima solo se ve ejecutando: `contraste.py --dom <url>` y axe
  (`scripts/auditar_a11y.py`, `accesibilidad.md`).

## Excepciones legítimas

- **Marcado de terceros con su propia paleta** (un widget de pago, un mapa) que exige colores
  concretos para funcionar o por contrato de marca.
- **Ilustraciones, logotipos y gráficos** donde el color *es* el contenido: la serie de un gráfico o
  el rojo de una marca ajena no son tokens del sistema. Si el proyecto tiene varias, el sitio
  correcto es una paleta de datos **en el propio origen**, no repartida por los componentes.
- **Un valor calculado en ejecución** (el ancho de una barra de progreso) va en `style`, y no es una
  excepción a nada: es para lo que existe `style`.
- **Entrega urgente sin `owner` disponible** — paso 4.5. Con fecha, para que se pueda saldar.

```tsx
// pattern-exempt: fe-color-por-token — colores de marca del proveedor de pago, fijados por su
// guía; no son tokens nuestros (2026-01-15)
```

Una excepción sin razón escrita no es una excepción, es el sistema de diseño deshaciéndose despacio.

## Related

- `estilos.md` (Tailwind al escribir: `cn()`, utilidades, iconos) · `componentes.md`
  (`fe-color-por-token`) · `accesibilidad.md` (el contraste, que solo se ve ejecutando)
- `rules/plan-docs-structure.md` §`.docs/core/` — por qué el documento vive ahí y qué significa
  `reviewed:` · `rules/adr.md` (si la decisión es cara de revertir, además lleva ADR)
- **`.claude/templates/core/design-system.md`** — el molde que se copia (capa 6 del core, registrado
  en `templates/core/core.json`); `.specify/memory/constitution.md` es su precedente: un documento
  fundacional al que el resto obedece
- `frontend-stack.md` §componentes de UI — quién consume estos tokens: los componentes copiados al
  repo (patrón shadcn), que por eso pueden rebrandearse enteros
