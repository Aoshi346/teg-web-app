// Hoja de contactos: lee <salida>/informe.json (el que escribe responsive.mjs) y escribe
// <salida>/index.html, una página autocontenida para revisar las capturas EN EL MÓVIL por el tailnet.
// Arriba el resumen (casos, fallos por regla) y los filtros; debajo, por página (en el orden del informe,
// con su `titulo`), las miniaturas
// de la primera vista agrupadas por tipo de pantalla, con el tamaño y los fallos en rojo. Al tocar una,
// se abre la captura completa. No va a web/ ni lleva CSP: el JS en línea está permitido aquí.
// Uso: node .claude/skills/capturas-responsive/hoja-responsive.mjs <salida>
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const [out] = process.argv.slice(2);
if (!out) { console.error('Uso: node .claude/skills/capturas-responsive/hoja-responsive.mjs <salida>'); process.exit(2); }
const rutaInforme = join(out, 'informe.json');
if (!existsSync(rutaInforme)) { console.error(`No encuentro ${rutaInforme}: corre antes responsive.mjs.`); process.exit(2); }
const inf = JSON.parse(readFileSync(rutaInforme, 'utf8'));
const casos = Array.isArray(inf.casos) ? inf.casos : [];
const extras = Array.isArray(inf.extras) ? inf.extras : [];

// Todo lo que viene del informe se escapa: hay detalles con texto de la página.
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
// Rutas relativas a <salida>: se codifica cada tramo, sin tocar las barras.
const href = (r) => String(r ?? '').split('/').map(encodeURIComponent).join('/');

// Título y orden de cada página: los del informe (caso.titulo; el orden en que responsive.mjs las recorrió).
const titulos = {};
for (const c of casos) if (!(c.pagina in titulos)) titulos[c.pagina] = c.titulo || c.pagina;
const nombre = (p) => titulos[p] ?? p;
const GRUPOS = [['movil', 'Móvil'], ['apaisado', 'Móvil apaisado'], ['tableta', 'Tableta'], ['escritorio', 'Escritorio']];
// Reparto por tipo de pantalla: apaisado = más ancho que alto y poco alto (640×360, 844×390);
// 1024×768 cuenta como tableta.
const grupo = ({ ancho: w, alto: h }) => (w >= 1280 ? 'escritorio' : w > h && h <= 500 ? 'apaisado' : w >= 600 ? 'tableta' : 'movil');

const paginas = [...new Set(casos.map((c) => c.pagina))];
const conFallos = casos.filter((c) => c.fallos?.length);
const totalFallos = casos.reduce((n, c) => n + (c.fallos?.length || 0), 0);
const porRegla = {};
for (const c of casos) for (const f of c.fallos || []) porRegla[f.regla] = (porRegla[f.regla] || 0) + 1;
const extrasMal = extras.filter((e) => !e.ok);
// Un extra «sin medir» corrió pero no midió lo que dice: ni bien ni mal.
const estado = (e) => (!e.ok ? ['mal', 'mal'] : e.sinMedir ? ['sin-medir', 'sin medir'] : ['ok', 'bien']);
const itemExtra = (e, conPagina) => `<li class="${estado(e)[0]}" data-ok="${e.ok ? 1 : 0}"><span>${estado(e)[1]}</span> <b>${esc(e.prueba)}</b> ${conPagina ? esc(e.pagina ? `(${e.pagina}) ` : '') : ''}${esc(e.detalle)}${e.captura ? ` · <a href="${href(e.captura)}" target="_blank" rel="noopener">captura</a>` : ''}</li>`;
const fecha = inf.fecha ? new Date(inf.fecha) : null;
const fechaTxt = fecha && !isNaN(fecha) ? fecha.toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short' }) : esc(inf.fecha);

const ficha = (c) => {
  const fallos = c.fallos || [];
  const img = c.primeraVista || c.captura;
  const lista = fallos.map((f) => `<li><b>${esc(f.regla)}</b> ${esc(f.detalle)}</li>`).join('')
    + (c.avisos || []).map((f) => `<li class="aviso"><b>aviso ${esc(f.regla)}</b> ${esc(f.detalle)}</li>`).join('');
  const medidas = c.medidas ? `<span class="medida">${esc(c.medidas.scrollWidth)} × ${esc(c.medidas.scrollHeight)} px de página</span>` : '';
  return `<figure class="ficha${fallos.length ? ' mal' : ''}" data-fallos="${fallos.length}">
  <a href="${href(c.captura || img)}" target="_blank" rel="noopener" aria-label="Captura completa ${esc(c.pagina)} a ${esc(c.ancho)}×${esc(c.alto)}">
    <img src="${href(img)}" alt="" loading="lazy" style="aspect-ratio:${Number(c.ancho) || 1}/${Number(c.alto) || 1}">
  </a>
  <figcaption><span class="tam">${esc(c.ancho)}×${esc(c.alto)}${c.etiqueta ? ` (${esc(c.etiqueta)})` : c.instagram ? ' (Instagram)' : ''}</span> ${fallos.length ? `<span class="n">${fallos.length} ${fallos.length === 1 ? 'fallo' : 'fallos'}</span>` : '<span class="ok">bien</span>'}
    ${medidas}${lista ? `<ul>${lista}</ul>` : ''}</figcaption>
</figure>`;
};

const seccion = (p) => {
  const suyos = casos.filter((c) => c.pagina === p);
  const ruta = suyos[0]?.ruta ?? '';
  const nMal = suyos.filter((c) => c.fallos?.length).length;
  const bloques = GRUPOS.map(([g, titulo]) => {
    const del = suyos.filter((c) => grupo(c) === g).sort((a, b) => a.ancho - b.ancho || a.alto - b.alto);
    if (!del.length) return '';
    return `<div class="grupo" data-mal="${del.some((c) => c.fallos?.length) ? 1 : 0}"><h3>${titulo}</h3><div class="rejilla">${del.map(ficha).join('')}</div></div>`;
  }).join('');
  const ext = extras.filter((e) => e.pagina === p);
  const extHtml = ext.length ? `<ul class="extras">${ext.map((e) => itemExtra(e, false)).join('')}</ul>` : '';
  return `<section class="pagina" data-pagina="${esc(p)}" data-mal="${nMal || ext.some((e) => !e.ok) ? 1 : 0}">
  <h2>${esc(nombre(p))} <small>${esc(ruta)} · ${suyos.length} tamaños${nMal ? ` · <em>${nMal} con fallos</em>` : ''}</small></h2>
  ${bloques}${extHtml}
</section>`;
};

// Extras sin página conocida (o de una página sin casos): van en el resumen.
const extrasSueltos = extras.filter((e) => !paginas.includes(e.pagina));

const html = `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Hoja responsive</title>
<style>
:root{--fondo:#f7f6f2;--texto:#1d2528;--suave:#5f6b70;--linea:#dcd9d0;--rojo:#b3261e;--verde:#2e6b3f;--acento:#0f4c5c;--chip:#ebe8df}
@media (prefers-color-scheme:dark){:root{--fondo:#111618;--texto:#e6e8e6;--suave:#9aa5a8;--linea:#2a3336;--rojo:#ff8a80;--verde:#8bd19d;--acento:#7fc4d4;--chip:#1c2427}}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--texto);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-text-size-adjust:100%}
main{max-width:1200px;margin:0 auto;padding:16px}
h1{font-size:1.35rem;margin:.2rem 0 .1rem}
.sub{color:var(--suave);margin:0 0 1rem;font-size:.9rem;word-break:break-all}
.cifras{display:flex;flex-wrap:wrap;gap:.4rem 1.4rem;margin:0 0 .8rem}
.cifras div{font-size:.85rem;color:var(--suave)} .cifras b{display:block;font-size:1.4rem;color:var(--texto)}
.cifras .mal b{color:var(--rojo)}
.reglas,.extras{list-style:none;padding:0;margin:.2rem 0 1rem;font-size:.9rem}
.reglas li{padding:.15rem 0}.reglas b{color:var(--rojo);margin-right:.4rem}
.extras li{padding:.25rem 0;border-top:1px solid var(--linea)}
.extras li>span{font-weight:600;font-size:.8rem;margin-right:.3rem}
.extras li.ok>span{color:var(--verde)} .extras li.mal>span{color:var(--rojo)} .extras li.sin-medir>span{color:var(--gris,#777)}
li.aviso b{color:#8a6d00}
.filtros{position:sticky;top:0;z-index:2;background:var(--fondo);padding:.6rem 0;border-bottom:1px solid var(--linea);display:flex;flex-wrap:wrap;gap:.4rem;align-items:center}
.filtros button{font:inherit;font-size:.85rem;border:0;background:var(--chip);color:var(--texto);padding:.45rem .75rem;border-radius:999px;min-height:36px;cursor:pointer}
.filtros button[aria-pressed=true]{background:var(--acento);color:var(--fondo)}
.filtros label{font-size:.9rem;display:flex;gap:.35rem;align-items:center;margin-left:auto;min-height:36px}
.filtros input{width:18px;height:18px}
.pagina{padding-top:1.2rem}
h2{font-size:1.1rem;margin:0 0 .3rem}
h2 small{display:block;font-weight:400;color:var(--suave);font-size:.82rem;word-break:break-all}
h2 em{color:var(--rojo);font-style:normal}
h3{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--suave);margin:1rem 0 .5rem;font-weight:600}
.rejilla{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:14px 12px;align-items:start}
.ficha{margin:0;min-width:0}
.ficha a{display:block}
.ficha img{display:block;width:100%;height:auto;max-height:260px;object-fit:cover;object-position:top;border-radius:6px;background:var(--chip);outline:1px solid var(--linea)}
.ficha.mal img{outline:2px solid var(--rojo)}
figcaption{font-size:.8rem;margin-top:.35rem}
.tam{font-weight:600;font-variant-numeric:tabular-nums}
.n{color:var(--rojo);font-weight:600} .ok{color:var(--verde)}
.medida{display:block;color:var(--suave);font-size:.75rem}
figcaption ul{margin:.25rem 0 0;padding-left:1rem;color:var(--rojo)}
figcaption li{margin:.1rem 0;word-break:break-word}
.oculto{display:none!important}
.vacio{color:var(--suave);padding:2rem 0}
@media (min-width:700px){.rejilla{grid-template-columns:repeat(auto-fill,minmax(170px,1fr))}}
</style>
</head>
<body>
<main>
<h1>Hoja responsive</h1>
<p class="sub">${esc(inf.base)} · ${fechaTxt}${inf.version?.servido ? ` · sirve ${esc(inf.version.servido)}${inf.version.servido !== inf.version.head ? ` <em class="n">(HEAD ${esc(inf.version.head)}: no es lo último)</em>` : ''}` : ''}</p>
<div class="cifras">
  <div><b>${casos.length}</b>casos</div>
  <div class="${conFallos.length ? 'mal' : ''}"><b>${conFallos.length}</b>con fallos</div>
  <div class="${totalFallos ? 'mal' : ''}"><b>${totalFallos}</b>fallos en total</div>
  ${extras.length ? `<div class="${extrasMal.length ? 'mal' : ''}"><b>${extras.length - extrasMal.length}/${extras.length}</b>extras bien</div>` : ''}
</div>
${Object.keys(porRegla).length ? `<ul class="reglas">${Object.entries(porRegla).sort((a, b) => b[1] - a[1]).map(([r, n]) => `<li><b>${n}</b>${esc(r)}</li>`).join('')}</ul>` : '<p class="ok">Ningún fallo en las comprobaciones automáticas.</p>'}
${extrasSueltos.length ? `<ul class="extras">${extrasSueltos.map((e) => itemExtra(e, true)).join('')}</ul>` : ''}
<nav class="filtros" aria-label="Filtros">
  <button type="button" data-filtro="" aria-pressed="true">Todas</button>
  ${paginas.map((p) => `<button type="button" data-filtro="${esc(p)}" aria-pressed="false">${esc(nombre(p))}</button>`).join('')}
  <label><input type="checkbox" id="solo-mal">Solo con fallos</label>
</nav>
${paginas.map(seccion).join('')}
<p class="vacio oculto" id="vacio">Nada que enseñar con estos filtros.</p>
</main>
<script>
(() => {
  const botones = [...document.querySelectorAll('[data-filtro]')];
  const solo = document.getElementById('solo-mal');
  let pagina = '';
  try { const g = JSON.parse(sessionStorage.getItem('hoja-filtros') || '{}'); pagina = g.pagina || ''; solo.checked = !!g.solo; } catch (e) {}
  const aplicar = () => {
    botones.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.filtro === pagina)));
    let visibles = 0;
    document.querySelectorAll('.pagina').forEach((s) => {
      const ver = (!pagina || s.dataset.pagina === pagina) && (!solo.checked || s.dataset.mal === '1');
      s.classList.toggle('oculto', !ver);
      if (!ver) return;
      visibles++;
      s.querySelectorAll('.ficha').forEach((f) => f.classList.toggle('oculto', solo.checked && f.dataset.fallos === '0'));
      s.querySelectorAll('.grupo').forEach((g) => g.classList.toggle('oculto', solo.checked && g.dataset.mal === '0'));
      s.querySelectorAll('.extras li').forEach((l) => l.classList.toggle('oculto', solo.checked && l.dataset.ok === '1'));
    });
    document.getElementById('vacio').classList.toggle('oculto', visibles > 0);
    try { sessionStorage.setItem('hoja-filtros', JSON.stringify({ pagina, solo: solo.checked })); } catch (e) {}
  };
  botones.forEach((b) => b.addEventListener('click', () => { pagina = b.dataset.filtro; aplicar(); }));
  solo.addEventListener('change', aplicar);
  if (!botones.some((b) => b.dataset.filtro === pagina)) pagina = '';
  aplicar();
})();
</script>
</body>
</html>
`;

writeFileSync(join(out, 'index.html'), html);
console.log(`Hoja: ${join(out, 'index.html')} · ${casos.length} casos, ${conFallos.length} con fallos${extras.length ? `, ${extrasMal.length} extras mal` : ''}.`);
