// /bug-sweep — Barrido de bugs en el codebase (loop-until-dry + verificación multi-lente)
//              + los bugs YA CONOCIDOS, todos clasificados por prioridad (antes el comando /fix-bugs)
//
// CUÁNDO: auditoría amplia de bugs sin lista previa; quieres encontrar el "tail" de bugs, no
//   solo los obvios. Y también para gestionar y arreglar los bugs que ya están reportados: lo hacía
//   el comando `/fix-bugs`, retirado el 2026-10-19 (LI-11) para que hubiera una sola puerta. Este
//   workflow los RECOGE, los PRIORIZA y devuelve el procedimiento de arreglo; quien arregla es la
//   sesión (el TL), no el workflow: un subagente de workflow corre en acceptEdits y sin input humano.
// COSTE: alto (loop de finders). APRUEBA antes de correr.
// ARGS: opcional — área/glob a barrer (default: todo el código fuente del proyecto). Ej: "src/api".
//   `conocidos` (o `conocidos src/api`): SOLO los bugs ya reportados, sin barrido — lo que hacía
//   /fix-bugs, al coste de dos agentes (recoger + clasificar) en vez del loop de finders.
// Mapea a la skill `verification-loops`.
//
// Patrón: loop-until-dry — rondas de finders en paralelo hasta K rondas sin findings nuevos;
//   cada bug fresco se verifica desde 3 lentes (correctitud / repro / seguridad).
//
// ── Lo que era /fix-bugs — Gestionar y arreglar bugs conocidos ──────────────────────────────────
// «Lee los bugs reportados y guía su resolución por prioridad.» Sus cuatro partes viven aquí:
//   · Fuentes de Bugs   → FUENTES (las lee la fase «Conocidos», antes del barrido)
//   · Clasificación     → PRIORIDADES (las aplica la fase «Clasificar», al final)
//   · Workflow por Bug  → COMO_ARREGLAR (va en el resultado: es lo que sigue el TL con cada bug)
//   · Anti-patterns     → ANTI_PATRONES (idem)

export const meta = {
  name: 'bug-sweep',
  description: 'Barrido exhaustivo de bugs por rondas hasta agotar, con verificación multi-lente, más los bugs ya reportados; todos clasificados P0/P1/P2 con el procedimiento de arreglo',
  whenToUse: 'Buscar bugs sin lista previa, o gestionar y arreglar los bugs conocidos (antes /fix-bugs): recoge los reportados, barre el código, verifica, prioriza y devuelve cómo arreglar cada uno. No arregla nada. args: área/glob (opcional); "conocidos" = solo los reportados, sin barrido.',
  phases: [{ title: 'Conocidos' }, { title: 'Find' }, { title: 'Verify' }, { title: 'Clasificar' }],
}

// Presupuesto (MO-74, sub-ola 2.18): `budget.total` es el «+Nk» que el Usuario pone al pedir el run, y es
// duro (al llegar, agent() lanza). Si no queda ni lo mínimo, no se arranca; el barrido, además, se para
// por rondas y por presupuesto (MAX_ROUNDS y `queda`, abajo).
if (budget.total && budget.remaining() < 50_000) {
  log(`Presupuesto: quedan ${budget.remaining()} tokens; no arranco`)
  return { exit_code: 2, error: 'presupuesto insuficiente' }
}


const RAW = (typeof args === 'string') ? args.trim() : ''
const SOLO_CONOCIDOS = /^conocidos\b/i.test(RAW)          // antes /fix-bugs: sin barrido
const AREA = RAW.replace(/^conocidos\b\s*/i, '')
const SCOPE = AREA || 'el código fuente del proyecto'
const FINDERS = ['lógica/correctitud', 'manejo de errores y edge cases', 'concurrencia/async y estado compartido']
const MAX_DRY_ROUNDS = 2
// Presupuesto (MO-74, sub-ola 2.18). El bucle de abajo corre «hasta que se seque», y un área con
// muchos bugs no se seca nunca: sin tope, solo lo paraba el límite de 1000 agentes del runtime. Con
// «+Nk» del Usuario (`budget.total`) se para antes de quedarse sin lo de la clasificación final; sin
// él, MAX_ROUNDS. Las dos paradas se dicen con log().
const MAX_ROUNDS = 6
const RESERVA = 60_000                       // tokens que se guardan para clasificar
const queda = (n) => !budget.total || budget.remaining() > n

// ## Fuentes de Bugs — según existan en el proyecto:
const FUENTES = [
  '`.claude/docs/tests/naive-test-*/REPORT.md` — Tests de usuarios no-técnicos (Lidia, Ramón, etc.) vía `naive-user-playthrough`',
  '`pending-tasks.md` del plan activo (`python3 .claude/scripts/tasks_registry.py list`) — peticiones T-NNN que sean bugs, o P0/P1 reabiertas (`[>]` con nota)',
  '`PROGRESS.json` → `notes[]` para bugs recientes',
  'Linear/GitHub issues (vía `mcp__github__*` si configurado)',
  '`.specify/sessions/*/tasks.md` — tareas pendientes marcadas como bug',
]

// ## Clasificación — presenta los bugs organizados por prioridad:
const PRIORIDADES = {
  P0: '### 🔴 P0 — CRITICAL (arreglar YA). Bugs que causan crash o pérdida de funcionalidad: ' +
      'Errores 500 en endpoints críticos · Pérdida de datos (delete accidental, DB corruption) · ' +
      'Crashes en frontend (pantalla blanca, ErrorBoundary ausente) · Security issues (auth bypass, SQL injection)',
  P1: '### 🟡 P1 — MEDIUM (próximo sprint). Bugs que afectan UX pero no bloquean: ' +
      'Estados inconsistentes en UI · Datos mal formateados · Performance degradada (>3s load time) · Accesibilidad rota',
  P2: '### 🟢 P2 — LOW (backlog). Mejoras menores: ' +
      'Textos de UI desactualizados · Falta onboarding para features nuevas · Mejoras estéticas no críticas',
}

// ## Workflow por Bug — para cada bug (lo hace el TL, en su sesión):
const COMO_ARREGLAR = [
  '1. Identificar archivo(s) afectado(s)',
  '2. Reproducir con Playwright (o test) si es UI',
  '3. Implementar fix',
  '4. Verificar con test unitario/E2E',
  '5. Screenshot after fix (si UI)',
  '6. Aplicar `verification-loops` como pre-DONE gate (canon: `rules/verification.md`)',
  '7. Actualizar PROGRESS.json y cerrar la petición: `python3 .claude/scripts/tasks_registry.py done T-NNN --nota "<qué se arregló>"`',
  '8. Si cambió UX — considerar re-lanzar `lidia-naive-tester` sobre la pantalla afectada',
]

// ## Anti-patterns
const ANTI_PATRONES = [
  '❌ Arreglar bugs sin reproducir primero (fix a ciegas)',
  '❌ Commitear el fix sin screenshot (si era UI)',
  '❌ Cerrar el bug sin actualizar REPORT.md / `pending-tasks.md` (`tasks_registry.py done`)',
  '❌ Marcar P0 como DONE sin tests unitarios nuevos',
]

const BUGS_SCHEMA = {
  type: 'object',
  properties: {
    bugs: {
      type: 'array',
      items: {
        type: 'object',
        properties: { key: { type: 'string' }, desc: { type: 'string' }, file: { type: 'string' }, line: { type: 'string' } },
        required: ['key', 'desc'],
      },
    },
  },
  required: ['bugs'],
}
const KNOWN_SCHEMA = {
  type: 'object',
  properties: {
    bugs: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          key: { type: 'string' }, desc: { type: 'string' }, file: { type: 'string' },
          line: { type: 'string' }, fuente: { type: 'string' },
        },
        required: ['key', 'desc', 'fuente'],
      },
    },
  },
  required: ['bugs'],
}
const VERDICT_SCHEMA = {
  type: 'object',
  properties: { real: { type: 'boolean' }, why: { type: 'string' } },
  required: ['real'],
}
const CLASS_SCHEMA = {
  type: 'object',
  properties: {
    items: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          key: { type: 'string' },
          prioridad: { type: 'string', enum: ['P0', 'P1', 'P2'] },
          por_que: { type: 'string' },
        },
        required: ['key', 'prioridad'],
      },
    },
  },
  required: ['items'],
}

const seen = new Set()
const confirmed = []
let dry = 0
let round = 0
let parada = null                    // por qué se paró el barrido antes de secarse (MO-74)

// 0) CONOCIDOS — los bugs que ya están reportados (antes /fix-bugs §Fuentes de Bugs). Van primero
//    y siembran `seen`, para que los finders no los vuelvan a "descubrir".
phase('Conocidos')
const known = await agent(
  `Recoge los bugs YA REPORTADOS de este proyecto (si el barrido está acotado a ${SCOPE}, quédate con ` +
  `los de esa área). Lee, según existan —si una fuente no existe, sáltala; NO inventes bugs—:\n` +
  FUENTES.map(f => `- ${f}`).join('\n') +
  `\nPor cada bug: key estable (file:symbol si se sabe; si no, el id de su fuente, p. ej. T-123), ` +
  `desc, file y line si constan, y fuente (cuál de las de arriba). NO arregles nada.`,
  { label: 'conocidos', phase: 'Conocidos', schema: KNOWN_SCHEMA })
const conocidos = ((known && known.bugs) || []).filter(b => b && b.key)
conocidos.forEach(b => seen.add(b.key))
// Las keys de los conocidos pueden ser ids de petición (T-123) y las de los finders file:symbol: con
// solo la key, el finder no sabría que es el mismo bug. Se le pasa también la descripción.
const YA_REPORTADOS = conocidos.map(b => `${b.key}${b.file ? ` (${b.file})` : ''}: ${String(b.desc).slice(0, 120)}`)
log(`Conocidos: ${conocidos.length}${SOLO_CONOCIDOS ? ' · modo «conocidos»: sin barrido' : ''}`)

while (!SOLO_CONOCIDOS && dry < MAX_DRY_ROUNDS) {
  if (round >= MAX_ROUNDS) { parada = `tope de ${MAX_ROUNDS} rondas sin secarse: puede haber más bugs`; log(`Paro: ${parada}`); break }
  if (!queda(RESERVA + 150_000)) { parada = `presupuesto: quedaban ${budget.remaining()} tokens en la ronda ${round}`; log(`Paro: ${parada}`); break }
  round += 1
  phase('Find')
  const found = (await parallel(FINDERS.map(lens => () =>
    agent(`Ronda ${round}. Busca BUGS en ${SCOPE} desde la lente "${lens}". Usa Read/Grep/Glob. NO repitas bugs ya conocidos: ${[...seen].join(' | ') || '(ninguno aún)'}${YA_REPORTADOS.length ? `. Ya reportados (aunque su key no sea file:symbol, son el mismo bug si describen lo mismo): ${YA_REPORTADOS.join(' | ')}` : ''}. Devuelve bugs concretos con key estable (file:symbol).`,
      { label: `find:${lens}`, phase: 'Find', schema: BUGS_SCHEMA })
  ))).filter(Boolean).flatMap(r => r.bugs || [])

  const fresh = found.filter(b => !seen.has(b.key))
  if (!fresh.length) { dry += 1; log(`Ronda ${round}: sin bugs nuevos (dry ${dry}/${MAX_DRY_ROUNDS})`); continue }
  dry = 0
  fresh.forEach(b => seen.add(b.key))

  phase('Verify')
  const judged = await parallel(fresh.map(b => () =>
    parallel(['correctitud', 'reproducibilidad', 'seguridad'].map(lens => () =>
      agent(`Juzga si este bug es REAL desde la lente ${lens} (escéptico): ${JSON.stringify(b)}`,
        { label: `verify:${lens}`, phase: 'Verify', schema: VERDICT_SCHEMA })))
      .then(votes => ({ bug: b, real: votes.filter(Boolean).filter(v => v.real).length >= 2 }))
  ))
  confirmed.push(...judged.filter(j => j.real).map(j => j.bug))
  log(`Ronda ${round}: ${fresh.length} frescos · confirmados acumulados: ${confirmed.length}`)
}

// 3) CLASIFICAR — antes /fix-bugs §Clasificación. Un solo agente, con los criterios escritos arriba.
phase('Clasificar')
const todos = [
  ...conocidos.map(b => ({ ...b, origen: 'conocido' })),
  ...confirmed.map(b => ({ ...b, origen: 'barrido' })),
]
let bugs = todos
if (todos.length) {
  const cls = await agent(
    `Clasifica cada bug por prioridad con ESTOS criterios, sin inventar otros:\n` +
    Object.values(PRIORIDADES).join('\n') +
    `\nBugs:\n${JSON.stringify(todos)}\nDevuelve, por cada key, su prioridad (P0|P1|P2) y una línea de por qué.`,
    { label: 'clasificar', phase: 'Clasificar', schema: CLASS_SCHEMA })
  const pri = new Map(((cls && cls.items) || []).map(x => [x.key, x]))
  bugs = todos.map(b => ({
    ...b,
    prioridad: (pri.get(b.key) || {}).prioridad || 'sin clasificar',
    por_que: (pri.get(b.key) || {}).por_que || '',
  }))
}
const ORDEN = { P0: 0, P1: 1, P2: 2 }
bugs.sort((a, b) => (ORDEN[a.prioridad] ?? 3) - (ORDEN[b.prioridad] ?? 3))

return {
  scope: SCOPE, rounds: round,
  parada,                                // null = se secó; si no, por qué se paró antes
  conocidos: conocidos.length, confirmed,
  bugs,                                  // conocidos + confirmados, P0 primero
  como_arreglar: COMO_ARREGLAR,          // el «Workflow por Bug» de /fix-bugs: lo sigue el TL
  anti_patrones: ANTI_PATRONES,
}
