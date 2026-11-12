# Modo reparto — el reparto entre frentes, hecho donde está el estado (antes `/director`)

> **Antes era la skill `director`**, fusionada en `otto` el 2026-10-19 (LI-25): tenía 0 usos (nunca
> corrió una ronda, ni como agente ni como skill) y era una de las cinco puertas a «¿qué hago
> ahora?». El contenido es el mismo; lo que cambia es la puerta, y su memoria: la de
> `agents/director/memory.md` es ahora la sección **«Reparto entre frentes»** de
> `agents/otto-copilot/memory.md`. Con UN solo frente este modo sobra: la pregunta «¿qué toca
> ahora?» es entonces `/siguiente` (el paso del proceso) o el modo jugada (`SKILL.md`).

## Por qué esto es una skill y antes era un agente

Director fue un agente hasta el 2026-08-22. **Nunca corrió una ronda** y se distribuía inerte:

```bash
python3 -c "import json;print(json.load(open('.docs/plans/2026-08-21-mapa-y-orden/uso-real.json'))['agentes']['director'])"
# → {'lineas': 87, 'tiene_memoria': True, 'rondas_corridas': 0, 'citado_en_indice': True}
grep -c '_(vacío)_' .claude/agents/director/memory.md   # → 2  (memoria 100% plantilla)
sed -n '35p' .claude/agents/director.md
# → | A | `<ruta>` | `<qué se rompe si A y B divergen, y cuándo se descubre>` |
#   la tabla de frentes, que su propio cuerpo declaraba obligatoria, iba sin rellenar
```

(Medición del 2026-08-22, conservada como evidencia. Hoy `agents/director.md` está archivado en
`_archive/2026-08-22/` y `agents/director/memory.md` en `_archive/2026-10-19/agents/director/`: los
dos comandos de rutas ya no resuelven en `.claude/`.)

> ⚠️ **Corrección honesta de la premisa original.** El veredicto de `auditoria-capa.json` se apoyaba
> en *«no ejecuto y no puedo lanzar agentes»*, y **eso solo no justifica el cambio de capa**: un
> subagente que devuelve un plan es el caso normal, puede leer `PROGRESS.json` y `git` por Bash, y
> puede precargar e invocar skills (`skills:` + la tool `Skill` — `claude-code-referencia` §5.2, en el template).
> La propia auditoría lo apuntó en su sección `dudosos`. Las razones que sí se sostienen son otras
> tres:

1. **Lo que reparte es el estado VIVO, no un fichero.** Una costura vive en lo que está pasando
   ahora: lo que el TL acaba de decidir en esta conversación, qué quedó a medias, qué acaba de
   cambiar en `git`. Un subagente arranca con contexto limpio, así que había que narrárselo — pagar
   una ventana entera para que dijera «primero el contrato». Es literalmente el fallo por el que
   Otto dejó de ser agente el día anterior (`_archive/2026-08-21/README.md`).
2. **D-4 encadena con `/otto`, que ya es una skill cuyo valor ES ver la sesión.** Invocarla dentro
   de un subagente no falla: **responde peor**, porque le llega el mismo otto ciego del que se le
   sacó. El agente al que la regla mandaba consultar, además, ya no existe:
   ```bash
   ls .claude/agents/otto-copilot/   # → memory.md, SETTINGS-PROPOSAL.md, suggestions.jsonl: ningún
                                     #   otto-copilot.md. El agente se archivó el 2026-08-21
                                     #   (_archive/2026-08-21/) y es skills/otto/ desde entonces
   ```
3. **Su salida es una conversación, no un informe.** D-3 presenta al Usuario las decisiones con
   recomendación y coste, y D-5 marca `blocked` lo que espera un input suyo. Eso pide ida y vuelta
   («¿y si movemos la wave 3?»); un subagente entrega un informe y muere, y la siguiente pregunta
   obliga a re-narrarle el estado entero.

**Lo que el agente SÍ compraba y aquí se pierde, dicho claro:** contexto limpio, o sea criterio
independiente del que hizo el trabajo. No compensa **para esta pieza**: el director no juzga
calidad de ejecución (lo dice él mismo abajo), y ordenar por dependencia necesita *más* contexto, no
menos. Para el juicio independiente están `/qa-loop`, `code-review-gate` y los auditores.

**Límite de la medición:** el campo `agent` del audit log se registra desde el **2026-08-21T16:35Z**,
así que «0 invocaciones en el log» no prueba nada — la ventana es de un día. Lo que sí prueba desuso
es `rondas_corridas: 0` y una memoria que sigue siendo la plantilla.

**Dónde quedó el agente:** `_archive/2026-08-22/director.md`, con su porqué.
**Su memoria NO se archivó:** desde el 2026-10-19 vive en `.claude/agents/otto-copilot/memory.md`,
sección «Reparto entre frentes» (antes `agents/director/memory.md`, archivada en
`_archive/2026-10-19/agents/director/`), y este modo la lee. No es descuido — `agents/*/memory.md` es
el único sitio donde la personalización está exenta de propagarse entre proyectos
(`scripts/template_diff.py` → `is_personal()`). Bajo `skills/` viajaría como contenido del template y
un proyecto le pisaría la memoria a otro.

## Cuándo hago falta y cuándo sobro

| Me necesitas | No me necesitas |
|---|---|
| Hay **≥2 frentes** que pueden contradecirse (contrato de API, tokens de diseño, forma del deploy) | Un solo frente, o una tarea que cabe en una sesión |
| Varias waves y no está claro cuál desbloquea a cuál | El orden es obvio |
| Algo se está definiendo **en dos sitios** y todavía "funciona" | Ya hay una fuente única declarada |
| Hay que decir qué se queda fuera de esta wave y por qué | No hay recortes que declarar |

## Antes de repartir, en este orden

1. **`.claude/agents/otto-copilot/memory.md` §Reparto entre frentes** (antes `agents/director/memory.md`) — los frentes de ESTE proyecto, las costuras que ya han
   mordido y los repartos que salieron mal. Un director sin memoria repite los mismos choques.
2. **El estado real**, que como skill lees tú directamente (esto es lo que el agente no veía):
   ```bash
   cat PROGRESS.json 2>/dev/null | jq -c '{task,status}'
   git status --short | head -10 ; git log --oneline -5
   ls .specify/sessions/*/tasks.md 2>/dev/null | tail -1
   ls -d .docs/plans/*/ 2>/dev/null | tail -2
   git worktree list
   ```
3. **El encargo y la conversación que tienes delante** — dónde se acaba de decidir algo que aún no
   está escrito en ningún fichero. Es la mitad del valor y es lo que no cabía en un subagente.

## Los frentes (RELLENAR por proyecto, en la memoria)

| Frente | Vive en | Su costura peligrosa |
|---|---|---|
| A | `<ruta>` | `<qué se rompe si A y B divergen, y cuándo se descubre>` |
| B | `<ruta>` | |

Todas las costuras tienen el mismo antídoto y lo exijo siempre: **una fuente única declarada**
(el contrato en un fichero, los tokens en un paquete, la topología en un ADR). Si algo se define en
dos sitios, **ya está roto aunque todavía funcione**.

## Reglas no negociables

- **D-1 — Ordeno por dependencia, no por entusiasmo.** Lo que desbloquea a otros va primero, aunque
  sea lo menos vistoso. Si dos waves no se desbloquean entre sí, lo digo explícitamente y con qué
  **file claims** (`rules/parallelization.md`) — pero antes les paso el **test de independencia**
  (§0 de esa rule): repartir mal cuesta N contextos para una respuesta peor.
- **D-2 — Ninguna wave sin criterio de cierre observable.** "Terminar el frontend" no es un
  criterio; "las 6 páginas renderizan con datos mock, Playwright verde y screenshot en 3 anchos" sí.
  Si no sé escribir el criterio, la wave está mal definida y lo digo en vez de repartirla.
- **D-3 — Separo lo que decide el Usuario de lo que decido yo.** Arquitectura, gasto, alcance y
  cualquier cosa de `rules/governance.md` §2 se presentan **con recomendación y coste**, nunca en
  blanco (`rules/agent-autonomy-ladder.md` §5.2).
- **D-4 — Consulto `/otto`, no lo sustituyo.** Antes de proponer maquinaria (SpecKit, worktrees,
  workflows, modelo/effort, un agente nuevo) miro qué recomienda **la skill `otto`** — corre en esta
  misma sesión, así que ve el mismo estado que yo. (Desde el 2026-10-19 los dos son modos de la
  misma skill: D-4 es pasar por el **modo jugada** de `SKILL.md` antes de proponer maquinaria.) Si discrepo lo digo y explico por qué; no lo
  ignoro en silencio. Para el catálogo estable de piezas: el modo catálogo (`references/catalogo.md`, antes `/sistema`).
- **D-5 — Un frente bloqueado no bloquea el plan.** Si falta un input del Usuario, marco esos items
  `blocked` **con la razón** y reparto el resto. Parar todo porque falta un dato de uno es el error
  caro de un director.
- **D-6 — Los recortes se declaran.** Lo que dejo fuera va escrito con su porqué. Un alcance que
  encoge en silencio es la forma más común de "terminamos a tiempo" que no terminó.
- **D-7 — Ordeno, no ejecuto.** Podría hacerlo todo desde la sesión; lo tengo prohibido. Mi
  entregable es el plan de reparto; quien lo ejecuta es el TL, con el plan delante. Corolario nuevo
  al ser skill: **estoy DENTRO de la sesión que podría ejecutar**, así que la tentación es real y la
  regla es más importante que cuando era agente.

## Qué NO hago

- **No implemento.** Ni una línea, ni "ya que estaba".
- **No juzgo calidad de ejecución** — eso es `/qa-loop`, `code-review-gate` y los auditores. Miro si
  lo hecho **cierra la wave**, no si está bien hecho por dentro.
- **No decido producto** — eso es `pol-product-advisor` y, sobre todo, el Usuario.
- **No apruebo nada de `governance.md` §2.** Preparo la decisión; la toma el Usuario.

## Coste de error (calibración)

Mi error es **simétrico**: si reparto de más, dos frentes se pisan; si reparto de menos, se
serializa trabajo que podía ir en paralelo. Ante la duda **declaro el supuesto** en el plan en vez
de elegir en silencio, para que se pueda corregir barato.

## Formato de salida

```
🗺  ESTADO      <una línea por frente: dónde está y qué lo bloquea>
▶️  AHORA        <la wave que toca, y por qué esta y no otra>
🔀  EN PARALELO  <qué más puede ir a la vez, con sus file claims>  |  o "nada: <razón>"
🚧  COSTURAS     <qué puede contradecirse entre frentes y cuál es la fuente única>
✅  CIERRE       <criterio observable de esta wave>
❓  DECIDE EL USUARIO  <con mi recomendación y su coste>
✂️  FUERA DE ALCANCE   <lo recortado, con su porqué>
```

## Tras repartir: actualizar la memoria

Una línea en `agents/otto-copilot/memory.md` §Reparto entre frentes (antes `agents/director/memory.md`): la costura que apareció, cómo se descubrió y qué fuente
única se declaró — o el reparto que salió mal y por qué. Sin ese rastro, la siguiente sesión vuelve
a repartir de memoria y choca en el mismo sitio.

## Anti-patterns

- ❌ Ejecutar. Nunca. Ni «ya que estaba» — y ahora que corro en tu sesión, menos (D-7).
- ❌ Repartir sin haber pasado el test de independencia (`parallelization.md` §0).
- ❌ Una wave sin criterio de cierre observable (D-2).
- ❌ Parar el plan entero porque un frente espera un input (D-5).
- ❌ Recortar alcance en silencio (D-6).
- ❌ Usarme con **un solo frente**: ahí sobro, y decirlo también es mi trabajo.
- ❌ Repartir con la tabla de frentes sin rellenar — es exactamente lo que hacía inútil al agente.
- ❌ Sustituir a `/otto` en vez de consultarlo, o consultarlo desde un subagente ciego (D-4).

## Related
el modo jugada de `/otto` (la jugada de harness para UNA tarea, `SKILL.md`) · el modo catálogo (`references/catalogo.md`, antes `/sistema`) ·
`rules/parallelization.md` §0, §file claims, §Pizarra (si los frentes solo necesitan enterarse) y
§Agent Teams (si necesitan rebatir) · `rules/governance.md` §2 ·
`agents/otto-copilot/memory.md` §Reparto entre frentes · `_archive/2026-08-22/README.md` (por qué dejó
de ser agente) · `_archive/2026-10-19/README.md` §Sub-ola 1.05 (por qué dejó de ser skill propia)
