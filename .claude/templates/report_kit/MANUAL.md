# Report-kit — el manual largo (el porqué, la historia y el detalle de cada regla)

> **Qué es este fichero.** Hasta la sub-ola 2.15 (21-10-2026, MO-78) era el cuerpo de
> `rules/report-kit.md`: 44 KB que se cargaban enteros cada vez que se tocaba un informe. La rule se
> quedó con lo normativo, en corto; aquí sigue **todo** lo que decía, palabra por palabra, para quien
> necesite el porqué de una regla, su medición o su historia. **Si la rule y este manual dicen cosas
> distintas, manda la rule** — y entonces este manual está desactualizado: arréglalo.
>
> No se carga solo (no es una rule): se lee cuando hace falta. Los números de regla (1-10, 4a-4d,
> 5a-5i, 6b-6c, 9b) son los mismos en los dos sitios.

## El principio que ordena todo lo demás

> **Un entregable que no aparece en el informe NO está entregado.**

No es una aspiración: es la razón de que el informe exista. Si el wireframe vive en una carpeta
suelta, el mensaje al cliente en otra y las evidencias de calibración en una tercera, el informe
deja de ser el mapa del plan y pasa a ser una vista parcial — y quien lo abre se queda con la
impresión de que eso es todo lo que hay.

Se detectó del peor modo posible: un wireframe de portada quedó fuera y el Usuario tuvo que
reclamarlo. La pestaña **Entregables** (§Reglas 9) es el mecanismo que lo cierra, y recoge por
exclusión —todo lo que no tenga pestaña propia— para que no haya que tocar código cada vez que
aparezca un tipo de material nuevo.

## Qué es

Un **set multi-página** (cada "pestaña" es un `.html` autocontenido con la misma topnav) generado
desde **un único `report.json`** (schema: `templates/report_kit/item.schema.json`). Las decisiones
se toman EN el documento y persisten: localStorage en modo estático, disco (`server.py`) en modo
backend, export JSON/MD siempre.

```
report.json  ──build.py──▶  index.html      resumen: KPIs + tablas + mapa conceptual SVG
(+ graph-dataset.json)      structure.html  estructura del código (contrato /code-graph; fixture si no hay)
(+ sources/*.md)            dashboard.html  tareas: 4 vistas (lista · kanban · gantt · mapa mental)
                            diseno.html     referencias · marca · direcciones · wireframes · bocetos · mockups (perfiles proyecto y diseño)
                            entregables.html  mensajes · adjuntos · todo lo demás (y lo visual si el perfil no lleva Diseño)
                            results.html    verdicts con doble evidencia 🔎/👁 + imágenes base64
                            pruebas.html    manual de prueba MANUAL + qué verificó ya el agente
                            fuentes.html    los informes de investigación detrás de los items (si hay sources/)
                            otto.html       sección fija del copiloto (sugerencias + permisos)
```

## Las 4 vistas del dashboard (una sola página, un solo `visible()`)

| Vista | Responde | Notas |
|---|---|---|
| **Lista** por página | qué hay y en qué estado | vista por defecto; selección múltiple + barra masiva |
| **Kanban** | en qué fase está cada cosa | drag&drop entre estados |
| **Gantt** (US-1) | **en qué orden y cuánto dura** | calendario ORIENTATIVO derivado de `effort` |
| **Mapa mental** (US-2) | **la forma del conjunto** — y se decide ahí mismo | plegado por defecto; 4 botones de decisión en la hoja |

Son vistas y no páginas propias **a propósito**: comparten los filtros de arriba, el mismo
`visible()` y la misma persistencia. Un Gantt que no respeta el filtro que acabas de poner miente.

### Gantt — el modelo de planificación, dicho en voz alta
Cada **carril** (epic o página) avanza de uno en uno; `blocks[]` añade precedencias **entre**
carriles. Duración = `effort` (**S=1 · M=3 · L=5 · XL=10** días). Sobre ese grafo se corre CPM real
(pasada adelante/atrás) → holgura y camino crítico (**franja roja bajo la barra**, no borde: un
borde rojo es invisible sobre las barras ámbar y rojas). Ciclos en `blocks[]` no rompen la vista:
se colocan al final y se avisa. Con `start`/`due` el eje pasa a fechas reales y aparece la marca de
"hoy". **La vista declara en su propia cabecera que es orientativa** — un Gantt derivado de
estimaciones no es un compromiso de calendario, y callarlo lo convierte en una promesa falsa.

### Mapa mental — plegado por defecto
Plan → ramas (epic/página) → hojas (tareas). Arranca **plegado**: con >100 items, todo desplegado
no se lee. Las ramas de más de **40** hojas se recortan y remiten a los filtros. La hoja lleva los
mismos 4 botones de decisión (`setDec()`/`save()` reutilizados) y se recolorea al decidir.
Etiquetas recortadas **midiendo** (`fitText`), no contando caracteres: los nombres de epic son de
largo libre y a ojo siempre acaban pisando la columna de al lado.

### `pruebas.html` — el manual para una PERSONA (US-3)
Dos mitades por item: **(a)** el guion paso a paso (qué abrir, qué hacer, qué debes ver, captura de
referencia) y **(b)** qué verificó ya el agente (verdict + doble evidencia + galería), para no
repetir trabajo. Caso chatbot: tabla *frase de entrada · respuesta esperada · respuesta real*.
El guion sale de `item.manual_test`, que se escribe en `tasks.md` (ver abajo) desde los criterios de
aceptación en Dado/Cuando/Entonces. **Si un item no tiene pasos, se deriva uno de `goal` y se marca
`derivado`**: sale genérico a propósito, y la cabecera dice cuántos están así — es el termómetro de
cuántos items no tienen criterio de aceptación de verdad. Lo que marca la persona vive en
`item.tested` (KEEP) y se exporta a markdown para el agente.

## Cómo se escribe un item — los 4 bloques (obligatorio)

Un informe de decisiones falla si quien decide **no entiende qué está aprobando**. Por eso el campo
`desc` de todo item lleva estos cuatro bloques, en este orden y con estos rótulos exactos (el
dashboard los detecta y los pone en párrafos separados):

```
📍 Cómo está ahora — qué hay hoy y qué duele. Con el fichero o el dato concreto.
🎯 Qué queremos conseguir — el resultado observable, no la tarea.
🔧 Cómo se haría — el mecanismo: qué se crea o se toca, con qué herramienta.
🧭 Por qué así y no de otra manera — la alternativa obvia y por qué pierde. Límites honestos.
⚠️ AVISO — (opcional) lo que cuesta, lo que puede salir mal, o lo que no cubre.
```

**Escríbelos para alguien que no conoce la jerga.** Es la parte que más se incumple y la que más
valor tiene:

| Regla | Mal | Bien |
|---|---|---|
| **Explica cada término la primera vez** | "generar tipos desde OpenAPI" | "**OpenAPI** es un fichero que describe la API, como la carta de un restaurante: qué URLs hay y qué devuelve cada una. No se escribe a mano: se genera leyendo el código" |
| **Un ejemplo concreto vale más que la explicación** | "desincronización de contratos entre capas" | "un compañero renombra `nombre` a `nombre_completo`; la pantalla se queda en blanco y nadie se entera hasta que llama un cliente" |
| **Di el coste, no solo el beneficio** | (silencio) | "un rato de configuración la primera vez y casi nada después" |
| **El porqué es una comparación, no un adjetivo** | "es más limpio y escalable" | "la alternativa es mantener dos listas a mano y confiar en acordarse; funciona hasta que alguien tiene prisa" |

**La prueba de que está bien escrito:** que alguien ajeno al proyecto entienda, leyendo solo ese
item, qué se gana y qué se arriesga. Si hace falta preguntar "¿y esto qué es?", el item está a
medias — el lector no está para descifrar, está para decidir.

**`tl_rec` es un campo aparte y NO es del Usuario.** Ahí va la recomendación del agente (bloque A/B/C
y por qué); `note` queda **siempre libre** para que escriba el Usuario. Ningún agente escribe en
`note`.

## Tabla de decisión — qué usar cuándo

Se movió a **`rules/output-choice.md`** (MO-78 en la 2.15 a `html-output.md`; AN-2 en la 3.18 a su rule propia): elegir QUÉ
informe entregar es una decisión anterior al kit, y es la rule que se mira antes de elegir.

## Reglas (no negociables)

1. **Un solo schema.** `item.schema.json` es el canon: `title/desc/goal/status/decision/note/
   verdict/evidence[]/history[]`. **PROHIBIDO inventar el 5º schema de item** — si falta un campo,
   se propone en el schema, no se improvisa en la página. (Antes convivían 4 incompatibles.)
2. **Vocabulario único de status**: `backlog|doing|review|done|blocked`. Muere `wip` y `pend`.
   Checkboxes de tasks.md: ` `→backlog · `>`→doing · `x`→done · `!`→blocked.
3. **Clave localStorage única**: `tlr::<project>::<plan_id>::v1`. Nunca claves ad-hoc (antes había
   4 formatos y colisionaban entre proyectos).
4. **Persistencia del item COMPLETO** (lista `x-keep` del schema: status, decision, note, severity,
   effort, evidence, **tested**) en localStorage Y servidor. El bug histórico de persistir solo 3
   campos en modo estático (evidencias perdidas al recargar) está arreglado — no lo reintroduzcas.
4a. **Toda página que escriba en localStorage serializa la lista `x-keep` ENTERA.** `dashboard.html`
   y `pruebas.html` comparten clave: si una omitiera un campo (p.ej. `tested`), la última en guardar
   lo borraría. Es el mismo bug de las evidencias, un año después y con otro campo. Al añadir un
   campo KEEP hay que tocar `keepOf`/`applyKeep` en **las dos** páginas y `KEEP` en `tasks_to_items.py`.
4b. **El chip de modo explica su propio modo.** El indicador (`solo navegador` / `guardado en disco`)
   lleva un `?` que abre qué implica cada modo y el **comando exacto y copiable** para levantar el
   backend (`cd <plan_dir> && python3 server.py`; `plan_dir` lo inyecta `build.py`). Sin esa
   afordancia el modo servidor existe pero nadie lo encuentra: el usuario decide 100 items en
   localStorage y **el agente no ve ni uno**. Regla: si existe un modo mejor, se ofrece DONDE se
   hace la pregunta, no en una rule.
4c. **Las preferencias de UI se recuerdan, en clave APARTE.** Filtros, vista activa, modo aprobación
   y páginas desplegadas se guardan en `…::ui` — nunca mezclados con las decisiones, que son el dato
   que importa. Al restaurar se **podan los valores que ya no existen** (una épica o etiqueta que
   desapareció al regenerar): un filtro fantasma dejaría la lista vacía sin explicación y parecería
   que el informe está roto. La selección múltiple, en cambio, es efímera a propósito.
4d. **El «🚀 Modo yolo» del dashboard cambia los permisos de verdad (T-101, 2026-09-29).** En modo
   servidor, activarlo aplica `settings_profile.py --yolo on` al proyecto del plan y desactivarlo
   `--yolo off`, que **restaura el bloque `permissions` entero** — no `--perfil estandar`, que nunca
   baja el deny y dejaría push y merge denegados en vez de preguntados (medido con control
   negativo). Cada cambio queda en `<plan>/decisiones.md`, `/api/health` enseña el perfil vigente y
   el hook `yolo-politica.sh` le recuerda la política al agente en cada turno. Por eso `/api/save`
   exige `Content-Type: application/json` (415) y un `Origin` local (403): un endpoint que cambia
   permisos no acepta un POST de cualquier página abierta en el navegador. **Límite honesto:** una
   sesión ya abierta puede no releer `settings.json` hasta reabrirse, y los permisos solo aplican a
   una sesión cuyo proyecto es ESE (no a una que trabaja sobre él por ruta absoluta).
5. **Nav vía `render_nav.py`, PROHIBIDA a mano.** Fuente única `report_kit/nav.json` (items +
   perfiles), marcadores `<!-- NAV:BEGIN/END -->` idempotentes, `--all <plan>` regenera el set.
   La nav a mano en ~19 ficheros fue la causa de la divergencia 8-vs-10 items.
5a. **Lo PERMANENTE no vive en el plan (PV-3).** Un informe de plan es el registro de lo que se
   decidió entonces y se congela con él; el Core dice lo que el proyecto **ES hoy**, así que no
   puede vivir dentro de algo que se cierra. Las páginas declaradas en `nav.json#permanent`
   (`core.html` y sus capas, incluido el Equipo) se generan en **`.docs/core/`**; el resto
   —Dashboard, Flujo, Resultados, Pruebas, Entregables, Fuentes— es de un plan concreto y sigue en
   `.docs/plans/<plan>/`.
   **Un solo juego de enlaces para disco y para servido**, y no es casualidad: desde un plan el Core
   es `../../core/x.html` y desde el Core el plan es `../plans/<plan>/x.html`; en disco resuelven
   solas, y servidas funcionan porque el navegador **descarta los `..` que se pasan de la raíz**
   (RFC 3986 §5.2.4) y `server.py` monta `/core/` y `/plans/`. Mantener dos juegos de rutas sería
   garantizar que uno de los dos se queda viejo.
   **El Core sale SOLO del plan activo** (misma regla que `tasks_registry.py`: continuidad primero,
   fecha del nombre después, **jamás el `mtime`**). Reconstruir un informe de hace tres meses no
   reescribe el Core: `build.py` lo dice y no lo toca.
   ⚠️ Y el orden importa: el Core se genera **antes** de pintar la nav del plan. Al revés, el filtro
   de existencia omite las pestañas del Core la primera vez y la barra sale correcta, solo que más
   corta — un fallo mudo.
5b. **El menú lleva SIEMPRE todas las pestañas del perfil (T-047).** La que este plan no puede
   llenar todavía **no desaparece**: `gen_placeholders.py` la genera diciendo qué se vería y **con
   qué comando se consigue** (`nav.json#como_se_llena`), que es lo que `plan-docs-structure.md`
   pedía desde el principio.
   La regla anterior —omitir lo que no existe, para no dar un 404— evitaba ese fallo y creaba uno
   peor: **el menú cambiaba de un plan a otro**, así que era imposible saber si a este informe le
   falta la Arquitectura o si simplemente es de otro tipo. Un menú que cambia solo no es fiable.
   Solo se omite lo que no tiene página **ni receta**: ahí sí sería un 404.
   Y no se rellena con un ejemplo: publicar un diagrama de demostración es el fallo que ya costó
   dos `structure.html` enseñando un proyecto que no existía. Vacío y dicho es honesto.
   ⚠️ Orden: los placeholders se generan **antes** de pintar la nav. Al revés, el filtro los
   omitiría igual y el fallo sería mudo.
5d. **La barra se AGRUPA por la pregunta que responde cada pestaña, no por dónde vive el
   fichero.** El perfil `proyecto` declara 23 pestañas: planas son una pared que no se navega, y
   ya se desbordaban. Tres desplegables las bajan a **9 entradas de primer nivel**:

   | Grupo | La pregunta | Qué lleva |
   |---|---|---|
   | **Core ▾** | qué **ES** este proyecto — permanente | las 8 capas, incluida **Las piezas** |
   | **Mapas ▾** | cómo está **dibujado** — de este plan | Estructura · Arquitectura · Datos · Flujos · Esquemas · **Diseño** (2.15) |
   | **Calidad ▾** | ¿está **bien**? | Resultados · Pruebas · Personas · Auditoría |

   Sueltas quedan las cuatro más usadas (Resumen · Dashboard · Flujo de acción · Entregables) más
   Fuentes y Otto: meter el Dashboard en un desplegable añade un clic a la acción más frecuente
   del informe, y eso cuesta más de lo que ahorra.

   **La separación Core / Mapas no es estética: arregla una ambigüedad real.** Antes, `structure`
   y `schemas` colgaban del Core, así que la barra ofrecía a la vez «Cómo está construido»
   (`core-arquitectura`, permanente, en `.docs/core/`) y «Arquitectura» (`architecture.html`, de
   ese plan) sin nada que dijera en qué se diferencian. Ahora el grupo lo dice: **Core es lo que
   sobrevive al plan; Mapas es lo que se congela con él.**

   Un grupo cuyas hijas no existen **no se pinta** — un desplegable vacío es peor que una entrada
   de menos. Se declara en `nav.json#groups`, con el `_por_que` de cada uno escrito ahí.

5e. **`core-sistema.html` — «Las piezas»: el inventario del harness, y siempre.** Responde a la
   pregunta que ninguna otra pestaña contestaba: **qué tiene instalado este proyecto y cómo llega
   cada pieza a usarse.** Las 277 piezas (comandos, workflows, skills, agentes, rules, hooks,
   patrones, scripts, plugins) con su descripción, buscables y filtrables por tipo.

   La columna que la hace útil es **«cómo se usa»**, y sale de `descubrimiento`:

   | | Cuántas | Qué significa |
   |---|---:|---|
   | **La escribes tú** | 36 | comandos y workflows: `/nombre` |
   | **El modelo la encuentra** | 199 | skills, rules, agentes, patrones, scripts — dependen enteramente de su `description` |
   | **Salta sola** | 18 | hooks, en su evento |
   | **Instalada** | 24 | plugins |

   Esas 199 son el dato que cambia decisiones: una pieza con la descripción vaga **no se activa
   nunca y parece que no está**, que es la diferencia entre una skill muerta y una mal descrita
   (`self-improvement-loop.md` §5). Y `huerfana` —`fan_in 0` **y** solo descubrible por cita— es
   literalmente «nadie la encuentra».

   Se genera desde **`graph-dataset.full.json`**, no desde el enfocado: el enfocado colapsa
   comandos, plugins y workflows en un nodo «(+21 más)» para que el **grafo** se lea, y un
   inventario necesita justo lo contrario.

   ```bash
   python3 .claude/scripts/gen_harness_graph.py                     # el inventario
   python3 .claude/templates/report_kit/gen_core_capas.py <plan> --out .docs/core
   ```

   Es **permanente** (`.docs/core/`, regla 5a): el harness de un proyecto no muere con un plan.

5f. **La topnav se COMPRUEBA, no se supone: `render_nav.py --check <plan>`.** Verifica las tres
   cosas que fallan por separado —la pestaña existe · lleva la nav pintada · sus enlaces resuelven
   en disco— y sale 1 si algo falla. `build.py` lo corre al final y avisa sin romper.

   Existe porque el fallo lo encontró el Usuario navegando: los placeholders de subcarpeta
   (`feedback/personas.html`, `schemas/schemas.html`) salían **sin marcadores de nav**, así que al
   entrar en Personas **desaparecía el menú** y no había forma de volver. En los 8 planes: 16
   callejones sin salida. La causa era la interacción de dos piezas correctas por separado —
   `gen_placeholders.py` no emitía marcadores, y `render_nav --all` solo los auto-inserta a
   profundidad 1 (guarda que existe para no pintarle la topnav a fixtures vendorizados, PRU-9).

5c. **`fuentes.html` — los informes que hay DETRÁS de los items.** Si el plan tiene `sources/*.md`,
   `build.py` los descubre (título del primer `#`, primera frase como resumen, KB, épicas vía
   `meta.sources_map`, nº de items) y genera la pestaña; sin carpeta, la pestaña no aparece (5b).
   Los informes se guardan **literales, sin resumir**: un resumen del agente sobre su propio
   análisis no es verificable, y es justo donde viven las propuestas que **se cayeron** al
   refutarlas — el material que explica por qué una recomendación dice lo que dice.

5g. **Una página de `sources/` es una página MÁS del informe, no un anexo** (cosechado de
   `web-manager-coolify`, donde lo reportó el dueño navegando). Tres consecuencias, y las tres se
   aplican solas — no hay nada que recordar al escribir un informe:
   - **Lleva la topnav completa, con Fuentes marcado como activo**, vía `nav.json#owns_dir:
     "sources"`: `active_for()` resuelve por carpeta cuando el nombre del fichero no casa con
     ningún item. Un menú que no señala nada le dice al lector que se ha salido del informe.
   - **Hereda los tokens del bloque `SHARED`** (`md_to_html.py`) y **sin modo oscuro**: la topnav
     que inyecta `render_nav.py` es de color **fijo claro**
     (`.topnav{background:rgba(246,244,239,.93)}`), así que un `prefers-color-scheme:dark` en la
     página producía un fondo `#16161a` con una barra crema pegada encima — medido, no supuesto.
     Si el kit adopta modo oscuro algún día, los dos bloques vuelven **a la vez**.
   - **Salidas hacia Fuentes arriba Y abajo.** Al final de un informe de 60 KB, «vuelve arriba» no
     es una salida: es pedirle al lector que desande lo que acaba de leer.
   - **El HTML autor-escrito** (un `.html` en `sources/` sin `.md` hermano) **se lista igual**, con
     la etiqueta *página propia*, y recibe la nav — pero **su `<style>` no se toca**: suele ser una
     comparación visual donde la maquetación ES el contenido. `render_nav.py` sabe insertar la nav
     aunque el fichero no declare `<body>`.
   - **Su resumen en Fuentes sale del fichero ENTERO** (MO-40, sub-ola 2.15). Hasta el 21-10
     `build.py` leía solo los primeros 8 KB, y la topnav que se inyecta tras `<body>` ocupa 13-15 KB:
     al reconstruir, la entradilla quedaba fuera y la página salía sin resumen (6 de las 14 páginas
     propias de la revisión integral). Ahora se quita la nav, los comentarios, `<style>` y `<script>`
     antes de buscar, por este orden: `<p class="entradilla">` del cuerpo → `<meta name="description">`
     (la pone `md_to_html.py`) → `<!-- entradilla: … -->` (el apaño de antes, que sigue valiendo) →
     el primer `<p>` que no sea un `eyebrow`. Sin ninguno, vacío: no se inventa. Copiar la entradilla
     en un comentario del `<head>` ya no hace falta.

5h. **`auditoria.html` — la salud del PROPIO repo, aparte del plan** (cosechado de
   `web-manager-coolify`; el código ya estaba en `build.py` y no lo documentaba nadie). El resto
   del informe trata de *lo que hay que construir*; esta pestaña, de *lo que ya está construido y
   no está bien*: deuda, ficheros que afirman lo que ya no es cierto, duplicados. Se genera si el
   plan declara `meta.audit_prefixes` (qué prefijos de item son salud del repo) y hay alguno.
   **No decide, y eso es deliberado**: dos sitios donde decidir el mismo item acaban con dos
   respuestas distintas. Lo que sí hace es llevarte a decidir en un clic — los items van marcados
   con `meta.audit_tag` y la pestaña enlaza a `dashboard.html?tag=<esa etiqueta>`, que abre el
   dashboard **ya filtrado** y con toda su maquinaria; cada id enlaza además a `dashboard.html#ID`.
   Regla general: **una sola pantalla donde se decide; las demás llevan a ella filtrada.**

5i. **`sesiones.html` — el reparto en sesiones, con el comando de cada una** (2026-09-26, petición
   del Usuario). Si el plan se ejecuta en frentes paralelos —sesiones en worktrees que manda una
   sesión directora—, se declaran en **`<plan>/sesiones.json`** (nombre, ola, worktree, rama, franja
   de datos, misión, ficheros reclamados, lo que no toca, dependencias y prompt inicial).
   `gen_sesiones.py` pinta una tarjeta por sesión con su comando copiable, y con `--vivo` cruza cada
   una con `claude agents --json` para mostrar su estado real.
   **El comando se construye en UN solo sitio**: `gen_sesiones.py --comando <plan> <nombre>` imprime
   el mismo que enseña la página, y es el que ejecuta el lanzador. Escrito en dos sitios, el que se
   ve y el que corre acabarían siendo distintos. Sin `sesiones.json`, la pestaña lo dice y enseña el
   formato (regla 5b: el menú no cambia de un plan a otro).

6. **Evidencias autocontenidas**: en el HTML final las imágenes van embebidas base64 (`embed.py`,
   resize ~820px q~52). El informe debe abrir OFFLINE sin servidor.
6b. **`otto.html` abre con el «Resumen del proyecto»** (`meta.otto.resumen[]`): tarjetas de
   `titulo / que_es / por_que_importa / estado` (`ok|atencion|pendiente`) que explican de qué va el
   informe **en cristiano**, antes de la configuración y las sugerencias. Es la primera sección a
   propósito: quien abre un informe de 160 items necesita saber qué está mirando y cómo recorrerlo
   antes que ninguna otra cosa. Cada tarjeta lleva su «Por qué importa» — sin él es un titular, no
   una explicación.
6c. **`refs[]` — una referencia fuera de la carpeta del plan NO se enlaza, se copia.** `server.py`
   sirve solo el directorio del plan: un `href="../../../.claude/rules/qa-loop.md"` da **404 en modo
   servidor** y solo abre desde disco. El dashboard lo detecta (`location.protocol`) y en modo
   servidor pinta esas refs como botón que copia la ruta limpia (`.claude/rules/qa-loop.md`) para
   abrirla en el editor; las refs internas al plan y las `https://` siguen siendo enlaces. **No se
   arregla ampliando lo que el servidor sirve** — el repo guarda datos reales de cliente, y relajar
   la raíz servida para que un enlace no dé 404 es un intercambio pésimo.
7. **`otto.html` es parte del set** en los 4 perfiles (`minimo` incluido, 2.15): la sección del copiloto (sugerencias
   justificadas + permisos pendientes con "copiar aprobación"). Si Otto no ha corrido, la página
   muestra su estado vacío — no se omite.
8. **Multi-ronda**: al regenerar con `--round N+1`, `tasks_to_items.py` guarda snapshot de la ronda
   anterior en `item.history[]`. La evolución se ve en `results.html`.
9. **Pestaña Entregables — el principio de arriba, hecho mecanismo.** `gen_entregables.py` recoge
   por CONVENCIÓN DE CARPETAS todo lo que el plan produce y no tiene pestaña propia: `wireframes/`
   y `mockups/` embebidos en iframe, textos enlazados con su primer encabezado como título, y el
   resto listado con su tamaño. De `shots/` toma **solo las capturas huérfanas** —las que ningún
   item referencia en `evidence[]`—: las que ya son evidencia se ven en Resultados y duplicarlas
   sería ruido, pero las otras son justo el material que hoy se pierde.
   Recoge por **exclusión**, no por inclusión: `RESERVADAS` lista lo que ya tiene casa
   (`sources/`, `schemas/`, `feedback/`…) y todo lo demás entra solo. Añadir un tipo de material
   nuevo no exige tocar código.
   Se genera con `python3 gen_entregables.py <plan>` y después `render_nav.py --all <plan>`.
   **Con la pestaña Diseño** (perfiles `proyecto` y `diseño`, MO-76, sub-ola 2.15), el material
   VISUAL —`referencias/`, `arranque/12-kit-marca/`, `direcciones/`, `wireframes/`, `bocetos/`,
   `mockups/`, `prototipos/` y las capturas huérfanas de `shots/`— va a `diseno.html`
   (`gen_diseno.py`, cosechado de webs), ordenado por las fases de `rules/motores-de-diseno.md` Parte F, y
   Entregables lo dice arriba en vez de repetirlo. Sin la pestaña (perfil `incidencia`), se recoge
   aquí como siempre. Las capturas que ya son evidencia de un item no salen en ninguna de las dos:
   están en Resultados.
   ⚠️ `render_nav.py` **excluye** `wireframes/`, `mockups/`, `resources/`, `mensajes/` y `replays/`
   de su barrido: el HTML de esas carpetas se EMBEBE, y meterle la topnav le pinta la barra del
   informe dentro del iframe. Se descubrió al probarlo, no antes.

9b. **A cada página se le inyecta SOLO lo que esa página lee** (T-048). El `report.json` se
   incrustaba entero en las 7, y con un plan grande eso lo bloquea todo: en `ai4dev` (208 items,
   `report.json` de 610 KB) las siete páginas pesaban 582-662 KB y el hook de pre-commit las
   frenaba —con razón— así que el plan llevaba días sin poder actualizarse.

   El peso está muy concentrado, y quién lo usa también:

   | Campo | Pesa | Lo lee |
   |---|---:|---|
   | `desc` | 237 KB | **solo el dashboard** |
   | `tl_rec` | 50 KB | solo el dashboard |
   | `why` · `refs` · `goal` · `manual_test` | 120 KB | dos o tres páginas |

   `otto`, `fuentes` y `auditoria` no leen **ningún** campo de item. Resultado tras proyectar:
   dashboard 662→648 · index 597→406 · pruebas 605→265 · results 598→237 · otto 589→198 ·
   auditoria 587→148 · fuentes 582→143 KB. **Seis de las siete pasan el gate**; el dashboard
   sigue por encima y es el único que de verdad necesita todo.

   **La decisión de qué quitar se toma leyendo la plantilla, no de una tabla escrita a mano**
   (`_proyectar` en `build.py`): una tabla se queda vieja en cuanto alguien añade `it.refs` a una
   página, y entonces el campo desaparece en silencio — el peor fallo posible. Se busca el nombre
   del campo **como palabra** (`\b`): sin el límite, `desc` casaba dentro de `description` y no
   se ahorraba nada. Cualquier uso real casa (`it.desc`, `it["desc"]`, `{desc}`, `desc:`), y todo
   falso positivo va en la dirección segura: **conservar** el campo, nunca perderlo.

   Se descartó cargar `report.json` en runtime: `fetch` no funciona sobre `file://`, así que el
   informe dejaría de abrir desde disco — que es media razón de ser del formato
   (`html-output.md`).

10. **Verificación pre-DONE** (de `html-output.md` + `verification.md`): servir con
   `python3 -m http.server --bind 127.0.0.1`, screenshot multi-viewport, consola sin errores,
   `grep -L stylesheet *.html` (todas self-contained), y probar decisión→recarga→persiste.

## Flujo canónico

```bash
K=.claude/templates/report_kit ;  PLAN=.docs/plans/<fecha>-<slug>
# 1) tasks.md → report.json (idempotente; conserva decisiones por id)
python3 $K/tasks_to_items.py $PLAN --project <slug> --profile proyecto
# 2) (opcional) estructura real del código → graph-dataset.json   (skill /code-graph)
#    sin él, build.py usa el fixture sintético y structure.html lo avisa
# 3) (opcional) evidencias base64
python3 $K/embed.py $PLAN
# 3b) la pestaña Entregables: recoge wireframes, mockups, mensajes, adjuntos y capturas huérfanas
python3 $K/gen_entregables.py $PLAN
# 4) materializar el set (inyección + server.py + nav única)
python3 $K/build.py $PLAN --embed
# 5) modo backend (decisiones a disco con backup atómico) — el que hace que el agente LEA lo decidido
cd $PLAN && python3 server.py --port 8830        # escucha en 127.0.0.1 (default correcto)
```

### Cómo lo ve el Usuario: túnel SSH, nunca `0.0.0.0`

`server.py` escucha solo en `127.0.0.1` **a propósito** — exponerlo publicaría material de cliente
en internet sin auth. El acceso desde fuera es un túnel:

```bash
ssh -N -L 8830:127.0.0.1:8830 <usuario>@<servidor>   # en la máquina del Usuario
# → http://localhost:8830/dashboard.html   (comprobado antes con enlace.py, MO-26)
```

**Un puerto por informe**, y se cierra al terminar: estos servidores sobreviven a la sesión y se
acumulan (se encontraron 11 abiertos el 2026-08-21, y varios expuestos). Comprueba antes con
`ss -tlnp | grep 88`. Detalle y el caso real: `rules/security.md` §Servir HTML.

### Los dos ficheros del plan, y por qué no se llaman parecido

| Fichero | Qué es | Quién lo escribe |
|---|---|---|
| **`dashboard.md`** | Los items del informe: qué hay que hacer | el agente, desde el análisis |
| **`pending-tasks.md`** | Las peticiones del Usuario en esta sesión | el hook `capture-task.sh` |

Antes se llamaban `tasks.md` y `TASKS.md`, y no era solo confuso: **en macOS y Windows son el
mismo fichero** — sistemas sin distinción de mayúsculas —, así que colisionaban de verdad al
clonar. `tasks_to_items.py` sigue aceptando `tasks.md` como fallback: hay planes anteriores con
ese nombre y romperlos sería el peor resultado de un renombrado.

### Qué se escribe en `dashboard.md` para alimentar las vistas nuevas

Líneas indentadas de una sola línea bajo el checkbox del item (todas opcionales):

```markdown
- [ ] `API-1` [P0/S] Endpoint de alta de cliente
  goal: POST /api/clientes devuelve 201 y persiste
  blocks: UI-1, UI-2                     ← flechas y camino crítico del Gantt
  start: 2026-09-01                      ← fecha REAL (con ella el eje pasa a fechas)
  due:   2026-09-05
  prereq: backend levantado en :8000     ← cabecera del guion de pruebas
  url:   /api/clientes
  test: Envía un POST con NIF válido → responde 201 con el id nuevo
  case: "quiero cita para mañana" → propone 3 huecos y pide confirmación
  nocturno: si — el gate es pytest apps/api; reversible y falla ruidoso   ← ¿corre sin supervisión?
  rec: aprobar — es una avería, no una propuesta: bloquea todos los tests  ← sugerencia del REVISOR
```

**`rec:`** (`aprobar|duda|no-aprobar` + razón) es **la sugerencia de quien analizó, no la decisión
del Usuario**. Vive separada de `decision` a propósito, y esa separación es el campo entero:

- Si la recomendación se escribiera en `decision`, **no quedaría rastro de quién dijo qué** y
  "aprobar lo que recomienda el revisor" dejaría de ser una decisión del Usuario para convertirse
  en un valor por defecto que nadie tomó.
- Va en **`CARRY`, no en `KEEP`**: la escribe el agente en `tasks.md` y una regeneración la
  actualiza. Lo que el Usuario marca (`decision`, `note`) sigue siendo intocable.
- El dashboard la expone como **una fila de chips de filtro, y nada más**. Para decidir en bloque
  se encadena lo que ya existe: filtrar por **`👍 Aprobar`** → **`☑ Seleccionar visibles`** →
  **`✓ Aprobar`** de la barra masiva. Hubo un botón dedicado de "aprobar todo lo que aprueba el
  revisor" y **se retiró**: era un camino paralelo con reglas propias (solo visibles, solo sin
  decidir) para algo que la maquinaria existente ya hacía, y además el filtro **te deja ver qué
  vas a aprobar antes de aprobarlo**.
- **La razón no es opcional en la práctica**: una recomendación sin porqué solo se puede obedecer,
  no contrastar. Y un revisor que recomienda aprobar el 100% no está revisando.
- Ojo al separador: la razón se separa con `—`, `–`, `--` o `:` — **nunca con un guion simple**,
  porque `no-aprobar` lo lleva dentro.

**`si_si:` y `si_no:`** son las **consecuencias de decidir**, y sin ellas un item con recomendación
solo se puede obedecer, no contrastar. Nacen de una petición directa del Usuario (2026-08-26), y el
motivo es el mismo por el que `rec` lleva razón obligatoria: *"es complicado decidir; pon qué pasaría
si se aprueba, a qué afectaría, y qué pasaría si no"*.

- Se pintan **antes** que las referencias en el detalle del item: las dos caras se leen primero, y
  las fuentes están para quien quiera bajar más.
- **Son obligatorias de facto en los items `rec: duda`**, que son justamente aquellos en los que el
  revisor no tiene una respuesta y el criterio es del Usuario. En los de `aprobar` ayudan; en los de
  `duda` son lo que hace posible la decisión.
- El `si_no` **no es una amenaza**: la mitad de las veces la respuesta honesta es *"no pasa nada
  grave, se sigue como hoy"*, y decirlo así es lo que hace creíble el resto.

**`nocturno:`** (`si|no|revisar` + razón) marca qué items pueden ejecutarse **sin nadie mirando**.
Los criterios —y lo que nunca es elegible— están en **`rules/goal-vs-loop.md` §Modo noche**; aquí solo el
cableado. Tres detalles que no son casuales:

- **Va en `KEEP`, no en `CARRY`**: lo que se escribe en `tasks.md` es la *propuesta*; quien decide
  es el Usuario en el dashboard (chips de filtro + acciones masivas), y su marca sobrevive a las
  regeneraciones.
- **Sin declarar ≠ no apto.** El filtro los distingue a propósito: tratar lo no declarado como apto
  es exactamente cómo se cuela de noche algo que nadie evaluó.
- **La razón es la mitad del campo.** Una marca sin razón no se puede auditar al mes siguiente; por
  eso la acción masiva la pide una vez para toda la selección en vez de item por item, que es la
  forma segura de que nadie la escriba.

**`blocks:` es una línea**, y esa es toda la intención: mientras declarar una dependencia costara
editar JSON a mano, nadie lo hacía y el Gantt salía plano (`blocks[]` estaba vacío en los 122 items
del primer plan que lo estrenó). Declara solo las que importen de verdad; el resto lo deriva el
esfuerzo.

### Quién es dueño de cada campo al regenerar — los TRES grupos

La frontera es de **propiedad**, no de comodidad: manda quien lo escribe.

| Grupo | Campos | Al regenerar |
|---|---|---|
| **REFRESH** — lo escribe el AGENTE en `dashboard.md` | `desc` `goal` `rec` `auditor` `blocks` `start` `due` `manual_test` | **Siempre se relee del fichero.** Si el fichero ya no lo declara, **se vacía** |
| **KEEP** — lo escribe el USUARIO en el tablero | `decision` `note` `nocturno` `tested` `evidence` `severity` `effort` `status` | **Nunca se pisa** (excepción de `status` abajo) |
| **CARRY** — generado y editable, pero el fichero no sabe expresarlo | `verdict` `why` `howto` `confidence` `history` `refs` `tags` `agent` `tl_rec` | Se hereda del `report.json` anterior |

**Corregir el informe se hace editando `dashboard.md`, jamás borrando `report.json`** — el borrado
se lleva por delante las decisiones del Usuario, y es exactamente el apaño que este reparto existe
para hacer innecesario. El grupo REFRESH nació de tres mordiscos del mismo bug (RKT-1): con la regla
anterior (`CARRY_IF_EMPTY`) solo ganaba **lo declarado**, así que **borrar** una línea `rec:` o
`auditor:` equivocada no la quitaba del informe: el valor viejo se heredaba para siempre.

**`status` lo manda el fichero, salvo que el Usuario lo cambiara a mano** (MO-D5, decisión del
Usuario del 18-10, por elvion #20: 16 casillas `[x]` que el informe seguía enseñando en backlog).
`tasks_to_items.py` guarda en `meta.tasks_status` lo que el fichero decía de cada item; en la
siguiente regeneración, si el status guardado coincide con esa foto (nadie lo tocó en el dashboard),
gana el fichero —`[>]` y `[ ]` incluidos—; si difiere (lo movió el Usuario, p. ej. a `review`, que el
fichero no sabe expresar), se conserva, salvo ante una casilla `[x]` o `[!]` **nueva** en el fichero,
que es una afirmación explícita posterior. Un `report.json` sin `meta.tasks_status` (anterior a la
2.14) sigue la regla de antes —solo `[x]` y `[!]` pisan— hasta la primera regeneración. Límite: en
modo estático lo que el Usuario mueve vive en su localStorage y se aplica encima al abrir; esto
gobierna lo que se guarda en `report.json` (modo `server.py`).

Medido el 2026-08-22 sobre el plan `2026-08-21-mapa-y-orden` (85 items): **0 diferencias** entre el
código anterior y el nuevo, y **0 campos vaciados** — el cambio solo actúa donde el fichero dejó de
declarar algo.

## Dónde vive

`rules/plan-docs-structure.md` manda: el set se genera en `.docs/plans/<YYYY-MM-DD-slug>/`.
`report.json` ES la fuente de decisiones del plan (el `items.json` del viejo `/plan-dashboard`).
Las páginas opcionales (Alcance/Integraciones/Paralelización/Diff/Configs) van fuera de la topnav
por defecto, enlazadas desde `index.html` (`nav.json#optional_pages`).

## Anti-patterns

- ❌ Inventar un schema de item nuevo o una clave de localStorage ad-hoc.
- ❌ Añadir un campo KEEP y tocar `keepOf` en una sola página del set (la otra lo borrará al guardar).
- ❌ Presentar el Gantt como un calendario comprometido, o quitarle el aviso de "orientativo".
- ❌ Desplegar el mapa mental entero por defecto — con >100 items deja de comunicar.
- ❌ Escribir el manual de pruebas a mano al cerrar la wave: se deriva de los criterios de
  aceptación (`test:`/`case:` en tasks.md), o sale `derivado` y genérico y ya te está avisando.
- ❌ Recortar etiquetas SVG por número de caracteres cuando el ancho es fijo → usa `fitText`.
- ❌ **Tocar un token/estilo del bloque `/* SHARED:BEGIN/END */` en UNA plantilla y no en las 5.**
  El bloque debe ser IDÉNTICO byte a byte (verificación: `python3 .claude/scripts/check_shared_block.py`).
  CSS divergente entre páginas fue la causa raíz de los findings "×N" del QA iter-1 (G2 de Pol).
- ❌ Reabrir/editar el informe de un plan con `meta.closed_at` seteado — está congelado (banner
  solo-lectura); si el plan revive, se limpia `closed_at` conscientemente y se anota por qué.
- ❌ Editar la topnav a mano en un HTML del set.
- ❌ Publicar una página del informe **sin los marcadores `NAV:BEGIN/END`** → se entra y no se
  puede salir. Si la genera un script, el script los emite; `render_nav.py --check` lo caza.
- ❌ Dejar la barra plana con 20 pestañas → es una pared, no un menú (regla 5d).
- ❌ Meter el **Dashboard** (o el Resumen) dentro de un desplegable → un clic más en lo que más se
  usa cuesta más de lo que ahorra agrupar.
- ❌ Agrupar por **dónde vive el fichero** en vez de por la pregunta que responde → vuelve a
  juntar `core-arquitectura` (permanente) con `architecture` (de este plan) sin decir en qué se
  diferencian, que era el problema.
- ❌ Generar «Las piezas» desde el `graph-dataset.json` enfocado → sale «(+21 más)» donde debería
  haber 21 comandos con su nombre.
- ❌ Dejar que una pestaña desaparezca del menú porque este plan no tiene sus datos → el menú deja
  de ser el mismo entre informes y nadie puede fiarse de él. Se genera con su «cómo conseguirlo».
- ❌ Añadir una pestaña al perfil y no darle receta en `nav.json#como_se_llena` → o da 404, o
  genera una página que dice «sin datos» y no dice qué hacer, que es un callejón sin salida.
- ❌ Generar las páginas del Core **dentro del plan** → el «qué es este proyecto» se congela y muere
  cuando ese plan se cierra (PV-3). Van a `.docs/core/`.
- ❌ Regenerar el Core desde un plan que no es el activo → el panel pasa a describir el pasado.
- ❌ Enlazar entre plan y Core con una ruta que solo vale en un modo → pruébala **servida y en
  disco**; el 404 de la vuelta al plan lo encontró un navegador, no una lectura del código.
- ❌ Ampliar la raíz que sirve `server.py` para que un enlace deje de dar 404 → `.docs/resources/`
  tiene código de cliente. Se monta la carpeta concreta, con el escape bloqueado.
- ❌ Publicar `structure.html` con el FIXTURE sintético: enseña un proyecto Django inventado en el
  informe de un repo que no es ese, y el banner de "datos de demostración" no lo arregla.
  **Esto ya no es advisory**: `build.py` mira `meta.source` del `graph-dataset.json` —no si el
  fichero está— y si dice FIXTURE no genera la página y borra la que hubiera. El guard anterior
  solo comprobaba la existencia, y `graph_reduce.py --fixture <plan>/graph-dataset.json` se la
  colaba entera. La demo sigue disponible pidiéndola: `--pages structure`.
- ❌ Un "sin resultados" que no dice QUÉ filtros están puestos ni ofrece quitarlos: con filtros
  persistentes, el usuario vuelve días después, ve la lista vacía y concluye que está roto.
- ❌ Dejar en la nav (o en los enlaces del index) una página que el plan no ha generado → 404 y
  sensación de informe roto. El filtro por existencia de `render_nav.py` está para eso.
- ❌ Guardar los informes de investigación en `sources/` y no enlazarlos desde ninguna página:
  el análisis existe pero nadie lo encuentra, y el dashboard queda sin su porqué largo.
- ❌ Informe con `<img src="ruta">` sin embeber → no abre offline (usa `embed.py`).
- ❌ Añadir un campo nuevo al item y **olvidar meterlo en un grupo** (`KEEP`/`CARRY`/`REFRESH`) de
  `tasks_to_items.py` → la siguiente regeneración lo borra en silencio. Le pasó a `refs[]`: se
  perdía en el primer rebuild.
- ❌ Meter en `CARRY` algo que escribe el agente en `dashboard.md` → se hereda para siempre y
  **corregir el fichero deja de servir**: reescribes 26 recomendaciones, regeneras, y el informe
  sigue enseñando las viejas. Va en `REFRESH`.
- ❌ Arreglar un informe desfasado **borrando `report.json`** → te llevas por delante `decision`,
  `note`, `nocturno` y `tested`. Si hace falta borrarlo para que se actualice algo, el bug está en
  el reparto de grupos, no en el JSON.
- ❌ Escribir a mano la tabla de «qué campo va en qué página» → se queda vieja y el campo
  desaparece en silencio. Se deduce de la plantilla (regla 9b).
- ❌ Cargar `report.json` con `fetch` para adelgazar las páginas → rompe el `file://` y con él
  la regla de autocontenido.
- ❌ Dejar una página de `sources/` sin topnav, con estilo propio o con modo oscuro → el lector
  entra, el menú no señala nada y no sabe volver; y en oscuro sale la barra crema sobre negro (5g).
- ❌ Declarar `meta.audit_prefixes` y además dejar decidir en `auditoria.html` → dos sitios donde
  decidir el mismo item acaban con dos respuestas distintas (5h).
- ❌ Usar `wip`/`pend` como status.
- ❌ Regenerar el set pisando decisiones (el merge idempotente por id existe para eso).
- ❌ Un "informe total" en markdown de 400 líneas — para eso existe este kit.
- ❌ Recuperar `speckit_dashboard/` o los dashboards «lite» de `_archive/2026-10-19/templates/` para un informe nuevo: se retiraron porque duplicaban este kit (LI-12).

---

_Rule version: 1.1 · 2026-08-24 — +5g (`sources/` es una página más: `owns_dir`, tokens SHARED y
sin modo oscuro) y +5h (`auditoria.html`), ambas cosechadas de `web-manager-coolify`; el código de
5h llevaba meses en `build.py` sin documentar. Antes: v1.0 · TPL-1 W3._
