# `.claude/patterns/stack/REGLAS.md` — el detalle de cada mitad, sus medidas y lo que se cayó

> **Qué es este fichero.** Hasta la sub-ola 2.15 de la revisión integral (21-10-2026, MO-78) era el
> cuerpo de `README.md`, que pesaba 42 KB para ser un índice. El índice (qué documento fija qué, con
> sus comprobadores) sigue en `README.md`; aquí está todo lo demás, **palabra por palabra**: los
> cuatro defaults con su porqué, los fixtures de cada mitad, la medición de la mitad de agentes con
> sus denominadores, la lista negra, Mongo, las reglas que se cayeron y el vocabulario de agentes.
> Los títulos son los mismos que tenía `README.md`, así que una cita «stack/README.md §X» antigua se
> encuentra aquí por su §X.

## Los cuatro defaults que NO son reglas (EVO-4)

El set presuponía cuatro cosas sin justificarlas y las trataba como obligatorias. Ninguna estaba
respaldada por una medida, y las cuatro cuestan cientos de ficheros en un backend que ya existe.
**Pasan a ser el default de un proyecto NUEVO: se aplican al arrancar de cero y NO se marcan como
incumplimiento en un proyecto existente.**

| Presuposición | Qué era | Qué es ahora | Por qué (medido sobre un backend Django real de 740 ficheros) |
|---|---|---|---|
| Carpeta `apps/` | implícita en los fixtures | **default de proyecto nuevo.** Apps hermanas planas del paquete de configuración son igual de válidas | Mover 46 apps son 46 renombrados + los imports de 740 ficheros, para resolver **cero** problemas demostrados |
| `settings/` partido en `base/dev/prod` | implícito en los fixtures | **default de proyecto nuevo.** Un `settings.py` único es igual de válido | Un settings de 960 líneas ya resuelve por ~40 variables de entorno lo que el split resuelve por ficheros, con una sola rama por entorno |
| El nombre `services.py` | parte del enunciado de la regla | **default de proyecto nuevo.** La regla es la SUSTANCIA: la capa no importa HTTP ni recibe `request`. La ubicación se declara con `# pattern-layer: services` | `utils.py` **ya es** la capa de servicios en ese repo (28-30 ficheros, 11.385 líneas, una función con 5 tipos de invocador). Renombrar 30 ficheros no arregla ninguno de los 3 sitios donde la lógica sí está atrapada |
| Backend = DRF | 3 reglas de settings lo exigían **siempre** | **default de proyecto nuevo.** Las 3 reglas se comprueban solo si el proyecto usa DRF | Ese backend tiene **385 clases de formulario y 1 solo `ModelViewSet`**. Antes del gate, un backend server-rendered recibía 3 hallazgos ACTIVOS pidiendo configurar un framework que no usa |

**Cómo se comprueba cada una** (porque una degradación sin comprobación es una degradación
perdida):

- **Layout y settings** → el fixture `_fixtures/conforme-plano/` es apps planas + `settings.py`
  único + server-rendered, y **debe puntuar 0 hallazgos** en el `--self-test`. Ese fixture *es* el
  test: si alguien vuelve a colar una regla que presupone `apps/` o el split, deja de estar en 0.
- **Nombre de la capa de servicio** → `# pattern-layer: services` en la cabecera del fichero.
  `_fixtures/infractor-plano/expedientes/utils.py` lo lleva y `be-svc-sin-drf` dispara allí dos
  veces: el nombre cambió, la regla no.
- **DRF** → detección por import real o app declarada (`DRF_PRESENT_RE`), no por la palabra suelta
  en un comentario. Mismo gate que ya llevaban Celery y `CACHES`: se comprueba lo que existe.

Fuente de las medidas: `.docs/core/ai4dev/K-estilo-evopreven-mejorado.md`.

## Mitad BACKEND — 55 reglas · `pattern_check_backend.py`

(La tabla de documentos de esta mitad está en `README.md` §Índice.)

**Los dos arquetipos.** `backend-serializers.md` y la mitad de API de `backend-vistas.md` aplican
**solo a backends DRF**; `backend-formularios-django.md` aplica **solo a server-rendered**. Pueden
convivir en un repo; lo que no puede es aplicarse el documento equivocado. El checker lo resuelve
solo: las reglas de cada arquetipo se activan por lo que encuentra en el código, no por decreto.

**Y un tercero que no es de casa.** `backend-controllers.md` describe el **framework CRUD propio**
de un backend heredado (`evo-preven`): `class X(XSettings, ModelController)`. No prescribe nada —
existe para que quien toque ese repo escriba como ese repo, que es el eje de Rita. Sus 3 reglas
nacen en `sombra`, **no tienen comprobador escrito** y están medidas en **un solo repo** (GAP-1).
En un proyecto nuevo, construir esto sería una decisión de arquitectura con Gate C + ADR.

```bash
python3 .claude/patterns/stack/pattern_check_backend.py              # ficheros cambiados
python3 .claude/patterns/stack/pattern_check_backend.py --all        # inventario del repo
python3 .claude/patterns/stack/pattern_check_backend.py --list       # las 55 reglas y su estado
python3 .claude/patterns/stack/pattern_check_backend.py --json       # para otro agente
python3 .claude/patterns/stack/pattern_check_backend.py --self-test  # FPR + sensibilidad
```

| Fichero | Qué es |
|---|---|
| `pattern_check_backend.py` | Las 55 reglas, ejecutables (AST + grep, stdlib pura). Misma política que `hooks/pattern-check.sh`: `activo` bloquea (exit 1), `debil` avisa, `sombra` solo mide |
| `_fixtures/conforme/` | Arquetipo **DRF**: `apps/`, settings partido, ViewSets (11 ficheros). **0 hallazgos** |
| `_fixtures/conforme-plano/` | Arquetipo **server-rendered**: apps planas, `settings.py` único, formularios, capa de servicio en `utils.py` (6 ficheros). **0 hallazgos** — es la prueba de EVO-4 |
| `_fixtures/conforme-casa/` | Arquetipo **con bases de casa**: modelo base + `Meta` compartido + vista base con el filtrado por dueño + señales con `on_commit` + comando que valida + tests + `/healthz` (18 ficheros). **0 hallazgos** |
| `_fixtures/infractor*/` | Una infracción deliberada por regla, repartidas por arquetipo. **55/55 disparan**: es el control de sensibilidad |
| `_catalog-entries-backend.yaml` | Propuesta de filas para `catalog.yaml` (el TL las integra; este set no toca el catálogo) |

`_fixtures/` está excluido del barrido normal (`SKIP_DIRS`): si no, cada run del repo reportaría
las infracciones inventadas.

**Que haya TRES fixtures conformes no es duplicación: es la afirmación.** Un solo fixture conforme
solo puede demostrar que *ese* layout pasa; con tres que puntúan 0 se demuestra que **ninguno es
obligatorio** — ni la carpeta `apps/`, ni el split de settings, ni DRF, ni las bases de casa. Al
añadir una regla, pásala por los tres: si solo pasa por uno, la regla está presuponiendo un layout
y hay que gatearla (§"los cuatro defaults").

**El tercer par (`*-casa`) añade una afirmación nueva:** las reglas "de casa"
—`be-model-base-de-casa`, `be-model-meta-base-de-casa`, `be-view-base-de-casa`,
`be-form-base-de-casa`, `be-owner-create-sin-dueno`— están **gateadas por descubrimiento**: solo
disparan si el proyecto YA tiene esa base, y la base se busca leyendo el repo, no declarándola en
un YAML. Que `conforme/` y `conforme-plano/` (que no las tienen) sigan en 0 es la prueba de que un
proyecto nuevo no recibe reproches por no seguir un patrón que aún no ha creado.

**Verificación permanente** — antes de tocar una regla, y después:

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --self-test
# ── FPR [conforme]:        0 hallazgo(s) sobre 11 ficheros CONFORMES
# ── FPR [conforme-casa]:   0 hallazgo(s) sobre 18 ficheros CONFORMES
# ── FPR [conforme-plano]:  0 hallazgo(s) sobre  6 ficheros CONFORMES
# ── Sensibilidad TOTAL: 55/55 reglas disparan sobre los fixtures INFRACTORES
```

⚠️ **`--all` sobre ESTE repo** (que no es un proyecto Django) devuelve ~12 hallazgos, casi todos en
`resources/` y `.docs/` — repos de terceros vendorizados. Los dos propios son `débil` y están en
`assets/` de dos skills: plantillas de código Django ilustrativas, que efectivamente "tocan el ORM
y no dicen cómo se ejecutan" porque no se ejecutan. Es un falso positivo aceptado y no se
silencia con una lista de exclusión: un directorio `assets/` en un proyecto real sí puede tener
código nuestro, y saltárselo en silencio sería peor que el ruido.

Si tocas una regla y el FPR deja de ser 0, la regla está mal — no el fixture. Es la regla 3 del
`README.md` de arriba: FPR bajo demostrado **antes** de activar nada.

## Mitad FRONTEND — 38 reglas · `pattern_check_frontend.py`

**Empieza por [`frontend-stack.md`](frontend-stack.md):** dice qué librería resuelve cada papel y en
qué versión mayor. Los demás documentos dan ese stack por supuesto, así que leerlos sin él lleva a
copiar ejemplos que no compilan en el proyecto de destino.

⚠️ **Los VALORES de diseño no están aquí y no van a estar** (decisión del Usuario, EST-2). El
template pone el **procedimiento** —cómo se define un sistema de diseño, dónde vive, cómo lo
consumen los componentes, qué se hace cuando falta un valor— en
[`frontend-design-system.md`](frontend-design-system.md); la paleta, la escala y la tipografía las
declara **cada proyecto** en su `.docs/core/design-system.md`, con el peso de una `constitution.md`.
Si algún día lees aquí una paleta concreta, es un error: bórrala.

(La tabla de documentos de esta mitad está en `README.md` §Índice.)

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py                      # ficheros cambiados
python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src   # inventario
python3 .claude/patterns/stack/pattern_check_frontend.py --only componentes
python3 .claude/patterns/stack/pattern_check_frontend.py --list               # las 38 reglas
python3 .claude/patterns/stack/pattern_check_frontend.py --self-test          # FPR + sensibilidad
```

**37 reglas juzgan un fichero; 1 juzga el conjunto** (`fe-origen-de-tokens`: ¿hay un origen de
tokens y está declarado?). Las de proyecto **solo corren con `--all`**, porque desde un diff de dos
ficheros no se puede afirmar que al proyecto le falta algo — y hacerlo daría un aviso falso en cada
commit hasta que alguien desactivara la regla.

⚠️ **`--all` se apunta al `src` del proyecto, no a la raíz.** `--all .` en ESTE repo barre también
`resources/` (repos de terceros vendorizados) y devuelve ~104 hallazgos que no son nuestros. No hay
lista de exclusión a propósito: un directorio llamado `resources/` en un proyecto real sí puede
tener código nuestro, y saltárselo en silencio sería peor que el ruido.

**Verificación permanente**, igual que en la mitad de backend — antes de tocar una regla, y después:

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --self-test
# ── FPR: 0 hallazgo(s) sobre 11 ficheros CONFORMES
# ── Sensibilidad: 38/38 reglas disparan sobre los fixtures INFRACTORES
```

Los fixtures del frontend van **embebidos en el propio script** (`FIXTURES_CONFORME` /
`FIXTURES_INFRACTOR`) y se materializan en un temporal, no en `_fixtures/`: esa carpeta es del
comprobador de backend, y así ningún barrido del repo ve código React inventado. El criterio es el
mismo — si tocas una regla y el FPR deja de ser 0, la regla está mal, no el fixture.

Además del `.tsx`/`.ts`, este comprobador lee **`package.json`** (capa `stack`) y las hojas de estilo
con ámbito propio — `*.module.css`, `*.vue`, `*.svelte` (regla `fe-apply-con-reference`).

> Los dos checkers son independientes a propósito (lenguajes y parsers distintos) pero comparten
> vocabulario de estado (`activo`/`debil`/`sombra`) y el mecanismo de excepción `pattern-exempt`.
> **Divergencia pendiente de unificar por el TL:** el YAML de frontend usa `origen: casa` +
> `referencia:` y el de backend usa `dominancia: declarado` + `source:` para decir lo mismo.

### El único punto donde las dos mitades deben decir lo mismo: el error 400

```
400  {"errors": {"campo": ["mensaje"], "non_field_errors": ["mensaje de formulario"]}}
```

Lo consume el frontend (`api-y-errores.md` → `ApiError.fields`, `formularios.md` → `setError`) y lo
produce el backend (`backend-vistas.md` §El contrato del error 400). **No sale gratis:** DRF por
defecto usa dos formas distintas —campo a nivel raíz en validación, `{"detail": ...}` en
auth/404/throttling—, así que un cliente que leyera solo `body.errors` encontraría `undefined` y no
pintaría ningún error. Ese fue el fallo original que destapó este contrato. Lo sostienen **dos
reglas en pareja**, las dos `activo`:

| Regla | Cierra |
|---|---|
| `be-api-exception-handler` | que exista el `EXCEPTION_HANDLER` que pone el sobre |
| `be-view-error-sin-excepcion` | que ninguna vista lo esquive con `return Response(..., status=4xx)` — la doc de DRF avisa de que el handler **solo** corre para excepciones LANZADAS |

El frontend añade además una capa defensiva (`normalizeErrors`) que tolera las tres formas, por los
endpoints de terceros y legacy que quedan fuera del alcance del handler. Es complementaria, no
sustituta: evita la pantalla en blanco, no que la API tenga dos contratos.

## Mitad AGENTES — 17 documentos, 13 reglas · `pattern_check_agente.py` (y por qué NINGUNA bloquea)

(La tabla de documentos de esta mitad está en `README.md` §Índice.)

```bash
python3 .claude/patterns/stack/pattern_check_agente.py <repo>            # legible
python3 .claude/patterns/stack/pattern_check_agente.py <repo> --json     # para otro agente
python3 .claude/patterns/stack/pattern_check_agente.py --self-test       # 0 falsos positivos
```

### La medición, con sus denominadores (2026-08-22)

Los dos únicos repos con agentes de esta casa. `find <repo> -name '*.py' | wc -l` da 641 y 290; el
comprobador recorre 520 y 240 porque salta `migrations/`, `__pycache__/`, `.venv/` y `node_modules/`.
De esos, están **en el camino del agente** —donde se construye el grafo, se definen tools o se
ejecutan nodos— 34 ficheros en elvion y 10 en musa.

| Regla | elvion | musa | Conformidad medida | Qué dice el número |
|---|---|---|---|---|
| `ag-historial-sin-leer` | 1 (repo) | 1 (repo) | **0/2 repos** | Los dos guardan estado con checkpointer y **ninguno lo lee** (agosto; 2026-10-21: 1 fichero de test o script cada uno) |
| `ag-sin-vuelta-sin-puerta` | **0** (no aplica) | 1 (repo) | **0/1 repos aplicables** | 0 puertas en 931 ficheros (medida del 2026-08-22; re-medido el 2026-10-21 en código propio: 0 en elvion y musa, 35 en autoparte-demo). musa tiene 6 tools que escriben en sistemas de terceros; elvion **0**, y ahí la regla se calla sola |
| `ag-sin-stream` | 1 (repo) | 1 (repo) | **0/2 repos** | 12 invocaciones de grafo entre los dos, cero observadas (agosto; 2026-10-21: `stream_mode` y `astream_events` en 0 ficheros propios) |
| `ag-config-pobre` | 11 | 1 | **0/12 invocaciones** | Ninguna invocación lleva `tags`/`metadata`/`run_name` |
| `ag-except-mudo` | 47 en 13 ficheros | 25 en 4 | sin denominador estable | Dispara en los dos, y en un tercio de los ficheros del camino |
| `ag-log-secreto` | 4 en 4 ficheros | 8 en 4 | sin denominador estable | Dispara en los dos — y **faltaba en `catalog.yaml`** hasta hoy |
| `ag-print` | **67 en 4 ficheros** | **1 en 1** | no hay patrón | Los dos repos se contradicen en dos órdenes de magnitud |
| `ag-tool-sin-schema` | 1 de 25 tools | 1 de 27 | 50/52 (**96%**) | Alta, pero apoyada en **2** incumplimientos |
| `ag-tool-lanza` | 2 | 0 | 50/52 (**96%**) | Los dos casos están en el mismo repo |
| `ag-tool-sin-doc` | **0** de 25 | **0** de 27 | 52/52 (**100%**) | **Cero evidencia**: nunca ha disparado, luego nunca ha podido fallar |

### El límite, sin adornos (GAP-1)

**n = 2, y los dos son nuestros.** Mismo equipo, mismo trimestre, mismo stack (LangGraph), los dos
chatbots. `patterns/README.md` §1 exige *dominancia medida* antes de fijar nada, y dos repos del
mismo autor no miden dominancia: miden **nuestra manera de escribir**. Tres cosas concretas que la
tabla deja ver y que conviene decir en voz alta:

1. **Cuatro reglas describen lo que creemos correcto, no lo que el código hace.** `ag-config-pobre`,
   `ag-sin-stream` y `ag-historial-sin-leer` dan **0% de conformidad**: por el criterio del canon
   (<60% = no hay patrón) no son patrones de casa, son **reglas declaradas** con fuente externa
   (`agente-observabilidad.md`). Legítimas — pero en el cajón de "Declarado, no medido" de más
   abajo, no en el de "medido".
2. **Un 100% puede ser peor dato que un 60%.** `ag-tool-sin-doc` no ha disparado ni una vez en 52
   tools. Eso no prueba que la regla acierte: prueba que **no ha tenido ocasión de fallar**, igual
   que un fixture de calibración en techo no mide al auditor (`rules/qa-loop.md` §4b). Promoverla
   por su 100% sería promover una regla nunca probada.
3. **Cuando los dos repos discrepan, no hay patrón que extraer.** `ag-print`: 67 hallazgos
   concentrados en 4 ficheros de elvion frente a 1 en musa. Con n=2 no se puede distinguir "regla
   del equipo" de "cómo escribió aquel día quien tocó esos 4 ficheros".

**Por eso las 10 están en `sombra` y ninguna bloquea nada.** No es prudencia decorativa: un gate que
marca 172 sitios en dos repos se aprende a ignorar, y con él se ignoran los avisos que sí importan
(`rules/refactor-progresivo.md` §0).

### Lo que pasó el 2026-08-26: entraron dos repos ajenos, y NO desbloquean el gate

Se vendorizaron dos repos de LangGraph de terceros en `.docs/resources/langgraph/` (detalle y
patrones citables: su `README.md`). Es la primera vez que la fila 1 de la tabla de abajo tiene
candidatos, así que se midieron el mismo día:

```bash
python3 .claude/patterns/stack/pattern_check_agente.py .docs/resources/langgraph/LangGraph-Udemy-Course
python3 .claude/patterns/stack/pattern_check_agente.py .docs/resources/langgraph/agents
```

| Regla | Curso Udemy (langgraph 1.0.1) | `agents/` (0.4.7) | Nuestros dos |
|---|---|---|---|
| `ag-historial-sin-leer` | falla | falla | falla |
| `ag-sin-stream` | falla | falla | falla |
| `ag-config-pobre` | 3 hallazgos | 2 hallazgos | 0/12 invocaciones |
| `ag-print` | 4 | 0 | 68 |
| `ag-except-mudo` | ~1 | ~81 en 183 ficheros | 72 en 17 |
| `ag-tool-*` | sin hallazgos | **no medible** — 6 tools con `Tool(name=…)`, que el AST no veía |

**Cuatro conclusiones, y ninguna es la que esperábamos:**

1. **No sirven como tercer repo para promover nada.** Son código **de curso**, no de producción, y
   además fallan las mismas reglas de observabilidad que nosotros. La fila 1 sigue en ❌.
2. **4 repos de 4 tienen checkpointer y ninguno lee el historial.** Pero la explicación no es que la
   regla esté mal: los dos ajenos **declaran `langsmith`** y se apoyan en el auto-tracing por
   variables de entorno, que no exige escribir código. Nosotros no tenemos ni lo uno ni lo otro. La
   regla se mantiene, y `agente-observabilidad.md` §4 recoge la vía que nos faltaba.
3. **`ag-tool-sin-doc` seguía sin poder fallar, y ahora sabemos por qué.** Ese repo define sus tools
   con `Tool(name=, func=)`, sin decorador, y el comprobador **no las veía**. Un 0 no era "cumple":
   era "no lo estoy mirando". Arreglado el mismo día — ahora imprime `⚠ CEGUERA DECLARADA` con las
   tools que no puede juzgar. Es el fallo de TPL-21 otra vez: **un mecanismo que no falla haciendo
   ruido**.
4. **Donde sí hay señal es en `ag-print` y `ag-except-mudo`**, y no nos favorece: el curso tiene 4
   `print` y nosotros 68. Ahí la comparación externa dice que nuestro código es peor, no distinto.

### Qué tiene que pasar para que alguna suba de escalón

Criterio escrito **antes** de medir el tercer repo, para no elegirlo después según lo que salga:

| # | Condición | Hoy |
|---|---|---|
| 1 | Medirlas sobre un repo con agentes **que no sea nuestro** (otro equipo u otro cliente) | ❌ entraron dos el 2026-08-26 y **no valen**: son de curso, no de producción (§arriba) |
| 2 | Que la regla **dispare** allí también (una regla que nunca dispara no se puede promover) | `ag-tool-sin-doc` ya falla esta |
| 3 | Conformidad ≥85% en los tres → `activo`; 60-85% → `debil`; <60% → se queda o se retira | 4 reglas están hoy en 0% |
| 4 | FPR 0 en el `--self-test` después de tocar el enunciado | ✅ verificado |
| 5 | Si la regla marcase >20-30 sitios preexistentes, **la mala es la regla** (regla de inversión) | ya pasó con `ag-print` y `ag-except-mudo`: se acotó el enunciado al camino del agente |

Mientras la fila 1 siga en ❌, la respuesta honesta a "¿qué fuerza tiene este patrón?" es
**ninguna todavía; es una hipótesis con dos observaciones y su comprobador escrito**. Se reevalúa
cuando entre un tercer repo, no por calendario.

### Las tres reglas de roturas de API (CB-34, sub-ola 3.26) — declaradas, no medidas

`ag-temperature-modelo-nuevo`, `ag-reasoning-minimal` y `ag-modelo-retirado` no salen de cómo
escribimos: salen de lo que el **proveedor** rechaza (guías de migración de Claude 5.5 y de GPT-6,
páginas de retiradas leídas el 20-10-2026) y de lo que el spike U.02-U.03 vio fallar. Van al cajón de
§Declarado, no medido, con su fuente en `agente-modelo-y-coste.md` §Roturas, y nacen en `sombra` por
otra razón que las diez de arriba: **son reglas por texto**, y el modelo casi siempre llega por
settings. Por eso la de temperatura tiene tres escalones (el modelo en la misma llamada · en el mismo
fichero · en cualquier sitio del repo) y el tercero avisa de más cuando un repo mezcla modelos.

| Regla | Medido el 31-10 (solo lectura) | Qué dice el número |
|---|---|---|
| `ag-modelo-retirado` | musa/backend **6** · autoparte/apps **1** · autoparte/autopartes **2** | Los mismos sitios que el calendario del spike (`client.py:31` con `claude-3-haiku` ya retirado, `:503`, `settings/base.py:314,326`). Ningún falso positivo leído |
| `ag-temperature-modelo-nuevo` | **0** en los tres | Correcto: hoy mandan `gpt-4.1-mini`/`gpt-4o-mini`, que aceptan la temperatura. Con `OPENAI_MODEL = "gpt-6-luna"` plantado al lado de la copia de `llm_openai.py` de autoparte, **dispara en `:106`**: el 400 que el spike midió |
| `ag-reasoning-minimal` | **0** | Nadie usa `minimal`: la regla solo tiene el sabotaje del `--self-test` como prueba |

Topes de RAM: el recorrido de configuración usa los mismos (`MAX_BYTES_FICHERO`, sin `.env`, sin
`node_modules`); RSS máximo medido, 44 MB.

## Qué NO copiar de la referencia — la lista negra (REF-8)

Buena parte de este catálogo sale de leer un backend Django real en producción. Ese repositorio
tiene cosas excelentes —están arriba, con su medida— y tiene cosas que **no se trasladan**. Sin
esta lista escrita, un agente que lo lea para inspirarse copiará lo peor junto con lo mejor, y con
la misma confianza: todo funciona en producción.

| Qué NO se copia | Por qué | ¿Hay check? |
|---|---|---|
| **El framework CRUD propio entero** (944 líneas de metaprogramación, clases generadas con `type()` en tiempo de ejecución) | Es una inversión de años que **solo se amortiza con 356 tablas homogéneas**. Un proyecto nuevo no las tiene, y hereda toda la complejidad sin ninguno de los beneficios | ❌ juicio |
| **Monkeypatch de `Manager`** (`Manager.for_user = ...`) | Efecto global sobre Django, terceros y el admin; no navegable; genera el ciclo de imports que después se parchea | ✅ `be-py-monkeypatch-django` |
| **Monkeypatch de `FileField.default_validators`** | Igual, y aquí es **seguridad**: la única defensa de subida de ficheros depende del orden de importación. Y es una lista **negra** de extensiones, que no cubre `.svg`, `.html`, ni dobles extensiones | ✅ `be-py-monkeypatch-django` |
| **Lógica de negocio en `signals.py`** (109 receivers; guardar un objeto crea otros cuatro sin que nada lo indique donde se llama) | Control de flujo invisible. Y 9 funciones de servicio quedaron ahí dentro, inalcanzables fuera del `post_save` | ✅ `be-sig-logica-de-negocio` |
| **Efectos (enviar email) desde métodos de modelo** | Cualquier código que toque el modelo puede disparar un correo, incluido un test o un backfill | ❌ juicio |
| **Catch-all `<path:path>` al final de las URLs** | Convierte cualquier 404 en un 200 con la página principal, y hace inalcanzable toda ruta registrada después | ❌ juicio |
| **`FilterSet` declarados dentro de `views.py`** (61 clases) | Nadie los encuentra donde los busca, y se reescriben al lado | ❌ juicio (el equivalente de formularios sí: `be-form-clase-fuera-de-forms`) |
| **`MockRequest` fabricado dentro de una task** | Pagar el acoplamiento a HTTP con un doble falso; falla el día que el código toque un atributo que el doble no tiene, de madrugada | parcial: `be-svc-sin-drf` caza la causa (el servicio que pide `request`) |
| **`beat_schedule` escrito en `celery.py`** | Un periodo de 10 segundos enterrado en código es una decisión operativa que nadie puede cambiar sin desplegar | ❌ juicio |
| **Resultados de tareas en `/tmp` servidos por URL** | Ata el worker y el proceso web a la misma máquina —prohíbe contenedores— y hace descargable cualquier fichero de `/tmp` | ❌ aviso documentado (`backend-celery.md`) |

**Y las ausencias también son datos, en el otro sentido:** ese repositorio tiene **0 constraints, 4
índices y 0 `TextChoices` en 360 modelos**. Ahí acierta nuestro patrón y no el repo. Conviene
decirlo explícitamente para que la referencia no se tome como autoridad en todo: es una fuente
excelente sobre **cómo se organiza** un backend Django grande, y una fuente pobre sobre **cómo se
protege un dato**.

## Quitar Mongo — qué cambia exactamente (REF-9)

El stack canónico es PostgreSQL puro. El backend de referencia usa `djongo` vendorizado, así que
antes de tomarlo como base hay que saber el alcance real de la descontaminación — y, sobre todo,
**distinguir el mecanismo del destino**, que es lo que evita tirar lo bueno con lo malo.

| Uso en la referencia | Alcance medido | Sustituto en PostgreSQL |
|---|---|---|
| **Historial de auditoría** (`HistoricalCRUDModel`) | **~200 de 360 modelos** — la contaminación de mayor alcance | `django-simple-history` sobre tablas normales. **Y la task asíncrona deja de hacer falta**: existía solo para escribir en Mongo |
| Catálogo CIE/ICD | 1 app, solo lectura | tabla con índice **GIN** |
| `form_builder` sobre documentos | 6 ficheros | `JSONField` — es exactamente el caso que cubre |
| Log de acciones | 3 escritores, 3 lectores | tabla con `JSONB` + índice por fecha y tipo |
| `ObjectId` colándose hasta presentación (el framework CRUD importa `bson`) | 1 rama | **desaparece sola** al quitar el resto |

**El mecanismo de auditoría es excelente y sí se traslada**: historial automático + escritura
asíncrona para no pagar una fila de historial síncrona en cada `save()` de 200 modelos. Esa
decisión de rendimiento sobrevive al cambio de base. Lo que no se traslada es el **destino**.

Efecto colateral, y es el premio: `DATABASES` pasa de **11 alias a 1**, los routers desaparecen, se
va el pin de `sqlparse 0.2.4` que bloqueaba la actualización de Django… y **la suite de tests vuelve
a ser ejecutable** (`backend-tests.md` §"que la suite arranque"). La regla `be-no-mongo` marca los
restos; es **débil**, porque un proyecto puede usar Mongo con razón y entonces se exime.

## Reglas que se propusieron y se cayeron al verificarlas (EVO-15)

Se guardan **con su refutación** por una razón práctica: sin esto vuelven a proponerse dentro de
seis meses, con los mismos argumentos, y hay que rehacer el trabajo de tumbarlas.

### ✘ "El código operacional vive en `management/commands/`; un `.py` suelto que importe modelos es un hallazgo"

- **La premisa central era falsa y comprobable.** Se sostenía en que *sin `django.setup()` un script
  standalone no puede tocar el ORM*, y la doc de Django documenta `manage.py shell < script.py` y
  `shell --command=`. El "74 ficheros inejecutables" no medía ficheros muertos: medía **"ficheros
  que no contienen la cadena `django.setup()`"** — la ceguera del detector, no un hallazgo.
- **El canon del propio repo la tumba por aritmética:** 61 comandos frente a 86 scripts = **41,5%**
  de conformidad. Por debajo del 60% no hay patrón, y la regla de inversión (si marcaría >20-30
  sitios, la mala es la regla) marcaba 74.
- **El remedio era una regresión de seguridad.** Promover a comandos oficiales unos scripts
  reconocidamente basura los haría salir en `manage.py help` y parecer soportados — incluido uno
  que vacía una cola republicando mensajes. Eso es convertir un cable pelado en un botón rojo sin
  tapa.
- **Lo que SÍ sobrevive**, en otro eje y mucho más modesto: *todo `.py` que toque el ORM declara
  cómo se ejecuta* → `be-script-sin-runner` (`backend-estructura-apps.md` §4).

### ✘ "La raíz del proyecto solo contiene configuración y paquetes de app"

- **El hallazgo era real y urgente** (89 MB de cuadernos y una clave privada en el repositorio) y
  **el instrumento estaba roto**: la regla mide **ubicación** cuando el daño es **contenido**. Se
  satisface con un `git mv` — los 89 MB siguen en cada clon y la regla da 0 hallazgos.
- **6 falsos positivos frente a 10 aciertos**: marcaba los agrupadores de subapps, `locale/` (la
  ubicación estándar de i18n) y `scripts/`. Un agente "normalizando" eso rompe cientos de imports.
- **La remediación prometida era incorrecta en sus dos daños titulares:** `git rm --cached` **no
  saca los 89 MB del historial**, y una clave privada publicada **se rota, no se borra**.
- **El arreglo correcto no es una regla de patrón, es un hook de pre-commit** (bloquear ficheros
  >500 KB, detectar claves privadas, bloquear `.ipynb`). Doctrina del propio template: lo
  crítico-si-se-ignora vive en hooks, no en prosa — y un hook lo caza en cualquier punto del árbol,
  donde esta regla era ciega. Queda **fuera de este catálogo**, propuesto al TL.

## Declarado, no medido — y qué significa al adoptarlo

`.claude/patterns/README.md` exige "dominancia medida antes de fijar", y tiene razón: un patrón se
infiere del repo. **Estas reglas son la excepción consciente a esa regla**, porque nacen para el
caso en que no hay repo del que inferir. Por eso cada fila lleva su origen declarado y un enlace a
su documento — que es justo lo que la regla **R-9 de Rita** admite: una regla declarada con
`source:` sustituye a los dos precedentes, y se cita textual.

Además, `_fixtures/conforme/` es código real y parseable, así que Rita puede citarlo como
`file:line` igual que citaría el repo. En la práctica estas reglas sí tienen precedentes.

**El estado que trae cada regla es el de un proyecto NUEVO.** En un proyecto que ya tiene código
manda lo que el repo hace — imponerle el estilo de casa haría que Rita marcase medio repo, que es
exactamente lo que US-7 quiere evitar. Protocolo al adoptar sobre código existente:

1. Sembrar todas las filas como `estado: sombra`.
2. Medir: `pattern_check_backend.py --all --json`.
3. Congelar lo preexistente en `baseline/<id>.json` (deuda aceptada, intocable en PRs que no la
   tocan) y promover a `activo` **solo** las reglas cuya violación sea minoritaria. Si una regla
   marcaría más de 20-30 sitios, la mala es la regla (regla de inversión).

## Cómo se nombran los patrones de agente IA — el vocabulario es el de Anthropic (PAT-5)

Los patrones de agente de este set (`agente-*.md`) usan **el nombre de la fuente primaria** —la
guía *Building Effective Agents* de Anthropic— como nombre principal, y mencionan el **alias
popular entre paréntesis la primera vez** que aparece en el documento. Después, solo el nombre
principal.

| El póster de divulgación dice | Aquí se llama (Anthropic) |
|---|---|
| Reflection / Critic | **evaluator-optimizer** |
| Multi-Agent | **orchestrator-workers** |
| — (no aparece en la lámina) | **prompt chaining** |
| — (no aparece en la lámina) | **parallelization** (sectioning / voting) |

Ejemplo de la primera mención, tal como debe escribirse:

> El patrón **evaluator-optimizer** (lo que las láminas de divulgación llaman *Reflection/Critic*)
> separa quien genera de quien juzga…

**Por qué.** Adoptar el vocabulario de un divulgador nos deja hablando un idioma que la
documentación que vamos a leer no usa. El coste no aparece al escribir —ahí cualquier nombre
sirve— sino **al buscar ayuda**: se busca "reflection agent" y no se encuentra la página que
explica el patrón, ni sus condiciones de parada, ni sus fallos conocidos. Y las dos que el póster
ni menciona son las dos más baratas de aplicar.

**Alcance y estado, medido el 22-ago-2026** (la primera medida de esta sección se tomó con solo
dos patrones de agente escritos; se rehace aquí con los cinco que hay):

```bash
$ ls .claude/patterns/stack/agente-*.md
.claude/patterns/stack/agente-cuando-no.md
.claude/patterns/stack/agente-evaluator-optimizer.md
.claude/patterns/stack/agente-memoria.md
.claude/patterns/stack/agente-observabilidad.md
.claude/patterns/stack/agente-tools.md

$ grep -rniE "reflection|critic|multi-agent" .claude/patterns/stack/*.md --exclude=README.md | wc -l
8      # los 8 en agente-evaluator-optimizer.md, y ninguno nombra al patrón
```

**Ningún patrón se llama con el vocabulario del póster.** Los 8 aciertos del grep son de un solo
fichero y de dos clases legítimas: **2** son la mención del alias en la primera línea —lo que esta
convención permite y pide— y **6** son la palabra `critic` **como término de búsqueda medido en
elvion**, en el bloque que demuestra que allí `critic` era en realidad `critical`. Medir un nombre
no es adoptarlo; el grep no sabe distinguirlo y por eso se anota aquí en vez de dejar el `0` viejo.

Nacieron ya con esta convención `agente-memoria.md`, `agente-evaluator-optimizer.md` y
`agente-cuando-no.md` (items `PAT-1`, `PAT-3` y `PAT-4`) y `agente-hitl.md` (`PAT-2`, 2026-08-22). El grep excluye este README a propósito: la tabla de equivalencias de arriba nombra los
alias, y contarla sería contarse a sí misma.

**Límites declarados**, para que nadie la aplique donde no toca:

- **No hay comprobador.** Es una convención de redacción, no una regla del checker: no entra en
  `pattern_check_agente.py` ni bloquea nada. Se verifica leyendo, en la revisión del documento.
- **Solo aplica a los nombres de los patrones de arquitectura de agente.** No renombra nada del
  código (una clase `Critic` en elvion se sigue llamando `Critic`), ni toca `rules/` del harness:
  `parallelization.md` es la rule de repartir trabajo entre TLs, y **no** es el patrón
  `parallelization` de Anthropic. Mismo nombre, cosas distintas.
- **La equivalencia es de nombres, no de definiciones.** Cuando el patrón de casa se aparte de lo
  que describe la guía, se dice en el documento en vez de esconderlo detrás del nombre prestado.

Fuente: Anthropic, *Building Effective Agents*
(https://www.anthropic.com/engineering/building-effective-agents). Contraste de las láminas y las
medidas de cobertura: `.docs/plans/2026-08-21-mapa-y-orden/sources/01-patrones-agenticos.md`.
