// /codebase-map — Mapa de arquitectura del repo (lectores en paralelo → síntesis)
//
// CUÁNDO: onboarding a un repo grande/desconocido; quieres un mapa de subsistemas, entry points
//   y hot paths sin leerlo todo tú. COSTE: medio. APRUEBA antes de correr.
// ARGS: opcional — lista de subsistemas/dirs a mapear (CSV). Default: descubre los top-level dirs.
// Mapea a la skill `codebase-onboarding`. Buen primer paso antes de `plan-research`.
//
// Patrón: scout inline (descubre subsistemas) → fan-out (un lector por subsistema) → síntesis.

export const meta = {
  name: 'codebase-map',
  description: 'Mapea la arquitectura del repo: subsistemas, entry points, hot paths y dependencias',
  phases: [{ title: 'Scout' }, { title: 'Read' }, { title: 'Synthesize' }],
}

// Presupuesto (MO-74, sub-ola 2.18): `budget.total` es el «+Nk» que el Usuario pone al pedir el run, y es
// duro (al llegar, agent() lanza). Si no queda ni lo mínimo, no se arranca; sin él, mandan los topes
// de este script (sus .slice y el tamaño de sus entradas).
if (budget.total && budget.remaining() < 50_000) {
  log(`Presupuesto: quedan ${budget.remaining()} tokens; no arranco`)
  return { exit_code: 2, error: 'presupuesto insuficiente' }
}


const SUBSYS_SCHEMA = {
  type: 'object',
  properties: {
    subsystem: { type: 'string' },
    purpose: { type: 'string' },
    entry_points: { type: 'array', items: { type: 'string' } },
    key_files: { type: 'array', items: { type: 'string' } },
    depends_on: { type: 'array', items: { type: 'string' } },
  },
  required: ['subsystem', 'purpose'],
}

// 1) SCOUT — descubrir los subsistemas (o usar los pasados por args)
phase('Scout')
let subsystems
if (typeof args === 'string' && args.trim()) {
  subsystems = args.split(',').map(s => s.trim()).filter(Boolean)
} else {
  const scout = await agent(
    'Lista los subsistemas/áreas top-level de este repo (usa Glob/Read sobre la raíz, package.json, etc.). Devuelve SOLO una lista de nombres de directorio/área, uno por línea, máx 12.',
    { label: 'scout', phase: 'Scout' }
  )
  subsystems = String(scout).split('\n').map(s => s.replace(/^[-*\d.\s]+/, '').trim()).filter(Boolean).slice(0, 12)
}
log(`Subsistemas a mapear: ${subsystems.join(', ')}`)

// 2) READ — un lector por subsistema, en paralelo
phase('Read')
const maps = (await parallel(subsystems.map(s => () =>
  agent(`Explora el subsistema/área "${s}" del repo (Read/Grep/Glob). Describe su propósito, entry points, ficheros clave y de qué otros subsistemas depende. Sé conciso y concreto con paths.`,
    { label: `read:${s}`, phase: 'Read', schema: SUBSYS_SCHEMA })
))).filter(Boolean)

// 3) SYNTHESIZE — mapa de arquitectura + hot path
phase('Synthesize')
const map = await agent(
  `Sintetiza un MAPA DE ARQUITECTURA del repo a partir de estos subsistemas:\n${JSON.stringify(maps, null, 2)}\n\nEntrega: (1) diagrama textual de relaciones entre subsistemas, (2) entry points principales, (3) el "hot path" más importante, (4) riesgos/zonas frágiles. Apto para onboarding o como insumo de /plan-research.`,
  { label: 'synthesize', phase: 'Synthesize' }
)

return { subsystems, maps, architecture: map }
