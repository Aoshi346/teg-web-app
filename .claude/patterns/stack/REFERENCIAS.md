# Los cuerpos de referencia — qué código miramos para decidir cómo se escribe aquí

> **Para quién es este documento.** Para **ti, agente**, cuando te configuren en un proyecto y
> tengas que construir o revisar un backend Django, un frontend React o un agente LangGraph. No es
> documentación de lectura: es el índice de **dónde está hecho bien**, para que cites precedentes
> en vez de opinar.
>
> **La regla que lo justifica** (`patterns/README.md` §1): un patrón sin **≥2 precedentes
> `fichero:línea`** no es un patrón, es una preferencia. Este documento dice dónde buscarlos.
>
> **NO uses este documento para:** decidir *qué* construir (eso es `pol-product-advisor` y
> `/producto`) · saber en qué orden se crean los ficheros de un proyecto nuevo (eso es
> **`ARRANQUE.md`**, y es el que hay que leer primero) · el porqué de cada decisión (está en el
> patrón concreto, no aquí).

---

## Cómo se usa esto, en tres pasos

1. **`ARRANQUE.md`** te dice qué ficheros crear y en qué orden.
2. **El patrón concreto** (`backend-modelos.md`, `agente-memoria.md`…) te da la regla y el porqué.
3. **Este documento** te dice **en qué código real ir a verlo funcionando**, con el comando para
   abrirlo.

Si vas a proponer algo que se sale del molde, primero busca en estos cuerpos si alguien ya lo
resolvió. Casi siempre sí.

---

## Los dos cuerpos, y dónde viven

| Cuerpo | Ruta | Qué enseña |
|---|---|---|
| **Django + React** | `resources/code-refference/` | Un backend Django grande y vivo, con su frontend |
| **LangGraph** | `.docs/resources/langgraph/` | Cómo se construye un agente conversacional, en 7 sabores |

Ninguno se versiona en git (son código de terceros o snapshots): se **indexan**. El índice medido
de cada uno vive en `<plan>/referencia/*.json` y se ve en la pestaña **El stack** del informe.

### Cómo se traen en una máquina limpia

**El código NO está en el repo, y es a propósito**: son 219 MB entre todos. Lo que sí está
versionado es **`.claude/patterns/referencia/procedencia.json`** — el remote y el **sha exacto** de
cada cuerpo. Con eso se reconstruyen al commit preciso, que es más fiable que guardar el código
suelto: fija la versión.

```bash
python3 .claude/scripts/traer_referencias.py            # qué hay, qué falta, qué está en otro sha
python3 .claude/scripts/traer_referencias.py --traer    # clona lo que falte, al sha del manifiesto
python3 .claude/scripts/traer_referencias.py --solo deepagents
```

Nunca pisa lo que ya existe: si un cuerpo está en otro sha, **lo dice y no lo toca**. Rehacerlo es
una decisión de quien lo mira, no del script.

> ⚠️ **Cuatro de los once son PRIVADOS** y quien no tenga acceso al remote se queda sin ellos:
> `advanced_marketing_system`, `evo-preven`, `elvion` y `proxera_musa`. El script los marca
> `[PRIVADO]` y falla con un mensaje claro en vez de fingir que es un error suyo. Los otros siete
> son públicos y se traen sin credenciales.
>
> **`evo-preven` es el caso raro**: viene de un `.zip` sin git propio, así que **no tiene sha**. Se
> puede clonar la rama `develop` de su remote, pero **no será el mismo commit** que el snapshot del
> 2026-08-24. El manifiesto lo dice con `sha: null` en vez de inventarse uno.

**Y los inventarios medidos viven fuera de los planes**, en
`.claude/patterns/referencia/inventarios/` (604 KB de JSON, versionados). Un plan se congela; lo que
un cuerpo de referencia ES, no. Es la regla 5a del report-kit (PV-3) aplicada aquí: cualquier plan
nuevo hereda los nueve cuerpos sin volver a medirlos.

```bash
# Reindexar un cuerpo (por ejemplo, tras actualizarlo)
python3 .claude/scripts/gen_inventario_stack.py <ruta-del-cuerpo> <plan>/referencia/<nombre>.json
python3 .claude/templates/report_kit/gen_stack_dataset.py <plan>
```

---

## Backend · Django — `evo-preven`

**Ruta:** `resources/code-refference/evo-preven-develop/` — **ya no está en disco**: la copia y su
`.zip` se borraron el 2026-10-18 (T03 · LI-31) y nunca se versionaron. Lo que queda es el inventario
medido (`referencia/inventarios/evo-preven.json`); para volver a mirar el código hay que clonar la
rama `develop` del remote, que no será el snapshot del 2026-08-24 (ver el aviso de arriba).

**Medido el 2026-08-27** — contenido del snapshot del **2026-08-24**, sin git propio, así que **no
tiene sha**: 1401 ficheros `.py` · **325 vistas** · 28 tareas Celery · 19 modelos · 3 serializers.

**Qué mirar aquí, y qué NO:**

| Ve a verlo para… | Porque… |
|---|---|
| **Estructura de apps por dominio** | 40+ apps planas (`campaigns`, `documents`, `equipment`, `courses`…), una por cosa del negocio, no por capa técnica. Es el ejemplo grande de `backend-estructura-apps.md` |
| **Vistas basadas en clase a escala** | 325 vistas es suficiente muestra para ver el patrón repetido, no el caso bonito |
| **Tareas en segundo plano** | 28 tareas Celery reales, con sus reintentos |

> ⚠️ **Lo que NO se copia de aquí, y está medido**: `refactor-progresivo.md` §3 analizó este mismo
> repo y **descartó 13 "mejoras"** que parecían obvias y no lo eran — mover las apps a `apps/`
> (46 renombrados + imports de 740 ficheros, cero problemas resueltos), partir el `settings.py` de
> 960 líneas, enumerar los 384 `from X import *` (que son *load-bearing*: solo 4 símbolos se pisan
> de verdad). **Antes de proponer "modernizar" algo de este repo, lee esa lista.** Ya se estudió.

> 🔒 **Y lo que NO se copia por otra razón: la seguridad de sus endpoints no es canon.** Medido el
> 2026-09-04 sobre el mismo snapshot: **17 `@csrf_exempt` en 5 ficheros** (`api_portal/views.py`,
> `form_builder/views.py`, `import_export_data/views.py`, `questionnaires/views.py`) y **201
> apariciones de `queryset = …objects.all()`** — entre ellas la que `backend-vistas.md` §1.5
> disecciona como el caso de libro de IDOR: `api_portal/views.py:60`, sin `get_queryset()`, con
> `lookup_field` = documento de identidad.
>
> Es **código de cliente en producción, no una demostración de cómo se hace bien**. Sirve para ver
> *qué forma tiene* un Django grande y vivo — estructura, escala, repetición del patrón — y para
> extraer **precedentes de estructura**. No sirve como precedente de **autorización, CSRF ni
> contrato HTTP**: para eso mandan `backend-vistas.md`, `rules/api-http-contract.md` y
> `rules/security.md`. Un agente que grepee aquí "cómo se hace en casa" encuentra `csrf_exempt`
> normalizado 17 veces; por eso este aviso está en el fichero que dice qué mirar.

---

## LangGraph · siete cuerpos, y cada uno enseña una cosa distinta

**La versión importa y varía mucho entre ellos.** Medido el 2026-08-27:

| Cuerpo | Versión declarada | Tamaño medido | Para qué es la referencia |
|---|---|---|---|
| **`advanced_marketing_system`** | sin pin | 1120 py · 585 ts/tsx · **63 modelos · 187 serializers · 104 vistas · 297 componentes · 220 hooks · 18 nodos · 11 tools · 98 tareas** | **El más completo: Django + React + LangGraph en producción.** Es el único con **panel de depuración** (`agente-panel-debug.md`) y con 11 páginas de Streamlit para probar |
| `expertos/deepagents` | sin pin | 8 nodos · **182 tools** · 6 state | Un agente con muchísimas tools. Mira cómo las nombra y describe (`agente-tools.md`) |
| `expertos/open_deep_research` | `>=0.5.4` | **23 nodos · 21 aristas** · 8 state · 5 tools | ⚠️ **Archivado (2026-08-21).** Lectura histórica de la **forma del grafo** (subgrafos anidados), no dependencia ni referencia viva |
| `expertos/langgraph-supervisor-py` | `>=1.0.2` | 3 nodos · 6 tools | ⚠️ **Archivado (2026-09-20).** Su README manda montar el supervisor **con tools** (`agente-arquitecturas.md` §6); se conserva como lectura histórica |
| `expertos/langgraph-swarm-py` | sin pin | 1 nodo · 1 tool | El patrón **swarm**. Es diminuto a propósito (activo: último commit 2026-09-20) |
| `agents` | `>=0.3.18` | 183 py · **66 notebooks** · 6 nodos · 24 tareas | Material didáctico: los notebooks explican paso a paso |
| `LangGraph-Udemy-Course` | **`==1.0.1`** (el único pineado exacto) | 15 py · 15 notebooks · 11 nodos · **10 state** | La versión 1.x moderna. Útil para ver qué cambió respecto a nuestros repos |

**Y para comparar, lo nuestro:** elvion `^0.6.7` · musa `*` **(sin lock ninguno — es el peor caso y
está declarado como tal)**.

> ⚠️ **Antes de copiar una línea de aquí, mira la versión.** Entre 0.3 y 1.0 cambiaron cosas que no
> dan error al copiar: dan comportamiento distinto. Si el cuerpo no declara versión, **no asumas la
> tuya**: comprueba la firma de la función en tu `site-packages`.

### Frontend · `bulletproof-react`

**202 componentes · 72 páginas · 51 hooks.** Es la referencia de estructura de un React grande:
carpetas por *feature*, no por tipo de fichero. Alimenta `frontend-stack.md` y
`frontend-nueva-pantalla.md`.

---

## Qué patrón sale de qué cuerpo

Esta es la tabla que hace útil el documento: **cuando un patrón te pida un precedente, aquí está
dónde buscarlo.**

| Patrón | Ve a verlo en |
|---|---|
| `agente-panel-debug.md` | **`advanced_marketing_system`** — `proxera/services/agent_debug/` y `frontend/src/components/settings/tabs/agent-debug/` |
| `agente-observabilidad.md` | Los expertos **declaran `langsmith` y no escriben instrumentación**: se apoyan en el auto-tracing por entorno. Es un contraejemplo útil |
| `agente-tools.md` | `deepagents` (182 tools) para nombres y descripciones · `advanced_marketing_system` para tools con sub-pasos |
| `agente-arquitecturas.md` | La doc oficial de LangChain (taxonomía de 2026: subagents, handoffs, skills, router, custom workflow) · `langgraph-swarm-py` (activo) · `open_deep_research` y `langgraph-supervisor-py` **solo como lectura histórica: archivados** |
| `agente-memoria.md` | `LangGraph-Udemy-Course` para el `State` moderno (10 campos, versión 1.0.1) |
| `agente-rag.md` | `advanced_marketing_system` — `RAGTestingTab.tsx` y los `RAGSubStep` |
| `backend-estructura-apps.md` · `backend-vistas.md` | **`evo-preven`** (40+ apps, 325 vistas) |
| `backend-celery.md` | `evo-preven` (28 tareas) · `advanced_marketing_system` (98 tareas) |
| `backend-serializers.md` | `advanced_marketing_system` (187 serializers) |
| `frontend-stack.md` · `frontend-nueva-pantalla.md` | `bulletproof-react` (202 componentes, 72 páginas) |

---

## La lista negra — lo que NO se copia de ningún cuerpo

Son errores reales, vistos en estos repos. Copiarlos es fácil porque están en código que por lo
demás está bien:

1. **`requirements.txt` sin pinear** (`langgraph = "*"`). Un agente que funciona hoy y no mañana
   sin que nadie haya tocado nada.
2. **Mutar el estado y devolverlo entero** desde un nodo. En LangGraph un nodo devuelve **solo lo
   que cambia**; devolver todo pelea con los reducers.
3. **Mezclar `input=` con `input_schema=`** — dos APIs de generaciones distintas en el mismo grafo.
4. **`Chroma.from_documents` como efecto de un import**: reindexa la base vectorial cada vez que
   alguien importa el módulo.
5. **Escribir en campos que el `State` no declara.** LangGraph los **descarta en silencio**
   (`langgraph/graph/state.py`). Es el bug mudo más caro y ya nos ha pasado (`agente-memoria.md`).
6. **`operator.add` como reducer de `messages`** en vez de `add_messages`: duplica el historial en
   cada turno.
7. **Un LLM decidiendo lo que un `if` ya decide.** El reparto es: entender → modelo, **ejecutar →
   código**, redactar → modelo (`agente-determinismo.md`).

---

## Cómo se mantiene esto vivo

Un mapa de referencias envejece igual que cualquier documentación. Tres reglas:

1. **Cada cuerpo se reindexa al actualizarlo**, con el comando de arriba. El índice lleva el `sha`
   del cuerpo — y si no tiene git propio, dice **`(sin git propio)`** en vez de heredar el del
   template, que era un fallo mudo hasta el 2026-08-27.
2. **Un cuerpo que ningún patrón cita es un cuerpo que sobra.** Se mide con un grep, y si un cuerpo
   lleva meses sin citarse, o se conecta o se retira.
3. **Los números de este documento están medidos y fechados.** Si al comprobarlos no cuadran, el
   documento miente: reindexa y corrige aquí. No los "actualices de memoria".

```bash
# ¿Qué cuerpos NO cita ningún patrón? (los candidatos a retirar o a conectar)
# Se busca la RUTA, no el nombre suelto: "agents" a secas casa con .claude/agents/ y miente.
cd .claude/patterns/stack
for c in advanced_marketing_system evo-preven-develop bulletproof-react \
         expertos/deepagents expertos/open_deep_research expertos/langgraph-supervisor-py \
         expertos/langgraph-swarm-py LangGraph-Udemy-Course langgraph/agents; do
  printf '%-40s %s documentos\n' "$c" "$(grep -rl "$c" *.md 2>/dev/null | wc -l)"
done
```

Medido así el **2026-08-27**, la cobertura real es baja y hay que decirlo: la mayoría de los cuerpos
se citan en **0 o 1** documentos. Conectar cada patrón con su precedente `fichero:línea` en estos
cuerpos es trabajo pendiente, no algo ya hecho.

---

_Documento vivo · creado 2026-08-27 · los inventarios se regeneran, este índice se edita a mano.
Cuerpos indexados: **9**. Patrones en el molde: **40** (+ este índice, `ARRANQUE.md` y `README.md`)._
