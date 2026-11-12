---
paths:
  - ".claude/patterns/**"
  - ".claude/scripts/pattern_baseline.py"
  - ".claude/patterns/baseline/**"
---
# Refactor progresivo — adoptar el patrón de casa en un proyecto que YA existe (y delegarlo a un agente)

> **Cuándo aplicar:** cuando el patrón de casa (`.claude/patterns/`) se lleva a un proyecto **que ya
> tiene código escrito**: adoptar el template en un repo existente, encender el gate de patrones en
> un proyecto vivo, o planificar un refactor grande hacia el estilo de casa. Define **el orden** de
> las fases, **el criterio de qué NO se toca nunca** (§3) y **el baseline** que impide que el gate
> bloquee contra el código antiguo (§4).
>
> **NO aplicar:** proyecto NUEVO sin código (ahí manda `.claude/patterns/stack/`, que ya trae el
> estado de cada regla para campo verde) · refactor de un solo módulo sin tocar reglas ni gates
> (eso es una tarea normal) · estilo cosmético —indentación, comillas, orden de imports— que ya
> cubren Ruff y Prettier (`rules/code-style.md`). **Delegar la ejecución a un agente** (encargo,
> guardarraíles, lote, revisión de lo que vuelve) es la **Parte II** de esta misma rule (§Refactor
> asistido por agente, §A0-§A8), que se lee **después** de la Parte I: aquí se decide QUÉ se toca,
> allí CÓMO se entrega el encargo.
>
> **Relacionado:** §Refactor asistido por agente (Parte II, abajo) ·
> `.claude/patterns/README.md` (el canon medido: dominancia, regla de inversión) ·
> `.claude/patterns/stack/README.md` (el patrón declarado y sus comprobadores) ·
> `.claude/patterns/baseline/README.md` (el formato del baseline, al detalle) ·
> `.claude/scripts/pattern_baseline.py` (la herramienta) · `rules/governance.md` §3.1 (autonomía por
> tipo de tarea) · `rules/plan-gates.md` (Gate D: un refactor de arquitectura cierra con ADR) ·
> `rules/verdict-contract.md` §Intent (buscar el porqué antes de condenar) · agente
> `rita-pattern-keeper` · skill `practices-manifesto`.
>
> **Fusionada el 2026-10-20 (LI-29, sub-ola 1.06):** la Parte II es la antigua
> `refactor-asistido.md`, con sus secciones renumeradas §A0-§A8 para no chocar con las de aquí. El
> porqué y lo que no se trasladó: `_archive/2026-10-19/README.md` §Sub-ola 1.06.

---

## 0. El fallo que esta rule existe para evitar

Enciendes el gate de patrones el primer día en un proyecto de verdad y te salen **cientos** de
incumplimientos. No son bugs: son código que lleva años funcionando y que se escribió antes de que
existiera la regla. Nadie va a arreglar cientos de sitios, así que el equipo hace lo único
razonable — **empieza a ignorar el aviso**.

Y esa es la peor consecuencia posible, peor que no tener gate: a partir de ese momento tampoco ve
los avisos que **sí** importan. Es el mismo mecanismo que la fatiga de aprobación de
`rules/agent-security.md` (ASI09): la fricción que no se puede atender se aprende a saltar.

Números reales, medidos en este mismo repo, para que se vea la escala:

| Medición real | Resultado |
|---|---|
| Comprobador de frontend sobre `resources/` (código de terceros vendorizado) | **108 hallazgos en 57 ficheros**, y **74 de ellos de una sola regla** |
| Contrato de capas propuesto para `evo-preven` (§4 del informe de estilo) | **126 entradas de baseline** — veinte veces el único baseline vivo del repo |

La salida no es bajar el listón ni apagar el gate: es **separar el pasado del presente**. El código
viejo se congela como deuda conocida (§4) y la regla solo se aplica a lo que se escribe desde hoy.

---

## 1. Las tres preguntas antes de tocar una línea

1. **¿Esto lo pide un problema o lo pide el gusto?** Un refactor sin daño demostrado es una apuesta
   pagada con el tiempo de otro. Si no sabes nombrar el incidente, el ticket o la línea que dolió,
   no hay refactor: hay preferencia.
2. **¿Tengo red debajo?** Sin tests del módulo y sin señal (logs, errores visibles) no estás
   refactorizando, estás reescribiendo a ciegas. La red va **antes** que el estilo (fase 1).
3. **¿Está en la lista de §3?** Si es una de esas, la respuesta ya está escrita y es "no se toca".

---

## 2. El orden — cinco fases, y ninguna se salta

### Fase 0 · Medir en sombra (no se toca nada)

**Sombra** = la regla corre y cuenta, pero no avisa a nadie ni bloquea nada. Es el estado con el que
entra toda regla en un proyecto existente; el vocabulario completo (`sombra` → `debil` → `activo`)
está en `.claude/patterns/README.md`.

```bash
# el comprobador que corresponda al stack; --all barre el proyecto, --json lo deja medible
python3 .claude/patterns/stack/pattern_check_backend.py  --all --json > /tmp/medicion.json
python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src --json > /tmp/fe.json
```

Salida de esta fase: **cuántos sitios marca cada regla**. Ese número decide sola la mitad de las
decisiones siguientes — sobre todo la regla de inversión (§4.4).

### Fase 1 · La red, antes que el estilo

No hay refactor seguro sin dos cosas, y en un proyecto heredado suelen faltar las dos:

- **Tests del módulo que vas a tocar.** No de todo el proyecto: del módulo. (En el caso medido:
  8 `def test_` en 740 ficheros, de los cuales 2 reales. Ahí el primer trabajo no es refactorizar,
  es poder verificar.)
- **Señal de vuelta.** Sin logging ni errores visibles, un refactor que rompe algo se entera el
  cliente. *No hay autonomía sin señal de vuelta*, y sin ella cualquier otra mejora es invisible.

Esta fase construye; no cambia estilo. Y es la que más se salta.

### Fase 2 · Solo el daño ya materializado

Se ordena por **valor ÷ coste**, donde valor = **daño que ya ocurrió**, no riesgo teórico. Ejemplos
del informe de estilo, con su evidencia:

| Se toca | Por qué (daño real, no hipotético) |
|---|---|
| Filas escritas en bloque saltándose la lógica de guardado | Filas en producción sin su código y **sin historial**, en un producto cuyo valor ES el registro auditable |
| Dos apps sirviendo la misma ruta de plantilla | 34 líneas que **no se renderizan nunca**; editarlas no produce cambio ni error. El bug más caro de diagnosticar de la lista |
| Llamadas HTTP sin `timeout` | 37 de 39. Una conexión colgada aparca un worker indefinidamente — ya provocó un incidente documentado |

Lo de **seguridad** (un `DEBUG` activado por defecto, una clave privada versionada) **no va por
aquí**: no es refactor, es incidente, y va por su vía y con su prioridad (`rules/security.md`).

### Fase 3 · Lo mecánico y barato

Cambios sin decisión de diseño: añadir un argumento a 37 llamadas, borrar ficheros stub muertos.
`rules/governance.md` §3.1 los clasifica como **mecánicos y verificables** → autonomía alta, en
lote, con dos guardarraíles obligatorios: **tests en verde antes y después**, y **el diff acotado a
los ficheros previstos** (un fichero fuera de la lista para el lote).

### Fase 4 · Promover reglas — con criterio escrito ANTES de medir

Aquí es donde el proyecto pasa de "medimos" a "esto bloquea". Es la fase que crea fricción real, y
por eso el criterio se escribe **antes** de ver los números — si se decide después, se decide para
que salga lo que ya querías. Criterio duro en §4.5.

### Nunca · La lista de §3

---

## 3. Lo que NO se toca — el test, y los 13 casos que lo produjeron

Esta es la parte que más valor tiene, y la que más se incumple: llegar a un repo ajeno y
"modernizarlo" es la forma más rápida de romper algo que funcionaba y de perder la confianza del
equipo que lo mantiene. Lo que sigue **no es una lista de hechos de Django**: es el test que
rechazó 13 candidatos concretos, medidos uno a uno, en un backend real en producción.

### El test — 8 preguntas. Basta una para dejarlo como está

| # | Pregunta | Se deja como está cuando… | Caso medido |
|---|---|---|---|
| 1 | **¿Qué problema demostrado resuelve?** | La respuesta es "ninguno, pero es lo moderno" | Mover 46 apps a una carpeta `apps/`: **46 renombrados + los imports de 740 ficheros**. Problemas resueltos: **ninguno** |
| 2 | **¿Cuánto cuesta, contado en ficheros?** | El coste se cuenta en cientos y el beneficio en adjetivos | Partir un `settings.py` de 960 líneas que ya resuelve por ~40 variables lo que el split resolvería por ficheros |
| 3 | **¿Es *load-bearing*?** (parece deuda, pero sostiene algo) | Quitarlo rompe lo que hoy funciona | **384 `from X import *`** en 220 ficheros. Al medir los símbolos realmente pisados: **4, de un solo nombre, en 2 ficheros**. Funciona *porque* el arquetipo garantiza qué hay en cada fichero |
| 4 | **¿Lo ve alguien de fuera?** | Es contrato con un humano o un sistema externo, no implementación | La clave primaria entera genera `COM-1423`, **un código que el usuario final dicta por teléfono**. Con UUID pasa a ser ilegible |
| 5 | **¿Ya cumple el objetivo con otro nombre?** | Solo cambiaría la etiqueta | `utils.py` **ES** la capa de servicios: 28-30 ficheros, funciones puras con cinco tipos de invocador. Renombrar 30 ficheros no arregla los 3 sitios donde la lógica sí está atrapada |
| 6 | **¿Un gate aquí moriría de ruido?** | La regla marcaría la mayoría de los casos | **390 borrados en cascada = 67% de las claves ajenas.** Una regla que marca dos de cada tres sitios no es una regla (→ regla de inversión, §4.4) |
| 7 | **¿La razón es "puede quedar obsoleto"?** | La documentación dice *may be deprecated* — futuro condicional | Migrar 3 declaraciones que funcionan, sin tests que las cubran, es cambio por moda |
| 8 | **¿Añade corrección o comodidad?** | Añade comodidad y lo valioso ya está hecho | Las 187 tuplas de opciones ya están centralizadas y compartidas; la sintaxis moderna añade tipado y etiqueta — cómodo, no correcto |

Dos avisos que acompañan al test:

- **Lo que parece ilegal puede estar verificado.** Los agrupadores de subapps sin `__init__.py`
  parecen un error y no lo son: la restricción de la documentación aplica a **la app**, no al
  agrupador. Antes de marcar algo raro como defecto, compruébalo contra la doc de la versión que
  usa el proyecto. Es el **Intent** de `rules/verdict-contract.md` aplicado a la arquitectura.
- **Lo raro suele ser coherente con una decisión mayor.** Que la validación viva en el formulario y
  no en el modelo es coherente con tener **un** framework CRUD. El problema real no era dónde
  validaba el formulario, sino que **no hubiera** validación en las vías que no son el formulario.
  Arregla el hueco, no la coherencia.

### Los 13, y qué pregunta los rechaza

| # | Candidato descartado | Rechazado por |
|---|---|---|
| 1 | Mover las apps planas a una carpeta `apps/` | 1, 2 |
| 2 | Partir el `settings.py` único en `base/dev/prod` | 1, 2 |
| 3 | Renombrar `utils.py` a `services.py` | 5 |
| 4 | Enumerar los 384 `from X import *` | 3 |
| 5 | "Arreglar" los agrupadores namespace-package | verificado contra la doc |
| 6 | Sustituir el import explícito en `ready()` por autodescubrimiento | 5 (y es **mejor**: greppable y determinista) |
| 7 | Cambiar el registro con clave derivada del modelo | 1 |
| 8 | Partir el fichero plano de 1.768 líneas en un paquete | 1, 3 |
| 9 | Migrar `unique_together` | 7 |
| 10 | Poner un gate al borrado en cascada | 6 |
| 11 | Migrar las 187 tuplas de opciones a la sintaxis moderna | 8 |
| 12 | Imponer UUID como clave primaria | 4 |
| 13 | Mover la validación del formulario al modelo | coherencia (arregla el hueco, no el patrón) |

**Se escribe la decisión, no solo se toma.** Cada "no se toca" se anota una vez —en el ADR del plan
o en el propio `patterns/`— con su medida. Si no, dentro de seis meses alguien vuelve a proponer
mover las apps y se rehace el análisis entero.

---

## 4. El baseline — congelar la deuda para que el gate no bloquee

### 4.1 Qué es, en una frase

Un **baseline** (o *ratchet*, trinquete) es la lista escrita de las infracciones que **ya existían**
el día que encendiste la regla. El gate las conoce y **no las reporta**; solo avisa de lo que
aparezca a partir de ahí. Trinquete porque solo gira en un sentido: la deuda puede bajar, nunca
subir en silencio.

Vive en `.claude/patterns/baseline/<patron_id>.json`, versionado en git — **nunca por usuario**: una
exención que solo existe en la máquina de alguien no es una exención, es un secreto.

### 4.2 El formato (no hay schema nuevo)

Es el mismo fichero que ya usaba el repo. Ejemplo real, tras una retirada:

```json
{
  "patron_id": "rule-header-cuando-aplicar",
  "frozen_at": "2026-08-07",
  "nota": "Deuda aceptada (ratchet). Solo un humano amplía esta lista. Migran por boy-scout.",
  "migradas": [
    {"file": ".claude/rules/security.md", "fecha": "2026-08-08",
     "por": "cabecera añadida por boy-scout durante la adopción; verificado 2026-08-08"}
  ],
  "violations": [
    ".claude/rules/code-style.md",
    ".claude/rules/speckit-progress-tracking.md"
  ]
}
```

**La clave es el fichero, no la línea** — y es deliberado. Los números de línea se mueven con
cualquier edición de más arriba: un baseline anclado a líneas empieza a mentir en el primer commit.
El precio de anclar al fichero es real y hay que decirlo: **un fichero congelado queda exento de esa
regla entero**. Lo que cierra ese agujero no es afinar el baseline, es el modo `--diff-scope`
(§4.3): si tocas la línea, se te juzga la línea.

Detalle del formato, campos opcionales y ciclo de vida: `.claude/patterns/baseline/README.md`.

### 4.3 Los tres comandos

```bash
# 1) CONGELAR — una sola vez, al adoptar la regla en el proyecto
python3 .claude/patterns/stack/pattern_check_backend.py --all --json > /tmp/medicion.json
python3 .claude/scripts/pattern_baseline.py freeze --from /tmp/medicion.json

# 2) EL GATE DEL DÍA A DÍA — solo se juzga lo que este cambio ha tocado
python3 .claude/patterns/stack/pattern_check_backend.py --json \
  | python3 .claude/scripts/pattern_baseline.py check --from - --diff-scope

# 3) SANEAR — qué deuda queda y qué ya se puede retirar
python3 .claude/scripts/pattern_baseline.py status --from /tmp/medicion.json
python3 .claude/scripts/pattern_baseline.py retire --from /tmp/medicion.json --apply
```

**Los dos modos de `check`, que responden a preguntas distintas:**

| Modo | Qué juzga | Para qué |
|---|---|---|
| `check` (por defecto) | Todos los hallazgos, silenciando los ficheros congelados | Barrido del proyecto entero, informe de deuda |
| `check --diff-scope` | **Solo las líneas que este cambio ha añadido o modificado** (las lee de `git diff`) | El gate de un PR o de un pre-push |

En `--diff-scope` el baseline **no silencia**: si has tocado esa línea, es tuya (*boy-scout*: se deja
un poco mejor de como se encontró). Así el código nuevo cumple desde el día uno aunque el fichero
esté lleno de deuda antigua.

**Retirar una entrada no se hace a mano.** `retire` compara la medición de hoy contra el baseline,
detecta lo que ya no infringe, lo mueve a `migradas` con fecha y motivo, y deja `violations` más
corto. Sin `--apply` es un simulacro. Ese historial es lo que impide que la deuda vuelva a entrar
sin que nadie lo note.

### 4.4 La regla de inversión — el baseline no sirve para blanquear una regla mala

> Si una regla marcaría **más de 20-30 sitios existentes**, lo que está mal es la regla, no el código.

Ya estaba en `.claude/patterns/README.md`; aquí se hace ejecutable. `freeze` **se niega** a congelar
una regla que supere el umbral y explica por qué:

```
✗ fe-error-no-silencioso: congelaría 49 ficheros (> 30).
   REGLA DE INVERSIÓN (patterns/README.md §2): si una regla marca tantos sitios,
   lo que está mal es la regla, no el código. Congelarla es blanquearla.
   → revisa el enunciado, acótalo, o déjala en 'sombra' y no la promuevas.
```

Se puede forzar con `--force`, y entonces el fichero queda marcado con `aviso_inversion` para que la
decisión sea visible en el diff. **Usar el baseline para acallar una regla que el propio canon
declara equivocada es exactamente el atajo que la regla de inversión existe para impedir.**

### 4.5 Criterio de promoción — escrito ANTES de medir

Una regla pasa de `sombra` a `debil` o `activo` **solo si cumple las cinco**, y la lista se acuerda
antes de mirar los números:

1. **Dominancia ≥85%** en el repo (`patterns/README.md` §1) **o** baseline por debajo del umbral de
   inversión (≤30 ficheros).
2. **Cero falsos positivos** sobre los ficheros conformes (`--self-test` de su comprobador).
3. **La deuda baja entre dos mediciones.** Si el baseline no se mueve, nadie la está pagando y
   activarla solo va a producir excepciones.
4. **Hay arreglo mecánico o exención documentada** (`pattern-exempt: <id> — razón`).
5. **Lo firma un humano, con fecha.** Ningún agente se auto-promociona una regla
   (`rules/governance.md` §2, `rules/agent-autonomy-ladder.md`).

**Y el aviso que no se puede omitir:** en `sombra` la fricción es **cero**, así que un baseline
enorme no molesta a nadie y es fácil convencerse de que no pasa nada. La fricción aparece de golpe
**al promover**. Con un baseline como el del contrato de capas —**126 entradas**— cada import nuevo
legítimo pasaría por revisión humana o por una exención escrita. Por eso, si el baseline supera las
~30 entradas, la promoción exige además responder por escrito: **quién revisa cada caso nuevo y en
cuánto tiempo.** Si no hay respuesta, la regla se queda en sombra. No es un "ya veremos".

---

## 5. Límites honestos

- **El baseline por fichero es una exención por fichero.** `--diff-scope` cierra la mayor parte del
  agujero, no todo: una línea nueva en un fichero congelado se ve, pero una infracción vieja en una
  línea que nadie toca sigue invisible. Es el precio de no anclar a números de línea.
- **Nada de esto ordena el trabajo por ti.** Decide qué se congela y qué se arregla; no dice si el
  módulo merece el refactor. Eso es criterio, y sigue siendo humano.
- **La medición envejece.** Un `status` de hace tres meses no vale: se vuelve a medir antes de
  decidir.
- **El hook actual no distingue `violations` de `migradas`.** `hooks/pattern-check.sh` comprueba el
  baseline con un `grep` de la ruta sobre **todo** el fichero, así que un fichero ya migrado sigue
  exento para siempre. Es una fuga real del trinquete, **anterior a esta rule**, y su arreglo toca
  `hooks/` → requiere aprobación (`governance.md` §2). Mientras tanto, la comprobación fiable es
  `pattern_baseline.py check`, que sí lee solo `violations`.

---

## Anti-patterns

- ❌ Encender el gate en un proyecto existente **sin congelar** antes → cientos de avisos el primer
  día y un equipo que aprende a ignorarlos.
- ❌ Congelar una regla que marca 49 sitios "para poder activarla ya" → estás blanqueando la regla
  (§4.4), no pagando deuda.
- ❌ Refactorizar antes de tener tests del módulo → no es refactor, es reescritura a ciegas.
- ❌ Modernizar por gusto lo que pasa el test de §3 → coste en cientos de ficheros, beneficio en
  adjetivos.
- ❌ Tocar la clave primaria, el formato de un código o cualquier cosa **que el usuario final ve**
  tratándola como detalle de implementación (§3, pregunta 4).
- ❌ Anclar el baseline a números de línea → miente en el primer commit.
- ❌ Editar `violations` a mano para quitar una entrada → se pierde el historial de `migradas`; usa
  `retire`.
- ❌ Re-congelar el baseline entero "para actualizarlo" → crece en silencio y el trinquete gira al
  revés. `freeze` se niega salvo `--replace` explícito.
- ❌ Promover una regla porque "ya está medida", sin haber escrito antes el criterio (§4.5).
- ❌ Dejar el baseline sin mirar durante meses → deja de reflejar la realidad y nadie confía en él.
- ❌ Anotar la deuda en el ticket de alguien en vez de en `baseline/` → no es auditable ni se puede
  medir si baja.

---

## Refactor asistido por agente — cómo se delega un refactor sin que te lo devuelvan roto

*Antes `rules/refactor-asistido.md`: es la **Parte II** de esta rule, y se lee **después** de la
Parte I (arriba), que decide qué se toca.* **Cuándo:** cuando el que ejecuta el refactor **no eres
tú, es un agente** — un subagente, una instancia en worktree, una sesión desatendida o nocturna.
Define **el encargo** (qué tiene que llevar escrito para ser delegable, §A2), **los cuatro
guardarraíles** con su comando (§A3), **el tamaño del lote** (§A4), qué cambia **sin nadie mirando**
(§A5) y **cómo se revisa lo que vuelve** cuando son cuarenta commits (§A6). **No:** para decidir
**qué** refactorizar, en qué orden y qué no se toca nunca — eso es la Parte I · para un refactor que
haces tú a mano (ahí manda el criterio, no el protocolo) · para estilo cosmético que ya cubren Ruff y
Prettier (`code-style.md`) · para una **reescritura** o un cambio de comportamiento deliberado, que no
es un refactor y no entra aquí bajo ningún concepto. **Relacionado:** `governance.md` §3.1 (autonomía
por tipo de tarea: de dónde salen los guardarraíles) · `agent-autonomy-ladder.md` (§4 lo no
delegable, §5 el freno que acciona el propio agente) · `parallelization.md` §file claims (dos
frentes, un fichero) · `verdict-contract.md` §Intent (buscar el porqué antes de "arreglar" algo raro)
· `verification.md` (la escalera de 4 niveles: el Stop hook de §A5 es su nivel 3) · `plan-gates.md`
(Gate D: si cambia arquitectura, cierra con ADR) · `goal-vs-loop.md` §Modo noche · agente
`rita-pattern-keeper` · skill `pattern-gate`.

### A0. El hueco que cierra

Tenemos escrito **qué** refactorizar (la Parte I, arriba) y **cuánta cuerda** dar según el tipo
de tarea (`governance.md` §3.1). No teníamos escrito lo del medio: **cómo se redacta el encargo, qué
se comprueba mientras corre y qué se mira cuando vuelve.** Y es justo donde se pierde el dinero,
porque el refactor delegado tiene una propiedad incómoda: **sale bien casi siempre, y cuando sale mal
lo parece bien.** Cuarenta ficheros tocados, tests en verde, y en el commit 23 el agente "aprovechó
que estaba ahí" y cambió una condición.

#### La corrección al argumento habitual (léela antes de fiarte)

El argumento a favor de delegar refactors —y de hacerlo de noche— es bueno y es este: **el test
decide y el diff está acotado**, así que hay una señal objetiva de que no se rompió nada. Es cierto.
Pero dice menos de lo que parece, y conviene tenerlo claro antes de dejar un agente corriendo ocho
horas:

> **El test verifica que no rompiste nada. No verifica que hayas mejorado algo.**

Un refactor cuyo objetivo es *"que esto se entienda"* no tiene ninguna comprobación automática de si
lo consiguió. Los tests pueden salir verdes sobre un resultado **peor** que el original: más
indirección, una abstracción que nadie pidió, tres ficheros donde había uno. Eso es un **fallo con
forma de éxito**, y ningún gate lo caza.

Consecuencia práctica, y es la que ordena toda esta rule:

| Eje | ¿Quién lo juzga? |
|---|---|
| **¿Se rompió algo?** | El test. **Automatizable** → aquí sí hay autonomía alta (§A3) |
| **¿Quedó mejor?** | Una persona, o `rita-pattern-keeper` contra el patrón del repo. **No automatizable** |

Por eso lo que se delega con manga ancha es el refactor **mecánico** (§A1), donde "mejor" ya está
decidido de antemano por la regla que se aplica, y lo que **no** se delega así es el refactor con
criterio, por muchos tests que tenga.

---

### A1. ¿Es delegable? — el semáforo, antes de escribir el encargo

Cruza el tipo de trabajo (`governance.md` §3.1) con la red que hay debajo (§2, fase 1, arriba).
**Manda siempre la casilla más restrictiva.**

| | **Con tests del módulo** | **Sin tests, o tests que no cubren lo que temes** |
|---|---|---|
| **Mecánico** — aplicar una regla decidida a N sitios: añadir un argumento, renombrar, migrar sintaxis, mover imports | 🟢 **Delegable en lote.** Los 4 guardarraíles de §A3 y a correr | 🟡 **El agente propone, tú aplicas.** Que genere el diff completo y **no commitee**: lo revisas y lo aplicas tú |
| **Con criterio** — extraer un módulo, partir un fichero, reordenar responsabilidades | 🟡 **Plan primero, ejecución después.** El agente escribe el plan (`[PLAN]` en `PROGRESS.log`), lo apruebas, y **entonces** ejecuta | 🔴 **No se delega.** Primero la red (fase 1), y la red no es parte del refactor: es una tarea aparte y anterior |
| **De arquitectura o contrato** — límites de módulo, esquema, API pública | 🔴 **No se delega la decisión.** Se decide con ADR (`plan-gates.md` Gate D); el agente ejecuta lo ya decidido, y eso vuelve a ser mecánico | 🔴 **No** |

#### El límite honesto, dicho sin adornos

> **Sin tests no hay refactor autónomo, por mecánico que parezca el trabajo.** El guardarraíl es el
> test, no la etiqueta. Un renombrado en 200 ficheros sin una sola prueba que lo cubra no es
> "mecánico y verificable": es **mecánico y no verificable**, que es otra cosa y baja de autonomía.

Y una vuelta de tuerca que se salta casi todo el mundo: **que haya tests no significa que haya red.**
Una suite que pasa igual con el módulo roto no protege de nada. Antes de delegar un lote grande,
compruébalo en treinta segundos:

```bash
# Rompe UNA línea a propósito en el módulo que se va a tocar y comprueba que la suite se entera.
# Si sigue en verde, la red no existe: no delegues todavía.
pytest apps/<modulo>/ -v --maxfail=1      # debe salir ROJO con el sabotaje puesto
git checkout -- <el fichero saboteado>    # y se deshace, obviamente
```

Cuesta un minuto y es la diferencia entre tener red y creer que la tienes.

Para que no dependa de acordarse, el arnés lo deja escrito junto a los tests y lo repite en cada
lote: `python3 .claude/scripts/sabotage.py <sabotajes.json>` (cada sabotaje cambia una línea, corre la
suite, restaura y exige rojo; uno de control tiene que seguir en verde). Formato en su cabecera.

---

### A2. El encargo — las 7 líneas sin las cuales no se delega

Un refactor delegado se cuela por lo que **no** dijiste. El agente rellena los huecos con criterio
propio, y su criterio es "mejorar", que es exactamente lo que no le has pedido. El encargo lleva
estas siete líneas, siempre, y son literales:

```
REGLA:        la ÚNICA transformación a aplicar, en una frase, con un antes/después de ejemplo
FICHEROS:     la lista EXACTA (o el glob) — y "nada fuera de esta lista"
TESTS:        el comando exacto que tiene que estar en verde antes y después
COMPROBADOR:  el comando del catálogo/linter, si lo hay (pattern_check_*.py, tsc, ruff)
LOTE:         cuántos ficheros por commit, y el formato del mensaje
PROHIBIDO:    cambiar comportamiento · tocar tests · renombrar nada público · "de paso" arreglar otra cosa
SI PASA X:    qué hacer ante lo imprevisto → PARAR y reportar, nunca improvisar
```

Ejemplo real y completo, del tamaño que debe tener:

```
REGLA:        toda llamada con requests.<verbo>(...) lleva timeout=10 si no lo trae ya.
              antes: requests.get(url)     después: requests.get(url, timeout=10)
FICHEROS:     los 37 de /tmp/sin-timeout.txt. Nada fuera de esa lista.
TESTS:        pytest apps/integraciones/ -v --maxfail=3
COMPROBADOR:  ruff check apps/integraciones/
LOTE:         10 ficheros por commit · "refactor(integraciones): timeout explícito (lote N/4)"
PROHIBIDO:    cambiar el valor si ya había timeout · tocar ningún test · reordenar imports ·
              cualquier otra mejora que veas por el camino
SI PASA X:    si una llamada está dentro de un reintento o un with, o el timeout tendría que ser
              distinto → NO la toques, anótala y sigue con las demás. Al final me pasas la lista.
```

Fíjate en la última línea: **da una salida al caso raro que no es "decide tú"**. Sin ella, el agente
elige entre pararse del todo (y pierdes la noche) o improvisar (y pierdes la confianza en el lote).
La tercera vía —sáltala y anótala— es casi siempre la correcta en un refactor mecánico.

`PROHIBIDO` no es paranoia: **el scope creep es EL modo de fallo del refactor delegado.** Un agente
que está editando un fichero y ve al lado algo mejorable, lo mejora. Es lo que le hemos pedido toda
la vida. Aquí no.

---

### A3. Los cuatro guardarraíles — cada uno con su comando

Vienen de `governance.md` §3.1, que los enuncia. Aquí se vuelven ejecutables. **Los cuatro, en cada
lote, no una vez al final.**

#### G1 · Verde antes y verde después — y ni un test tocado

Lo primero es de `governance.md`. Lo segundo es la parte que faltaba, y es la comprobación más
barata y más decisiva de todo este documento:

> **Si para que pasen los tests hubo que tocar un test, no era un refactor.**

Un refactor, por definición, no cambia el comportamiento observable. Los tests observan el
comportamiento. Luego los tests **tienen que pasar sin modificarse**. Que el agente haya ajustado
uno significa una de dos cosas, y las dos exigen un humano: cambió el comportamiento sin querer, o el
test estaba acoplado a la implementación (lo cual es un hallazgo legítimo, pero **es otra tarea**).

```bash
# En cada lote, antes de aceptarlo:
pytest apps/<modulo>/ -v --maxfail=3                     # verde
git diff --name-only <base>..HEAD | grep -E '(^|/)(tests?|test_|.*_test|.*\.test\.[jt]sx?)' \
  && echo "⛔ PARA: se tocaron tests en un refactor → no era un refactor" \
  || echo "✅ ningún test modificado"
```

#### G2 · El diff no se sale de la lista

```bash
# Los ficheros que el agente tocó, contra los que se le encargaron:
git diff --name-only <base>..HEAD | sort > /tmp/tocados.txt
comm -23 /tmp/tocados.txt <(sort /tmp/encargados.txt)
# Cualquier línea de salida = un fichero que nadie pidió → se para el lote y se mira
```

Un fichero de más no se perdona "porque el cambio era bueno". El valor del lote acotado es **poder
no leerlo entero** (§A6); en cuanto hay sorpresas, esa propiedad se pierde y hay que leerlo todo.

#### G3 · Un lote = un commit revisable

Ver §A4. El mensaje dice el lote y el total (`lote 2/4`), para que al volver se vea de un vistazo si
falta alguno.

#### G4 · Un reintento y se escala

De `parallelization.md` (DEC-5): si un lote falla, **un** reintento con el motivo registrado, y
después el error sube a una persona. Insistir con la misma estrategia rota quema presupuesto y no
cambia el resultado. En modo desatendido esto es lo que separa "amaneció a medias" de "amaneció con
cuarenta commits malos".

---

### A4. El tamaño del lote

El lote no lo decide la comodidad del agente: lo decide **cuánto es capaz de revisar de verdad una
persona de una sentada**. Un commit de 200 ficheros no se revisa, se aprueba.

| Naturaleza del cambio | Ficheros por commit | Por qué |
|---|---|---|
| Idéntico y trivial (añadir un argumento, un import) | 10–20 | El diff se escanea en diagonal y las anomalías saltan |
| Idéntico pero con variantes (mismo fix, contextos distintos) | 5–10 | Cada variante hay que mirarla |
| Mismo objetivo, aplicación distinta en cada sitio | 1–3 | Ya no es un lote: son N tareas pequeñas |

Regla práctica: **si al mirar el diff del lote no puedes decir en diez segundos que todos los cambios
son el mismo cambio, el lote es demasiado grande.**

---

### A5. Desatendido y nocturno — qué cambia

Delegar un refactor mecánico de noche es defendible, y es de los pocos trabajos que lo son. Lo que
cambia no es el permiso: es que **nadie va a leer un aviso hasta mañana**, así que todo lo que en
horario sería un "avísame" tiene que ser un "para".

1. **El criterio de parada se escribe, y es alcanzable.** `/goal` con una condición demostrable en la
   propia conversación (`goal-vs-loop.md`), no `/loop` sin fin.
2. **El gate deja de ser advisory.** Un **Stop hook** (nivel 3 de `verification.md`) que compruebe G1
   y G2 impide cerrar el turno con el lote sucio. Con el aviso documentado allí: a los **8 bloqueos
   consecutivos sin ninguna tool entre medias** el harness anula el hook y termina igual (el
   contador se reinicia con cada tool, así que un agente que sigue intentándolo no sale a los ocho),
   y el mensaje de bloqueo tiene que decir exactamente qué falta y cómo arreglarlo.
3. **Commit sí, push y merge no.** El trabajo se queda en la rama. `governance.md` §2 no se relaja
   porque sean las cuatro de la mañana — al contrario: es cuando más barato sale saltárselo.
4. **Presupuesto y tope de lotes**, o amaneces con el trabajo hecho y la factura también
   (`agent-security.md` ASI08).
5. **Un frente por fichero.** Si hay otro agente vivo, los ficheros del encargo se **reclaman** por
   escrito (`parallelization.md` §file claims). Dos refactors nocturnos sobre el mismo módulo no se
   resuelven en el merge: se resuelven no lanzándolos.

---

### A6. La revisión al volver — cómo se miran cuarenta commits sin leerlos todos

Aquí es donde el refactor delegado se gana o se pierde. Leer 400 ficheros no es revisar, es fingir
que revisas; y aprobar sin leer es peor. La salida no es leerlo todo ni leer nada: es **mirar la
forma antes que el contenido.**

En este orden, y los tres primeros son mecánicos:

```bash
# 1) ¿Hay algún cambio que no sea EL cambio? — la huella del diff
git diff --stat <base>..HEAD | tail -1          # total: ¿cuadra con lo esperado?
git diff <base>..HEAD | grep -c '^+'            # líneas añadidas
git diff <base>..HEAD | grep -c '^-'            # y quitadas: en un refactor mecánico
                                                #  la diferencia debería ser ~0 o muy regular

# 2) ¿Se tocó algo que no tocaba? — G1 y G2 de arriba, sobre el rango entero
# 3) ¿Qué cambios NO se parecen a los demás? — los raros, que son los que hay que leer
git diff <base>..HEAD --unified=0 | grep '^[+-]' | grep -vE '^(\+\+\+|---)' \
  | sort | uniq -c | sort -n | head -30
```

El paso 3 es el que hace el trabajo: en un refactor mecánico bien hecho, **las mismas líneas se
repiten cientos de veces** y la cola de frecuencia 1 es cortísima. Esa cola —los cambios que aparecen
una sola vez— es exactamente lo que hay que leer con los ojos. Suele ser una página de diff, no
cuatrocientas.

Y después de lo mecánico, lo que ninguna herramienta contesta:

4. **Coge tres ficheros al azar** y léelos enteros. No el diff: el fichero. Es la única forma de ver
   si el resultado quedó mejor o solo distinto (§A0).
5. **¿Quedó mejor?** Si el refactor tenía criterio, esta pregunta es el entregable, no un extra. Si
   la respuesta es "está igual pero movido", el refactor no valía su coste y conviene decirlo — es
   información para el siguiente encargo, no un reproche.

---

### A7. Lo que un agente no decide durante un refactor

Además de los 13 intocables de la Parte I (§3, arriba), que siguen
mandando enteros:

| No lo decide el agente | Por qué | Qué hace en su lugar |
|---|---|---|
| **Ampliar el alcance** ("ya que estaba, arreglé…") | Rompe G2 y con él la posibilidad de revisar por muestreo | Lo anota en una lista y sigue |
| **Tocar un test para que pase** | Si hace falta, no era un refactor (G1) | Para y reporta el test concreto |
| **Renombrar algo público** — endpoint, campo de API, clave, formato de un código | Es contrato con alguien de fuera (§3 de la Parte I, pregunta 4) | Ni lo propone dentro del lote |
| **"Arreglar" código raro sin buscar el porqué** | Suele ser deliberado: `// defensive:`, `// workaround: #N`, `// historical:` | `verdict-contract.md` §Intent: mira `git log -L` y, si no hay explicación, **pregunta**, no sentencia |
| **Migrar de paso a una API más nueva** | Es otro cambio, con otro riesgo y otra revisión | Lote aparte, encargo aparte |
| **Borrar código que "parece muerto"** | Casi siempre lo llama alguien que no aparece en el grep | Lo lista como candidato; el borrado es su propia tarea |

---

### A8. Límites honestos

- **Nada de esto detecta el refactor que salió peor**, solo el que salió roto (§A0). Para lo otro hay
  personas y está `rita-pattern-keeper`.
- **Los guardarraíles son comandos, no muros.** Mientras no vivan en un hook, se pueden saltar; y en
  modo desatendido el hook tiene el tope de 8 bloqueos, que se reinicia con cada tool (`verification.md` nivel 3).
- **`git diff --name-only` no ve lo que el agente hizo fuera de git** (mover ficheros a `/tmp`, tocar
  algo en otro directorio). El acotado real de ese riesgo es el sandbox y los permisos, no esta rule.
- **El muestreo del §A6 es muestreo**: reduce mucho la probabilidad de que se cuele algo, no la anula.
  A cambio, es lo único que la gente hace de verdad — y una revisión que se hace vale más que una
  exhaustiva que se salta.

---

### Anti-patterns del refactor delegado

- ❌ Delegar un refactor **sin tests del módulo** porque "es mecánico" → mecánico y no verificable no
  es delegable (§A1).
- ❌ Dar por buena una suite que **nunca se ha visto fallar** → sabotea una línea y compruébalo (§A1).
- ❌ Un encargo sin la lista de ficheros ni la línea `PROHIBIDO` → el agente rellena el hueco
  mejorando cosas que nadie pidió (§A2).
- ❌ Aceptar un lote donde **se tocó un test** → o cambió el comportamiento o el test estaba acoplado;
  las dos cosas requieren un humano (G1).
- ❌ Perdonar un fichero fuera de la lista "porque el cambio era bueno" → pierdes la propiedad que
  hacía revisable el lote (G2).
- ❌ Un commit de 200 ficheros → eso no se revisa, se aprueba (§A4).
- ❌ Reintentar tres veces el lote que falla en vez de escalar a la primera repetición (G4).
- ❌ Dejarlo corriendo de noche **sin criterio de parada y sin tope de lotes** (§A5).
- ❌ Que el agente haga push o merge de madrugada porque "ya estaba todo verde" (§A5).
- ❌ Dos agentes refactorizando el mismo módulo en paralelo y "ya lo arreglamos en el merge" (§A5).
- ❌ Revisar leyendo los 400 ficheros (no lo vas a hacer) o no leyendo ninguno (peor) → mira la forma
  del diff y lee la cola de frecuencia 1 (§A6).
- ❌ Declarar el refactor un éxito porque los tests están verdes, sin haber abierto un solo fichero
  para ver si quedó mejor (§A0, §A6.4).
- ❌ Empezar por aquí: **primero la Parte I** decide qué se toca y qué no. Esta parte
  solo dice cómo se entrega el encargo.

---

_Rule version: 2.0 · 2026-10-20 (LI-29, sub-ola 1.06): la Parte II es la antigua `refactor-asistido.md`
(v1.0 · 2026-08-08 · RFC-3: hacía ejecutables los guardarraíles que `governance.md` §3.1 enuncia
para el trabajo mecánico), renumerada §A0-§A8. · v1.0 · 2026-08-08 · RFC-1 (orden y lista de intocables,
destilada del informe de estilo de evo-preven §3) + RFC-2 (baseline ejecutable: `scripts/pattern_baseline.py`)._
