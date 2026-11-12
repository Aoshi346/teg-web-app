# Instrumentos de Vera — versionados, con su prueba y sus límites

> Cosechado de elvion (AN-25, sub-ola 3.20): allí Vera arregló su propio instrumento en vez de anotar
> el límite, y el arreglo vivía en el scratchpad y moría con la ronda. **Un límite anotado se vuelve a
> pisar; uno arreglado y guardado, no.** Cualquier auditor que mida con código propio lo guarda en
> `.claude/agents/<él>/instruments/`, con su comprobación de cordura y la lista de lo que no resuelve.

## `contrast-compositor.js`

Se inyecta con `page.evaluate(<contenido del fichero>)`. Mide contraste (más desbordamiento, foco,
tipografía, iconos, dinero y tildes) sobre `document.body` o sobre `window.__VERA_SCOPE`.

**Prueba contra fixture** (página con defectos contados; abre navegador, `check-ram.sh` antes):

```bash
<python con playwright> .claude/smoke/harvest/contrast_fixture.py --chromium /usr/bin/chromium-browser
```

Comprueba que el gris sobre blanco falla, que el blanco sobre un degradado oscuro NO falla, que un
fondo `oklab()` con opacidad se compone bien y que el texto sobre `url()` sale como indeterminado.
Con la lectura de degradados saboteada (`--js` con `if(par)` → `if(false)`), la cabecera pasa a fallar:
el fixture lo caza (31-10).

### La comprobación de cordura es OBLIGATORIA antes de fiarse de una medición

`oklab(0.769729 0.0546647 0.155194 / 0.25)` sobre blanco → `rgb(252,231,194)`. Devuelve `sanity` y
`sanity_ok`; **si `sanity_ok` es false, la medición no vale.**

### Por qué compone en canvas 2D y no parsea

Tailwind 4 emite `oklab()`/`oklch()` para los modificadores de opacidad (`bg-brand/25`). Un parser
escrito a mano devuelve `null` y el fondo cae a blanco en silencio: toda la familia «color saturado
sobre su propio tinte» queda sin medir.

### Degradados

`backgroundColor` no ve un `linear-gradient` (es `background-image`): subir por los ancestros leyendo
solo `backgroundColor` hace que el texto blanco sobre una cabecera con degradado mida ~1,05:1. En el
caso de origen, 5 de 12 patrones únicos eran ese falso positivo. El compositor extrae las paradas, compone
una por una y se queda con el **peor caso**. Lo que no sabe leer (`url()`, `image-set`) sale
`fondo_indeterminado: true` y se cuenta en `medidos_contra_fondo_inventado`: **un cero con
indeterminados > 0 no es un cero**.

### Cobertura honesta

`elementos_medidos` es la cobertura; `nodos_visitados` no (incluye los que se descartan por
visibilidad o tamaño, ~19 % más en el caso de origen).

### Límites conocidos, sin resolver

- **Mide el estado en REPOSO**: el `hover` hay que provocarlo a mano, control a control (un botón que
  en hover baja a 3,6:1 no sale en el barrido).
- `opacity` de un ancestro no se compone (atenúa texto y fondo por igual y el ratio sale intacto);
  `mix-blend-mode`, `filter` y `backdrop-filter` tampoco: los cuenta en `no_componibles`, y si alguno es
  > 0 el cero es parcial.
- Texto sobre foto: indeterminado, no medido.
- Desbordamiento: se mide contra `main` (si el scroll vive ahí, `documentElement` no puede dar positivo).

### El descarte se mide igual que el hallazgo

Toda entrada de `falsos_positivos_evitados` cita QUÉ se midió para descartarla. *«Descartar a ojo no
es medir, tampoco cuando se descarta.»*
