---
paths:
  - ".claude/agents/**"
---
# Escalera de autonomía del agente — promoción, no-delegables y escalado por incertidumbre

> **Cuándo aplicar:** al **crear un agente nuevo** (decidir en qué fase entra), al **darle o quitarle
> voz** a uno existente (salir de modo sombra, dejar que comente en PRs, dejarlo correr sin revisión),
> y al **diseñar cómo pide ayuda** cuando duda. Es el eje de PROCESO que falta en `governance.md`.
>
> **NO aplicar:** para decidir si una ACCIÓN concreta necesita aprobación (deploy, merge a main,
> migración destructiva) — eso es el catálogo de `governance.md` §2, y sigue mandando. Tampoco para
> tareas de un solo turno sin agente dedicado.
>
> **Relacionado:** `governance.md` (§2 catálogo de acciones · §3 los 3 niveles del TL · §3.1 autonomía
> por tipo de tarea), `plan-gates.md` (Gate 0b: clarificación inversa antes de planear),
> `verdict-contract.md` (`review`/`blocked` en la SALIDA; aquí gobernamos la INTERRUPCIÓN en curso),
> `parallelization.md` (§Agent Teams, §Pizarra), `self-improvement-loop.md`, `agents/README.md`.

---

## 1. Los tres ejes de autonomía (no se sustituyen — se cruzan)

| Eje | Dónde vive | Qué responde | Quién lo mueve |
|---|---|---|---|
| **Acción** | `governance.md` §2 | ¿esta acción concreta necesita OK? | Está pre-declarado, no se negocia por tarea |
| **Estado del TL** | `governance.md` §3 | ¿en qué nivel opera hoy este Tech Lead? | El Supervisor/Usuario lo **declara** |
| **Fase del agente** (esta rule) | aquí | ¿qué ha **demostrado** este agente para merecer más cuerda? | Se **gana** con evidencia, se pierde con fallos |

Los tres niveles de `governance.md` describen el **estado actual**; la escalera describe **el proceso
para cambiarlo**. Un agente en fase 2 dentro de un TL `Autonomous` sigue siendo fase 2.

## 2. La escalera — 4 fases

Adaptada del framework de delegación efectiva (I DO/YOU WATCH → … → YOU DO). El caso de casa:
**Rita (`rita-pattern-keeper`) arrancó en "modo sombra" — eso ES la fase 3**, se inventó por instinto
y no estaba nombrada. Nombrarla la hace reutilizable para todo agente nuevo.

| Fase | Nombre | Qué hace el agente | Qué hace el humano/TL | Ejemplo en casa |
|---|---|---|---|---|
| **1** | **I DO · YOU WATCH** | Observa. Se le pasa trabajo ya hecho y produce su salida **contra un resultado conocido** (replay) | Hace el trabajo y compara | Un auditor nuevo re-audita una wave ya cerrada y se contrasta con el `REPORT.md` real |
| **2** | **I DO · YOU DO** | Trabaja **a la vez** que el humano sobre el mismo input; se comparan las dos salidas | Trabaja en paralelo y revisa las diferencias | Pol revisando un plan que el TL ya revisó |
| **3** | **YOU DO · I WATCH** (**modo sombra**) | Trabaja solo de principio a fin y **escribe su informe**, pero su salida **no tiene efecto**: no comenta PRs, no bloquea, no cierra tareas | Lee el informe y anota qué habría aplicado | **Rita hoy** → `.docs/feedback/rita/<fecha>/REPORT.md` + `patterns/telemetry.jsonl` |
| **4** | **YOU DO** | Trabaja y su salida **tiene efecto** dentro de su ámbito declarado | Revisa por muestreo y en los gates de `governance.md` §2 | Los auditores del `/qa-loop`, cuyo score cuenta para el gate |

**La responsabilidad no se delega.** Sube la fase de un agente y sigue siendo tuyo el resultado; por
eso las fases existen (y por eso no se salta ninguna con prisa).

## 3. Criterios de paso — qué hay que demostrar

Los umbrales son **defaults para calibrar, no métricas automáticas**: los evalúa el Usuario leyendo
la evidencia. Lo que la rule fija es **que haya evidencia y que esté escrita**, no el número exacto.

| Paso | Evidencia mínima (default) | Dónde vive la evidencia |
|---|---|---|
| 1 → 2 | 2 replays sobre trabajo ya cerrado sin contradecir el resultado conocido | informe del agente + nota en su `memory.md` |
| 2 → 3 | 3 rondas en paralelo con **≥1 hallazgo propio útil** que el humano no tenía, y **0 hallazgos falsos de severidad alta** | `memory.md` (sugerencias vivas) + `trend.json` |
| 3 → 4 | **N=5 rondas en sombra** con address-rate simulado alto (hallazgos que el equipo habría aplicado / total) y sin falso positivo de severidad alta | `telemetry.jsonl` del agente / `trend.json` |
| Degradación | **1 incidente** causado por su salida, o 2 rondas seguidas con FP de severidad alta → baja una fase | anotar el porqué en su `memory.md` |

**El «0 hallazgos falsos» de un auditor visual se mide, no se estima:** `scripts/calibrar_auditor.py
<fixture> <findings.json>` compara sus hallazgos con los defectos plantados de `smoke/calibracion/`
(`A-limpio`, `B-landing`) y da **recall**, **falsos positivos** y **trampas condenadas** (defectos
aparentes con su razón escrita al lado: condenarlos es un FP). La clave vive fuera del proyecto
(`~/.claude/calibracion-diseno/`) y la crea `smoke/calibracion/plantar.py`; sin ella el script sale con
2 y lo dice, no con un 0 % que parezca bueno (comprobado el 2026-10-21). Para los auditores de código
(Roberto, Pilar) el fixture es `smoke/calibracion/auditores/` (`montar.py`) y la clave se pasa con
`--clave`; un hallazgo `nit` o `pre-existing` fuera de la clave sale aparte y lo adjudica una persona.

Reglas del proceso:

1. **Quién decide:** el Usuario (o el Supervisor si el Usuario lo delegó **por escrito** para ese agente).
   Un agente **nunca** se auto-promociona — igual que un TL nunca auto-escala su nivel.
2. **La fase se escribe** en la ficha del agente (`.claude/agents/<agente>.md`) y en su `memory.md`.
   Para un agente **nuevo**, si no está escrita se asume **fase 3** (sombra: reporta, no tiene efecto).
   ⚠️ Esto **no degrada retroactivamente** a la flota existente: los agentes que ya operan con efecto
   (los del `/qa-loop`, por ejemplo) están de facto en fase 4 y se les anota la fase al tocarlos por
   otra razón — boy-scout, no una migración masiva. Cuando se escribió esto solo tres la llevaban
   escrita (`rita-pattern-keeper` 3, `ignacio-roig` 4, `pol-product-advisor` 4); el recuento vivo,
   agente por agente, es la tabla generada de `agents/README.md` §0 (el 2026-10-20, todos).
3. **La promoción es por ámbito, no global**: se puede dar fase 4 en "detectar `description:` que falta"
   y mantener fase 3 en "juzgar si un patrón nuevo aplica".
4. **La degradación no es un castigo, es información**: si un agente baja de fase, el fallo suele
   estar en su contrato (input mal acotado), no en el modelo.

## 4. Qué NO se delega a la IA — lista dura

No es un catálogo de acciones peligrosas (ese es `governance.md` §2): son **clases de trabajo** que no
entran en la escalera en ninguna fase.

| No delegable | Por qué | Qué se hace en su lugar |
|---|---|---|
| **Confidencial** — secretos, credenciales, datos personales reales, contratos, datos de clientes | El blast radius de una prompt injection o de un log accidental no se revierte; el sandbox limita el daño pero **no previene la inyección** | Datos sintéticos o de-identificados; el agente trabaja contra un esquema, nunca contra la tabla real (`rules/security.md`) |
| **Urgente sin tiempo de verificar** — hotfix en producción, incidente en curso | Delegar exige explicar y **verificar**; si no hay tiempo para lo segundo, no es delegación, es apostar | Lo hace el humano; el agente ayuda en paralelo (diagnóstico, búsqueda) sin escribir en producción. Post-mortem después (`governance.md` §8) |
| **Alto riesgo con un agente no preparado** — agente recién creado, sin memoria, sin patrones del repo, o fuera de su dominio declarado | Es la combinación que produce el fallo caro: máxima libertad con mínimo contexto | Fase 1-2 primero, sobre trabajo de bajo riesgo, hasta que su `memory.md` tenga contenido real |

Corolario práctico: **un agente nuevo nunca nace en fase 4**, por bueno que parezca el prompt.

---

## 5. Escalado iniciado por el agente — parar por INCERTIDUMBRE o SEVERIDAD

`governance.md` §2 cubre lo previsible: "vas a hacer X, pide permiso". No cubre el caso caro: el
agente **no sabe que lo que va a hacer es peligroso** porque no entendió el encargo. Este es el freno
que falta, y es **el agente quien lo acciona**.

### 5.1 Disparadores de parada (cualquiera basta)

**Por incertidumbre:**
- No entiendo el objetivo, solo el procedimiento (sé qué teclear, no qué se quiere conseguir).
- Hay **dos interpretaciones razonables** del encargo y llevan a resultados distintos.
- El encargo asume un dato que no tengo y que estoy a punto de **suponer** (nombre de módulo, formato,
  destinatario, umbral). Esto es el Gate 0b de `plan-gates.md` aplicado en mitad de la ejecución.
- Estoy fuera de mi dominio declarado (un auditor de estilo opinando de criptografía).

**Por severidad:**
- Lo que voy a tocar afecta a **datos reales** y no tengo forma de verificar el resultado.
- El error sería **silencioso** (nadie se enteraría hasta mucho después): backfill, borrado lógico,
  cambio de umbral, migración de datos, texto que sale a un cliente.
- El cambio es **irreversible** o caro de revertir, y no está en el catálogo de §2 (por eso nadie
  puso un gate).
- Mi propia confianza es baja **y** el coste de equivocarme es alto (ver §6).

### 5.2 Formato obligatorio: escalado CON propuesta

Un agente que pregunta demasiado, o que pregunta en blanco, es inútil — se vuelve un formulario. La
regla es: **nunca preguntes sin traer tu mejor respuesta y el coste de acertar o fallar.**

```
⏸ PARO — <incertidumbre|severidad> · <una línea: qué estaba haciendo>
🤔 LA DUDA      <la ambigüedad concreta, no "no estoy seguro">
🎯 MI PROPUESTA <lo que haría si tuviera que decidir ahora> — confianza <alta|media|baja>
🔀 LA OTRA      <la interpretación alternativa y en qué cambia el resultado>
💥 SI ME EQUIVOCO <consecuencia concreta y si es reversible>
✅ QUÉ NECESITO <la respuesta mínima que me desbloquea: "confírmame A" / un dato>
```

Reglas: (1) **una sola parada por duda**, agrupando lo que se pueda responder junto; (2) mientras
esperas, **sigue con lo que no depende de la respuesta** y dilo; (3) si la duda se resuelve leyendo
código o docs, **no es una parada** — léelo; (4) si nadie responde y el trabajo es reversible, ejecuta
tu propuesta, **anótala como supuesto** y márcalo en el informe.

## 6. Coste de error — cada agente declara qué error le sale caro

Un falso negativo de una pentester (no ve el agujero) y un falso positivo de una auditora de estilo
(marca como error algo deliberado) son fallos de naturaleza opuesta, y hoy todos los agentes se
calibran igual: contra inflación de nota. Falta el eje de **asimetría**.

| El error caro es… | Cómo sesga el umbral | Qué hace de más | Ejemplos en casa |
|---|---|---|---|
| **Falso negativo** (se me escapa) | Umbral **bajo**: ante la duda, reportar | Acepta ruido; su informe marca la confianza de cada hallazgo | `sofia-pentester`, `priya-privacy-auditor`, `rafa-retrieval-engineer`, `marco-qa-breaker`, `ignacio-roig` (adversarial por diseño: baseline 3.0, ≥10 findings) |
| **Falso positivo** (marco lo correcto) | Umbral **alto**: ante la duda, callar | Exige evidencia dura antes de hablar (Rita: ≥2 precedentes `file:line` o silencio) | `rita-pattern-keeper`, `code-review-gate` y cualquier gate que **bloquee** (un FP para el trabajo de otro) |
| **Simétrico** | Umbral medio; el sesgo lo pone el contexto de la tarea | Declara en cada informe qué asumió | `pol-product-advisor`, `/otto` |

**Antes de condenar, pregunta la intención.** El antídoto del falso positivo es asumir que lo raro
puede ser deliberado: código defensivo, workaround, decisión histórica (la lista *What NOT to Change*
de `/simplify`). Si no puedes distinguir intención de descuido, el veredicto es `review`, no `notdone`.

### 6.1 Dónde se declara (verificado — leer antes de copiar)

Se declara en **dos sitios**, y esto no es redundancia:

```yaml
# .claude/agents/<agente>.md — frontmatter (inventario y tooling)
error_cost: false-negative      # false-negative | false-positive | symmetric
autonomy_phase: 3               # 1..4 — ver §2; si falta, se asume 3 (sombra)
```

```markdown
## Coste de error (calibración)
Mi error caro es el **falso negativo**: si no veo un agujero, alguien lo explota. Ante la duda
REPORTO, marcando la confianza. Acepto ruido; no acepto silencio.
```

⚠️ **Por qué los dos.** El frontmatter de un subagente es **configuración**: el harness lee las claves
que conoce (`name`, `description`, `tools`, `model`, `skills`…) e **ignora las demás**; lo que llega al
agente como prompt es el **cuerpo** del fichero. Así que una declaración que viva solo en el
frontmatter **no cambia el comportamiento del agente** — solo sirve para inventario. Precedente en
casa: `shared_utils_version:` es exactamente eso, una clave propia que ninguna herramienta lee y que
mantiene una convención escrita en `agents/README.md`. Por tanto: frontmatter para poder listar y
auditar la flota; **cuerpo para que el agente se calibre de verdad**.

## 7. Checklist — agente nuevo

```
[ ] Fase inicial declarada (1 o 2; nunca 4) en la ficha + memory.md
[ ] Criterio de paso a la fase siguiente escrito, con dónde vivirá la evidencia
[ ] error_cost declarado en frontmatter Y en el cuerpo (§6.1)
[ ] Dominio declarado: qué SÍ juzga y qué NO (la línea "no soy…")
[ ] Disparadores de parada de §5 aplicables a su dominio
[ ] Ninguna de las 3 clases no-delegables de §4 entra en su ámbito
[ ] memory.md creada (aunque sea vacía) — un agente sin memoria está en fase 1
[ ] Las 4 condiciones de alta de `audit-team.md` §6b (juicio propio, error_cost, fixture si es juez,
    owner:) — `python3 .claude/scripts/fleet_policy.py`
```

---

## Anti-patterns

- ❌ Estrenar un agente en fase 4 porque "el prompt quedó muy bien" → es la combinación de §4: máxima
  libertad, mínimo contexto.
- ❌ Declarar la fase y no escribir el criterio de paso → la escalera vuelve a ser una etiqueta a dedo,
  que es justo lo que ya teníamos.
- ❌ Un agente que se auto-promociona ("ya llevo varias rondas bien, empiezo a comentar en PRs").
- ❌ Escalar en blanco ("no sé qué hacer, ¿me dices?") → §5.2 exige propuesta, alternativa y coste.
- ❌ Parar por algo que se resuelve leyendo un fichero → eso no es incertidumbre, es pereza.
- ❌ Declarar `error_cost` solo en el frontmatter y esperar que cambie el comportamiento (§6.1).
- ❌ Dar los mismos permisos a "convertir sintaxis" y a "diseñar la lógica de negocio" → eso lo
  gradúa `governance.md` §3.1, no esta rule.

---

_Rule version: 1.0 · AGT-2 + AGT-3 (adopción AI4DEVS, 2026-08-08)_
