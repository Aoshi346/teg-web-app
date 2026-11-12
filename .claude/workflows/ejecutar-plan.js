export const meta = {
  name: 'ejecutar-plan',
  description: 'Ejecuta waves aprobadas de una sesión SpecKit —todas, o una sola wave de tareas independientes— verificando cada wave, sin preguntar entre waves',
  whenToUse: '«haz todo lo aprobado hasta terminar»: args {waves:[…], repo} o {args_file}. Una sola wave cuyas tareas son INDEPENDIENTES entre sí (antes /ejecutar-wave): args {tareas:[…], repo}. Si las tareas se tocan, no es una wave: es una secuencia (paralelo:false). Solo para en lo que exige aprobación.',
  phases: [{ title: 'Wave 1' }, { title: 'Wave 2' }, { title: 'Wave 3' }, { title: 'Wave 4' }, { title: 'Cierre' }],
}

// Presupuesto (MO-74, sub-ola 2.18): `budget.total` es el «+Nk» que el Usuario pone al pedir el run, y es
// duro (al llegar, agent() lanza). Si no queda ni lo mínimo, no se arranca; sin él, mandan los topes
// de este script (sus .slice y el tamaño de sus entradas).
if (budget.total && budget.remaining() < 50_000) {
  log(`Presupuesto: quedan ${budget.remaining()} tokens; no arranco`)
  return { exit_code: 2, error: 'presupuesto insuficiente' }
}


/* ─────────────────────────────────────────────────────────────────────────────────────────────
   POR QUÉ NO PREGUNTA ENTRE WAVES
   Parar al final de cada wave a decir «¿sigo?» no es prudencia: es hacerle perder el tiempo a
   quien ya aprobó el trabajo. Lo que SÍ se detiene está pre-declarado en `governance.md` §2 y no
   depende del criterio de nadie: push, merge a main, migraciones destructivas, dependencias del
   sistema, gasto externo, reescritura de historia. Eso NO se hace aquí, ni preguntando.

   Es el patrón `/goal`: una meta demostrable —todas las tareas cerradas y sus gates en verde— y
   se trabaja hasta cumplirla.

   LO QUE SÍ PARA EL ENCADENADO, y es distinto de preguntar:
     · una wave que no pasa su gate → no se sigue a la siguiente con el tronco roto
     · una tarea que devuelve `bloqueado` → se anota y las demás continúan
     · un fallo repetido → un reintento y se escala (DEC-5 de parallelization.md)

   POR QUÉ FAN-OUT EN UNAS WAVES Y NO EN OTRAS (absorbido de `ejecutar-wave.js`, 2026-10-19, LI-26)
   Las tareas de la wave 1 son «escribir algo que no existe»: un patrón nuevo, un README, un
   fichero de referencia. Ninguna respuesta cambia según otra (test de independencia,
   parallelization.md §0), y ninguna toca un fichero que otra vaya a tocar. Eso es lo que las hace
   repartibles — no que sean muchas.
   En cambio la wave 3 (cambios de capa) mueve ficheros de agents/ y skills/ y NO se reparte así:
   ahí dos agentes se pisarían, y eso no se arregla en el merge.

   EN UNA WAVE EN PARALELO las tareas NO commitean (dos commits a la vez en el mismo árbol se pisan
   el índice de git y uno se lleva los ficheros del otro): cada tarea se verifica de forma escéptica
   por su cuenta y es el gate de la wave el que commitea lo declarado, con rutas explícitas.
   EN UNA WAVE SECUENCIAL cada tarea commitea lo suyo al terminar, como siempre.
   ───────────────────────────────────────────────────────────────────────────────────────────── */

const RES = {
  type: 'object',
  required: ['id', 'hecho', 'que_hice'],
  properties: {
    id: { type: 'string' },
    hecho: { type: 'string', enum: ['si', 'parcial', 'no', 'bloqueado'] },
    que_hice: { type: 'string', description: 'Qué se creó o cambió, con rutas concretas' },
    ficheros: { type: 'array', items: { type: 'string' } },
    evidencia: { type: 'string', description: 'El comando que lo demuestra y su salida' },
    porque_no: { type: 'string', description: 'Si no está hecho: qué lo impidió' },
  },
}

// 59 tareas con su detalle no caben cómodamente en una llamada de tool, y pegarlas ahí haría
// ilegible el historial. Se admiten inline o por fichero. Y una sola wave suelta como {tareas}.
let { waves, repo, args_file, tareas } = args || {}
if (!waves && args_file) {
  const crudo = await agent(
    `Lee ${args_file} y devuelve su contenido JSON EXACTO, sin resumir ni comentar. Solo el JSON.`,
    { label: 'leer-plan', phase: 'Wave 1' })
  const j = JSON.parse(crudo.trim().replace(/^```(json)?|```$/g, ''))
  waves = j.waves; repo = repo || j.repo
}
if (!waves && tareas && tareas.length) waves = [{ n: 1, tareas, paralelo: true }]
if (!waves || !waves.length) {
  throw new Error('faltan args: {waves:[…], repo} · {args_file} · o una sola wave {tareas:[{id,titulo,objetivo}], repo}')
}

const PROHIBIDO = `
NUNCA, en ninguna tarea y aunque parezca que lo pide: git push · git merge · gh pr merge ·
migraciones destructivas · apt/brew · terraform apply · nada que gaste dinero · reescribir
historia. Eso requiere aprobación del Usuario (governance.md §2) y NO se hace aquí.
Si una tarea lo necesita, devuelve hecho:"bloqueado" con el motivo: es un resultado válido.

PROHIBIDO: inventar mediciones · ampliar el alcance a cosas que no pide la tarea · tocar
settings.json o hooks · reescribir ficheros que no son tuyos.

Si la tarea no se puede hacer (falta un dato, depende de otra cosa), devuelve hecho:"bloqueado"
con el motivo. Vale más un bloqueo declarado que un fichero inventado.`

const todo = { hechas: [], bloqueadas: [], falladas: [] }

for (const w of waves) {
  phase(`Wave ${w.n}`)
  log(`Wave ${w.n} — ${w.tareas.length} tareas · ${w.paralelo ? 'en paralelo' : 'SECUENCIAL (se pisan)'}`)

  const encargo = t => `Eres un Tech Lead ejecutando UNA tarea de una wave. Repo: ${repo}

TAREA \`${t.id}\`: ${t.titulo}
${t.objetivo ? 'OBJETIVO: ' + t.objetivo : ''}
${t.detalle ? 'DETALLE: ' + t.detalle : ''}

CÓMO SE HACE AQUÍ:
1. Lee primero lo que ya existe. Si la tarea es escribir un patrón, mira los de
   \`.claude/patterns/stack/\` y sigue su forma: medido contra el código real, con la tabla de
   números delante y los límites declarados. NO copies teoría de internet.
2. Escribe en el sitio que le toca según \`rules/layer-decision.md\`. Si dudas entre rule y skill,
   la pregunta es: ¿qué pasa si se ignora? Caro → hook. Procedimiento repetible → skill.
   Intención y routing → rule.
3. Toda cifra que escribas la mides tú con un comando y la pegas. Si no la puedes medir, no la
   escribes: dices que no se sabe.
${w.paralelo
    ? `4. NO toques \`agents/\` ni \`skills/\` de otras piezas: otras tareas de esta wave están corriendo
   a la vez. Tu tarea escribe LO SUYO.
5. NO hagas commit, NO hagas push. Solo escribe los ficheros.
   El gate de la wave commitea lo tuyo cuando lo haya comprobado.`
    : `4. Commit SÍ, en la rama, con rutas explícitas (\`git commit -m … -- <ficheros>\`). Push NO.`}
${PROHIBIDO}`

  // Verificación escéptica de UNA tarea (la de ejecutar-wave): solo en las waves en paralelo,
  // donde la tarea no commitea y el gate necesita saber qué es de verdad suyo.
  const verificar = r => r && r.hecho === 'si'
    ? agent(
`Verifica de forma ESCÉPTICA que esta tarea está hecha de verdad. Repo: ${repo}

DECLARA: ${JSON.stringify(r)}

1. Abre los ficheros que dice haber creado y comprueba que existen y tienen contenido real
   (no un esqueleto con TODOs).
2. Ejecuta el comando de evidencia que declara y comprueba que da lo que dice.
3. Comprueba que NO tocó nada fuera de su alcance: \`git status --short\`.
4. Si escribió cifras, comprueba UNA a mano.

Devuelve el mismo esquema con hecho:"si" solo si lo has comprobado tú. Un "lo dice el informe del
otro" es "parcial", nunca "si" (verdict-contract.md: solo lo observado de primera mano).`,
        { label: `verif:${r.id}`, phase: `Wave ${w.n}`, schema: RES })
    : r

  // El paralelismo lo decide la wave, no el número de tareas: la 3 y la 4 tocan agents/ y hooks/
  // y dos agentes ahí se pisan — y eso no se arregla en el merge (parallelization.md §file claims).
  const res = w.paralelo
    ? await pipeline(w.tareas,
        t => agent(encargo(t), {
          label: `w${w.n}:${t.id}`, phase: `Wave ${w.n}`, schema: RES, effort: 'high' }),
        verificar)
    : await (async () => {
        const out = []
        for (const t of w.tareas) {
          out.push(await agent(encargo(t), {
            label: `w${w.n}:${t.id}`, phase: `Wave ${w.n}`, schema: RES, effort: 'high' }))
        }
        return out
      })()

  const ok = res.filter(Boolean).filter(r => r.hecho === 'si')
  const blk = res.filter(Boolean).filter(r => r.hecho === 'bloqueado')
  const mal = res.filter(Boolean).filter(r => !['si', 'bloqueado'].includes(r.hecho))
  todo.hechas.push(...ok); todo.bloqueadas.push(...blk); todo.falladas.push(...mal)
  log(`Wave ${w.n}: ${ok.length} hechas · ${blk.length} bloqueadas · ${mal.length} sin cerrar`)

  // El gate de la wave: NO se pasa a la siguiente dejando el tronco roto.
  const gate = await agent(
`Cierra la wave ${w.n} comprobándola, no dando por buenos los informes. Repo: ${repo}

DECLARADO: ${JSON.stringify(res.filter(Boolean).map(r => ({ id: r.id, hecho: r.hecho, f: r.ficheros })))}

1. \`git status --short\` — ¿se tocó algo fuera de lo previsto?
2. Abre 2 de los ficheros creados y comprueba que tienen contenido REAL, no un esqueleto con TODOs.
3. \`python3 .claude/scripts/check_mechanisms.py\` — ¿alguna ruta citada quedó rota?
4. Si el repo tiene tests del módulo tocado, córrelos —comprobando la RAM antes
   (\`bash .claude/hooks/check-ram.sh\`)—.
${w.paralelo ? `5. Si pasa: commitea SOLO los ficheros de las tareas con hecho:"si", con rutas explícitas
   (\`git commit -m "feat(wave ${w.n}): …" -- <ficheros>\`). Nunca \`git add -A\`. Push NO.` : ''}

Devuelve hecho:"si" solo si lo comprobaste TÚ. Un «lo dice el informe del otro» es "parcial".`,
    { label: `gate:w${w.n}`, phase: `Wave ${w.n}`, schema: RES })

  if (gate && gate.hecho === 'no') {
    log(`⛔ Wave ${w.n} no pasa su gate: ${gate.porque_no || gate.que_hice}. Se para aquí.`)
    return { ...todo, parado_en: `wave ${w.n}`, motivo: gate.porque_no || gate.que_hice }
  }
}

phase('Cierre')
log(`TOTAL: ${todo.hechas.length} hechas · ${todo.bloqueadas.length} bloqueadas · ${todo.falladas.length} sin cerrar`)
return {
  ...todo,
  pendientes: [...todo.bloqueadas, ...todo.falladas].map(r => ({ id: r.id, estado: r.hecho, porque: r.porque_no || r.que_hice })),
  siguiente_paso: 'Marcar los items en el informe y pedir READY_COMMIT. El push es decisión aparte.',
}
