// Las reglas de medida de la matriz responsive. UNA sola función, autocontenida (se pasa entera a
// page.evaluate, así que no puede cerrar sobre nada de fuera: ni imports ni constantes del módulo).
//
// medirEnPagina({ reglas, W, ultima, selectores }) → { fallos: [{regla, detalle}], avisos: [...], medidas }
//   reglas      qué medir (lista de nombres de abajo)
//   W           el ancho configurado del viewport. Con isMobile, Chrome ensancha la ventana de diseño
//               hasta el contenido (innerWidth pasa de 320 a 330): comparar con innerWidth escondería
//               justo el desborde, así que todo se compara con W.
//   ultima      true en la última parada del scroll (burbuja-tapa es más estricta ahí)
//   selectores  { flotante, cta, nota, hero, tarjeta } — solo hacen falta para las reglas opcionales
//
// Reglas genéricas (no necesitan selectores):
//   sin-scroll-horizontal  scrollWidth ≤ W, y ningún elemento sale por la derecha escondido por el
//                          overflow-x:hidden del body (que enmascara el scroll pero no el corte).
//                          Incluye `ventana-ensanchada`: innerWidth > W con isMobile = algo empuja la página
//   texto-cortado          texto recortado por un ancestro con overflow hidden/clip (incluye las elipsis)
//                          o que sale del viewport a lo ancho (sin contar carruseles con scroll propio)
//   solapes                botones, enlaces, campos y títulos que se pisan (sin contar contenedor-hijo
//                          ni lo que va fijo, que es cosa de burbuja-tapa)
//   tactil-24              objetivos interactivos ≥ 24×24 CSS px (WCAG 2.5.8, con sus excepciones de
//                          espaciado y de enlace dentro de un texto)
//   hueco                  AVISO (no fallo): una tarjeta estirada con > 160 px vacíos. Tarjeta =
//                          selectores.tarjeta o, por defecto, article / [class*="card"] / [class*="tarjeta"]
// Reglas opcionales (SOLO corren si `selectores` trae lo que necesitan; si no, callan):
//   burbuja-tapa           selectores.flotante: el botón flotante no tapa un botón/enlace en la vista
//                          actual (se llama en la primera vista y en cada parada al recorrer la página)
//   una-vista              selectores.cta (+ nota opcional): el CTA (y la nota) enteros en el primer
//                          viewport y sin scroll vertical («todo en una vista, ni scroll»)
//   cta-hero               selectores.hero: el primer botón visible del hero cabe en el primer viewport
// Lo oculto, lo aria-hidden y lo transparente no cuenta; se mide con las animaciones ya acabadas.
export function medirEnPagina({ reglas, W, ultima, selectores }) {
  const fallos = [], avisos = [];
  const sel = selectores || {};
  const vw = W ?? innerWidth, vh = innerHeight;
  const oculto = (el) => el.closest('[aria-hidden="true"],[hidden],[inert]') ||
    !el.checkVisibility({ opacityProperty: true, visibilityProperty: true });
  const visible = (el) => { if (oculto(el)) return false; const r = el.getBoundingClientRect(); return r.width > 0.5 && r.height > 0.5; };
  const fijo = (el) => { for (let a = el; a && a !== document.body; a = a.parentElement) { const p = getComputedStyle(a).position; if (p === 'fixed' || p === 'sticky') return true; } return false; };
  const nombre = (el) => {
    const t = (el.getAttribute('aria-label') || el.textContent || el.value || el.placeholder || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    return `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : el.classList[0] ? '.' + el.classList[0] : ''}${t ? ` «${t}»` : ''}`;
  };
  const px = (n) => Math.round(n);
  // Recorre los ancestros por debajo del body: ¿quién recorta y quién tiene scroll propio en cada eje?
  const recortes = (el) => {
    const r = { x: [], y: [], scrollX: false, scrollY: false, invisible: false };
    for (let a = el; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.position === 'fixed') break;
      for (const [eje, ov] of [['x', cs.overflowX], ['y', cs.overflowY]]) {
        const scroll = eje === 'x' ? 'scrollX' : 'scrollY';
        if (r[scroll]) continue;
        if (ov === 'auto' || ov === 'scroll') r[scroll] = true;
        else if (ov === 'hidden' || ov === 'clip') {
          const ar = a.getBoundingClientRect();
          if (ar.width <= 2 || ar.height <= 2) r.invisible = true; // tipo sr-only
          r[eje].push([a, ar]);
        }
      }
    }
    return r;
  };

  if (reglas.includes('sin-scroll-horizontal')) {
    const sw = document.documentElement.scrollWidth;
    if (sw > vw) fallos.push({ regla: 'sin-scroll-horizontal', detalle: `scrollWidth ${sw} > ancho ${vw} (+${sw - vw})` });
    if (innerWidth > vw + 0.5) fallos.push({ regla: 'ventana-ensanchada', detalle: `innerWidth ${innerWidth} con un ancho de ${vw}: algo empuja la página` });
    // El overflow-x:hidden del body tapa el scroll; lo que se sale por la derecha queda cortado igual.
    const fuera = [];
    for (const el of document.body.querySelectorAll('*')) {
      if (!visible(el) || fijo(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.right <= vw + 1 && r.left >= -1) continue;
      const rc = recortes(el.parentElement || el);
      if (rc.scrollX || rc.x.length) continue; // lo recorta o lo desplaza un contenedor suyo: no es la página
      if (fuera.some((f) => f.contains(el))) continue;
      fuera.push(el);
    }
    for (const el of fuera.slice(0, 8)) { const r = el.getBoundingClientRect(); fallos.push({ regla: 'sin-scroll-horizontal', detalle: `${nombre(el)} va de ${px(r.left)} a ${px(r.right)} (viewport ${vw})` }); }
    if (fuera.length > 8) fallos.push({ regla: 'sin-scroll-horizontal', detalle: `y ${fuera.length - 8} elemento(s) más` });
  }

  if (reglas.includes('texto-cortado')) {
    const vistos = new Set(); const malos = [];
    const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, { acceptNode: (n) => /\S/.test(n.data) ? 1 : 2 });
    const rango = document.createRange();
    for (let n = tw.nextNode(); n; n = tw.nextNode()) {
      const el = n.parentElement;
      if (!el || vistos.has(el) || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(el.tagName) || !visible(el)) continue;
      rango.selectNodeContents(n);
      const rs = [...rango.getClientRects()].filter((r) => r.width > 0.5 && r.height > 0.5);
      if (!rs.length) continue;
      const rc = recortes(el);
      if (rc.invisible) continue;
      let motivo = null;
      for (const r of rs) {
        for (const [a, ar] of rc.x) if (r.right > ar.right + 1 || r.left < ar.left - 1) { motivo = `cortado a lo ancho por ${nombre(a).split(' ')[0]} (${px(Math.max(r.right - ar.right, ar.left - r.left))} px)`; break; }
        if (motivo) break;
        for (const [a, ar] of rc.y) if (r.bottom > ar.bottom + 1 || r.top < ar.top - 1) { motivo = `cortado a lo alto por ${nombre(a).split(' ')[0]} (${px(Math.max(r.bottom - ar.bottom, ar.top - r.top))} px)`; break; }
        if (motivo) break;
        if (!rc.scrollX && !fijo(el) && (r.right > vw + 1 || r.left < -1)) { motivo = `sale del viewport (${px(r.left)}–${px(r.right)} de ${vw})`; break; }
      }
      if (motivo) { vistos.add(el); malos.push(`${nombre(el)}: ${motivo}`); }
    }
    for (const m of malos.slice(0, 10)) fallos.push({ regla: 'texto-cortado', detalle: m });
    if (malos.length > 10) fallos.push({ regla: 'texto-cortado', detalle: `y ${malos.length - 10} texto(s) más` });
  }

  if (reglas.includes('solapes')) {
    const cajas = [];
    for (const el of document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],h1,h2,h3,h4')) {
      if (!visible(el) || fijo(el)) continue;
      let rs;
      if (/^H\d$/.test(el.tagName)) { const g = document.createRange(); g.selectNodeContents(el); rs = [g.getBoundingClientRect()]; } // el texto, no el bloque
      else rs = [...el.getClientRects()];
      rs = rs.filter((r) => r.width > 0.5 && r.height > 0.5);
      if (rs.length) cajas.push([el, rs]);
    }
    const pares = [];
    for (let i = 0; i < cajas.length; i++) for (let j = i + 1; j < cajas.length; j++) {
      const [a, ra] = cajas[i], [b, rb] = cajas[j];
      if (a.contains(b) || b.contains(a)) continue;
      for (const p of ra) for (const q of rb) {
        const w = Math.min(p.right, q.right) - Math.max(p.left, q.left), h = Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top);
        if (w > 2 && h > 2) { pares.push(`${nombre(a)} pisa ${nombre(b)} (${px(w)}×${px(h)} px)`); break; }
      }
    }
    for (const m of [...new Set(pares)].slice(0, 10)) fallos.push({ regla: 'solapes', detalle: m });
  }

  if (reglas.includes('tactil-24')) {
    const objetivos = [...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[tabindex]:not([tabindex="-1"])')]
      .filter(visible).map((el) => [el, el.getBoundingClientRect()]);
    // Excepción «en línea»: un enlace dentro de una frase (su bloque tiene más texto que él).
    const enLinea = (el) => {
      if (el.tagName !== 'A' || getComputedStyle(el).display !== 'inline') return false;
      const p = el.parentElement; return p && p.textContent.trim().length > el.textContent.trim().length + 3;
    };
    const chicos = objetivos.filter(([el, r]) => (r.width < 24 - 0.5 || r.height < 24 - 0.5) && !enLinea(el));
    const centro = (r) => [r.left + r.width / 2, r.top + r.height / 2];
    const dist = ([x, y], r) => Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom));
    const malos = [];
    for (const [el, r] of chicos) {
      // Excepción de espaciado (2.5.8): un círculo de 24 px centrado en él no toca otro objetivo ni otro círculo.
      const c = centro(r);
      const choca = objetivos.some(([o, ro]) => o !== el && !o.contains(el) && !el.contains(o) && (
        dist(c, ro) < 12 || (chicos.some(([k]) => k === o) && Math.hypot(c[0] - centro(ro)[0], c[1] - centro(ro)[1]) < 24)));
      if (choca) malos.push(`${nombre(el)} mide ${px(r.width)}×${px(r.height)} y tiene otro objetivo a menos de 12 px`);
    }
    for (const m of malos.slice(0, 10)) fallos.push({ regla: 'tactil-24', detalle: m });
    if (malos.length > 10) fallos.push({ regla: 'tactil-24', detalle: `y ${malos.length - 10} más` });
  }

  if (reglas.includes('una-vista') && typeof sel.cta === 'string') {
    const cta = document.querySelector(sel.cta);
    if (!cta || !visible(cta)) fallos.push({ regla: 'una-vista', detalle: `${sel.cta} no se ve (¿sin datos?)` });
    else {
      const r = cta.getBoundingClientRect(), alto = visualViewport ? visualViewport.height : vh;
      if (r.top < 0 || r.bottom > alto + 0.5) fallos.push({ regla: 'una-vista', detalle: `${sel.cta} acaba en ${px(r.bottom)} y la vista mide ${px(alto)}: sobran ${px(r.bottom - alto)} px` });
      // «Ni scroll»: la nota (si la hay) dentro, y la página no más alta que la vista.
      const nota = typeof sel.nota === 'string' ? [...document.querySelectorAll(sel.nota)].find(visible) : null;
      if (nota && nota.getBoundingClientRect().bottom > alto + 0.5) fallos.push({ regla: 'una-vista', detalle: `${sel.nota} acaba en ${px(nota.getBoundingClientRect().bottom)} y la vista mide ${px(alto)}` });
      const sh = document.documentElement.scrollHeight;
      if (sh > vh + 1) fallos.push({ regla: 'una-vista', detalle: `hay scroll: la página mide ${sh} y la vista ${vh} (sobran ${sh - vh} px)` });
    }
  }

  if (reglas.includes('cta-hero') && typeof sel.hero === 'string') {
    const a = [...document.querySelectorAll(sel.hero)].find(visible);
    if (!a) fallos.push({ regla: 'cta-hero', detalle: `no hay botón visible en ${sel.hero}` });
    else { const r = a.getBoundingClientRect(); if (r.bottom + scrollY > vh + 0.5) fallos.push({ regla: 'cta-hero', detalle: `${nombre(a)} acaba en ${px(r.bottom + scrollY)} y la primera vista mide ${vh}` }); }
  }

  if (reglas.includes('hueco')) { // una tarjeta estirada con el contenido flotando en medio
    const tarjetas = typeof sel.tarjeta === 'string' ? sel.tarjeta : 'article,[class*="card"],[class*="tarjeta"]';
    for (const el of document.querySelectorAll(tarjetas)) {
      if (!visible(el)) continue;
      const cs = getComputedStyle(el), hijos = [...el.children].filter(visible);
      if (!hijos.length) continue;
      const usado = hijos.reduce((n, h) => n + h.getBoundingClientRect().height, 0) + (hijos.length - 1) * (parseFloat(cs.rowGap) || 0) + parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
      const libre = el.getBoundingClientRect().height - usado;
      if (libre > 160) avisos.push({ regla: 'hueco', detalle: `${nombre(el).split(' ')[0]} tiene ${px(libre)} px vacíos` });
    }
  }

  if (reglas.includes('burbuja-tapa') && typeof sel.flotante === 'string') {
    const f = document.querySelector(sel.flotante);
    if (f && visible(f) && parseFloat(getComputedStyle(f).opacity) > 0.5) {
      const rf = f.getBoundingClientRect(), c = [rf.left + rf.width / 2, rf.top + rf.height / 2], radio = Math.min(rf.width, rf.height) / 2;
      for (const el of document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button]')) {
        if (f.contains(el) || !visible(el)) continue;
        for (const r of el.getClientRects()) {
          if (r.bottom < 0 || r.top > vh) continue;
          const d = Math.hypot(Math.max(r.left - c[0], 0, c[0] - r.right), Math.max(r.top - c[1], 0, c[1] - r.bottom));
          if (d >= radio - 1) continue;
          // Tapar la esquina de una fila ancha mientras se baja no es fallo. Lo es si tapa > 40 % del
          // elemento, si lo que queda libre no llega a 44×24, o si sigue tapado en la última parada del scroll.
          const iw = Math.min(r.right, rf.right) - Math.max(r.left, rf.left), ih = Math.min(r.bottom, rf.bottom) - Math.max(r.top, rf.top);
          const parte = (iw * ih) / (r.width * r.height);
          const libres = [[rf.left - r.left, r.height], [r.right - rf.right, r.height], [r.width, rf.top - r.top], [r.width, r.bottom - rf.bottom]];
          const queda = libres.some(([w, h]) => w >= 44 && h >= 24);
          if (parte > 0.4 || !queda || ultima) { fallos.push({ regla: 'burbuja-tapa', detalle: `con scrollY ${px(scrollY)}, la burbuja tapa ${nombre(el)} (${Math.round(parte * 100)} %${ultima ? ', última parada' : ''})` }); break; }
        }
      }
    }
  }

  const medidas = { scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight };
  return { fallos: fallos.map(({ regla, detalle }) => ({ regla, detalle })), avisos, medidas };
}
