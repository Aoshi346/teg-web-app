#!/usr/bin/env python3
"""gen_modulos.py — `modulos.html`: la torre de control de un plan repartido en módulos.

Una solapa por módulo: su puerto, su base de datos, su rama, su sesión SpecKit, de qué ficheros es
dueño, qué tickets cubre y cómo va (el avance sale de los items de `report.json` de su página).
Cosechado de accounting_AMC (sub-ola 4.18, WA-19), donde vivía como copia local del kit.

Por qué una página y no una pestaña por módulo: ocho entradas más desbordarían la topnav
(`rules/report-kit.md` §5d). Es página opcional (`nav.json#optional_pages`): solo existe si el
plan trae `modulos.json`, y `build.py` la genera entonces.

Uso:  python3 gen_modulos.py <dir-del-plan>
Lee:  <plan>/modulos.json (+ <plan>/report.json para el avance)

modulos.json — claves en inglés; las del fichero de AMC (`nombre`, `que_es`, `rama`…) se aceptan:
  {"title": "…", "intro": "…",
   "modules": [{"id", "name", "page", "what", "panel", "api", "db", "redis", "branch", "speckit",
                "tickets": [], "status", "owns": [], "missing", "blocked", "overlap", "start"}],
   "parent_files": [{"f", "why"}],
   "split_files": [{"f", "commits", "lines", "into", "how"}]}
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# clave inglesa → clave heredada de AMC
LEGACY = {"modules": "modulos", "name": "nombre", "page": "pagina", "what": "que_es", "db": "base",
          "branch": "rama", "tickets": "jira", "status": "estado_codigo", "owns": "dueno",
          "missing": "falta", "blocked": "bloqueado", "overlap": "solape", "parent_files": "del_padre",
          "split_files": "partidos", "why": "por_que", "lines": "lineas", "into": "en", "how": "como"}

STATUS = {
    "construido": ("var(--green, #15803d)", "construido"), "built": ("var(--green, #15803d)", "construido"),
    "esqueleto": ("#b45309", "esqueleto"), "skeleton": ("#b45309", "esqueleto"),
    "a medias": ("#b45309", "a medias"), "partial": ("#b45309", "a medias"),
    "vacío": ("#b42318", "vacío"), "empty": ("#b42318", "vacío"),
    "sin arrancar": ("#6b6b76", "sin arrancar"), "not started": ("#6b6b76", "sin arrancar"),
}


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""), quote=True)


def get(d: dict, key: str, default=None):
    if not isinstance(d, dict):
        return default
    if key in d:
        return d[key]
    return d.get(LEGACY.get(key, key), default)


def shared_block() -> str:
    """El CSS común, copiado LITERAL de index.template.html (regla nº 5 del report-kit)."""
    t = (HERE / "index.template.html").read_text(encoding="utf-8")
    m = re.search(r"/\* SHARED:BEGIN \*/.*?/\* SHARED:END \*/", t, re.S)
    return m.group(0) if m else ""


def progress_by_page(report: dict) -> dict:
    """Avance por página. Los items citan la página por su `code`; modulos.json, por su nombre."""
    code_of = {p.get("name"): p.get("code") for p in (report.get("meta") or {}).get("pages", [])
               if isinstance(p, dict)}
    by_code: dict = {}
    for it in report.get("items", []):
        d = by_code.setdefault(it.get("page") or "", {"total": 0, "done": 0, "blocked": 0})
        d["total"] += 1
        d["done"] += it.get("status") == "done"
        d["blocked"] += it.get("status") == "blocked"
    return {name: by_code.get(code, {"total": 0, "done": 0, "blocked": 0}) for name, code in code_of.items()} | \
        {code: v for code, v in by_code.items() if code}


def module_panel(m: dict, i: int, prog: dict) -> tuple[str, str]:
    mid = esc(get(m, "id"))
    color, label = STATUS.get(str(get(m, "status", "")).lower(), ("#6b6b76", get(m, "status", "")))
    av = prog.get(get(m, "page") or "", {"total": 0, "done": 0, "blocked": 0})
    pct = round(av["done"] * 100 / av["total"]) if av["total"] else 0
    sel = ' aria-selected="true"' if i == 0 else ""
    tab = (f'<button class="solapa" role="tab" data-panel="m-{mid}"{sel}>'
           f'<span class="punto" style="background:{color}"></span>{esc(get(m, "name", get(m, "id")))}'
           + (f'<span class="cuenta">{av["total"]}</span>' if av["total"] else "") + "</button>")
    tickets = " · ".join(f"<code>{esc(t)}</code>" for t in get(m, "tickets") or []) or "<em>sin ticket propio</em>"
    owns = "".join(f"<li><code>{esc(f)}</code></li>" for f in get(m, "owns") or []) or "<li><em>sin declarar</em></li>"
    notes = ""
    if get(m, "blocked"):
        notes += f'<p class="aviso bloqueo"><b>Bloqueado.</b> {esc(get(m, "blocked"))}</p>'
    if get(m, "overlap"):
        notes += f'<p class="aviso"><b>Solape declarado.</b> {esc(get(m, "overlap"))}</p>'
    facts = [("Panel", f"127.0.0.1:{get(m, 'panel')}" if get(m, "panel") else ""),
             ("API", f"127.0.0.1:{get(m, 'api')}" if get(m, "api") else ""),
             ("Base de datos", get(m, "db")), ("Redis", f"/{get(m, 'redis')}" if get(m, "redis") is not None else ""),
             ("Rama", get(m, "branch")), ("SpecKit", get(m, "speckit"))]
    grid = "".join(f'<div class="dato"><span>{k}</span><b>{esc(v)}</b></div>' for k, v in facts if v)
    cmds = []
    if get(m, "panel"):
        cmds.append(f"ssh -N -L {get(m, 'panel')}:127.0.0.1:{get(m, 'panel')} <usuario>@<servidor>")
    if get(m, "start"):
        cmds.append(str(get(m, "start")))
    elif get(m, "branch"):
        cmds.append(f"claude --worktree {get(m, 'id')}")
    cmd_html = (f'<div class="comandos"><h3>Cómo se levanta</h3><pre><code>{esc(chr(10).join(cmds))}</code></pre></div>'
                if cmds else "")
    blocked = f" · {av['blocked']} bloqueada(s)" if av["blocked"] else ""
    panel = f"""
<section class="panel" id="m-{mid}"{'' if i == 0 else ' hidden'}>
  <header class="cabecera">
    <div><h2>{esc(get(m, 'name', get(m, 'id')))} <span class="badge" style="background:{color}">{esc(label)}</span></h2>
      <p class="que-es">{esc(get(m, 'what', ''))}</p></div>
    <div class="avance" title="{av['done']} de {av['total']} tareas">
      <div class="barra"><i style="width:{pct}%"></i></div>
      <span>{av['done']}/{av['total']} hechas{blocked}</span></div>
  </header>
  {notes}
  <div class="rejilla">{grid}</div>
  <div class="dos">
    <div><h3>Qué falta</h3><p class="falta">{esc(get(m, 'missing', '—'))}</p><h3>Tickets</h3><p>{tickets}</p></div>
    <div><h3>Dueño de estos ficheros <small>— fuera de aquí, se pide</small></h3><ul class="ficheros">{owns}</ul></div>
  </div>
  {cmd_html}
</section>"""
    return tab, panel


def split_section(data: dict) -> str:
    split = get(data, "split_files") or []
    parent = get(data, "parent_files") or []
    if isinstance(parent, dict):  # forma de AMC: {"ficheros": [...]}
        parent = parent.get("ficheros") or parent.get("files") or []
    if not split and not parent:
        return ""
    rows_s = "".join(
        f'<tr><td><code>{esc(get(p, "f"))}</code></td><td class="num">{esc(get(p, "commits", ""))}</td>'
        f'<td class="num">{esc(get(p, "lines", ""))}</td><td><code>{esc(get(p, "into", ""))}</code><br>'
        f'<small>{esc(get(p, "how", ""))}</small></td></tr>' for p in split)
    rows_p = "".join(f'<tr><td><code>{esc(get(p, "f"))}</code></td><td>{esc(get(p, "why", ""))}</td></tr>'
                     for p in parent)
    out = '<section class="reparto"><p class="eyebrow">El reparto</p>'
    if rows_s:
        out += ('<h3>Ficheros compartidos que se partieron</h3><div class="envolvente-tabla"><table class="tabla">'
                '<thead><tr><th>Fichero</th><th class="num">Commits</th><th class="num">Líneas</th>'
                f'<th>Cómo quedó</th></tr></thead><tbody>{rows_s}</tbody></table></div>')
    if rows_p:
        out += ('<h3 style="margin-top:26px">Del padre — nadie más los toca</h3><div class="envolvente-tabla">'
                '<table class="tabla"><thead><tr><th style="width:32%">Fichero</th><th>Por qué</th></tr></thead>'
                f'<tbody>{rows_p}</tbody></table></div>')
    return out + "</section>"


CSS = """
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 var(--sans)}
.envoltura{max-width:1180px;margin:0 auto;padding:28px 22px 60px}
.solapas{display:flex;gap:6px;flex-wrap:wrap;border-bottom:1px solid var(--line);margin:18px 0 0}
.solapa{display:flex;align-items:center;gap:7px;background:transparent;border:1px solid transparent;border-bottom:none;
  border-radius:var(--radius-sm) var(--radius-sm) 0 0;padding:9px 14px;cursor:pointer;font:600 13.5px/1 var(--sans);
  color:var(--muted);margin-bottom:-1px}
.solapa[aria-selected="true"]{background:var(--card);border-color:var(--line);color:var(--navy)}
.solapa .punto{width:8px;height:8px;border-radius:50%;flex:none}
.solapa .cuenta{font:600 11px/1 var(--mono);color:var(--faint);background:#efece4;padding:2px 6px;border-radius:var(--radius-pill)}
.panel{background:var(--card);border:1px solid var(--line);border-top:none;border-radius:0 0 var(--radius) var(--radius);padding:24px 26px 28px}
.cabecera{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;flex-wrap:wrap}
.cabecera h2{margin:0 0 4px;font-size:24px;color:var(--navy);display:flex;align-items:center;gap:10px}
.badge{color:#fff;font-size:11px;padding:2px 8px;border-radius:var(--radius-pill)}
.que-es{margin:0;color:var(--muted);font-size:14px}
.avance{min-width:190px}.avance .barra{height:7px;background:#efece4;border-radius:var(--radius-pill);overflow:hidden}
.avance .barra i{display:block;height:100%;background:var(--green)}
.avance span{display:block;font:11px/1.6 var(--mono);color:var(--faint);margin-top:5px}
.aviso{margin:16px 0 0;padding:10px 14px;border-radius:var(--radius-sm);font-size:13px;background:#eef1f5;border:1px solid #d7dee8}
.aviso.bloqueo{background:#fdf3e3;border-color:#eed9b0;color:#78350f}
.rejilla{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px;margin:20px 0 0}
.dato{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius-sm);padding:10px 12px}
.dato span{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
.dato b{font:600 14px/1.4 var(--mono);color:var(--navy);word-break:break-all}
.dos{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:26px;margin:24px 0 0}
h3{font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--accent);margin:0 0 8px}
h3 small{text-transform:none;letter-spacing:0;color:var(--faint);font-weight:400}
.ficheros{margin:0;padding:0;list-style:none}.ficheros li{padding:3px 0;border-bottom:1px dashed var(--line)}
.ficheros code,.tabla code{font:12.5px/1.5 var(--mono);background:#efece4;padding:1px 5px;border-radius:5px;overflow-wrap:anywhere}
.comandos{margin:24px 0 0}.comandos pre{margin:0;max-width:100%;background:var(--navy);color:#e8ecf4;border-radius:var(--radius-sm);padding:14px 16px;overflow-x:auto}
.tabla{width:100%;border-collapse:collapse;margin:10px 0 0;font-size:13.5px}
.tabla th{text-align:left;font-size:11px;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);padding:6px 10px 6px 0}
.tabla td{border-bottom:1px solid var(--line);padding:9px 10px 9px 0;vertical-align:top}
.tabla td.num{font:600 13px/1.5 var(--mono);text-align:right;padding-right:18px}
.reparto{margin:44px 0 0;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:22px 26px}
.envolvente-tabla{overflow-x:auto}
@media (max-width:620px){.solapa{flex:1 1 auto;justify-content:center}.envoltura{padding:20px 14px 48px}
  .panel,.reparto{padding:18px 14px 22px}.tabla{min-width:460px}}
"""

JS = """
document.querySelectorAll(".solapa").forEach(function (b) {
  b.addEventListener("click", function () {
    document.querySelectorAll(".solapa").forEach(function (o) { o.removeAttribute("aria-selected"); });
    document.querySelectorAll(".panel").forEach(function (p) { p.hidden = true; });
    b.setAttribute("aria-selected", "true");
    var p = document.getElementById(b.dataset.panel);
    if (p) p.hidden = false;
  });
});
"""


def build(plan: pathlib.Path) -> pathlib.Path | None:
    src = plan / "modulos.json"
    if not src.is_file():
        return None  # página opcional: sin datos no se publica un ejemplo inventado
    data = json.loads(src.read_text(encoding="utf-8"))
    rp = plan / "report.json"
    report = json.loads(rp.read_text(encoding="utf-8")) if rp.is_file() else {}
    prog = progress_by_page(report)
    mods = get(data, "modules") or []
    tabs, panels = zip(*(module_panel(m, i, prog) for i, m in enumerate(mods))) if mods else ((), ())
    title = esc(data.get("title") or "Los módulos")
    intro = esc(data.get("intro") or get(data, "_que_es", "") or
                "Cada módulo con su worktree, su puerto, su base de datos y su sesión.")
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:,">
<title>{title}</title>
<style>
{shared_block()}
{CSS}
</style></head>
<body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="envoltura">
  <p class="eyebrow">Módulos del plan</p>
  <h1>{title}</h1>
  <p style="max-width:66ch;color:var(--muted);margin:0">{intro}</p>
  <div class="solapas" role="tablist">{"".join(tabs)}</div>
  {"".join(panels) or '<p class="aviso">modulos.json no declara ningún módulo.</p>'}
  {split_section(data)}
</div>
<script>{JS}</script>
</body></html>
"""
    out = plan / "modulos.html"
    out.write_text(doc, encoding="utf-8")
    print(f"Escrito {out} — {len(mods)} módulos")
    return out


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "."))
