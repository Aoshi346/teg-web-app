# Estilos e iconos — patrón de casa

> Capa `estilos` del patrón de casa (Tailwind CSS 4 · lucide-react). El color literal ya lo cubre
> `componentes.md` (`fe-color-por-token`); aquí van las otras tres formas de salirse del sistema de
> diseño sin darse cuenta: el valor a ojo, la clase condicional concatenada y el icono que arrastra
> el catálogo entero.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only estilos`.

## La regla (una frase)

Se estiliza con utilidades de Tailwind sobre los **tokens del tema**, las clases que dependen de una
condición pasan siempre por `cn()`, y cada icono se importa por su nombre.

## Implementación de referencia

**Qué es un token, y dónde vive ahora.** Un **token** es un valor del sistema de diseño con nombre
propio —"el color de fondo de una tarjeta", en vez de un código de color suelto— para poder
cambiarlo en un sitio y que cambie en toda la app. En Tailwind 4 los tokens se declaran **en CSS**,
con la directiva `@theme`, y no en un `tailwind.config.js`; ese fichero ya no hace falta. Cada token
declarado ahí genera además su utilidad: declarar `--color-card` te da `bg-card`, `text-card`,
`border-card`.

> ⚠️ **Los valores no los pone el template.** La paleta, la escala de espaciado y la tipografía son
> de cada proyecto, y aquí no hay ninguna que copiar. **El procedimiento completo —qué preguntas
> responde el sistema de diseño, en qué fichero vive, con qué formato, y qué se hace cuando falta un
> valor— está en [`frontend-design-system.md`](frontend-design-system.md).** Este documento cubre lo
> otro: cómo se escribe el estilo día a día una vez el sistema existe.

```css
/* src/app.css — EL origen de tokens. Los nombres son la forma; los valores, del proyecto. */
@import "tailwindcss";

@theme {
  --color-fg:     <valor del proyecto>;
  --color-card:   <valor del proyecto>;
  --color-border: <valor del proyecto>;
  --radius-card:  <valor del proyecto>;
}
```

**El componente usa utilidades, no CSS propio:**

```tsx
<article className="rounded-xl border border-border bg-card p-5 shadow-sm">
```

En este documento, los nombres de token de los ejemplos (`bg-card`, `text-fg`, `border-border`…)
son **ilustrativos**: enseñan la forma de consumirlos, no un juego de tokens que haya que adoptar.
Cada proyecto nombra los suyos en su documento fundacional.

**El ayudante `cn()`** — `src/lib/cn.ts`. Tres líneas que resuelven un problema real:

```ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

`clsx` monta la lista de clases descartando lo que sea `false`, `null` o `undefined`;
`tailwind-merge` resuelve los choques. **El choque es el motivo de todo esto**, y no es intuitivo:
si en la lista acaban `px-2` y `px-4`, gana la que Tailwind haya escrito **después en la hoja de
estilos**, no la última del texto. Escribir `"px-2 px-4"` no garantiza `px-4`. Con `cn()`, la última
de la lista gana siempre, que es lo que cualquiera espera:

```tsx
export function Button({ variant, className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-lg px-4 py-2 font-medium focus-visible:ring-2 focus-visible:ring-ring',
        variant === 'ghost' && 'bg-transparent text-fg hover:bg-card',
        variant === 'primary' && 'bg-ring text-bg',
        className,
      )}
      {...props}
    />
  );
}
```

Ese `className` al final es lo que hace un componente reutilizable de verdad: quien lo use puede
pasar `className="px-8"` y **gana**, sin `!important` ni pelearse con la especificidad.

**Los iconos, uno a uno:**

```tsx
import { Camera, X } from 'lucide-react';

<Camera aria-hidden="true" />
<button type="button" aria-label="Cerrar"><X aria-hidden="true" /></button>
```

Lucide está publicado como módulos ES, lo que permite al empaquetador hacer **tree-shaking**: quitar
del paquete final todo lo que no se importa. Importando por nombre viajan dos iconos; el paquete
tiene más de 1.700. El `aria-hidden` es de `accesibilidad.md`: un icono decorativo no debe leerse en
voz alta, y uno que es el único contenido de un botón necesita que el botón lleve `aria-label`.

**Cuando el nombre del icono lo decide un dato** (viene de la API, de un CMS, de la base de datos),
la respuesta no es importar el paquete entero: es el mapa de importaciones dinámicas que la propia
librería publica, que carga solo el que toca y cuando toca.

```tsx
const icon = await lucideDynamicIconImports[name]?.();
if (!icon) return <FallbackIcon />;   // el nombre puede no existir: valida siempre
```

**El responsive se escribe de móvil hacia arriba.** Los prefijos de Tailwind (`sm:`, `md:`,
`lg:`…) son `min-width`: la clase sin prefijo es la que vale **siempre**, y cada prefijo la pisa a
partir de su ancho. Por eso la base se escribe para la pantalla pequeña y los prefijos solo añaden
lo que cambia al ensanchar:

```tsx
// ✅ la base es móvil; a partir de md se pasa a dos columnas
<div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6">

// ❌ desktop-first: la base es la excepción y hay que deshacerla hacia abajo
<div className="grid grid-cols-2 gap-6 max-md:grid-cols-1 max-md:gap-4">
```

Las dos pintan lo mismo. La diferencia aparece al añadir la tercera pantalla: en la primera se
suma un prefijo, en la segunda hay que revisar qué se estaba deshaciendo. Y el móvil —el caso más
restringido y casi siempre el más visitado— queda descrito por la clase que **no** lleva prefijo,
que es la que nunca se olvida.

> **Sin comprobación, y por eso no es una regla del catálogo.** `max-md:grid-cols-1` es sintaxis
> válida y a veces la correcta (deshacer un estilo de una librería de terceros, por ejemplo), así
> que un comprobador que marcara todo `max-*:` sería ruido. Queda como default escrito: se sigue
> por convenio, no se bloquea. Es el mismo criterio que el `README.md` del set aplica a las reglas
> que no supieron traer su comprobación — se documentan, no se disfrazan.

**Lo que se anima son `transform` y `opacity`, y nada más.** Cambiar `width`, `height`, `margin`,
`padding` o `top` obliga al navegador a recolocar lo que hay alrededor en **cada** fotograma;
`transform` y `opacity` los resuelve sin volver a medir la maqueta. El movimiento que se ve es el
mismo; el coste, no.

```css
/* ✅ se desplaza y se desvanece: dos propiedades que no recolocan nada */
@keyframes entrar { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

/* ❌ el mismo efecto a ojo, recalculando la posición de los vecinos en cada fotograma */
@keyframes entrar-mal { from { opacity: 0; margin-top: 8px; } to { opacity: 1; margin-top: 0; } }
```

> **Medido en el corpus (2026-08-22).** Los **9** bloques `@keyframes` propios de los dos proyectos
> —5 en `elvion/frontend/src/styles/global.css`, 4 en
> `proxera_musa/frontend/widget/src/styles/widget.css`— animan **solo** dos propiedades:
> `transform` ×18 y `opacity` ×16. Ni una `width`, `height`, `margin` o `padding` dentro de un
> `@keyframes`, y ninguna `transition:` sobre una propiedad de maqueta:
>
> ```bash
> cd .docs/resources/coding
> grep -rnoE "transition[^;]*(width|height|margin|padding|top|left|right|bottom)[^;]*;" \
>      --include='*.css' --include='*.tsx' --include='*.jsx' . | grep -v node_modules
> # → sin salida
> ```
>
> 9 de 9 es dominancia, no preferencia. **Lo que la medida NO cubre**, y por eso se dice: la
> utilidad `transition-all` aparece **35** veces (frente a 76 `transition-colors`, 11
> `transition-opacity`, 11 `transition-shadow`, 7 `transition-transform`), y `transition-all` anima
> *lo que cambie* — incluida la propiedad de maqueta que alguien le añada mañana a ese mismo
> elemento. Nombrar la propiedad cuesta lo mismo que escribir `all`.
>
> Tampoco esta trae comprobador —distinguir la animación cara de la barata exige saber qué genera
> Tailwind con el tema del proyecto, el mismo límite que el checker declara para las clases en
> conflicto—, así que queda como default escrito: se sigue por convenio, no se bloquea.

**El hueco de una imagen lo reserva la caja que la contiene, no los atributos `width`/`height`.**
Una imagen que llega de la red no ocupa nada hasta que carga: si su sitio no estaba reservado, todo
lo que hay debajo salta hacia abajo en cuanto aparece — y si el usuario ya estaba pulsando algo,
pulsa otra cosa. La forma de casa es dar el tamaño **en la clase**, al contenedor o a la propia
`<img>`, para que el hueco exista desde el primer pintado:

```tsx
// ✅ el contenedor tiene la altura; la imagen la rellena, y el marcador de posición ocupa lo mismo
<div className="relative h-28 overflow-hidden bg-muted">
  {src && !imgError
    ? <img src={src} alt={name} className="w-full h-full object-cover" loading="lazy"
           onError={() => setImgError(true)} />
    : <div className="w-full h-full flex items-center justify-center"><ImageOff className="w-8 h-8" /></div>}
</div>

// ❌ sin caja: la fila mide 0 px hasta que la imagen llega, y entonces empuja al resto
<img src={src} alt={name} />
```

> **Medido en el corpus (2026-08-22).** De las **11** `<img>` de código de aplicación (209 ficheros
> `.tsx`/`.jsx` de los tres frontends, sin `node_modules` ni plantillas de informe), **11 llevan la
> caja en la clase** (`h-10 w-10`, `w-full h-full` dentro de un padre con altura, `aspect-*`) y
> **0 llevan `width=`/`height=`**:
>
> ```bash
> cd .docs/resources/coding
> grep -rn --include='*.tsx' --include='*.jsx' -A6 '<img' \
>      elvion/frontend/src proxera_musa/frontend/{admin,widget}/src | grep -c 'width=\|height='
> # → 0
> ```
>
> 11 de 11 es dominancia. Y la clase gana al atributo por una razón que el atributo no puede cubrir:
> **el marcador de posición ocupa el mismo hueco que la imagen** cuando la URL falla o no existe
> (`elvion/frontend/src/components/widget/shared/ProductCard.tsx:33-46`,
> `proxera_musa/frontend/admin/src/pages/Products.tsx:122-131`) — con `width`/`height` en la `<img>`,
> la rama del fallo se queda sin tamaño y el salto vuelve.
>
> **Lo que la medida NO cubre:** `loading="lazy"` sale en **5** de las 11 y no es patrón (por debajo
> del 60% del `README.md` de esta carpeta). Mirando solo las que apuntan a una URL remota dentro de
> una lista o de un chat —donde `lazy` significa algo— son 5 de 9, que sigue sin serlo. Se deja
> dicho como criterio, no como regla: en una imagen que se ve al abrir la pantalla, `lazy` **retrasa**
> justo la que había que pintar primero. Sin comprobador, por lo mismo: saber si una imagen está
> arriba del todo exige renderizar.

## El antipatrón que sustituye

```tsx
// ❌ src/components/panel.tsx
import * as Icons from 'lucide-react';

<div className={`p-[13px] rounded-[7px] ${active ? 'bg-blue-500 px-4' : 'px-2'}`}>
  <Icons.Camera />
</div>
```

- **`import * as Icons`** trae el catálogo entero al ámbito del fichero. El empaquetador ya no puede
  demostrar qué iconos sobran, así que no quita ninguno: más de 1.700 componentes en el paquete
  final por usar uno. Es el fallo más caro de la lista y el más invisible — no rompe nada, solo hace
  la página más lenta para todo el mundo, y no aparece hasta que alguien mira el tamaño del bundle.
- **`p-[13px]`** salta la escala. La escala existe para que los espacios de pantallas distintas
  encajen entre sí; un 13 suelto no encaja con nada, y el siguiente que pase no sabrá si el 13 era
  una decisión de diseño o el resultado de mover el valor hasta que "se veía bien".
- **`px-4` y `px-2` en la misma lista** es el choque de antes: cuál gana depende del orden en que
  Tailwind generó la hoja, no del ternario. Da igual lo que diga el código; funciona por accidente
  hasta el día que deja de funcionar.
- **Concatenar con plantilla** además arrastra `false` y `undefined` al atributo cuando la condición
  no se cumple, y acabas con `class="p-4 undefined"` en el HTML.

Y en las hojas de estilo con ámbito propio:

```css
/* ❌ src/styles/card.module.css */
.card {
  @apply rounded-xl border p-5;
}
```

Un fichero `.module.css` (o el `<style>` de un componente Vue o Svelte) se compila **por separado**
del CSS principal, así que no ve el `@theme`. En Tailwind 4 eso significa que el `@apply` se queda
sin resolver. Se arregla con una línea, `@reference "../app.css";` al principio del fichero — o
mejor, usando la variable directamente (`border-radius: var(--radius-card);`), que no obliga a
Tailwind a procesar el módulo y compila más rápido.

Conviene decir qué **no** es antipatrón: `@apply` en sí. La documentación de Tailwind lo recoge como
herramienta legítima, sobre todo para dar estilo a marcado que no controlas (el de una librería de
terceros). Lo que esta regla persigue es el `@apply` que **no funciona**, no el que existe. Dicho
esto, la preferencia de casa es la utilidad en el marcado: en cuanto se empieza a acumular estilo en
clases propias, vuelve el problema que Tailwind vino a quitar — dos sitios que tocar por cada
cambio, y una hoja de estilos que crece y que nadie se atreve a limpiar.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only estilos
```

| id | estado | qué detecta |
|---|---|---|
| `fe-iconos-tree-shakeable` | activo | `import * as … from 'lucide-react'`, o `import { icons }` (que es el catálogo completo) |
| `fe-escala-de-tailwind` | débil | valor arbitrario en px/rem en una utilidad con escala: `p-*`, `m-*`, `gap-*`, `text-*`, `rounded-*`, `leading-*` |
| `fe-clases-con-helper` | débil | `className={\`…\`}` con una condición dentro, en un fichero que no usa `cn`/`clsx`/`twMerge`/`cva` |
| `fe-apply-con-reference` | débil | `@apply` sin `@reference` en `*.module.css`, `*.vue` o `*.svelte` |
| `fe-origen-de-tokens` | débil | **regla de proyecto** (solo con `--all`): que haya **un** `@theme` y que exista `.docs/core/design-system.md` → [`frontend-design-system.md`](frontend-design-system.md) |

`fe-escala-de-tailwind` deja fuera **a propósito** `w-` y `h-`: un ancho fijo en píxeles (una barra
lateral, el alto de una cabecera) es legítimo con frecuencia, y meterlos convertía la regla en ruido.

`fe-clases-con-helper` mira el fichero entero: basta con que use `cn()` en algún sitio para que deje
de avisar. Es deliberado — la regla busca el fichero que todavía no conoce el ayudante, no auditar
cada línea.

Refuerzo fuera del comprobador, que ve cosas que este no puede:

- **`prettier-plugin-tailwindcss`** ordena las clases siempre igual. No es cosmético: con un orden
  estable, dos personas escribiendo lo mismo producen el mismo texto, y el diff de un cambio de
  estilo se lee.
- **`eslint-plugin-better-tailwindcss`** detecta clases inexistentes y algunos conflictos dentro de
  un mismo atributo, que es lo que el comprobador **no** puede hacer (haría falta conocer las clases
  reales que Tailwind ha generado).
- **La extensión Tailwind CSS IntelliSense** avisa del conflicto mientras escribes, que es cuando
  sale gratis arreglarlo.
- **El tamaño del paquete**, para el caso de los iconos: `vite build` ya imprime el peso de cada
  fragmento, y ahí se ve el salto.

**Lo que no se comprueba y no se puede:** si dos clases de un mismo `className` chocan de verdad hay
que saber qué propiedades CSS toca cada una, y eso solo lo sabe Tailwind después de generar la hoja
—que depende del tema del proyecto—. El comprobador no lo intenta; por eso la regla que existe es
"pasa por `cn()`", que sí es comprobable, en vez de "no tengas clases en conflicto", que no lo es.

## Excepciones legítimas

- **Un valor que viene del diseño y no está en la escala.** Existe: la altura exacta de una cabecera
  fijada por el diseñador, el ancho de un logo. La salida buena no es el valor arbitrario suelto sino
  **añadir el token al `@theme`** y usarlo; si de verdad es de un solo sitio, se exceptúa y se dice.
- **Marcado de terceros que no puedes tocar** (un calendario, un editor enriquecido): ahí `@apply`
  sobre sus clases es la única forma de darle el estilo del sistema.
- **Estilos calculados en ejecución** (una barra de progreso cuyo ancho es un porcentaje): van en
  `style={{ width: `${pct}%` }}`, no en una clase. No es una excepción a nada, es el caso para el que
  existe `style`.
- **Iconos de marca** (logotipos de terceros) que Lucide no tiene: van como SVG propio en
  `src/components/icons/`, no se busca una segunda librería de iconos.

```tsx
// pattern-exempt: fe-escala-de-tailwind — alto exacto de la cabecera fijado por diseño (64px)
```

## Related

- `frontend-stack.md` (por qué Tailwind y por qué lucide-react) · `componentes.md`
  (`fe-color-por-token`: el color literal) · `accesibilidad.md` (el icono decorativo y el
  `aria-label` del botón de solo icono;
  §*El movimiento, apagable en un sitio* — **dónde** se apaga la animación, con su regla
  `fe-movimiento-apagable`. Aquí solo está **qué** se anima)
- `rules/html-output.md` §gotcha de tokens de color — el mismo error, en los informes HTML del repo
