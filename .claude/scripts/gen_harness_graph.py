#!/usr/bin/env python3
"""El mapa del sistema de agentes: agentes, skills, rules, hooks, plugins y quién usa a quién.

Uso:  python3 .claude/scripts/gen_harness_graph.py [DESTINO] [--check] [--json]
      DESTINO = carpeta del plan (por defecto .claude/). Escribe DESTINO/graph-dataset.json

POR QUÉ EXISTE, y por qué NO es graphify: graphify extrae AST de CÓDIGO. Medido el 2026-08-21
sobre este repo: 8.611 nodos, de los que 6.457 eran prosa markdown. El grafo que hace falta aquí
—agente → skill → plugin → hook → rule— no sale de un AST: sale del FRONTMATTER y de las
REFERENCIAS CRUZADAS. Eso es lo que parsea este script.

Produce el MISMO formato que `report_kit/structure.html` ya sabe pintar (nodes/edges/communities),
así que no hay que tocar esa página: se alimenta. Y sustituye al FIXTURE sintético de un Django
inventado que hoy se publica en dos planes (anti-pattern declarado en rules/report-kit.md).

LAS DOS SEÑALES QUE JUSTIFICAN TODO ESTO:
  · arista `roto`  → A cita a B y B NO EXISTE. Es lo que se nos escapa.
  · `huerfana`     → nadie la nombra Y la cita ES su forma de encontrarse (ver DESCUBRIMIENTO):
                     la pieza existe y es invisible. `fan_in == 0` a secas NO significa eso —
                     un comando o un hook lo tienen a cero siempre y están perfectamente vivos.
"""
from __future__ import annotations
import json, os, re, subprocess, sys, datetime
from pathlib import Path

# Una cita CONDICIONAL no es una referencia rota: es un "si lo tienes". Los tres casos que
# encontró la primera pasada eran exactamente eso — «scripts/monitor-agent.sh **si existe en el
# proyecto**» y «consolidadores internos **por proyecto**» —, y marcarlos en rojo enseña a
# ignorar el detector, que es peor que no tenerlo (verdict-contract.md §Intent: busca la
# intención antes de condenar).
CONDICIONAL_RE = re.compile(
    r"si existe|si lo tienes|si est[áa] instalad|si hay|opcional|por proyecto|en el proyecto|"
    r"if (it )?exists|if present|when available|cuando exista|de cada proyecto|propio de|del proyecto|se archiv|archivada|absorbi|se fusion|rescat",
    re.IGNORECASE)

ROOT = Path(__file__).resolve().parents[1]           # .claude/
REPO = ROOT.parent

COMMUNITIES = {
    "agente":  {"label": "Agentes",            "color": "#7c3aed"},
    "skill":   {"label": "Skills",             "color": "#2563eb"},
    "rule":    {"label": "Rules",              "color": "#15803d"},
    "hook":    {"label": "Hooks (enforcement)", "color": "#b91c1c"},
    "command": {"label": "Commands",           "color": "#0891b2"},
    "workflow":{"label": "Workflows",          "color": "#c2410c"},
    "pattern": {"label": "Patrones de código", "color": "#a16207"},
    "script":  {"label": "Scripts",            "color": "#4b5563"},
    "plugin":  {"label": "Plugins / MCP",      "color": "#db2777"},
}

# Un nombre que aparece en prosa no siempre es una referencia. Estas son las formas que sí lo son.
REF_RE = re.compile(r"`([a-z0-9][a-z0-9._/-]{2,60})`|\b(?:skills?|agents?|rules?|hooks?|"
                    r"commands?|workflows?)/([a-z0-9][a-z0-9._-]{2,60})")

# Las dos formas de cita que REF_RE no veía, y que aquí son las MÁS comunes. Sin ellas el grafo
# daba por huérfano a `task_progress.py`, que está citado en el propio CLAUDE.md:
#   1) la ruta con un directorio que faltaba en la lista — scripts/, patterns/, templates/ —
#      y con el `.claude/` delante, que también rompía el match;
#   2) la cita DENTRO de un comando: `python3 .claude/scripts/x.py --gate` no casa con el grupo
#      de backticks porque ese no admite espacios, y en bloque cerrado no hay backticks que valgan.
# La segunda es deliberadamente laxa (cualquier .py/.sh suelto): solo crea arista si el nombre
# resuelve a un nodo real, así que un falso positivo es imposible por construcción — y NUNCA
# alimenta la detección de referencias rotas, donde sí haría daño.
REF_PATH_RE = re.compile(
    r"(?:\.claude/)?((?:rules|skills|agents|hooks|commands|workflows|patterns|scripts|templates)"
    r"/[a-z0-9][a-z0-9._/-]{2,80})")
REF_FILE_RE = re.compile(r"\b([a-z0-9][a-z0-9_-]{2,40}\.(?:py|sh|js))\b")


# Frontmatter de una rule que solo declara `paths:` (cuándo la carga Claude Code). Son globs, no
# citas: `.claude/commands/speckit.*` saldría como referencia rota. Solo se quita ESE bloque; el
# frontmatter de una skill (description) sí cita piezas y se sigue escaneando.
_PATHS_FM = re.compile(r"\A---\npaths:\n(?:[ \t]+-[ \t].*\n)+---\n")


def _citados(txt):
    """Todos los nombres citables de un texto, en las tres formas. Devuelve
    (estrictos, laxos). El reparto es ASIMÉTRICO a propósito, y es la parte que importa:

      · estrictos (REF_RE, la de siempre) → aristas Y detección de referencias rotas.
      · laxos (ruta con .claude/ delante, o un .py/.sh suelto) → SOLO aristas.

    Por qué. Para «quién nombra a quién» un falso positivo es imposible: la cita solo produce
    arista si resuelve a un nodo real. Para «esto cita algo que no existe» un falso positivo es
    caro — se aprende a ignorar el aviso, y entonces tampoco se ven los de verdad. Medido: dejar
    que los laxos alimentaran las rotas las subía de 0 a 71, y de esas 71 la mayoría eran prosa
    una enumeración de carpetas separadas por barras, un nombre de comando cortado por el punto
    final de la frase) o scripts del proyecto AUDITADO, no del harness.

    (Los ejemplos van descritos y no literales a propósito: escritos tal cual, este mismo
    comentario los disparaba — el fichero que documenta el falso positivo lo producía.)"""
    txt = _PATHS_FM.sub("", txt)
    estrictos = []
    for m in REF_RE.finditer(txt):
        c = (m.group(1) or m.group(2) or "").strip().rstrip("/")
        if c:
            estrictos.append((c, m))
    laxos = {m.group(1).strip().rstrip("/") for m in REF_PATH_RE.finditer(txt)}
    laxos |= {m.group(1) for m in REF_FILE_RE.finditer(txt)}
    return estrictos, laxos

def sh(*a) -> str:
    try:
        return subprocess.run(a, cwd=REPO, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""

def frontmatter(txt: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", txt, re.S)
    if not m:
        return {}
    fm = {}
    lines = m.group(1).splitlines()
    for i, line in enumerate(lines):
        km = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if not km:
            continue
        val = km.group(2).strip()
        # Escalar en bloque (`>-`, `|`): el valor son las líneas sangradas que siguen. Sin esto,
        # las 89 skills y agentes con `description: >-` salían con «>-» de descripción.
        if val in (">", ">-", ">+", "|", "|-", "|+"):
            cuerpo = []
            for nxt in lines[i + 1:]:
                if nxt.strip() and not nxt.startswith((" ", "\t")):
                    break
                cuerpo.append(nxt.strip())
            val = " ".join(x for x in cuerpo if x)
        fm[km.group(1)] = val.strip('"').strip("'")
    return fm

def recoger() -> tuple[dict, dict]:
    """nodos por id, y el texto de cada uno para buscar referencias después."""
    nodos, textos = {}, {}

    def add(nid, group, label, path, desc="", extra=None):
        nodos[nid] = {"id": nid, "label": label, "group": group, "kind": group,
                      "files": [path], "loc": 0, "fan_in": 0, "fan_out": 0,
                      "desc": (desc or "")[:180], **(extra or {})}

    for f in sorted(ROOT.glob("agents/*.md")):
        if f.stem == "README": continue
        t = f.read_text(errors="replace"); fm = frontmatter(t)
        add(f.stem, "agente", f.stem, f"agents/{f.name}", fm.get("description", ""),
            {"model": fm.get("model", ""), "error_cost": fm.get("error_cost", ""),
             "autonomy_phase": fm.get("autonomy_phase", ""), "loc": len(t.splitlines())})
        textos[f.stem] = t

    for f in sorted(ROOT.glob("skills/*/SKILL.md")):
        n = f.parent.name
        t = f.read_text(errors="replace"); fm = frontmatter(t)
        add(n, "skill", n, f"skills/{n}/SKILL.md", fm.get("description", ""),
            {"user_invocable": fm.get("user-invocable", ""), "effort": fm.get("effort", ""),
             "loc": len(t.splitlines())})
        textos[n] = t

    for f in sorted(ROOT.glob("rules/*.md")):
        t = f.read_text(errors="replace")
        cu = re.search(r"\*\*Cuándo aplicar:\*\*\s*(.+?)(?:\n\n|\.\s)", t, re.S)
        add(f.name, "rule", f.stem, f"rules/{f.name}",
            (cu.group(1) if cu else "").replace("\n", " "), {"loc": len(t.splitlines())})
        textos[f.name] = t

    try:
        settings = json.loads((ROOT / "settings.json").read_text())
    except Exception:
        settings = {}
    declarados = {}
    for ev, arr in (settings.get("hooks") or {}).items():
        for m in arr:
            for h in m.get("hooks", []):
                cmd = h.get("command", "")
                hm = re.search(r"hooks/([a-z0-9-]+\.sh)", cmd)
                if hm:
                    declarados.setdefault(hm.group(1), []).append(f"{ev}:{m.get('matcher','*')}")

    for f in sorted(ROOT.glob("hooks/*.sh")):
        t = f.read_text(errors="replace")
        ev = declarados.get(f.name, [])
        add(f.name, "hook", f.stem, f"hooks/{f.name}",
            ("dispara en " + ", ".join(ev)) if ev else "NO registrado en settings.json",
            {"eventos": ev, "registrado": bool(ev), "loc": len(t.splitlines())})
        textos[f.name] = t

    # El `desc` de estos cuatro grupos NO sale de frontmatter: comandos, workflows, patrones y
    # scripts no lo llevan. Se saca de donde cada formato pone de verdad su explicación, y sin
    # esa línea el inventario de `core-sistema.html` sale con la columna «para qué» en blanco
    # — que es tanto como no tener inventario.
    def _primera_linea_util(t, patrones):
        for pat in patrones:
            m = re.search(pat, t, re.M)
            if m:
                d = re.sub(r"\s+", " ", m.group(1)).strip(" -—·:")
                if len(d) > 8:
                    return d[:400]
        return ""

    for f in sorted(ROOT.glob("commands/*.md")):
        t = f.read_text(errors="replace")
        # un comando explica qué es en su H1 (`# /qa-loop — QA convergente…`); si el H1 es solo
        # el nombre, sirve el primer párrafo.
        d = _primera_linea_util(t, [r"^#\s*/?[\w.-]+\s*[-—:]\s*(.+)$", r"^(?!#)(\S.{20,})$"])
        add("/" + f.stem, "command", "/" + f.stem, f"commands/{f.name}", d,
            {"loc": len(t.splitlines())})
        textos["/" + f.stem] = t
    for f in sorted(ROOT.glob("workflows/*.js")):
        t = f.read_text(errors="replace")
        d = _primera_linea_util(t, [r"description:\s*['\"`](.+?)['\"`]", r"^\s*//\s*(\S.{20,})$"])
        add("/" + f.stem, "workflow", "/" + f.stem, f"workflows/{f.name}", d,
            {"loc": len(t.splitlines())})
        textos["/" + f.stem] = t
    for f in sorted(ROOT.glob("patterns/stack/*.md")):
        if f.stem.startswith("_"): continue
        t = f.read_text(errors="replace")
        d = _primera_linea_util(t, [r"^#\s*(.+)$", r"^>\s*(\S.{20,})$"])
        add(f.name, "pattern", f.stem, f"patterns/stack/{f.name}", d, {"loc": len(t.splitlines())})
        textos[f.name] = t
    for f in sorted(ROOT.glob("scripts/*.py")):
        t = f.read_text(errors="replace")
        # el docstring de módulo, que es donde un script dice para qué sirve
        d = _primera_linea_util(t, [r'^"""\s*(.+?)(?:\n|""")', r"^#\s*(\S.{20,})$"])
        add(f.name, "script", f.stem, f"scripts/{f.name}", d, {"loc": len(t.splitlines())})
        textos[f.name] = t

    cat = ROOT / "docs/reference/plugins-catalog.md"
    if cat.exists():
        for p, mk in sorted(set(re.findall(r"`([a-z0-9-]{3,})@([a-z0-9-]+)`", cat.read_text(errors="replace")))):
            nid = f"{p}@{mk}"
            add(nid, "plugin", p, "docs/reference/plugins-catalog.md",
                f"marketplace: {mk}", {"marketplace": mk,
                "verificado": mk == "claude-plugins-official"})
    return nodos, textos

# Cómo se ENCUENTRA cada tipo de pieza — y por tanto qué significa que nadie la nombre.
#
# Sin este reparto, `fan_in: 0` marcaba 53 de 70 piezas: el 100% de los comandos y el 100% de los
# workflows, que se encuentran TECLEÁNDOLOS y por diseño no los cita nadie. Una medida que señala
# dos categorías enteras no está midiendo esas categorías — es la regla de inversión de
# `patterns/README.md` §2 aplicada a una métrica. Con el reparto puesto quedan 4 casos reales.
DESCUBRIMIENTO = {
    "rule":     "cita",       # la rutea INDEX.md; sin cita nadie la abre -> fan_in 0 SÍ es defecto
    "skill":    "cita",       # la encuentra el modelo por su description
    "agente":   "cita",       # lo invoca el TL por su nombre
    "pattern":  "cita",       # lo aplica un comprobador que lo nombra
    "script":   "cita",       # lo llama un hook, una rule, o una persona leyendo un doc
    "command":  "se teclea",  # /x — no aplica
    "workflow": "se teclea",  # /x, o lo lanza una skill
    "hook":     "evento",     # lo dispara settings.json, no una cita
    "plugin":   "instalada",  # vive en settings.json
}

# AGENTS.md y CATALOG.md salieron el 2026-10-20 (LI-32): eran índices a mano. Los índices de
# carpeta que los sustituyen son generados (agents/README.md §0, skills/README.md).
ENRUTADORES = ("INDEX.md", "AGENT-SYSTEM.md", "CLAUDE.md", "agents/README.md", "skills/README.md")


def aristas(nodos, textos):
    """Quién nombra a quién. Y lo importante: quién nombra a algo que NO existe."""
    out, rotas = [], []
    # nombres citables → id del nodo
    idx = {}
    for nid, n in nodos.items():
        idx[nid] = nid
        idx[n["label"]] = nid
        if nid.endswith(".md") or nid.endswith(".sh"):
            idx[nid.rsplit(".", 1)[0]] = nid

    # Los enrutadores primero: no son nodos, pero son los que hacen que una pieza se encuentre.
    for nombre in ENRUTADORES:
        f = ROOT / nombre
        if not f.exists(): continue
        txt = f.read_text(errors="replace")
        estrictos, laxos = _citados(txt)
        for cand in [c for c, _ in estrictos] + sorted(laxos):
            base = cand.split("/")[-1]
            dst = idx.get(cand) or idx.get(base) or idx.get(base.rsplit(".", 1)[0])
            if dst:
                out.append({"from": nombre, "to": dst, "kind": "rutea", "weight": 1,
                            "evidence": "EXTRACTED"})

    for src, txt in textos.items():
        if src not in nodos: continue
        vistos = set()
        estrictos, laxos = _citados(txt)
        # los laxos van con m=None: crean arista pero NUNCA cuentan como referencia rota
        for cand, m in estrictos + [(c, None) for c in sorted(laxos)]:
            if not cand or cand == src: continue
            base = cand.split("/")[-1]
            dst = idx.get(cand) or idx.get(base) or idx.get(base.rsplit(".", 1)[0])
            if dst and dst != src and dst not in vistos:
                vistos.add(dst)
                kind = "dispara" if nodos[src]["group"] == "hook" else "usa"
                out.append({"from": src, "to": dst, "kind": kind, "weight": 1,
                            "evidence": "EXTRACTED"})
            elif m is not None and not dst and re.match(r"^(rules|skills|agents|hooks|commands|workflows|patterns|scripts|templates)/", cand):
                # Rota SOLO si no existe en disco. Un directorio (agents/shared) o un fichero que
                # no es nodo (memory.md) son referencias VÁLIDAS. Un detector con falsos positivos
                # se aprende a ignorar, que es peor que no tenerlo.
                if cand in vistos:
                    continue
                vistos.add(cand)
                if not (ROOT / cand).exists() and not (REPO / cand).exists():
                    # La línea donde se cita decide: si la cita viene condicionada, no es rota.
                    ini = txt.rfind("\n", 0, m.start()) + 1
                    fin = txt.find("\n", m.end());  fin = len(txt) if fin < 0 else fin
                    if CONDICIONAL_RE.search(txt[ini:fin]):
                        continue
                    rotas.append((src, cand))
    for src, cand in rotas:
        out.append({"from": src, "to": f"⚠ {cand}", "kind": "roto", "weight": 1,
                    "evidence": "MISSING"})
        nodos.setdefault(f"⚠ {cand}", {"id": f"⚠ {cand}", "label": f"⚠ {cand.split('/')[-1]}",
            "group": "roto", "kind": "roto", "files": [], "loc": 0, "fan_in": 0, "fan_out": 0,
            "desc": f"Citado desde {src} y NO EXISTE en disco"})
    return out

def build(dest: Path):
    nodos, textos = recoger()
    eds = aristas(nodos, textos)
    for e in eds:
        if e["from"] in nodos: nodos[e["from"]]["fan_out"] += 1
        if e["to"] in nodos:   nodos[e["to"]]["fan_in"] += 1
    # Cada pieza dice cómo se la encuentra, y por tanto si su fan_in significa algo. `huerfana`
    # es la única lectura honesta de «nadie la encuentra»; el `fan_in` a secas, no.
    for n in nodos.values():
        n["descubrimiento"] = DESCUBRIMIENTO.get(n.get("group"), "cita")
        # Un README.md es el índice de SU carpeta: se encuentra abriéndola, no porque alguien lo
        # cite. Contarlo como invisible es el mismo error de categoría que contar un comando.
        es_indice = any(f.endswith("README.md") for f in (n.get("files") or []))
        n["huerfana"] = bool(n["fan_in"] == 0 and n["descubrimiento"] == "cita"
                             and n.get("group") != "roto" and not es_indice)
    comm = dict(COMMUNITIES)
    if any(n["group"] == "roto" for n in nodos.values()):
        comm["roto"] = {"label": "⚠ Referencias rotas", "color": "#dc2626"}
    return {
        "meta": {"source": "gen_harness_graph.py — frontmatter + referencias cruzadas del harness",
                 "sha": sh("git", "rev-parse", "--short", "HEAD"),
                 "date": datetime.date.today().isoformat(),
                 "nodes_total": len(nodos), "edges_total": len(eds), "reduced": False},
        "nodes": list(nodos.values()), "edges": eds, "communities": comm,
    }

def enfocar(d, tope=70):
    """Deja el grafo legible SIN perder lo que importa.

    280 nodos en columnas son una pared, no un mapa (comprobado al pintarlo). Pero el cap por
    conectividad que trae graph_reduce.py haría desaparecer justo lo valioso: las piezas con
    fan_in 0 son, por definición, las menos conectadas — y son las que nadie encuentra.

    Así que la prioridad es al revés de lo habitual:
      1. TODAS las referencias rotas y sus origenes  (lo que se nos escapa)
      2. TODAS las piezas huérfanas de verdad        (lo invisible; ver DESCUBRIMIENTO)
      3. Los hubs, por fan_in                        (para que se entienda la forma)
      4. El resto se agrega en un nodo "(+K más)" por comunidad
    """
    nodos = {n["id"]: n for n in d["nodes"]}
    rotas = [e for e in d["edges"] if e["kind"] == "roto"]
    prio = set()
    for e in rotas:
        prio.add(e["to"]); prio.add(e["from"])
    # `huerfana` y no `fan_in == 0`: con lo segundo entraban los 21 comandos y los 15 workflows,
    # que por diseño no cita nadie, y desplazaban del mapa a los hubs que dan la forma.
    prio |= {n["id"] for n in d["nodes"]
             if n.get("huerfana", n["fan_in"] == 0 and n["group"] != "roto")}
    resto = sorted((n for n in d["nodes"] if n["id"] not in prio),
                   key=lambda n: -(n["fan_in"] + n["fan_out"]))
    prio |= {n["id"] for n in resto[:max(0, tope - len(prio))]}

    fuera = [n for n in d["nodes"] if n["id"] not in prio]
    keep = [n for n in d["nodes"] if n["id"] in prio]
    from collections import Counter
    for g, c in Counter(n["group"] for n in fuera).items():
        keep.append({"id": f"+{c} {g}", "label": f"(+{c} más)", "group": g, "kind": "agregado",
                     "files": [], "loc": 0, "fan_in": 0, "fan_out": 0,
                     "desc": f"{c} piezas de {g} bien conectadas y sin incidencias — "
                             f"el grafo completo está en graph-dataset.full.json"})
    d["nodes"] = keep
    ids = {n["id"] for n in keep}
    d["edges"] = [e for e in d["edges"] if e["from"] in ids and e["to"] in ids]
    d["meta"]["reduced"] = bool(fuera)
    d["meta"]["nodes_total"] = len(keep); d["meta"]["edges_total"] = len(d["edges"])
    d["meta"]["source"] += f" · vista enfocada: rotas + huérfanas + {tope} hubs (de {len(nodos)})"
    return d


def main():
    global ROOT, REPO
    # --root <proyecto>: mapear el .claude/ de OTRO proyecto, no el propio.
    # Sin esto el script solo sabía mirarse a sí mismo, y la mitad de su valor es poder
    # apuntarlo a un proyecto derivado para ver qué tiene y qué le cita a nada.
    if "--root" in sys.argv:
        i = sys.argv.index("--root")
        if i + 1 >= len(sys.argv):
            print("--root necesita un path", file=sys.stderr); return 2
        base = Path(sys.argv[i + 1]).resolve()
        cand = base / ".claude" if (base / ".claude").is_dir() else base
        if not cand.is_dir():
            print(f"no existe un .claude/ en {base}", file=sys.stderr); return 2
        ROOT, REPO = cand, cand.parent
        sys.argv = [x for j, x in enumerate(sys.argv) if j not in (i, i + 1)]

    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    dest = Path(a[0]) if a else ROOT
    # --out <fichero>: nombre de salida distinto, para no pisar el grafo del propio proyecto
    if "--out" in sys.argv:
        j = sys.argv.index("--out")
        if j + 1 < len(sys.argv):
            dest = Path(sys.argv[j + 1]).parent
    out = (Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv
           and sys.argv.index("--out") + 1 < len(sys.argv) else dest / "graph-dataset.json")
    d = build(dest)
    if "--json" in sys.argv:
        print(json.dumps(d, ensure_ascii=False, indent=1)); return 0
    if "--check" in sys.argv:
        if not out.exists():
            print("no hay grafo generado", file=sys.stderr); return 1
        old = json.load(open(out))
        if {n["id"] for n in old["nodes"]} != {n["id"] for n in d["nodes"]}:
            print("DESFASADO: el grafo no refleja el harness", file=sys.stderr); return 1
        print(f"OK: grafo al día ({d['meta']['nodes_total']} nodos)"); return 0
    # el completo, para quien lo quiera; y el enfocado, que es el que se pinta
    (dest / "graph-dataset.full.json").write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    import copy
    out.write_text(json.dumps(enfocar(copy.deepcopy(d)), ensure_ascii=False, indent=1) + "\n")
    rotas = [e for e in d["edges"] if e["kind"] == "roto"]
    huerf = [n for n in d["nodes"]
             if n.get("huerfana", n["fan_in"] == 0 and n["group"] != "roto")]
    print(f"Escrito {out} — {d['meta']['nodes_total']} nodos · {d['meta']['edges_total']} aristas")
    from collections import Counter
    for g, c in Counter(n["group"] for n in d["nodes"]).most_common():
        print(f"    {c:>4}  {g}")
    print(f"\n  ⚠ referencias ROTAS: {len(rotas)}")
    for e in rotas[:8]: print(f"      {e['from']} → {e['to']}")
    print(f"  ⚠ piezas que NADIE nombra (fan_in 0): {len(huerf)}")
    for n in huerf[:12]: print(f"      [{n['group']}] {n['id']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
