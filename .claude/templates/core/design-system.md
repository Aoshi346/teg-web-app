---
title: Sistema de diseño
reviewed:
reviewed_by:
---

<!--
  CAPA 6 del core (.docs/core/design-system.md) — documento FUNDACIONAL.

  Las capas 1-5 DESCRIBEN lo que hay. Esta MANDA sobre lo que se construye: es el equivalente
  al constitution.md de SpecKit, pero para la interfaz. Si un componente contradice este
  documento, el que está mal es el componente.

  ⚠️ `reviewed:` (YYYY-MM-DD) es obligatorio. Vacío → el índice lo marca SIN FECHA, en rojo.

  ⚠️ SI ESTE PROYECTO NO TIENE INTERFAZ (una CLI, una librería, un backend puro), NO rellenes
  esto con prosa plausible: bórralo y marca el documento como `"optional": true` en core.json
  con un `question` que empiece por "No aplica:" y diga por qué. Un hueco declarado es mejor
  que un sistema de diseño inventado que nadie sigue. Ver `data-model` en core.json.

  Se revisa al cerrar cada plan que toque UI.
-->

# Sistema de diseño

## 0. Antes de dar esto por bueno

**El mínimo innegociable.** Un documento a medias es peor que no tenerlo: la gente lo lee, ve huecos
y aprende a ignorarlo. Si no puedes cerrar estos cuatro puntos, **no pongas `reviewed:`** — déjalo
en rojo, que es la verdad.

```
[ ] §0b El PERFIL (`web-cliente` o `producto-panel`) y la dirección de arte con su nombre.
[ ] §1  El origen único, con RUTA EXACTA de fichero. No "en el theme": la ruta.
[ ] §4c El NIVEL de movimiento (0/1/2) y la metáfora, aunque el nivel sea 0.
[ ] §5  Al menos una fila de INTOCABLE, con el porqué y quién puede cambiarlo.
[ ] §6  Cómo se verifica: un comando, un linter o un nombre de persona. Algo real.
[ ] Frontmatter `reviewed:` con la fecha de hoy y `reviewed_by:` con quién firma.
```

Lo demás (paleta completa, escala, decisiones históricas) se puede ir rellenando después. Estos
seis, no: sin ellos el documento no dice **dónde está la verdad** ni **quién la hace cumplir**.

> **Por qué §0b y §4c entraron en el mínimo (2026-09-18).** Sin perfil declarado, todas las skills
> caen al mismo default y una landing de cliente se diseña como un panel de administración. Y sin
> nivel de movimiento, el default es «apágalo»: era el estado del template entero, y es la causa
> medida de que los diseños salieran correctos y muertos. Un `0` **declarado** es una decisión;
> un hueco es un accidente.

Y al revés: **borra las secciones que no apliquen** en vez de dejarlas con `[PERSONALIZAR]`. Un
`[PERSONALIZAR]` que sobrevive tres meses es una mentira con fecha.

## 0b. Perfil y dirección de arte

Lo que decide todo lo demás. Si esto está vacío, las skills de diseño no saben para quién están
trabajando (`patterns/diseno/perfiles.yaml`).

| | |
|---|---|
| **Perfil** | `web-cliente` \| `producto-panel` — [PERSONALIZAR] |
| **Dirección de arte** | [PERSONALIZAR — el NOMBRE, no la descripción: «Boho Chic Mediterráneo», «Editorial numerada»] |
| **Metáfora de sector** | [PERSONALIZAR — en una frase: «un masaje se mueve como agua»] |
| **Qué NO debe parecer nunca** | [PERSONALIZAR — es la mitad útil de esta tabla] |
| **Ficha completa** | [PERSONALIZAR — ruta a la dirección elegida en `.docs/diseno/direcciones/`] |

<!-- Ejemplo (bórralo): perfil `web-cliente` · dirección «Boho Chic Mediterráneo» · metáfora: las
     plantas se mecen, nada se desliza · NO debe parecer: una plantilla de wellness genérica con
     stock de piedras zen. -->

**El perfil no es una etiqueta: cambia el presupuesto, las referencias, los diales y la rúbrica con
la que te van a auditar.** `producto-panel` prohíbe además el scroll suavizado, el cursor propio y
los botones magnéticos: en una herramienta de trabajo estorban.

## 1. El origen único de los tokens

Lo primero y lo más importante: **de dónde salen los valores**. Sin un origen único, cada
componente inventa su propio gris y en seis meses hay once.

| Qué | Dónde vive (ruta exacta) | Cómo se consume |
|---|---|---|
| Color | [PERSONALIZAR] | [PERSONALIZAR] |
| Tipografía | [PERSONALIZAR] | [PERSONALIZAR] |
| Espaciado | [PERSONALIZAR] | [PERSONALIZAR] |
| Radios, sombras, bordes | [PERSONALIZAR] | [PERSONALIZAR] |

<!-- Ejemplo de fila bien rellenada (bórralo al terminar):
| Color | `frontend/tailwind.config.js` → `theme.extend.colors` | clase de Tailwind: `text-brand-600`. Nunca `text-[#1d4ed8]` |
Dónde suele vivir según el stack, por si no lo tienes claro:
  Tailwind → tailwind.config.{js,ts} · CSS puro → :root de un app.css · React → theme.ts /
  styled-components ThemeProvider · Django plantillas → un solo <style> con :root · design tokens
  formales → tokens.json + Style Dictionary.
Si hay DOS sitios con colores, el documento tiene que decir cuál MANDA y marcar el otro como deuda. -->


**Regla que no se negocia:** ningún componente escribe un color, una fuente o un espaciado **a
mano**. Si el valor que necesitas no está en el origen, la conversación es "añadimos un token",
no "pongo el hex aquí y sigo".

## 2. Color

| Token | Valor | Para qué es | Para qué NO es |
|---|---|---|---|
| [PERSONALIZAR] | [PERSONALIZAR] | [PERSONALIZAR] | [PERSONALIZAR] |

Contraste mínimo exigido: [PERSONALIZAR — p.ej. WCAG AA: 4.5:1 texto normal, 3:1 texto grande].

**Parejas de contraste** — cada combinación de texto y fondo que el producto usa de verdad. Las mide
`python3 .claude/scripts/contraste.py --tokens <este fichero> --css <origen de tokens>` (exit 1 si una
cae bajo su mínimo, 2 si un token no resuelve). Una pareja nueva se añade aquí al declarar el color,
no al descubrir el problema. Mínimo: 4.5 texto normal · 3 texto grande y componentes (SC 1.4.11).

| Texto | Fondo | Mínimo | Para qué |
|---|---|---|---|
| [PERSONALIZAR] | [PERSONALIZAR] | 4.5 | [PERSONALIZAR] |

## 3. Tipografía

| | Familia | Papel | Pesos | De dónde se carga |
|---|---|---|---|---|
| **Display** | [PERSONALIZAR] | titulares, y solo titulares | [PERSONALIZAR] | [PERSONALIZAR] |
| **Texto** | [PERSONALIZAR] | cuerpo, interfaz, formularios | [PERSONALIZAR] | [PERSONALIZAR] |
| **Datos** (opcional) | [PERSONALIZAR] | cifras, código, tabulares | [PERSONALIZAR] | [PERSONALIZAR] |

**Escala fluida** — los `clamp()` que existen, y no hay otros:

| Token | Mínimo | Preferido | Máximo | Interlineado | Tracking |
|---|---|---|---|---|---|
| [PERSONALIZAR] | | | | | |

- **Medida de línea máxima:** [PERSONALIZAR — por debajo de 80 caracteres; una serif aguanta algo más]
- **La display NO se usa para cuerpo.** Si aparece en un párrafo, es un error, no una variante.
- Emparejamiento por sector y la regla «en `web-cliente`, Inter nunca va sola»:
  `patterns/diseno/tipografia.md`.
- Si las fuentes se cargan de fuera, **declara el fallback** y qué pasa sin red.

## 4. Escala de espaciado

[PERSONALIZAR — la escala completa, p.ej. 4/8/12/16/24/32/48. Si no hay escala y se usan valores
sueltos, **dilo**: es deuda conocida, no un detalle que se oculta.]

## 4b. Rejilla y composición

| | |
|---|---|
| Contenedor máximo | [PERSONALIZAR] |
| Columnas y gutters | [PERSONALIZAR] |
| Ritmo vertical entre secciones | [PERSONALIZAR — p.ej. `clamp(80px, 10vw, 140px)`] |
| Grosor del filete | [PERSONALIZAR — 1-2px; en el corpus la rejilla se dibuja con `gap`, no con bordes] |
| Breakpoints | [PERSONALIZAR] |
| Alineación por defecto | [PERSONALIZAR — izquierda / centrada / justificada, y por qué] |

## 4c. Movimiento

**Nivel: [PERSONALIZAR — 0, 1 o 2].** Aunque sea 0, se declara: un cero decidido no es un hueco.

| Nivel | Qué entra |
|---|---|
| **0** | Solo lo que responde a una acción y dice qué cambió |
| **1** | Lo anterior + reveals al entrar en pantalla + micro-interacciones |
| **2** | Lo anterior + un momento orquestado (scroll, parallax, entrada) — solo si la metáfora lo pide |

**Los efectos, con nombre** (3-6; sin nombre no es movimiento, es relleno):

1. [PERSONALIZAR — p.ej. «el logo respira», «onda de agua al pulsar»]

**Tokens** (se declaran una vez y no se escribe una duración a mano en ningún componente):

| Token | Valor | Para qué |
|---|---|---|
| `--dur-fast` | [PERSONALIZAR] | hover, foco |
| `--dur-base` | [PERSONALIZAR] | abrir, cerrar |
| `--dur-reveal` | [PERSONALIZAR] | entrada al hacer scroll |
| `--ease-*` | [PERSONALIZAR] | |

**Reglas duras, las dos:**

- **Ningún contenido depende del JS para ser visible.** El `opacity:0` cuelga de una clase que
  añade el propio JS (`body.js-ready`), nunca del elemento. Detalle y el contraejemplo real —una
  página publicada que no se ve— en `patterns/diseno/movimiento.md` §3.2.
- **`prefers-reduced-motion` en CSS Y en JS.** Solo en CSS no basta: lo que anima una librería desde
  JavaScript se lo salta.

## 4d. Elevación y textura

| Nivel | Valor | Cuándo |
|---|---|---|
| [PERSONALIZAR] | | |

- **Las sombras van TEÑIDAS con el oscuro de marca, nunca negro puro.** Medido en el corpus: 134
  `box-shadow` y solo 7 en negro (94,8 %). Lo comprueba `agents/shared/red-flags.sh` R4.
- Grano o textura: [PERSONALIZAR — sí/no, y con qué opacidad]
- Cuándo borde y cuándo sombra: [PERSONALIZAR]

## 4e. Imagen

| | |
|---|---|
| Aspect-ratios permitidos | [PERSONALIZAR] |
| Tratamiento (overlay, duotono, máscara) | [PERSONALIZAR] |
| Al hover | [PERSONALIZAR] |
| **De dónde salen las fotos** | [PERSONALIZAR — **reales del cliente**: qué se le pidió y qué entregó] |
| Qué se prohíbe | [PERSONALIZAR — stock genérico, ilustración de IA…] |

> **Esta es la palanca de mayor efecto medida, y no depende de nosotros.** Sin fotos, servicios,
> horarios y colores reales del cliente, el resultado será pulido y genérico por construcción.
> Si no los hay, se pide; y si no llegan, se dice — no se rellena con stock y se entrega igual
> (`patterns/diseno/imagen.md`).

## 5. Qué es INTOCABLE y qué es libre

La parte que más se salta y la que más cara sale. Sé concreto: rutas y nombres, no adjetivos.

| Intocable (cambiarlo rompe consistencia en N sitios) | Por qué | Quién puede cambiarlo |
|---|---|---|
| [PERSONALIZAR] | [PERSONALIZAR] | [PERSONALIZAR] |

<!-- Ejemplo (bórralo): | La paleta `brand.*` de tailwind.config.js | La usan 40 pantallas; tocarla
     repinta el producto entero | Solo con OK del Usuario, y se anota en §7 |
Candidatos habituales a INTOCABLE: la paleta de marca · la familia tipográfica · el radio base ·
el componente de botón primario · los colores semánticos de estado (ok/aviso/error). -->


| Libre (decide cada pantalla) | Límite |
|---|---|
| [PERSONALIZAR] | [PERSONALIZAR] |

## 6. Cómo se verifica

Un sistema de diseño sin comprobación es una recomendación. Qué lo hace cumplir aquí:

- [PERSONALIZAR — el script/linter/hook que lo comprueba y su comando exacto]
- [PERSONALIZAR — quién lo audita a ojo, si aplica]
- **El gate determinista** (corre antes de gastar un turno de auditor):
  ```bash
  python3 .claude/scripts/gate_diseno.py <dir|url> --json     # 0 limpio · 1 hallazgos · 2 NO SE PUDO MEDIR
  ```
  Un **2** no es «está bien»: es que no se pudo mirar, y hay que arreglarlo antes de creerse nada.

## 7. Decisiones de diseño ya tomadas

Lo que alguien podría querer "arreglar" sin saber que fue deliberado.

| Decisión | Por qué | Cuándo |
|---|---|---|
| [PERSONALIZAR] | [PERSONALIZAR] | [PERSONALIZAR — fecha o fuente] |

## 8. Deuda conocida

- [PERSONALIZAR — lo que sabemos que está mal y aún no se ha arreglado]

---

## 9. Referencias

Las webs que se miraron **antes** de decidir nada, con qué se tomó de cada una y —lo más útil— qué
**no**. Sin esta sección, las referencias se piden una vez al arrancar y se pierden; tres meses
después nadie sabe por qué la tipografía es la que es.

| URL | Fecha | Qué SÍ tomamos | Qué NO tomamos |
|---|---|---|---|
| [PERSONALIZAR] | | | |

- Set de referencias del proyecto (lo produce `skills/marca` (paso 3)): [PERSONALIZAR — ruta]
- Referencias internas citables del corpus de la casa: `resources/referencias-diseno/INDEX.json`

> Una referencia se cita con **fecha**, porque una web viva cambia sin avisar. Si necesitas citarla
> línea a línea, copia el fragmento al proyecto: «como hace X hoy» no es verificable mañana.

## Qué NO va en este documento

- **El inventario de componentes** ("tenemos Button, Card, Modal…") → eso es la capa 2, y se
  genera del código. Aquí van las **reglas**, no el catálogo.
- **El porqué de un recorrido de usuario** ("primero pedimos el email porque…") → eso es `ux.md`
  (capa 4). Aquí no se decide el flujo, se decide con qué se pinta.
- **Capturas de pantalla** ni maquetas → envejecen a la primera y nadie las actualiza.
- **Valores duplicados del fichero de tokens.** Si copias aquí los 40 hex, en un mes mienten.
  Enlaza el origen y transcribe solo lo que necesite explicación.
- **Decisiones caras de revertir con alternativas descartadas** → eso es un ADR (`rules/adr.md`);
  aquí queda la regla resultante, con un enlace al ADR.
