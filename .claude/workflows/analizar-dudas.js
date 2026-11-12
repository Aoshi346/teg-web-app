export const meta = {
  name: 'analizar-dudas',
  description: 'Investiga a fondo cada item en duda hasta poder recomendar sí o no, o decir por qué no se puede',
  whenToUse: 'Items marcados rec:duda que llevan tiempo sin decidirse porque falta información.',
  phases: [{ title: 'Investigar' }, { title: 'Contrastar' }, { title: 'Recomendar' }],
}

// Presupuesto (MO-74, sub-ola 2.18): `budget.total` es el «+Nk» que el Usuario pone al pedir el run, y es
// duro (al llegar, agent() lanza). Si no queda ni lo mínimo, no se arranca; sin él, mandan los topes
// de este script (sus .slice y el tamaño de sus entradas).
if (budget.total && budget.remaining() < 50_000) {
  log(`Presupuesto: quedan ${budget.remaining()} tokens; no arranco`)
  return { exit_code: 2, error: 'presupuesto insuficiente' }
}


/* Una duda que sigue siendo duda después de investigarla es un resultado legítimo — pero hay que
   decir QUÉ falta para resolverla, no dejarla como estaba. Un informe que devuelve las mismas 26
   dudas con más palabras no ha servido de nada. */

const ANALISIS = {
  type: 'object',
  required: ['id', 'veredicto', 'porque', 'evidencia'],
  properties: {
    id:         { type: 'string' },
    veredicto:  { type: 'string', enum: ['aprobar', 'no-aprobar', 'sigue-en-duda'] },
    porque:     { type: 'string', description: 'Una frase. La razón, no el resumen.' },
    evidencia:  { type: 'array', items: { type: 'string' },
                  description: 'fichero:línea o salida de comando OBSERVADA por ti' },
    riesgo:     { type: 'string', description: 'Qué pasa si se hace, y qué pasa si no' },
    reversible: { type: 'string', enum: ['si', 'no', 'parcial'] },
    que_falta:  { type: 'string', description: 'Solo si sigue-en-duda: el dato exacto que la resolvería' },
    orden:      { type: 'string', description: 'Si depende de otro item, cuál y por qué' },
  },
}

// Los items pueden venir inline o por fichero: 26 bloques con su análisis previo no caben
// cómodamente en una llamada de tool, y pegarlos ahí los haría ilegibles en el historial.
let { items, repo, args_file } = args || {}
if (!items && args_file) {
  const crudo = await agent(
    `Lee el fichero ${args_file} y devuelve su contenido JSON EXACTO, sin resumir ni comentar ` +
    `nada. Solo el JSON.`, { label: 'leer-items', phase: 'Investigar' })
  const j = JSON.parse(crudo.trim().replace(/^```(json)?|```$/g, ''))
  items = j.items; repo = repo || j.repo
}
if (!items || !items.length) throw new Error('faltan args: {items:[...], repo} o {args_file}')

phase('Investigar')
log(`${items.length} items en duda`)

const res = await pipeline(
  items,
  it => agent(
`Investiga este item hasta poder recomendar. Repo: ${repo}

ITEM \`${it.id}\`: ${it.titulo}
LO QUE YA SE SABE: ${it.analisis || '(nada)'}
RAZÓN DE LA DUDA: ${it.razon || ''}

QUÉ TIENES QUE AVERIGUAR — con comandos, no con opinión:
1. **¿Quién lo usa DE VERDAD?** Cuenta citas solo desde \`rules/\`, \`skills/\`, \`agents/\`,
   \`hooks/\`, \`commands/\` y \`workflows/\`. **EXCLUYE \`INDEX.md\`, \`AGENT-SYSTEM.md\`,
   \`skills/README.md\`, \`agents/README.md\` e \`inventario.json\`**: son índices que listan todo, y
   citarse a sí mismo no es estar en uso.
2. **¿Qué se rompe si se quita?** Abre los ficheros que lo citan y mira si es una referencia de
   paso o una dependencia real.
3. **¿Hay otra pieza que haga lo mismo?** Si la hay, la pregunta deja de ser "¿sobra?" y pasa a ser
   "¿cuál de las dos sobrevive?" — y eso cambia la recomendación.
4. **¿Es reversible?** Archivar a \`_archive/\` lo es; borrar del historial no.

REGLAS DURAS:
- Solo evidencia que hayas OBSERVADO tú, con \`fichero:línea\` o la salida del comando.
- Si tras investigar sigue sin estar claro, di "sigue-en-duda" y **el dato exacto que lo
  resolvería**. Devolver la misma duda con más palabras no sirve de nada.
- NO modifiques nada. Esto es análisis.`,
    { label: `duda:${it.id}`, phase: 'Investigar', schema: ANALISIS, effort: 'high' })
)

phase('Recomendar')
const r = res.filter(Boolean)
const ap = r.filter(x => x.veredicto === 'aprobar')
const no = r.filter(x => x.veredicto === 'no-aprobar')
const sigue = r.filter(x => x.veredicto === 'sigue-en-duda')
log(`aprobar ${ap.length} · no-aprobar ${no.length} · sigue en duda ${sigue.length}`)
return { analisis: r, resumen: { aprobar: ap.length, no_aprobar: no.length, sigue_duda: sigue.length } }
