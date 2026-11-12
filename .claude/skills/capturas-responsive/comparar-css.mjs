// Compara variantes de CSS sobre la página publicada SIN tocar el código: captura las mismas zonas con
// cada variante inyectada en memoria y escribe <salida>/index.html con las capturas lado a lado.
// bypassCSP es imprescindible: con una CSP estricta, addStyleTag se bloquea en silencio y todas las
// variantes salen iguales.
//
// Uso:
//   node .claude/skills/capturas-responsive/comparar-css.mjs --url=http://127.0.0.1:PUERTO/ --zonas='#seccion-a,#seccion-b' \
//     --variante='Hoy=' --variante='880 px=.tabla,.catalogo{max-width:880px}' \
//     --anchos=1440,1920 --salida=<carpeta> [--titulo='…'] [--playwright=<ruta a playwright-core>]
// Un solo Chrome (CHROME_BIN o /usr/bin/google-chrome); una página por ancho y variante, en serie.
// bash .claude/hooks/check-ram.sh en verde antes de lanzarlo.
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const uno = (k, d) => args.find((a) => a.startsWith(`--${k}=`))?.slice(k.length + 3) ?? d;
const varios = (k) => args.filter((a) => a.startsWith(`--${k}=`)).map((a) => a.slice(k.length + 3));
const url = uno('url');
const zonas = (uno('zonas') || '').split(',').filter(Boolean);
const variantes = varios('variante').map((v) => { const i = v.indexOf('='); return { nombre: v.slice(0, i), css: v.slice(i + 1) }; });
const anchos = (uno('anchos', '1440') || '').split(',').map(Number);
const salida = uno('salida');
if (!url || !zonas.length || variantes.length < 2 || !salida) {
  console.error('Faltan --url, --zonas, al menos dos --variante y --salida'); process.exit(2);
}
const pw = uno('playwright', resolve('node_modules/playwright-core/index.mjs'));
const { chromium } = await import(pw);
mkdirSync(salida, { recursive: true });

const slug = (s) => s.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase();
const b = await chromium.launch({ executablePath: process.env.CHROME_BIN || '/usr/bin/google-chrome' });
const filas = [];
for (const W of anchos) for (const z of zonas) filas.push({ W, z, celdas: [] });
for (const W of anchos) for (const v of variantes) {
  const p = await b.newPage({ viewport: { width: W, height: 900 }, bypassCSP: true });
  await p.goto(url);
  if (v.css) await p.addStyleTag({ content: v.css });
  for (const z of zonas) {
    // Bajar hasta la zona dispara lo que entra al hacer scroll; luego se espera a que acaben las animaciones
    // (una animación cancelada rechaza su .finished con AbortError: se ignora).
    await p.$eval(z, (e) => e.scrollIntoView());
    await p.evaluate(() => Promise.race([Promise.all(document.getAnimations().map((a) => a.finished.catch(() => {}))), new Promise((r) => setTimeout(r, 4000))]));
    await p.waitForTimeout(300);
    const f = `${slug(z)}-${W}-${slug(v.nombre)}.png`;
    await p.locator(z).first().screenshot({ path: `${salida}/${f}` });
    filas.find((x) => x.W === W && x.z === z).celdas.push({ nombre: v.nombre, f });
  }
  await p.close();
}
await b.close();

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const titulo = uno('titulo', 'Comparar variantes');
writeFileSync(`${salida}/index.html`, `<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>${esc(titulo)}</title><style>
:root{--f:#f6f3ec;--t:#1f2430;--s:#5b6270;--a:#00757f}
@media (prefers-color-scheme:dark){:root{--f:#14181f;--t:#eef0f3;--s:#a3a9b4;--a:#4fc3cc}}
body{margin:0;background:var(--f);color:var(--t);font:16px/1.45 system-ui,sans-serif}
main{max-width:1400px;margin:0 auto;padding:20px 16px 60px}h1{font-size:22px;margin:0 0 4px}p{color:var(--s);margin:0 0 20px}
h2{font-size:17px;margin:32px 0 10px;color:var(--a)}.par{display:grid;grid-template-columns:repeat(${variantes.length},1fr);gap:16px}
@media (max-width:800px){.par{grid-template-columns:1fr}}figure{margin:0}figcaption{font-weight:600;margin-bottom:6px}
img{width:100%;height:auto;display:block;border-radius:6px;box-shadow:0 2px 10px rgb(0 0 0/.12)}
</style><main><h1>${esc(titulo)}</h1><p>${variantes.map((v, i) => `${'ABCDEFG'[i]} · ${esc(v.nombre)}`).join(' — ')}. Toca una imagen para verla grande.</p>
${filas.map((r) => `<h2>${esc(r.z)} · ${r.W} px</h2><div class="par">${r.celdas.map((c, i) => `<figure><figcaption>${'ABCDEFG'[i]} · ${esc(c.nombre)}</figcaption><a href="${c.f}"><img src="${c.f}" alt="" loading="lazy"></a></figure>`).join('')}</div>`).join('\n')}
</main></html>`);
console.log(`${filas.length * variantes.length} capturas · ${salida}/index.html`);
