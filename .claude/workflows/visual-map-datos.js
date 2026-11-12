// /visual-map-datos — Genera los DATOS de los mapas visuales del plan desde código real.
//
// NOMBRE (2026-10-19, LI-11): hasta hoy este fichero era `visual-map.js` y se registraba como
//   `/visual-map`, el MISMO nombre que el comando `commands/visual-map.md`. Con dos piezas del mismo
//   nombre, cuál corría dependía de la precedencia. Ahora: `/visual-map` es el comando (el
//   procedimiento entero: datos → plantillas → render) y este workflow es su motor de datos.
//
// CUÁNDO: tarea grande / gate de plan; quieres regenerar los diagramas multi-página
//   (.claude/templates/html/{architecture,data-model,user-flows}.html) a partir del repo
//   en vez de a mano. COSTE: medio. APRUEBA antes de correr.
// ARGS: opcional — lista de subsistemas/dirs a mapear (CSV). Default: descubre top-level dirs.
// Hermano de `codebase-map.js`: mismo patrón scout→read→synthesize, pero la SÍNTESIS emite
//   objetos JSON listos para PEGAR en las plantillas HTML.
//
// SALIDA (return): { NODES, EDGES, ENTITIES, RELATIONS, FLOWS }
//   - NODES/EDGES        → pegar en architecture.html  (const NODES / const EDGES)
//   - ENTITIES/RELATIONS → pegar en data-model.html    (const ENTITIES / const RELATIONS)
//   - FLOWS              → pegar en user-flows.html     (const FLOWS)
// El agente abre cada plantilla, reemplaza el bloque "EDITA AQUÍ", guarda el set en
//   .docs/plans/<plan>/ o .claude/docs/html/, y verifica el render (python3 -m http.server).

export const meta = {
  name: 'visual-map-datos',
  description: 'Mapea el repo y emite NODES/EDGES + ENTITIES/RELATIONS + FLOWS para las plantillas HTML del plan',
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
    models: { type: 'array', items: { type: 'string' } },     // modelos/tablas que define
    routes: { type: 'array', items: { type: 'string' } },     // endpoints/rutas que expone
    depends_on: { type: 'array', items: { type: 'string' } },
  },
  required: ['subsystem', 'purpose'],
}

// 1) SCOUT — descubrir subsistemas + modelos/rutas (o usar los pasados por args)
phase('Scout')
let subsystems
if (typeof args === 'string' && args.trim()) {
  subsystems = args.split(',').map(s => s.trim()).filter(Boolean)
} else {
  const scout = await agent(
    'Lista los subsistemas/áreas top-level de este repo (Glob/Read sobre raíz, package.json, manage.py, apps/, settings de rutas). Devuelve SOLO nombres de directorio/área, uno por línea, máx 12.',
    { label: 'scout', phase: 'Scout' }
  )
  subsystems = String(scout).split('\n').map(s => s.replace(/^[-*\d.\s]+/, '').trim()).filter(Boolean).slice(0, 12)
}
log(`Subsistemas a mapear: ${subsystems.join(', ')}`)

// 2) READ — un lector por subsistema, en paralelo (incluye modelos y rutas para el mapa de datos/flujos)
phase('Read')
const maps = (await parallel(subsystems.map(s => () =>
  agent(`Explora el subsistema/área "${s}" (Read/Grep/Glob). Reporta: propósito, entry points, MODELOS/tablas que define (con sus campos clave y FKs), RUTAS/endpoints que expone, y de qué otros subsistemas depende. Sé conciso y concreto con paths.`,
    { label: `read:${s}`, phase: 'Read', schema: SUBSYS_SCHEMA })
))).filter(Boolean)

// 3) SYNTHESIZE — emitir los 3 datasets como JSON pegable en las plantillas
phase('Synthesize')
const instructions = `
A partir de estos subsistemas:\n${JSON.stringify(maps, null, 2)}\n
Devuelve UN JSON con exactamente estas claves, usando el MISMO esquema que las plantillas HTML del plan:
1) "NODES": [{id,label,sub,x,y,group("channel"|"core"|"data"|"integ"),desc,files:[],deps:[]}] y
   "EDGES": [["from","to"], ...]   (para architecture.html — flujo de un mensaje/request)
2) "ENTITIES": [{id,label,group("core"|"content"|"tax"),x,y,desc,fields:[{name,type,pk?,fk?}]}] y
   "RELATIONS": [{from,to,kind("1-1"|"1-N"|"N-N"),label}]   (para data-model.html)
3) "FLOWS": [{id,label,persona,goal,steps:[{action,screen,endpoint,note?}]}]   (para user-flows.html;
   3-6 flujos de USUARIO reales del repo, lenguaje de usuario, con la pantalla y el endpoint de cada paso)
Coloca coordenadas x/y razonables (cuadrícula ~200px) para que no se solapen. Devuelve SOLO el JSON.`
const raw = await agent(instructions, { label: 'synthesize', phase: 'Synthesize' })

let data
try { data = JSON.parse(String(raw).replace(/^```json\s*|\s*```$/g, '')) }
catch (e) { log('No se pudo parsear el JSON de síntesis; devuelvo el texto crudo para pegar a mano.'); data = { raw: String(raw) } }

return {
  subsystems,
  NODES: data.NODES, EDGES: data.EDGES,
  ENTITIES: data.ENTITIES, RELATIONS: data.RELATIONS,
  FLOWS: data.FLOWS,
  ...(data.raw ? { raw: data.raw } : {}),
}
