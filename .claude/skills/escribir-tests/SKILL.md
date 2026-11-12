---
name: "escribir-tests"
description: >-
  Usar cuando haya que ESCRIBIR tests o montar la suite de un módulo: 'escribe los tests de apps/X',
  'esto no tiene ni un test', 'añade un test que cubra este bug', 'pairwise', 'property-based'. NO
  usar para: juzgar tests que ya existen (code-review-gate), un E2E intermitente
  (rules/verification.md), el pre-DONE (verification-loops) ni los datos tras migrar
  (migration-integrity-checks).
user-invocable: true
metadata:
  version: 1.3.0
  author: Tech Lead Template
  category: workflow
  updated: 2026-10-21
  source: "agents/especialista-testing.md — archivado 2026-08-22, ver _archive/2026-08-22/README.md"
  absorbe: "pairwise-test-data (§Combinatoria, references/pairwise.md + pairwise.py) — fusionada el 2026-10-19 (LI-10)"
---

# escribir-tests — el orden en que se escribe un test, y cómo se corre sin tumbar el servidor

## Cuándo se activa (detalle)

Disparadores: 'escribe los tests de apps/X', 'esto no tiene ni un test', 'monta la suite de este
módulo', 'añade un test que cubra este bug', 'qué nivel de test le pongo a esto', 'el test pasa pero
no prueba nada', 'pytest me tumbó el servidor', '/escribir-tests', 'write tests for this module',
'add a regression test'. Y cuando las entradas se multiplican: 'son demasiadas combinaciones',
'genera datos de prueba', 'pairwise', 'all-pairs', 'cobertura combinatoria', 'matriz de
compatibilidad', 'combinaciones de X e Y', '/pairwise-test-data' (§Combinatoria: genera el conjunto
mínimo y verifica que no queda ningún par sin cubrir). Y cuando un criterio dice siempre/nunca:
'pruebas basadas en propiedades', 'property-based', 'Hypothesis', 'fast-check', 'invariante'
(§Propiedades: del Gherkin a la propiedad). Decide el NIVEL, enruta al patrón de casa que
corresponde (patterns/stack/backend-tests.md · tests.md · rules/verification.md) y da el orden de
ejecución seguro en esta máquina (hook check-ram.sh, por módulo, nunca --cov). · NO usar para:
JUZGAR tests que ya existen o que escribió otro (eso es code-review-gate §rúbrica de 7 puntos),
arreglar un E2E que falla de forma intermitente (rules/verification.md), el checklist pre-DONE de
una tarea entera (verification-loops), ni comprobar la integridad de los datos tras una migración
(migration-integrity-checks).

## Principio

**Cómo se ve un buen test ya está escrito y medido** en el patrón de casa
(`patterns/stack/backend-tests.md` y `tests.md`, cada uno con su comprobador). Lo que no estaba en
ninguna parte es **el orden**: qué nivel elegir, dónde poner el fichero para que el descubridor lo
encuentre, cómo ejecutarlo sin OOM en esta máquina y cómo saber que el test sirve para algo.

Esta skill es ese orden. **Enruta al mecanismo, no lo reescribe**: si volviera a pegar aquí el
`ViewSet` de ejemplo y el `render()` de Testing Library habría dos verdades, y la que envejece
siempre es la copia. Es exactamente el defecto por el que se retiró el agente del que viene
(`_archive/2026-08-22/README.md`).

## Contrato de entrada

| Necesita | Si falta |
|---|---|
| **Qué módulo/fichero** hay que cubrir | **Pregunta.** No elijas tú qué cubrir: es una decisión de alcance |
| **Qué debe demostrar** el test | Derívalo del cambio (`git diff`) o del bug. Si no sabes qué afirmar, no escribas todavía: el paso 1 no se puede hacer |
| El stack | Míralo (`ls`, `pyproject.toml`/`package.json`). No lo preguntes si está en el disco |

---

## Paso 0 — ¿Hay red? (30 segundos, y decide si el resto sirve)

Antes de añadir un test a una suite que ya existe, comprueba que la suite **se entera** cuando algo
se rompe. Una suite que nunca se ha visto en rojo no es una red (`rules/refactor-progresivo.md` §1):

```bash
# Rompe UNA línea a propósito en el módulo y comprueba que la suite se pone ROJA
pytest apps/<modulo>/ -v --maxfail=1     # debe salir ROJO con el sabotaje puesto
git checkout -- <el fichero saboteado>
```

Y en un proyecto Django que nunca ha corrido tests, el primer fallo no es de tests: **es que la
suite no arranca**. `pytest-django` crea una base por cada alias de `DATABASES`, y un alias sin
`ENGINE` la tumba con un error que no dice que la causa sea la configuración. Compruébalo primero
(`backend-tests.md` §"Lo primero, y no es escribir tests"):

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-test-db-alias-sin-engine
```

---

## Paso 1 — El nivel

**Un test vive en el nivel más barato que puede demostrar lo que afirma.** Lo que decide el nivel no
es el tamaño del código probado: es *qué se está afirmando*.

| Lo que afirmas | Nivel | Herramienta | El patrón que manda |
|---|---|---|---|
| Una regla de negocio, un cálculo, un estado | Servicio / unitario | pytest · Vitest sin DOM | `patterns/stack/backend-tests.md` · `tests.md` |
| Que la BD rechaza lo que debe rechazar | Modelo | pytest + `django_db` | `backend-tests.md` §pirámide |
| Que un componente hace lo que promete, con su red simulada | Integración | Testing Library + MSW | `tests.md` (**sin navegador**) |
| El contrato de un endpoint: status, forma del error, **filtrado por dueño** | API | pytest + `APIClient` | `backend-tests.md` · `rules/verification.md` §Smoke testing (requests reales) |
| Que una task no se ejecuta dos veces | Idempotencia | pytest | `backend-celery.md` |
| Un flujo crítico completo (login, el que cobra) | E2E | Playwright | **`rules/verification.md` §Estabilidad E2E** (el único que abre navegador) |

Dos fronteras que no se cruzan, y son las que producen suites lentas y frágiles: **un test de
integración no abre navegador y un E2E no usa `render()`**. Lo comprueba `fe-nivel-del-test`.

> El test que más vale de todo un backend multi-usuario es **que un usuario no ve las filas de
> otro**. Si el módulo tiene dueño y solo escribes uno, escribe ese.

---

## Paso 2 — Dónde va el fichero y cómo se llama

Un test que el descubridor no encuentra **no falla nunca**, y por eso es peor que no tenerlo: alguien
lo escribió creyendo que protegía algo. Django descubre `test*.py`; pytest, `test_*.py` y
`*_test.py`. Cualquier otro nombre no corre.

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-test-descubrible,be-test-stub-vacio
```

**Sobre el nombre de la función, medido en este repo el 2026-08-22:**

```bash
grep -rhcE "^\s*def test_" --include="*.py" . | paste -sd+ | bc   # → 362
grep -rhoE "def test_should_[a-z0-9_]*" --include="*.py" . | wc -l # → 0
```

362 funciones de test y **cero** usan el `test_should_<X>_when_<Y>` que enseñaba el agente
archivado. Lo que sí se usa es `test_<sujeto>_<lo que debe pasar>`
(`test_abrir_expediente_asigna_dueno`, `test_zero_denominator`). **No impongas la convención que
nadie sigue**: el nombre tiene que decir qué debería pasar, para que al fallar se sepa si el fallo
importa. Ahí acaba la regla.

---

## Paso 3 — Escribir

Lee **el patrón que corresponde antes de teclear** (30 segundos, y trae fixtures, factories y el
antipatrón que evita):

| Estás escribiendo | Lee | Lo que te ahorra |
|---|---|---|
| Backend Django/DRF | `patterns/stack/backend-tests.md` | `conftest.py`, `factory_boy` con `Sequence` (el literal revienta el `unique` en el test de al lado), `--reuse-db`, la trampa de `on_commit` |
| Frontend React | `patterns/stack/tests.md` | La prioridad de consulta (`getByRole` ▸ … ▸ `getByTestId`), MSW en el boundary, por qué `toMatchSnapshot` no afirma nada |
| E2E | `rules/verification.md` §Estabilidad E2E | Estado determinista, `data-testid`, esperar por condición y no por tiempo |
| Muchas combinaciones de entrada | §Combinatoria, abajo (`references/pairwise.md`) | El CSV de casos, para no escribir 40 tests a mano |

⚠️ **Recordatorio repetido a propósito**: aunque el test parezca trivial y "ya sepas cómo va", el
patrón se abre igual. Es justo en el test trivial donde se cuela el `vi.mock('../api/…')` o el
`Model.objects.create(referencia="EXP-1")` que rompe el fichero entero dos semanas después.

### Combinatoria: cuando las entradas se multiplican (antes skill `pairwise-test-data`)

Con ≥3 variables que interactúan (navegador × rol × plan × idioma, feature flags, parámetros
opcionales que se combinan), el cartesiano es inviable y elegir cuatro casos "a ojo" deja agujeros
que nadie puede nombrar. **Pairwise** genera el conjunto mínimo en el que cada par de valores de
cada par de variables aparece al menos una vez, y el script lo **verifica**:

```bash
python3 .claude/skills/escribir-tests/pairwise.py variables.json          # casos + verificación
python3 .claude/skills/escribir-tests/pairwise.py variables.json --csv > tests/data/casos.csv
# exit 0 = todos los pares cubiertos · exit 1 = faltan pares (no uses la salida)
```

Medido al fusionarlo: 3·3·2·2·2 valores → **9 casos** frente a 72 del cartesiano, 0 pares sin cubrir.
Lo que no se negocia: un valor por **clase de equivalencia** (bordes y tóxicos incluidos, no veinte
datos), **re-verificar** tras filtrar combinaciones imposibles, y **añadir a mano** los tríos que ya
mordieron (pairwise cubre pares, no tríos). Con ≤2 variables, el cartesiano entero; si buscas romper
la lógica de negocio, es `marco-qa-breaker`. Procedimiento completo (JSON de variables, volcado a
`parametrize`, restricciones, anti-patterns y ejemplos): **`references/pairwise.md`**.

### Propiedades: del criterio de aceptación a la prueba que genera los casos (MO-80)

Un ejemplo fijo cubre el caso que alguien imaginó. Una **propiedad** declara lo que tiene que cumplirse
**siempre** —«el total del carrito nunca es negativo»— y la herramienta genera cientos de entradas,
y cuando una la rompe la **reduce al caso mínimo**. No hace falta un agente aparte: quien escribe el
código escribe sus propiedades, con esta skill.

**De dónde salen.** De los criterios de aceptación que ya existen: el Gherkin de
`arranque/02-requisitos.md` (fase 1b de `/arrancar`) y el `spec.md` que deriva
`scripts/requisitos_to_spec.py`. **Cada «Entonces» que dice siempre, nunca, cualquier o ningún es una
propiedad candidata**; los que hablan de un caso concreto se quedan como ejemplo fijo.

| Forma del criterio | Propiedad | Ejemplo |
|---|---|---|
| «…entonces **nunca** X» / «**siempre** Y» | Invariante: para toda entrada, se cumple | el total ≥ 0 · el stock nunca baja de 0 |
| «exportar y volver a importar deja lo mismo» | Ida y vuelta: `leer(escribir(x)) == x` | CSV, JSON, serializadores |
| «repetirlo no cambia nada» | Idempotencia: `f(f(x)) == f(x)` | cancelar, normalizar, reintentar un webhook |
| «añadir un producto no baja el total» | Metamórfica: cambio conocido en la entrada → efecto conocido en la salida | ordenar, filtrar, sumar |
| «lo rebajado no se descuenta» | Condicional: dada la condición, la salida es la que dice | `rebajado → precio_final == precio` |

| Stack | Herramienta (2026-10-21) | El ejemplo, en su forma |
|---|---|---|
| Python | **Hypothesis 6.170.5** · MPL-2.0 | `@settings(max_examples=200)` + `@given(lineas, cupones)` y un `assert total(lineas, cupon) >= 0` |
| JS/TS | **fast-check 4.10.2** · MIT | `fc.assert(fc.property(fc.array(linea), fc.integer({min: 0, max: 5_000}), (l, c) => total(l, c) >= 0), {numRuns: 200})` |

```python
from decimal import Decimal
from hypothesis import given, settings, strategies as st

precios = st.decimals(min_value=Decimal("0.01"), max_value=Decimal("999.99"), places=2)
lineas = st.lists(st.tuples(precios, st.integers(min_value=1, max_value=20)), max_size=10)
cupones = st.decimals(min_value=Decimal("0"), max_value=Decimal("50"), places=2)

# Criterio: «Dado un carrito con cupón, cuando se calcula el total, entonces NUNCA es negativo»
@settings(max_examples=200)
@given(lineas, cupones)
def test_el_total_nunca_es_negativo(lineas, cupon):
    assert total(lineas, cupon) >= 0, f"{lineas=} {cupon=}"
```

**Probado aquí** (2026-10-21, `_archive/2026-10-20/medicion-2.17/pbt/`): contra un `total` que resta el
cupón sin tope, el test de ejemplo de siempre (`30 € × 2 − 10 € = 50 €`) **pasa**; la propiedad lo
rompe y Hypothesis lo reduce a `lineas=[], cupon=Decimal('0.01')` → `-0.01`. fast-check, con la
misma propiedad en céntimos, da `Counterexample: [[],1]` a los 10 casos. Con el tope
(`max(neto, 0)`), los dos en verde.

Lo que no se negocia:
- **Acotada por módulo.** Cada ejemplo es una ejecución: `max_examples`/`numRuns` explícitos (los dos
  traen 100 por defecto), dentro del `pytest <módulo>` del Paso 4 y con el mismo gate de RAM.
- **La propiedad viene del criterio, no del código.** Escribirla mirando la implementación es validar
  el código contra sí mismo; se escribe desde el «Entonces».
- **El contraejemplo reducido se queda como ejemplo fijo** (`@example(...)` en Hypothesis): es un caso
  real que ya mordió.
- `.hypothesis/` (la base de ejemplos de Hypothesis) va al `.gitignore` del proyecto.
- **No sustituye a §Combinatoria, la completa:** pairwise cubre combinaciones de valores discretos
  (rol × plan × idioma); una propiedad cubre rangos de valores y lo que tiene que cumplirse en todos.

### Si el fallo está fuera de tu claim: se escribe el test, no se arregla el código

Con varios frentes en paralelo (`rules/parallelization.md` §file claims), encontrar un fallo real en
ficheros que ha reclamado otro frente **no da derecho a tocarlos** — y anotarlo en un informe no
sirve, porque nadie lo ejecuta. La salida es escribir el test **dentro de tu claim**, marcado
`@pytest.mark.xfail(strict=True, reason=...)`, con el `reason` llevando `fichero:línea`, el
diagnóstico y el arreglo concreto: eso convierte la queja en un parte de trabajo que corre en cada
suite.

Lo que lo cierra es el `strict=True`. Sin él, el día que alguien arregle el código el test pasa a
XPASS, nadie se entera y el marcador se queda ahí para siempre. Con `strict`, el arreglo **rompe la
suite** y obliga a retirar el marcador — el test se autodestruye cuando ha cumplido su función. El
protocolo completo, con el ejemplo y el caso que lo originó (un bug que no daba **ninguna** señal),
está en `rules/parallelization.md` §file claims.

⚠️ No es una excusa para no arreglar lo tuyo: **dentro de TU claim un fallo se arregla, no se marca
como `xfail`**. El marcador es para lo que no puedes tocar.

---

## Paso 4 — Correr (el gate es real, no un consejo)

**Paso 1, siempre, y es un hook que bloquea:**

```bash
bash .claude/hooks/check-ram.sh && echo "vía libre"
```

Umbral, tope de sesiones (derivado de la RAM libre, no fijo) y workers: los calcula el hook —
`bash .claude/hooks/check-ram.sh --explain`. No los copies aquí: pregúntaselo. El detalle es
`rules/ram-pytest.md` — **no lo copies a ningún sitio**: la copia que llevaba el agente archivado se
quedó desfasada y enseñaba a contar instancias así:

```bash
ps aux | grep claude | grep -v grep | wc -l    # ← el conteo que enseñaba el agente: 7
```

Medido a la vez, el 2026-08-22: **7 frente a 4** del hook. El conteo ingenuo engloba el daemon, los
`bg-pty-host`/`bg-spare` y hasta shells cuyo `PATH` contiene `/root/.claude/`; con él, el gate
bloquea siempre, y un gate que bloquea siempre se aprende a ignorar. La copia del conteo «bueno» que
había aquí envejeció igual: el 2026-10-07 contaba como sesiones los Vitest de los worktrees de fitapp
y el hook cambió de forma de contar (por el binario de Claude Code, MO-23). **Usa el hook, no lo
reimplantes**: la línea «Sesiones ahora» de `--explain` es el conteo.

```bash
pytest apps/<modulo>/ -v --maxfail=3     # ✅ por MÓDULO
pytest -k "test_abrir_expediente" -v     # ✅ un test suelto
pytest -n <N> apps/<modulo>/ -v          # ✅ workers explícitos, N ≤ los de --explain

pytest            # ❌ la suite entera → OOM, y el OOM mata la sesión y lo que estuviera a medias
pytest -n auto    # ❌
pytest --cov      # ❌ coverage multiplica la RAM
```

Con muchos módulos: chunks, y `check-ram.sh` entre chunk y chunk.

> **Límite honesto sobre `--cov`:** aquí no hay ningún gate de cobertura y no es un olvido — medirla
> exige correr la suite entera con `--cov`, que es lo que el límite de RAM prohíbe
> (`backend-tests.md` §"Lo que NO se comprueba"). El gate de cobertura, cuando exista, será de CI.
> Y `settings.local.json:44` **tiene `Bash(pytest --cov*)` en el allow**: la prohibición es de
> criterio, el permiso no la bloquea. No la uses porque el harness te deje.

---

## Paso 5 — ¿El test sirve? (criterio de salida)

Un test nuevo no está terminado por estar verde. Los tres modos de estar verde sin probar nada:

1. **Verde también con el código roto.** Sabotea la línea que el test debería proteger y confirma que
   se pone rojo. Si sigue verde, el test no afirma lo que crees.
2. **`transaction.on_commit` que no se ejecuta.** Dentro de `TestCase` / `django_db` la transacción
   se revierte, el callback **nunca corre** y los `assert` que van detrás tampoco. Se resuelve con
   `captureOnCommitCallbacks(execute=True)` (`backend-tests.md` §caso especial).
3. **`findBy*` sin `await`** — verde y sin comprobar nada. Lo caza
   `testing-library/await-async-queries`, no el checker.

Y la regla dura, prestada de `rules/refactor-progresivo.md` §A3 G1: **si para que pase el test hubo que
tocar el test, no era un test — era el código el que había que mirar.** Modificar la aserción para
que deje de molestar es la forma más barata de perder la suite entera.

## Qué se entrega (formato de salida)

Al cerrar, una línea por campo — no prosa:

```
modulo:      apps/expedientes
nivel:       servicio (2) · api (1)
ficheros:    apps/expedientes/tests/test_expedientes.py (nuevo)
comando:     pytest apps/expedientes/ -v --maxfail=3
salida:      3 passed in 1.84s          ← pegada, no resumida
sabotaje:    ok — al romper `abrir_expediente` el test 2 se pone rojo
sin_cubrir:  el reintento de Celery (necesita el broker; queda fuera y se dice)
```

`sin_cubrir` no es opcional: lo que no se probó se declara. Un informe que solo cuenta lo verde
convierte "no lo miré" en "está bien".

---

## Anti-patterns

- ❌ Escribir el test **antes** de saber qué debe demostrar → sale un `test('renders')` que no dice
  nada cuando falla.
- ❌ Copiar aquí (o a un agente, o a un `CLAUDE.md`) los límites de RAM en vez de llamar al hook →
  es literalmente cómo el agente archivado acabó enseñando un conteo falso.
- ❌ `pytest` a secas, `-n auto` o `--cov` "solo esta vez".
- ❌ Un `tests.py` vacío del `startapp`: hace que el contador diga "41 apps con tests" con 2 tests
  reales, y el sitio menos cubierto del proyecto es el que parece cubierto. Se borra.
- ❌ Un fichero con tests que el descubridor no encuentra (`expedientes_tests.py`) → no fallan nunca.
- ❌ Subir un test al nivel E2E porque "así se prueba de verdad" → lento, frágil y cuenta doble en RAM.
- ❌ `data-testid` en un test de integración → te saltas la única comprobación de accesibilidad gratis.
- ❌ Dar por bueno un test verde sin haberlo visto fallar ni una vez.
- ❌ Tocar el test para que pase.
- ❌ Marcar `xfail` un fallo que está **dentro de tu propio claim** en vez de arreglarlo.
- ❌ `xfail` sin `strict=True` → al arreglarse queda en XPASS y el marcador vive para siempre.
- ❌ Prometer un porcentaje de cobertura: aquí no se puede medir (§Paso 4).

## Ejemplos

**Usuario:** *"apps/facturacion no tiene ni un test, móntale la suite."*
→ Paso 0 (¿arranca la suite? `be-test-db-alias-sin-engine`) → Paso 1: los servicios primero y **el
filtrado por dueño** del endpoint → Paso 2: `apps/facturacion/tests/test_facturacion.py` +
`conftest.py` con las fixtures → Paso 3: `backend-tests.md` (factories con `Sequence`) → Paso 4:
`check-ram.sh` y `pytest apps/facturacion/ -v --maxfail=3` → Paso 5: sabotaje + bloque de salida.

**Usuario:** *"arregla este bug: al cancelar un pedido no se libera el stock."*
→ Primero el test que **reproduce el bug y está rojo** (nivel servicio, es una regla de negocio),
después el fix, y el mismo test en verde es la evidencia. Sin el rojo previo no sabes si el test
prueba el fix o cualquier otra cosa.

**Usuario:** *"revisa estos tests que ha generado la IA."*
→ **No es esta skill.** Es `code-review-gate` §rúbrica de 7 puntos (nombres · AAA · parametrización ·
mensajes · casos límite · mock de BD · control negativo).

## Related

- `patterns/stack/backend-tests.md` — el patrón de backend, con `pattern_check_backend.py`
- `patterns/stack/tests.md` — el patrón de frontend, con `pattern_check_frontend.py --only tests`
- `patterns/stack/agente-tests-grafo.md` — el grafo de un bot LangGraph: enrutado, nodo, contrato de tools y un tramo, con modelo falso (ejemplos en `templates/bot-evals/test_graph_example.py`)
- **`rules/ram-pytest.md`** — el límite duro · `hooks/check-ram.sh` es el enforcement real
- `rules/verification.md` §Estabilidad E2E — todo lo de E2E · `rules/qa-loop.md` — el gate visual de una wave con UI
- skill `code-review-gate` — **juzga** tests (esta los escribe) · §Combinatoria + `references/pairwise.md` — los datos
  (antes skill `pairwise-test-data`)
- **`rules/parallelization.md`** §file claims — el `xfail(strict=True)` como traspaso cuando el fallo
  está en territorio de otro frente
- skill `verification-loops` — el checklist pre-DONE de la tarea entera, del que esta skill es un paso
- `_archive/2026-08-22/README.md` §`especialista-testing.md` — de dónde viene y por qué no es un agente
