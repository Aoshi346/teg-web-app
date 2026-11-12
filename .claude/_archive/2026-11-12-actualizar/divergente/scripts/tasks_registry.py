#!/usr/bin/env python3
"""tasks_registry.py — el registro de TODO lo que pide el Usuario, para que no se pierda nada.

EL PROBLEMA, dicho por el Usuario y con razón: «se te está olvidando todo, yo voy diciéndote cosas
y se van perdiendo». Cierto, y la causa no es el descuido: es que **no había ningún sitio donde
quedara escrita cada petición**. Lo que no se anota, depende de que el agente lo recuerde entre
veinte tareas — y eso falla siempre, no a veces.

POR QUÉ ES UN HOOK Y NO UNA SKILL. Una skill hay que acordarse de invocarla, que es el mismo fallo
otra vez. El hook `UserPromptSubmit` corre SIEMPRE, esté el agente distraído o no. Es
`el criterio de capas del template` aplicado a nosotros mismos: si el coste de que se ignore es alto, baja de
capa.

QUÉ HACE
  add    — registra una petición nueva (lo llama el hook, no una persona)
  list   — los pendientes, para inyectarlos en el contexto de cada turno
  done   — marca una como hecha
  bg     — la marca como delegada a background (con su id de tarea)

FORMATO: `pending-tasks.md` DENTRO del plan, markdown legible por un humano — no un JSON que solo lea el agente.
El Usuario tiene que poder abrirlo y ver qué pidió y qué falta.
"""
import argparse, os, re, sys
from datetime import datetime

def _plan_activo(base):
    """El registro vive DENTRO del plan, no en la raíz — decisión del Usuario, y es la correcta:
    cada plan tiene sus peticiones, y un fichero global mezcla trabajos que no tienen que ver.

    CÓMO SE ELIGE, y por qué NO por fecha de modificación. La primera versión usaba el `mtime` y
    se rompió el mismo día: bastó regenerar el informe de un plan viejo para que pasara a ser «el
    más reciente» y el registro se partiera en dos ficheros sin que nadie se enterara. Un registro
    partido es un registro perdido — justo lo que esto existe para impedir.

    El orden es: (1) continuidad —si ya se registra en un plan, se sigue ahí—, (2) el de fecha más
    reciente EN EL NOMBRE (los planes son `YYYY-MM-DD-slug`, así que ordenan solos), (3) la raíz."""
    planes = os.path.join(base, ".docs", "plans")
    if not os.path.isdir(planes):
        return os.path.join(base, "pending-tasks.md")
    dirs = sorted(d for d in os.listdir(planes) if os.path.isdir(os.path.join(planes, d)))

    con_registro = [d for d in dirs if os.path.exists(os.path.join(planes, d, "pending-tasks.md"))]
    if con_registro:
        return os.path.join(planes, sorted(con_registro)[-1], "pending-tasks.md")

    con_informe = [d for d in dirs if os.path.exists(os.path.join(planes, d, "report.json"))]
    if con_informe:
        return os.path.join(planes, sorted(con_informe)[-1], "pending-tasks.md")
    return os.path.join(base, "pending-tasks.md")

_BASE = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
RUTA = os.environ.get("TL_TASKS_FILE") or _plan_activo(_BASE)

CAB = """# Peticiones pendientes — lo que se ha pedido en este plan

> Lo escribe el hook `capture-task.sh` en cada petición del Usuario, y lo marca el TL al terminar.
> **No se edita a mano para "limpiar"**: una tarea que desaparece sin marcarse es una tarea perdida,
> que es justo lo que este fichero existe para impedir.
>
> `[ ]` pendiente · `[>]` en curso · `[~]` en background · `[x]` hecha · `[!]` bloqueada o descartada

## Pendientes

## En background

## Hechas
"""

def leer():
    if not os.path.exists(RUTA):
        return CAB
    return open(RUTA, encoding="utf-8").read()

def guardar(t):
    open(RUTA, "w", encoding="utf-8").write(t)

def siguiente_id(t):
    ids = [int(m) for m in re.findall(r"`T-(\d+)`", t)]
    return f"T-{max(ids) + 1 if ids else 1:03d}"

def add(texto):
    t = leer()
    limpio = " ".join(texto.split())
    if len(limpio) > 260:
        limpio = limpio[:257] + "…"
    # No duplicar: si la misma petición ya está pendiente, no se registra otra vez
    for ln in t.splitlines():
        if limpio[:80] in ln and ln.strip().startswith("- [ ]"):
            return None
    tid = siguiente_id(t)
    linea = f'- [ ] `{tid}` ({datetime.now().strftime("%m-%d %H:%M")}) {limpio}\n'
    t = t.replace("## Pendientes\n", "## Pendientes\n" + linea, 1)
    guardar(t)
    return tid

def listar(solo_pendientes=True, maximo=12):
    t = leer()
    sec = re.search(r"## Pendientes\n(.*?)(?=\n## |\Z)", t, re.S)
    pend = [l for l in (sec.group(1).splitlines() if sec else []) if l.strip().startswith("- [ ]")]
    bg = re.search(r"## En background\n(.*?)(?=\n## |\Z)", t, re.S)
    enbg = [l for l in (bg.group(1).splitlines() if bg else []) if l.strip().startswith("- [~]")]
    return pend[:maximo], enbg[:6], len(pend)

def refinar(tid, texto):
    """Reescribe la petición en lenguaje claro, conservando id, fecha y estado.

    POR QUÉ NO LO HACE EL HOOK. El hook registra el texto CRUDO a propósito: es instantáneo y no
    puede fallar. Si llamara a un modelo para entenderlo, tardaría, podría fallar y entonces se
    perdería la petición — que es exactamente lo que este registro existe para impedir.
    Refinar es una MEJORA posterior, no un requisito para registrar.

    Lo hace el TL al ponerse con la tarea: es el momento en que de verdad entiende qué se pedía.
    Y conserva el original entre paréntesis: si el refinado se equivoca, el texto de partida
    sigue ahí para comprobarlo."""
    t = leer()
    pat = re.compile(r"^(- \[[ >~x!]\]\s*`" + re.escape(tid) + r"`\s*\([^)]*\)\s*)(.*)$", re.M)
    m = pat.search(t)
    if not m:
        return False
    resto = m.group(2)
    nota = ""
    if "  — " in resto:                      # conservar la nota de cierre si la hay
        resto, nota = resto.split("  — ", 1); nota = "  — " + nota
    original = resto.strip()
    # el original se guarda solo si difiere de verdad del refinado
    cola = f'  <!-- pedido: {original[:150]} -->' if original[:60].lower() != texto[:60].lower() else ""
    t = pat.sub(lambda _: m.group(1) + texto + nota + cola, t, count=1)
    guardar(t)
    return True


def marcar(tid, estado, nota=""):
    t = leer()
    pat = re.compile(r"^(- )\[[ >~x!]\](\s*`" + re.escape(tid) + r"`.*)$", re.M)
    m = pat.search(t)
    if not m:
        return False
    linea = f"{m.group(1)}[{estado}]{m.group(2)}"
    if nota:
        linea += f"  — {nota}"
    t = pat.sub(lambda _: linea, t, count=1)
    # mover de sección
    destino = {"x": "## Hechas", "~": "## En background", "!": "## Hechas"}.get(estado)
    if destino:
        t = t.replace(linea + "\n", "")
        t = t.replace(destino + "\n", destino + "\n" + linea + "\n", 1)
    guardar(t)
    return True

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("texto", nargs="+")
    rf = sub.add_parser("refine"); rf.add_argument("id"); rf.add_argument("texto", nargs="+")
    sub.add_parser("list").add_argument("--max", type=int, default=12)
    for c, e in (("done", "x"), ("bg", "~"), ("doing", ">"), ("block", "!")):
        p = sub.add_parser(c); p.add_argument("id"); p.add_argument("--nota", default="")
    ns = ap.parse_args()

    if ns.cmd == "refine":
        print("ok" if refinar(ns.id, " ".join(ns.texto)) else f"no encontrada: {ns.id}")
    elif ns.cmd == "add":
        tid = add(" ".join(ns.texto))
        print(tid or "(duplicada, no registrada)")
    elif ns.cmd == "list":
        pend, bg, n = listar(maximo=ns.max)
        if not pend and not bg:
            return 0
        if pend:
            print(f"📋 {n} petición(es) pendiente(s) — de pending-tasks.md, no las pierdas:")
            for l in pend: print("  " + l.strip())
        if bg:
            print("⏳ en background:")
            for l in bg: print("  " + l.strip())
    else:
        est = {"done": "x", "bg": "~", "doing": ">", "block": "!"}[ns.cmd]
        print("ok" if marcar(ns.id, est, ns.nota) else f"no encontrada: {ns.id}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
