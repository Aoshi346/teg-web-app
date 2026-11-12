// Matriz responsive: páginas × tamaños con reglas de medida (medir.mjs), capturas y informe.json.
// Por cada página y tamaño: captura de página entera + captura de la primera vista + las reglas genéricas
// (sin-scroll-horizontal, ventana-ensanchada, texto-cortado, solapes, tactil-24; aviso hueco) y las
// opcionales que el config active con sus selectores (burbuja-tapa, una-vista, cta-hero).
//
// Uso: node responsive.mjs <salida> [<base>] [--config=responsive.config.json] [--tamanos=390x844,1440x900]
//                                  [--paginas=inicio,404] [--playwright=<ruta a playwright-core>]
//   <salida>  carpeta de la corrida (fuera de git). <base> manda sobre `base` del config.
//   --config  por defecto ./responsive.config.json (ejemplo: responsive.config.example.json, al lado).
// Escribe <salida>/<pagina>/<W>x<H>.png, <W>x<H>-vista.png e <salida>/informe.json (lo lee hoja-responsive.mjs).
// Sale 0 si todo bien · 1 si hay fallos · 2 config inválido o argumentos · 3 RAM en rojo · 4 sin playwright-core.
//
// Config (responsive.config.json):
//   base?           URL base (http://127.0.0.1:PUERTO; nunca 0.0.0.0)
//   paginas         [{ pagina, ruta, titulo?, llenar?: {id: valor}, status?, movilVertical?, hero?, extra? }]
//                     movilVertical: true → regla una-vista (necesita selectores.cta) en móvil vertical
//                     hero: true          → regla cta-hero (necesita selectores.hero)
//                     extra: false        → sin los tamanosExtra en esta página (por defecto, con ellos)
//   tamanos         [[W, H], …]      tamanosExtra?  [{ w, h, etiqueta }]  (p. ej. el alto útil en Instagram)
//   selectores?     { flotante?, cta?, nota?, hero?, tarjeta? }  — cada uno un selector CSS (string)
//   auth?           { usuario, envClave }  basic-auth; la clave se lee de process.env[envClave]
//   versionServida? { comando? | fichero? }  qué versión sirve el servidor; se compara con el HEAD de git
//                     y se avisa si no coinciden (una matriz entera medida sobre una release vieja no vale)
// Un solo Chrome, contextos en serie y cerrados: la RAM manda (check-ram.sh antes de lanzarlo).
import { mkdirSync, writeFileSync, readFileSync, existsSync, readlinkSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { medirEnPagina } from './medir.mjs';

const args = process.argv.slice(2);
const [out, baseArg] = args.filter((a) => !a.startsWith('--'));
const opcion = (n) => args.find((a) => a.startsWith(`--${n}=`))?.slice(n.length + 3);
const aqui = dirname(fileURLToPath(import.meta.url));
const salir = (msg, codigo = 2) => { console.error(`✗ ${msg}`); process.exit(codigo); };
if (!out) salir('Uso: node .claude/skills/capturas-responsive/responsive.mjs <salida> [<base>] [--config=…] [--tamanos=WxH,…] [--paginas=…]');

// ---------- Config: se valida TODO antes de tocar Chrome (un selector mal escrito = regla que calla) ----------
const rutaConfig = resolve(opcion('config') || 'responsive.config.json');
if (!existsSync(rutaConfig)) salir(`no encuentro el config ${rutaConfig} (copia responsive.config.example.json de la skill o pasa --config=)`);
let cfg;
try { cfg = JSON.parse(readFileSync(rutaConfig, 'utf8')); } catch (e) { salir(`${rutaConfig} no es JSON válido: ${e.message}`); }
const esStr = (v) => typeof v === 'string' && v.trim() !== '';
const esTam = (t) => Array.isArray(t) && t.length === 2 && t.every((n) => Number.isInteger(n) && n > 0);
const errores = [];
if (!cfg || typeof cfg !== 'object' || Array.isArray(cfg)) errores.push('el config tiene que ser un objeto');
else {
  if (!Array.isArray(cfg.paginas) || !cfg.paginas.length) errores.push('`paginas` tiene que ser una lista con al menos una página');
  else cfg.paginas.forEach((p, i) => {
    const q = `paginas[${i}]`;
    if (!p || typeof p !== 'object') { errores.push(`${q} tiene que ser un objeto`); return; }
    if (!esStr(p.pagina) || /[\/\\]/.test(p.pagina)) errores.push(`${q}.pagina tiene que ser un nombre (sin barras): es la carpeta de capturas`);
    if (!esStr(p.ruta) || !p.ruta.startsWith('/')) errores.push(`${q}.ruta tiene que ser una ruta que empiece por /`);
    if (p.titulo !== undefined && !esStr(p.titulo)) errores.push(`${q}.titulo tiene que ser texto`);
    if (p.status !== undefined && !(Number.isInteger(p.status) && p.status >= 100 && p.status < 600)) errores.push(`${q}.status tiene que ser un código HTTP`);
    if (p.llenar !== undefined && (!p.llenar || typeof p.llenar !== 'object' || Array.isArray(p.llenar) || !Object.values(p.llenar).every((v) => typeof v === 'string'))) errores.push(`${q}.llenar tiene que ser {id: "valor"} (valores de texto)`);
    for (const b of ['movilVertical', 'hero', 'extra']) if (p[b] !== undefined && typeof p[b] !== 'boolean') errores.push(`${q}.${b} tiene que ser true/false`);
    if (p.movilVertical && !esStr(cfg.selectores?.cta)) errores.push(`${q}.movilVertical pide selectores.cta`);
    if (p.hero && !esStr(cfg.selectores?.hero)) errores.push(`${q}.hero pide selectores.hero`);
  });
  if (!Array.isArray(cfg.tamanos) || !cfg.tamanos.length || !cfg.tamanos.every(esTam)) errores.push('`tamanos` tiene que ser una lista de [ancho, alto] en px enteros');
  if (cfg.tamanosExtra !== undefined && (!Array.isArray(cfg.tamanosExtra) || !cfg.tamanosExtra.every((t) => t && esTam([t.w, t.h]) && esStr(t.etiqueta)))) errores.push('`tamanosExtra` tiene que ser una lista de {w, h, etiqueta}');
  if (cfg.selectores !== undefined) {
    if (!cfg.selectores || typeof cfg.selectores !== 'object' || Array.isArray(cfg.selectores)) errores.push('`selectores` tiene que ser un objeto');
    else for (const [k, v] of Object.entries(cfg.selectores)) {
      if (!['flotante', 'cta', 'nota', 'hero', 'tarjeta'].includes(k)) errores.push(`selectores.${k}: no existe esa regla (valen flotante, cta, nota, hero, tarjeta)`);
      else if (!esStr(v)) errores.push(`selectores.${k} tiene que ser un selector CSS (texto)`);
    }
  }
  if (cfg.auth !== undefined && (!cfg.auth || !esStr(cfg.auth.usuario) || !esStr(cfg.auth.envClave))) errores.push('`auth` tiene que ser {usuario, envClave}');
  if (cfg.base !== undefined && !esStr(cfg.base)) errores.push('`base` tiene que ser una URL');
  if (cfg.versionServida !== undefined && (!cfg.versionServida || !(esStr(cfg.versionServida.comando) || esStr(cfg.versionServida.fichero)))) errores.push('`versionServida` tiene que ser {comando} o {fichero}');
}
const baseCruda = baseArg || cfg?.base;
if (!errores.length && !esStr(baseCruda)) errores.push('falta la base: pásala como segundo argumento o en `base` del config');
if (!errores.length && /0\.0\.0\.0/.test(baseCruda)) errores.push('la base no puede ser 0.0.0.0: sirve en 127.0.0.1 y llega por túnel');
if (errores.length) salir(`config inválido (${rutaConfig}):\n  - ${errores.join('\n  - ')}`);
const base = baseCruda.replace(/\/$/, '');
if (cfg.auth && !process.env[cfg.auth.envClave]) salir(`auth: falta la variable de entorno ${cfg.auth.envClave} con la clave de ${cfg.auth.usuario}`);
const auth = cfg.auth ? { httpCredentials: { username: cfg.auth.usuario, password: process.env[cfg.auth.envClave] } } : {};
const selectores = cfg.selectores || {};

const filtroTam = opcion('tamanos')?.split(',');
const TAMANOS = cfg.tamanos.filter(([w, h]) => !filtroTam || filtroTam.includes(`${w}x${h}`));
const EXTRA = (cfg.tamanosExtra || []).filter((t) => !filtroTam || filtroTam.includes(`${t.w}x${t.h}`));
const filtroPag = opcion('paginas')?.split(',');
const PAGINAS = cfg.paginas.filter((p) => !filtroPag || filtroPag.includes(p.pagina));
if (!PAGINAS.length) salir('--paginas no deja ninguna página del config');
if (!TAMANOS.length && !EXTRA.length) salir('--tamanos no deja ningún tamaño del config');
const esMovil = (w, h) => w <= 932 && h <= 932;

// ---------- RAM antes de Chrome (regla crítica del template) ----------
const checkRam = [join(process.cwd(), '.claude/hooks/check-ram.sh'), join(aqui, '../../hooks/check-ram.sh')].find(existsSync);
if (!checkRam) salir('no encuentro .claude/hooks/check-ram.sh: sin la RAM en verde no se lanza Chrome', 3);
if (spawnSync('bash', [checkRam], { stdio: 'inherit' }).status !== 0) salir('RAM en rojo (check-ram.sh): no lanzo Chrome', 3);

// ¿Qué versión sirve el servidor? Solo si el config lo dice; si no, se omite.
const git = (...a) => spawnSync('git', a, { encoding: 'utf8' }).stdout?.trim() || null;
let version = null;
if (cfg.versionServida) {
  let servido = null;
  try {
    if (cfg.versionServida.comando) servido = spawnSync('bash', ['-c', cfg.versionServida.comando], { encoding: 'utf8' }).stdout.trim() || null;
    else { const f = resolve(cfg.versionServida.fichero); try { servido = readlinkSync(f).split('/').pop(); } catch { servido = readFileSync(f, 'utf8').trim(); } }
  } catch (e) { console.log(`⚠ versionServida: no se pudo leer (${e.message})`); }
  version = { head: git('rev-parse', '--short=7', 'HEAD'), servido };
  if (version.servido && version.head && version.servido !== version.head) console.log(`\n⚠ el servidor sirve ${version.servido} y el HEAD es ${version.head}: lo que midas no es lo último`);
}

// ---------- Playwright: el del proyecto (node_modules) o el que diga --playwright= ----------
const rutaPw = opcion('playwright') || resolve('node_modules/playwright-core/index.mjs');
let chromium;
try { ({ chromium } = await import(existsSync(rutaPw) ? pathToFileURL(rutaPw).href : 'playwright-core')); }
catch { salir(`no encuentro playwright-core (ni ${rutaPw} ni instalado): npm i -D playwright-core o --playwright=<ruta>`, 4); }

// Espera a que acaben las animaciones y transiciones finitas (las infinitas no se esperan; tope 4 s).
const quieto = (p) => p.evaluate(() => Promise.race([
  Promise.all(document.getAnimations().filter((a) => a.playState === 'running' && Number.isFinite(a.effect?.getComputedTiming().endTime)).map((a) => a.finished.catch(() => {}))),
  new Promise((r) => setTimeout(r, 4000)),
]));

async function abrir(p, pag) {
  const resp = await p.goto(base + pag.ruta, { waitUntil: 'load' });
  const esperado = pag.status ?? 200;
  const fallos = [];
  if (resp?.status() !== esperado) fallos.push({ regla: 'carga', detalle: `HTTP ${resp?.status()} (esperaba ${esperado})` });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300); await quieto(p);
  if (pag.llenar) {
    for (const [id, v] of Object.entries(pag.llenar)) await p.fill('#' + id, v);
    await p.waitForTimeout(900); // una cifra que rueda con requestAnimationFrame no sale en getAnimations
    await p.evaluate(() => document.activeElement?.blur());
    await quieto(p);
  }
  return fallos;
}

// Baja la página de pantallazo en pantallazo: dispara las entradas de cada sección y, si hay flotante,
// mira en cada parada si tapa algo. Vuelve arriba al final. Con `capturas` (prefijo de ruta), guarda la
// vista de cada parada donde el flotante tapa algo.
async function recorrer(p, W, capturas) {
  const fallos = [];
  const vh = await p.evaluate(() => innerHeight);
  for (let y = 0; ; y += Math.round(vh * 0.8)) {
    const tope = await p.evaluate(() => document.documentElement.scrollHeight - innerHeight);
    await p.evaluate((y) => scrollTo(0, y), Math.min(y, tope));
    await p.waitForTimeout(250); await quieto(p);
    if (y > 0 && selectores.flotante) {
      const f = (await p.evaluate(medirEnPagina, { reglas: ['burbuja-tapa'], W, ultima: y >= tope, selectores })).fallos;
      if (f.length && capturas) { const sy = await p.evaluate(() => Math.round(scrollY)); await p.screenshot({ path: `${capturas}-burbuja-${sy}.png` }); }
      fallos.push(...f);
    }
    if (y >= tope) break;
  }
  await p.evaluate(() => scrollTo(0, 0)); await p.waitForTimeout(1700); await quieto(p); // lo que se quita solo al llegar arriba
  const vistos = new Set();
  return fallos.filter((f) => !vistos.has(f.detalle.replace(/con scrollY \d+, /, '')) && vistos.add(f.detalle.replace(/con scrollY \d+, /, '')));
}

const informe = { base, fecha: new Date().toISOString(), config: rutaConfig, ...(version ? { version } : {}), casos: [] };
mkdirSync(out, { recursive: true });
const b = await chromium.launch({ executablePath: process.env.CHROME_BIN || '/usr/bin/google-chrome' });
let total = 0;

for (const pag of PAGINAS) {
  mkdirSync(join(out, pag.pagina), { recursive: true });
  console.log(`\n${pag.pagina} (${pag.ruta})`);
  const tamanos = [...TAMANOS.map(([w, h]) => ({ w, h })), ...(pag.extra === false ? [] : EXTRA)];
  for (const { w: W, h: H, etiqueta } of tamanos) {
    const movil = esMovil(W, H);
    const ctx = await b.newContext({ ...auth, viewport: { width: W, height: H }, isMobile: movil, hasTouch: movil, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    const consola = [];
    p.on('pageerror', (e) => consola.push(String(e)));
    // Si el propio documento llega con el status esperado ≠ 200 (una 404), Chrome lo apunta en consola: es lo esperado.
    p.on('console', (m) => { if (m.type() === 'error' && !(pag.status && pag.status !== 200 && new RegExp(`status of ${pag.status}`).test(m.text()) && m.location().url.startsWith(base + pag.ruta))) consola.push(m.text()); });
    const caso = { pagina: pag.pagina, titulo: pag.titulo || pag.pagina, ruta: pag.ruta, ancho: W, alto: H, captura: `${pag.pagina}/${W}x${H}.png`, primeraVista: `${pag.pagina}/${W}x${H}-vista.png`, fallos: [], avisos: [], medidas: {} };
    if (etiqueta) caso.etiqueta = etiqueta;
    try {
      caso.fallos.push(...(await abrir(p, pag)));
      const reglas = ['sin-scroll-horizontal', 'texto-cortado', 'solapes', 'tactil-24', 'hueco'];
      if (selectores.flotante) reglas.push('burbuja-tapa');
      if (pag.movilVertical && movil && H > W) reglas.push('una-vista');
      if (pag.hero) reglas.push('cta-hero');
      const primeras = ['burbuja-tapa', 'una-vista', 'cta-hero'];
      // Primera vista: arriba del todo, como llega el visitante.
      const sinScroll = await p.evaluate(() => document.documentElement.scrollHeight <= innerHeight + 1);
      const primera = await p.evaluate(medirEnPagina, { reglas: reglas.filter((r) => primeras.includes(r)), W, ultima: sinScroll, selectores });
      await p.screenshot({ path: join(out, caso.primeraVista) });
      caso.fallos.push(...primera.fallos);
      caso.fallos.push(...(await recorrer(p, W, join(out, pag.pagina, `${W}x${H}`))));
      const m = await p.evaluate(medirEnPagina, { reglas: reglas.filter((r) => !primeras.includes(r)), W, selectores });
      caso.fallos.push(...m.fallos); caso.avisos.push(...m.avisos); caso.medidas = m.medidas;
      // Un fondo con background-attachment:fixed solo se pinta el alto de la vista en la captura de página
      // entera (debajo sale blanco). Solo para la captura, se pasa a scroll por CSSOM (la CSP no deja inyectar <style>).
      await p.evaluate(() => { document.body.style.backgroundAttachment = 'scroll'; document.documentElement.style.minHeight = '100%'; });
      await p.screenshot({ path: join(out, caso.captura), fullPage: true });
      if (consola.length) caso.fallos.push({ regla: 'consola', detalle: consola.join(' | ').slice(0, 300) });
    } catch (e) { caso.fallos.push({ regla: 'error', detalle: String(e).slice(0, 300) }); }
    await ctx.close();
    informe.casos.push(caso); total += caso.fallos.length;
    const porRegla = Object.entries(caso.fallos.reduce((a, f) => ((a[f.regla] = (a[f.regla] || 0) + 1), a), {})).map(([r, n]) => `${r}×${n}`).join(' ');
    console.log(`  ${`${W}x${H}`.padEnd(9)} ${etiqueta ? etiqueta.slice(0, 5).padEnd(6) : movil ? 'móvil ' : '      '} alto ${String(caso.medidas.scrollHeight ?? '?').padStart(5)} · ${caso.fallos.length ? '✗ ' + porRegla : 'bien'}`);
    for (const f of caso.fallos) console.log(`      ✗ ${f.regla}: ${f.detalle}`);
    for (const f of caso.avisos) console.log(`      · aviso ${f.regla}: ${f.detalle}`);
  }
}

await b.close();
writeFileSync(join(out, 'informe.json'), JSON.stringify(informe, null, 1));
const malosCasos = informe.casos.filter((c) => c.fallos.length).length;
console.log(`\n${informe.casos.length} casos (${malosCasos} con fallos) · informe en ${join(out, 'informe.json')}`);
console.log(total ? `${total} fallo(s)` : 'todo bien');
process.exit(total ? 1 : 0);
