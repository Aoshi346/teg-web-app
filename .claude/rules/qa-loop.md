---
paths:
  - ".docs/feedback/**"
  - "**/trend-delta.json"
  - "vrt.json"
  - ".claude/commands/qa-loop.md"
  - ".claude/agents/lidia-naive-tester*"
  - ".claude/agents/vera-art-director*"
  - ".claude/agents/ignacio-roig*"
  - ".claude/agents/shared/calibration-v2.md"
  - ".claude/scripts/certifica_objeto.py"
---
# QA Loop — Protocolo Lidia + Vera + Ignacio hasta avg ≥ 9.0

> **Cuándo aplicar:** al cerrar cualquier wave/feature **con UI**. Orquesta los tres auditores de
> persona que el template ya trae (`lidia-naive-tester`, `vera-art-director`, `ignacio-roig`) en un
> bucle convergente hasta una nota media ≥ 9.0.
>
> **NO aplicar:** waves backend-only u operacionales (sin UI) — para esas usa `verification-loops`
> / `ux-reviewer`. Tampoco sobre código que no compila (verifica build antes).
>
> **Relacionado:** `verification.md`, `verdict-contract.md` (esquema de veredicto reutilizable),
> **`verification.md` §Estabilidad E2E** (estado determinista + selectores estables: prerrequisito para que este
> bucle no mida ruido), skills `verification-loops`, `ux-reviewer`, `naive-user-playthrough`,
> `visual-regression` (diff objetivo contra baseline, complementa la crítica subjetiva de Vera),
> `feedback-audit`; agentes `lidia-naive-tester`, `vera-art-director`, `ignacio-roig`; skills
> `disenar-pantalla` + `nueva-pantalla` (quien construye lo que estos tres auditan).

---

## Disparo

- Manual: `/qa-loop` o "lanza qa-loop sobre la wave actual".
- Autónomo: con `/goal` y el prompt de cierre de wave como condición («`RESULT.md` con PASS según
  §4, o para tras 3 iteraciones», que es el tope de §6). El bucle converge a una nota, así que es una
  meta verificable, no un `/loop` por reloj; y la condición tiene que poder demostrarse en la
  conversación (`goal-vs-loop.md` §`/goal`). Antes ponía «dentro de `/loop` (plugin ralph-loop)»:
  son dos cosas distintas y ninguna era la buena (MO-30). Si se quiere repetir el mismo prompt
  entero, es `/ralph-loop:ralph-loop … --max-iterations 3`.

---

## Protocolo (estricto)

### 0. El gate determinista — ANTES de gastar un turno de auditor

Lo barato va primero. Hoy Vera gasta turnos haciendo greps que una máquina hace mejor y más rápido.

```bash
python3 .claude/scripts/gate_diseno.py <build|url> --exigir-impeccable --json \
  > .docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/gate/gate.json
```

| Sale | Qué significa | Qué se hace |
|---|---|---|
| **0** | Medido, sin hallazgos de reglas `activo` | Se sigue |
| **1** | Medido, hay hallazgos | **La ronda no arranca.** Se arreglan y se vuelve a medir |
| **2** | **NO SE PUDO MEDIR** (sin npx, sin red, destino inexistente) | **Tampoco arranca**, y no es lo mismo que «limpio». Se arregla el instrumento |

Un `--sin-impeccable` en una ronda de `/qa-loop` **invalida este paso**: queda escrito en el JSON y
la ronda se marca como medida a medias.

### 1. Pre-flight
- RAM libre: `bash .claude/hooks/check-ram.sh` en verde — el umbral lo calcula el hook (`--explain`)
  (`rules/ram-pytest.md`). Ojo: 3 auditores con Chrome cuentan ~doble.
- Build limpio: el equivalente del proyecto a `npm run build` + check del backend pasa sin errores.
- URL viva: `curl -fsS http://localhost:<PORT>/ -o /dev/null` (sustituye `<PORT>` por el puerto del
  proyecto; usa `PROJECT_DOMAIN`/`BACKEND_PORT` de `settings.json` si están definidos, o producción
  cuando aplique).
- Anotar `WAVE_ID` y `iteration_n` (empieza en 1).
- **Congelar el build y anotar su sha** (`git rev-parse --short HEAD`) → es el `target_sha` de la
  ronda. Se lo pasas a los tres auditores. Ver §1b.
- **Sellar el objeto al abrir** (`certifica_objeto.py sellar … --salida …/sello/apertura.txt`): el
  sha no ve el bundle servido ni lo que responde la API. Ver §1b, punto 5.
- **Si los auditores van a la vez contra un despliegue vivo**: cuentas, límites de peticiones e
  instrumento, §2c, antes de lanzar a nadie.
- **Declarar el perfil de rúbrica** del objetivo: `web-cliente` | `producto-panel` (antes `landing` |
  `herramienta-interna`, que siguen valiendo por compatibilidad —
  `patterns/diseno/perfiles.yaml#equivalencias`). Decide los pesos de los ejes, si `fotos_videos`
  cuenta o es N/A (AUD-8), y **no se cambia a mitad de ronda**.

### 1c. Regresión visual — el baseline se bendice al CERRAR, no al abrir

`visual-regression` existe desde hace meses y **no estaba cableada a este bucle**: era el hueco nº3
declarado en §2b, y es el que dejó pasar L-008, F-008 y F-012 (defectos que una ronda introdujo y
nadie vio hasta la siguiente).

```bash
VRT=.claude/skills/visual-regression/vrt.py
python3 $VRT capture --config vrt.json
python3 $VRT compare --config vrt.json      # exit 1 = regresión contra la iteración anterior
```

Tres decisiones que lo hacen funcionar, y las tres importan:

1. **El baseline se bendice al CERRAR cada iteración**, no al abrirla. Así iter-n+1 compara contra
   iter-n y los defectos nuevos los caza la máquina, no la suerte.
2. **Un `bless` cita el finding que lo justifica** (`fix(F-012): … — baseline actualizado`). Un
   bless sin id de hallazgo es la puerta por la que cualquier regresión desaparece sin dejar rastro.
3. **El diff NO se le pasa a Vera.** Un rectángulo rojo señalando dónde mirar es anclaje, y rompe la
   evaluación ciega de `calibration-v2.md` §2. El diff va al orquestador y al que arregla.

### 1d. ¿El fix declarado se aplicó de verdad?

Es el hueco **mejor documentado** de §2b: Ignacio cazó **3 fixes declarados y no aplicados**, de
forma incidental, en 1 de cada 3 rondas. No necesita un auditor nuevo — necesita un script.

```bash
python3 .claude/scripts/verificar_fixes.py <WAVE_ID> <iter> --json
```

- **Entrada**, y es el único coste real: quien arregla escribe `iter-<n>/fixes/fixes-declarados.json`
  con, por cada hallazgo, **cómo se comprueba** (selector + propiedad + valor esperado). El campo se
  autopropone desde el `fix_proposal` que Vera ya emite.
- **Doble evidencia** (`rules/verdict-contract.md`): 🔎 el `git diff` entre los dos sha toca la
  región citada · 👁 una sonda evalúa el predicado contra el build congelado.
- Lo que no admite predicado automático se marca `verificacion: manual` y cae en la relectura de
  Ignacio. El hueco se reduce a esos, en vez de ser total.
- **Un `notdone` sobre un fix declarado es P0 y la ronda NO se promedia**: significa que estamos
  midiendo un build cuyos cambios no son los que se dijo, y promediar eso es peor que no medir
  (mismo razonamiento que §1b).

### 1b. El build NO se toca durante la ronda (AUD-3) — regla dura

> **Auditores en paralelo + arreglos en caliente = medición destruida.** No es teoría: pasó en
> TPL1-W3/iter-3. Mientras las tres auditorías corrían, el orquestador parcheó en caliente dos P0
> que Ignacio acababa de encontrar; Vera había mirado **antes** del parche. **Vera e Ignacio
> auditaron builds distintos y sus notas se promediaron en un único `score_wave` de 7.55** — un
> número que no describe ningún objeto real. El propio `RESULT.md` lo admite al pie: *«el 7.35 de
> Vera es pre-hot-patch»*. Ese 7.55 es el que cerró el bucle.

1. **Se congela** un sha antes de lanzar a nadie. Los tres auditores reciben el **mismo**
   `target_sha` y lo escriben en su salida (`run.target_sha`, `run.build_frozen: true`).
2. **No se toca nada** —ni un fix «de un minuto», ni un typo— hasta que **los tres** han
   terminado y entregado.
3. **Si aparece un P0 crítico a mitad: se ABORTA la ronda entera** y se reinicia sobre el build
   nuevo. **No se parchea en caliente.** Repetir una ronda es más barato que publicar una media
   inventada — y una media inventada contamina además todo lo que se compare con ella después.
4. Al cerrar, el orquestador verifica que los tres `target_sha` coinciden. Si no coinciden,
   **la ronda no se promedia**: se anota como inválida en `RESULT.md` y se repite.
5. **El sha no basta: se certifica el objeto al abrir y al cerrar** (MO-51, de elvion). Un sha no
   describe lo servido: en elvion, quince rondas se certificaron con el sha y el md5 de la plantilla,
   y un reordenado del catálogo que cambiaba por completo lo que veía el cliente **no movió ni un bit**
   de la plantilla, porque viajaba por la API; el bundle del widget, en `.gitignore`, ni siquiera se
   puede reconstruir desde un sha. Por eso son **dos medidas**: la de cierre cazó dos movimientos que
   la de apertura no podía ver.

   ```bash
   S=.docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/sello
   C="--base http://127.0.0.1:<PORT> --pagina / --bundle /static/<bundle>.js --api /api/<ruta>/ \
      --cabecera-env X-API-Key=<VARIABLE> --ignorar <clave-volátil> --git-ruta frontend/"
   python3 .claude/scripts/certifica_objeto.py sellar $C --guardar $S/apertura --salida $S/apertura.txt  # antes de lanzar a nadie
   python3 .claude/scripts/certifica_objeto.py sellar $C --guardar $S/cierre --salida $S/cierre.txt      # cuando entregó el último
   python3 .claude/scripts/certifica_objeto.py comparar $S/apertura.txt $S/cierre.txt
   ```

   | Sale | Qué se hace |
   |---|---|
   | **0** | El objeto no se movió: la ronda se puede promediar |
   | **1** | **Se movió: la ronda no vale.** Se anota inválida en `RESULT.md` con las líneas que cambiaron y se repite sobre el objeto nuevo. Si fue una API, el `diff` de las dos copias guardadas dice qué cambió |
   | **2** | **No se pudo medir** (una ruta que no da 200 —un 401, un 429 o una redirección a `/login` sellarían esa pantalla; las redirecciones no se siguen—, un JSON que no parsea, la variable de la clave vacía). No es «sin cambios»: se arregla el instrumento |

   `sin_commitear` mayor que 0 en el sello quiere decir que el sha no describe lo servido. La clave
   de la API se pasa por variable de entorno (`--cabecera-env`), nunca escrita en el comando, y su
   valor no sale en el sello. Las copias de la API van en **carpetas distintas** al abrir y al cerrar
   (`$S/apertura`, `$S/cierre`): con la misma, el cierre pisa la apertura. Probado contra un servidor
   local con el bundle y un precio cambiados a mitad de ronda y un panel que redirige a `/login`:
   `_archive/2026-10-20/medicion-2.16/probar_certifica.py`.
6. **Congelado quiere decir también sin commits, sin build y sin escribir los datos que se ven**
   (AMC, 2026-09-06 y 2026-09-26). Vera hace `git rev-parse HEAD` al empezar y al acabar y declara
   desvío aunque el commit no toque el panel; `npm run build` a mitad de ronda cambia lo que sirve
   nginx en vivo. Y el **dato** tampoco puede moverse: un auditor que preparó 57 informes a mitad de
   ronda cambió los recuentos que veía otro. Editar el árbol sin commitear ni construir sí vale; en
   el encargo de cada auditor se dice qué **no** puede escribir en la demo.

Los tres auditores llevan esta regla escrita en su ficha (Lidia §Contrato de salida, Vera §Bloque
`run`, Ignacio Regla #6). El orquestador es quien la hace cumplir.

### 2. Ejecución paralela de los 3 auditores

Lanzar **en un solo mensaje con 3 Agent tool calls** (paralelización, ver `parallelization.md`):

| Agente | Trigger | Output |
|--------|---------|--------|
| **Lidia** (`lidia-naive-tester`) | "Lanza naive test como [persona objetivo del proyecto], 30s, móvil+desktop" | `.docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/lidia/REPORT.md` + `trend-delta.json` + screenshots |
| **Vera** (`vera-art-director`) | "Audita visual tier-1, gate 9.0, los 5 tokens son obligatorios" | `.docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/vera/REPORT.md` + `findings.json` + screenshots 1440/768/390 |
| **Ignacio** (`ignacio-roig`) | "Crítica adversarial, ≥10 findings, delta ≥1.0 vs Vera" | `.docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/ignacio/REPORT.md` |

El prompt de cada uno **debe** llevar el `target_sha` congelado (§1b) y el perfil de rúbrica (§1),
y **no debe** llevar la lista de cambios de la ronda anterior (evaluación ciega,
`shared/calibration-v2.md` §2).

**Topes de la puerta de UI** (`audit-team.md` §3): ≤5 jueces y ≤3 con navegador a la vez. Los tres de
siempre más Aitor o Lena caben; la batería entera (todos los auditores-persona) solo en un hito de
release, con `hito_release: true` en el acta. Desde la iteración 2, la ronda mira **solo lo que
cambió** (las pantallas que tocó el diff entre los dos `target_sha`), no la web entera.

### 2b. Quién cubre qué — y qué NO cubre nadie (AUD-5)

El template declara **13 auditores-persona; 8 no han corrido nunca** (eran «10» hasta el
2026-09-18: Aitor y Conrado sí tienen rondas con evidencia en disco — ver el aviso de abajo). Trece
nombres en una lista tranquilizan; los que corren de verdad protegen. **Un agente que no corre en
esta ronda no es cobertura de esta ronda** — y esto no es teórico: la accesibilidad de teclado
figuraba «cubierta» por Aitor y en 3 rondas sobre un dashboard con modales y kanban drag&drop no la
miró nadie. Que Aitor hubiera auditado OTRO proyecto en junio no protegía a este.

**Dueño único por dimensión (reparto vigente, medido sobre TPL1-W3):**

> ⚠️ **Dos preguntas que esta rule colapsaba en una (corregido 2026-09-18).** Decía que Aitor y
> Conrado «nunca han corrido», y **es falso y está en disco**: los dos tienen iter-1 e iter-2 sobre
> `mini-RetoquePro`, fechadas el **2026-06-21**, con hallazgos identificados y evolución de score en
> su `memory.md`. Lo que era cierto es otra cosa: **no corren en ESTE bucle**. Son preguntas
> distintas y por eso ahora van en dos columnas. La frase que sí hay que conservar: *un auditor que
> no corre en esta ronda no es cobertura de esta ronda* — da igual cuántas haya corrido antes.

| Dimensión | Dueño en este bucle | Absorbido de | ¿Ha corrido alguna vez? |
|---|---|---|---|
| Contraste WCAG AA | **Vera** | `aitor-a11y-auditor` | **Sí** — 2 rondas (mini-RetoquePro, 2026-06-21, 5.71 → 7.0) |
| Consistencia de componentes | **Vera**, prestado — vuelve a Rita cuando salga de modo sombra | `rita-pattern-keeper` | No — 0 rondas |
| Brand voice / AI-slop | **Vera** (eje 10 + AI1-AI4 + `red-flags.sh`) | `lena-i18n-auditor` | No |
| Onboarding · microcopy sin jerga · empty states | **Lidia** (modo primer uso) | `tomas-onboarding-tester` (retirado en la 3.01) | No |
| Primeros niveles de conversión (oferta, confianza, CTA) | **Lidia** | `conrado-cro-auditor` | **Sí** — 2 rondas (mini-RetoquePro, 2026-06-21, 4.9 → 5.3) |

**Huecos declarados — nadie los audita hoy.** No los cuentes como cubiertos:

1. **a11y que no es contraste**: teclado, foco visible, roles ARIA, target size ≥24px, alternativa
   a gestos de arrastre. Un drag&drop sin alternativa de teclado incumple WCAG 2.2 (2.5.7).
2. **Verificar que el fix declarado existe de verdad.** Es el hueco más caro y el mejor
   documentado: Ignacio cazó **3 fixes que el fixer declaró aplicados y no lo estaban**, y solo de
   forma incidental. Ocurrió en 1 de 3 rondas: la tasa base no es despreciable. Hoy no tiene dueño
   — existe como una línea en la memoria de Ignacio.
3. **Regresiones entre rondas.** Cada ronda introdujo defectos nuevos (iter-2 generó L-008; iter-3
   generó F-008 y F-012). La skill `visual-regression` existe en el repo y **no está cableada a
   este bucle**; la propia Vera escribió que *«un CI de regresión visual habría atrapado ambos
   antes de iter-3»*.
4. **Coherencia semántica de los datos mostrados** (¿el número de la página coincide con su
   fuente?) y **la salida imprimible** (`window.print()`, nunca auditada).

**Los ortogonales que no han corrido NUNCA** —ocho, no diez (`sofia-pentester`,
`priya-privacy-auditor`, `rafa-retrieval-engineer`, `bruno-perf-cop`, `marco-qa-breaker`,
`nadia-chatbot-evaluator`, `lena-i18n-auditor`, `lidia-naive-tester`)— se conservan, pero
**como checklist, no como auditor**: se citan como «pendiente de correr una vez», nunca como
cobertura de la wave. Salen de esa categoría cuando corran y dejen evidencia en disco.
**Aitor y Conrado ya salieron** (§tabla de arriba): tienen rondas con evidencia, y lo que falta de
ellos es entrar en este bucle, no estrenarse.

### 2c. QA en paralelo contra un despliegue vivo — que el entorno no se cuele como hallazgo (MO-27)

Cosechado de `accounting_AMC` (rondas AMC-3, AMC-5 y NUC-2, septiembre de 2026): cada uno de estos
fallos costó una ronda o una hora y **parecía un defecto del producto** —pantallas vacías, blanco
sobre blanco, un 404 en una pantalla que funciona—. Antes de lanzar a los auditores a la vez:

| Riesgo | Qué se ve | Qué se hace |
|---|---|---|
| **El límite de peticiones** (en AMC, `UserRateThrottle` de DRF: 2.000/h por usuario; el de login, por conexión) | Páginas que cargan **vacías, sin mensaje**; el único síntoma es un `429` en la consola o en la red | **Una cuenta por auditor** y **una sesión reutilizada por auditor**, nunca un login por script. Si un auditor dice «pantalla vacía» o «no encuentro el botón», **se mira el 429 antes de creer el hallazgo** (consola y red del navegador). La pentester va antes o después de los de navegador, no a la vez |
| **Datos que se mueven** | Recuentos distintos entre dos auditores de la misma ronda | §1b punto 6: el encargo dice qué no se escribe. Los ids de una demo que se re-siembra se descubren por API, no se escriben a mano (si no, salen 404 que no son del panel) |
| **El navegador** | Playwright no arranca, o un `set_input_files` entrega un fichero de 0 bytes y el POST muere con `ERR_ALPN_NEGOTIATION_FAILED` | El Chromium **del sistema** (detectar el binario, como `scripts/screenshot.py`; aquí `/usr/bin/chromium-browser`). El Chromium de **snap no lee `/tmp`**: las fixtures que se suben van bajo `/home`. Comprobación en una línea: `document.querySelector('input[type=file]').files[0].size` → 0 es esto |
| **Colores en `oklch()` o `color(srgb …)`** | Contraste **exactamente 1,00** en todo: es la firma de una medición rota, no de un panel roto | `getComputedStyle` devuelve el color en el espacio en que se declaró, y un regex de `rgb()` no lo lee y cae al blanco. Se resuelve pintando el color en un `<canvas>` de 1×1 y leyendo `getImageData` (el snippet está en las fichas de Vera §R-B y de Aitor) |
| **Código viejo servido** | La captura enseña lo de antes del arreglo, y `manage.py shell` (que carga el fichero fresco) dice que está bien | `runserver --noreload` no recarga: **reiniciar el servidor tras tocar backend, antes de capturar** |
| **Una captura reducida como prueba de un carácter** | «Falta la tilde» leído de una captura de 390 px vista a 271 | Para tildes, ñ, comillas o guiones la evidencia 👁 es el texto del DOM (`el.textContent`), no la imagen (`verdict-contract.md`) |

Y dos comprobaciones baratas antes de fiarse de una tanda de capturas: que **no pesen todas lo
mismo** (si pesan igual, no entraste: es la pantalla de login) y que el contraste **no salga 1,00**
(si sale, no estás leyendo los colores). El instrumento que no puede medir aborta
(`verification.md` §El instrumento que no puede medir).

### 2d. Validar cada P0/P1 antes de arreglar (EQ-D13)

Antes del paso 5, un **verificador con contexto limpio** (subagente nuevo, no uno de los tres)
recibe cada hallazgo P0/P1 de Lidia, Vera e Ignacio **con su material crudo** —la captura, el
selector, el DOM, el `fichero:línea`— y lo **confirma** o lo **descarta** citando lo que vio
(`verification.md` §Nivel 4: sin material, su veredicto es un eco). Solo los confirmados entran en la
lista de arreglos y en el informe al Usuario; los descartados se quedan en el acta con su porqué. El
coste es una pasada más; el ahorro, no arreglar fantasmas (un contraste 1,00 de un `oklch()` mal leído,
un 429 tomado por pantalla vacía, §2c).

Con la validación se escribe el **acta** de la iteración (`iter-<n>/acta.json`, formato:
`gate_auditor.py --ejemplo`): puerta `ui`, autor (quien construyó y arregla), los auditores con su
informe, las rondas con su alcance y cada P0/P1 con `validacion`, `validador` y `evidencia`.

### 2e. Trampas del arnés — antes de creerle un negativo al instrumento (EQ-27, sub-ola 3.14)

Cosechadas de las memorias de Lidia, Vera e Ignacio en tres proyectos (31-10). Valen para los tres,
por eso viven aquí y no en cada ficha. La raíz común: **un instrumento nuevo se calibra contra un caso
de resultado conocido antes de creerle un «0» o un «no funciona»**, y el síntoma se contrasta por otra
vía (el mismo endpoint con `curl`, otro método de interacción) antes de reportarlo.

| Trampa | Síntoma falso | Qué se hace |
|---|---|---|
| URL final `/login` | N capturas byte-idénticas (mismo md5) que «auditan» el login | Abortar si la URL final acaba en `/login`; comparar md5 de capturas hermanas |
| Token en `sessionStorage` | `storage_state()` no lo guarda: todas las capturas, del login | Comprobar con `page.evaluate(() => JSON.stringify(sessionStorage))` tras entrar; reutilizar con `add_init_script` o una sola `page` por ancho |
| Color `oklab()`/`oklch()` (Tailwind 4, también `bg-x/25`) | Un parser de `rgb()` da null → blanco → contraste sin medir o fantasma | Componer en canvas 2D y leer el píxel; cordura antes: `oklab(0.769729 0.0546647 0.155194 / 0.25)` sobre blanco = `rgb(252,231,194)`. El medidor no ve `background-image` (degradados): mirar el píxel |
| Shell con scroll en `<main>` | `documentElement.scrollWidth == clientWidth` siempre: el desborde no puede dar positivo; `full_page=True` devuelve solo el viewport | Medir contra el contenedor que hace scroll (`main.getBoundingClientRect()`, `main.scrollHeight`); un sidebar `sticky`+`100vh` descolgado en `full_page` es artefacto |
| `is_visible()` | `true` para elementos fuera de la zona visible por overflow | `bounding_box().x < viewport.width` y `scrollWidth` frente a `clientWidth`, con captura |
| Selectores genéricos | `[class*=modal]`, «el primer `overflow-x:auto`» (suele ser el nav), `has_text` sin anclar («No» casa con «Prefiero no contestar») | Anclar con `closest()` y regex `^…$`; `nav a:visible` con menú duplicado; confirmar con captura antes/después |
| `check({force:true})` sobre input `sr-only` | No dispara el `onChange` de React: casi un P0 de seguridad falso | `label.click()` y comprobar `checked` con `evaluate`; todo P0 se reproduce con dos vías |
| `accept_downloads=False` | «La descarga baja 0 bytes, 3/3» | Contrastar el endpoint con `curl`; las condiciones del arnés (descargas, viewport, permisos) van en el informe |
| Visor de PDF en headless | Pantalla negra | Bytes y cabecera `%PDF` con `fetch(location.href)`; pintar con `pdftoppm -png -r 70` |
| Avisos efímeros (toasts) | Un grep del texto esperado solo confirma la hipótesis | `MutationObserver` sobre nodos nuevos; el estado de carga, con `page.route` diferido, no con `sleep` |
| Fila escrita por el propio instrumento | Un stub de la ronda anterior pasa por dato real | Antes de que una fila sostenga un P0: ¿la escribí yo? Con datos de demo compartidos, medir la contaminación |

El compositor de contraste que resuelve las filas de `oklab()` y degradados está **versionado** en
`agents/vera-art-director/instruments/contrast-compositor.js`, con su fixture
(`smoke/harvest/contrast_fixture.py`) y sus límites en el `README.md` de esa carpeta (AN-25). Un
instrumento que un auditor arregla en una ronda se guarda ahí, no en el scratchpad. Y probar como
cliente sin ensuciar la cola real: `agents/shared/clean-testing.md`.

### 3. Cálculo del score

```python
# Lidia: media de las dimensiones que APLICAN al perfil declarado en §1 (AUD-8).
# En `herramienta-interna`, fotos_videos es N/A: un informe no puede tener fotos de personas,
# y con L-D clavándola en 3/10 restaba 0.6 fijos, dejando su máximo en 9.125 con el gate en 9.0.
lidia_avg = score_profiled   # media de las 7-8 dimensiones aplicables. Se guarda también score_raw
vera_avg  = (sum de los 10 ejes de Vera) / 10
ignacio_score = score adversarial 0-10 (informativo)

score_wave = (lidia_avg + vera_avg) / 2   # Ignacio NO entra en la media (mide "qué falta", no PASS)
```

Recalculado sobre TPL1-W3 con los ficheros ya guardados: Lidia 6.6/7.1/7.75 →
**7.14/7.71/8.43**, y el `score_wave` de iter-3 habría sido **7.89** en vez de 7.55.
**Sigue por debajo de 9.0** — ver el aviso del gate.

### 3b. Comparación por pares: ¿la nueva es mejor que la anterior? (EQ-36)

Desde la iteración 2, además de la nota, cada auditor contesta **una pregunta más**: entre la versión
anterior y la nueva de las pantallas que cambiaron, ¿cuál es mejor y por qué? Las ve como **A y B en
orden aleatorio** (el orquestador guarda qué es cuál); no se le dice cuál es la nueva. En su salida:

```json
"pairwise": {"mejor": "A", "porque": "el CTA se ve sin hacer scroll en 390", "pantallas": ["/precios"],
             "a_es": "iter-1", "b_es": "iter-2"}
```

La guía oficial de dynamic workflows lo dice así: *la comparación por pares es más fiable que la nota
absoluta* (el patrón *tournament*). La nota se mantiene —quitarla rompería los históricos—, pero el
par manda cuando discrepan: si la media sube y **la mayoría de los jueces prefiere la anterior**, la
iteración **no cuenta como mejora** para la regla de parada de §6 y se anota en `RESULT.md`
(«la nota sube, el par dice que no»). Es la defensa contra un juez que puntúa alto o bajo por costumbre.

### 4. Gate PASS estricto — **el categórico primero**

El orden importa y no es cosmético: **el veredicto categórico es la salida más fiable del bucle y
la media es la menos fiable.** En las 3 rondas de Lidia solo 4 de sus 8 dimensiones se movieron,
así que la media divide entre 8 una señal que llevan 4; su gate binario, en cambio, aguantó «con
ayuda» dos rondas mientras la media subía y solo cambió con evidencia en 3 anchos (AUD-11).

**Paso 1 — gates categóricos (bloqueantes, se evalúan antes que ningún número):**

| Criterio | Umbral |
|----------|--------|
| Lidia veredicto | «¿lo consigue sola / volvería mañana?» = **Sí** + ninguna página en "Confuso"/"Muy Confuso" (`con ayuda` NO es aprobado) |
| Findings P0 abiertos | **0** |
| `target_sha` de los 3 auditores | **idéntico** (§1b) — si no, la ronda es inválida y no se promedia |
| Ignacio delta vs Vera | ∈ [1.0, 3.0] (si <1.0 = no fue adversarial; si >3.0 = divergencia, escalar al Supervisor) |

**Paso 2 — umbrales numéricos (solo si el paso 1 pasa):**

| Criterio | Umbral |
|----------|--------|
| `score_wave` (con `score_profiled` de Lidia) | ≥ **9.0** |
| Vera promedio | ≥ **9.0** — fuente única del umbral; el `7.5` de su ficha y su `trend.json` era un segundo umbral contradictorio y está retirado |

> ⚠️ **Honestidad sobre este gate (AUD-15).** Excluir las dimensiones N/A corrige *una* causa —una
> dimensión imposible arrastrando la media— **sin relajar el listón**, que es lo que haría bajar el
> número. Pero **no rescata el 9.0**: el 7.89 recalculado sigue lejos, y el resto del hueco son los
> ejes de Vera y los descuentos de Ignacio, que es otra conversación. Mientras eso siga así, una
> wave como TPL1-W3 **escalará al Usuario igualmente** — es decir, la salida de emergencia se usa
> como camino normal. Si tras dos waves más el gate sigue sin discriminar nunca, hay que
> replantearlo por perfil de producto en vez de fingir que discrimina.

> ⚠️ **Y sobre la regla de parada de +0.3 (§6).** Hoy compara un delta (en iter-3 fue **+0.07**)
> contra un ruido **que nadie ha medido**. Si la σ de Lidia consigo misma resultara ~0.5 —
> plausible—, toda la progresión 6.6→7.1→7.75 cabría dentro del ruido y esa regla no significaría
> nada. Se mide en `.claude/agents/lidia-naive-tester/measurement-protocol.md` §5 (5 pasadas sobre
> un build congelado); **hasta entonces, la regla de parada se usa como señal para escalar a un
> humano, no como veredicto.**

### 4b. Fixture de calibración con errores plantados (KIT-8)

El aviso de arriba deja el bucle midiendo con un instrumento sin calibrar: no sabemos ni la σ del
auditor consigo mismo, ni **su tasa de falsos positivos**, y las dos entran en cada score que
publicamos. La σ se mide repitiendo (protocolo de Lidia §5). Esta sección resuelve la otra mitad, y
es barata: **un artefacto con defectos conocidos y contados de antemano.**

Es el Paso 6-7 del kit 08 traído aquí: *ejemplo de práctica con errores plantados a propósito, y
correr el sistema contra él*. Su lógica es que **un auditor que nunca se ha medido contra una
respuesta conocida no es un instrumento, es una opinión con decimales**.

**Cómo se monta** — cuatro pasos, ninguno necesita herramienta nueva:

1. **Congela un artefacto real** del proyecto (una pantalla, un informe, un correo, un documento) y
   duplícalo. Real, no sintético: un fixture de juguete mide la capacidad de leer juguetes.
2. **Planta N defectos catalogados** en la copia, cada uno con su tipo, su severidad esperada y su
   ubicación exacta. **La lista se escribe ANTES y se guarda fuera del alcance del auditor** — si
   puede leerla, la prueba no mide nada. Mezcla los fáciles con los que se ven de refilón: un
   fixture que solo lleva errores obvios mide lo obvio.
3. **Pasa el auditor a ciegas**, con su prompt normal, sin decirle que es un fixture ni cuántos
   defectos hay.
4. **Cuenta las dos cosas**: **recall** (cuántos de los N plantados cazó — medio punto al que
   detecta el defecto pero le pone la severidad equivocada) y **falsos positivos** (cuántos
   hallazgos marca que ni estaban plantados ni son defectos reales del artefacto). El segundo número
   es el que decide si al auditor se le puede hacer caso: uno con recall alto y FP alto no filtra,
   solo hace ruido caro.

**Las dos mediciones reales de esta casa** (plan `2026-08-16-agents-hq-reorg`):

| Fecha | Qué se midió | Resultado |
|---|---|---|
| **2026-08-16** (PRU-9) | Auditor de negocio contra un fixture de **15 errores plantados** | **14,5 / 15** cazados · **0 falsos positivos** |
| **2026-08-17** | El agente `nuria-receptora` ordenando **3 correos de calidad conocida** de antemano | Orden **correcto**, con **6,6 puntos** de distancia entre el mejor y el peor |

La segunda es una variante útil cuando no hay defectos que plantar: en vez de recall, se mide
**capacidad de ordenar**. Un auditor que pone el mejor y el peor caso a 6,6 puntos de distancia
discrimina; uno que los deja a 0,5 no, por mucho que su número parezca preciso.

> ⚠️ **El aviso honesto de PRU-9, y es lo más importante de esta sección: una prueba en la que se
> saca el 97 % está EN TECHO y por tanto NO discrimina.** Un 14,5/15 no demuestra que el auditor sea
> bueno: demuestra que el fixture era fácil para él. Con la puntuación pegada al máximo no se puede
> distinguir una versión del auditor de la siguiente, que es justo para lo que sirve calibrar. Para
> calibrar de verdad hacen falta **fixtures más difíciles** — defectos sutiles, defectos que parecen
> deliberados (`// workaround:`), y algún artefacto **sin ningún defecto plantado** para que el
> falso positivo tenga dónde aparecer. Mientras el fixture no haga fallar al auditor alguna vez, su
> resultado dice más del fixture que del auditor.

**Cuándo se corre** (no en cada ronda, o se convierte en ceremonia): al **estrenar** un auditor
—antes de que su score cuente para un gate, o sea, en la promoción a fase 4 de
`rules/agent-autonomy-ladder.md`—, al **cambiar su rúbrica o su prompt**, y una vez por trimestre
sobre los que ya operan. El resultado (fecha, N, recall, FP) se anota en el `memory.md` del auditor:
sin esa línea escrita, la siguiente sesión vuelve a no saber si su número vale algo.

### 5. Bucle de mejora (si score < 9.0)

1. **El fix lo aplica el Tech Lead en la sesión** — no un subagente: arreglar exige ver el código,
   el boceto y la conversación, que es justo lo que un contexto limpio no tiene. De los P0/P1, solo
   los **confirmados** en §2d. Consume:
   - `lidia/REPORT.md` (P0 y P1)
   - `vera/findings.json` (todo lo de severity ≥ medium)
   - `ignacio/REPORT.md` (UGLY + AMATEUR + PLACEHOLDER + INCONSISTENT)
2. Implementa fixes (en worktree si se está paralelizando; en main si es wave única) siguiendo
   `patterns/stack/` (`estilos` · `componentes` · `accesibilidad`) y cerrando cada pantalla tocada
   con la skill `ux-reviewer`. Si un finding obliga a **replantear la forma** de la pantalla, eso ya
   no es un fix: es `disenar-pantalla`, media ronda.
3. `iteration_n += 1` → vuelve al paso 2 (re-ejecutar los 3 auditores).
4. Actualizar `.docs/feedback/qa-loop/<WAVE_ID>/RESULT.md` con la fila de la iteración.

### 6. Tope de iteraciones

- Máximo **3 iteraciones** consecutivas (`audit-team.md` §3: ≤3 rondas por puerta, de la 2ª en
  adelante solo sobre el diff). Perseguir cada hallazgo hasta el último lleva
  a sobreingeniería.
- Si tras 3 iteraciones no se alcanza `score_wave ≥ 9.0` **o** el score no mejora ≥ 0.3 entre dos
  iteraciones consecutivas **o** la comparación por pares (§3b) dice que la nueva no es mejor:
  - **Escalar al Supervisor** por el canal que exista en la máquina (`CLAUDE.md` regla 4; aquí,
    Telegram): `python3 .claude/scripts/avisar.py "BLOCKED [proyecto]: QA loop wave <ID> no converge —
    score actual <X> tras <n> iter"`. Si sale con 1, el aviso no llegó: dilo en `RESULT.md`.
  - Documentar el bloqueo en `RESULT.md`.
  - Detener el loop.

### 7. Cierre

Al PASS:
- **Gate del acta**: `python3 .claude/scripts/gate_auditor.py .docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/acta.json`
  en 0. Con 1, la wave no cierra aunque la nota llegue: falta un auditor distinto del autor, se pasó un
  tope o hay un P0/P1 sin validar (`audit-team.md` §1).
- Registrar a cada juez: `agent_registry.py add … --puerta ui --hallazgos N --validados V --descartados D`.
- Marcar la wave como `[x]` en `tasks.md`.
- Actualizar `MEMORY.md` con la decisión final.
- Notificar por el mismo canal:
  `python3 .claude/scripts/avisar.py "DONE [proyecto]: QA loop wave <ID> PASS avg <X>"`.

---

## Estructura de output

```
.docs/feedback/qa-loop/
└── <WAVE_ID>/
    ├── RESULT.md                        ← trazabilidad de versiones, score final
    ├── iter-1/
    │   ├── acta.json                    ← auditores, rondas y validación de cada P0/P1 (§2d)
    │   ├── lidia/   { REPORT.md, trend-delta.json, screenshots/ }
    │   ├── vera/    { REPORT.md, findings.json, screenshots/ }
    │   └── ignacio/ { REPORT.md, screenshots/ }
    ├── iter-2/...
    └── iter-N/
```

> `.gitignore`: los screenshots son grandes — versiona solo `REPORT.md`/`findings.json`/`RESULT.md`
> (`.docs/feedback/*/**/screenshots/*.png`). Al crear un agente, `create-agent` paso 8 lo añade.

**Gate de formato antes de cerrar la iteración** (AUD-7) — cuesta un segundo y evita descubrir en
la ronda 4 que las rondas 1-3 no se pueden comparar:

```bash
python3 .claude/scripts/trend_lint.py .docs/feedback/qa-loop/<WAVE_ID>/    # exit 1 = arréglalo
```

Comprueba claves estables, que **la media declarada sea de verdad la media de las dimensiones**,
que el perfil y las N/A sean coherentes, que el bloque `run` esté completo (modelo exacto, no
alias) y qué cobertura de anclas trae la ronda. Esquema:
`.claude/templates/trend-delta.schema.json`.

---

## Anti-patrones

- ❌ Ignorar Ignacio porque "está siendo duro" → su delta vs Vera es métrica de salud del proceso.
- ❌ Cerrar la wave con `score_wave = 8.9` "está cerca" → el gate es ≥ 9.0 estricto.
- ❌ Re-lanzar sin haber tocado código entre iteraciones → estás malgastando contexto.
- ❌ Lanzar QA loop sobre código con errores de build → verifica build antes (paso 1).
- ❌ Saltar el verdict categórico de Lidia ("¿Volvería mañana?") aunque el score numérico esté bien.
- ❌ **Parchear en caliente mientras los auditores corren** → destruye la ronda (§1b). Ya pasó, y
  el 7.55 con el que se cerró TPL1-W3 no describe ningún objeto real.
- ❌ Promediar las notas de auditores que miraron **builds distintos**.
- ❌ Dar por bueno el objeto porque el sha no cambió → el sha no ve el bundle servido ni la API (§1b.5).
- ❌ Creerse una «pantalla vacía» sin mirar si hubo un `429`, o lanzar tres auditores con la misma
  cuenta (§2c).
- ❌ Reportar un contraste de 1,00 como hallazgo → es la firma de un `oklch()` mal leído (§2c).
- ❌ Leer los `trend.json` de los auditores como su boletín de notas: miden **el producto** (AUD-1).
- ❌ Contar como cobertura un auditor que **nunca ha corrido** (§2b) — parece cobertura y no la da.
- ❌ Cambiar el perfil de rúbrica a mitad de ronda para que salga mejor el número.
- ❌ Arreglar un P0/P1 que nadie validó, o validarlo pasando solo la conclusión del juez (§2d).
- ❌ Contar como mejora una iteración en la que la nota sube y los jueces prefieren la anterior (§3b).
- ❌ Una cuarta iteración, o re-auditar la web entera desde la 2ª (§6).
- ❌ Cerrar la ronda sin pasar `trend_lint.py` sobre el `trend-delta.json` de Lidia (exit 1 = las
  rondas no se pueden comparar entre sí, y el fallo aparece al parsear, no al auditar).
- ❌ Tratar el `+0.3` de la regla de parada como un umbral con significado estadístico mientras la
  σ siga sin medirse.
- ❌ Promover a un auditor a que su score cuente para un gate **sin haberlo pasado nunca por un
  fixture de errores plantados** (§4b) → su tasa de falsos positivos es literalmente desconocida.
- ❌ Enseñarle al auditor la lista de defectos plantados, o dejársela donde pueda leerla → la
  prueba deja de medir.
- ❌ Presentar un 14,5/15 como prueba de que el auditor es bueno → **eso es techo**: mide que el
  fixture era fácil, no que él acierte (§4b).
- ❌ Contar solo el recall del fixture y no los falsos positivos → un auditor que lo caza todo y
  además marca lo que no existe no filtra nada, solo hace ruido caro.
- ❌ Plantar los defectos en un artefacto sintético en vez de en uno real del proyecto.

---

## Integración con SpecKit

En `tasks.md` de cada wave con UI, añade el item de QA como gate de cierre:

```markdown
## Wave N — [Feature]

- [ ] TN.1 ... [implementación]
- [ ] TN.QA — QA Loop (Lidia + Vera + Ignacio) hasta score ≥ 9.0
  - referencia: .claude/rules/qa-loop.md
  - output: .docs/feedback/qa-loop/WN/
```

---

_Rule version: 1.4 · 2026-10-31 (sub-ola 3.11): §2d validación de cada P0/P1 por un verificador
limpio y acta de la iteración (EQ-D13, EQ-1); §3b comparación por pares (EQ-36); topes de la puerta y
tope de 3 iteraciones, de la 2ª en adelante solo sobre el diff (EQ-D8); el cierre exige `gate_auditor.py`.
v1.3 · 2026-10-21 (sub-ola 2.16): §1b.5 certificar el objeto al abrir y al cerrar
(`certifica_objeto.py`, MO-51, de elvion) y §1b.6 congelar también commits, build y datos; §2c QA en
paralelo contra un despliegue vivo (MO-27, de AMC); el disparo autónomo pasa a `/goal` (MO-30).
v1.1 · 2026-08-08 · adaptada de un patrón en producción (productivity_system).
v1.1 (AUD-1/3/5/7/8/9/11/15): §1b build congelado — la causa raíz que invalidó iter-3 · §2b dueño
único por dimensión y huecos declarados · §3 el score de Lidia pasa a `score_profiled` · §4 los
gates categóricos se evalúan ANTES que los numéricos, con el aviso honesto de que el 9.0 sigue sin
alcanzarse y de que el `+0.3` no tiene σ detrás · gate de formato con `trend_lint.py`.
v1.2 (2026-08-17, KIT-8): §4b fixture de calibración con errores plantados — cierra la otra mitad
del hueco que declara §4 (la σ mide reproducibilidad; el fixture mide recall y falsos positivos),
con las dos mediciones reales de 2026-08-16 y 2026-08-17 y el aviso de techo. Fuente vendorizada en
`resources/kits-referencia/`._
