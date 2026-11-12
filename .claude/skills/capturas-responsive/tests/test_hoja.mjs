// Pruebas sin navegador de la skill capturas-responsive:
//   1. hoja-responsive.mjs: un informe.json de 3 casos (1 con fallo) → index.html con «1 fallo», el título
//      de la página del informe y el HTML de los detalles escapado.
//   2. responsive.mjs: con un config inválido aborta con exit 2 sin lanzar Chrome (ni pasar por check-ram).
// Uso: node .claude/skills/capturas-responsive/tests/test_hoja.mjs   (sale 0 si todo pasa)
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

const skill = join(dirname(fileURLToPath(import.meta.url)), '..');
const tmp = mkdtempSync(join(tmpdir(), 'capturas-responsive-'));
let fallos = 0;
const prueba = (nombre, fn) => { try { fn(); console.log(`  ✓ ${nombre}`); } catch (e) { fallos++; console.log(`  ✗ ${nombre}\n    ${String(e.message).split('\n').join('\n    ')}`); } };
const corre = (script, args) => spawnSync(process.execPath, [join(skill, script), ...args], { encoding: 'utf8', cwd: tmp });

// ---------- 1. La hoja ----------
const informe = {
  base: 'http://127.0.0.1:8080', fecha: '2026-11-01T10:00:00.000Z',
  casos: [
    { pagina: 'inicio', titulo: 'Página de inicio', ruta: '/', ancho: 320, alto: 568, captura: 'inicio/320x568.png', primeraVista: 'inicio/320x568-vista.png',
      fallos: [{ regla: 'sin-scroll-horizontal', detalle: 'div.hero va de 0 a 340 <b>"viewport"</b> 320' }], avisos: [], medidas: { scrollWidth: 340, scrollHeight: 2400 } },
    { pagina: 'inicio', titulo: 'Página de inicio', ruta: '/', ancho: 1440, alto: 900, captura: 'inicio/1440x900.png', primeraVista: 'inicio/1440x900-vista.png',
      fallos: [], avisos: [{ regla: 'hueco', detalle: 'article tiene 200 px vacíos' }], medidas: { scrollWidth: 1440, scrollHeight: 1800 } },
    { pagina: 'contacto', titulo: 'Formulario de contacto', ruta: '/contacto', ancho: 390, alto: 664, etiqueta: 'Instagram', captura: 'contacto/390x664.png', primeraVista: 'contacto/390x664-vista.png',
      fallos: [], avisos: [], medidas: { scrollWidth: 390, scrollHeight: 664 } },
  ],
};
const salida = join(tmp, 'salida');
spawnSync('mkdir', ['-p', salida]);
writeFileSync(join(salida, 'informe.json'), JSON.stringify(informe));
const r1 = corre('hoja-responsive.mjs', [salida]);
console.log('hoja-responsive.mjs');
prueba('sale 0 y escribe index.html', () => { assert.equal(r1.status, 0, r1.stderr); assert.match(r1.stdout, /3 casos, 1 con fallos/); });
const html = r1.status === 0 ? readFileSync(join(salida, 'index.html'), 'utf8') : '';
prueba('cuenta «1 fallo» en la ficha y en el resumen', () => { assert.match(html, /<span class="n">1 fallo<\/span>/); assert.match(html, /<b>1<\/b>con fallos/); });
prueba('el título sale del informe, en su orden, sin nombres cableados', () => {
  assert.match(html, /<h2>Página de inicio <small>/); assert.match(html, /<h2>Formulario de contacto <small>/);
  assert.ok(html.indexOf('<h2>Página de inicio') < html.indexOf('<h2>Formulario de contacto'));
});
prueba('escapa el HTML que viene del informe', () => { assert.ok(!html.includes('<b>"viewport"</b>')); assert.ok(html.includes('&lt;b&gt;&quot;viewport&quot;&lt;/b&gt;')); });
prueba('la etiqueta del tamaño extra y el aviso salen', () => { assert.match(html, /390×664 \(Instagram\)/); assert.match(html, /aviso hueco/); });
prueba('sin extras no pinta el contador de extras', () => assert.ok(!html.includes('extras bien')));
prueba('sin informe.json sale 2', () => assert.equal(corre('hoja-responsive.mjs', [join(tmp, 'no-existe')]).status, 2));

// ---------- 2. responsive.mjs aborta con config inválido ----------
console.log('responsive.mjs');
const conConfig = (cfg, nombre) => { const f = join(tmp, nombre); writeFileSync(f, typeof cfg === 'string' ? cfg : JSON.stringify(cfg)); return corre('responsive.mjs', [join(tmp, 'out'), 'http://127.0.0.1:8080', `--config=${f}`]); };
const ok = JSON.parse(readFileSync(join(skill, 'responsive.config.example.json'), 'utf8'));
prueba('sin config: exit 2 y lo dice', () => { const r = corre('responsive.mjs', [join(tmp, 'out'), '--config=' + join(tmp, 'nada.json')]); assert.equal(r.status, 2); assert.match(r.stderr, /no encuentro el config/); });
prueba('JSON roto: exit 2', () => { const r = conConfig('{"paginas": [', 'roto.json'); assert.equal(r.status, 2); assert.match(r.stderr, /no es JSON válido/); });
prueba('sin paginas: exit 2', () => { const r = conConfig({ ...ok, paginas: [] }, 'sin-paginas.json'); assert.equal(r.status, 2); assert.match(r.stderr, /`paginas`/); });
prueba('selector que no es string: exit 2 y nombra el selector', () => { const r = conConfig({ ...ok, selectores: { flotante: 3 } }, 'sel.json'); assert.equal(r.status, 2); assert.match(r.stderr, /selectores\.flotante/); });
prueba('movilVertical sin selectores.cta: exit 2', () => { const r = conConfig({ ...ok, paginas: [{ pagina: 'a', ruta: '/', movilVertical: true }] }, 'mv.json'); assert.equal(r.status, 2); assert.match(r.stderr, /selectores\.cta/); });
prueba('tamanos mal formados: exit 2', () => { const r = conConfig({ ...ok, tamanos: [[320]] }, 'tam.json'); assert.equal(r.status, 2); assert.match(r.stderr, /`tamanos`/); });
prueba('base 0.0.0.0: exit 2', () => { const f = join(tmp, 'ok.json'); writeFileSync(f, JSON.stringify(ok)); const r = corre('responsive.mjs', [join(tmp, 'out'), 'http://0.0.0.0:8080', `--config=${f}`]); assert.equal(r.status, 2); assert.match(r.stderr, /0\.0\.0\.0/); });
prueba('el config de ejemplo es válido (no cae en la validación)', () => { const r = conConfig(ok, 'ejemplo.json'); assert.ok(!/config inválido/.test(r.stderr), r.stderr); assert.notEqual(r.status, 2, r.stderr); });

rmSync(tmp, { recursive: true, force: true });
console.log(fallos ? `\n${fallos} prueba(s) mal` : '\ntodo bien');
process.exit(fallos ? 1 : 0);
