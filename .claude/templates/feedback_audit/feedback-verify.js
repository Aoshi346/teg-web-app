export const meta = {
  name: 'feedback-verify',
  description: 'Verifica items de feedback contra el sitio en vivo, 1 agente por página, con veredicto estructurado',
  whenToUse: 'Paso 4 de la skill feedback-audit, que lo lanza con el tool Workflow (scriptPath: .claude/templates/feedback_audit/feedback-verify.js). Tras capturar páginas (capture_pages.py): verifica cada item de feedback contra código + DOM en vivo y produce verdicts.json',
  phases: [
    { title: 'Scout', detail: 'lee pages_config.json + items.json' },
    { title: 'Verify', detail: '1 agente por página → veredictos' },
    { title: 'Persist', detail: 'escribe verdicts.json' },
  ],
}

// args = audit_dir (string o {audit_dir}). Contiene pages_config.json, items.json, shots/pages/<CODE>.dom.json.
const DIR = (typeof args === 'string' ? args : (args && args.audit_dir) || '').trim() || (() => { throw new Error('falta args: la carpeta de la auditoría (audit_dir). Sin ella no se verifica "." a ciegas: lánzalo desde la skill feedback-audit') })()

// ---- Esquema del contrato de veredicto (ver rules/verdict-contract.md) ----
const VERDICT_ITEM = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    verdict: { type: 'string', enum: ['done', 'partial', 'notdone', 'blocked', 'review'] },
    confidence: { type: 'string', enum: ['alta', 'media', 'baja'] },
    precision_pct: { type: 'integer', minimum: 0, maximum: 100 },
    interpretacion: { type: 'string' },
    why: { type: 'string', description: 'doble evidencia: 🔎 Código (file:line) + 👁 En vivo (DOM/screenshot)' },
    howto: { type: 'string' },
    anchor_type: { type: 'string', enum: ['text', 'selector', 'scroll_pct'] },
    anchor_value: { type: 'string' },
    viewport: { type: 'string', enum: ['desktop', 'mobile'] },
  },
  required: ['id', 'verdict', 'confidence', 'why', 'anchor_type', 'anchor_value', 'viewport'],
  additionalProperties: false,
}
const PAGE_RESULT = {
  type: 'object',
  properties: {
    code: { type: 'string' },
    results: { type: 'array', items: VERDICT_ITEM },
  },
  required: ['code', 'results'],
  additionalProperties: false,
}
const SCOUT = {
  type: 'object',
  properties: {
    base: { type: 'string' },
    pages: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          code: { type: 'string' },
          url: { type: 'string' },
          populate_hint: { type: 'string' },
          items: {
            type: 'array',
            items: {
              type: 'object',
              properties: { id: { type: 'string' }, text: { type: 'string' } },
              required: ['id', 'text'], additionalProperties: false,
            },
          },
        },
        required: ['code', 'url', 'items'], additionalProperties: false,
      },
    },
  },
  required: ['pages'], additionalProperties: false,
}

// ---- Scout: descubre páginas + sus items ----
phase('Scout')
const plan = await agent(
  `Lee \`${DIR}/pages_config.json\` y \`${DIR}/items.json\`. Para cada página de pages_config, ` +
  `resuelve su URL (page.url o meta.base+slug) y reúne los items de items.json cuyo \`page\` == page.code ` +
  `(id, text). Devuelve {base, pages:[{code,url,populate_hint,items:[{id,text}]}]}. ` +
  `Omite páginas sin items.`,
  { label: 'scout', schema: SCOUT },
)
const pages = (plan?.pages || []).filter(p => p.items && p.items.length)
log(`Scout: ${pages.length} páginas con items (${pages.reduce((n, p) => n + p.items.length, 0)} items)`)
if (!pages.length) return { pages: [], note: 'sin páginas/items que verificar' }

// ---- Verify: 1 agente por página, en paralelo (cada uno verifica sus items) ----
phase('Verify')
const results = await parallel(pages.map(p => () =>
  agent(
    `Eres un verificador. Verifica si CADA item de feedback de la página "${p.code}" está implementado, ` +
    `cruzando CÓDIGO + EN VIVO. Sigue el contrato de \`.claude/rules/verdict-contract.md\`.\n\n` +
    `Página: ${p.code} — URL: ${p.url}\n` +
    (p.populate_hint ? `Pista de código: ${p.populate_hint}\n` : '') +
    `Evidencia disponible (léela):\n` +
    `- DOM en vivo: \`${DIR}/shots/pages/${p.code}.dom.json\` (headings, secciones, links)\n` +
    `- Screenshots: \`${DIR}/shots/pages/${p.code}-full.jpg\`, \`-m.jpg\`, \`-s<N>.jpg\`\n` +
    `- Auditoría de enlaces: \`${DIR}/shots/pages/_links_audit.json\`\n` +
    `- El código del repo (usa Grep/Read sobre la pista y rutas relacionadas).\n\n` +
    `Items a verificar:\n${p.items.map(it => `- ${it.id}: ${it.text}`).join('\n')}\n\n` +
    `Por cada item devuelve un objeto del esquema: verdict (done/partial/notdone/blocked/review), ` +
    `confidence, precision_pct, interpretacion, why (con "🔎 Código: …(file:line)" Y "👁 En vivo: …"), ` +
    `howto (vacío si done), y anchor_type/anchor_value/viewport para localizar la evidencia en la página ` +
    `(anchor_value = un texto exacto del DOM, o un selector CSS, o un % de scroll). ` +
    `REGLA: "done" exige que 🔎 y 👁 coincidan; si solo una lo confirma → "partial". No inventes: cita evidencia.`,
    { label: `verify:${p.code}`, phase: 'Verify', schema: PAGE_RESULT },
  ),
))
const verdicts = { pages: results.filter(Boolean) }
const flat = verdicts.pages.flatMap(pg => pg.results || [])
log(`Verify: ${flat.length} veredictos en ${verdicts.pages.length} páginas`)

// ---- Persist: un agente escribe verdicts.json en disco ----
phase('Persist')
await agent(
  `Escribe EXACTAMENTE este JSON en \`${DIR}/verdicts.json\` (sobrescribe), sin comentarios ni texto extra:\n\n` +
  '```json\n' + JSON.stringify(verdicts, null, 1) + '\n```\n' +
  `Luego confirma el conteo por verdict.`,
  { label: 'persist', phase: 'Persist' },
)

return {
  audit_dir: DIR,
  pages: verdicts.pages.length,
  verdicts: flat.length,
  counts: flat.reduce((m, r) => ((m[r.verdict] = (m[r.verdict] || 0) + 1), m), {}),
  next: `python3 .claude/templates/feedback_audit/capture_items.py ${DIR} && ` +
        `python3 .claude/templates/feedback_audit/reconcile.py ${DIR} && ` +
        `python3 .claude/templates/feedback_audit/build_report.py ${DIR}`,
}
