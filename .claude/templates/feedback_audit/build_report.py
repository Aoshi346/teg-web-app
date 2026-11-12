#!/usr/bin/env python3
"""
Informe AUTOCONTENIDO (imágenes embebidas base64, sin CDN, abre sin servidor).
Por item: 📄 texto · 📋 cita verbatim (CTRL+F) · 🔎 interpretación · estado + % precisión ·
ANTES / ACTUAL / DESPUÉS · por qué (evidencia) · qué hacer. Filtros + copiar-pendientes-md + PDF.
Tokens compartidos de .claude/templates/html/base.html (navy/paper editorial).

Uso:
    python3 build_report.py <audit_dir>            # -> <audit_dir>/informe.html

Cabecera y bloque de transparencia se parametrizan desde items.json -> meta:
  meta.title, meta.eyebrow, meta.lead, meta.report_notes (lista de strings, opcional).
Dependencia opcional: Pillow (recomprime imágenes). Sin Pillow embebe el jpg tal cual.
"""
import json, os, sys, html, base64, io

MAXW = 820
QUALITY = 52

try:
    from PIL import Image
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

VMAP = {
    "done": ("✅ Hecho", "#1a7f4b", False),
    "partial": ("⚠️ Parcial", "#B26A00", True),
    "notdone": ("❌ No hecho", "#C1262C", True),
    "blocked": ("🟥 Bloqueado", "#5b6577", True),
    "review": ("🟪 A revisar", "#6b3fa0", True),
}


def esc(s):
    return html.escape(str(s or ""))


def make_embed(audit_dir):
    cache = {}

    def embed(relpath):
        if not relpath:
            return ""
        if relpath in cache:
            return cache[relpath]
        p = os.path.join(audit_dir, relpath)
        if not os.path.exists(p):
            cache[relpath] = ""
            return ""
        data = None
        if HAVE_PIL:
            try:
                im = Image.open(p).convert("RGB")
                if im.width > MAXW:
                    im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=QUALITY, optimize=True)
                data = buf.getvalue()
            except Exception:
                data = None
        if data is None:
            data = open(p, "rb").read()
        uri = "data:image/jpeg;base64," + base64.b64encode(data).decode()
        cache[relpath] = uri
        return uri

    return embed


def verdict_of(it):
    v = it.get("verdict")
    if v in VMAP:
        return v
    st = it.get("status", "backlog")
    return {"backlog": "notdone", "doing": "partial", "review": "review",
            "blocked": "blocked", "done": "done"}.get(st, "notdone")


def pct_color(p):
    return "#1a7f4b" if p >= 85 else ("#B26A00" if p >= 55 else "#C1262C")


def main(audit_dir):
    embed = make_embed(audit_dir)
    d = json.load(open(os.path.join(audit_dir, "items.json")))
    meta = d["meta"]; items = d["items"]
    epics = meta.get("epics", {})
    pages = {p["code"]: p for p in meta.get("pages", [])}
    for it in items:
        it["_v"] = verdict_of(it)

    cnt = {k: 0 for k in VMAP}
    for it in items:
        cnt[it["_v"]] += 1
    total = len(items) or 1
    done = cnt["done"]; pend = len(items) - done
    pct = round(done * 100 / total)

    bypage, byepic = {}, {}
    for it in items:
        bypage.setdefault(it["page"], {k: 0 for k in VMAP})[it["_v"]] += 1
        byepic.setdefault(it.get("epic", "A"), {k: 0 for k in VMAP})[it["_v"]] += 1

    def chip(txt, bg, fg="#fff"):
        return f'<span class="chip" style="background:{bg};color:{fg}">{esc(txt)}</span>'

    def bar(c, tot):
        seg = ""
        for v in ["done", "partial", "review", "blocked", "notdone"]:
            n = c.get(v, 0)
            if n:
                seg += f'<i style="width:{n*100/tot:.2f}%;background:{VMAP[v][1]}" title="{VMAP[v][0]}: {n}"></i>'
        return f'<div class="bar">{seg}</div>'

    ov = [f'<div class="kpi"><b>{len(items)}</b><span>items</span></div>',
          f'<div class="kpi ok"><b>{done}</b><span>Hecho</span></div>',
          f'<div class="kpi"><b style="color:#B26A00">{cnt["partial"]}</b><span>Parcial</span></div>',
          f'<div class="kpi"><b style="color:#C1262C">{cnt["notdone"]}</b><span>No hecho</span></div>',
          f'<div class="kpi"><b style="color:#6b3fa0">{cnt["review"]}</b><span>A revisar</span></div>',
          f'<div class="kpi"><b style="color:#5b6577">{cnt["blocked"]}</b><span>Bloqueado</span></div>']

    rows = []
    for code in sorted(bypage, key=lambda c: -sum(v for k, v in bypage[c].items() if k != "done")):
        c = bypage[code]; tot = sum(c.values()) or 1; nm = pages.get(code, {}).get("name", code)
        rows.append(f'<tr><td><b>{esc(code)}</b> <span class="muted">{esc(nm)}</span></td>'
                    f'<td class="num">{sum(c.values())}</td><td>{bar(c,tot)}</td>'
                    f'<td class="num" style="color:#1a7f4b">{c["done"]}</td>'
                    f'<td class="num" style="color:#C1262C">{c["notdone"]+c["partial"]}</td>'
                    f'<td class="num" style="color:#5b6577">{c["blocked"]}</td>'
                    f'<td class="num" style="color:#6b3fa0">{c["review"]}</td></tr>')

    eleg = []
    for ec, ev in byepic.items():
        nm = epics.get(ec, {}).get("name", ec); tot = sum(ev.values()) or 1
        eleg.append(f'<div class="erow"><div class="ehead">{chip(ec, epics.get(ec,{}).get("color","#444"))} '
                    f'<span class="muted">{esc(nm)}</span> <b>{sum(ev.values())}</b></div>{bar(ev,tot)}</div>')

    page_opts = "".join(f'<option value="{c}">{c} · {esc(pages.get(c,{}).get("name",c))}</option>' for c in sorted(bypage))
    epic_opts = "".join(f'<option value="{ec}">{ec} · {esc(epics.get(ec,{}).get("name",ec))}</option>' for ec in sorted(byepic))

    def idnum(iid):
        m = iid.rsplit("-", 1)
        return int(m[1]) if len(m) == 2 and m[1].isdigit() else 0

    items_sorted = sorted(items, key=lambda it: (it.get("page_order", 99), it["page"], idnum(it["id"])))

    def imgblk(it, uri, label, sub=""):
        cap = f'<figcaption>{label}{f"<small>{sub}</small>" if sub else ""}</figcaption>'
        if uri:
            return (f'<figure class="ev">{cap}'
                    f'<img loading="lazy" src="{uri}" alt="{label} {esc(it["id"])}" '
                    f'onclick="window.open(this.src)" style="cursor:zoom-in"></figure>')
        return f'<figure class="ev noev">{cap}<div class="nobox">sin captura</div></figure>'

    cards = []
    for it in items_sorted:
        v = it["_v"]; lab, col, _ = VMAP[v]
        p = int(it.get("precision_pct", 0) or 0)
        before_uri = embed(it.get("before2", ""))
        after_uri = embed(it.get("after", ""))
        fut_uri = embed(it.get("after_fix", ""))
        if fut_uri:
            third = imgblk(it, fut_uri, "DESPUÉS", "tras los cambios")
        elif v == "done":
            third = ('<figure class="ev fut done"><figcaption>DESPUÉS<small>tras los cambios</small></figcaption>'
                     '<div class="nobox">✓ Ya aplicado — ver columna ACTUAL</div></figure>')
        else:
            third = ('<figure class="ev fut"><figcaption>DESPUÉS<small>tras los cambios</small></figcaption>'
                     '<div class="nobox">⏳ Pendiente — se rellenará al implementar el cambio</div></figure>')
        evs = (imgblk(it, before_uri, "ANTES", "versión anterior")
               + imgblk(it, after_uri, "ACTUAL", "estado hoy") + third)
        why = it.get("why") or it.get("note", "")
        howto = it.get("howto") or ""
        interp = it.get("interpretacion") or ""
        orig = it.get("texto_original") or ""
        if orig and orig != it.get("text", ""):
            orig_block = (f'<div class="orig"><span class="qlab">📋 Cita verbatim (CTRL+F):</span>'
                          f'<span class="origtxt">{esc(orig)}</span></div>')
        else:
            orig_block = ""
        ep = it.get("epic", "A")
        cards.append(f'''
<article class="card" data-v="{v}" data-page="{it['page']}" data-epic="{ep}">
  <div class="cardhead">
    <span class="badge" style="background:{col}">{lab}</span>
    <span class="pct" style="color:{pct_color(p)}" title="precisión/confianza">{p}%</span>
    {chip(it['page'], '#1B2A4A')}
    {chip(ep, epics.get(ep,{}).get('color','#444'))}
    <span class="sev">{esc(it.get('severity',''))}</span>
    <span class="id">{esc(it['id'])}</span>
  </div>
  <p class="docq"><span class="qlab">📄 Item:</span> {esc(it['text'])}</p>
  {orig_block}
  {f'<p class="interp"><span class="qlab">🔎 Interpretación:</span> {esc(interp)}</p>' if interp else ''}
  <div class="evrow">{evs}</div>
  <div class="why"><b>Por qué ({lab.split(" ",1)[-1].lower()}):</b> {esc(why)}</div>
  {f'<div class="howto"><b>Qué hacer:</b> {esc(howto)}</div>' if v!="done" and howto else ''}
</article>''')

    md_lines = [f"# {meta.get('title','Feedback audit')} — pendiente\n"]
    for it in items_sorted:
        if it["_v"] == "done":
            continue
        md_lines.append(f"- [{VMAP[it['_v']][0]}] **{it['id']}** ({it['page']}, {it.get('precision_pct',0)}%): {it['text'][:160]}")
        if it.get("howto"):
            md_lines.append(f"    - Qué hacer: {it['howto']}")
    md_js = json.dumps("\n".join(md_lines))

    title = meta.get("title", "Feedback audit")
    eyebrow = meta.get("eyebrow", "Auditoría de feedback · verificado en vivo")
    lead = meta.get("lead", "Verificación item por item (código + en vivo con Playwright). Cada item lleva "
                            "su cita verbatim, interpretación, estado, % de precisión y 3 capturas: ANTES · ACTUAL · DESPUÉS.")
    notes = meta.get("report_notes", [])
    applybox = ""
    if notes:
        lis = "".join(f"<li>{esc(n)}</li>" for n in notes)
        applybox = f'<div class="applybox"><h3>🛠 Notas de transparencia</h3><ul>{lis}</ul></div>'

    doc = f'''<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>
/* tokens compartidos de .claude/templates/html/base.html (navy/paper editorial) */
:root{{--ink:#1b1b1f;--mut:#6b6b76;--faint:#9a9aa4;--paper:#f6f4ef;--card:#fff;--line:#e4e0d7;
  --navy:#1b2a4a;--accent:#c2410c;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
*{{box-sizing:border-box}}
body{{margin:0;font:15px/1.55 var(--sans);color:var(--ink);background:var(--paper)}}
header.top{{border-bottom:1px solid var(--line);padding:40px 0 26px;
  background:radial-gradient(1000px 280px at 82% -45%,#fff,transparent 70%),var(--paper)}}
header.top .inn{{max-width:1180px;margin:0 auto;padding:0 22px}}
header.top .eyebrow{{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0 0 10px}}
header.top h1{{margin:0 0 10px;font-size:clamp(24px,4vw,38px);letter-spacing:-.02em;color:var(--ink)}}
header.top p.lead{{margin:0;font-size:16px;color:var(--mut);max-width:80ch}}
header.top .navlinks{{margin-top:16px;display:flex;gap:10px;flex-wrap:wrap}}
header.top .navlinks a{{font-size:13px;font-weight:600;text-decoration:none;color:var(--navy);border:1px solid var(--line);background:#fff;padding:7px 12px;border-radius:9px}}
.wrap{{max-width:1180px;margin:0 auto;padding:22px}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}}
.kpi{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 18px;min-width:104px;text-align:center}}
.kpi b{{display:block;font-size:30px;line-height:1}} .kpi span{{font-size:12px;color:var(--mut)}} .kpi.ok b{{color:#1a7f4b}}
.bigbar{{height:26px;border-radius:8px;overflow:hidden;display:flex;border:1px solid var(--line);margin:6px 0 2px}}
.bigbar i{{display:block;height:100%}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin:8px 0 2px}}
.legend i{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px}}
h2{{font-size:17px;margin:26px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}}
table{{width:100%;border-collapse:collapse;font-size:13px;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
th,td{{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line)}} th{{background:#f3efe6;font-size:12px}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;width:54px}}
.bar{{height:12px;border-radius:6px;overflow:hidden;display:flex;background:#eee;min-width:120px}} .bar i{{display:block;height:100%}}
.muted{{color:var(--mut)}} .erow{{margin:6px 0}} .ehead{{display:flex;gap:8px;align-items:center;font-size:13px;margin-bottom:3px}}
.chip{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600}}
.toolbar{{position:sticky;top:0;z-index:5;background:#fbfaf7;border-bottom:1px solid var(--line);padding:10px 0;display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
.toolbar select,.toolbar button{{font:13px inherit;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer}}
.toolbar button.act{{background:var(--navy);color:#fff;border-color:var(--navy)}}
.card{{background:#fff;border:1px solid var(--line);border-left:5px solid #ccc;border-radius:12px;padding:14px 16px;margin:12px 0}}
.card[data-v=done]{{border-left-color:#1a7f4b}} .card[data-v=partial]{{border-left-color:#B26A00}}
.card[data-v=notdone]{{border-left-color:#C1262C}} .card[data-v=blocked]{{border-left-color:#5b6577}} .card[data-v=review]{{border-left-color:#6b3fa0}}
.cardhead{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px}}
.badge{{color:#fff;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px}}
.pct{{font-weight:800;font-size:14px}}
.sev{{font-size:11px;color:var(--mut);border:1px solid var(--line);border-radius:6px;padding:1px 6px}}
.applybox{{background:#eef3f7;border:1px solid #cfe0ec;border-left:4px solid var(--navy);border-radius:12px;padding:14px 18px;margin:18px 0 8px}}
.applybox h3{{margin:0 0 8px;font-size:15px}} .applybox ul{{margin:0;padding-left:18px}} .applybox li{{font-size:13.5px;margin:4px 0}}
.id{{font-size:11px;color:var(--mut);font-family:ui-monospace,Menlo,monospace;margin-left:auto}}
.qlab{{font-weight:700;color:var(--navy)}}
.docq{{margin:0 0 6px;font-size:15px;background:#f7f5ef;border-radius:8px;padding:9px 12px}}
.orig{{margin:0 0 8px;font-size:13px;background:#fff;border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:8px 12px}}
.orig .origtxt{{display:block;margin-top:4px;font-family:var(--mono);font-size:12.5px;color:#333;white-space:pre-wrap;user-select:all}}
.interp{{margin:0 0 10px;font-size:14px;color:#333}}
.evrow{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:6px 0 10px}}
@media(max-width:760px){{.evrow{{grid-template-columns:1fr}}}}
.ev{{margin:0}} .ev figcaption{{font-size:11px;font-weight:700;color:var(--mut);margin-bottom:4px;line-height:1.25}}
.ev figcaption small{{display:block;font-weight:400;font-size:10px;color:var(--faint)}}
.ev img{{width:100%;border:1px solid var(--line);border-radius:8px;display:block}}
.ev .nobox{{background:#f3efe6;color:var(--mut);border:1px dashed var(--line);border-radius:8px;padding:24px 12px;text-align:center;font-size:12.5px;min-height:90px;display:flex;align-items:center;justify-content:center}}
.ev.fut .nobox{{background:#fff7ed;border-color:#f3c9a8;color:#9a4b16}}
.ev.fut.done .nobox{{background:#eef7f0;border-color:#cfe9da;color:#1a7f4b}}
.why{{background:#eef3f7;border-radius:8px;padding:10px 12px;font-size:14px;margin-bottom:8px}}
.howto{{background:#eaf6ef;border:1px solid #cfe9da;border-radius:8px;padding:10px 12px;font-size:14px}} .howto b{{color:#1a7f4b}}
.count{{font-size:13px;color:var(--mut);margin-left:auto}}
@media print{{.toolbar{{position:static}}.card{{break-inside:avoid}}}}
</style></head><body>
<header class="top"><div class="inn">
  <p class="eyebrow">{esc(eyebrow)}</p>
  <h1>{esc(title)}</h1>
  <p class="lead">{esc(lead)}</p>
</div></header>
<div class="wrap">
  <div class="kpis">{''.join(ov)}</div>
  <div class="bigbar">
    <i style="width:{cnt['done']*100/total:.2f}%;background:#1a7f4b"></i>
    <i style="width:{cnt['partial']*100/total:.2f}%;background:#B26A00"></i>
    <i style="width:{cnt['review']*100/total:.2f}%;background:#6b3fa0"></i>
    <i style="width:{cnt['blocked']*100/total:.2f}%;background:#5b6577"></i>
    <i style="width:{cnt['notdone']*100/total:.2f}%;background:#C1262C"></i>
  </div>
  <div class="legend">
    <span><i style="background:#1a7f4b"></i>Hecho {cnt['done']}</span>
    <span><i style="background:#B26A00"></i>Parcial {cnt['partial']}</span>
    <span><i style="background:#6b3fa0"></i>A revisar {cnt['review']}</span>
    <span><i style="background:#5b6577"></i>Bloqueado {cnt['blocked']}</span>
    <span><i style="background:#C1262C"></i>No hecho {cnt['notdone']}</span>
    <span><b>{pct}% hecho</b> · {pend} pendientes</span>
  </div>
  {applybox}
  <h2>Avance por página</h2>
  <table><thead><tr><th>Página</th><th class="num">Tot</th><th>Progreso</th>
    <th class="num">✓</th><th class="num">✗</th><th class="num">⛔</th><th class="num">?</th></tr></thead>
    <tbody>{''.join(rows)}</tbody></table>
  <h2>Avance por área (epic)</h2>
  {''.join(eleg)}
  <h2>Items · verbatim · interpretación · evidencia</h2>
  <div class="toolbar">
    <button class="act" data-f="all">Todos</button>
    <button data-f="pend">Solo pendientes</button>
    <button data-f="notdone">❌ No hecho</button>
    <button data-f="partial">⚠️ Parcial</button>
    <button data-f="review">🟪 Revisar</button>
    <button data-f="blocked">🟥 Bloqueado</button>
    <button data-f="done">✅ Hecho</button>
    <select id="fpage"><option value="">— Página —</option>{page_opts}</select>
    <select id="fepic"><option value="">— Área —</option>{epic_opts}</select>
    <button id="copy">⧉ Copiar pendientes (md)</button>
    <button onclick="window.print()">🖨 PDF</button>
    <span class="count" id="count"></span>
  </div>
  <div id="list">{''.join(cards)}</div>
</div>
<script>
const MD={md_js};
let fv="all",fp="",fe="";
const cards=[...document.querySelectorAll('.card')];
function apply(){{
  let n=0;
  cards.forEach(c=>{{
    const v=c.dataset.v; let ok=true;
    if(fv==="pend") ok=v!=="done";
    else if(fv!=="all") ok=v===fv;
    if(ok&&fp) ok=c.dataset.page===fp;
    if(ok&&fe) ok=c.dataset.epic===fe;
    c.style.display=ok?"":"none"; if(ok)n++;
  }});
  document.getElementById('count').textContent=n+" items";
}}
document.querySelectorAll('.toolbar button[data-f]').forEach(b=>b.onclick=()=>{{
  fv=b.dataset.f;
  document.querySelectorAll('.toolbar button[data-f]').forEach(x=>x.classList.remove('act'));
  b.classList.add('act'); apply();
}});
document.getElementById('fpage').onchange=e=>{{fp=e.target.value;apply()}};
document.getElementById('fepic').onchange=e=>{{fe=e.target.value;apply()}};
document.getElementById('copy').onclick=()=>{{navigator.clipboard.writeText(MD);
  const b=document.getElementById('copy');const t=b.textContent;b.textContent="✓ Copiado";setTimeout(()=>b.textContent=t,1500);}};
apply();
</script>
</body></html>'''
    out = os.path.join(audit_dir, "informe.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    mb = len(doc) / 1024 / 1024
    print(f"OK -> {out}  ({mb:.1f} MB, {len(items)} items, {done} hechos, {pend} pendientes, PIL={HAVE_PIL})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
