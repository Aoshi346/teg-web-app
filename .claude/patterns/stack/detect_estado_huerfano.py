"""Campos que un NODO del grafo escribe y el State no declara.

EL FALLO QUE CAZA. LangGraph descarta en silencio toda clave que el State no
declare -- `langgraph/graph/state.py:962`:

    return [(k, v) for k, v in input.items() if k in output_keys]

Ni excepcion, ni log. El nodo cree que ha escrito la bandera, quien la lee
recibe None, y el bot sigue respondiendo. Un agente que "dice cosas raras"
-- repite el saludo, ignora un flag que el codigo si escribe -- casi siempre
es esto, y no el prompt.

COMO SE ACOTA, y por que. Un nodo en LangGraph es una funcion que recibe el
estado y devuelve un dict. Ese es el filtro: `add_node(...)` explicito, o la
firma `def f(state, ...)`. Sin el, el detector mira cualquier dict del fichero
y marca ~350 sitios en un repo real -- muere por la regla de inversion
(`patterns/README.md` §2). El return de una `@tool` NO entra: va al
ToolMessage, no al estado.

MEDIDO EL 2026-08-26 sobre los tres repos con agentes de esta casa:

    repo                | hallazgos | comentario
    elvion (core/)      |     2     | `greeting_shown` es un bug REAL confirmado
                        |           | `trace_checkpoint` es falso positivo: pertenece
                        |           | a otro State (LumiConversationState), que se
                        |           | maneja a mano y ademas hace `pop` despues
    autoparte-demo      |     0     | correcto
    proxera_musa        |     0     | correcto

LIMITE DECLARADO: tiene falsos NEGATIVOS. En elvion no caza
`handoff_requested` (`flexible_graph.py:4680`), que se escribe en un dict
literal que no es el return directo del nodo. Un 0 aqui NO demuestra que no
haya campos huerfanos: demuestra que no los hay de la forma que este detector
sabe mirar.

USO:
    python3 .claude/patterns/stack/detect_estado_huerfano.py <ruta>
"""
import ast, pathlib, sys

raiz = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SALTAR = ("migrations", "__pycache__", ".venv", "node_modules")
ACUM = {"updates", "state", "new_state", "estado", "result", "out", "patch", "delta"}

declarados, nodos, escritos = set(), set(), {}
arboles = []

for f in raiz.rglob("*.py"):
    if any(x in f.parts for x in SALTAR):
        continue
    src = f.read_text(encoding="utf-8", errors="ignore")
    try:
        arbol = ast.parse(src)
    except SyntaxError:
        continue
    arboles.append((f, arbol))
    for n in ast.walk(arbol):
        if isinstance(n, ast.ClassDef) and any(
            getattr(b, "id", getattr(b, "attr", "")) == "TypedDict" for b in n.bases
        ):
            declarados |= {s.target.id for s in n.body if isinstance(s, ast.AnnAssign)}
        # quien es NODO: lo que se pasa a add_node(...)
        if (isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "add_node"):
            for a in n.args:
                if isinstance(a, ast.Name):
                    nodos.add(a.id)
                elif isinstance(a, ast.Attribute):
                    nodos.add(a.attr)
                elif isinstance(a, ast.Constant) and isinstance(a.value, str):
                    nodos.add(a.value)
                elif isinstance(a, ast.Lambda):
                    nodos.add("<lambda>")

def anota(clave, f, linea):
    escritos.setdefault(clave, f"{f}:{linea}")

for f, arbol in arboles:
    for fn in ast.walk(arbol):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = [a.arg for a in fn.args.args]
        # firma de un nodo en LangGraph: recibe el estado como primer argumento
        es_nodo = fn.name in nodos or (args and args[0] in ("state", "estado")) \
            or (len(args) > 1 and args[0] == "self" and args[1] in ("state", "estado"))
        if not es_nodo:
            continue
        for n in ast.walk(fn):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
                for k in n.value.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        anota(k.value, f, k.lineno)
            if isinstance(n, ast.Assign):
                for tgt in n.targets:
                    if (isinstance(tgt, ast.Subscript) and isinstance(tgt.value, ast.Name)
                            and tgt.value.id in ACUM
                            and isinstance(tgt.slice, ast.Constant)
                            and isinstance(tgt.slice.value, str)):
                        anota(tgt.slice.value, f, tgt.lineno)

huerfanos = {k: v for k, v in escritos.items() if k not in declarados}
print(f"State declara {len(declarados)} · nodos detectados {len(nodos)} · "
      f"claves escritas por nodos {len(escritos)} · NO declaradas {len(huerfanos)}\n")
for k, v in sorted(huerfanos.items()):
    print(f"  x '{k}' -> {v}  (LangGraph lo descarta)")
if not huerfanos:
    print("  sin hallazgos")
