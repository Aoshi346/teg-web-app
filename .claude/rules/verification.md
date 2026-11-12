---
paths:
  - "**/migrations/*.py"
  - "**/models.py"
  - "**/models/*.py"
  - ".claude/scripts/check_*.py"
  - ".claude/scripts/gate_*.py"
  - ".claude/scripts/verificar_*.py"
  - ".claude/smoke/**"
  - "**/e2e/**"
  - "**/*.spec.ts"
  - "**/*.spec.tsx"
  - "**/*.spec.js"
  - "**/*.e2e.*"
  - "**/playwright.config.*"
  - "**/cypress/**"
  - "vrt.json"
  - "**/CHANGELOG.md"
---
# Reglas de Verificación — del smoke al ciclo de producción

> **Cuándo aplicar:** antes de reportar DONE en cualquier tarea, y al diseñar el gate de
> verificación de una sesión larga o autónoma (`/loop`, waves, trabajo desatendido). También: al
> comprobar que "lo básico vive" tras un deploy o al llamar por primera vez un endpoint recién
> escrito (§Smoke testing); al escribir, arreglar o ejecutar un test **end-to-end** (§Estabilidad
> E2E); en releases, en toda feature importante o cuando el prompt diga "ciclo de producción"
> (§Ciclo de producción); y **antes de darle una cifra al Usuario** («mejoró», «15/15», «arreglado»):
> §Una cifra sin sus condiciones no es evidencia.
>
> **NO aplicar:** como sustituto de los gates específicos — wave con UI → `qa-loop.md`; formato del
> veredicto → `verdict-contract.md`.
>
> **Relacionado:** `verdict-contract.md`, `qa-loop.md`, `ram-pytest.md` (el browser cuenta doble),
> `api-http-contract.md`, skills `verification-loops`, `visual-regression`, `code-review-gate`,
> `prompt-contracts`.
>
> **Fusionada el 2026-10-20 (LI-27, sub-ola 1.06).** Aquí viven ahora las antiguas
> `smoke-testing.md` (§Smoke testing), `e2e-stability.md` (§Estabilidad E2E) y `production-cycle.md`
> (§Ciclo de producción; su aviso se retiró el 2026-10-22, cuando `CLAUDE.md` dejó de citarla). El
> porqué y lo que no se trasladó: `_archive/2026-10-19/README.md` §Sub-ola 1.06.

## Principio
No reportar DONE sin verificar que el cambio funciona. La verificación es parte del trabajo, no opcional.

**Corolario operativo (doc oficial de best-practices): "dale a Claude una forma de verificar su
trabajo".** Un agente sin bucle de verificación no sabe si acertó; con uno, itera hasta acertar.
Cómo montar ese bucle según cuánta autonomía tenga la sesión → la escalera de 4 niveles de abajo.

## Antes de reportar cualquier tarea como completada

### 1. Verificación de código
```bash
# Backend
python manage.py check  # sin warnings

# Frontend
npm run build           # sin errores TypeScript
```

#### `check` en verde NO significa que el esquema aplique (medido 2026-08-25)

En un proyecto con base de datos, el gate no es `check`: es **`migrate` contra el contenedor
real**. Y no es "corre un comando más" — es que estos tres **no responden a la misma pregunta**:

| Comando | A quién le pregunta | Qué demuestra |
|---|---|---|
| `manage.py check` | A Django, en memoria | Que la configuración y los modelos son coherentes **entre sí** |
| `makemigrations --check` | Al historial de migraciones | Que no falta ninguna migración por escribir |
| **`manage.py migrate`** | **A Postgres** | Que el esquema que describes **se puede construir de verdad** |

En una sesión de esta semana, **dos bugs distintos** pasaron el checklist pre-DONE con los dos
primeros en verde (`check` → *"no issues"*; `makemigrations --check` → *"No changes detected"*):

- `Key columns "created_by_id" and "id" are of incompatible types: uuid and bigint` — el modelo
  `User` se quedó con la clave primaria `bigint` por defecto mientras las bases abstractas
  declaraban UUID. La incompatibilidad **solo existe cuando Postgres intenta crear la clave
  ajena**, y eso pasa en `migrate`, no en `check`.
- `relation "audit_event" does not exist` — una migración con SQL crudo contra un nombre de tabla
  escrito a mano. Tumbó los tests de **otra app**, `customers`, sin relación con la que introdujo
  el fallo.

A los dos los encontró el Tech Lead corriendo los gates, **no** el frente que los introdujo: los
dos frentes habían dado su trabajo por cerrado y, con el checklist que tenían, con razón.

```bash
python manage.py migrate --no-input     # contra el contenedor real, no contra sqlite en memoria
```

Y **sobre una base recién creada**: una migración ya aplicada queda anotada en `django_migrations`
y no vuelve a correr, así que sobre una base vieja el fallo de creación no se reproduce y el gate
se pasa sin haber comprobado nada.

### 2. Tests (respetar límites de RAM)
```bash
# Verificar RAM antes
free -h | awk '/Mem:/ {print "Libre:", $7}'

# Correr solo el módulo afectado
pytest apps/<module>/ -v --maxfail=3
```

### 3. Verificación visual (si hay UI)
- Tomar screenshot con Playwright MCP o Python
- Confirmar que la página carga correctamente
- Revisar consola del browser (sin errores JS)
- **Con datos personales en pantalla, dos cosas y ninguna basta sola** (EVO-2876: el chequeo de
  texto dio «0 nombres» y los nombres iban dentro de la imagen): `screenshot.py` no guarda la captura
  si el texto de la página lleva un dato personal (siempre en un proyecto delicado o con
  `.claude/pii-capturas.json`; si no, `--guarda-pii`), y antes de entregar se MIRA cada imagen y se
  anota: `guarda_pii_capturas.py --registrar <carpeta> --por "<quién>" <png…>`, y
  `--comprobar <carpeta>` sale con 1 si falta una o cambió después (sub-ola 2.29, SE-42)

**Verificar de extremo a extremo con lo que trae Claude Code** (doc `code.claude.com/docs/en/skills`
§Run and verify your app y `chrome`, 2026-10-20): el «dale a Claude una forma de verificar su
trabajo» de §Principio, que Claude Code trae ya de serie:

| Herramienta | Qué hace | Ojo |
|---|---|---|
| `/run` (skill integrada) | Arranca y maneja la app para ver el cambio funcionando | Deduce el arranque del tipo de proyecto y del README; con base de datos, `.env` o build en varios pasos esa deducción se vuelve poco fiable |
| `/verify` (skill integrada) | Construye y corre la app para confirmar que el cambio hace lo que debe, **sin** refugiarse en tests ni tipos | **Claude no la lanza solo** desde la v2.1.215: hay que invocarla. Dentro de un `/loop` llega como texto, no se ejecuta. Puede grabar su receta como skill `verify` del proyecto (`<repo>/.claude/skills/verify/SKILL.md`) |
| `/run-skill-generator` | Deja la receta de arranque (instalación, variables, script) como skill del proyecto, `.claude/skills/run-<nombre>/` | Una vez por proyecto, y otra si cambia el build |
| `claude --chrome` | Claude in Chrome: el navegador de verdad, con consola y formularios | Necesita `/login`; con API key o token largo se queda apagado |

Con una skill **de proyecto** llamada `verify` (la que graba `/verify` en la raíz cuenta), Claude
Code le dice a Claude que la corra antes de cada commit, salvo cambios de docs o tests (v2.1.286+;
la integrada no cuenta). En este servidor el Playwright del MCP no tiene Chrome: las capturas van con
`/usr/bin/chromium-browser` y el Playwright de un venv: `bash .claude/scripts/preparar_navegador.sh`
los deja listos y saca una captura de prueba (exit 2 y el error entero si no puede).

**Medido en X-2.22 (28-10, Django · Next.js · Django+React, sonnet):** `/run` arrancó y capturó 3/3
y `/verify` dio PASS 3/3 comprobando además consola y título, que `screenshot.py` no mira. Por eso
son complemento de `screenshot.py`, no su sustituto: la captura con el comando conocido tarda 20-81 s
sin modelo, y `/run`+`/verify` 107-164 s por app (en fitapp, 2,4 $ nominales). En el prompt hay que
darles la banda de puertos, `127.0.0.1` y la BD; si no, no está medido qué eligen. `/run-skill-generator`,
una vez por proyecto, salió bien en 1 de 3: en `-p` le denegaron escribir en `.claude/skills/`, en
otro tocó `AGENTS.md`, y en fitapp tardó 16 min. Su diff se revisa antes de commitearlo.

### 4. Flujos críticos
- Login funciona
- La feature principal no está rota
- No hay datos mock visibles en producción

## Checklist pre-DONE

```
[ ] Código corre sin errores
[ ] Si el proyecto tiene base de datos: `python manage.py migrate` en verde contra el contenedor
    real (`check` valida la configuración; solo `migrate` le pregunta a Postgres — ver §1)
[ ] Tests del módulo pasan (si aplica)
[ ] Screenshot tomado (si hay UI)
[ ] No hay console errors en browser
[ ] Cada cifra que se reporta lleva línea base, condiciones y N, y lo medido es lo desplegado
    (§Una cifra sin sus condiciones no es evidencia)
[ ] PROGRESS.json actualizado
[ ] Si hay sesión SpecKit: gates deterministas en verde (SPEC-1/2, aprobados 2026-08-07):
      python3 .claude/scripts/task_progress.py "<sesión>/tasks.md" --gate   # checkboxes = aritmética
      python3 .claude/scripts/spec_lint.py "<sesión>"                        # estructura de la spec
    (spec_lint: ERROR bloquea; WARN se documenta. /speckit.analyze queda para lo semántico)
```

## Gate de verificación — la escalera de 4 niveles (DEC-4)

Fuente: `code.claude.com/docs/en/best-practices`, *"Give Claude a way to verify its work"*. Los
niveles son **acumulativos en fuerza y en coste**: sube solo lo que la tarea justifique. El criterio
es cuánta **autonomía sin supervisión humana** tiene la sesión.

| Nivel | Mecanismo | Qué fuerza | Cuándo usarlo | Coste |
|---|---|---|---|---|
| **1** | **En el prompt**: "corre los tests y pega la salida antes de decir DONE" | nada (advisory) | tarea normal supervisada | ~0 |
| **2** | **`/goal`** con condición demostrable | el turno no acaba hasta cumplir la meta | migración, refactor con criterio objetivo | bajo |
| **3** | **Stop hook** que bloquea el fin de turno | determinista: el agente **no puede** terminar | trabajo desatendido, `/loop`, waves | medio |
| **4** | **Subagente verificador** (contexto limpio) | criterio independiente del que hizo el trabajo | pre-merge, release, cambio de riesgo | alto |

### Nivel 1 — el prompt (advisory, pero gratis)

Pide la evidencia, no la conclusión: *"ejecuta `pytest apps/billing/ -v` y **pega la salida**"*,
*"haz screenshot y descríbeme lo que se ve"*. Es advisory — el agente puede ignorarlo — así que
nunca es el único nivel en algo que importe.

### Nivel 2 — `/goal` (condición de finalización)

```
/goal Migra apps/billing al nuevo cliente de pagos hasta que pytest apps/billing/ -v salga
      100% verde y pegue la salida en la conversación
```
El evaluador juzga **sobre lo que el agente muestra en la conversación**: la condición tiene que ser
demostrable ahí, y lleva lo que no puede cambiar y un tope («sin tocar `tests/`; o para tras 20
turnos»): la forma más corta de poner verde un test es cambiar el test. Detalle en `goal-vs-loop.md`
§`/goal`.

### Nivel 3 — Stop hook que bloquea el fin de turno (determinista)

El único nivel que **no depende del criterio del modelo**. Un hook `Stop` con exit code 2 impide
cerrar el turno y devuelve al agente el motivo:

```bash
#!/usr/bin/env bash
# .claude/hooks/verify-gate.sh — Stop hook: no se cierra el turno con la wave a medias
TASKS=$(ls .specify/sessions/*/tasks.md 2>/dev/null | head -1)
[ -z "$TASKS" ] && exit 0
if ! python3 "$CLAUDE_PROJECT_DIR/.claude/scripts/task_progress.py" "$TASKS" --gate >/tmp/gate.out 2>&1; then
  echo "BLOQUEADO: quedan tareas sin cerrar en $TASKS" >&2
  cat /tmp/gate.out >&2
  exit 2   # exit 2 = bloquea el fin de turno y el stderr vuelve al agente
fi
exit 0
```

Se registra en `settings.json` junto a los Stop hooks ya existentes (`notify-telegram.sh`, síncrono
con vía rápida, y `flag-visual-staleness.sh`, `async`; `session-stop.sh` pasó a `SessionEnd` el
2026-10-21, MO-72). `Stop` salta al final de **cada** respuesta: el gate debe ser **rápido y determinista** — un
script que ya existe (`task_progress.py --gate`, `spec_lint.py`, `check_shared_block.py`), no una
llamada al modelo.

> ⚠️ **`verify-gate.sh` es el nombre del ejemplo, no un hook del template**: no existe en
> `.claude/hooks/` (comprobado el 2026-10-20). Montarlo es crear el script y registrarlo en
> `settings.json`, y eso requiere aprobación (`governance.md` §2).

**Con base de datos, `migrate` es el candidato natural de este nivel**: es determinista y sale con
código ≠ 0 él solo, que es justo lo que pide un gate de nivel 3. Cuesta más que un `check` —crea el
esquema de verdad— y ese coste es exactamente lo que se paga por lo que compra (§1). Cablearlo como
hook toca `settings.json`, así que **requiere aprobación** (`governance.md` §2): aquí queda dicho
dónde encaja, no montado.

> ⚠️ **Límite real, documentado**: *Claude Code anula el hook y termina el turno tras **8 bloqueos
> consecutivos*** — **sin ninguna tool entre medias**: *"The count of consecutive continuations
> resets each time Claude calls a tool"* (doc `hooks` §Stop input, 2026-10-20). El Stop hook es una
> red de seguridad contra el olvido, **no una jaula, y tampoco un techo**: si el agente se limita a
> contestar, a los 8 bloqueos sale igual; si sigue trabajando contra un gate imposible —lee, edita,
> corre tests—, pone el contador a cero en cada vuelta y **no** sale a los ocho: gira hasta el tope
> de presupuesto o de turnos. Corolario: el mensaje de bloqueo debe decir **exactamente qué falta y
> cómo arreglarlo**, el gate debe ser alcanzable por el propio agente, y el script mira
> `stop_hook_active` para no bloquear sobre algo que nunca se va a resolver. El tope se sube con
> `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`. (Hasta el 2026-10-21 este aviso decía que «a los 8 intentos el
> agente sale igual», sin el matiz: corregido en la sub-ola 2.16.)

### Nivel 4 — subagente verificador (criterio independiente)

Un subagente con **contexto limpio** verifica el trabajo: no arrastra las racionalizaciones del que
lo hizo. Es el patrón Writer/Reviewer. Salida en el esquema de `verdict-contract.md` (doble
evidencia 🔎/👁 + Impact/Intent). Candidatos ya en el template: `code-review-gate`,
`rita-pattern-keeper`, `ignacio-roig`, `/feedback-audit`.

> ⚠️ **El caveat del reviewer adversarial** (misma fuente): *"un reviewer al que se le pide encontrar
> fallos normalmente reportará algunos, aunque el trabajo esté bien"*. Es sesgo de instrucción, no
> señal. Tres calibraciones que ya usamos:
> - **Ignacio y el `qa-loop`**: por eso su score **no entra en la media** y su valor está en el
>   *delta* contra Vera (`qa-loop.md`), no en el número absoluto.
> - **Rita**: por eso exige **≥2 precedentes `file:line`** del propio repo o calla.
> - **Todos**: por eso `verdict-contract.md` obliga a buscar el **Intent** antes de condenar y a
>   citar evidencia observada de primera mano.
>
> Regla práctica: si un verificador vuelve con hallazgos pero **ninguno con evidencia citable**, el
> resultado es "sin hallazgos", no "hay problemas difusos".

> ⚠️ **Segundo caveat: contexto limpio ≠ criterio independiente** (GRF-6, medido 2026-08-22).
> Que el verificador arranque con **contexto limpio** solo garantiza que no está contaminado *por la
> conversación* del que hizo el trabajo. Lo que decide de verdad su independencia es **qué se le pone
> delante**: si su único input es la conclusión del otro agente, el contexto limpio no lo salva —no
> tiene nada más que juzgar—, así que confirma o refuta **de oídas**, justo lo que prohíbe
> `verdict-contract.md` §3.
>
> El caso medido en casa, y su contraejemplo, están en el mismo directorio:
>
> | Workflow | Qué recibe el verificador | Qué exige su schema |
> |---|---|---|
> | `workflows/review-branch.js` (fase Verify) **hasta el 31-10** | `JSON.stringify(finding)` **y nada más**: ni el `git diff`, ni la ref base, ni instrucción de abrir el fichero | solo `isReal` — ningún campo para citar lo observado |
> | `workflows/review-branch.js` **desde la 3.03** (EQ-D9) | la base, la orden de abrir el fichero y su `git diff`; en `mantenibilidad`, los `evidence[].command`, que **re-ejecuta** | `observed` (`fichero:línea`) obligatorio; el JS compara la salida re-ejecutada con la declarada y descarta si no cuadra (`smoke/review-branch/check_evidence.mjs`) |
> | `templates/feedback_audit/feedback-verify.js` (fase Verify) | el DOM capturado, las capturas, la auditoría de enlaces y la pista de código, con orden explícita de leerlos | `why` **obligatorio**, con doble evidencia 🔎 código + 👁 en vivo |
>
> Misma arquitectura de workflow, independencia opuesta. (La misma forma aparece en
> `workflows/bug-sweep.js:62`, mitigada solo a medias por un voto 2-de-3 entre tres verificadores
> igual de ciegos.) En `review-branch.js` la mitigación ya está aplicada (sub-ola 3.03); `bug-sweep.js`
> sigue con la forma vieja.
>
> **Las dos preguntas antes de fiarte de un nivel 4:**
> 1. ¿El verificador **puede llegar al material crudo**, y se le dice explícitamente que lo abra?
> 2. ¿Su esquema de salida le **obliga** a citar lo que vio (`file:line`, DOM, salida del comando)?
>    Si el veredicto puede salir `true` sin evidencia propia, eso no es un gate: es un voto.
>
> Y ojo a la dirección del sesgo, que aquí se invierte respecto al caveat de arriba: un verificador
> **sin material** al que además se le instruye "ante la duda, refuta" está en duda permanente, así
> que su modo por defecto es suprimir hallazgos. No hemos medido cuántos suprime — habría que
> correrlo contra un fixture de findings conocidos (`qa-loop.md` §4b) y nadie lo ha hecho.

### Cómo elegir nivel

```
¿La verá un humano antes de que se propague?  → sí: nivel 1 (+2 si hay meta objetiva)
¿Sesión autónoma / desatendida (/loop, wave)? → nivel 3 (hook determinista)
¿Merge, release o cambio de riesgo?           → nivel 4 (+3 si además es autónoma)
```

### El nivel dice cuánta FUERZA; el dominio dice QUÉ se comprueba

Los cuatro niveles gradúan el enforcement, no el contenido. Un Stop hook que corre `npm test` es
nivel 3 exactamente igual que uno que corre la comprobación que solo tiene sentido en este negocio
— y el segundo caza lo que el genérico no puede ni ver:

| Dominio | La comprobación que ningún test genérico hace por ti |
|---|---|
| Salud | ningún dato de paciente aparece en logs ni en la respuesta de la API |
| Facturación / pagos | los apuntes cuadran · ningún importe viaja en coma flotante |
| Documentos / legal | el documento generado no arrastra material de otro cliente |
| Comercio | un pedido no puede quedar pagado sin stock reservado |

Al montar un gate, la pregunta que añade valor es **qué se rompería aquí que no se rompería en
cualquier otro proyecto**, y eso se comprueba *además* de los tests. Lo mismo vale para el
"simulador": correr la feature de verdad con una entrada real del dominio y mirar la salida suele
enterarse de cosas que la suite no mira.

> ⚠️ **Los cuatro ejemplos son ilustraciones, no gates medidos**: `grep -rn HIPAA .claude/` no
> devuelve nada, y ninguno de esos checks existe hoy en este repo. Es el eje que hay que rellenar
> por proyecto, no una lista que ya esté implementada.


## El instrumento que no puede medir debe ABORTAR, no devolver cero

> **Los dos lados de la misma moneda:** el instrumento que no puede medir **aborta**; el que sí
> puede **dice qué está midiendo**.

Cosechado de `elvion` (2026-08-26) y confirmado por separado en esta casa el 2026-08-27. Dos
sesiones llegaron a la misma conclusión sin hablarse, contando **catorce casos entre las dos**.

**Por qué es peor que un fallo normal.** Un instrumento apuntando a otro sitio no da *menos* señal:
da **señal falsa con el signo bueno**. Y nadie investiga un número que sale bien.

### Los catorce casos, y todos tienen la misma forma

| El instrumento | Decía | Y en realidad |
|---|---|---|
| Arnés de QA sin poder entrar (401) | **«0 fallos de contraste»** | Medía la pantalla de login, 8 elementos |
| Lector de contraste sobre un degradado | 7 fallos | Fantasmas: leía `backgroundColor` de un degradado |
| Conteo de tráfico `es-ES` | 16 registros | Era **nuestro propio tráfico de QA** |
| `grep -c` de un símbolo | 830 clases | Contaba **menciones**, no definiciones. Con AST: 298 |
| `printenv X >/dev/null && echo ok` | éxito | La variable estaba **declarada y vacía** |
| Un `--self-test` | siempre verde | **Imposible de satisfacer por construcción** |
| Gate de RAM | bloqueado | Contaba **sesiones**, no memoria. Bloqueaba con 24 GB libres |
| Bucle de espera `[ -f REPORT.md ]` | ronda completa | El fichero existía con **tres líneas de esqueleto** |
| `verificar-demo.sh` con `stderr` a `/dev/null` | «catálogo VACÍO» | Un `ImportError` era indistinguible de un catálogo vacío. Había 15 productos |
| `pattern_check_{backend,frontend}` | 2.643 hallazgos | **677 de 813 ficheros no eran nuestros** |
| Conteo de baseline | «sin baseline» | Comparaba `pattern_check_agente` contra `ag-tool-sin-schema` |
| `pgrep -f pytest` | «pytest en curso» | Cáscaras de bash de 3 MB al 0% de CPU |
| Grep del cuestionario | «usa LangGraph» | Encontraba **la doc del propio harness** |
| `red-flags.sh` | «(clean)» × 6 | Miraba `src/`, que en ese repo no existe |

### Las tres reglas que salen de ahí

**1. Un chequeo tiene TRES desenlaces, no dos.**

> hay dato · no hay dato · **el chequeo se rompió**

Colapsarlos destruye justo la información que hace falta para arreglarlo. Mandar `stderr` a
`/dev/null` es la forma más común de colapsarlos.

**2. Si el instrumento no puede llegar al sujeto, aborta con código ≠ 0.** No devuelve cero, no
imprime «(clean)», no dice «sin hallazgos». `red-flags.sh` es el ejemplo aplicado: si el directorio
no existe, sale con **exit 2** y lo dice.

**3. Se pregunta por el EFECTO, no por el artefacto.** La frase que resume los catorce:

> **Se pregunta por el artefacto porque es barato, y se contesta como si se hubiera preguntado por
> el efecto.**

«¿Existe `REPORT.md`?» es barato; «¿contiene un informe?» es la pregunta. «¿Está la variable
declarada?» es barato; «¿tiene valor?» es la pregunta.

### Tres pautas: listas contra el disco, contenido y no nombre, y el navegador que se va

La regla 3 aplicada a tres casos de `accounting_AMC` (`.claude/improvements_tl.md`, 26 y 27-08-2026;
MO-64, sub-ola 2.17). Los tres fallan en silencio y del lado peligroso.

| Pauta | El caso | Qué se hace |
|---|---|---|
| **Una lista escrita a mano se cruza con el disco en las DOS direcciones** | `test_por_modulo.sh` avisaba de módulos de la lista que ya no existían, pero no de tests en disco que la lista no nombraba: los 22 de `backend/core/arbol` no corrieron nunca en el CI, y el script decía «✓ 9 módulos en verde» | En la lista y no en disco: lista desfasada. En disco y no en la lista: **un fallo**, no un aviso. En el template lo hace `gate_diseno.py --self-test` contra `smoke/diseno/` (cualquier carpeta sin regla registrada sale con exit 1) |
| **Un hallazgo sobre el contenido se mide sobre el contenido, no sobre el nombre** | Una carpeta `datos_reales/` (el `MEDIA_ROOT` por defecto) hizo que una auditoría contara 712 ficheros como datos fiscales de clientes; por checksum eran 3 contenidos distintos, todos de prueba | `find <dir> -type f -exec sha256sum {} + \| cut -d' ' -f1 \| sort \| uniq -c \| sort -rn` antes de afirmar nada. Y ningún valor por defecto con nombre de producción (`subidas/`, no `datos_reales/`) |
| **El navegador puede desaparecer a mitad de sesión** | La caché de Playwright (`~/.cache/ms-playwright/`) se borró entre dos ejecuciones, probablemente desde otra sesión: «Executable doesn't exist» | El script que abre navegador sale con ≠ 0 dejando ver el error de Playwright **entero** (la causa va en sus «Browser logs»: una librería del sistema que falta no se arregla instalando el navegador) y, **solo** si lo que falta es el navegador, dice `playwright install chromium` (o «instala chromium-browser»); y cuenta cuántas páginas × anchos midió frente a las que pretendía. `medir_referencia.py` lo recortaba a la primera línea; desde el 2026-10-21 lo da entero, igual que `galeria.py`. `screenshot.py` ya dejaba salir el error entero |

### Y el aviso que hace esto una rule y no un consejo

De la sesión que lo escribió, y es incómodo:

> *«Un chequeo verde no está verificado; solo está sin ejecutar contra el caso que lo rompe.»*

Lo escribió **en el mismo fichero cuyo comentario avisaba de que un `printenv` había mentido por esa
misma razón**. O sea: **la lección escrita no protegió ni a quien la escribió.**

Por eso el único remedio que funciona es **verlo fallar**: antes de fiarte de un gate, plántale una
violación a propósito y comprueba que la caza. Los dos gates de patrones de este harness se probaron
así, y por eso se sabe que funcionan.

---

## Una cifra sin sus condiciones no es evidencia — línea base, N y «lo medido es lo desplegado»

> El otro lado de la sección anterior: el instrumento que no puede medir **aborta**; el que sí
> puede **dice qué midió, contra qué y sobre qué versión**. Una cifra sin eso no se reporta al
> Usuario ni sostiene una decisión.

Cosechado de `proxera_musa` (`.claude/improvements_tl.md` #1, #2, #3, #10 y #33, agosto-septiembre
de 2026, medido en su bot en producción; MO-63) y del feedback repetido del Usuario: *«deja de decirme
que está bien si no es así»*.

### Las cinco reglas

1. **El banco dice contra qué midió.** Elige sus condiciones **consultando el sistema**, no
   suponiéndolas, y las imprime en la cabecera de cada ejecución (`BANCO: 2026-08-24 (lunes) · 19
   huecos`). Sin esa línea, dos mediciones no son comparables y nadie lo nota. El caso: un banco
   decía «mañana por la mañana» y se ejecutó un sábado; «mañana» era domingo, centro cerrado, cero
   huecos: **1/10 donde el día antes daba 9/10**. Salieron tres cifras inventadas (5/10, 2/10, 1/10),
   se reportaron como regresiones y se estuvo a punto de revertir dos veces código que funcionaba.
2. **Lo medido es lo desplegado — en las dos direcciones.**
   - Antes de dar por buena una medición, **prueba que lo que corrió contiene el cambio**: el
     `grep` del símbolo nuevo se hace **dentro del contenedor**, no en el repo. En musa el arreglo se
     montó en `/code` y Python importaba de `/app`: dio **10/10 sin haberse ejecutado**; montado
     donde tocaba, 6/10 — era una regresión.
   - Antes de promocionar, **prueba que lo commiteado es lo medido**: la imagen que dio el buen
     resultado llevaba cambios sin commitear. En Python, comparar el AST sin docstrings ni
     comentarios entre el fichero de la imagen y el del repo separa diferencias reales de ruido.
   - En web, el sha no describe lo servido: el bundle y la respuesta de la API se sellan aparte
     (`qa-loop.md` §1b, `scripts/certifica_objeto.py`).
3. **Un parche no medido es una hipótesis, no un arreglo.** Con un LLM en el bucle, sobre todo:
   línea base **antes** de tocar nada; un cambio → una medición → comparar en **las mismas
   condiciones**; si empeora, revertir y **decirlo con el número**; nunca dos cambios sin medir
   entre medias. En musa, tres arreglos «obvios» medidos: uno cosmético (mejora dentro del ruido),
   otro rompía el grafo (**13/15 → 5/15**) y el tercero bloqueaba un rescate que nadie había visto
   (**9/10 → 6/10**). Los tres se revirtieron; el bueno apareció al instrumentar.
4. **Al Usuario, números con línea base, condiciones y N.** Nada de adjetivos donde hay un número.
   Un `15/15` con N=15 **no es** «100 % fiable»: se dice qué no se probó. Un arreglo revertido se
   cuenta, con su número, no se omite.
5. **Un informe de QA es una lista de síntomas, no de causas.** Cada punto se comprueba contra el
   sistema (base de datos, logs, catálogo) **antes** de escribir una línea de código; se mira
   **desde dónde miró** quien lo escribió —el mismo síntoma en dos entornos son dos historias— y se
   lee con más atención lo que el informe da por **dudoso**: lo que afirma seguro lo vio, lo dudoso
   es donde no pudo mirar. En musa, 2 de 11 puntos eran de otro entorno (el URGENTE incluido: miró el
   simulador de producción y había reservado en stage), y el punto que su autor daba por dudoso era
   el más grave.

### El formato del reporte

```
RESULTADO   <cifra> con N=<n>                  p. ej. 14/15 conversaciones del banco, N=15
FRENTE A    <línea base>, medida <cuándo>, en las MISMAS condiciones   (o «sin línea base»)
CONDICIONES <lo que imprimió el banco: fecha, datos, entorno, modelo, semilla>
OBJETO      <sha (sucio sí/no) · imagen o bundle medido · cómo se comprobó que es lo desplegado>
NO PROBADO  <lo que queda fuera: casos, entornos, tamaño de N>
```

Una casilla vacía **declarada** («sin línea base», «no comprobado que sea lo desplegado») vale; una
omitida es justo la cifra sin condiciones de la regla 1. El formato es el de `verification-loops`
cuando el resultado lleva un número, y el campo `why` de `verdict-contract.md` cuando es un veredicto.

---

## Lo importante no es que FALTE algo: es que SOBRE algo (TPL-4, cosecha de Xera)

> *«Un campo que nadie lee es indistinguible de un campo que funciona. La comprobación más importante
> de un validador no es que falte algo obligatorio — es que sobre algo.»*

El caso: un job con JSON válido y un campo `"mensaje"` de nombre razonable. El lector
(`run-job.sh`) solo leía `<nombre>.prompt`, así que el campo nunca se usó, y el fallo apareció
**seis horas después**, con un recordatorio que era una decisión de dinero. Ningún validador de
«campos obligatorios» lo habría cazado: no faltaba nada, sobraba algo que parecía funcionar.

Dos reglas que salen de ahí, y son las que hacen que un validador no envejezca:

1. **El validador comprueba sus propias reglas contra el consumidor al arrancar.** El de Xera
   (`validar-jobs.sh`) extrae `CLAVES_LEIDAS` **del propio `run-job.sh`** y falla si su lista y el
   lector divergen — *«si no, esto se queda viejo y no avisa»*. Es la misma forma que el gate de
   catálogo de `report-kit.md` (`render_nav.py --check`) y que `gen_docs.py --check`.
2. **La forma inversa también existe: un lector sin emisor.** `uso.py` leía un fichero de telemetría
   que escribía un hook que **no estaba instalado**; pasaba todas las comprobaciones de forma y
   contestaba siempre «sin datos». Antes de fiarte de un instrumento: ¿existe quien escribe lo que
   lee?

## Qué NO cuenta como verificación

- ❌ "Debería funcionar" sin haber ejecutado nada
- ❌ Leer el código y asumir que está correcto
- ❌ Pasar tests en local y no verificar en el entorno real
- ❌ Reportar DONE con errores pendientes de baja prioridad sin documentarlos
- ❌ Dar por verificado un cambio de modelos o de migraciones porque `check` y `makemigrations
  --check` están en verde — **ninguno de los dos habla con la base de datos**
- ❌ Un instrumento que no puede llegar al sujeto y **devuelve cero** en vez de abortar
- ❌ Mandar `stderr` a `/dev/null` en un chequeo: colapsa «no hay dato» con «se rompió»
- ❌ Preguntar por el **artefacto** (¿existe el fichero?) y contestar como si se hubiera
  preguntado por el **efecto** (¿contiene un informe?)
- ❌ Pedirle a un verificador que juzgue el hallazgo de otro agente pasándole **solo la conclusión**,
  sin el código ni el diff — eso no es un segundo criterio, es un eco del primero
- ❌ Una cifra sin línea base, condiciones ni N, o un «está bien» donde había un número (§Una cifra
  sin sus condiciones)
- ❌ Medir un objeto y desplegar otro: el repo en vez del contenedor, el sha en vez del bundle servido
- ❌ Trabajar un informe de QA sin comprobar antes cada punto contra el sistema ni desde qué entorno miró

---

## Smoke testing — `.claude/smoke/` (specs y evidencias atómicas)

*Antes `rules/smoke-testing.md`.* **Cuándo:** verificación rápida de que "lo básico vive" tras un
deploy, un cutover, o un gate de fase — antes de invertir en tests E2E completos o en el ciclo QA
visual. **No** sustituye a los tests unitarios/E2E ni al `qa-loop`: el smoke es el primer filtro
barato, no la garantía de calidad.

### Qué es

Una carpeta `.claude/smoke/` donde cada archivo es una **evidencia o spec atómica** de smoke-test:

- **Headers/HTTP**: salida de `curl -sI` de endpoints clave (`01-root.txt`, `02-admin.txt`, …) — que
  carguen y devuelvan el status esperado.
- **Screenshots**: capturas de páginas/estados clave (login, dashboard) antes/después de una fase.
- **Notas de gate**: decisiones por fase (`<fase>-<tema>.md`) — qué se validó, resultado, si pasa el gate.

El número/prefijo da orden de ejecución. Cada archivo es autoexplicativo y barato de regenerar.

### Patrón de uso

```bash
# Ejemplo de smoke HTTP (adapta host/puerto a $PROJECT_DOMAIN / $BACKEND_PORT)
for path in / /admin/ /api/health/; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${BACKEND_PORT}$path")
  echo "$path -> $code"
done
```

Una spec de gate (`.md`) registra: **qué se prueba → comando → resultado esperado → resultado real → PASA/NO**.

### Requests reales al endpoint recién escrito (PRM-4, aprobado 2026-08-07)

**Todo endpoint nuevo o modificado se llama de verdad antes de reportar DONE.** Es el hueco que
dejaban `verification-loops` (UI y tests) y el ciclo de producción (§Ciclo de producción: E2E de
flujos críticos): nadie comprobaba que el endpoint que acaba de escribirse responde cuando se le
llama. Cuesta segundos y caza el fallo más vergonzoso — el endpoint que existe en el código y
devuelve 500 al primer intento.

Es el **paso 5 de la escalera "explica antes de codear"** (plantilla en la skill `prompt-contracts`).

```bash
# Una petición por endpoint nuevo. Guarda status + cuerpo como evidencia.
API=http://127.0.0.1:${BACKEND_PORT}
{
  echo "### POST /api/candidates/  (crear)"
  curl -s -w '\nHTTP %{http_code} · %{time_total}s\n' -X POST "$API/api/candidates/" \
       -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
       -d '{"name":"Smoke Test","email":"smoke@example.com"}'
  echo "### GET /api/candidates/?search=Smoke  (leer lo recién creado)"
  curl -s -w '\nHTTP %{http_code}\n' "$API/api/candidates/?search=Smoke" -H "Authorization: Bearer $TOKEN"
} | tee .claude/smoke/10-candidates-endpoints.txt
```

Qué se mira en la salida (y se anota en el `.txt`):

| Comprobación | Falla si… |
|---|---|
| **Status esperado** por caso | 500 en el camino feliz · 200 donde debía haber 201/204 |
| **Forma del cuerpo** | Faltan campos del contrato, o aparecen campos internos que no deberían salir |
| **Camino de error** | Payload inválido devuelve 500 en vez de 400 con mensaje útil |
| **Auth** | La misma llamada **sin token** no devuelve 401/403 → el endpoint está abierto |
| **Método** | Un verbo que el endpoint no soporta no devuelve **405** → si sale 404 resuelve por ruta y oculta errores de integración; si sale 500 hay una vista que ramifica a mano (`rules/api-http-contract.md` §2-3) |
| **Ida y vuelta** | Creas algo y el GET siguiente no lo encuentra |

Mínimo por endpoint: **camino feliz + un payload inválido + una llamada sin auth + una con el
método incorrecto**. No sustituye a los tests de integración (mejor, pero mucho más caros y por eso
se posponen siempre): es el filtro barato que va antes.

```bash
# La cuarta, que cuesta un segundo y caza el endpoint que acepta más verbos de los que debía
curl -s -o /dev/null -w 'método incorrecto → HTTP %{http_code}\n' \
     -X GET "$API/api/candidates/" -H "Authorization: Bearer $TOKEN"   # en un endpoint solo-POST: 405
```

### Convenciones

- Versiona solo lo ligero: `.md` y `.txt`. Los screenshots grandes van en `.gitignore`
  (`.claude/smoke/**/*.png`) salvo que el equipo quiera conservarlos.
- Un smoke debe correr en **segundos** y no depender de datos de producción.
- Si un smoke falla → no sigas con E2E/QA; arregla el básico primero.

### Anti-patterns del smoke

- ❌ Meter lógica de test pesada en `smoke/` (eso es E2E).
- ❌ Smokes que dependen de credenciales/datos reales de producción.
- ❌ Dejar de regenerar las evidencias tras un cambio (quedan stale y engañan).
- ❌ Reportar DONE de un endpoint nuevo **sin haberlo llamado ni una vez**.
- ❌ Probar solo el camino feliz → el 500 aparece con el primer payload raro del cliente.
- ❌ Probar siempre con token de admin → nunca se detecta el endpoint que quedó abierto.
- ❌ No probar nunca un verbo que no toca → el endpoint que acepta GET **y** POST para la misma
  acción pasa el smoke entero sin que nadie lo note (`rules/api-http-contract.md` §2).
- ❌ Pegar la salida en el chat y no guardarla en `.claude/smoke/` (sin evidencia no hubo smoke).

---

## Estabilidad E2E — estado determinista, selectores estables y resiliencia a la UI

*Antes `rules/e2e-stability.md`.* **Cuándo:** siempre que escribas, arregles o ejecutes un test
**end-to-end** (Playwright, Cypress, Selenium) o el harness visual del proyecto (`/qa-loop`,
`screenshot.py`, `feedback-audit`). Es la parte que responde a *por qué el E2E pasa en tu máquina y
falla en CI*. **No** aplica a tests unitarios ni de integración de backend (ahí manda `ram-pytest.md`
+ el checklist pre-DONE de arriba), ni a un smoke HTTP de 3 endpoints (§Smoke testing).

### Principio del E2E

Un E2E que falla de forma intermitente **es peor que no tener E2E**: entrena al equipo a ignorar
el rojo. Los tres problemas que producen esa intermitencia son siempre los mismos —
**punto de partida inestable**, **selectores frágiles** y **cambios de UI** — y los tres se
resuelven en el diseño del test, no reintentando.

| Problema | Síntoma típico | Solución (esta sección) |
|---|---|---|
| Punto de partida inestable (BD, configs, filesystem) | Pasa el primer run, falla el segundo; "ya existe ese email" | §E2E-1 estado determinista |
| Selectores frágiles | Rompe al cambiar una clase de Tailwind o un texto | §E2E-2 `data-testid` |
| Cambios de UI | Rompen 12 tests a la vez por un rediseño | §E2E-3 Page Objects + §E2E-2 |
| Entorno de CI distinto al local | Verde en local, rojo en el pipeline | §E2E-4 flakiness en CI |

### E2E-1. Estado inicial determinista — el test crea su propio mundo

**Regla:** un test E2E nunca asume datos preexistentes ni deja residuos. Debe poder correrse
**dos veces seguidas** con el mismo resultado (idempotencia) y **en cualquier orden**.

#### Estrategias, de mejor a peor

| Estrategia | Cuándo | Coste |
|---|---|---|
| **BD efímera por sesión de test** (en memoria / contenedor desechable) | default para suites E2E | bajo, aisla del todo |
| **Transacción con rollback** por test | backend que expone hook de test | bajo |
| **Seed determinista + limpieza explícita** (`setUp`/`tearDown`) | cuando la app necesita datos "de fábrica" | medio |
| Reutilizar la BD de desarrollo | ❌ nunca | flakiness garantizado |

```bash
# Django — BD de test desechable y reutilizable entre runs de la MISMA sesión
pytest tests/e2e/ -v --maxfail=3 --reuse-db          # rápido en local
pytest tests/e2e/ -v --maxfail=3 --create-db          # limpio en CI

# Seed determinista (fixture versionada, NO un dump de producción)
python manage.py loaddata tests/fixtures/e2e_seed.json
```

```python
# Datos únicos por run: nada de "test@test.com" hardcodeado
import uuid
email = f"e2e-{uuid.uuid4().hex[:8]}@example.test"
```

**Congela lo que se mueve solo.** Fechas relativas ("hace 3 días"), `now()`, aleatoriedad y
paginación por fecha son fuentes de fallo intermitente: fija el reloj (`freezegun`,
`page.clock.set_fixed_time()`) o usa fechas absolutas en el seed. Esto es además prerrequisito de
la skill `visual-regression` (un baseline con la fecha de hoy caduca en 24h).

#### Prerrequisito de RAM (no negociable)

Los E2E abren browser: cuentan **~doble** en RAM y **nunca** se solapan con `pytest` de otros
módulos. Antes de lanzar, comprueba el umbral vigente en `ram-pytest.md`:
`free -h | awk '/Mem:/ {print $7}'`.

### E2E-2. Selectores estables — `data-testid` y nada más

**Regla:** el test se ancla a un contrato explícito (`data-testid`), no a la implementación visual.

```tsx
// Frontend: el testid es parte del contrato del componente, como una prop pública
<button data-testid="checkout-submit" className="rounded-lg bg-brand-600 …">Pagar</button>
```

```python
# Playwright (python)
page.get_by_test_id("checkout-submit").click()          # ✅ estable
page.get_by_role("button", name="Pagar").click()        # ✅ aceptable (rol + nombre accesible)
page.click(".rounded-lg.bg-brand-600 > span:nth-child(2)")  # ❌ rompe con el próximo rediseño
page.click("text=Pagar")                                 # ⚠️ rompe al traducir o cambiar copy
```

Jerarquía de preferencia: **`data-testid` > rol/nombre accesible > texto > CSS > XPath**.
Los dos últimos solo con justificación inline en el test.

**Convención de nombres:** `<área>-<elemento>-<acción|estado>` en kebab-case
(`login-email-input`, `orders-row-3`, `toast-error`). Un `data-testid` es API: renombrarlo es un
cambio que rompe consumidores, y se trata como tal.

**Beneficio lateral (a11y):** preferir rol + nombre accesible antes que CSS obliga a que los
elementos tengan `aria-label`/label real — el mismo trabajo que audita Aitor.

### E2E-3. Resiliencia a cambios de UI

- **Page Objects / helpers**: la ruta a un elemento se define **una vez**. Un rediseño toca un
  fichero, no doce tests.
- **Aserta comportamiento, no maquetación**: "tras enviar, aparece el pedido en la lista" resiste
  un rediseño; "el botón está a 24px del borde" no (eso es `visual-regression`, otro eje).
- **Espera por condición, nunca por tiempo**: `expect(locator).to_be_visible()` /
  `page.wait_for_url(...)`. `sleep(2)` es la causa nº1 de flakiness lenta.
  Gotcha del template: con `ThreadingHTTPServer` usa `wait_until="load"`, **nunca** `networkidle`.
- **Cobertura mínima viable**: E2E solo para los flujos críticos (login, el camino feliz del core,
  el flujo que da dinero). Todo lo demás, más abajo en la pirámide — es más barato y más estable.

### E2E-4. Flakiness en CI — el entorno es distinto y hay que asumirlo

| Fuente de flakiness | Mitigación |
|---|---|
| Máquina de CI más lenta → timeouts | timeouts explícitos y generosos en CI; nunca `sleep` fijo |
| Servicios externos (pagos, email, IA) | **mock en el boundary**; el E2E no debe salir a internet |
| Paralelismo → colisión de datos | datos únicos por worker (§E2E-1) o un worker para E2E |
| Zona horaria / locale del runner | fijar `TZ` y locale en el entorno del job |
| Falta de artefactos al fallar | guardar screenshot + vídeo + trace **siempre que falle** |
| Test flaky "conocido" | se marca y se **arregla o se borra**; no se reintenta en silencio |

```bash
# Playwright: artefactos de diagnóstico solo cuando falla
pytest tests/e2e/ -v --screenshot=only-on-failure --video=retain-on-failure --tracing=retain-on-failure
```

**Retries:** como máximo 1 reintento en CI y **con el fallo registrado**. Un retry que oculta el
problema convierte la suite en decorativa. Si un test necesita 3 retries, no es flaky: está roto.

### Checklist pre-merge de un test E2E

```
[ ] Corre dos veces seguidas sin limpiar nada a mano (idempotente)
[ ] No depende de datos que ya estaban en la BD
[ ] Todos los elementos se localizan por data-testid o rol+nombre
[ ] Ninguna espera por tiempo fijo (sleep) — todas por condición
[ ] No llama a servicios externos reales
[ ] Al fallar deja screenshot/trace en el artefacto de CI
[ ] Cubre un flujo crítico (no un detalle que ya cubre un unit test)
```

### Anti-patterns del E2E

- ❌ Correr E2E contra la BD de desarrollo (o peor, de producción).
- ❌ `time.sleep(2)` "para que dé tiempo a cargar" → lento y flaky a la vez.
- ❌ Selectores CSS acoplados a clases de utilidad (Tailwind) o a `nth-child`.
- ❌ Emails/usernames hardcodeados que violan `unique` en la segunda ejecución.
- ❌ Tests que dependen del orden en que se ejecutan.
- ❌ Reintentar hasta que pase y llamarlo verde.
- ❌ Lanzar la suite E2E en paralelo con `pytest` de otros módulos (el browser cuenta doble en RAM).
- ❌ Aserciones sobre píxeles/maquetación dentro de un E2E funcional → eso es `visual-regression`.

---

## Ciclo de producción — testing E2E, verificación visual y anti-mock

*Antes `rules/production-cycle.md` (su aviso corto se retiró el 2026-10-22 a
`_archive/2026-10-20/rules/`).* **Cuándo:** cuando el prompt incluya "ciclo de producción", en
releases y en toda feature importante. Consolidada desde CLAUDE.md (poda TPL-1, 2026-08-07). Complementa el checklist
pre-DONE genérico de arriba y `qa-loop.md` (gate visual de waves con UI).

### Flujo obligatorio de testing (antes de reportar DONE)

1. **Tests unitarios** → `pytest apps/MODULE/ -v` (RAM antes: `rules/ram-pytest.md`).
2. **E2E con Playwright MCP** → navegar la app, verificar flujos completos.
3. **Screenshots** → estado final de cada página/componente modificado.
4. **Guardar evidencia** → `/tmp/tl-*.png` o en el proyecto.

El Supervisor hará verificación adicional con su propio browser; si encuentra errores, relanza.
Waves con UI: cerrar además con `/qa-loop` (Lidia+Vera+Ignacio hasta media ≥9.0).

### GENERAL TESTS (siempre, en releases)

1. La web/app carga sin errores JS en consola.
2. Login funciona.
3. Navegación principal sin errores.
4. Screenshots before/after de cada página modificada.
5. APIs principales → HTTP 200.
6. **NO hay datos mock/hardcodeados visibles en UI.**

### SPECIFIC TESTS (por feature)

- Cada feature nueva → test Playwright que la verifica end-to-end.
- Cada bug fix → test que demuestra que el bug no ocurre.
- Screenshot como evidencia de cada test.

### Verificación anti-mock

```bash
grep -r "mockData\|fakeData\|hardcoded\|TODO.*real\|// fake\|demo_data" src/ \
  --include="*.tsx" --include="*.ts" --include="*.jsx"
```

Si aparece algo → arreglarlo antes de DONE. (El gate completo pre-merge: skill `code-review-gate`,
que añade además el check de dependencias alucinadas — SEC-1.)

### Verificación visual — cómo

Playwright MCP (`browser_navigate`, `browser_take_screenshot`…) o el helper con detección de Chrome:

```bash
python3 .claude/scripts/screenshot.py "http://127.0.0.1:8000/" /tmp/verify.png
```

Gotchas: `file://` bloqueado → servir con `python3 -m http.server --bind 127.0.0.1`; con ThreadingHTTPServer usa
`wait_until="load"`, nunca `networkidle`. **Si la tarea toca UI, screenshot SIEMPRE antes de DONE.**

### E2E con Playwright (python) — esqueleto

```python
import asyncio
from playwright.async_api import async_playwright

async def test_page_loads():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://127.0.0.1:8000/")
        assert await page.title()
        await browser.close()

asyncio.run(test_page_loads())
```

Instalación (pedir confirmación del Usuario): `pip install playwright && playwright install chromium`.
Úsalo solo para flujos críticos — es más lento que los tests unitarios. Cómo hacer que no sea
intermitente: §Estabilidad E2E.

### Anti-patterns del ciclo de producción

- ❌ Reportar DONE sin los 4 pasos del flujo.
- ❌ E2E de todo (lento) en vez de flujos críticos.
- ❌ Mock visible en producción "porque era una demo".

---

## Reglas y skills relacionadas

- **§Estabilidad E2E** (arriba; antes `e2e-stability.md`) — estado inicial determinista,
  `data-testid` y flakiness en CI: los tres motivos por los que un E2E "verificado" no verifica nada
- `verification-loops` — protocolo completo de loops de verificación
- `visual-regression` — diff objetivo de capturas contra baseline (caza el fix declarado que no se
  aplicó, algo que ningún checklist detecta)
- `ux-reviewer` — gate pre-DONE para cambios de UI
- `naive-user-playthrough` — verificación desde perspectiva de usuario no técnico
- `qa-loop` (`rules/qa-loop.md`, `/qa-loop`) — gate de cierre para waves **con UI**: orquesta
  Lidia + Vera + Ignacio en bucle convergente hasta nota media ≥ 9.0
- `feedback-audit` (`/feedback-audit`) — verifica feedback de cliente item por item contra el sitio
  en vivo (código + DOM), con veredicto estructurado e informe de evidencia
- **Contrato de veredicto** (`rules/verdict-contract.md`) — esquema único de salida para cualquier
  verificación "¿está hecho?": verdict/confidence/precision + nota de **doble evidencia** 🔎código / 👁 en vivo

---

_Rule version: 2.2 · 2026-10-31 (sub-ola 3.03, EQ-D9): GRF-6 aplicado en `review-branch.js`.
v2.1 · 2026-10-21 (sub-ola 2.16): §Una cifra sin sus condiciones (MO-63, de musa),
`/run`·`/verify`·`--chrome` en §3 (MO-79) y el tope de 8 del Stop hook, que se reinicia con cada tool.
v2.0 · 2026-10-20 (LI-27, sub-ola 1.06): absorbe tres rules y sus `paths:` —
`smoke-testing.md` (v1.2 · 2026-09-04, API-1: el mínimo por endpoint pasa de 3 llamadas a 4 con la
del método incorrecto, 405; v1.1 · requests reales al endpoint, PRM-4, aprobado 2026-08-07),
`e2e-stability.md` (v1.0 · 2026-08-08 · QA-1) y `production-cycle.md` (consolidada desde CLAUDE.md en
la poda TPL-1, 2026-08-07). Y avisa de que `verify-gate.sh` es un ejemplo, no un hook instalado._
