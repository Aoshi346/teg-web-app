# Cómo se mide a Lidia — protocolo ejecutable, NO ejecutado

> **Estado: escrito, sin correr.** Ninguna de las mediciones de este fichero se ha ejecutado
> todavía. Cada bloque dice qué se corre, contra qué build congelado, cuántas veces y **cuál es la
> regla de decisión, escrita antes de mirar los resultados**. Pre-registrar la regla es la mitad
> del valor: sin ella siempre aparece una lectura que justifica lo que ya queríamos hacer.
>
> **Este fichero NO se carga en una corrida normal.** La Regla #0 de Lidia carga `memory.md`, no
> esto. Es para quien vaya a medirla.
>
> **Origen:** AUD-2 · AUD-4 · AUD-6 · AUD-12 · AUD-13 · AUD-16 del plan
> `.docs/plans/2026-08-07-ai4dev-specs-adopcion` (los 6 aprobados como *diseño de experimento*).
> Análisis de fondo: `sources/L-auditoria-agentes-persona.md` y `sources/M-mejorar-lidia-medible.md`.

---

## 0. La pregunta y por qué hoy no tiene respuesta

*¿Ha mejorado Lidia?* Hoy: **no se sabe, y no existe el instrumento para saberlo.** La serie
6.6 → 7.1 → 7.75 mide **el producto auditado** (AUD-1) — la prueba es que los tres auditores
sobre el mismo objetivo en las mismas 3 rondas **divergen en signo**. Y los tres números son
**N=1** sobre tres artefactos distintos: la serie es compatible a la vez con «mejoró», «empeoró»
y «no cambió».

Lo que sí está demostrado, y justifica su coste, es que **funciona**: su gate categórico aguantó
«con ayuda» dos rondas mientras la media subía. Funcionar y haber mejorado son cosas distintas.

## 1. Prerrequisitos — sin esto el experimento produce un número que parece significar algo

| # | Prerrequisito | Estado | Por qué bloquea |
|---|---|---|---|
| P1 | **Build congelado toda la ronda** (AUD-3) | ✅ regla escrita en `rules/qa-loop.md` §1b | La ronda 3 se parcheó en caliente: Vera e Ignacio auditaron builds distintos y se promediaron en un 7.55 que no describe ningún objeto. Un A/B montado sobre un bucle que corrompe sus mediciones hereda la corrupción |
| P2 | **Esquema de salida estable** (AUD-7) | ✅ `templates/trend-delta.schema.json` + `scripts/trend_lint.py` | Sin él el comparador se rompe al parsear — y se rompe *después* de gastar las pasadas caras |
| P3 | **Modelo pinneado + metadata** (AUD-9) | ✅ bloque `run` obligatorio | `model: sonnet` es un alias móvil: el modelo cambia solo y se lee como «mejoró» |
| P4 | **Anclas por hallazgo** (AUD-10) | ✅ en el esquema | Sin ancla, emparejar hallazgo↔defecto lo hace a mano quien construyó la v2 |
| P5 | **Memoria blanqueada para la corrida** | ⚠️ operativo, en cada corrida | Su Regla #0 la obliga a leer una memoria que dice «L-008 CERRADO», «Mobile 5→9», «Score 7.75». Relanzarla sobre `e05a93d` (donde los 7 hallazgos están **abiertos**) le dispara «cerrado que reaparece = regresión P0» en los siete. Hay que blanquearla **y declarar que entonces se mide la Lidia de arranque en frío**, no la verificadora con estado |

## 2. Los dos objetivos congelados

Verificados en este repo (`git log`):

| Alias | Commit | Qué es | Para qué |
|---|---|---|---|
| **T-def** | `e05a93d` | *"report-kit completo pre-QA"* — contiene los 7 defectos que originaron L-001…L-007 | Detección. Es el **único** snapshot utilizable a ciegas: en `e28f0df` y posteriores, la `memory.md` de Lidia versionada dentro del commit **ya trae las respuestas** |
| **T-clean** | `785be03` | *"iter-3 cerrada"* — todos los fixes aplicados | **Falsa alarma**. Es el contrapeso obligatorio del recall: sin él, una v2 sube recall bajando su umbral de reporte y sale «mejor» siendo peor auditora |

Servir con `python3 -m http.server` sobre un **worktree del sha**, nunca sobre el checkout
principal (`file://` está bloqueado — `rules/harness-gotchas.md`).

```bash
git worktree add /tmp/lidia-Tdef   e05a93d
git worktree add /tmp/lidia-Tclean 785be03
( cd /tmp/lidia-Tdef/.claude/templates/report_kit/demo 2>/dev/null || cd /tmp/lidia-Tdef; \
  python3 -m http.server 8813 )      # ajustar a la ruta real del demo en ese sha
```

---

## 3. El orden de ejecución (y por qué no es «primero el benchmark»)

Los cuatro primeros pasos cuestan **≤4 pasadas de navegador** y ya responden buena parte de la
pregunta:

```
AUD-3 congelar ✅ → instrumentación ✅ (AUD-1/7/8/9/10/11) → recálculo del histórico ✅ (gratis)
   → §4 suite de conformidad (2-4 pasadas)  ← lo más rentable por pasada
   → §5 σ + A/B de memoria  (10 pasadas, comparten 5)
   → §6 multipersona        (+3 pasadas)
   → §7 A/B v1 vs v2        (20 pasadas) — SOLO si §5 produce una v2 que exista
```

**Presupuesto de RAM.** Cada pasada abre navegador y **cuenta doble** (`rules/ram-pytest.md`):
máximo 3 instancias **con navegador** (ese tope NO se deriva: cuentan doble), nunca solapadas con
`pytest`. Las pasadas se serializan o van de dos en dos.
Coste unitario medido: una ronda de Lidia = 25-33 capturas ≈ 3.6-4.0 MB en disco.

---

## 4. AUD-13 · Suite de conformidad con sus propias reglas — **empezar por aquí**

**Qué mide:** ¿hace lo que dice que hace? Es lo más parecido a medir **al agente** y no al
producto que se puede conseguir barato, y no necesita ni dos versiones ni conocer la verdad del
producto — que es justo lo caro.

**Coste:** 2-4 pasadas. **Determinista:** cada regla es un test de pasa/no pasa; ningún humano
interpreta nada. O marcó lo que su regla le obliga a marcar, o no lo marcó.

| Test | Regla de Lidia | Fixture (página mínima servida en local) | Resultado esperado |
|---|---|---|---|
| C-1 | **L-B** clickbait | CTA con `shine sweep` animado (opacity 40%) | Reporta **CRITICAL "clickbait"**. Si lo elogia como micro-interacción → FALLO |
| C-2 | **L-D** fotos, perfil `landing` | Landing sin ninguna foto humana | `fotos_videos ≤ 4` |
| C-3 | **L-D** fotos, perfil `herramienta-interna` | El mismo fixture declarado herramienta interna | `fotos_videos.na = true` y **fuera** de `score_profiled` |
| C-4 | **L-H** evaluación ciega | Prompt que incluye "mejoras aplicadas en esta versión: X, Y" | El REPORT **no** menciona el delta ni premia progreso |
| C-5 | **Regla #0** regresión | Memoria con `L-XXX CERRADO` + fixture donde ese defecto reaparece | Lo marca **regresión P0** |
| C-6 | **escalado ≥3** | Memoria con un finding con `versions_seen` de 3 entradas | Lo escala a **P0 automático** |
| C-7 | **gate categórico** | Fixture con una página claramente «Confuso» | Veredicto global ≠ «sí», por alto que salga la media |
| C-8 | **L-A** 2 segundos | Página sin decir a quién va dirigida | `claridad ≤ 4` |

**Regla de decisión (pre-registrada):** la suite es un **gate binario, no una nota**. Un fallo en
C-1, C-5 o C-7 es bloqueante — son sus reglas «no negociables». Un fallo en el resto se documenta
y se repite la pasada una vez; si se repite, es un defecto de la ficha, **no** una excusa para
relajar el test. Repetir la suite tras cada edición de la ficha es su prueba de regresión.

⚠️ **Lo que esta suite NO mide:** que sus reglas sean *buenas*. Solo que las cumple. Una regla
mala cumplida al 100% sigue siendo una regla mala.

---

## 5. AUD-2 (σ) + AUD-12 (A/B de memoria) — 10 pasadas que comparten 5

Van juntas a propósito: **el brazo "con memoria" ES el brazo de σ**, así que dos experimentos
salen por el precio de uno y medio.

### 5.1 Diseño

| Brazo | K | Objetivo | Memoria | Sale de aquí |
|---|:-:|---|---|---|
| A | 5 | T-def (`e05a93d`) | **completa** (`memory.md` tal cual, blanqueada de veredictos de rondas futuras) | **σ de Lidia** (AUD-2) |
| B | 5 | T-def (`e05a93d`) | **solo método** (limitaciones de Playwright, falso positivo del favicon, truco `scrollWidth` vs `clientWidth`) — sin la parte de veredictos | **efecto del anclaje** (AUD-12) |

Todo lo demás fijo y registrado en el bloque `run`: mismo `model_id` exacto, misma
`calibration_version`, mismo `target_sha`, mismo `agent_sha`, mismos viewports, mismo texto de
persona. `run_index` = 1..5.

### 5.2 Qué se calcula

- **σ** = desviación típica de `score_profiled` en las 5 pasadas del brazo A.
- **Reproducibilidad** = **Jaccard** medio entre los conjuntos de hallazgos de cada par de pasadas
  del brazo A (10 pares). Es la métrica estrella y la más barata: no necesita verdad de ningún
  tipo y es diagnóstica por sí sola — *un auditor que no coincide consigo mismo no es fiable por
  mucho recall que tenga*.
- **Estabilidad del bit** = % de las 5 pasadas con el mismo `verdict_categorico.label`.
- **Δ anclaje** = media(A) − media(B) sobre `score_profiled`; test de signo sobre las 5 parejas.

### 5.3 Reglas de decisión, pre-registradas

1. **AUD-12 (el split de memoria) se implementa SOLO si `|Δ| ≥ σ`.** Si Δ < σ, la hipótesis del
   anclaje **está muerta**, se anota como descartada y **no se toca la memoria**. Para eso sirve
   tener el instrumento antes que la idea.
2. **AUD-11 se valida o se retira aquí**, gratis, con los mismos datos: la predicción es que el
   **bit saldrá estable (≥4/5 idénticos) y la media variará ≥0.5 puntos**. Si sale al revés — la
   media más estable que el bit — la sección «la media es diagnóstico» de la ficha **se retira**.
3. **Lo que σ probablemente hará con la historia.** Si σ resulta ~0.5 en la escala de 10 —
   plausible: la propia Lidia movió `mobile` 4 puntos al volver a mirar — entonces nada por debajo
   de ~1.0 punto es interpretable y **toda la progresión 6.6 → 7.1 → 7.75 cabe dentro del ruido**.
   En particular la regla de parada de `/qa-loop` compara un delta de **+0.07** contra un ruido no
   medido probablemente 5-10 veces mayor: **hoy esa regla no significa nada**. No se puede
   afirmar antes de medir; por eso este bloque va antes que cualquier A/B.

⚠️ **Límite declarado:** el brazo B mide **la Lidia de arranque en frío**, no la verificadora con
estado que produjo su mejor trabajo en las rondas 2-3. Son agentes distintos y la comparación no
dice cuál es mejor *en producción*, solo cuánto pesa el anclaje en la nota.

---

## 6. AUD-16 · Multipersona — ¿señal distinta o disfraz? (+3 pasadas)

**Estado de partida:** `.claude/agents/personas/` contiene **solo `_example/`** con
`{"rounds": []}`. Ninguna persona ha corrido nunca. El único artefacto multipersona que existe
está etiquetado por su propio `RESULT.md` como «ejemplo de formato», y en un plan **sin UI**.
Encima la ficha de Lidia sigue con los huecos sin rellenar (`[Nombre Persona]`, `[edad]`) mientras
su memoria corre como «María, dueña de negocio»: **la persona cambió entre la ficha y la ejecución
sin que quedara registro.** Hoy la multipersona es cosmética hasta que se demuestre lo contrario.

**Diseño:** una persona nueva, **3 pasadas**, mismo objetivo congelado (T-def). La persona nueva
debe diferir en **el trabajo que viene a hacer** (jobs-to-be-done), no en la biografía: *una
peluquera y un coach que buscan lo mismo son el mismo agente con disfraz distinto*.

**Se compara** contra la distribución nula que ya dieron las 5 pasadas de §5:
- **Jaccard** entre los conjuntos de hallazgos de las dos personas.
- **Distancia entre medias de persona** contra la **σ intra-persona** ya medida.

**Regla de poda, escrita ANTES de mirar los resultados:**

> Si la diferencia entre personas **< σ intra-persona** **y** el Jaccard de hallazgos **> 0.7**
> → **es un disfraz**: se poda y se queda una sola persona.

**Predicción falsable:** los *scores* apenas divergirán —todas comparten modelo base, la misma
rúbrica de 8 dimensiones y los mismos tests L-A…L-H, así que la persona entra **solo por la
prosa**—; si hay señal, aparecerá en **qué hallazgos emite cada una**, no en la nota. Por eso la
métrica que decide es el Jaccard, no la media. Y por eso la variable real de la multipersona es
**el flujo que se le pide completar**, no su biografía.

---

## 7. AUD-4 · La verdad de referencia — replay histórico primero

Sin verdad conocida no hay recall: solo sabemos lo que un auditor encontró, nunca lo que se le
escapó. Tres opciones, y el orden importa: **(a) ahora · (b) después · (c) nunca como verdad.**

### (a) Replay histórico — coste de preparación cero, ejecutable hoy
El repo ya tiene 3 rondas de hallazgos contra builds identificables por commit. Se corre el
auditor candidato contra T-def y se puntúa frente al conjunto de defectos que **acabaron
confirmándose reales** a lo largo de las 3 rondas (~40 entre los tres auditores; 7-8 de Lidia),
**cada uno validado por el commit que lo arregló** — la forma de confirmación más fuerte
disponible, y defectos reales con su dificultad real.

*Límites que hay que escribir en el informe:* (1) solo contiene defectos que **alguien acabó
encontrando** → es *recall@conocidos*, relativo y no absoluto; (2) un hallazgo fuera del conjunto
puede ser cierto-pero-nunca-detectado, así que **hay que adjudicarlo a mano**, no contarlo como
falso positivo por defecto; (3) un solo objetivo de un solo tipo (HTML autocontenido) → no
generaliza a una app Django.

### (b) Defectos sembrados — después, construidos desde la verdad de (a)
Revertir fixes **reales** del historial de git en lotes pequeños e independientes, en vez de
inventar bugs sintéticos. Dos avisos duros: **no sembrar dentro del bloque
`/* SHARED:BEGIN/END */`** (`check_shared_block.py` obliga a que sea idéntico byte a byte en las 5
plantillas: ahí el defecto lo caza un `grep`, no una auditora), y reservar un subconjunto **oculto
y rotado** o el agente se sobreajusta al examen.

### (c) Consenso entre auditores — **NUNCA como verdad**
Penaliza estructuralmente al mejor auditor (un hallazgo único y cierto cuenta como falso positivo
porque nadie más lo vio) y **certifica los puntos ciegos compartidos** — Lidia, Vera e Ignacio
comparten `calibration-v2`, así que fallan juntos. Uso admisible: **triaje barato de falsos
positivos**, nada más.

---

## 8. AUD-6 · El A/B v1 vs v2 — 20 pasadas, y solo si existe una v2

**No se lanza hasta que §5 produzca una v2 real.** Hoy no existe: la única candidata es el split
de memoria (AUD-12), y está condicionada a que Δ ≥ σ.

**Diseño:** 2 brazos × K=5 × 2 objetivos (T-def + T-clean) = 20 pasadas, **pareado** (ambas
versiones sobre los mismos objetivos).

### Métricas, ordenadas por fiabilidad — y esa jerarquía es el punto

| Nivel | Métrica | Cómo se compara |
|---|---|---|
| **Primaria** | **Gate categórico** (1 bit por corrida) | McNemar pareado v1 vs v2; test-retest = % de veredictos idénticos en las 5 |
| **Primaria** | **Detección de los defectos conocidos** en T-def, **ancla contra ancla** | recall por corrida; McNemar por defecto. ⚠️ Con el aviso de circularidad: esos defectos son hallazgos de la propia v1, así que mide *reproducibilidad*, no capacidad de detección |
| **Primaria** | **Falsa alarma** en T-clean | nº de hallazgos P0/P1 sobre un objetivo sin defectos conocidos. Contrapeso **obligatorio** del recall |
| Secundaria | **Conformidad** (§4) | suite pass/fail |
| **Diagnóstico, NUNCA titular** | media de las 8 dimensiones | media ± SD; Wilcoxon pareado |

### Regla de decisión, escrita ANTES de correr

Con **1 objetivo × K=5 por brazo, el A/B solo detecta cambios casi categóricos** (0-1/5 → 4-5/5).
Se dice el número porque es la parte incómoda: cualquier diferencia más fina exigiría ~25-30
artefactos independientes o ~100-120 defectos, y eso **está descartado** (ver la tabla de
descartes en la ficha de Lidia).

`v2` se declara mejor **solo si se cumplen las tres**:

1. **Superioridad categórica** en al menos una métrica primaria: v2 detecta en ≥4/5 corridas algo
   que v1 detecta en ≤1/5, o su gate acierta donde el de v1 falla, sobre el mismo objetivo.
2. **No inferioridad en ruido**: la falsa alarma en T-clean no sube más de **+0.5** hallazgos
   P0/P1 por corrida (margen pre-registrado).
3. **No inferioridad en estabilidad**: la SD de la media no empeora.

Si las tres se cumplen a medias, la conclusión correcta es **«no se puede demostrar que v2 sea
mejor»** — y no se busca otra métrica hasta encontrar una que gane.

### Lo que este A/B NO puede decidir (escribirlo en el informe final)

- **Validez** frente a usuarios reales: **NO MEDIBLE** sin presupuesto (5 usuarios sobre un
  snapshot). Mide consistencia y acuerdo, nada más.
- **Fidelidad de persona y accionabilidad**: dos agentes detectan lo mismo, uno escribe algo que
  el equipo arregla y el otro algo que se ignora. No medible con defectos conocidos.
- **Descubrimiento de lo desconocido**: su mejor hallazgo real —**L-008**, la nav 100% fuera del
  viewport en las 5 páginas— **no podía estar en ningún catálogo**: apareció porque el fix de
  L-006 creó un problema que nadie predijo. Ningún benchmark puede contener eso por construcción.

### `matrix-eval-harness.js` — sirve con 4 cambios, no tal cual

`.claude/workflows/matrix-eval-harness.js`. El esqueleto encaja (`MATRIX` = versiones del auditor,
`EVAL_SET` = build congelado + ficha de verdad, y la fase `verify` —*"¿son fallos reales o
artefactos del set de evaluación?"*— es casi literalmente el paso de adjudicación que hace falta).
Lo que hay que cambiar antes de usarlo:

| # | Problema hoy | Arreglo |
|---|---|---|
| 1 | **Sin repeticiones**: `pipeline(MATRIX, run, verify)` corre cada config **una vez**, y la varianza es el problema central | Expandir la matriz a tuplas `{id, version, rep}` (5 reps × 2 versiones = 10) y agregar por `version` al final. El runtime lo aguanta: tope de 16 concurrentes |
| 2 | **`rank()` es incorrecto**: `primary_metric + secondary_metric` deja que recall y precisión se compensen en silencio, e **ignora el coste** | Ordenar por F1 (o por recall con una precisión mínima) y sacar el coste como **columna aparte**, nunca como sumando |
| 3 | **No hay emparejador contra la verdad**: `SCORE_SCHEMA` tiene `failed_cases` pero nada mapea hallazgos↔defectos | Etapa de matching `{findings[], ground_truth[]}` → `{matched[], missed[], novel[]}`, con el juez **ciego a la versión** |
| 4 | **No reporta varianza**: corona un ganador con n=1 | Mostrar **media ± dispersión por versión** y decir explícitamente cuándo la diferencia cae dentro del ruido. Un harness que declara ganador con n=1 **es peor que no tenerlo**: fabrica confianza falsa |

Detalle menor: `avg_cost_usd` está en el esquema y **nada lo rellena** — hay que poblar `tokens` y
`wall_ms` o el eje de coste queda vacío. (Ningún agente registra hoy coste de auditar; sin él,
«¿ha mejorado?» no se puede responder aunque se midiera la calidad: una versión que encuentra un
10% más gastando el triple no es mejor.)

---

## 9. Qué NO hay que medir, y por qué

Está en la ficha de Lidia, sección «Lo que ya se descartó» (AUD-18). Resumen de una línea cada
uno, para no reabrirlos aquí: catálogo de 100-120 defectos sembrados (≥150 pasadas, >10× todo el
QA hecho), gold set desde sus propios aciertos (circular), recall solo (gameable), consenso entre
auditores (penaliza al mejor, certifica el punto ciego común), κ/Krippendorff como titular
(mienten por prevalencia).

---

_Protocolo v1 · 2026-08-08 · AUD-2/4/6/12/13/16. **Ninguna medición ejecutada.**_
