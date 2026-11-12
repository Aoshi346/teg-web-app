---
paths:
  - "**/design-system.md"
  - "**/DESIGN.md"
  - "**/*.dc.html"
  - ".claude/patterns/diseno/**"
  - ".claude/scripts/gate_diseno.py"
  - "resources/referencias-diseno/**"
  - ".claude/skills/movimiento/**"
  - ".claude/hooks/aviso-envio-externo.sh"
  - ".claude/envios-externos.json"
  - ".claude/proyecto-delicado.md"
  - ".claude/templates/envios-externos.json"
  - ".claude/templates/proyecto-delicado.md"
  - "**/brand.html"
  - "**/bocetos/**"
  - ".docs/plans/*/wireframes/**"
  - ".docs/plans/*/mockups/**"
  - ".claude/skills/marca/**"
  - ".claude/skills/disenar-pantalla/**"
  - ".claude/skills/nueva-pantalla/**"
  - ".claude/skills/direcciones-de-arte/**"
  - ".claude/skills/ux-reviewer/**"
  - ".claude/skills/impeccable/**"
  - ".claude/skills/review-animations/**"
  - ".claude/skills/animation-performance/**"
  - ".claude/skills/mobile-native/**"
  - ".claude/skills/break-ui/**"
  - ".claude/skills/ui-ux-pro-max-design/**"
  - ".claude/resources/referencias-diseno/**"
  - ".claude/templates/skills-opcionales/shadcn/**"
  - ".claude/scripts/gate_fases_diseno.py"
  - ".claude/hooks/gate-fases-diseno.sh"
  - ".claude/scripts/previsualizar_tokens.py"
  - ".claude/templates/frontend-screens/**"
  - ".claude/smoke/diseno-modos/**"
  - "**/mockup-cerrado.md"
---
# Motores y fases de diseño — quién manda cuando dos dicen cosas distintas, y en qué orden se diseña

> **Cuándo aplicar:** siempre que haya **más de una voz** opinando sobre cómo se ve algo: el skill
> oficial `frontend-design` (que se auto-activa al tocar UI), nuestro canon `patterns/diseno/`, el
> detector de Impeccable, `superdesign`, Claude Design (la web aparte cierra el 14-12-2026) y las
> propias skills de la casa (§0-§8). Y cuando hay que construir interfaz y todavía no está decidido
> cómo se ve: **el orden de las fases** marca → low-fi → high-fi → mockup → backend (Parte F, §F0-§F5,
> que hasta el 31-10 era la rule `fases-diseno`).
>
> **NO aplicar:** para la **técnica** en sí (qué tipografía, qué movimiento, qué composición) — eso
> es `patterns/diseno/` · para decidir **qué pantallas** hacen falta (`/producto`, que va antes) ·
> para un cambio de una pantalla que ya existe dentro de un sistema visual ya decidido
> (`disenar-pantalla` a secas) · para el tono del **texto** (`escribir-copy`) · para **auditar** lo
> construido (`rules/qa-loop.md`) · para la seguridad de conectar un servidor MCP (`rules/security.md` §MCP).
>
> **Relacionado:** `skills/marca` (fases 0-1) · `skills/disenar-pantalla` (fases 2-3) ·
> `skills/nueva-pantalla` (fase 4) · `patterns/diseno/README.md` · `patterns/diseno/perfiles.yaml` ·
> `patterns/stack/frontend-nueva-pantalla.md` (el molde de 10 ficheros) ·
> `patterns/stack/frontend-design-system.md` (cómo se declaran los tokens) ·
> `resources/referencias-diseno/` · `rules/qa-loop.md` (la fase 5) · `rules/html-output.md`
> §excepción de tipografía · `rules/layer-decision.md` (por qué esto es una rule y no un párrafo suelto).

---

## 0. El problema, y por qué no se arregla escribiendo mejor una de las voces

Desde el 2026-09-18 esta máquina tiene **cuatro motores de diseño activos a la vez**, y tres de
ellos no los escribimos nosotros:

| Motor | Qué es | Se activa |
|---|---|---|
| **`frontend-design`** (Anthropic) | La base de gusto: obliga a comprometerse con una dirección estética antes de escribir CSS, y lista los 5 clusters del «look de IA» | **Solo, al tocar UI.** No lo invoca nadie |
| **Impeccable** | 24 comandos de retoque + un **detector determinista** de 59 reglas (versión 4.6.0) que corre sin modelo | A mano, o desde `scripts/gate_diseno.py` |
| **`superdesign`** | Lienzo: genera pantallas y variantes, extrae el ADN visual de una URL | Desde `skills/marca` paso 3 |
| **Claude Design** | Canvas `.dc.html` y artifacts de claude.ai. **La web aparte cierra el 14-12-2026**: solo se LEE (paso 0 de `marca`, tool `DesignSync`) hasta esa fecha, y ya no es el escaparate (§F1b) | A petición del Usuario; publicar fuera del repo es decisión pendiente (U.19) |
| **Codex** (OpenAI, `codex-cli`) — *desde el 2026-09-19* | Un **segundo modelo** que lee las mismas skills (`.agents/skills/` → `.claude/skills/`) y el mismo `AGENTS.md` | Lo lanza Claude con `codex exec`, o el Usuario directamente (§6) |

Más el nuestro: `patterns/diseno/`, las skills y los auditores.

**Cuando dos de esas voces dicen cosas distintas en el mismo contexto, el modelo elige la última que
ha leído.** Eso no es un fallo del modelo: es lo que pasa siempre que un sistema tiene varias
fuentes y ninguna jerarquía escrita. Por eso esta rule no intenta que las voces coincidan —no
coinciden, y algunas tienen razón donde nosotros no— sino que **declara el orden**.

---

## 1. El orden de autoridad

De arriba abajo. Gana el primero que tenga algo que decir sobre el punto en disputa.

| # | Quién manda | Sobre qué | Por qué está ahí |
|---|---|---|---|
| **1** | **El Usuario** | Su elección de dirección y su ranking | Es quien paga y quien conoce a su cliente. Gana incluso a un detector en verde |
| **2** | **Los hechos del cliente** | Sus colores reales, sus fotos, sus servicios, su logo | Ninguna herramienta inventa por encima de un hecho. «No inventar» |
| **3** | **Las rules del harness** | Dónde van los ficheros, abrir sin red, permisos, aprobaciones | `governance.md`, `security.md`, `html-output.md`. Son de la casa y no se negocian con una herramienta |
| **4** | **`design-system.md` en disco** | Los tokens | Es la regla «EL DISCO MANDA» de §F1b, extendida a todos los motores: gana a `DESIGN.md`, a Claude Design (web o artifact) y a lo que extraiga `superdesign` |
| **5** | **`impeccable detect`** | Lo que MIDE (sus 59 reglas) | **Es lo único reproducible de la lista.** Sobre lo que mide, gana a cualquier prosa — incluida la nuestra |
| **6** | **`frontend-design`** | «¿esto parece hecho por IA?» | Calibrado contra una muestra muchísimo mayor que nuestros diez diseños. Cuando dice que algo es un tell, normalmente lo es |
| **7** | **`patterns/diseno/`** | Gusto y técnica: qué emparejamiento por sector, qué valores, qué defectos arrastran nuestras referencias | Es lo específico de esta casa, que ningún motor externo puede saber. **Nunca bloquea** |
| **8** | **Prosa de los comandos de Impeccable · salida de `superdesign`** | Sugerencias sobre un artefacto | No conocen el brief ni al cliente |

**La regla de lectura, en una frase:** cuanto más arriba, más cerca de un hecho; cuanto más abajo,
más cerca de una opinión. Y una opinión bien escrita sigue siendo una opinión.

---

## 2. Los choques concretos, ya resueltos

No son hipotéticos: los tres salieron al escribir el canon, y están resueltos en su documento.

| Choque | Dónde está resuelto | Resumen |
|---|---|---|
| `frontend-design` lista **T1** (línea itálica en el titular) y **T4** (eyebrow) como señales de página generada | `patterns/diseno/tipografia.md` §5 | Tiene razón: nuestro T1 cae dentro de su descripción sin trampa. La diferencia está en su propia frase *«whatever the subject»* — el tell es el cromo que aparece sea cual sea el tema. **Tope medible: máximo 2 rasgos de sus 5 clusters por página, cada uno justificado con una frase que solo valga para ESE brief.** Si no puedes escribir la frase, el rasgo sobra |
| `frontend-design` dice que los reveals sección a sección **leen como generados por IA**, y pide *un solo momento orquestado* | `patterns/diseno/movimiento.md` §9 | Él tiene razón en la **cantidad**, nosotros en el **mecanismo** (mejora progresiva, easing largo). Lo que salva al reveal de ser relleno es que **exprese la metáfora del sector** (T18). Y se dice la consecuencia incómoda: el nivel 1 es más movimiento del que él recomienda, y se elige a sabiendas |
| `calibration-v2.md:77` penaliza toda duración **>500 ms**, y los reveals medidos duran 0,7-0,9 s | `patterns/diseno/movimiento.md` §10 | Faltaba la frontera: micro-interacción ≤400 ms · reveal 0,7-0,9 s · ambiente 3-30 s, con el zoom de imagen al hover como excepción nombrada hasta 0,8 s. **Es criterio, no mecanismo**: A2 sigue siendo el número que aplica el auditor hasta que se corrija el fichero compartido |

**Cómo se resuelve uno nuevo:** se escribe en el documento del canon que lo toca, citando la línea
del motor con el que choca, y se deja una **regla operativa medible**. Lo que no vale es elegir en
silencio ni borrar el conflicto.

---

## 3. El reparto de los 24 comandos de Impeccable

> Nosotros mandamos en el **QUÉ** (referencias, dirección, contenido real, perfil, tokens).
> Impeccable manda en el **CÓMO se retoca**, y en el detector.

| Comando | Cuándo se usa aquí |
|---|---|
| `init`, `extract` | Una vez por proyecto de cliente · `extract` lo llama el paso 3 de `marca` como **segunda opinión**, nunca como fuente única |
| `craft`, `generate`, `shape` | Andamiaje dentro de `direcciones-de-arte`, **subordinado al presupuesto y al contenido real**: lo que devuelva con 200 líneas es un boceto, no una dirección |
| `animate` | Dentro de `movimiento`, **después** de nombrar la metáfora. Antes, sale genérico |
| `typeset`, `colorize`, `layout`, `delight`, `bolder`, `quieter`, `distill`, `overdrive`, `clarify`, `adapt`, `optimize`, `polish`, `live` | **El bucle de retoque sobre la URL viva.** Adoptados tal cual; lo nuestro es decidir *cuándo* y *contra qué objetivo*. Es la evidencia medida del corpus (15 commits en 41 minutos arreglando contraste) convertida en herramienta |
| `harden` | Último paso antes de entregar a auditoría. Se solapa con T23: T23 dice **qué** andamiaje, `harden` lo aplica |
| `document`, `onboard` | **No adoptamos su formato como fuente.** `DESIGN.md` es derivado de `design-system.md`, nunca al revés |
| `critique`, `audit`, `detect` | Auditoría: `detect` va dentro de `scripts/gate_diseno.py`; `critique` y `audit` son una segunda opinión, no el gate |

**No se crea una skill por comando.** 24 comandos son 24 opciones más que el modelo pondera en cada
sesión (`rules/layer-decision.md`): esta tabla es el enrutado, y con eso basta.

---

## 4. Claude Design: el escaparate, no la fuente

Sin cambios respecto a §F1b —**el disco manda**— y una frontera que se añade:

- El **canvas** (`design`, ficheros `.dc.html`) sirve para los modos 🤝/✍️ de `producto` y para
  artboards de baja fidelidad.
- **Las direcciones de arte NO se comparan en el canvas**: se comparan en la **galería de
  thumbnails** de `direcciones-de-arte`, porque el punto es ver **HTML real renderizado**, con su
  tipografía, su movimiento y su comportamiento — no una maqueta.
- `check_design_login.py` mantiene sus tres veredictos, y **«no medible» no es «no autorizado»**.

---

## 5. Límites honestos

- **Esto es criterio, no mecanismo.** Ningún hook comprueba que se respete el orden de autoridad.
  Lo que sí es mecanismo es el escalón 5 (`gate_diseno.py` sale con código ≠ 0) y el escalón 3
  (los hooks y permisos que ya existen). El resto se sostiene porque está escrito y enrutado.
- **`frontend-design` se auto-activa y no controlamos cuándo.** Por eso nuestras rules se escriben
  como *compatibles* con él y no como override: si el modelo recibe dos voces en el mismo contexto,
  elige la más reciente, y perderíamos el choque sin enterarnos.
- **Impeccable es un tercero.** 59 reglas (4.6.0, contadas en su README) que no escribimos, que cambiarán bajo nosotros, y con los
  exit codes **invertidos** respecto a los nuestros. Mitigación: versión pineada y grabada en cada
  JSON; un bump se trata como una recalibración.
- **El orden no se aplica solo a la primera.** Cuando dos motores chocan, alguien tiene que
  **notarlo**. Lo que hace que se note es que los choques conocidos estén escritos (§2): el
  siguiente se parecerá a uno de esos.

---

## 6. Codex — el segundo modelo, no un segundo árbitro

Desde el 2026-09-19 Codex ve las skills de diseño (eran seis; cinco desde que `referencias-visuales`
entró en `marca`, 31-10; verificado con `codex exec` el 19-09, y vigilado por
`scripts/check_skills_codex.py`: Codex **descarta sin avisar** las skills con la `description` por
encima de 1.024 caracteres). Lee el mismo `AGENTS.md`, cuya sección `CODEX-DISENO` le da las reglas
de la casa.

**Dónde entra en el orden de autoridad: en ninguna fila nueva.** Lo que produce Codex es un artefacto
más, y se juzga con la misma escalera que todo lo demás — una dirección suya compite en la galería y
la rankea el Usuario (#1); una revisión suya es una opinión (#8) hasta que el gate (#5) la confirme.

| Uso | Cuándo compensa | Cuándo NO |
|---|---|---|
| **Una dirección de arte más** para `direcciones-de-arte` | Siempre que la galería vaya a tener ≥3 direcciones: dos del mismo modelo se parecen más de lo que parece, y la independencia es justo lo que la galería existe para comprar | Si ya no hay tiempo de rankear: una dirección más sin ranking es ruido |
| **Segunda opinión** sobre una pantalla terminada | Antes del `/qa-loop`, como filtro barato con criterio independiente del que la hizo | Como sustituto de Vera o del gate: no está calibrado, y un revisor sin calibrar es una opinión con decimales (`qa-loop.md` §4b) |

Dos condiciones que no se negocian, porque **Codex no pasa por los permisos ni por los hooks de Claude
Code**: la carpeta de trabajo va acotada (`-C <dir>`, `-s read-only` para revisar y `workspace-write`
solo en la carpeta de su dirección), y su salida es **dato a verificar**, nunca una aprobación
(`agent-security.md` §4b).

> ⚠️ **Lo que manda Codex a OpenAI, y lo que no está resuelto.** Todo lo que Codex lee viaja al
> proveedor. El informe `.docs/plans/2026-08-21-mapa-y-orden/sources/07-codex.md` §8 dejó cuatro
> condiciones para adoptarlo, y **la tercera sigue abierta: no hay DPA firmado ni respuesta escrita
> sobre la retención del tráfico de Codex CLI**. Hasta que la haya, Codex trabaja sobre **material
> público o propio** (la web ya publicada del cliente, el template), **nunca sobre código privado ni
> datos personales de un cliente**. Aquel informe nunca llegó a decidirse (sus items `CDX-*` no
> están en ningún `report.json` ni hay ADR); la adopción de hoy la pidió el Usuario el 2026-09-19.
> Las otras tres condiciones hablan del plugin y de la revisión cruzada que reescribe, no de
> `codex exec` en solo lectura o en una carpeta acotada: comprobado, **0 brokers `app-server`
> colgados** tras varias ejecuciones.
>
> ⚠️ **Lo que falta, dicho como tal.** El plugin de Claude Code que envuelve a Codex **no está
> instalado** en esta máquina ni aparece en ningún marketplace configurado (medido 2026-09-19): la vía
> que hay es `codex exec` por Bash. Instalar ese plugin es cadena de suministro de un tercero
> (`agent-security.md` §5) y lo decide el Usuario.

---

## 7. Vendorizar una skill de terceros — y lo que manda fuera (sub-ola 2.29, SE-40)

Algunas skills de diseño de terceros **mandan material del cliente a un servicio externo**: en fitapp
(T-070), los generadores de logo, identidad e iconos de `ui-ux-pro-max-design` enviaban el texto de la
marca —y con `--logo`, la imagen— a Gemini, AtlasCloud o MuAPI. Una skill así no se instala con el
`/plugin` y ya: se **vendoriza** con la norma general, **`rules/vendoring.md`** (commit fijo, sin el
instalador del autor, `disable-model-invocation: true`, procedencia en `metadata.vendored`, parches
marcados y lo que envía declarado en `.claude/envios-externos.json`). Lo propio de diseño:

- **No instalar** las sub-skills que dupliquen `marca` o el sistema de tokens (en fitapp quedaron
  fuera `brand`, `design-system`, `ui-styling`, `slides` y `banner-design`).
- Los parches de fitapp que conviene repetir: las claves solo del `.env` de la propia skill y solo sus
  nombres; la clave no viaja en una redirección a otro dominio; «para y avisa» en vez de reescribir
  sus scripts cuando fallan.

**«Delicado»** lo decide un marcador, una vez por proyecto: `.claude/proyecto-delicado.md`, cuya primera
línea es el motivo (plantilla: `templates/proyecto-delicado.md`). Lo rellena `arrancar` en su fase de
ética cuando la marca es de un cliente, hay datos de salud o personales de terceros, o el contrato no
cubre a terceros. El hook también lo da por delicado si `CONFIGURACION.yaml` responde
`datos_sensibles: salud` o `datos_reales_desarrollo: si-…`, si el perfil de `design-system.md` es
`web-cliente` o si el arranque habla de datos de salud. Una entrada con `always_ask: true` pregunta en
**cualquier** proyecto, delicado o no: así van los generadores de Pro Max (3.66, decisión del Usuario de
avisar cada vez). En un proyecto delicado pregunta además ante
lo que envía fuera sin declararlo: un `curl`/`wget` que sube algo a un host que no es local, publicar
un Artifact y las tools MCP que suben, crean o mandan. Y la guarda de capturas
(`scripts/guarda_pii_capturas.py`) queda encendida sin bandera.

> **Límite, el del propio hook:** mira el texto del comando y el nombre de la tool. Un envío desde
> dentro de un script, o con un cliente que no es curl/wget, no lo ve. Es el freno para el envío que
> nadie había visto, no una defensa contra quien quiere sacar los datos. Sin nadie delante
> (`claude -p`), su pregunta se queda en denegación: medido en una sesión real de Claude Code 2.1.306
> (el curl no corrió; sin el marcador, sí).

---

## 8. El paquete UI/UX — núcleo y extensión, cada pieza en su fase y su escalón (sub-ola 3.65, UX-D5)

Lo que el template trae para diseñar y revisar interfaz, en **una** tabla: qué es cada pieza, en qué
fase entra (Parte F) y **en qué escalón de §1 pesa su voz** cuando choca con otra. «—» en el escalón
significa que la pieza **produce**, no juzga: lo que sale de ella se juzga con la escalera como todo lo
demás. Lo que aún no existe lleva la sub-ola en la que llega; hasta entonces, la fila es un hueco
declarado, no una pieza.

**Núcleo** — todo proyecto con UI (pack `nucleo` de `packs/packs.yaml`):

| Pieza | Fase | Escalón | Estado |
|---|---|---|---|
| `producto` (qué pantallas) | −1 | — | existe |
| `marca` (identidad → tokens), con la **medición de referencias** dentro (paso 3, `references-visual.md` + `medir_referencia.py`) | 0-1 | — produce · 2 lo que mide del cliente | existe; la skill `referencias-visuales` pasó a ser su paso 3 en 3.65 |
| `direcciones-de-arte` (galería y ranking) | 1.5 | — · el ranking es escalón 1 | existe |
| `disenar-pantalla` (low-fi y high-fi) | 2-3 | — | existe |
| `nueva-pantalla` (molde React; `--mockup`) | 4-5 | — | existe; alcance React declarado en 3.65 |
| `movimiento` + `comprobar_movimiento.py` | 3-5 | 7 la técnica · 5 lo que mide el script | existe |
| `frontend-design` (Anthropic, se auto-activa) | 3-5 | 6 | plugin declarado |
| `patterns/diseno/` (canon de la casa), con el **chequeo a 3 anchos** (`README.md` §Chequeo a 3 anchos, destilado de TasteSkill) | 0-5 | 7 | existe; el chequeo, 3.65 |
| `scripts/gate_diseno.py` (detector de Impeccable + 15 reglas GD) · `--contra-lienzo` (tokens del código frente al lienzo aprobado) · `--dom` (la página pintada) | 3-5 | 5 | existe; los dos modos, GD-15 y sin los FP de GD-07/08, 3.67 |
| `ux-reviewer` — **una** revisión de interfaz en español: anti-patrones de UX + reglas de Vercel fijadas (`references/web-interface-guidelines.md`, `434b7f9`) | 4-5 | 7 los anti-patrones de casa · 8 las reglas de Vercel (terceros, prosa) | existe; fusión en 3.65 |
| `visual-regression` (`vrt.py`) | 5 | 5 | existe |
| `hooks/aviso-envio-externo.sh` + `proyecto-delicado.md` (§7) | todas | 3 | existe (2.29) |
| Pestaña Diseño del report-kit (`gen_diseno.py`) | informes | — | existe |
| `contraste.py` · axe a 1440/768/390 en Aitor · `preparar_navegador.sh` (lo cita `previsualizar_tokens.py`) | 3-5 | 5 · 5 · herramienta | existe (3.64) |
| Gate de fases (`hooks/gate-fases-diseno.sh`, solo avisa; §F3c) y modo maqueta (`templates/frontend-demo/mockup/`) · `previsualizar_tokens.py` (la piel de cada dirección sobre el producto) · mapa de pantallas (`templates/frontend-screens/`) | 4→5 · 1.5 · 4-5 | 3 · — · — | existe (3.67); el gate viaja sin registrar |
| Corpus `resources/referencias-diseno/` (las reglas GD del gate) | 3-5 | 5 vía el gate | existe; viaja con `gate_diseno.py` desde la 3.67 (`propagar.py`) |
| `impeccable` (skill 4.6.0, a mano; comandos que sí y que no en su cabecera) | 3-5 | 8 la prosa · su detector, 5 vía el gate | existe (3.66); el motor binario no está instalado: Decisión pendiente |
| `review-animations` · `animation-performance` · `mobile-native` · `break-ui` (Emil Kowalski, bajo `movimiento`) | 3-5 | 7-8 | existe (3.66) |
| `templates/skills-opcionales/shadcn` (la ofrece `project-setup` solo con `components.json`) | 4-5 | 8 | existe (3.66), opcional |
| Datos de UI/UX Pro Max (`resources/referencias-diseno/terceros/ui-ux-pro-max/`, buscador sin red) | 0-1 | 8 | existe (3.66) |
| `ui-ux-pro-max-design` (generadores de logo, CIP e iconos; Gemini, sin DPA) | 1 | 8 | existe (3.66); el hook pregunta CADA VEZ (`always_ask: true`, §7) |
| `playwright-cli` | — | herramienta | no se trae en 3.66: la vía de navegador la eligió 3.63 |
| Auditores: Vera · Ignacio · Lidia · Aitor · Conrado · `/qa-loop` | 1-5 | juzgan con su rúbrica; ninguno sube por encima del 5 en lo que no mide | existen |

**Extensión «comercio-conversacional»** — solo proyectos con un bot que vende (va con el pack
`conversacional`); sus piezas llegaron en la **3.68**:

| Pieza | Fase | Escalón | Estado |
|---|---|---|---|
| Patrón `chat-ui-comercio.md` en `patterns/stack/` (web y WhatsApp: chips, carrusel 3-8, tarjeta ≤2 acciones, salida al checkout nativo, `aria-live` en el streaming) | 2-3 | 7 | existe (3.68) |
| Skill `probar-widget` (el paso de Playwright de `widget-embed-test`, generalizado: CW1-CW11 a 1440 y 390) | 4-5 | 5 lo que mide | existe (3.68) |
| Filas de venta en `templates/core/ux.md` (tarjeta, carrusel, carrito, pago, humano) · checklist de checkout en Conrado · pautas HAX en `disenar-conversacion` y Nadia | 2-5 | 7 | existe (3.68) |

**Lo que se queda fuera, y por qué:**

| Pieza | Decisión | Por qué |
|---|---|---|
| **TasteSkill** (`Leonxlnx/taste-skill`, MIT) | **No se instala** (UX-D8, opción A). Se toma su **chequeo a 3 anchos** al canon | La dirección la elige el agente **por sorteo** (3 de 20) y aquí la rankea el Usuario (escalón 1); además busca imágenes en internet con material del brief y no sirve para paneles. **Sin medir:** su estudio de 247 webs (no se leyó: `references/research.md` de su repo) y si su `redesign-skill` como cuarta variante gana a nuestro flujo (era X-13, laboratorio saltado el 31-10) |
| `awesome-design-md` · `awesome-design-skills` | Solo lectura en la fase 0 | Escalón 8: son DESIGN.md ajenos, no fuente de tokens (§1, escalón 4) |
| Generadores de UI/UX Pro Max | **Dentro, con aviso CADA VEZ** (decisión del Usuario 18-10, UX-D2; aplicado en 3.66) | Mandan marca y logo a Google Gemini sin DPA (§7): el hook pregunta en cualquier proyecto y en `claude -p` deniega |
| Sub-skills de Pro Max `brand`, `design-system`, `ui-styling`, `slides`, `banner-design` y las de Emil fuera de las 4 (`emil-design-eng`…) | No se traen | Duplican `marca` o los tokens, o se activarían solas (§7) |

**Sin medir** (lo que habría dicho X-13): si el paquete produce mejores pantallas que lo hecho a mano,
y cuántas veces se invocan de verdad en fitapp las piezas de terceros que 3.66 trae.

---

# Parte F — Las fases de diseño

> Hasta el 31-10-2026 era la rule `fases-diseno` (sub-ola 3.65, UX-10: las dos rules se citaban
> mutuamente). Cada cita antigua `fases-diseno.md §X` es ahora **§FX** de esta rule.
>
> Define **el orden de las cinco fases**, qué se decide en cada una, qué NO se puede decidir todavía,
> y quién la audita. Era la rule que faltaba: de las 42 de este repo, **ninguna ordenaba el diseño
> visual** — cada skill iba por su cuenta y el resultado era predecible.

## F0. El problema, y por qué el orden no es una preferencia

Tres cosas medidas el 2026-09-12 que explican por qué las interfaces salían genéricas:

1. **La marca no existía.** Identidad, guía y kit: **0 ficheros** en todo `.claude/`.
2. **No había baja fidelidad.** *"baja fidelidad"* aparece **una vez** en todo el repo, en prosa,
   delegando en una skill que el harness no controla. Y el «boceto» de `disenar-pantalla` usa tokens
   reales: es **alta** fidelidad. Las fases 2 y 3 estaban colapsadas en la 3.
3. **El backend iba antes que el mockup.** `nueva-pantalla` declara *«requisito no negociable: el
   endpoint del backend ya existe y responde»*, que es exactamente el orden inverso al que sirve
   para enseñar algo pronto.

El orden importa porque **cada fase decide una cosa y solo una**. Mezclarlas no acelera: hace que
gane siempre la discusión más superficial. Si enseñas un boceto con colores, nadie habla de la
estructura; si enseñas la estructura en gris, se habla de la estructura.

---

## F1. Las fases

```
0 REFERENCIAS   mirar y MEDIR cómo lo hacen otros                 → skills/marca paso 3 (medir)
1 MARCA         identidad · guía · kit · logo · tokens · publicar → skills/marca
1.5 DIRECCIONES varios mundos con NOMBRE · galería · ranking      → direcciones-de-arte   (solo web-cliente)
2 LOW-FI        estructura y jerarquía, SIN color de marca        → disenar-pantalla --lowfi
3 HIGH-FI       con los tokens reales, los 4 estados              → disenar-pantalla
4 MOCKUP        funcionando con datos simulados, SIN backend      → nueva-pantalla --mockup
5 DESARROLLO    backend · base de datos · Y el frontend conectado de verdad → django-orm (crud)
```

> **Las dos fases nuevas (2026-09-18) y por qué faltaban.** La **0** existía de hecho pero no como
> paso: `marca` pedía «2-3 referencias» en una tanda de preguntas y esa información **no dejaba
> ningún artefacto** — tres meses después nadie sabía por qué la tipografía era la que era. Ahora se
> MIDEN con navegador (familias y tamaños reales, hex reales, y qué se mueve al hacer scroll) y
> dejan ficha, moodboard y §9 de `design-system.md`.
>
> La **1.5** es el hallazgo entero del análisis de `web_design`: lo que producía los diseños buenos
> no era una propuesta mejor, era **varias direcciones con nombre, comparadas en una galería, con un
> humano rankeando con razones de negocio y una fusión después**. Y solo aplica a `web-cliente`: en
> `producto-panel` el mundo visual ya está decidido por el sistema, y lo que se decide pantalla a
> pantalla es la estructura (§F1c).

| Fase | Qué se decide AQUÍ | Qué NO se puede decidir todavía | Quién la audita |
|---|---|---|---|
| **0 · Referencias** | De dónde sale el criterio: qué se toma de cada web y **qué NO** | Nada propio todavía — aquí solo se mira | El Usuario, validando el moodboard |
| **1 · Marca** | Personalidad, paleta, tipografía, jerarquía, **el logo**, el **perfil** y la **metáfora de movimiento** | Nada de pantallas concretas | `vera-art-director` sobre `brand.html` |
| **1.5 · Direcciones** | **Qué mundo visual** — entre varios, con nombre y lado a lado | La forma de cada pantalla | **El Usuario rankea.** El agente no |
| **2 · Low-fi** | Qué va arriba, qué agrupa con qué, cuántos pasos | El color, la tipografía final, el tono | El Usuario, en 3 minutos |
| **3 · High-fi** | Cómo se ve de verdad, los 4 estados | Cómo se implementa | `vera-art-director` · `aitor-a11y-auditor` |
| **4 · Mockup** | Que el recorrido **funciona** y se puede navegar | Nada de persistencia real | `lidia-naive-tester` · `ignacio-roig` · `/qa-loop` |
| **5 · Desarrollo** | Persistencia, permisos, reglas de negocio, y **sustituir MSW por el backend real** | Ya no se rediscute el diseño | `code-review-gate` · `verification-loops` |

---

## F1b. Las cosas que se llaman «diseño», y cuál hace qué

Nace de una pregunta del Usuario (2026-09-13): *«la parte de diseño es con Claude Design, ¿no? En la
web aparece incluso el manual de marca, y aquí solo veo diseños»*. Tres herramientas compartían
nombre y el harness solo conocía una. **Desde el 2026-10-31 (sub-ola U.19, CL-1) una de ellas tiene
fecha de cierre**: la web aparte de Claude Design **cierra el 14-12-2026** (changelog de Claude
Code v2.1.302). Ninguna fase depende ya de ella.

| | Qué es | Dónde encaja |
|---|---|---|
| **`superdesign`** (plugin) | El **lienzo**: genera pantallas y variantes, extrae el ADN visual de una URL de referencia, hace pósters y gráficos | El motor de las fases **1, 2 y 3** — lo invoca `skills/marca` |
| **`brand.html` servido en local** | El **escaparate**: el manual de marca (tipografía, paleta, espaciado, componentes, logo) en un HTML del repo, en `127.0.0.1` y por túnel SSH | El paso 6 de `skills/marca`. Abre sin red, se audita (Vera) y un cambio se ve en un `git diff` |
| **La web aparte de Claude Design** (cierra el 14-12-2026) | Un proyecto de tipo sistema de diseño en la cuenta de claude.ai | **Solo como origen de importación**, una vez, si el cliente ya mantiene allí su sistema (paso 0), y solo hasta el cierre. **No se publica en ella**: subir la marca a una web que cierra en seis semanas es trabajo perdido |

```
superdesign     GENERAR            el ADN visual de las referencias, las direcciones de logo (paso 3)
      ↓
design-system.md → app.css @theme  LOS TOKENS — esto es lo que lee el código (paso 4)
      ↓
vera-art-director sobre brand.html AUDITAR antes de enseñarlo (paso 5)
      ↓
brand.html en 127.0.0.1 + túnel    ENSEÑAR — el escaparate (paso 6)
```

> **La regla que lo ordena: EL DISCO MANDA.** El código lee los tokens de `src/app.css`, los gates
> miden ficheros del repo, `brand.html` abre sin red y un cambio de marca se ve en un `git diff`. Un
> sistema de diseño cuya fuente esté en una web no compila sin conexión, no se revisa en un PR y,
> como acaba de pasar, **puede cerrar**.
>
> **Única excepción, que es un sentido y no una fuente:** si el cliente ya mantiene su sistema en
> una herramienta suya (la web de Claude Design mientras exista, Figma, un PDF de marca), eso es el
> **origen** y se importa **una vez** al disco. Desde ahí, manda el disco igual.

**Publicar fuera del repo, Decisión pendiente del Usuario (U.19).** Después del cierre, la web
queda en solo lectura; Design funciona dentro de las conversaciones de claude.ai y como artifacts
(los sistemas de la web se mueven a mano, con el banner «Move team design systems»), y `/design`
(research preview) publica desde el CLI «as a Claude Design artifact». Todos van **sobre artifacts**, y la
regla de la casa es «informes: nunca artifact». Mientras el Usuario no decida, **el escaparate es
`brand.html` por túnel** y no se publica en ningún sitio más. Opciones: **A** solo `brand.html`
(lo vigente) · **B** además un Artifact *Design System*, privado, a petición y con el mismo permiso
que tenía el antiguo paso 6 · **C** otra herramienta que elija él.

**Y el logo es parte de la fase 1, no un adorno posterior.** La skill lo trata como una decisión con
tres rutas (ya existe · se eligen 3-4 direcciones distintas · se aplaza con fecha y dueño), nunca
como un campo que se queda vacío. La cuarta ruta —un logo generado que nadie eligió— es la que pasa
sola si no se decide, y es la única que no vale.

---

## F1c. La bifurcación por perfil — la decisión que más cambia el resultado

El perfil se declara en `design-system.md` §0b y sale de `patterns/diseno/perfiles.yaml`.

| | `web-cliente` (landing, web de cliente) | `producto-panel` (producto, panel, web app) |
|---|---|---|
| Fase 1.5 | **Sí**: 3 direcciones con nombre, galería, ranking, fusión | **No**: el mundo visual ya está decidido |
| Fase 3 | `disenar-pantalla` DENTRO de la dirección ganadora | `disenar-pantalla` con 2-3 variantes **estructurales** |
| Movimiento | nivel 2 permitido si la metáfora lo pide | nivel 1 · prohibidos Lenis, cursor propio y botones magnéticos |
| Presupuesto | fichero único, 2.500-5.000 líneas de CSS a mano | el molde de 10 ficheros y **un solo** `@theme` |

⚠️ **El presupuesto de 2.500-5.000 líneas es EXCLUSIVO de `web-cliente`.** Filtrarlo al panel rompe
el molde y el origen único de tokens. Y al revés: aplicar el camino del panel a una landing produce
una sola propuesta, estructural y olvidable — que es exactamente lo que este template hacía hasta
hoy.

---

## F2. Low-fi no es «high-fi en gris»

La diferencia no es el color: es **qué pregunta contesta**.

| | Low-fi | High-fi |
|---|---|---|
| Contesta | ¿Está bien **organizado**? | ¿Está bien **resuelto**? |
| Usa | Cajas, texto real, jerarquía por tamaño | Los tokens del proyecto, los 4 estados |
| **Prohibido** | El color de marca, la tipografía final, iconos decorados | Inventar un color que no esté en `design-system.md` |
| Se tira | **Sí, siempre** | Cuando la pantalla existe |
| Dura | Minutos | Una o dos rondas |

**Texto real desde el low-fi, nunca *lorem ipsum*.** Un bloque de relleno miente sobre el espacio
que ocupa lo que de verdad vas a escribir, y la discusión de estructura se hace sobre una longitud
falsa.

**Cuándo se puede saltar el low-fi:** cuando hay **precedente** — otra pantalla del mismo tipo ya
resuelta en el proyecto. Entonces la estructura ya está decidida y copiarla es lo correcto. Saltarlo
por prisa, no.

---

## F3. El mockup antes que el backend: cómo se resuelve la contradicción

`nueva-pantalla` tiene razón en su requisito y el Usuario tiene razón en su orden. Se resuelve
cambiando **qué** es lo que debe existir antes:

> **No hace falta el backend. Hace falta el CONTRATO.**

Y el contrato se decide en la **fase 2 de `/arrancar`** (el modelo de datos de diseño), no lo
descubre el backend al escribirse. Con el contrato decidido:

```
entidades.json (fase 2 de /arrancar)
   └─► schema.yml de DISEÑO ──► npm run api:types ──► src/types/api.d.ts
                                                          │
                        los 10 ficheros del molde ◄────────┘
                        7 no dependen del backend · ⑩ MSW sirve los datos
```

**El molde ya traía la pieza:** el fichero ⑩ son los handlers de MSW, y `patterns/stack/tests.md`
dice que *«los mismos handlers sirven al navegador en desarrollo»*. Estaba clasificada como «de
prueba» y nadie la usaba como fuente del mockup.

**Lo que NO cambia, y es la razón de la regla original:** sigue prohibido escribir los tipos a mano
«provisionalmente». Si no hay contrato, no hay mockup — hay invención, y ese provisional se queda.

**Cuando llega la fase 5**, el `schema.yml` de diseño **se sustituye** por el que genera
`manage.py spectacular`, se regeneran los tipos y **el diff entre ambos es información**: es donde
aparece lo que el backend cambió sin avisar.

---

### F3b. El momento exacto en que el mockup se convierte en producto

No es difuso y conviene tenerlo escrito, porque es donde se cuelan los «provisionales»:

```
1. El backend existe y responde        →  manage.py spectacular  →  schema.yml REAL
2. Se sustituye el schema.yml de DISEÑO por ese                  →  npm run api:types
3. Los 10 ficheros del molde no se tocan: ya apuntaban a los tipos generados
4. Los handlers de MSW (⑩) dejan de servir al navegador y vuelven a ser SOLO de test
```

**El diff entre los dos `schema.yml` es información, no ruido**: es exactamente lo que el backend
cambió respecto a lo que se acordó en la fase 2. Si ese diff es grande, el contrato se decidió mal
o alguien lo cambió sin avisar — y las dos cosas hay que saberlas antes de que lleguen al QA.

Y el frontend NO está terminado al salir del mockup: está terminado cuando habla con el backend
real y sus estados de error son los de verdad, no los que simulaba MSW.

### F3c. El modo maqueta y el gate de fases (sub-ola 3.67, UX-6)

**El modo maqueta es el patrón de la fase 4**, cosechado de fitapp (`VITE_MAQUETA=1`): el build de
demo sirve en el navegador los handlers de MSW (⑩) **menos `/api/auth/`**, que va siempre a la API
real (se enseña con usuarios de verdad), y deja pasar a la API real los prefijos que ya tienen
backend (`CONNECTED_PREFIXES`), así que se conecta **dominio a dominio** sin tocar las pantallas. Sin
el service worker de MSW: se sustituye `fetch` solo para esas rutas, y no se pelea con el de una PWA.
Con la variable a 0, Vite elimina la rama y los handlers no entran en el bundle (fitapp midió 568 KB
gzip de arranque con la maqueta frente a 280 KB sin ella). La plantilla es
`templates/frontend-demo/mockup/mockup.ts` (`VITE_MOCKUP`), y `nueva-pantalla --mockup` la cita.

**El gate de fases** hace que el orden de §F1 sea mecanismo: `hooks/gate-fases-diseno.sh` +
`scripts/gate_fases_diseno.py`. Ante un `Write`/`Edit` de `models.py`, `models/<x>.py` o una
migración, en un proyecto con interfaz (`.docs/core/design-system.md` o React/Vue/Svelte/Next en un
`package.json`), mira si existe `.docs/diseno/mockup-cerrado.md` con `cerrado:` y `aprobado_por:`.
Si no, **avisa** (al modelo y al Usuario) y deja pasar; el escape es `.docs/diseno/EXENCION-FASES.md`
con `autorizado_por`, `caduca` y un `motivo` de ≥40 caracteres. Cada aviso queda en
`.docs/diseno/avisos-fases.jsonl` con `falsa_alarma: null`, para contar cuántas lo eran **antes** de
endurecerlo. **Se queda solo avisando** (decisión del Usuario, 1-11): `TL_FASES_DISENO=bloquear`
(exit 2) existe, pero activarlo pide una decisión nueva con fecha y firma. **No se registra en el
template** (no es un producto): lo registra el proyecto con UI en su `settings.json` (matcher
`Write|Edit|MultiEdit`). Pruebas: `gate_fases_diseno.py --self-test`
y `smoke/fases-diseno/correr.sh`. **Sin medir:** cuántas falsas alarmas da en un proyecto real.

## F4. Qué se audita cuándo — y el hueco que esto cierra

Medido: **los cinco auditores visuales exigen una URL viva** (`curl -fsS http://localhost:<PORT>/`).
Consecuencia: las fases 1, 2 y 3 no tenían **ningún** control de calidad, y toda la severidad del
harness estaba concentrada en la 5, justo donde cambiar es más caro.

Se cierra sin construir auditores nuevos, solo dejándoles mirar antes:

- **`brand.html`** (fase 1) servido en local **es** una URL viva → Vera puede auditarlo.
- **El boceto de `disenar-pantalla`** (fase 3) es un HTML autocontenido → también.
- **El mockup con MSW** (fase 4) es la aplicación corriendo → aquí entran los cinco y el `/qa-loop`
  completo, **antes de que exista una línea de backend**.

> ⚠️ **Lo que un auditor no puede decir en fase 1-3:** nada sobre rendimiento, sobre integridad de
> datos ni sobre seguridad. Pedirle a Vera un veredicto de accesibilidad de teclado sobre un boceto
> estático es pedirle que invente. Cada fase se audita con lo que esa fase ya tiene.

---

## F5. La excepción de tipografía

`rules/html-output.md` §25 prohíbe Google Fonts y manda tipografía del sistema. Es correcto para los
informes —que tienen que abrir offline— y **hacía imposible representar un kit de marca con
tipografía propia**, que es justo el entregable de la fase 1.

**La excepción, acotada:** los artefactos de **marca y boceto** (`brand.html`, los bocetos de
`disenar-pantalla`) pueden cargar la tipografía real, porque su trabajo es enseñar cómo se va a ver.
Todo lo demás del harness sigue igual. Y con dos condiciones: **fallback declarado siempre** (que sin
red se siga leyendo) y **el aviso en la página** de que esa fuente es de la marca, no del sistema.

---

## Anti-patterns

### De los motores (§0-§8)

- ❌ Tratar la revisión de Codex como aprobación, o dejar que su dirección gane sin pasar por el ranking del Usuario → es un motor más, no un árbitro.
- ❌ Lanzar `codex exec` sin carpeta acotada ni `--sandbox`: no le alcanzan los hooks ni los permisos de Claude Code.
- ❌ Resolver un choque **en silencio**, eligiendo la voz que quedaba mejor en ese momento.
- ❌ Escribir nuestro canon como si `frontend-design` no existiera → el modelo lee las dos y elige
  la última.
- ❌ Tratar la salida de `superdesign` o la prosa de un comando de Impeccable como una decisión:
  son sugerencias sobre un artefacto, y no conocen el brief.
- ❌ Dejar que `DESIGN.md` o Claude Design se conviertan en la fuente de los tokens → en tres
  semanas hay dos sistemas de diseño y ninguno manda.
- ❌ Comparar direcciones de arte en un canvas en vez de en la galería de HTML renderizado.
- ❌ Crear una skill por cada comando de Impeccable.
- ❌ Dar por bueno un `exit 0` de un detector sin mirar si de verdad **pudo** medir: los códigos de
  Impeccable están invertidos respecto a los nuestros, y confundirlos convierte «no se pudo
  escanear» en «está limpio».
- ❌ Instalar una skill de terceros que manda la marca o datos del cliente fuera sin vendorizarla ni
  declarar sus envíos en `.claude/envios-externos.json` (§7).
- ❌ Instalar TasteSkill (o cualquier generador que sortee la dirección) para saltarse el ranking del
  Usuario → la dirección la rankea él (escalón 1); de TasteSkill solo se toma el chequeo a 3 anchos (§8).

### De las fases (Parte F)

- ❌ **Empezar por el high-fi** porque «ya sé cómo va a quedar» → se discute el color y nadie mira la
  estructura, que es lo que costará caro cambiar.
- ❌ Enseñar un low-fi **con el color de marca** → deja de ser low-fi y la fase se pierde.
- ❌ *Lorem ipsum* en cualquier fase → miente sobre el espacio que ocupa el texto real.
- ❌ **Inventar colores en la fase 2 o 3 porque no hay marca** → es la fase 1 la que falta; ir a
  `skills/marca`, no improvisar (el anti-pattern que `disenar-pantalla` ya declara).
- ❌ Escribir los tipos a mano «provisionalmente» para adelantar el mockup → ese provisional se queda,
  y es exactamente lo que `frontend-contrato-con-el-backend.md` avisa.
- ❌ Montar el mockup **sin contrato decidido** → no es un mockup, es una invención que habrá que
  rehacer entera.
- ❌ Dejar toda la auditoría para la fase 5 → es cuando cambiar cuesta diez veces más.
- ❌ Pedir a un auditor un veredicto que su fase no puede sostener (rendimiento sobre un boceto).
- ❌ Cargar una fuente remota en un informe del report-kit → rompe el offline; la excepción es solo
  para marca y bocetos.
- ❌ **Tratar una web de diseño como la fuente de verdad** → el código lee los tokens del disco; un
  sistema que vive solo en una web no compila sin red, no se revisa en un PR y puede cerrar (la web
  aparte de Claude Design cierra el 14-12-2026).
- ❌ **Publicar la marca en un artifact de claude.ai sin la decisión del Usuario** → es la
  «Decisión pendiente» de §F1b; hasta entonces el escaparate es `brand.html` por túnel.
- ❌ **Publicar antes de auditar** → enseñas un borrador con aspecto de manual, y lo que se enseña
  se da por decidido.
- ❌ **Empezar por `superdesign` sin haber mirado si ya existe una marca** (paso 0) → creas una
  marca paralela a la que el cliente ya usa, y no se nota hasta que alguien ve las dos juntas.
- ❌ Generar con `superdesign` **antes** de la entrevista de identidad → sale tu gusto con su logo
  encima.
- ❌ Saltarse el low-fi por prisa. Saltárselo **porque hay precedente** sí es correcto: son cosas
  distintas y conviene decir cuál de las dos estás haciendo.

---

_Rule version: 2.2 · 2026-11-01 · sub-ola 3.67 (UX-6, UX-20, UX-13, UX-19, UX-4): §F3c modo maqueta y
gate de fases; §8 con los modos del gate, `previsualizar_tokens.py`, el mapa de pantallas y el corpus
que viaja. 2.1 · 2026-10-31 · sub-ola 3.66 (UX-D2, UX-D6, UX-11, UX-12, UX-18): las piezas de terceros
de §8 ya existen, vendorizadas y a mano; Impeccable 4.6.0 con 59 reglas; `always_ask: true` en §7.
2.0 · 2026-10-31 · sub-ola 3.65 (UX-10, UX-D5, UX-D8): absorbe la rule `fases-diseno`
como Parte F (§F0-§F5) y añade §8, el paquete UI/UX (núcleo + extensión comercio-conversacional, cada
pieza con su escalón). 1.2 · 2026-10-31 · Claude Design deja de ser el escaparate: la web aparte cierra el
14-12-2026 (U.19, CL-1). 1.1 · 2026-10-21 · §7 vendorizar y declarar los envíos externos (SE-40, sub-ola 2.29,
de fitapp T-070). 1.0 · 2026-09-18 · DIS-1. Nace de tener cuatro motores de diseño activos a la vez
por primera vez, tres de ellos ajenos, y de que los tres primeros choques aparecieran el mismo día
en que se escribió el canon. Parte F: v1.1 · 2026-10-31 (U.19, §F1b sin la web aparte de Claude Design) ·
v1.0 · 2026-09-12, de una petición del Usuario («en la fase de diseño también tienes que tener un
proceso: identidad, guía, kit, low fidelity, high fidelity, mockup funcionando, y luego el backend») y
de la auditoría que midió que la marca no existía, que low-fi aparecía una sola vez en todo el repo, y
que el mockup sin backend estaba explícitamente prohibido._
