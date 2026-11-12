() => {
  const R = {};
  const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const cx = cv.getContext('2d', { willReadFrequently: true });
  function toRGBA(str){ if(!str||str==='none') return null;
    cx.clearRect(0,0,1,1); try{cx.fillStyle='#000';cx.fillStyle=str;}catch(e){return null;}
    cx.clearRect(0,0,1,1); cx.fillRect(0,0,1,1); const d=cx.getImageData(0,0,1,1).data;
    return {r:d[0],g:d[1],b:d[2],a:d[3]/255}; }
  function over(fg,bg){const a=fg.a+bg.a*(1-fg.a); if(a===0)return{r:0,g:0,b:0,a:0};
    return {r:(fg.r*fg.a+bg.r*bg.a*(1-fg.a))/a,g:(fg.g*fg.a+bg.g*bg.a*(1-fg.a))/a,
            b:(fg.b*fg.a+bg.b*bg.a*(1-fg.a))/a,a};}
  function lum(c){const f=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)};
    return 0.2126*f(c.r)+0.7152*f(c.g)+0.0722*f(c.b);}
  function ratio(a,b){const L1=lum(a),L2=lum(b);return (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);}
  // Paradas de color de un background-image de degradado. Devuelve [] si no es un degradado
  // o si lleva algo que no sabemos leer (url(), image-set...) -> entonces el fondo es indeterminado.
  function paradasDeDegradado(bgi){
    if(!bgi||bgi==='none') return null;
    if(!/gradient\(/.test(bgi)) return 'opaco-desconocido';   // url(), image-set: no medible
    const cols=[]; const re=/(rgba?\([^)]*\)|#[0-9a-f]{3,8}|oklab\([^)]*\)|oklch\([^)]*\)|hsla?\([^)]*\))/gi;
    let m; while(m=re.exec(bgi)){ const c=toRGBA(m[1]); if(c) cols.push(c); }
    return cols.length?cols:'opaco-desconocido';
  }
  // Devuelve {fondos:[...], indeterminado:bool}. Con degradado devuelve UNA composicion por parada:
  // si el peor caso cumple, cumple en todo el degradado.
  function fondosDe(el){
    let n=el; let capas=[];           // capas por encima del fondo opaco, de arriba a abajo
    while(n&&n!==document.documentElement.parentNode){
      const cs=getComputedStyle(n);
      const par=paradasDeDegradado(cs.backgroundImage);
      if(par==='opaco-desconocido') return {fondos:[{r:255,g:255,b:255,a:1}], indeterminado:true};
      if(par){                         // degradado: se ramifica en N fondos opacos
        return {fondos: par.map(pc=>{ let acc={r:0,g:0,b:0,a:0};
                  capas.forEach(c=>{acc=over(acc,c);});
                  return over(acc, over(pc,{r:255,g:255,b:255,a:1})); }), indeterminado:false};
      }
      const c=toRGBA(cs.backgroundColor);
      if(c&&c.a>0){ capas.push(c);
        if(c.a>=0.999){ let acc={r:0,g:0,b:0,a:0}; capas.forEach(x=>{acc=over(acc,x);});
                        return {fondos:[acc], indeterminado:false}; } }
      n=n.parentElement;
    }
    let acc={r:0,g:0,b:0,a:0}; capas.forEach(x=>{acc=over(acc,x);});
    return {fondos:[over(acc,{r:255,g:255,b:255,a:1})], indeterminado:false};
  }
  function bgOf(el){ return fondosDe(el).fondos[0]; }
  const sane = toRGBA('oklab(0.769729 0.0546647 0.155194 / 0.25)');
  const sw = sane? over(sane,{r:255,g:255,b:255,a:1}) : null;
  R.sanity = sw?{r:Math.round(sw.r),g:Math.round(sw.g),b:Math.round(sw.b)}:null;
  R.sanity_ok = !!sw && Math.abs(sw.r-252)<=2 && Math.abs(sw.g-231)<=2 && Math.abs(sw.b-194)<=2;

  const scope = window.__VERA_SCOPE ? document.querySelector(window.__VERA_SCOPE) : document.body;
  R.scope_ok = !!scope;
  if(!scope) return R;

  // contraste
  // v22 (ronda 13): la distribucion de margenes se calcula DENTRO del compositor.
  // Mi regla de la ronda 8 dice que a un cero se le exige su distribucion, y hasta hoy
  // yo la sacaba con un recorrido aparte que leia backgroundColor a pelo — o sea, con el
  // instrumento que YA sabia roto para degradados. Daba 6 «margenes negativos» en un build
  // con 0 fallos: los mismos falsos positivos de la ronda 6, colados por la puerta de atras.
  // El margen sale del MISMO ratio compuesto que decide el fallo, o no significa nada.
  const bandas={negativo:0,filo:0,medio:0,holgado:0}; const filos=[];
  const fails=[]; const walker=document.createTreeWalker(scope,NodeFilter.SHOW_TEXT); const seen=new Set(); let node;
  while(node=walker.nextNode()){
    const t=(node.textContent||'').trim(); if(!t) continue;
    const el=node.parentElement; if(!el||seen.has(el)) continue; seen.add(el);
    const cs=getComputedStyle(el);
    if(cs.visibility==='hidden'||cs.display==='none'||parseFloat(cs.opacity)<0.05) continue;
    const rect=el.getBoundingClientRect(); if(rect.width<1||rect.height<1) continue;
    const dis=el.closest('[disabled],[aria-disabled="true"]');
    const fg0=toRGBA(cs.color); if(!fg0) continue;
    const info=fondosDe(el);
    // v21: el indeterminado se cuenta SIEMPRE, no solo cuando el elemento falla.
    // Antes viajaba dentro del registro de un fallo, asi que un elemento que PASABA
    // contra un fondo inventado (blanco) no dejaba rastro. Era la unica direccion en
    // que este instrumento mentia en silencio.
    if(info.indeterminado){ R._indet=(R._indet||0)+1;
      if(!R.indeterminados_muestra) R.indeterminados_muestra=[];
      if(R.indeterminados_muestra.length<8) R.indeterminados_muestra.push(
        {txt:t.slice(0,40), tag:el.tagName, cls:String(el.className||'').slice(0,60)}); }
    // el PEOR caso de todas las paradas del degradado: si ese cumple, cumple en todo
    let bg=info.fondos[0], rr=Infinity;
    info.fondos.forEach(cand=>{ const f=over(fg0,cand); const r=ratio(f,cand);
      if(r<rr){ rr=r; bg=cand; } });
    const fg=over(fg0,bg);
    const px=parseFloat(cs.fontSize), w=parseInt(cs.fontWeight)||400;
    const umbral=(px>=24||(px>=18.66&&w>=700))?3.0:4.5;
    const margen=rr-umbral;
    if(margen<0) bandas.negativo++; else if(margen<0.5){ bandas.filo++;
      if(filos.length<12) filos.push({txt:t.slice(0,32),cls:String(el.className||'').slice(0,40),
        ratio:+rr.toFixed(3),umbral,margen:+margen.toFixed(3)}); }
    else if(margen<1.5) bandas.medio++; else bandas.holgado++;
    if(rr<umbral) fails.push({txt:t.slice(0,45),tag:el.tagName,cls:String(el.className||'').slice(0,70),
      ratio:+rr.toFixed(2),umbral,px:+px.toFixed(1),w,inactivo:!!dis,
      fondo_indeterminado:info.indeterminado, paradas:info.fondos.length,
      interactivo:!!el.closest('a,button,[role="button"],input,select,textarea'),
      fg:`rgb(${Math.round(fg.r)},${Math.round(fg.g)},${Math.round(fg.b)})`,
      bg:`rgb(${Math.round(bg.r)},${Math.round(bg.g)},${Math.round(bg.b)})`});
  }
  R.contraste_fallos=fails.filter(f=>!f.inactivo); R.contraste_inactivos=fails.filter(f=>f.inactivo).length;
  // v24 · F-V15-007: `seen.add(el)` ocurre ANTES de los filtros de visibilidad/tamano/color, asi que
  // seen.size NO es la cobertura: es cuantos nodos con texto se VISITARON. En iter-15 daba 15.302
  // frente a 12.444 realmente medidos — un 18,7% de inflacion, y con ese numero se publicaron los
  // «5.054 elementos» de iter-8, «5.652» de iter-10 y «5.100» de iter-11.
  // Se devuelven los DOS, con nombres que no se puedan confundir. La cobertura es elementos_medidos.
  R.nodos_visitados=seen.size;
  R.elementos_medidos=bandas.negativo+bandas.filo+bandas.medio+bandas.holgado;
  R.contraste_medidos=R.elementos_medidos;   // compatibilidad: ahora apunta a la cifra HONESTA
  R.descartados_por_filtro=R.nodos_visitados-R.elementos_medidos;
  R.margenes={n:seen.size, bandas, filos,
    pct_holgado:+(100*bandas.holgado/Math.max(seen.size,1)).toFixed(1)};
  // La PRUEBA de que el cero no esconde fondos inventados. Un cero con indeterminados>0
  // no es un cero: es «no lo se» disfrazado.
  R.medidos_contra_fondo_inventado = R._indet||0; delete R._indet;
  // Lo que este compositor NO sabe componer. Si alguno es >0, el cero es parcial.
  let opa=0, blend=0, filt=0, bfilt=0;
  scope.querySelectorAll('*').forEach(el=>{ const c=getComputedStyle(el);
    if(parseFloat(c.opacity)<1 && parseFloat(c.opacity)>=0.05) opa++;
    if(c.mixBlendMode && c.mixBlendMode!=='normal') blend++;
    if(c.filter && c.filter!=='none') filt++;
    if(c.backdropFilter && c.backdropFilter!=='none') bfilt++; });
  R.no_componibles = {ancestros_opacity:opa, mix_blend:blend, filter:filt, backdrop:bfilt};

  // R-B: computed vs declarado — cazar var() que no resuelve
  R.vars_no_resueltas = [];
  scope.querySelectorAll('*').forEach(el=>{
    const inline = el.getAttribute('style')||'';
    const m = inline.match(/var\((--[a-z0-9-]+)\s*(?:,([^)]*))?\)/gi);
    if(!m) return;
    m.forEach(exp=>{
      const nm = exp.match(/var\((--[a-z0-9-]+)/i)[1];
      const declarado = getComputedStyle(document.documentElement).getPropertyValue(nm).trim();
      const local = getComputedStyle(el).getPropertyValue(nm).trim();
      if(!declarado && !local) R.vars_no_resueltas.push({
        tag:el.tagName, id:el.id||'', token:nm, expr:exp,
        fallback:(exp.match(/,\s*([^)]+)\)/)||[])[1]||'(sin fallback)' });
    });
  });

  // objetivos táctiles y foco
  R.controles = [...scope.querySelectorAll('button,input,select,textarea,a[href]')].map(el=>{
    const r=el.getBoundingClientRect(); const c=getComputedStyle(el);
    return {tag:el.tagName, type:el.type||'', txt:(el.textContent||el.placeholder||'').trim().slice(0,28),
      w:Math.round(r.width), h:Math.round(r.height), radius:c.borderRadius, bg:c.backgroundColor,
      fs:c.fontSize, fw:c.fontWeight, border:c.borderWidth+' '+c.borderStyle,
      cursor:c.cursor, transition:c.transitionDuration, inline:!!el.getAttribute('style')};
  });
  // foco visible: enfocar cada control y leer outline/box-shadow
  R.foco = [];
  scope.querySelectorAll('button,input,select,textarea,a[href]').forEach(el=>{
    const antes=getComputedStyle(el); const a={o:antes.outlineWidth+'/'+antes.outlineStyle, s:antes.boxShadow};
    try{ el.focus(); }catch(e){}
    const d=getComputedStyle(el);
    R.foco.push({txt:(el.textContent||el.placeholder||'').trim().slice(0,24), tag:el.tagName,
      antes:a, despues:{o:d.outlineWidth+'/'+d.outlineStyle+'/'+d.outlineColor, s:d.boxShadow},
      cambia: (a.o!==d.outlineWidth+'/'+d.outlineStyle)||(a.s!==d.boxShadow)});
  });
  try{ document.activeElement && document.activeElement.blur(); }catch(e){}

  // tipografia del scope
  const sizes={}, fams={}, radios={};
  scope.querySelectorAll('*').forEach(el=>{ const t=(el.textContent||'').trim();
    const c=getComputedStyle(el);
    if(t && !el.children.length){ sizes[c.fontSize]=(sizes[c.fontSize]||0)+1; fams[c.fontFamily.split(',')[0]]=(fams[c.fontFamily.split(',')[0]]||0)+1;}
    const r=el.getBoundingClientRect(); if(r.width>20&&c.borderRadius!=='0px') radios[c.borderRadius]=(radios[c.borderRadius]||0)+1;
  });
  R.tamanos=Object.entries(sizes).sort((a,b)=>b[1]-a[1]).slice(0,10);
  R.familias=Object.entries(fams).sort((a,b)=>b[1]-a[1]).slice(0,5);
  R.radios=Object.entries(radios).sort((a,b)=>b[1]-a[1]).slice(0,8);

  const txt=scope.innerText||'';
  R.texto = txt.slice(0,700);
  // v27 · el rango anterior metia el bloque DINGBATS dentro de «emojis»: en el kiosco dio
  // «201 emojis» que eran 200 «✓» de «En stock» y un «✕» de cerrar. Un dingbat usado como
  // icono es un hallazgo del eje 9 (iconografia), NO del 10 (smell test), y confundirlos
  // convierte una decision de diseño discutible en una acusacion de amateurismo.
  R.emojis = (txt.match(/[\u{1F300}-\u{1FAFF}\u{1F000}-\u{1F2FF}]/gu)||[]);
  R.glifos_como_icono = (txt.match(/[\u{2190}-\u{21FF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}]/gu)||[]);
  R.emojis_glifos = R.emojis;   // compatibilidad: el nombre viejo ahora apunta SOLO a emojis
  R.dinero = { dolar_punto:(txt.match(/\$\s?\d[\d.]*\.\d{2}\b/g)||[]).length,
               dolar_coma:(txt.match(/\$\s?[\d.]*\d,\d{2}\b/g)||[]).length,
               cero:(txt.match(/[$€]\s?0[.,]00\b/g)||[]).length,
               muestras:(txt.match(/[$€]\s?[\d.,]+/g)||[]).slice(0,10),
               miles_ingles:(txt.match(/\d,\d{3}\.\d{2}/g)||[]).length };
  R.sin_tilde = [...new Set((txt.match(/\b(telefono|correo|numero|cerrara|contactara|articulo|categoria|informacion|proximo|minimo|maximo|mas)\b/gi)||[]))];

  // desbordamiento contra el propio scope o main
  const cont = document.querySelector('main') || document.body;
  const cr = cont.getBoundingClientRect();
  R.cont = {right:+cr.right.toFixed(1), width:+cr.width.toFixed(1), scrollH:cont.scrollHeight};
  R.overflow_doc = Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth);
  const desb=[];
  cont.querySelectorAll('*').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width<1||r.height<1) return;
    const ex=r.right-cr.right; if(ex<=1) return;
    let n=el.parentElement, dentro=false;
    while(n&&n!==cont){const c=getComputedStyle(n);
      if((c.overflowX==='auto'||c.overflowX==='scroll'||c.overflowX==='hidden')&&n.scrollWidth>n.clientWidth+1){dentro=true;break;} n=n.parentElement;}
    if(dentro) return;
    desb.push({tag:el.tagName,cls:String(el.className||'').slice(0,60),exceso:+ex.toFixed(1),txt:(el.innerText||'').trim().slice(0,30)});});
  desb.sort((a,b)=>b.exceso-a.exceso); R.desbordes=desb.slice(0,6); R.desborde_max=desb.length?desb[0].exceso:0;
  return R;
}
