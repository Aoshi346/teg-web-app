# Accesibilidad mínima exigible — patrón de casa

> Capa `a11y` del patrón de casa. Esto **no es la auditoría** — auditar es lo que hace Aitor
> (`aitor-a11y-auditor`, WCAG 2.2 AA) sobre la app ya construida. Esto es lo que hay que escribir
> para que la auditoría no encuentre nada obvio: reglas de escritura, con su comprobación.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only a11y`.

## La regla (una frase)

Usa el elemento HTML que ya hace el trabajo, dale a cada control un nombre accesible y comprueba lo
que no se puede leer en el código —contraste y tamaño de objetivo— con axe dentro del test, con
`target-size` **habilitada a mano**.

## Implementación de referencia

**Lo semántico primero.** Cuatro sustituciones cubren la mayoría de lo que Aitor reporta:

```tsx
// ✅ recibe foco, responde a Enter y Espacio, se anuncia como "botón"
<button type="button" onClick={onSelect}>Ver detalle</button>

// ✅ botón de solo icono: el nombre accesible es obligatorio, el icono no cuenta
<button type="button" aria-label="Cerrar" onClick={onClose}>
  <XIcon aria-hidden="true" />
</button>

// ✅ la etiqueta enlaza con el control; el error se anuncia
<label htmlFor="reference">Referencia</label>
<input id="reference" aria-invalid={!!error} {...register('reference')} />
{error && <p role="alert">{error.message}</p>}

// ✅ decorativa: alt vacío, para que el lector la salte en vez de leer la URL
<img src="/hero.png" alt="" />
```

**El foco se ve.** Nunca `outline: none` sin sustituto. Con Tailwind, el patrón de casa es
`focus-visible`, que muestra el anillo a quien navega con teclado y no a quien hace clic:

```tsx
className="rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
```

**Lo que el código no puede saber: contraste y 24 px.** Ninguna regla estática puede calcular el
contraste real (depende del color heredado, del fondo compuesto y del tema) ni el tamaño renderizado
de un objetivo táctil. Eso se comprueba **ejecutando** axe dentro del test que ya tienes:

```tsx
test('no tiene violaciones de accesibilidad', async () => {
  const { container } = render(<OrderList />, { wrapper: QueryWrapper });
  const results = await axe(container, {
    rules: { 'target-size': { enabled: true } },
  });
  expect(results).toHaveNoViolations();
});
```

Y en el E2E, sobre la página compuesta y con estilos reales:

```ts
const a11y = await new AxeBuilder({ page })
  .withTags(['wcag2a', 'wcag2aa'])
  .options({ rules: { 'target-size': { enabled: true } } })
  .analyze();
expect(a11y.violations).toEqual([]);
```

> **El detalle que hace que esto funcione de verdad.** En axe-core, `target-size` —la única regla
> de WCAG 2.2 que trae— está **desactivada por defecto** (`"enabled": false` en su definición) y su
> tag es `wcag22aa`, no `wcag2aa`. Es decir: pedir `withTags(['wcag2a','wcag2aa'])` **no la ejecuta**,
> y pedir `wcag22aa` tampoco basta mientras no se habilite explícitamente. Un gate de 24 px escrito
> sin ese `rules: { 'target-size': { enabled: true } }` pasa siempre, sin comprobar nada, y nadie se
> entera: es verde por no mirar. Por eso hay una regla del checker dedicada solo a esto.

**El movimiento, apagable en un sitio.** Quien pide menos movimiento —vértigo, migraña, trastorno
vestibular— no lo pide a ratos: lo tiene puesto en su sistema operativo y espera que la web lo
respete entera. Por eso la regla no es «esta animación respeta `prefers-reduced-motion`», sino que
**haya un sitio, uno solo, donde el movimiento del proyecto se apaga**:

```css
/* src/app.css — el único bloque que hay que acordarse de escribir, y se escribe una vez */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

No se pone a `0s` sino a `0.01ms` a propósito: una animación de duración cero **no dispara**
`animationend`, y el código que espera ese evento para pintar el paso siguiente se queda colgado
para justo el usuario que activó la preferencia. Con `0.01ms` el evento llega y no se ve nada.

La alternativa —apagar animación por animación, con la comprobación dentro de cada componente— es
la que se olvida en la siguiente que alguien escriba, y no hay forma barata de auditarla. Si aun
así hace falta la comprobación en JavaScript (una animación que no es CSS: un canvas, un lienzo,
una librería que anima con `requestAnimationFrame`), la fuente de verdad es la misma consulta:

```ts
const menosMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
```

> **Qué anima esta casa, medido.** Sobre los tres frontends del corpus: el único que anima de
> verdad lo hace con **utilidades CSS** —51 ficheros con clases `animate-*` (`animate-spin` ×42,
> `animate-pulse` ×37, `animate-in`/`animate-out` ×22) y 5 `@keyframes` propios— y lo apaga en un
> bloque de su hoja global. **Cero ficheros** importan `framer-motion`, `gsap` o `canvas-confetti`
> en los tres proyectos. No hay dominancia medida que justifique meter una librería de animación en
> el canon del stack (`frontend-stack.md`): con menos de 3 proyectos usándola, no hay patrón, hay
> preferencia.

## El antipatrón que sustituye

```tsx
// ❌ src/components/UserRow.tsx
<div onClick={handleSelect} style={{ color: '#999' }}>
  <img src="/avatar.png" />
  <span onClick={handleClose}>×</span>
</div>
```

- **`<div onClick>`** no está en el orden de tabulación, no responde a Enter ni a Espacio y se
  anuncia como texto plano. Para quien navega con teclado o con lector de pantalla, ese control
  **no existe**: no es que sea incómodo, es que la función es inalcanzable. Convertirlo en
  `<button>` lo arregla entero; simularlo con `tabIndex={0}` + `onKeyDown` es reimplementar mal lo
  que el navegador ya hace.
- **`<img>` sin `alt`** hace que el lector de pantalla lea la URL del fichero. `avatar.png` no es
  información; `alt=""` la omite limpiamente y `alt="Foto de Ana"` informa.
- **La `×` en un `<span>`** no tiene nombre accesible: se anuncia como "por" o se salta. Es
  `<button aria-label="Cerrar">`.
- **La animación que nadie puede parar.** Un `animate-pulse` en cada tarjeta y un carrusel que se
  mueve solo son, para alguien con trastorno vestibular, motivo de cerrar la pestaña. No es que
  moleste: es que marea. Y no lo caza ninguna auditoría de contraste.
- **`#999` sobre blanco** da unos 2.8:1, por debajo del 4.5:1 que exige WCAG AA para texto normal.
  Es el color con el que más se escribe texto secundario y el hallazgo más repetido de cualquier
  auditoría. Ningún grep lo detecta: lo detecta axe.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only a11y
```

| id | estado | qué detecta |
|---|---|---|
| `fe-interactivo-semantico` | activo | `onClick` sobre `<div>`, `<span>`, `<li>` o `<td>` |
| `fe-imagen-con-alt` | activo | `<img>` sin atributo `alt` (incluye etiquetas multilínea) |
| `fe-target-size-habilitado` | débil | test que ejecuta axe sin habilitar `target-size` |
| `fe-movimiento-apagable` | débil | **proyecto**: hay animación (`@keyframes`, `animation:`, clases `animate-*`) y **ningún** fichero del árbol menciona `prefers-reduced-motion` |

Refuerzo en ESLint con `eslint-plugin-jsx-a11y` (`plugin:jsx-a11y/recommended`), que cubre en el
AST lo que el checker cubre por texto y además lo que el checker **no** puede:
`jsx-a11y/click-events-have-key-events`, `jsx-a11y/no-static-element-interactions`,
`jsx-a11y/label-has-associated-control`, `jsx-a11y/alt-text`, `jsx-a11y/anchor-is-valid`,
`jsx-a11y/heading-has-content`. Actívalas como `error`.

Y en ejecución, axe: **contraste** (`color-contrast`), **nombre accesible** de botones y enlaces
(`button-name`, `link-name`), **orden de encabezados** y **tamaño de objetivo** (`target-size`, con
la advertencia de arriba). Ese es el reparto honesto: lo estructural se comprueba escribiendo, lo
computado se comprueba ejecutando.

Y sobre la página montada, a los tres anchos (un «0» medido solo a 1440 no es un 0: AMC):
`$PY .claude/scripts/auditar_a11y.py <url>` (axe-core 4.10.2 fijado por sha256, 1440/768/390, exit 0/1/2)
y `$PY .claude/scripts/contraste.py --dom <url>`, con `$PY` el de `scripts/preparar_navegador.sh`.

`fe-movimiento-apagable` es de **proyecto** y no de fichero porque la pregunta lo es: que un
componente anime no es un defecto, lo es que en todo el árbol no haya dónde apagarlo. Es **débil**
—avisa, no bloquea— por su medida: de los 3 frontends del corpus, **1 cumple** (tiene el bloque) y
**2 no** (animan sin él). Con esa n no se activa nada; se avisa. Y lo que la regla **no** puede
ver: si el bloque existe pero no cubre las animaciones que el proyecto usa de verdad — comprueba
que alguien lo escribió, no que funcione. Eso se mira una vez, a mano, con la preferencia activada
en el sistema.


## Excepciones legítimas

- **Lienzos y visualizaciones** (canvas, gráficos SVG complejos) donde la interacción no se puede
  expresar con controles nativos. La salida correcta no es exceptuar y olvidar: es ofrecer una
  alternativa equivalente —una tabla de datos, un control paralelo— y documentarlo.
- **Superficies deshabilitadas a propósito** (un elemento arrastrable, un mapa) donde WCAG 2.2 pide
  una **alternativa** al gesto de arrastre, no que el gesto desaparezca.
- **Texto puramente decorativo o deshabilitado**, que el propio `color-contrast` de axe ya exime.

```tsx
// pattern-exempt: fe-interactivo-semantico — celda arrastrable del planificador; el equivalente
// accesible son los botones "mover arriba/abajo" de la barra de acciones (ver a11y/planner.md)
```

Como en el resto del catálogo: una excepción sin alternativa escrita no es una excepción, es una
barrera con permiso.
