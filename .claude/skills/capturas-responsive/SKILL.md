---
name: "capturas-responsive"
description: >-
  Usar cuando haya que comprobar cómo se ve una web en TODOS los tamaños de pantalla y enseñárselo
  a una persona en su móvil, o comparar dos opciones de CSS sin tocar el código: 'revisa que se vea
  bien en el móvil', 'responsive', 'en mi teléfono se ve mal', 'pasa todos los tamaños', 'hoja de
  capturas', 'enséñamelo en el móvil', 'compara las dos opciones', 'cómo quedaría con X px',
  'iPhone SE', 'apaisado', 'navegador de Instagram', '/capturas-responsive'. Matriz páginas × tamaños
  con reglas de medida (scroll horizontal, texto cortado, solapes, táctil 24 px), hoja HTML para el
  móvil y A/B de CSS en memoria. NO usar para: detectar cambios NO intencionados contra un baseline
  (`visual-regression`); juzgar si el diseño es bueno (`vera-art-director`, `/qa-loop`); decidir la
  forma de una pantalla nueva (`disenar-pantalla`); ni accesibilidad —teclado, zoom 200 %, reflow a
  320, texto grande— (`aitor-a11y-auditor`).
user-invocable: true
metadata:
  version: 1.0.0
  author: "Tech Lead Template (cosechada de flujo-lanzamiento, 2026-10-30)"
  category: qa
  updated: 2026-11-01
  source: "flujo-lanzamiento · LANZ-001 W9 (15 tamaños × 6 páginas; cazó 11 casos con fallos invisibles a 390×844)"
---

# capturas-responsive — matriz de tamaños, hoja para el móvil y comparación A/B

## Principio

La persona decide mirando **capturas reales en su teléfono**, no leyendo un informe. El agente
mide con reglas automáticas, **mira él mismo las capturas** y le da un enlace que abre en el móvil.
Un «0 fallos» del script no prueba que se vea bien: prueba que no se rompió nada medible.

## Cuándo activar

- Antes de dar por buena una web o una pantalla nueva con público real (cierre de wave con UI).
- «En mi teléfono se ve mal» / «¿y en un iPhone SE?» / «¿y dentro de Instagram?».
- Hay que elegir entre dos anchos, dos tamaños de letra, dos CSS: `comparar-css.mjs` las pone lado a lado.
- Obligatorio después de tocar maquetación global (contenedores, rejillas, cabecera, flotantes).

## Piezas (todas en `.claude/skills/capturas-responsive/`)

| Pieza | Fichero | Qué hace |
|---|---|---|
| Reglas | `medir.mjs` | `medirEnPagina({reglas, W, ultima, selectores})`: una función autocontenida que corre dentro de la página (`page.evaluate`). Genéricas: `sin-scroll-horizontal` (+`ventana-ensanchada`), `texto-cortado`, `solapes`, `tactil-24` (WCAG 2.5.8), aviso `hueco`. Opcionales, solo si el config da el selector: `burbuja-tapa` (flotante), `una-vista` (cta + nota), `cta-hero` (hero) |
| Matriz | `responsive.mjs` | Lee `responsive.config.json` → páginas × tamaños, un solo Chrome, recorre cada página pantalla a pantalla, espera a las animaciones, escribe `<pagina>/<W>x<H>.png`, `-vista.png` e `informe.json` |
| Config | `responsive.config.example.json` | **La única fuente de los tamaños**: 15 tamaños (7 móvil · 2 apaisado · 3 tableta · 3 escritorio) + 3 altos del navegador de Instagram como `tamanosExtra`. Cópialo al proyecto y cambia páginas y selectores |
| Hoja | `hoja-responsive.mjs` | `informe.json` → `index.html` autocontenido: miniatura de la primera vista por tamaño, agrupadas por móvil/apaisado/tableta/escritorio, título y orden del informe, fallos en rojo, filtro «Solo con fallos», claro/oscuro |
| A/B | `comparar-css.mjs` | Misma zona con N variantes de CSS inyectadas en memoria (`bypassCSP`) → `index.html` lado a lado. Sin argumentos explica el uso |
| Prueba | `tests/test_hoja.mjs` | Hoja desde un informe fijo + validación del config sin lanzar Chrome: `node .claude/skills/capturas-responsive/tests/test_hoja.mjs` |

Sin dependencias nuevas: `playwright-core` del proyecto (`npm i -D playwright-core` o `--playwright=<ruta>`)
y el Chrome del sistema (`CHROME_BIN`, por defecto `/usr/bin/google-chrome`).

### El config

```json
{ "base": "http://127.0.0.1:8080",
  "paginas": [ { "pagina": "inicio", "ruta": "/", "titulo": "Página de inicio", "hero": true },
               { "pagina": "contacto", "ruta": "/contacto", "llenar": { "nombre": "Ana" }, "movilVertical": true, "extra": false } ],
  "tamanos": [[320, 568], …], "tamanosExtra": [{ "w": 390, "h": 664, "etiqueta": "Instagram" }],
  "selectores": { "flotante": "#flotante", "cta": "#cta", "nota": ".nota", "hero": ".hero a.boton" },
  "auth": { "usuario": "preview", "envClave": "PREVIEW_CLAVE" },
  "versionServida": { "comando": "readlink /srv/www/current | xargs basename" } }
```

| Campo | Obligatorio | Qué hace si falta o está mal |
|---|---|---|
| `paginas[].pagina`, `ruta` | sí | Aborta con exit 2 y la lista de errores (nombre con barras, ruta sin `/`, `status` que no es HTTP…) |
| `tamanos` | sí | Aborta. `[W, H]` enteros; `--tamanos=320x568,1440x900` filtra sin editar el fichero |
| `tamanosExtra`, `titulo`, `llenar`, `status` | no | Sin extras / título = `pagina` / no rellena nada / espera 200 |
| `movilVertical`, `hero` | no | Activan `una-vista` y `cta-hero`; **exigen** `selectores.cta` / `selectores.hero` o aborta |
| `selectores.*` | no | Cada uno un string; si no, aborta nombrando el selector. Sin `flotante`, `burbuja-tapa` no corre (no calla: no existe) |
| `auth` | no | La clave se lee de `process.env[envClave]`; si la variable no está, aborta |
| `versionServida` | no | Si está, compara con `git rev-parse HEAD` y avisa en consola y en el informe; si no, se omite |
| `base` | sí (o 2.º argumento) | `0.0.0.0` se rechaza: se sirve en `127.0.0.1` y se llega por túnel |

## Receta

1. `bash .claude/hooks/check-ram.sh` en verde (lo repite `responsive.mjs` antes de lanzar Chrome).
   **Un solo Chrome**, contextos en serie y cerrados. Nunca varios en paralelo para ir más rápido.
2. Servir **lo que se publica** (con su nginx y su CSP), en `127.0.0.1`. Si el config lleva
   `versionServida`, el script avisa cuando lo servido no es el HEAD: una matriz entera sobre una
   release vieja no vale nada.
3. Copiar `responsive.config.example.json` al proyecto como `responsive.config.json`: páginas reales,
   selectores reales (o ninguno), y los tamaños del ejemplo tal cual salvo motivo.
4. Matriz completa. Orden de magnitud: ~25 min para una landing larga con los 18 tamaños. Para iterar,
   solo lo afectado: `--tamanos=… --paginas=…`.
5. `node hoja-responsive.mjs <salida>` → servir `<salida>` en `127.0.0.1` (`python3 -m http.server <p> --bind 127.0.0.1`)
   → por el túnel que haya en la máquina (`tailscale serve --bg --https=<p'> http://127.0.0.1:<p>` o
   `ssh -L`) → esa URL al móvil de la persona. **Nunca funnel ni `0.0.0.0`.**
6. **Abre con Read** las primeras vistas de 320×568, 360×640, una apaisada y 1440×900, y cada caso con
   fallo, antes de decir nada. Un «0 fallos» del script no prueba que se vea bien.
7. Arreglos de maquetación directos; lo que cambie el diseño aprobado, a la persona con capturas.
   Re-correr el subconjunto hasta 0 fallos y volver a mirar.

```bash
K=.claude/skills/capturas-responsive
S=salida-responsive                                  # fuera de git; una carpeta por corrida
node $K/responsive.mjs $S http://127.0.0.1:8080 --config=responsive.config.json [--tamanos=320x568,1440x900] [--paginas=inicio]
node $K/hoja-responsive.mjs $S
node $K/comparar-css.mjs --url=http://127.0.0.1:8080/ --zonas='#precios' \
  --variante='Hoy=' --variante='880 px=.tabla{max-width:880px}' --anchos=1440,1920 --salida=$S/comparar-ancho
```
Puertos: uno libre local (`ss -tln`) y otro libre del túnel; si la hoja ya está servida, mete la
comparación como subcarpeta de `$S` y comparte `…/comparar-ancho/`. La variante vacía (`'Hoy='`) es la
página tal cual; los anchos son del viewport.

### Salida (`informe.json`, lo que lee la hoja)

```
{ base, fecha, config, version?: {head, servido},
  casos: [{ pagina, titulo, ruta, ancho, alto, etiqueta?, captura, primeraVista,
            fallos: [{regla, detalle}], avisos: [{regla, detalle}], medidas: {scrollWidth, scrollHeight} }] }
```
Exit: `0` todo bien · `1` hay fallos · `2` config o argumentos inválidos · `3` RAM en rojo · `4` sin `playwright-core`.

## Lo que falla sin esta skill

| Error | Corrección |
|---|---|
| `addStyleTag` para la variante B con CSP estricta → se bloquea y A y B salen iguales | `bypassCSP: true` en la página (ya en `comparar-css.mjs`); comprueba que las capturas difieren |
| Capturar sin bajar por la página → no aparece lo que entra con el scroll ni el botón flotante | Recorrer pantalla a pantalla y comprobar el flotante en cada parada |
| Medir en mitad de una animación | Esperar a `getAnimations()` con `.finished.catch()` (una cancelada lanza AbortError) y tope de 4 s |
| Solo 3-4 tamaños «típicos» | La matriz entera: los fallos salen en 320, en apaisado y a 412-430 |
| Varios Chrome en paralelo para ir más rápido | Uno solo; la RAM manda |
| Quitar una regla CSS para «deshacer» un cambio | Restaurar la regla original (`git show <commit>:<fichero>`): quitarla deja el valor por defecto, que no es lo de antes |
| Enseñar el informe en vez de las capturas | El enlace a la hoja por el túnel, con la primera vista de cada tamaño |
| Comparar con `innerWidth` en móvil | Con `isMobile`, Chrome ensancha la ventana de diseño al contenido (320 → 330): todo se compara con el `W` configurado (`ventana-ensanchada`) |
| `overflow-x: hidden` en el body «arregla» el scroll horizontal | Enmascara el scroll, no el corte: la regla busca lo que sale por la derecha igualmente |

## Anti-patterns

- ❌ Editar los tamaños en el SKILL.md o en el `.mjs`: viven en el config, y solo ahí.
- ❌ Dar por hecho que una regla opcional corrió: sin su selector en el config, no existe.
- ❌ Lanzar Chrome con la RAM en rojo o varios Chrome a la vez.
- ❌ Decir «se ve bien» sin haber abierto las capturas con Read.
- ❌ Meter aquí las comprobaciones de accesibilidad (teclado abierto, zoom 200 %, reflow a 320 px,
  texto grande del sistema): son de `aitor-a11y-auditor`, que las mide contra WCAG con su propio informe.

## Ejemplos

### User: «revisa que la landing se vea bien en el móvil antes de publicar»
TL: check-ram → sirve la build publicable en 127.0.0.1 → config con la landing (`hero: true`,
`selectores.hero`) → matriz entera → hoja por el túnel → abre con Read 320×568, 360×640, 844×390,
1440×900 y los casos con fallo → arregla maquetación → re-corre `--paginas=landing` hasta 0 → enlace.

### User: «¿la tabla de precios mejor a 880 o a 1040 px?»
TL: `comparar-css.mjs --zonas='#precios' --variante='Hoy=' --variante='880=.tabla{max-width:880px}'
--variante='1040=.tabla{max-width:1040px}' --anchos=1280,1440,1920` → comprueba que las capturas
difieren (si son iguales, la CSP bloqueó el CSS) → enlace lado a lado → la persona elige.

## Related

- `visual-regression` — detecta si CAMBIÓ contra un baseline; esta enseña CÓMO SE VE en cada tamaño.
- `aitor-a11y-auditor` — teclado, zoom, reflow, texto grande, contraste (WCAG 2.2 AA).
- `vera-art-director` · `/qa-loop` — si está BIEN, no si se rompe.
- `rules/verification.md` — screenshot obligatorio si hay UI; `rules/security.md` — nunca `0.0.0.0`.
- `scripts/screenshot.py` — una captura suelta; para la matriz, esta skill.
