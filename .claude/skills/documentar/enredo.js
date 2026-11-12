// Mide el enredo de un SVG de Mermaid YA PINTADO, en coordenadas de pantalla:
//  · cruces: puntos donde dos líneas distintas se cortan (fuera de los extremos, donde sí se juntan)
//  · atraviesa: pares línea-caja en que una línea pasa por DENTRO de una caja que no es la suya
//  · solapes: pares de etiquetas que se pisan, o etiqueta encima de una caja
window.analizarSVG = function (svg) {
  const caja = (el) => { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
  const dentro = (p, b, m) => p.x > b.x + m && p.x < b.x + b.w - m && p.y > b.y + m && p.y < b.y + b.h - m;
  const pisan = (a, b) => Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) *
                          Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  const nodos = [...svg.querySelectorAll("g.node, g.statediagram-state, g.entity")]
    .filter((g, i, arr) => !arr.some((o) => o !== g && o.contains(g)))   // el exterior, no los internos
    .map(caja).filter((b) => b.w > 4 && b.h > 4);
  const lineas = [...new Set(svg.querySelectorAll(
      ".edgePaths path, path.flowchart-link, path.relationshipLine, path.transition, g.edges path"))]
    .filter((p) => p.getTotalLength && p.getTotalLength() > 8);
  const polis = lineas.map((p) => {
    const L = p.getTotalLength(), n = Math.max(12, Math.min(80, Math.round(L / 10))), m = p.getScreenCTM();
    const pts = [];
    for (let k = 0; k <= n; k++) { const q = p.getPointAtLength((L * k) / n); const t = new DOMPoint(q.x, q.y).matrixTransform(m); pts.push({ x: t.x, y: t.y, f: k / n }); }
    return pts;
  });
  const corta = (a, b, c, d) => {
    const den = (b.x - a.x) * (d.y - c.y) - (b.y - a.y) * (d.x - c.x);
    if (Math.abs(den) < 1e-9) return null;
    const t = ((c.x - a.x) * (d.y - c.y) - (c.y - a.y) * (d.x - c.x)) / den;
    const u = ((c.x - a.x) * (b.y - a.y) - (c.y - a.y) * (b.x - a.x)) / den;
    return t > 0 && t < 1 && u > 0 && u < 1 ? { x: a.x + t * (b.x - a.x), y: a.y + t * (b.y - a.y) } : null;
  };
  // los extremos de una línea están en (o junto a) sus cajas: allí se juntan líneas a propósito
  const cerca = (p, poli) => Math.hypot(p.x - poli[0].x, p.y - poli[0].y) < 18 || Math.hypot(p.x - poli.at(-1).x, p.y - poli.at(-1).y) < 18;
  let cruces = 0;
  for (let i = 0; i < polis.length; i++) for (let j = i + 1; j < polis.length; j++) {
    const vistos = [];
    for (let a = 0; a < polis[i].length - 1; a++) for (let b = 0; b < polis[j].length - 1; b++) {
      const x = corta(polis[i][a], polis[i][a + 1], polis[j][b], polis[j][b + 1]);
      if (!x || cerca(x, polis[i]) || cerca(x, polis[j])) continue;
      if (vistos.some((v) => Math.hypot(v.x - x.x, v.y - x.y) < 10)) continue;
      vistos.push(x); cruces++;
    }
  }
  let atraviesa = 0;
  polis.forEach((poli) => nodos.forEach((b) => {
    const de = dentro(poli[0], b, -6) || dentro(poli.at(-1), b, -6);   // su origen o su destino
    if (!de && poli.some((p) => p.f > 0.04 && p.f < 0.96 && dentro(p, b, 3))) atraviesa++;
  }));
  const etiquetas = [...svg.querySelectorAll("g.edgeLabel, .edgeLabel")]
    .filter((g, i, arr) => !arr.some((o) => o !== g && o.contains(g)))
    .filter((g) => g.textContent.trim()).map(caja).filter((b) => b.w > 2 && b.h > 2);
  let solapes = 0;
  for (let i = 0; i < etiquetas.length; i++) {
    for (let j = i + 1; j < etiquetas.length; j++) if (pisan(etiquetas[i], etiquetas[j]) > 6) solapes++;
    for (const b of nodos) if (pisan(etiquetas[i], b) > 0.15 * etiquetas[i].w * etiquetas[i].h) solapes++;
  }
  // abanico: muchas líneas que ACABAN en la misma caja (4 «12 meses» bajando a «Caducado»)
  const llegan = nodos.map((b) => polis.filter((poli) => dentro(poli.at(-1), b, -10)).length);
  const esER = !!svg.querySelector("g.entity, .er, [id*='entity']") || svg.getAttribute("aria-roledescription") === "er";
  const abanico = esER ? 0 : Math.max(0, ...llegan);
  // rodeo: la línea mide más del doble que la distancia recta entre sus extremos, o cruza media hoja
  const W = svg.getBoundingClientRect().width, H = svg.getBoundingClientRect().height;
  const rodeos = polis.filter((poli) => {
    let L = 0; for (let k = 1; k < poli.length; k++) L += Math.hypot(poli[k].x - poli[k - 1].x, poli[k].y - poli[k - 1].y);
    const recta = Math.hypot(poli.at(-1).x - poli[0].x, poli.at(-1).y - poli[0].y);
    return L > 2 * recta + 40 || L > 0.6 * Math.hypot(W, H);
  }).length;
  // la misma etiqueta en 3 o más flechas: es una regla, no un flujo → va en una nota
  const textos = {}; [...svg.querySelectorAll("g.edgeLabel, .edgeLabel")].filter((g, i, arr) => !arr.some((o) => o !== g && o.contains(g))).forEach((g) => { const t = g.textContent.trim(); if (t.length >= 10) textos[t] = (textos[t] || 0) + 1; });
  const repetidas = Object.values(textos).filter((n) => n >= 3).reduce((x, n) => x + n, 0);
  const puntos = 3 * cruces + 3 * atraviesa + 3 * solapes + rodeos + (abanico >= 4 ? 2 : 0) + (repetidas ? 2 : 0);
  return { cruces, atraviesa, solapes, abanico, rodeos, repetidas, puntos, lineas: polis.length, nodos: nodos.length };
};

window.medirDiagrama = async function (src, motor, i) {
  const lienzo = document.getElementById("lienzo");
  lienzo.innerHTML = "";
  const tipo = src.split(/\s/)[0];
  const conMotor = motor === "elk" && /^(flowchart|graph|stateDiagram)/.test(tipo)
    ? `---\nconfig:\n  layout: elk\n---\n${src}` : src;
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "base",
    flowchart: { useMaxWidth: false, htmlLabels: true }, er: { useMaxWidth: false }, state: { useMaxWidth: false },
    themeVariables: { fontSize: "15px", fontFamily: "sans-serif" } });
  try {
    const { svg } = await mermaid.render(`d${i}${motor}`, conMotor);
    lienzo.innerHTML = svg;
    const r = window.analizarSVG(lienzo.querySelector("svg"));
    r.aplica = conMotor !== src || motor === "dagre";
    return r;
  } catch (e) { return { error: String(e).slice(0, 120) }; }
};
