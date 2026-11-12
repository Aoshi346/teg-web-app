# Reglas de interfaz a nivel de código (Vercel Web Interface Guidelines, fijadas)

> Traídas de `vercel-labs/web-interface-guidelines@434b7f9` (MIT, Copyright (c) 2025 Vercel Labs;
> licencia leída en el `LICENSE` de ese commit el 2026-10-31), vía la copia de fitapp
> (su comando `web-interface-guidelines`, T-065, 15-10). **No se actualizan solas**: la skill
> oficial de Vercel las baja de `main` en cada uso; aquí no. Para subir de commit: leer el diff del
> repo, reaplicar los parches y cambiar el sha de esta línea (`rules/vendoring.md` §Actualizar).
>
> **Parches de casa**, marcados en el texto: traducción al castellano (3.65) y las 3 adaptaciones de
> fitapp a ES/CA, marcadas **(ES/CA)**: comillas, mayúsculas y persona. Las reglas que son WCAG son
> un **linter previo**: el veredicto de accesibilidad es de Aitor (`aitor-a11y-auditor`).

Se leen los ficheros del cambio y se comprueban contra estas reglas. Salida corta, por fichero, con
`fichero:línea` (§Formato, al final).

## Accesibilidad

- Botones de solo icono: `aria-label`
- Controles de formulario: `<label>` o `aria-label`
- Elementos interactivos: manejadores de teclado (`onKeyDown`/`onKeyUp`)
- `<button>` para acciones, `<a>`/`<Link>` para navegar (nunca `<div onClick>`)
- Imágenes con `alt` (o `alt=""` si son decorativas)
- Iconos decorativos: `aria-hidden="true"`
- Actualizaciones asíncronas (toasts, validación): `aria-live="polite"`
- HTML semántico (`<button>`, `<a>`, `<label>`, `<table>`) antes que ARIA
- Encabezados jerárquicos `<h1>`–`<h6>`; enlace de salto al contenido principal
- `scroll-margin-top` en las anclas de los encabezados
- Medios con significado: subtítulos, transcripción o descripción, según toque
- Controles de medios usables con teclado; los medios decorativos, ocultos a la tecnología de apoyo

## Estados de foco

- Foco visible en todo lo interactivo: `focus-visible:ring-*` o equivalente
- Nunca `outline-none` / `outline: none` sin un foco que lo sustituya
- `:focus-visible` mejor que `:focus` (sin anillo al hacer clic)
- Foco de grupo con `:focus-within` en controles compuestos
- Cabeceras, pies o capas fijas no tapan el elemento con foco

## Formularios

- Campos con `autocomplete` y un `name` con sentido
- `type` correcto (`email`, `tel`, `url`, `number`) e `inputmode`
- Nunca bloquear el pegado (`onPaste` + `preventDefault`)
- Etiquetas clicables (`htmlFor` o envolviendo el control)
- Sin corrector en emails, códigos y nombres de usuario (`spellCheck={false}`)
- Casillas y radios: etiqueta y control comparten la zona de clic (sin huecos muertos)
- El botón de enviar sigue activo hasta que empieza la petición; spinner durante la petición
- Errores en línea junto al campo; al enviar, foco en el primer error
- Los placeholders terminan en `…` y enseñan un ejemplo del formato
- `autocomplete="off"` en campos que no son de acceso, para no disparar el gestor de contraseñas
- Avisar antes de salir con cambios sin guardar (`beforeunload` o guarda del router)

## Animación

- Respetar `prefers-reduced-motion` (variante reducida o desactivar)
- Animar solo `transform`/`opacity` (lo que va por el compositor)
- Nunca `transition: all`: listar las propiedades
- `transform-origin` correcto
- SVG: transformaciones en un `<g>` envoltorio con `transform-box: fill-box; transform-origin: center`
- Animaciones interrumpibles: responden a la entrada del usuario a mitad
- Movimiento automático de más de 5 s junto a otro contenido: control para pausar, parar u ocultar
- Bucles decorativos silenciados: se paran con `prefers-reduced-motion`

## Tipografía

- `…`, no `...`
- **(ES/CA)** Comillas tipográficas, nunca `"` recta: en ES/CA `«` `»` (y `“` `”` dentro de ellas); en EN `“` `”`
- Espacios de no separación: `10&nbsp;MB`, `⌘&nbsp;K`, nombres de marca
- Estados de carga terminan en `…`: «Cargando…», «Guardando…»
- `font-variant-numeric: tabular-nums` en columnas de cifras y comparaciones
- `text-wrap: balance` o `text-pretty` en encabezados (evita viudas)

## Contenido

- Los contenedores de texto aguantan texto largo: `truncate`, `line-clamp-*` o `break-words`
- Los hijos flex necesitan `min-w-0` para poder truncar
- Estados vacíos tratados: nada roto con cadenas o listas vacías
- Contenido del usuario: prever entradas cortas, medias y muy largas

## Imágenes

- `<img>` con `width` y `height` explícitos (evita CLS)
- Bajo el pliegue: `loading="lazy"`
- Críticas sobre el pliegue: `priority` o `fetchpriority="high"`

## Rendimiento

- Listas grandes (>50 elementos): virtualizar (`virtua`, `content-visibility: auto`)
- Sin lecturas de layout en el render (`getBoundingClientRect`, `offsetHeight`, `offsetWidth`, `scrollTop`)
- Lecturas y escrituras del DOM agrupadas, sin intercalar
- Mejor campos no controlados; los controlados, baratos por pulsación
- `<link rel="preconnect">` para los dominios de CDN y recursos
- Fuentes críticas: `<link rel="preload" as="font">` con `font-display: swap`
- Mejor `<video autoplay muted loop playsinline>` que un GIF animado; con alternativa fija
- Bucles cortos no esenciales: fuente MP4 H.264 en `<picture>` para Safari, condición `prefers-reduced-motion` y fallback fijo

## Navegación y estado

- La URL refleja el estado: filtros, pestañas, paginación y paneles abiertos en query params
- Enlaces con `<a>`/`<Link>` (Cmd/Ctrl+clic y clic central)
- Todo lo que tiene estado se puede enlazar (si usa `useState`, valorar sincronizar con la URL, p. ej. nuqs)
- Acciones destructivas con modal de confirmación o ventana de deshacer, nunca inmediatas

## Táctil e interacción

- `touch-action: manipulation` (sin retraso de zoom por doble toque)
- `-webkit-tap-highlight-color` puesto a propósito
- `overscroll-behavior: contain` en modales, cajones y hojas
- Rebote de la página: `overscroll-behavior: none` en `<html>` dentro de `@media (pointer: fine)`; en puntero grueso, el comportamiento por defecto (tirar para recargar). Probar dispositivos híbridos: `pointer` describe la entrada principal, y `none` también corta el encadenado de scroll y el gesto nativo de navegar
- Al arrastrar: sin selección de texto, `inert` en lo arrastrado
- Gestos de arrastrar, deslizar, pellizcar o trazar: alternativa con toque/clic y con teclado, salvo que sean esenciales
- `autoFocus` con mesura: solo escritorio y un único campo principal; en móvil, no

## Zonas seguras y maquetación

- Maquetas a sangre: `env(safe-area-inset-*)` para las muescas
- Sin barras de scroll no deseadas: `overflow-x-hidden` en contenedores y arreglar el desbordamiento
- Flex/grid antes que medir con JS

## Modo oscuro y temas

- `color-scheme: dark` en `<html>` para temas oscuros (arregla scrollbar y campos)
- `<meta name="theme-color">` igual al fondo de la página
- `<select>` nativo: `background-color` y `color` explícitos (modo oscuro de Windows)

## Idioma y locale

- Fechas y horas: `Intl.DateTimeFormat`, no formatos a mano
- Números y moneda: `Intl.NumberFormat`, no formatos a mano
- El idioma por `Accept-Language` / `navigator.languages`, no por la IP
- Nombres de marca, tokens de código e identificadores: `translate="no"` para que la traducción automática no los rompa

## Hidratación

- Campos con `value` necesitan `onChange` (o `defaultValue` si no son controlados)
- Fechas y horas: protegerse del desajuste servidor/cliente
- `suppressHydrationWarning` solo donde de verdad haga falta

## Hover y estados interactivos

- Botones y enlaces con estado `hover:` (respuesta visual)
- Los estados interactivos suben el contraste: hover/active/focus más marcados que el reposo

## Contenido y copy

- Voz activa: «Instala la CLI», no «La CLI será instalada»
- **(ES/CA)** Mayúscula solo en la primera palabra de encabezados y botones (lo correcto en ES/CA, y el estilo de casa también en EN), nunca Title Case
- Cifras para los recuentos: «8 despliegues», no «ocho»
- Etiquetas de botón concretas: «Guardar la clave de API», no «Continuar»
- Los mensajes de error dicen cómo arreglarlo o qué hacer después, no solo el problema
- **(ES/CA)** Segunda persona (el «tú» informal en ES/CA, salvo que el proyecto declare «usted»); evitar la primera persona
- `&` en vez de «y» donde falte espacio

## Anti-patrones (marcarlos siempre)

- `user-scalable=no` o `maximum-scale=1` que desactivan el zoom
- `onPaste` con `preventDefault`
- `transition: all`
- `outline-none` sin sustituto `focus-visible`
- Navegación con `onClick` en línea sin `<a>`
- `<div>` o `<span>` con manejador de clic (debería ser `<button>`)
- Imágenes sin dimensiones
- Arrays grandes con `.map()` sin virtualizar
- Campos de formulario sin etiqueta
- Botones de icono sin `aria-label`
- Formatos de fecha o número a mano (usar `Intl.*`)
- `autoFocus` sin justificación clara
- GIF animado donde valdría vídeo comprimido
- Acción solo por gesto, sin alternativa de toque/clic y teclado

## Formato de salida

Agrupado por fichero, `fichero:línea`, hallazgos escuetos. Sin preámbulo; la explicación, solo si el
arreglo no es obvio.

```text
## src/Button.tsx

src/Button.tsx:42 - botón de icono sin aria-label
src/Button.tsx:18 - campo sin etiqueta
src/Button.tsx:55 - animación sin prefers-reduced-motion
src/Button.tsx:67 - transition: all → listar propiedades

## src/Modal.tsx

src/Modal.tsx:12 - falta overscroll-behavior: contain
src/Modal.tsx:34 - "..." → "…"

## src/Card.tsx

✓ sin hallazgos
```

---

Aviso de licencia del original (MIT), que acompaña a esta copia:

> MIT License — Copyright (c) 2025 Vercel Labs
>
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
> associated documentation files (the "Software"), to deal in the Software without restriction,
> including without limitation the rights to use, copy, modify, merge, publish, distribute,
> sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions: The above copyright notice and this
> permission notice shall be included in all copies or substantial portions of the Software.
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
> NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
> NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
> DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
> OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
