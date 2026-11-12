---
paths:
  - ".specify/sessions/*/spec.md"
  - ".specify/sessions/*/plan.md"
  - ".docs/plans/*/plan.md"
  - ".docs/plans/*/arranque/**"
  - ".claude/skills/otto/**"
---
# Plan Gates — cuánta ceremonia lleva esta tarea, y qué gates se ofrecen

> **Cuándo aplicar:** en la **fase de plan** de cualquier tarea. Define un punto único que decide,
> según el **tamaño** y la **confianza**, cuánto andamiaje poner y qué gates ofrecer: research,
> mapa visual, buy-vs-build, ADR, vía de datos y modelo de amenazas. El objetivo es no planificar
> de memoria ni a ciegas en lo grande, y **no molestar** en lo pequeño.
>
> **Relacionado:** `research-driven-planning.md` (el QUÉ del research), `html-output.md` +
> `/visual-map` (el QUÉ del visual), `adr.md` (el QUÉ del ADR), `governance.md` (SpecKit vs cambio
> directo), skill `prompt-contracts` (el contrato — ver la tensión declarada en §1b), skill
> `modelado-amenazas` + `scripts/gate_amenazas.py` (el QUÉ y el CÓMO del Gate F),
> `harness-gotchas.md` §EnterPlanMode (el plan mode de Claude Code: el plan obligatorio de esta rule
> es proceso, no esa función).

---

## 1. Umbral — ¿esto es "tarea grande"?

Reutiliza el umbral que ya vive en `CLAUDE.md` (PLAN MODE) y `governance.md`. Es **tarea grande** si
cumple **cualquiera**:

- Toca **> 3 archivos**, o **≥ 2 módulos/apps**.
- Es una **feature nueva**, un **refactor** o un **módulo/app nuevo**.
- Es un **bug multi-capa** o de causa no clara.
- Cambia **schema/datos**, contratos de API, o arquitectura.

Es **tarea trivial** (NO dispara gates) si:

- Bugfix de causa clara en **1–3 archivos**, cambio de copy/estilo, typo, ajuste de config aislado.

> Regla rápida: si vas a **escribir un plan** (PLAN MODE obligatorio) → es grande → gates ON.
> Si vas directo al fix → es trivial → gates OFF.

---

## 1b. El segundo eje — CONFIANZA (DEC-3, aprobado 2026-08-07)

El tamaño dice **si** hay plan. La confianza dice **cuánto andamiaje** lleva ese plan. Son ejes
distintos: una tarea grande con el enfoque clarísimo y una tarea grande donde no sabes por dónde
empezar necesitan lo contrario.

**Pregúntate antes de andamiar: ¿qué tan seguro estoy de que mi enfoque es el correcto?**

| Confianza en el enfoque | Qué hacer | Por qué |
|---|---|---|
| **Alta** — sé qué ficheros, qué patrón y qué puede fallar | Andamiaje **pesado**: contrato `prompt-contracts` completo, pasos numerados, checklist, criterios de aceptación | El plan ya está en tu cabeza; escribirlo lo hace ejecutable y barato de delegar |
| **Baja** — no sé el enfoque, o hay varias formas y ninguna obvia | Andamiaje **suelto**: prompt deliberadamente subespecificado, Gate 0b a fondo, explorar 2-3 enfoques antes de comprometer nada | Un contrato escrito sobre un enfoque equivocado convierte el error en requisito |

**El andamiaje es una restricción, y las restricciones se pagan con confianza.** Andamiar todo por
defecto se siente como rigor y es lo contrario: el caso documentado son los recordatorios de lista
de tareas, que ayudaban al principio y luego estorbaban porque el modelo se quedaba pegado a los
todos originales aunque a mitad de camino el plan necesitara cambiar.

> ⚠️ **Tensión declarada con `prompt-contracts`.** Esa skill exige contrato
> (GOAL/CONSTRAINTS/FORMAT/FAILURE) **siempre que la tarea toca >3 archivos**. Este eje dice que en
> **baja confianza** el contrato se pospone hasta saber el enfoque. Las dos cosas conviven así:
> **`prompt-contracts` sigue siendo el default; la baja confianza es la excepción documentada**, y
> el contrato no se salta — se **retrasa** hasta después de elicitar (Gate 0b) o de explorar
> enfoques. Si al terminar de explorar sigues con >3 archivos, escribes el contrato entonces.
> Esto está anotado también en la propia skill: si algún día divergen, manda esta tabla y se
> corrige la skill, no al revés.

---

## 2. Los gates (solo si la tarea es grande)

En la fase de plan, **antes de comprometer el plan**, corre el Gate 0 y ofrece los gates A/B. Se
**preguntan** (con `AskUserQuestion` o una línea explícita); el agente **nunca** los auto-activa con
coste alto sin avisar. **No hace falta que el Usuario los pida** — el plan los propone solo.

### Gate 0 — Otto (modo guía) — SIEMPRE en tarea grande, ANTES de A/B

Corre la skill **`/otto`** con el estado de la tarea. Otto devuelve hasta 3
recomendaciones justificadas y copiables (formato QUÉ·POR QUÉ·CÓMO·COSTE): ¿SpecKit o cambio
directo? ¿algún workflow aplicable (/plan-research, /review-branch…)? ¿dashboard/report-kit?
¿worktrees? ¿**modelo y effort** adecuados para esta tarea? ¿algún agente del proyecto desactualizado
que convenga refrescar antes? El TL **presenta el bloque de Otto al Usuario junto con los gates A/B**
— las recomendaciones de coste alto (deep-research, ultracode, team) siguen necesitando el OK
explícito del Usuario. Otto NO ejecuta nada (regla O-1 de su definición).

**Sin preguntas dobles (G8):** si Otto ya recomendó research o mapas visuales en el Gate 0, los
gates A/B NO se preguntan de nuevo como pregunta abierta — se presentan como **confirmación de la
recomendación de Otto** ("Otto recomienda X por Y — ¿lo lanzo?"). Una sola decisión por tema.

### Gate 0b — Clarificación inversa (PRM-1, aprobado 2026-08-07) — SIEMPRE, antes que Otto y que A/B

**"No generes nada todavía: enumérame lo que te falta saber."** Antes de comprometer cualquier plan
grande, el agente **lista sus lagunas** — datos que está a punto de suponer, ambigüedades del
encargo, decisiones que son del Usuario — y pregunta SOLO eso (con `AskUserQuestion` si son pocas y
concretas). No es cortesía: es la técnica sistemática en la que convergen tres fuentes
independientes (el consultor experto "no se limita a suponer los datos sin avisar"). Dos matices:
- Si el prompt "parece completo", el agente tiende a saltarse la entrevista → hazla igual con las
  2-3 dudas de mayor riesgo.
- Prohibidas las preguntas obvias o de relleno: cada pregunta debe cambiar el plan según la respuesta.

### Gate A — Research
> "Esta tarea toca [librerías/APIs/decisión X]. ¿Lanzo research antes de planear?
> (context7 para libs · websearch para post-cutoff · `/deep-research` para cruzar fuentes)."

- Aplica el checklist de `research-driven-planning.md`.
- Si el Usuario dice no, anótalo en el plan ("research omitido por decisión del Usuario").

### Gate B — Mapa visual
> "¿Genero/actualizo los mapas visuales del plan con `/visual-map`?
> (arquitectura · modelo de datos · flujos de usuario · paralelización — HTML self-contained)."

- Si sí → corre `/visual-map` y enlaza los HTML desde el plan / `.docs/plans/<plan>/`.
- Si el código ya cambió y el mapa quedó viejo, el hook `flag-visual-staleness.sh` lo avisa en
  `PROGRESS.log`; este gate es el momento de refrescarlo.

**Y antes del mapa, la pregunta del grafo** — `/visual-map` dibuja mejor si le das los hechos del
código en vez de que los deduzca:

> "El proyecto tiene código real y ≥ ~100 ficheros. ¿Indexo la estructura con `/code-graph` para
> que los mapas salgan del código y no de mi lectura, y para poder responder «¿qué se rompe si
> toco X?»?"

| Ofrecerlo cuando… | NO ofrecerlo cuando… |
|---|---|
| Proyecto con código real (Django, React, WordPress) y del orden de 100 ficheros o más | Menos de unas decenas de ficheros: el grafo no aporta nada |
| Hay una pregunta de impacto antes de un merge o un refactor | Basta un `grep` puntual — no se indexa un repo para una pregunta |
| El grafo existente quedó desfasado (sello de sha viejo) | Repos de **configuración** como este template: `.claude/` + HTML no es un codebase |

⚠️ **Al ofrecerlo, di lo que compra y lo que no.** El único estudio con muestra grande (31 repos)
mide el enfoque de grafo **por debajo** de la exploración normal de ficheros —83% vs 92% de calidad
de respuesta— a cambio de **10× menos tokens y 2,1× menos llamadas**. Lo que se gana es **coste y
determinismo, no precisión**. Venderlo como "mejores respuestas" es vender lo que el dato no dice.
Y el paso 0 de la skill es **preguntar** backend, alcance y destino: indexar es la parte cara y la
que puede tumbar el servidor (pre-flight de RAM obligatorio).

### Gate C — Buy vs build (SPEC-7) — SOLO para **módulo o app NUEVA**

Antes de decidir *cómo* construirlo, decide **si hay que construirlo**. Este gate NO se dispara
para features dentro de un módulo existente: preguntar "¿compramos esto?" en cada feature sería
insoportable.

> "¿Esto es núcleo del negocio o es una pieza que el mercado ya resuelve? Busco alternativas
> (open source y comerciales) antes de escribir código."

Sale **una línea escrita en el plan**, no un informe:

| Naturaleza | Decisión por defecto | Escribe en el plan |
|---|---|---|
| **Commodity** (auth, pagos, envío de email, búsqueda, colas, analítica, CMS…) | **Comprar / integrar / librería** | "X es commodity → usamos [servicio/lib] · alternativas miradas: [A, B] · coste: [€/mes]" |
| **Core del negocio** (lo que nos diferencia y nadie más resuelve igual) | **Construir** | "X es core → construimos · lo comprado no encaja porque [razón concreta]" |

Se justifica **por escrito** en ambos sentidos. El sesgo por defecto se inclina a construir porque
construir es lo que sabemos hacer y lo que apetece; el gate cuesta minutos y libera capacidad para
el core. Si hay que evaluar alternativas de verdad → encadena con el Gate A (research).

**La licencia, en la misma línea — y el plan no cierra sin ella** (MO-29, 2026-10-21). Cada pieza de
fuera que se adopta (librería, motor, servicio) lleva su licencia y el veredicto **para el uso que se
le va a dar**, no para el uso en abstracto. Mirarla al final, con todo construido, obliga a rehacer;
vetarla por la etiqueta también es un error, porque casi todas obligan solo en un uso concreto:

```
X es commodity → usamos <pieza> · licencia: <SPDX> · ¿se modifica? sí/no · ¿se ofrece a terceros por red? sí/no
  · ¿se entrega o se vende con ella dentro? sí/no → vale | vale solo como herramienta interna, tras un adaptador | no vale
```

El criterio, licencia por licencia (LGPL/GPL sí como herramienta de desarrollo; AGPL y PolyForm
nunca en lo que se entrega), y las piezas ya verificadas: **`rules/licenses.md`**, que entra sola al
tocar un manifiesto (`package.json`, `requirements*.txt`, `pyproject.toml`…). La licencia se lee en la
**fuente**, con fecha. En el arranque de un proyecto es la tanda 3.2 de la skill `arrancar`; las
licencias medidas del stack por defecto, en `patterns/stack/ARRANQUE.md` y `frontend-stack.md`.

**Discovery de dominio desconocido** (opcional, dentro de este gate): si el terreno es nuevo, estos
4 prompts arrancan el análisis. Sustituye `[X]` por el dominio:

```
1. Eres un experto en producto, con experiencia en [X]. ¿Qué funcionalidades básicas tiene
   un [X]? Descríbemelas en un listado, ordenado de mayor a menor prioridad.
2. ¿Qué beneficios obtiene el cliente de un [X] para considerar su uso?
3. ¿Qué alternativas tiene a usar un [X] y cuándo pueden ser relevantes?     ← alimenta el buy vs build
4. ¿Cómo es el customer journey normal de un cliente que usa un [X]?
   Descríbeme paso a paso todas las interacciones.
```

Su salida es material para `/schema` (lean-canvas, casos de uso) y para `pol-product-advisor`.

### Gate D — ADR (SPEC-4) — el plan NO cierra sin él si toca arquitectura

Si la tarea grande cambia **arquitectura, schema o un contrato de API**, el plan no se cierra sin su
ADR: contexto · decisión · alternativas descartadas · consecuencias.

```bash
cp .claude/templates/adr-template.md .docs/adr/000N-<slug>.md
```

Se escribe con la decisión **fresca** (durante el plan), no en arqueología posterior. Detalle,
estados, numeración y anti-patterns: **`rules/adr.md`**. Acotado a arquitectura/schema/contrato a
propósito: si se pide ADR para toda tarea grande, no se escribe ninguno.

### Gate E — Vía de datos (KIT-8) — SOLO si el plan depende de una fuente EXTERNA

**Cuándo aplica.** El plan promete algo que depende de datos o herramientas **que no controlamos**:
una web que hay que leer o raspar, un panel o export de un tercero, un fichero que aporta el
cliente (PDF, hoja de cálculo, capturas), una API con clave, o un binario que tiene que estar
instalado en la máquina.

**Cuándo NO aplica** — y el acotamiento es deliberado: nuestra propia base de datos, nuestros
endpoints, ficheros que ya están en el repo, o cualquier plan que no lea nada de fuera. Disparar
este gate en todos los planes lo convertiría en un trámite que se firma sin hacer, que es
exactamente cómo muere un gate.

> "Antes de escribir una línea: **demuéstrame con el caso real que esa fuente se puede leer.**"

**Qué se comprueba.** Una prueba por cada fuente y cada dependencia, **con el caso real del
usuario** — la web de *su* gestoría, *su* PDF, *su* clave — nunca con `example.com` ni con un caso
de juguete. El comando se ejecuta y **su salida se pega en el plan**, con fecha:

```bash
# Una página web: ¿responde, y con qué código?
curl -sIL -o /dev/null -w "%{http_code}\n" "URL_REAL"      # + leerla con WebFetch a la vez
# Un binario: ¿está, y hace lo que creemos?
which PROGRAMA && PROGRAMA --version                        # y después, el comando REAL con un caso pequeño
# Una API con clave: una llamada mínima, y qué devuelve con la clave mal
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $KEY" "https://…/endpoint"
```

Si la fuente es una API con contrato publicado (Postman, OpenAPI), antes de la llamada se indexa ese
contrato y se consulta: skill `external-api-contract`. «No existe ese endpoint» sin haberlo buscado
allí no es un resultado del gate.

Las cuatro respuestas posibles al leer una web, y qué significa cada una:

| Devuelve | Diagnóstico | Vía |
|---|---|---|
| El contenido | ✓ | Ese comando pasa a ser la comprobación de arranque del proyecto |
| Una página de login | La fuente **no** se puede leer, y no es un fallo nuestro: es su diseño | El dato lo aporta el usuario (export, capturas). Suele ser **mejor**: los datos de su panel privado no los consigue ningún raspador |
| HTML casi vacío | Se monta con JavaScript | Navegador automatizado, o la versión estática: sitemap, feed, versión móvil |
| 403 / 401 | Protección anti-bots | Navegador automatizado; si tampoco, la parte se cae del plan |

**Y solo hay tres salidas. "Seguir igual" no es una de ellas:**

1. **✓ Funciona** → se apunta en el plan el comando exacto que lo demostró.
2. **✗ Pero hay vía alternativa** → se prueba **también**, y se apunta cuál quedó. Cambiar *cómo
   entran los datos* (del raspado al fichero que el usuario ya descarga) casi siempre es mejor
   solución que insistir en la vía original.
3. **✗ Y no hay vía** → esa parte **se cae del alcance**, se escribe en el plan bajo "qué queda
   fuera" y se dice en el momento, sin adornos. Un plan que promete menos y cumple vale más que uno
   que promete todo y falla en la primera prueba real.

**Por qué existe.** Es el **fallo documentado nº 1** del kit 08 (`resources/kits-referencia/estandar.md`
§"Los tres errores que más veces han roto un kit"): *se construye la cosa entera y en la primera
prueba real resulta que esa página devuelve un muro de login*. El coste de comprobarlo es un
comando; el de no comprobarlo es todo lo construido encima más la promesa hecha al cliente. Y jamás
se rellena el hueco con una estimación o un dato plausible: lo que no se pudo comprobar se marca
**"sin datos"**.

**Si la fuente es el catálogo de un cliente para un bot que vende** (CB-78), además de leerlo, se mide
si trae lo que el bot necesita, sobre su export y con su API de precio y stock:
`python3 .claude/scripts/catalog_readiness.py <export.json> --price-api '<url>/{id}'`. Nace en sombra
(avisa, sale 0): el informe de huecos se pega en el plan y lo que falte se le pide al cliente antes de
construir. Formato del export y umbrales: el docstring del script; el modelo: `patterns/stack/catalogo-modelo.md`.

Se corre **junto al Gate A** (research), antes de comprometer el plan — no después, cuando la
arquitectura ya asume que la fuente existe. La tabla de fuentes ya conocidas (qué se lee y qué no:
YouTube, redes sociales, carritos, tiendas con anti-bots, paneles privados) está en
`resources/kits-referencia/`, para no volver a descubrirlo cada vez.

### Gate F — Modelo de amenazas (SE-19) — SOLO si el plan cruza una frontera de confianza

**Cuándo aplica.** El plan **crea o cambia** una frontera por donde algo de fuera entra o algo nuestro
sale: un **endpoint público** (sin autenticar, `AllowAny`, formulario abierto) · una **subida de
ficheros** · un **webhook** · una **tool de agente con efecto** (escribe, cobra, envía, cancela) o un
servidor MCP · un **tenant nuevo** o el aislamiento entre clientes · una **integración externa** (API de
terceros, OAuth, CRM, WhatsApp, pagos) · **datos personales nuevos** (un módulo o app nueva que los
guarda o los trata).

**Cuándo NO aplica** — y el acotamiento es deliberado, como en el Gate E: un bugfix (aunque toque el
webhook, no lo crea), copy o estilo, un refactor que no mueve fronteras, o cualquier plan donde todo
sigue entrando y saliendo por donde ya entraba. Disparado en todo plan, se firmaría sin hacer.

> "Antes de comprometer el plan: **qué puede ir mal en cada frontera nueva, qué defensa decidimos y
> cómo la vamos a probar.**"

**Qué se hace.** La skill **`modelado-amenazas`**: una página (`templates/modelo-amenazas.md`) con
fronteras → STRIDE → respuesta (mitigar · eliminar · transferir · aceptar) → defensa decidida →
requisito **ASVS 5.0.0** (`v5.0.0-x.y.z`, del nivel del tipo de proyecto) → cómo se prueba; las cartas de
**LINDDUN GO** que aplican si hay datos personales; y la **Rule of Two** por agente si hay un LLM con
tools. Va junto al plan (`<carpeta-del-plan>/modelo-amenazas.md`).

**Cómo se comprueba** — es un script, no prosa:

```bash
python3 .claude/scripts/gate_amenazas.py <carpeta-del-plan>   # 0 cumple o no aplica · 1 falta · 2 no medible
```

El script detecta en `plan.md`/`spec.md` las líneas que crean una frontera (léxico: da candidatos con su
línea) y, si las hay, exige el modelo y lo valida: ids de ASVS y cartas que **existen**, una fila STRIDE
por frontera, prueba en lo que se mitiga, control cuando un agente tiene las tres propiedades (`interrupt`,
sesión nueva o una persona que confirma) y la firma de **una persona** que lo revisó: el gate rechaza la de
un agente o un modelo por su nombre (agente, Claude, GPT, Codex…). Su `--autoprueba` lleva los sabotajes y
los controles que demuestran que dispara y que calla.

**Y solo hay dos salidas. "Ya lo miraremos" no es una de ellas:**

1. **El modelo existe y pasa** → el plan sigue; Sofía atacará después su columna «Cómo se prueba».
2. **El detector se equivoca** → el plan lo dice por escrito: `Gate F: no aplica — <razón>` (20
   caracteres o más). Sin razón, el gate sale rojo; y si en la carpeta hay un modelo, se valida igual: el
   «no aplica» no tapa un modelo roto.

**Por qué existe.** La propuesta de la revisión integral (`r3-ciberseguridad-harness.md` §2.2, item SE-19,
P0): el SDLC del template no tenía diseño seguro entre los requisitos y el código. Las cuatro preguntas
son las del *OWASP Threat Modeling Cheat Sheet*, que pide hacerlo *«early in the SDLC, such as during the
design phase»*. Acotado a las fronteras es lo que evita que se convierta en el trámite que ya habría
matado al Gate E.

---

## 3. Tabla de decisión

| Tarea | Plan formal | Gate 0b + 0 | A research | B visual | C buy/build | D ADR | E vía de datos | F amenazas |
|-------|:-----------:|:-----------:|:----------:|:--------:|:-----------:|:-----:|:--------------:|:----------:|
| Bugfix 1–3 archivos, causa clara | no | — | — | — | — | — | — | — |
| Cambio de copy / estilo aislado | no | — | — | — | — | — | — | — |
| Feature multi-archivo | sí | **sí** | ofrecer | ofrecer | — | solo si cambia un contrato | **sí, si lee de fuera** | **sí, si cruza una frontera** |
| Refactor > 5 archivos | sí | **sí** | ofrecer | ofrecer | — | solo si cambia límites/contratos | — (no cambia las fuentes) | — (no mueve fronteras) |
| Módulo/app nuevo | sí | **sí** | ofrecer | ofrecer (recomendado; +`/code-graph` si hay ≥~100 ficheros) | **sí** | **sí** | **sí, si lee de fuera** | **sí, si guarda datos personales o abre una frontera** |
| Cambio de schema/arquitectura | sí | **sí** | ofrecer (recomendado) | ofrecer (recomendado) | — | **sí** | **sí, si lee de fuera** | **sí, si cruza una frontera** |
| Integración con un tercero (scraping, export, API con clave, binario) | sí | **sí** | ofrecer | ofrecer | **sí** | solo si cambia un contrato | **sí — es el caso central** | **sí** |

El **eje confianza** (§1b) se aplica encima de toda la tabla: con baja confianza, el plan arranca
suelto y el contrato se escribe después de elicitar. Los **Gates E y F** no dependen del tamaño sino de
la naturaleza: el E lo dispara la **fuente externa** y el F la **frontera de confianza**, no el número
de ficheros (y los dos solo existen en tareas con plan).

---

## Anti-patterns

- ❌ Preguntar por research/visual en un bugfix trivial → ruido; los gates son solo para lo grande.
- ❌ Activar research caro (`/deep-research`, ultracode) sin avisar del coste → ver `research-driven-planning.md`.
- ❌ Comprometer un plan grande sin pasar por los gates "porque ya me lo sé".
- ❌ Regenerar el mapa visual en cada cambio pequeño → se ofrece en plan grande / on-demand, no en cada edit.
- ❌ Ofrecer `/code-graph` en un repo de configuración o de pocas decenas de ficheros → no aporta
  nada y cuesta RAM. Ni venderlo como "mejores respuestas": compra coste y determinismo, no acierto.
- ❌ Andamiar por defecto porque "el andamiaje se siente como rigor" → con baja confianza, elicita antes.
- ❌ Empezar a construir un módulo nuevo sin haber escrito la línea de buy-vs-build.
- ❌ Disparar el gate buy-vs-build en cada feature → solo módulo/app nueva.
- ❌ Cerrar un plan que cambió arquitectura y dejar el ADR "para luego" → luego ya no se recuerdan
  las alternativas.
- ❌ Dar por hecho que una web se puede leer, que un binario está instalado o que una clave funciona
  → es el fallo nº 1 documentado, y aparece cuando ya está todo construido encima (Gate E).
- ❌ Comprobar la vía de datos con `example.com` o con un caso de juguete en vez de con el caso real
  → se comprueba otra cosa y sale ✓ igualmente.
- ❌ Disparar el Gate E en planes que no leen nada de fuera → trámite que se firma sin hacer.
- ❌ Rellenar con una estimación "plausible" el hueco de una fuente que no se pudo leer → lo que no
  se comprobó se marca **"sin datos"** y se recorta la promesa.
- ❌ Comprometer un plan que abre un webhook, una subida de ficheros o una tool con efecto sin su modelo
  de amenazas → la defensa se descubre en el pentest, cuando ya es cara (Gate F).
- ❌ Modelar el sistema entero, o disparar el Gate F en un bugfix → trámite; solo las fronteras que este
  trabajo crea o cambia.
- ❌ Citar un requisito ASVS de memoria → el gate rechaza los que no existen; se sacan de
  `gate_amenazas.py --tipo <tipo>` y se leen en el estándar.

---

_Rule version: 1.3 · 2026-10-20 · +Gate F modelo de amenazas (SE-19, sub-ola 2.25: skill
`modelado-amenazas` + `scripts/gate_amenazas.py`) · v1.2 · 2026-06-21 · +§1b eje confianza (DEC-3), +Gate C buy-vs-build (SPEC-7),
+Gate D ADR (SPEC-4) — aprobados 2026-08-07 · v1.2 (2026-08-17): +Gate E vía de datos (KIT-8,
destilado del Paso 3 del kit 08 — fuente en `resources/kits-referencia/`)_
