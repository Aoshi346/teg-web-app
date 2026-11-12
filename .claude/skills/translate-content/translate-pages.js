// translate-pages.js — motor de fan-out de la skill translate-content (antes el workflow /translate-pages;
// desde el 2026-10-19 vive aquí y lo lanza la skill con el tool Workflow, scriptPath)
//
// CUÁNDO: traducir muchas páginas/strings a un idioma de forma consistente y repetible.
//   Lo orquesta la skill `translate-content` (que prepara glossary.json + translation-manifest.json).
// COSTE: medio-alto (un agente por página). APRUEBA antes de correr.
// ARGS: "<dir>|<lang>" — dir con translation-manifest.json + glossary.json; lang = idioma destino (en/ca…).
//   Ej: args = ".docs/plans/i18n|en"
// Idempotente: preserva traducciones ya revisadas en translations.<lang>.json (merge por id).
//
// Patrón: scout (agrupa unidades por página) → fan-out por página (traducir con glosario) →
//   verify (HTML/placeholders/glosario) → write translations.<lang>.json. Motor LLM + glosario.

export const meta = {
  name: 'translate-pages',
  description: 'Traduce las unidades de translation-manifest.json a un idioma, con glosario y verificación',
  phases: [{ title: 'Scout' }, { title: 'Translate' }, { title: 'Verify' }, { title: 'Write' }],
}

const [DIR, LANG] = (typeof args === 'string' ? args : (args ? `${args.dir || ''}|${args.lang || ''}` : '')).split('|').map(s => (s || '').trim());
if (!DIR || !LANG) throw new Error('ARGS requeridos: "<dir>|<lang>" o {dir, lang} (ej: ".docs/plans/i18n|en"). Sin ellos no se traduce nada.');

const GROUP_SCHEMA = {
  type: 'object',
  properties: { pages: { type: 'array', items: { type: 'string' } } },
  required: ['pages'],
}
const TRANS_SCHEMA = {
  type: 'object',
  properties: {
    page: { type: 'string' },
    units: { type: 'array', items: {
      type: 'object',
      properties: { id: { type: 'string' }, target: { type: 'string' } },
      required: ['id', 'target'],
    } },
  },
  required: ['page', 'units'],
}
const VERDICT_SCHEMA = {
  type: 'object',
  properties: { ok: { type: 'boolean' }, issues: { type: 'array', items: { type: 'string' } } },
  required: ['ok'],
}

// 1) SCOUT — leer manifest + glosario, listar páginas
phase('Scout')
const scout = await agent(
  `Lee ${DIR}/translation-manifest.json y ${DIR}/glossary.json. Devuelve la lista de páginas distintas
   (campo "page" o agrupando por "file") que hay que traducir. Solo la lista.`,
  { label: 'scout', phase: 'Scout', schema: GROUP_SCHEMA }
)
const pages = (scout && scout.pages) ? scout.pages : []
log(`Páginas a traducir a ${LANG}: ${pages.length}`)

// 2+3) TRANSLATE + VERIFY por página (pipeline, sin barrera)
const results = await pipeline(
  pages,
  (page) => agent(
    `Traduce al idioma "${LANG}" las unidades de la página "${page}" del manifest ${DIR}/translation-manifest.json.
     Aplica ${DIR}/glossary.json: NO traduzcas lo de dontTranslate (marcas, códigos, URLs); usa los
     términos canónicos de "terms"; respeta el "tone"; **preserva intactos** HTML, <span class>,
     placeholders ({var}, %s, %(name)s), shortcodes. IDEMPOTENTE: si ${DIR}/translations.${LANG}.json ya
     tiene una unidad por id, conserva su "target" (ya revisado) y solo traduce las que falten.
     Devuelve {page, units:[{id, target}]}.`,
    { label: `tr:${page}`, phase: 'Translate', schema: TRANS_SCHEMA }
  ),
  (tr, page) => agent(
    `Verifica la traducción a "${LANG}" de la página "${page}": ${JSON.stringify(tr).slice(0, 6000)}
     Comprueba contra ${DIR}/glossary.json: nada de dontTranslate traducido; placeholders/HTML/URLs
     intactos; términos canónicos respetados; sin texto sin traducir. Devuelve {ok, issues[]}.`,
    { label: `qa:${page}`, phase: 'Verify', schema: VERDICT_SCHEMA }
  ).then(v => ({ page, units: tr?.units || [], verdict: v }))
)

// 4) WRITE — fusionar y escribir translations.<lang>.json (idempotente)
phase('Write')
const flat = results.filter(Boolean)
const writeRes = await agent(
  `Escribe/actualiza ${DIR}/translations.${LANG}.json fusionando estas traducciones por página
   (merge por id; conserva targets existentes ya revisados):\n${JSON.stringify(flat.map(f => ({ page: f.page, units: f.units })))}
   Estructura: { "lang":"${LANG}", "units": { "<id>": "<target>", ... }, "reviewed": false }.
   Confirma el path escrito y cuántas unidades.`,
  { label: 'write', phase: 'Write' }
)

const issues = flat.flatMap(f => (f.verdict && f.verdict.ok === false) ? [{ page: f.page, issues: f.verdict.issues || [] }] : [])
log(`Traducción ${LANG} lista. Páginas con issues de QA: ${issues.length}. RECUERDA: revisión nativa antes de publicar.`)
return { lang: LANG, pages: pages.length, qaIssues: issues, write: writeRes }
