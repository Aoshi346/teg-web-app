#!/usr/bin/env python3
"""gen_core_levels.py — el harness entero, de lo general a lo concreto, en diagramas que se abren.

Uso:  python3 .claude/templates/report_kit/gen_core_levels.py <plan> [--out .docs/core]
      python3 .claude/templates/report_kit/gen_core_levels.py --self-test

QUÉ RESPONDE (AN-9, sub-ola 3.19). «¿Cuándo entra en juego cada pieza?» sin leer rules sueltas.
Cuatro niveles, y cada caja del nivel abre el siguiente:
  1 · la sesión   ← los eventos registrados en settings.json (cuántos hooks salta cada uno) y las
                    capas, con el momento en que entra cada una
  2 · la capa     ← sus familias: pack (packs.yaml), familia de agente (gen_agent_index.FAMILIAS),
                    evento del hook, rule siempre cargada o con `paths:`
  3 · la familia  ← sus piezas, con cómo se usa cada una (se teclea · la encuentra el modelo · salta)
  4 · la pieza    ← quién la cita y qué usa (aristas de graph-dataset.full.json), navegable
Y aparte, el recorrido de un proyecto de ejemplo, de «empieza» a desplegar, paso a paso.

POR QUÉ GENERADA. Dibujada a mano se queda vieja en cuanto cambia una pieza. Lee el inventario
de `gen_harness_graph.py` (lo corre si falta) y el settings.json reales; los pasos del ejemplo que
ya no existan en disco se quitan y se dice cuáles.
"""
import html, json, os, subprocess, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_core_capas import shared_css, PAGE_CSS, _out_dir  # noqa: E402

LAYERS = [
    # (grupo, nombre, cuándo entra en la sesión)
    ("rule", "Instrucciones (CLAUDE.md y rules)",
     "Al arrancar, las que no llevan paths; las demás, al tocar un fichero que casa"),
    ("hook", "Hooks", "Saltan solos en un evento del harness; pueden bloquear"),
    ("skill", "Skills", "Al arrancar entra solo su description; el cuerpo, cuando el modelo la elige"),
    ("command", "Comandos", "Los tecleas tú: /nombre"),
    ("workflow", "Workflows", "Los tecleas tú; corren como script determinista"),
    ("agente", "Agentes", "Se lanzan a propósito, con contexto limpio"),
    ("pattern", "Patrones de código", "Los cita una rule o una skill al escribir código"),
    ("script", "Scripts", "Los ejecuta un hook, una skill o tú: gates y generadores"),
    ("plugin", "Plugins y MCP", "Instalados aparte; aportan tools, skills o agentes"),
]
SESSION = ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"]
SESSION_LABEL = {"SessionStart": "Arranca la sesión", "UserPromptSubmit": "Escribes un mensaje",
                 "PreToolUse": "Antes de cada tool", "PostToolUse": "Después de cada tool",
                 "Stop": "Termina la respuesta", "SessionEnd": "Se cierra la sesión"}
HOW = {"se teclea": "teclea", "cita": "cita", "evento": "evento", "instalada": "plug"}

# El recorrido de ejemplo: un proyecto web con pantallas, de «empieza» a producción.
EXAMPLE = [
    ("otto-briefing.sh", "Al abrir la sesión, Otto resume dónde estás"),
    ("arrancar", "«Empieza»: producto, requisitos, datos, stack, ética y superficie de ataque"),
    ("marca", "La identidad antes de dibujar"),
    ("producto", "Qué pantallas hacen falta y quién diseña cada una"),
    ("disenar-pantalla", "Cómo va a ser cada pantalla"),
    ("nueva-pantalla", "El CRUD en el frontend, primero con datos simulados"),
    ("escribir-tests", "Los tests del módulo"),
    ("verification-loops", "Nada es DONE sin verificar"),
    ("/qa-loop", "Lidia, Vera e Ignacio hasta media 9,0"),
    ("code-review-gate", "La revisión antes del merge"),
    ("/deploy", "A producción, con aprobación"),
]


def sh_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def session_events(settings):
    """evento → nº de hooks registrados en settings.json."""
    out = {}
    for ev, grupos in (settings.get("hooks") or {}).items():
        out[ev] = sum(len(g.get("hooks") or []) for g in grupos if isinstance(g, dict))
    return out


def family_maps(repo):
    """Las familias que ya existen en el repo: packs, familias de agente y grupos de skills."""
    scripts = os.path.join(repo, ".claude", "scripts")
    sys.path.insert(0, scripts)
    packs, agent_fam, skill_groups = {}, {}, []
    try:
        import gen_packs
        p, _ = gen_packs.cargar()
        donde, _ = gen_packs.pertenencia(p, gen_packs.piezas_en_disco())
        packs = {k: v[0][0] for k, v in donde.items() if v}
    except Exception as e:                     # defensive: sin packs, familias por defecto
        print(f"aviso: packs no disponibles ({e})", file=sys.stderr)
    try:
        import gen_agent_index
        agent_fam = dict(gen_agent_index.FAMILIAS)
    except Exception:
        pass
    try:
        import gen_skill_index
        skill_groups = list(gen_skill_index.GROUPS)
    except Exception:
        pass
    return packs, agent_fam, skill_groups


def family_of(n, packs, agent_fam, skill_groups, rule_always):
    g, name = n["group"], n["id"]
    if g == "hook":
        evs = n.get("eventos") or []
        return evs[0].split(":")[0] if evs else "sin registrar"
    if g == "rule":
        return "Siempre cargadas" if name in rule_always else "Al tocar sus ficheros (paths:)"
    if g == "agente":
        return agent_fam.get(name, "otros")
    if g == "plugin":
        return "marketplace " + name.split("@", 1)[1] if "@" in name else "plugins"
    if g == "skill":
        for label, rx in skill_groups:
            if rx.match(name):
                return label
    cat = {"skill": "skills", "command": "commands", "workflow": "workflows",
           "script": "scripts", "pattern": "patterns"}.get(g)
    key = name.lstrip("/")
    if g == "pattern":
        f = (n.get("files") or [""])[0]
        key = f[len("patterns/"):] if f.startswith("patterns/") else key
    pack = packs.get((cat, key))
    return f"pack {pack}" if pack else "sin pack"


def build_data(repo):
    full = os.path.join(repo, ".claude", "graph-dataset.full.json")
    if not os.path.exists(full):
        subprocess.run([sys.executable, os.path.join(repo, ".claude", "scripts", "gen_harness_graph.py")],
                       cwd=repo, capture_output=True, text=True)
    ds = sh_json(full)
    if not ds.get("nodes"):
        return None
    sys.path.insert(0, os.path.join(repo, ".claude", "scripts"))
    from check_instrucciones import frontmatter_paths
    rule_always = set()
    rdir = os.path.join(repo, ".claude", "rules")
    for f in os.listdir(rdir) if os.path.isdir(rdir) else []:
        if f.endswith(".md"):
            globs, _ = frontmatter_paths(open(os.path.join(rdir, f), encoding="utf-8").read())
            if globs is None:
                rule_always.add(f)
    packs, agent_fam, skill_groups = family_maps(repo)
    nodes = [n for n in ds["nodes"] if n.get("kind") != "agregado" and n["group"] != "roto"]
    idx = {n["id"]: i for i, n in enumerate(nodes)}
    out_nodes = []
    for n in nodes:
        out_nodes.append({"id": n["id"], "l": n["label"], "g": n["group"],
                          "d": (n.get("desc") or "").strip(), "f": (n.get("files") or [""])[0],
                          "h": HOW.get(n.get("descubrimiento", ""), "cita"),
                          "fi": n.get("fan_in", 0), "o": bool(n.get("huerfana")),
                          "ev": n.get("eventos") or [],
                          "fam": family_of(n, packs, agent_fam, skill_groups, rule_always)})
    edges = [[idx[e["from"]], idx[e["to"]]] for e in ds["edges"]
             if e["from"] in idx and e["to"] in idx and e["from"] != e["to"]]
    events = session_events(sh_json(os.path.join(repo, ".claude", "settings.json")))
    example, missing = [], []
    for pid, why in EXAMPLE:
        (example if pid in idx else missing).append({"id": pid, "why": why} if pid in idx else pid)
    return {"nodes": out_nodes, "edges": edges, "events": events, "session": SESSION,
            "sessionLabel": SESSION_LABEL,
            "layers": [{"g": g, "l": l, "when": w} for g, l, w in LAYERS],
            "example": example, "missing": missing,
            "meta": {"sha": (ds.get("meta") or {}).get("sha", "—"),
                     "date": (ds.get("meta") or {}).get("date", "—")}}


CSS = """
  .crumbs{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:13.5px;margin:6px 0 4px}
  .crumbs a{color:var(--blue);text-decoration:none}
  .crumbs a:hover{text-decoration:underline}
  .crumbs span.sep{color:var(--faint)}
  .tabs{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px}
  .tabs a{border:1px solid var(--line);background:var(--card);color:var(--ink);text-decoration:none;
    border-radius:var(--radius-pill);padding:6px 14px;font-size:13.5px}
  .tabs a.on{background:var(--navy);border-color:var(--navy);color:#fff}
  #lvl{font-family:var(--mono);font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:16px 0 2px}
  #title{margin:2px 0 6px;font-size:22px;color:var(--navy)}
  #lead{color:var(--muted);max-width:74ch;margin:0 0 6px;font-size:14.5px}
  #stage{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;margin:12px 0}
  #stage svg{display:block;width:100%;height:auto}
  #stage a:focus{outline:none}
  #stage a:focus rect.box{stroke-width:3}
  #stage a:hover rect.box{filter:brightness(.96)}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0;font-size:14.5px}
  .card p{margin:4px 0}
  .legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);margin:6px 0}
  .legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px;border:1.5px solid}
  @media(max-width:520px){#title{font-size:19px}.wrap{padding:18px 16px 50px}}
"""

JS = r"""
(function(){
var D=JSON.parse(document.getElementById('data').textContent);
var COL={rule:'#15803d',hook:'#b91c1c',skill:'#2563eb',command:'#0891b2',workflow:'#c2410c',
 agente:'#7c3aed',pattern:'#a16207',script:'#4b5563',plugin:'#db2777',ev:'#1b2a4a'};
var HOWL={teclea:'la tecleas',cita:'la encuentra el modelo',evento:'salta en un evento',plug:'instalada'};
var byId={},inE={},outE={};
D.nodes.forEach(function(n,i){byId[n.id]=i;inE[i]=[];outE[i]=[];});
D.edges.forEach(function(e){outE[e[0]].push(e[1]);inE[e[1]].push(e[0]);});
var L={};D.layers.forEach(function(l){L[l.g]=l;});
var $=function(id){return document.getElementById(id);};
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function cut(s,n){s=String(s||'');return s.length>n?s.slice(0,n-1)+'…':s;}
function W(){return Math.max(280,$('stage').clientWidth-24);}
function fams(g){var m={};D.nodes.forEach(function(n){if(n.g===g){(m[n.fam]=m[n.fam]||[]).push(n);}});return m;}
function href(parts){return '#/'+parts.map(encodeURIComponent).join('/');}
// Texto en varias líneas: corta por palabras y pone «…» si aún sobra
function wrap(s,cw,max){
  var ws=String(s||'').split(/\s+/),out=[],cur='';
  ws.forEach(function(w){if(!w)return;var t=cur?cur+' '+w:w;if(t.length<=cw||!cur){cur=t;}else{out.push(cur);cur=w;}});
  if(cur)out.push(cur);
  out=out.map(function(l){return cut(l,cw);});
  if(out.length>max){out=out.slice(0,max);out[max-1]=cut(out[max-1]+' …',cw);}
  return out;
}
function tw(w){return Math.max(6,Math.floor((w-20)/7.6));}
function lay(w,it){var c=tw(w);return {t:wrap(it.t,c,2),s:it.sub?wrap(it.sub,Math.floor(c*1.2),2):[]};}
function need(w,it){var L=lay(w,it);return 14+L.t.length*18+L.s.length*15+8;}
// Una caja enlazada: título, subtítulo y color de su capa
function box(x,y,w,h,it){
  var L=lay(w,it),s='',yy=y+22,col=it.col;
  L.t.forEach(function(l){s+='<text x="'+(x+10)+'" y="'+yy+'" font-size="13.5" font-weight="700" fill="#1b1b1f">'+esc(l)+'</text>';yy+=18;});
  yy+=1;
  L.s.forEach(function(l){s+='<text x="'+(x+10)+'" y="'+yy+'" font-size="11.5" fill="#55555f">'+esc(l)+'</text>';yy+=15;});
  return '<a href="'+it.link+'" aria-label="'+esc(it.aria||it.t)+'"><rect class="box" x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+
   '" rx="10" fill="'+col+'1a" stroke="'+col+'" stroke-width="1.5"/>'+s+'<title>'+esc(it.aria||it.t)+'</title></a>';
}
function grid(items,opt){
  var w=W(),gap=12,min=opt.min||170,cols=Math.max(1,Math.min(opt.max||6,Math.floor((w+gap)/(min+gap))));
  var bw=(w-gap*(cols-1))/cols,s='',rows=Math.ceil(items.length/cols),bh=opt.h||48;
  items.forEach(function(it){bh=Math.max(bh,need(bw,it));});
  items.forEach(function(it,i){var c=i%cols,r=Math.floor(i/cols);s+=box(c*(bw+gap),r*(bh+gap),bw,bh,it);});
  return {svg:s,h:rows*(bh+gap)-gap,w:w};
}
// Una cadena con flechas: en fila si cabe, en columna en el móvil
function chain(items,opt){
  var w=W(),n=items.length,gap=opt&&opt.gap||26,s='',horiz=!(opt&&opt.vertical)&&w>=n*130+(n-1)*gap,
      bw=horiz?(w-gap*(n-1))/n:Math.min(w,opt&&opt.maxw||420),bh=48;
  items.forEach(function(it){bh=Math.max(bh,need(bw,it));});
  items.forEach(function(it,i){
    var x=horiz?i*(bw+gap):0,y=horiz?0:i*(bh+gap);
    s+=box(x,y,bw,bh,it);
    if(i<n-1){s+=horiz?'<path d="M'+(x+bw+3)+' '+(bh/2)+'h'+(gap-8)+'" stroke="#6b6b76" stroke-width="1.6" marker-end="url(#ar)"/>'
      :'<path d="M'+(bw/2)+' '+(y+bh+3)+'v'+(gap-8)+'" stroke="#6b6b76" stroke-width="1.6" marker-end="url(#ar)"/>';}
  });
  return {svg:s,h:horiz?bh:n*(bh+gap)-gap,w:w};
}
var DEFS='<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#6b6b76"/></marker></defs>';
function svg(parts){
  var y=0,s='',w=W();
  parts.forEach(function(p){
    if(p.label){s+='<text x="0" y="'+(y+14)+'" font-size="11.5" font-weight="700" letter-spacing=".08em" fill="#6b6b76">'+esc(p.label.toUpperCase())+'</text>';y+=24;}
    if(p.g){s+='<g transform="translate(0,'+y+')">'+p.g.svg+'</g>';y+=p.g.h+18;}
  });
  return '<svg viewBox="0 0 '+w+' '+Math.max(40,y-6)+'" role="group" aria-label="'+esc($('title').textContent)+'">'+DEFS+s+'</svg>';
}
function show(lvl,title,lead,crumbs,stage,card){
  $('lvl').textContent=lvl;$('title').textContent=title;$('lead').innerHTML=lead;
  $('crumbs').innerHTML=crumbs.map(function(c,i){return i<crumbs.length-1?'<a href="'+c[1]+'">'+esc(c[0])+'</a><span class="sep">›</span>':'<b>'+esc(c[0])+'</b>';}).join(' ');
  $('stage').innerHTML=stage;$('card').innerHTML=card||'';$('card').style.display=card?'':'none';
  [].forEach.call(document.querySelectorAll('.tabs a'),function(a){a.classList.toggle('on',a.dataset.t===(lvl.indexOf('ejemplo')>=0?'ex':'lv'));});
  document.title=title+' · El harness por niveles';
}
var HOME=['La sesión','#/'];
function lvl1(){
  var ses=D.session.map(function(ev){var k=D.events[ev]||0;
    return {col:COL.ev,t:D.sessionLabel[ev]||ev,sub:ev+' · '+k+' hook'+(k===1?'':'s'),link:href(['f','hook',ev]),aria:ev+': '+k+' hooks'};});
  var otros=Object.keys(D.events).filter(function(e){return D.session.indexOf(e)<0;}).map(function(ev){
    return {col:COL.ev,t:ev,sub:D.events[ev]+' hook'+(D.events[ev]===1?'':'s'),link:href(['f','hook',ev])};});
  var capas=D.layers.map(function(l){var k=D.nodes.filter(function(n){return n.g===l.g;}).length;
    return {col:COL[l.g],t:l.l+' · '+k,sub:l.when,link:href(['c',l.g]),aria:l.l+' ('+k+'): '+l.when};});
  show('nivel 1 · la sesión','Qué pasa en una sesión, y qué entra en cada momento',
   'Arriba, los momentos de una sesión y cuántos hooks salta cada uno (de <code>settings.json</code>). Abajo, las capas del harness con <b>cuándo entra cada una</b>. Pulsa cualquier caja para bajar un nivel.',
   [HOME],svg([{label:'Los momentos de la sesión',g:chain(ses)},{label:'Otros eventos con hooks',g:grid(otros,{min:150,h:48})},
              {label:'Las capas y cuándo entran',g:grid(capas,{min:230,max:3,h:58})}]));
}
function lvl2(g){
  var l=L[g];if(!l)return lvl1();var m=fams(g),ks=Object.keys(m).sort(function(a,b){return m[b].length-m[a].length;});
  var items=ks.map(function(k){var ns=m[k];return {col:COL[g],t:k,sub:ns.length+' pieza'+(ns.length===1?'':'s')+' · '+ns.slice(0,3).map(function(n){return n.l;}).join(', '),link:href(['f',g,k]),aria:k+': '+ns.length+' piezas'};});
  show('nivel 2 · la capa',l.l,esc(l.when)+'. Están agrupadas en <b>'+ks.length+' familias</b>; pulsa una para ver sus piezas.',
   [HOME,[l.l,href(['c',g])]],svg([{g:grid(items,{min:220,max:4,h:58})}]));
}
function lvl3(g,fam){
  var ns=D.nodes.filter(function(n){return n.g===g&&n.fam===fam;}).sort(function(a,b){return b.fi-a.fi;});
  if(!ns.length)return lvl2(g);
  var items=ns.map(function(n){return {col:COL[g],t:n.l,sub:HOWL[n.h]+' · citada '+n.fi+(n.o?' · nadie la nombra':''),link:href(['p',n.id]),aria:n.l+' — '+(n.d||HOWL[n.h])};});
  var l=L[g]||{l:g};
  show('nivel 3 · la familia',fam,ns.length+' pieza'+(ns.length===1?'':'s')+' de '+esc(l.l)+', de la más citada a la que menos. «Cómo se usa» decide si depende de que su descripción esté bien escrita.',
   [HOME,[l.l,href(['c',g])],[fam,href(['f',g,fam])]],svg([{g:grid(items,{min:200,max:4,h:56})}]));
}
function lvl4(id){
  var i=byId[id];if(i===undefined)return lvl1();var n=D.nodes[i],l=L[n.g]||{l:n.g};
  function col(list,title){
    var uniq=list.filter(function(v,k){return list.indexOf(v)===k;}).sort(function(a,b){return D.nodes[b].fi-D.nodes[a].fi;});
    var top=uniq.slice(0,8).map(function(j){var m=D.nodes[j];return {col:COL[m.g]||'#4b5563',t:m.l,sub:(L[m.g]||{l:m.g}).l,link:href(['p',m.id])};});
    var more=uniq.length>8?' (las 8 más citadas de '+uniq.length+')':'';
    return top.length?{label:title+' · '+uniq.length+more,g:grid(top,{min:190,max:4,h:50})}:{label:title+' · ninguna'};
  }
  var me={col:COL[n.g]||'#4b5563',t:n.l,sub:HOWL[n.h],link:href(['p',n.id])};
  var card='<p><b>Para qué:</b> '+(n.d?esc(n.d):'<i>sin descripción</i>')+'</p><p><b>Fichero:</b> <code>.claude/'+esc(n.f)+'</code></p>'+
    '<p><b>Cómo se usa:</b> '+HOWL[n.h]+(n.ev.length?' — '+n.ev.map(esc).join(', '):'')+' · la citan '+inE[i].filter(function(v,k,a){return a.indexOf(v)===k;}).length+' piezas'+(n.o?' · <b>nadie la nombra</b>':'')+'</p>';
  show('nivel 4 · la pieza',n.l,'Lo que la cita (cómo se llega a ella) y lo que usa (a dónde lleva). Cada caja abre esa pieza.',
   [HOME,[l.l,href(['c',n.g])],[n.fam,href(['f',n.g,n.fam])],[n.l,href(['p',n.id])]],
   svg([col(inE[i],'La citan'),{label:'La pieza',g:grid([me],{min:260,max:1,h:52})},col(outE[i],'Usa')]),card);
}
function example(){
  var it=D.example.map(function(s,k){var n=D.nodes[byId[s.id]];return {col:COL[n.g],t:(k+1)+'. '+n.l,sub:s.why,link:href(['p',n.id]),aria:n.l+': '+s.why};});
  var miss=D.missing.length?'<p>Pasos del ejemplo que ya no existen en disco y se han quitado: <code>'+D.missing.map(esc).join('</code> · <code>')+'</code></p>':'';
  show('el ejemplo · un proyecto web','Un proyecto de ejemplo, de «empieza» a producción',
   'Una web con pantallas, paso a paso: qué pieza actúa en cada momento. Pulsa un paso para ver la pieza y a dónde lleva.',
   [['Proyecto de ejemplo','#/ejemplo']],svg([{g:chain(it,{vertical:true,maxw:620,gap:22})}]),miss);
}
function route(){
  var p=(location.hash||'#/').slice(2).split('/').map(decodeURIComponent);
  if(p[0]==='c')lvl2(p[1]);else if(p[0]==='f')lvl3(p[1],p.slice(2).join('/'));
  else if(p[0]==='p')lvl4(p.slice(1).join('/'));else if(p[0]==='ejemplo')example();else lvl1();
}
window.addEventListener('hashchange',function(){route();window.scrollTo(0,$('crumbs').offsetTop-10);});
var t;window.addEventListener('resize',function(){clearTimeout(t);t=setTimeout(route,120);});
route();
})();
"""


def render(data, gen):
    legend = "".join(f'<span><i style="border-color:{c};background:{c}1a"></i>{html.escape(t)}</span>'
                     for t, c in (("instrucciones", "#15803d"), ("hooks", "#b91c1c"), ("skills", "#2563eb"),
                                  ("comandos", "#0891b2"), ("workflows", "#c2410c"), ("agentes", "#7c3aed"),
                                  ("patrones", "#a16207"), ("scripts", "#4b5563"), ("plugins", "#db2777")))
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>El harness por niveles</title>
<link rel="icon" href="data:,">  <!-- sin esto, el navegador pide /favicon.ico y la consola sale con un 404 -->

<!-- entradilla: El harness entero en diagramas que se abren: sesión, capas, familias y piezas. -->
<style>{shared_css()}</style><style>{PAGE_CSS}{CSS}</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="wrap">
<p class="eyebrow">core · el harness por niveles</p>
<h1>El harness, de lo general a lo concreto</h1>
<p class="lead">{len(data['nodes'])} piezas, en cuatro niveles: la sesión, la capa, la familia y la
pieza. Cada caja abre el nivel siguiente; la ruta de arriba te devuelve.</p>
<nav class="tabs" aria-label="Vistas"><a href="#/" data-t="lv">Por niveles</a><a href="#/ejemplo" data-t="ex">Proyecto de ejemplo</a></nav>
<div class="legend">{legend}</div>
<nav class="crumbs" id="crumbs" aria-label="Ruta"></nav>
<p id="lvl"></p><h2 id="title"></h2><p id="lead"></p>
<div id="stage"></div><div class="card" id="card" style="display:none"></div>
<footer>Generada por <code>gen_core_levels.py</code> el {gen} desde <code>graph-dataset.full.json</code>
(sha {html.escape(str(data['meta']['sha']))}) y <code>settings.json</code> — no editar a mano.</footer>
</div>
<script type="application/json" id="data">{payload}</script>
<script>{JS}</script>
</body></html>"""


def self_test():
    """Control negativo: un paso del ejemplo que no existe se quita y se nombra; las familias salen."""
    repo = subprocess.run(["git", "-C", HERE, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip()
    global EXAMPLE
    saved = EXAMPLE
    EXAMPLE = saved + [("no-existe-xyz", "plantado")]
    try:
        d = build_data(repo)
    finally:
        EXAMPLE = saved
    ok = d is not None
    if ok and "no-existe-xyz" not in d["missing"]:
        print("✗ self-test: el paso plantado no salió en missing"); ok = False
    if ok and any(s["id"] == "no-existe-xyz" for s in d["example"]):
        print("✗ self-test: el paso plantado se pintó"); ok = False
    if ok and not all(n["fam"] for n in d["nodes"]):
        print("✗ self-test: hay piezas sin familia"); ok = False
    if ok and len({n["fam"] for n in d["nodes"] if n["g"] == "hook"}) < 3:
        print("✗ self-test: los hooks deberían repartirse en ≥3 eventos"); ok = False
    print("OK: self-test" if ok else "self-test FALLA")
    return 0 if ok else 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = os.path.abspath(sys.argv[1])
    repo = subprocess.run(["git", "-C", plan, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip() or os.getcwd()
    data = build_data(repo)
    if data is None:
        print("✗ sin inventario: corre python3 .claude/scripts/gen_harness_graph.py", file=sys.stderr)
        return 2
    out = os.path.join(_out_dir(plan), "core-levels.html")
    open(out, "w", encoding="utf-8").write(render(data, date.today().isoformat()))
    print(f"OK core-levels.html — {len(data['nodes'])} piezas, {len(data['edges'])} aristas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
