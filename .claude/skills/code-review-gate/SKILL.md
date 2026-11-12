---
name: "code-review-gate"
description: >-
  Usar antes de cada merge a develop o al juzgar tests ajenos: 'review del diff', 'pre-merge gate',
  'READY_MERGE', 'revisa estos tests', '¿la suite cazaría un fallo?'; y para auditar el repo
  entero: 'audita el repo', '/audit'. Seguridad, anti-mock, dependencias alucinadas y rúbrica de 7
  puntos. NO usar para: escribir tests (escribir-tests) ni el review del diff en paralelo
  (/review-branch).
user-invocable: false
metadata:
  version: 1.4.0
  author: Tech Lead Template
  category: workflow
  updated: 2026-10-27
  source: "adapted from boris-codex-review"
  tech-stack: "ajusta al stack del proyecto"
---

# Code Review Gate — Pre-merge

## Principio

Antes de cualquier merge a `develop`, el diff debe pasar por un review estructurado. El objetivo es atrapar issues de seguridad, N+1 queries, tipos laxos (any/untyped), y datos mock que se cuelan a producción.

## Cuándo activar el gate

- Antes de reportar `READY_MERGE` en cualquier SpecKit session
- Antes de cualquier PR que toque módulos de datos sensibles
- Siempre que el diff tenga >200 líneas cambiadas
- Siempre que el diff **añada o modifique tests** que no escribiste tú (generados por IA o ajenos)
  → aplica la rúbrica de 7 puntos
- Cuando se pide **auditar el repo entero** (seguridad + calidad, no un diff) → §/audit, abajo

Disparadores: 'review del diff', 'pre-merge gate', 'revisa estos tests', 'evalúa los tests que
generó la IA', 'control negativo', '¿la suite cazaría un fallo?', 'pruebas de mutación',
'READY_MERGE'; y la auditoría de seguridad y calidad del repo ENTERO (antes el comando /audit):
'audita el repo', 'auditoría de seguridad y calidad del código', '/audit'. Qué revisa: seguridad
backend (sin SQL raw, auth obligatoria), seguridad frontend (sin dangerouslySetInnerHTML, sin env
vars expuestas), grep anti-mock, dependencias alucinadas, la rúbrica de 7 puntos para REVISAR tests
generados por IA (nombres/AAA/parametrización/mensajes/casos límite/mock de BD/control negativo,
medible con mutación opcional mutmut/Stryker por módulo), los gotchas medidos en proyectos (Django
|default:True, migraciones copiadas, zonas horarias, import local, docker exec sin -i) y, opcional,
/codex:adversarial-review para auth y migraciones. Se adapta al stack del proyecto · NO usar para:
escribir tests (eso es escribir-tests; esto los JUZGA) ni el mismo review del diff en paralelo
(/review-branch).

## Cómo ejecutar el review

```bash
# Ver el diff actual
git diff --stat
git diff main...HEAD  # vs main

# Diff con auth, permisos, CORS o rate limiting: checklist de references/django-drf-security.md
```

**Revisor IA: solo local, sin CI (EQ-D19, decidido el 18-10 con la recomendación; anotado en la 3.14).**
La revisión con IA es la de esta máquina: Roberto (`roberto-clean-code`) + `/code-review` +
`/security-review`, sobre el diff, antes del merge. **Ningún proyecto lleva revisor IA en CI**, y
ningún SaaS de revisión (CodeRabbit, Greptile, Qodo, Sourcery): sacan el código fuera, y aquí hay
datos de salud y push solo con aprobación. Si un día se quiere CI, la opción es un revisor con clave
propia en el CI propio (`anthropics/claude-code-action` o PR-Agent) y se decide proyecto a proyecto;
`claude-code-security-review` no está endurecido contra prompt injection: solo PRs de confianza.

## Checklist de review — Backend (ej: Django/FastAPI/Node)

### Seguridad
- [ ] Sin SQL raw no parametrizado (`cursor.execute(f"...")` es BLOQUEANTE)
- [ ] Sin credenciales en código (`api_key = "sk-..."` es BLOQUEANTE)
- [ ] Auth/permission classes en endpoints (`permission_classes = [IsAuthenticated]` o equivalente del framework)
- [ ] Validación en serializers/schemas para inputs de usuario
- [ ] No se exponen IDs internos en URLs públicas sin auth

### Performance
- [ ] ForeignKey/joins accedidos en loop → ¿hay `select_related` o equivalente?
- [ ] Relaciones M2M accedidas en loop → ¿hay `prefetch_related` o equivalente?
- [ ] Listados sin filtro ni paginación sobre tablas grandes → revisar

### Calidad
- [ ] Endpoints/actions tienen docstring o están autodocumentados
- [ ] Serializers tienen `read_only_fields` donde corresponde
- [ ] Tests unitarios para lógica de negocio nueva

## Checklist de review — Frontend (ej: React/Vue/Svelte + TS)

### Seguridad
- [ ] Sin `dangerouslySetInnerHTML` (o equivalente) sin sanitización
- [ ] Variables de entorno sensibles no expuestas en bundle (no `VITE_SECRET_*`, `NEXT_PUBLIC_SECRET_*`, etc.)
- [ ] Tokens no almacenados en `localStorage` sin cifrado

### Calidad TypeScript
- [ ] Sin `as any` sin comentario de justificación (`// any-ok: razón`)
- [ ] Interfaces definidas para props de componentes nuevos
- [ ] Funciones asíncronas manejan errores (try/catch o `.catch()`)

### Anti-mock
```bash
# Ajusta paths al stack del proyecto
grep -rn "mockData\|fakeData\|HARDCODED\|TODO.*real\|placeholder_\|test_user\|demo_" \
  frontend/src --include="*.tsx" --include="*.ts" | grep -v "__tests__\|\.test\."
```

### Dependencias alucinadas (slopsquatting) — SEC-1, BLOQUEANTE
El agente puede inventar un paquete que no existe; alguien registra ese nombre en npm/PyPI y
tienes supply-chain. **Todo paquete AÑADIDO en el diff se verifica que existe de verdad**:

```bash
# Paquetes nuevos en el diff (ajusta al gestor del proyecto)
git diff develop... -- package.json | grep '^+.*"' | grep -v version   # npm
git diff develop... -- requirements*.txt pyproject.toml | grep '^+'    # python

# Verificación (exit != 0 → NO existe → BLOQUEANTE):
npm view <paquete> version          # npm
pip index versions <paquete>        # python (o: pip download <paquete> --no-deps -d /tmp --quiet)
```

Además del "¿existe?": nombre sospechosamente parecido a uno popular (typosquat), descargas
ínfimas o creado hace días → WARNING, verificar el repo fuente antes de mergear.

### Datos personales en logs, errores, trazas y cassettes — SE-36, BLOQUEANTE en apps de salud
Redactar al mostrar no protege el dato guardado: lo que entra al log queda en claro en la base de
logs y en sus copias (el caso EvoPreven: `str(instance)` con nombres y cuerpos POST con campos
clínicos). **Se corre sobre los ficheros del diff:**

```bash
python3 .claude/scripts/check_pii_logs.py $(git diff --name-only --diff-filter=d develop... -- '*.py' '*.log' '*.jsonl' '*.yaml' '*.yml' '*.json')
# exit 1 = hallazgos con file:line · exit 2 = no había nada que medir (no es «limpio»)
```

Caza: logger que vuelca un modelo entero o el cuerpo de la petición; ese cuerpo guardado en un
modelo de log; Sentry/GlitchTip sin `before_send` ni `include_local_variables=False`; Langfuse sin
máscara; cassettes de vcrpy con PII o con la cabecera `authorization`; ficheros `.log` con un dato
personal. **Si el proyecto tiene `cumplimiento-salud.yaml`** (la marca de «datos de salud» que deja
la skill `cumplimiento-salud`), el script lo detecta y **todo logger nuevo que serialice modelos o
cuerpos de petición es BLOQUEANTE**; fuera de salud, WARNING. Antes de bloquear, el Intent: un email
de `example.test` en un fixture no es un paciente (el script ya ignora esos dominios).

## Rúbrica de 7 puntos — evaluar tests generados por IA (QA-7)

Aplica a **todo test que entre en el diff sin haberlo escrito tú**: generado por un agente, por un
compañero o copiado de otro módulo. Escribir un test y **revisar** un test son trabajos distintos;
esto es el segundo. Un test que pasa no es un test que sirve.

| # | Criterio | Qué mirar | Falla si… |
|---|---|---|---|
| 1 | **Nombre descriptivo** | el nombre dice **qué caso** cubre y **qué se espera** | `test_create`, `test_1`, `test_works` |
| 2 | **Patrón AAA** | Arrange (montar) · Act (una acción) · Assert (comprobar), en ese orden y visibles | asserts intercalados con setup; dos acciones en un test |
| 3 | **Parametrización** | casos que solo cambian en los datos → `pytest.mark.parametrize` / `test.each` | 6 tests copiados que difieren en un literal |
| 4 | **Mensajes en las aserciones** | al fallar en CI se entiende **qué** falló sin abrir el código | `assert result` a secas |
| 5 | **Casos límite** | vacío, cero, negativo, máximo, máximo+1, nulo, tipo inesperado, duplicado | solo camino feliz |
| 6 | **Mock de la BD en unitarios** | el unitario no toca la BD real (ver razonamiento abajo) | `Model.objects.create(...)` en un test "unitario" |
| 7 | **Control negativo** (solo si protege un mecanismo) | existe un caso que **rompe la protección a propósito** y comprueba que el fallo aparece | el mecanismo se podría borrar entero y ningún test se pondría rojo |

```python
# ✅ 1+2+3+4 — nombre, AAA, parametrización y mensaje
@pytest.mark.parametrize("cantidad,esperado", [(0, False), (1, True), (99, True), (100, False)])
def test_cantidad_fuera_de_rango_no_se_acepta(cantidad, esperado):
    pedido = Pedido(stock=99)                                  # Arrange
    valido = pedido.acepta(cantidad)                            # Act
    assert valido is esperado, f"cantidad={cantidad} debería ser {esperado} con stock=99"  # Assert
```

### El razonamiento del punto 6 (el que casi nadie explica)

Mockear la BD en un unitario no es purismo, es **idempotencia**: sin mock no puedes verificar el ID
asignado (cambia en cada ejecución) y, en cuanto haya una restricción de integridad —un `unique` de
email, por ejemplo—, **el test pasa la primera vez y falla la segunda** por datos repetidos. Un test
que solo pasa con la BD recién creada es un test que va a fallar en CI un martes por la mañana.

Corolario: si el test **necesita** la BD de verdad, no es unitario — es de integración, y entonces
se rige por `rules/verification.md` §E2E-1 (estado determinista, datos únicos por run, limpieza).

### El punto 7 — el control negativo (solo para tests que protegen un MECANISMO)

Un test que solo puede pasar no demuestra nada. Es el fallo silencioso más común de una suite:
cientos de tests verdes sobre un mecanismo que se podría borrar entero sin que ninguno se pusiera
rojo. Cuando eso ocurre, **verde deja de significar "funciona" y pasa a significar "se ejecutó"**.

La forma del control negativo es siempre la misma: **desactivo o rompo la protección a propósito →
compruebo que el fallo aparece**. Tres ejemplos reales, cada uno de una variante distinta:

1. **`test_con_clave_no_determinista_se_duplica`** — el mecanismo es una clave de idempotencia
   determinista que evita duplicar un efecto externo al reanudar. El test construye a propósito una
   clave **no** determinista y comprueba que **entonces sí** se duplica: demuestra que el gate está
   gateando algo.
2. **`test_una_referencia_que_no_existe_no_cortocircuita`** — la capa 1 de un buscador cortocircuita
   cuando reconoce una referencia exacta. El test comprueba el caso contrario: con una referencia
   inventada **no** cortocircuita. Sin él, un bug que cortocircuitara *siempre* pasaría todos los
   tests del camino feliz.
3. **`test_el_nodo_se_reejecuta_de_verdad`** — antes de probar la mitigación, prueba **la premisa**:
   que el nodo efectivamente se re-ejecuta al reanudar. Si el framework cambiara ese comportamiento,
   este test avisa de que la mitigación ya no protege de nada y sobra.

El tercero es el más sutil y el que más se olvida: **una mitigación cuya premisa ya no se cumple es
código muerto que todos creen vivo** — sigue en verde y no está protegiendo de nada.

**Qué NO es un control negativo**, para que no se convierta en trámite: no es "probar el camino de
error". Que un payload inválido devuelva 400 es el **camino feliz del validador**. El control
negativo apunta al **mecanismo de protección**, y su prueba consiste en romperlo, no en ejercitar
otra rama del código.

**Cuándo se exige** — el acotamiento es deliberado:

| Sí lo lleva | No lo lleva |
|---|---|
| Idempotencia, reintentos, cortocircuitos | Transformaciones de datos (formateo, parseo, cálculo) |
| Aislamiento entre inquilinos, permisos, auth | Serialización y contratos de forma |
| Bloqueos, exclusión mutua, deduplicación | Casos límite de entrada (eso ya es el punto 5) |

Exigirlo en los seis puntos anteriores convertiría la rúbrica en ceremonia, y una rúbrica que se
firma sin hacer deja de valer. Se pide **solo** a los tests que protegen un mecanismo; en el resto
el punto sale `n/a` y así se anota.

#### Medirlo en vez de mirarlo: pruebas de mutación (opcional, bajo demanda — MO-50)

El punto 7 se contesta a ojo. Cuando haya duda sobre si una suite verde **cazaría un fallo real**,
hay herramienta: un probador de mutación cambia el código a propósito (un `*` por `/`, un `if` por su
contrario, un `2` por `3`) y cuenta cuántos cambios hacen que algún test se ponga rojo. El que sobrevive
es un fallo que la suite no ve.

| Stack | Herramienta (versión y licencia del 2026-10-21, PyPI y npm) | Por módulo, nunca la suite entera |
|---|---|---|
| Python | **mutmut 3.8.0** · BSD-3-Clause · Python ≥3.10 | `pyproject.toml`: `[tool.mutmut]` `source_paths = ["apps/billing/"]`, `pytest_add_cli_args_test_selection = ["apps/billing/tests/"]` y, en Django, `also_copy = ["config/", "pytest.ini"]` (todo lo que pytest necesite fuera de `source_paths`: el paquete de settings, el `pytest.ini` o `conftest.py` de la raíz) → `mutmut run --max-children 2` → `mutmut results` (los supervivientes) → `mutmut show <mutante>` (el diff) |
| JS/TS | **Stryker (`@stryker-mutator/core`) 10.0.0** · Apache-2.0 · Node ≥22 | `npx stryker run --mutate "src/lib/precio.ts" --concurrency 2` |

**Cuándo sí:** a petición o en un hito (antes de dar por bueno un módulo crítico, al heredar una suite
que nadie revisó), sobre el módulo que protege el mecanismo. **Cuándo no: en cada diff.** Son lentas y
cada mutante corre los tests otra vez.

⚠️ **RAM (rules/ram-pytest.md):** `bash .claude/hooks/check-ram.sh` en verde antes, y el número de
procesos a mano: **mutmut lanza por defecto tantos procesos como CPUs** (`os.cpu_count()`, leído en su
código, 3.8.0) y **Stryker usa por defecto CPUs − 1** (su doc de configuración, `concurrency`). En esta
máquina, 8 y 7 pytest o vitest a la vez: `--max-children 2` / `--concurrency 2`, siempre.

**Probado aquí** (2026-10-21, venv temporal, `_archive/2026-10-20/medicion-2.17/`): una función de 3
líneas con un test que solo comprueba que devuelve un número → **4 de 7 mutantes cazados**; los 3 que
sobreviven son `precio / 0.9` y `precio * 1.9` en vez de `* 0.9`, y el redondeo a 3 decimales en vez
de 2. Con los tres casos que fijan el resultado (descuento, rebajado, céntimos) → **7 de 7**. Y en un
proyecto Django mínimo (pytest-django), sin `also_copy` mutmut no arranca (`ImportError: No module
named 'config'`: a `mutants/` copia `source_paths`, `tests/`, `test/`, `setup.cfg`, `pyproject.toml`,
los lockfiles y `test*.py` de la raíz, pero no el paquete de settings ni el `pytest.ini`); con él, 7
de 7. Ojo, medido: **mutmut
reutiliza los resultados de `mutants/`** y, tras cambiar los tests, volvió a dar los mismos 3
supervivientes sin correr nada («0.00 mutations/second»). Antes de volver a medir, borra `mutants/`
(y añádelo al `.gitignore` del proyecto). Stryker no se ha corrido aquí: sus flags salen de su doc.

El número no es una nota: un mutante que sobrevive se lee como **«este cambio no lo ve ningún
test»**, y la decisión de escribir el test que lo vería es del revisor. Un 100 % no prueba la regla de
negocio (§El punto ciego, abajo): prueba que lo que hay escrito no se puede cambiar sin que se note.

### El punto ciego: la regla de negocio, no el formato

**Lo que la IA hace bien es el formato; lo que se le escapa es el dominio.** Genera AAA impecable,
nombres correctos y cobertura del camino feliz — y a la vez no tiene forma de saber que *no puede
haber dos historiales clínicos para el mismo paciente*, que *un pedido cancelado no se puede
reembolsar dos veces*, o que *el descuento no se aplica a los productos ya rebajados*. Esas reglas
no están en la signatura de la función.

Por eso el review de un test generado invierte el reparto de esfuerzo:

- **Los puntos 1–4 (formato)**: repaso rápido, casi siempre están bien.
- **Los puntos 5–7 y sobre todo el dominio**: aquí va el tiempo. La pregunta de revisión no es
  *"¿está bien escrito este test?"* sino **"¿qué invariante de negocio de este módulo NO está
  cubierta por ningún test?"**.
- Si el diff añade tests pero **ninguno** codifica una regla de negocio del módulo, el review
  devuelve **WARNING**: la cobertura sube y la confianza no.

Complementa, sin solaparse: `marco-qa-breaker` ataca la lógica de negocio ya implementada
(destructivo, estados ilegales); `escribir-tests` §Combinatoria genera la combinatoria de entradas; esta
rúbrica juzga los tests que ya están en el diff.

## Gotchas medidos en proyectos — búscalos en el diff (MO-62)

Cada uno causó un incidente real en un proyecto de la casa, y salvo el del `import` local (ruff
F823) ninguno lo caza un linter. Si el diff toca lo de la primera columna, se mira lo de la segunda.

| Si el diff toca… | Qué buscar | Por qué (el caso) | Cómo se prueba |
|---|---|---|---|
| Plantillas de Django con un booleano | `\|default:True` (o `default:` con cualquier verdadero) dentro de un `{% if %}` | `default` se dispara con **cualquier** falso, no solo con ausencia: `{{ False\|default:True }}` es `True`. En EvoPreven, `{% if child.show\|default:True %}` hacía que `'show': False` no ocultara nada: 12 entradas protegidas por permiso visibles para cualquiera, «Logs de Acceso» incluida (memoria `django-default-filter-oculta-permisos`, 2026-09-13) | La forma que vale en todas partes es `{% if child.show != False %}`. El test de abajo |
| Migraciones de Django traídas de otra rama, zip o clon | Ficheros `*/migrations/0*.py` nuevos que **no** generó `makemigrations` en esta rama | La numeración de otra rama choca con la de esta (`core/0009` de una rama de cliente frente a `0009…0019` de develop → «multiple leaf nodes»). Se portan los **modelos** y se genera la migración aquí (memoria `migraciones-makemigrations-no-copiar`, EvoPreven, 2026-09-28) | `git apply --exclude='*/migrations/*'` al portar; después `makemigrations <app> --name <nombre>`, revisar que solo trae lo esperado, y `makemigrations --check --dry-run` |
| Fechas y horas | `\.strftime\(` sobre un campo de modelo; horas *naive* de una API externa guardadas tal cual | **Guardar y enseñar son dos bugs distintos.** En musa (#9) una API devolvía hora local sin zona y se guardaba como UTC: todas las citas +2 h; al arreglarlo salió el segundo, `strftime` directo sobre el valor con zona imprimiendo UTC en crudo (−2 h), en el recordatorio de WhatsApp a una clienta real | Un helper explícito para lo que se le enseña a una persona (`localtime()` antes de formatear) y tests en **verano e invierno**: el desfase no es constante |
| Python: un `import` añadido **dentro** de una función | Que ese nombre ya se use más arriba en la misma función | El import lo convierte en local **en toda la función**: el uso anterior lanza `UnboundLocalError`. En musa (#35) estaba dentro de un `try/except` defensivo, se lo tragó y la agenda dejó de consultarse en silencio, con once tests en rojo señalando otra cosa. Reproducido aquí en 6 líneas: `tragado: UnboundLocalError` | `ruff check --select F823` lo caza de forma determinista (ruff 0.17.1: `F823 Local variable … referenced before assignment`, en la línea del uso). Además: no importar un nombre que ya existe en el módulo, o con alias; el código nuevo dentro de un `except Exception` se prueba **fuera** primero |
| Scripts con `docker exec` | `docker exec` con heredoc o tubería **sin `-i`** | Sin `-i` Docker no reenvía la entrada: el heredoc se descarta, `python -` no lee nada y sale con **0**. En musa (#17) un paso de datos «terminó bien» sin escribir una fila, dos veces en la misma sesión | `docker exec -i`; y el paso imprime cuántas filas escribió y el script comprueba ese número |

El test de ejemplo para la primera fila. Prueba la **tabla de verdad entera**, no solo el caso que
motivó el arreglo, sin proyecto ni base de datos:

```python
import pytest
from django.template import Context, Template

MENU = "{% if child.show != False %}visible{% else %}oculta{% endif %}"

@pytest.mark.parametrize("child,esperado", [
    ({"show": False}, "oculta"),    # el caso del incidente
    ({"show": True}, "visible"),
    ({"show": None}, "visible"),
    ({}, "visible"),                # la clave ausente: la entrada que no declara permiso se ve
])
def test_show_false_oculta_y_lo_demas_se_ve(child, esperado):
    assert Template(MENU).render(Context({"child": child})) == esperado, f"{child=}"
```

Corrido de verdad con pytest 8.4.2 y Django 5.2.7 (2026-10-21; en un proyecto con pytest-django los
settings ya están, fuera hace falta configurarlos como hace `menu_pytest.py`): con `!= False`,
**4 passed**; con `|default:True` en `MENU`, **1 failed en `show: False`**
(`_archive/2026-10-20/medicion-2.17/menu_pytest.py` y `default_true.pytest.txt`; la tabla de las cuatro
formas: `probar_default_true.py`). Y un matiz que la
memoria de EvoPreven daba por general: **dentro de `{% if %}`** una clave ausente resuelve a `None`, así
que `|default_if_none:True` también pasa; **fuera** (`{% with %}`, `{{ }}`) resuelve a `''` y oculta la
entrada. `!= False` vale en los dos sitios; por eso es la forma que se pide.

## Comentarios con cita en el diff (MO-59) — eje «comentarios»

`rules/code-style.md` §Comentarios: la cita `<fichero>:<línea>` y la historia van en la respuesta y
en el informe, no en el código (EVO-2876 dejó 27 comentarios con cita y 66 con historia). Se busca
en las líneas que **añade** el diff:

```bash
CITA_RE='^\+(([^+].*)?(#|//|/\*|<!--|--|""")|[[:space:]]*\*[[:space:]]).*[A-Za-z0-9_./-]+\.(py|tsx?|jsx?|vue|sql|sh|ya?ml|html|css|scss|md):[0-9]+'
git diff develop... -U0 | grep -nE "$CITA_RE"     # cada línea que sale es un hallazgo menor
```

Cubre `#`, `//`, `/* */`, `<!-- -->`, `--` de SQL, docstrings `"""` y líneas de JSDoc. Cada
hallazgo: la cita sale del comentario y va a la respuesta o al informe; si el comentario se queda
sin nada que decir, se borra. Un `http://host:8000` no casa (pide extensión de fichero), pero **una
URL que acaba en fichero y puerto** (`"https://cdn.x.com/lib/app.js:1"`) sí: el `//` de la URL cuenta
como comentario. Es un falso positivo conocido; se descarta mirándolo. En un `.md` del harness la
cita es legítima: este eje se pasa sobre código de producto.

## Seguridad Django/DRF del diff (lo que era `especialista-seguridad`)

El agente `especialista-seguridad` se retiró en la 3.01 (EQ-8: 1 uso, su checklist duplicaba
`rules/security.md` y esta skill). Su checklist y sus patrones (JWT, niveles de permiso, filtrar por
usuario, campos sensibles, rate limiting, CORS) están en `references/django-drf-security.md`. Se pasa
sobre el diff cuando toca auth, permisos, CORS o throttling, con esta salida:

```
Focus: OWASP top 10, permission/auth gates, tipos laxos, datos hardcodeados
Output: PASS / WARNINGS (considera arreglar) / BLOCKERS (arregla antes de merge)
```

Atacar la app con PoC sigue siendo de `sofia-pentester`; el RGPD, de `priya-privacy-auditor`.

## /audit — Auditoría de seguridad y calidad del código (el repo ENTERO, no el diff)

> **Antes era el comando `/audit`**, retirado el 2026-10-19 (LI-11): era la cuarta puerta a «revisar
> seguridad y calidad» y tenía 0 usos. El contenido es el mismo; lo que cambia es la puerta. Esta
> sección es para cuando se pide **auditar el repo entero** (no un diff): el review de un diff sigue
> siendo el gate de arriba, y en paralelo y con verificación adversarial, el workflow `/review-branch`.

Ejecuta una auditoría completa del proyecto. Los ejemplos usan rutas típicas (`backend/`, `frontend/src/`) — **ajusta a tu stack** (p. ej. `apps/`, `src/`, `services/`, etc.) antes de correr los comandos.

### Seguridad

1. Buscar credenciales hardcodeadas:
   ```bash
   # Ajusta rutas y extensiones a tu stack
   grep -rn "sk-ant-\|sk-[a-zA-Z0-9]\{20,\}\|password\s*=\s*['\"]\|api[_-]\?key\s*=\s*['\"]" backend/ frontend/src/ \
     --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
     | grep -v "test" | grep -v "node_modules"
   ```

2. Buscar SQL raw sin parametrizar (Django/SQLAlchemy/etc.):
   ```bash
   # Ajusta según ORM: .raw(/ .extra( para Django; session.execute(text( para SQLAlchemy
   grep -rn "\.raw(\|\.extra(\|session\.execute(text(" backend/ --include="*.py"
   ```

3. Buscar .env u otros secretos expuestos en git:
   ```bash
   git ls-files | grep -E "\.env($|\.)|credentials|secrets|\.pem$|\.key$|service-account.*\.json"
   ```

4. Verificar CORS settings (ajusta al path de settings de tu framework):
   ```bash
   grep -rn "CORS\|cors_origins\|allow_origins" . --include="*.py" --include="*.ts" --include="*.js" \
     | grep -v node_modules | grep -v ".venv"
   ```

5. Verificar CSRF / auth decorators relajados (Django/FastAPI/Flask):
   ```bash
   grep -rn "csrf_exempt\|@AllowAny\|permission_classes\s*=\s*\[\s*AllowAny" . --include="*.py"
   ```

### Calidad de Código

6. Buscar mock / demo data en producción (frontend):
   ```bash
   # Ajusta a tu path y extensiones
   grep -rn "mockData\|fakeData\|hardcoded\|TODO.*real\|demo_data\|DEMO_\|// fake\|// mock" frontend/src/ \
     --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js"
   ```

7. Buscar console.log / print() residuales:
   ```bash
   # Frontend
   grep -rn "console\.log\|console\.error\|console\.warn" frontend/src/ \
     --include="*.tsx" --include="*.ts" | grep -v "node_modules" | head -20
   # Backend Python (opcional)
   grep -rn "print(" backend/ --include="*.py" | grep -v "test" | head -20
   ```

8. Buscar TODO/FIXME pendientes:
   ```bash
   grep -rn "TODO\|FIXME\|HACK\|XXX" . \
     --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
     | grep -v node_modules | grep -v ".venv" | head -30
   ```

### Reporte

Genera un reporte con:
- 🔴 CRITICAL: Credenciales expuestas, SQL injection, `.env` en git, CORS `*` en producción
- 🟡 WARNING: Mock data en UI, `console.log` residuales, CSRF/auth exempt sin justificar
- 🟢 INFO: TODOs, refactors sugeridos, mejoras menores
- Puntuación: X/10 (10 = limpio)

Documenta hallazgos en `PROGRESS.json` bajo `notes[]` o en `.claude/PROGRESS.log`.

## Severity levels

- **BLOQUEANTE** — No mergear hasta arreglar: credenciales, SQL injection, auth missing
- **WARNING** — Arreglar si es posible: N+1 query, missing error handling, `any` sin justificar
- **SUGGESTION** — Optional: mejoras de naming, refactor cosmético

## Salida HTML (opcional)

Para PRs grandes o cuando el reviewer no conoce el área, genera un **PR writeup HTML Tier-2** con
la skill `html-suelto` (`/html-suelto review`): diff anotado por severidad + jump links +
motivación. Comunica mejor que el diff plano. Ver `.claude/rules/html-output.md`.

## Anti-patterns

- Reportar READY_MERGE sin review del diff
- Mergear con BLOCKERS "porque es urgente"
- Review solo del backend, ignorar el frontend (o viceversa)
- No verificar el comportamiento real después del review (tests)
- Dar por bueno un test generado por IA porque está bien formateado y pasa en verde
- Aceptar `Model.objects.create(...)` en un test etiquetado como unitario (rompe idempotencia)
- Contar cobertura como calidad: 90% de líneas sin una sola regla de negocio cubierta no es señal
- Dar por probado un mecanismo cuyo test **nunca se ha visto en rojo** — solo demuestra que se ejecuta
- Colar como control negativo el camino de error del validador (un 400 ante un payload inválido)
- Exigir control negativo en un test de transformación de datos → ceremonia, y entonces se firma sin hacer

## Related

- `rules/verification.md` §Estabilidad E2E — si el test necesita BD real, deja de ser unitario y se rige por esa rule
- `rules/verdict-contract.md` — formato del hallazgo (Impact/Intent, doble evidencia) al reportar
- `escribir-tests` §Combinatoria (antes `pairwise-test-data`) — generar la combinatoria de entradas que la rúbrica exige en el punto 5
- `marco-qa-breaker` (agente) — ataque destructivo a la lógica de negocio ya implementada
- `escribir-tests` (skill) — ESCRIBE los tests; esta skill los JUZGA
- `roberto-clean-code` (agente) — ¿hacía falta escribirlo y está en su capa? (reutilización, capa,
  diff mínimo). Esta skill no lo repite; él cita esta para seguridad, tests y N+1
- `pilar-impacto-produccion` (agente) — ¿algún cliente verá algo que nadie pidió? (migraciones,
  consumidores, foto antes/después). Esta skill no mide comportamiento; en un issue con plan, el
  cierre lo exige `scripts/gate_impacto.py` (los apartados de Pilar y Roberto, frescos al diff)
- **Sin `REVIEW.md`**: el `/code-review` local no lo lee (solo el Code Review gestionado de GitHub,
  Team/Enterprise). Las reglas de revisión de un proyecto van a la ficha de Roberto (§Lo de este
  proyecto) o a una sección breve de su `CLAUDE.md`
- `rules/refactor-progresivo.md` §A1 — el mismo control negativo a escala de suite: romper una línea a
  propósito para comprobar que la suite se entera, antes de fiarse de ella
