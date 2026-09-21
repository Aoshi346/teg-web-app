# Reglas de Verificación

> **Cuándo aplicar:** antes de reportar DONE en cualquier tarea, y al diseñar el gate de
> verificación de una sesión larga o autónoma (`/loop`, waves, trabajo desatendido).
>
> **NO aplicar:** como sustituto de los gates específicos — E2E → `e2e-stability.md`; wave con UI →
> `qa-loop.md`; release → el ciclo de producción del template; formato del veredicto → `verdict-contract.md`.
>
> **Relacionado:** `verdict-contract.md`, `e2e-stability.md`, `qa-loop.md`, el ciclo de producción del template,
> el smoke HTTP del template, skills `verification-loops`, `visual-regression`, `code-review-gate`.

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
demostrable ahí. Detalle en la escalera de `/goal` del template.

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

Se registra en `settings.json` junto a los Stop hooks ya existentes (`session-stop.sh`,
`notify-gateway.sh`, `flag-visual-staleness.sh`). El gate debe ser **rápido y determinista** — un
script que ya existe (`task_progress.py --gate`, `spec_lint.py`, `check_shared_block.py`), no una
llamada al modelo.

**Con base de datos, `migrate` es el candidato natural de este nivel**: es determinista y sale con
código ≠ 0 él solo, que es justo lo que pide un gate de nivel 3. Cuesta más que un `check` —crea el
esquema de verdad— y ese coste es exactamente lo que se paga por lo que compra (§1). Cablearlo como
hook toca `settings.json`, así que **requiere aprobación** (`governance.md` §2): aquí queda dicho
dónde encaja, no montado.

> ⚠️ **Límite real, documentado**: *Claude Code anula el hook y termina el turno tras **8 bloqueos
> consecutivos***. El Stop hook es una red de seguridad contra el olvido, **no una jaula**: si tu
> gate es imposible de satisfacer, a los 8 intentos el agente sale igual — y habrás quemado 8
> turnos. Corolario: el mensaje de bloqueo debe decir **exactamente qué falta y cómo arreglarlo**, y
> el gate debe ser alcanzable por el propio agente.

### Nivel 4 — subagente verificador (criterio independiente)

Un subagente con **contexto limpio** verifica el trabajo: no arrastra las racionalizaciones del que
lo hizo. Es el patrón Writer/Reviewer. Salida en el esquema de `verdict-contract.md` (doble
evidencia 🔎/👁 + Impact/Intent). Candidatos ya en el template: `code-review-gate`,
`especialista-seguridad`, `rita-pattern-keeper`, `ignacio-roig`, `/feedback-audit`.

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
> | `workflows/review-branch.js` (fase Verify) | `JSON.stringify(finding)` **y nada más**: ni el `git diff`, ni la ref base, ni instrucción de abrir el fichero | solo `isReal` — ningún campo para citar lo observado |
> | `workflows/feedback-verify.js` (fase Verify) | el DOM capturado, las capturas, la auditoría de enlaces y la pista de código, con orden explícita de leerlos | `why` **obligatorio**, con doble evidencia 🔎 código + 👁 en vivo |
>
> Misma arquitectura de workflow, independencia opuesta. (La misma forma aparece en
> `workflows/bug-sweep.js:62`, mitigada solo a medias por un voto 2-de-3 entre tres verificadores
> igual de ciegos.) El detalle del hallazgo, con líneas y la mitigación concreta, está escrito en un
> comentario dentro del propio `review-branch.js`.
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

### Y el aviso que hace esto una rule y no un consejo

De la sesión que lo escribió, y es incómodo:

> *«Un chequeo verde no está verificado; solo está sin ejecutar contra el caso que lo rompe.»*

Lo escribió **en el mismo fichero cuyo comentario avisaba de que un `printenv` había mentido por esa
misma razón**. O sea: **la lección escrita no protegió ni a quien la escribió.**

Por eso el único remedio que funciona es **verlo fallar**: antes de fiarte de un gate, plántale una
violación a propósito y comprueba que la caza. Los dos gates de patrones de este harness se probaron
así, y por eso se sabe que funcionan.

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
   catálogo de report-kit (template) (`render_nav.py --check`) y que `gen_docs.py --check`.
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

## Reglas y skills relacionadas

- **`e2e-stability.md`** — estado inicial determinista, `data-testid` y flakiness en CI: los tres
  motivos por los que un E2E "verificado" no verifica nada
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
