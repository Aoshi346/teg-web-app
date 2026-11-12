#!/usr/bin/env python3
"""stack-dataset.json — EL MOLDE del stack: cómo se monta un proyecto nuevo aquí.

QUE RESPONDE, y no lo respondia ninguna pagina del kit: cuando alguien arranca un
proyecto, ¿que se monta y en que orden? Que modelos hay y con que campos, como se
monta una app, que componentes existen, cuantos nodos tiene el grafo y que tools ve
el bot. Con NOMBRES, no con cajas.

TRES FUENTES, y las tres se declaran en la salida:
  1. `patterns/stack/*.md`      -> EL MOLDE: como se monta cada capa en esta casa
  2. `inventario/<proy>.json`   -> LO QUE HAY: cada modelo, vista, componente, tool
  3. `referencia/<repo>.json`   -> LOS EXPERTOS: los mismos numeros, para comparar

POR QUE JUNTOS. El patron a solas es prosa que nadie abre; el inventario a solas es
una lista sin criterio. Juntos responden "asi se monta, y esto es lo que tenemos".
Y la columna de los expertos evita el unico error que este informe no puede permitirse:
tomar nuestra manera de hacer las cosas por la manera correcta.

USO:
    python3 gen_stack_dataset.py <plan-dir>
"""
import argparse, json, re, sys, datetime
from pathlib import Path

# El orden en que se monta un proyecto. Cada bloque agrupa capas del inventario
# y apunta a los documentos de patrón que la fijan.
BLOQUES = [
    {"id": "backend", "label": "Backend · Django", "color": "#15803d",
     "que": "Los datos, las reglas y la API. Es lo primero y lo más caro de cambiar después.",
     "capas": [
        {"k": "modelos", "label": "Modelos", "pat": ["backend-modelos.md", "backend-estructura-apps.md"],
         "que": "Los datos y sus reglas. Cada migración arrastra lo que ya está guardado: es lo más caro de deshacer."},
        {"k": "serializers", "label": "Serializers", "pat": ["backend-serializers.md"],
         "que": "El contrato con quien consume la API. Cambiarlo rompe a alguien de fuera aunque los tests pasen."},
        {"k": "vistas", "label": "Vistas y ViewSets", "pat": ["backend-vistas.md", "backend-controllers.md"],
         "que": "Donde entra lo de fuera. Es la frontera: aquí se valida."},
        {"k": "tareas", "label": "Tareas en segundo plano", "pat": ["backend-celery.md"],
         "que": "Lo que corre sin nadie mirando. Por eso necesita su propio registro."},
     ]},
    {"id": "frontend", "label": "Frontend · React", "color": "#c2410c",
     "que": "Lo que el usuario ve. Se monta después del contrato del backend, no antes.",
     "capas": [
        {"k": "paginas", "label": "Páginas", "pat": ["frontend-nueva-pantalla.md", "frontend-stack.md"],
         "que": "Las pantallas y por dónde se navega."},
        {"k": "componentes", "label": "Componentes", "pat": ["componentes.md", "frontend-design-system.md"],
         "que": "Las piezas reutilizables. Si dos pantallas lo usan, cambiarlo las cambia las dos."},
        {"k": "hooks", "label": "Hooks y estado", "pat": ["estado.md", "frontend-contrato-con-el-backend.md"],
         "que": "De dónde saca cada pantalla lo que enseña."},
     ]},
    {"id": "agente", "label": "Agente IA · LangGraph", "color": "#7c3aed",
     "que": "El grafo, sus tools y lo que recuerda. La capa donde los fallos NO dan excepción.",
     "capas": [
        {"k": "state", "label": "El State", "pat": ["agente-memoria.md"],
         "que": "Qué recuerda entre turnos, y con qué reducer se fusiona cada campo. Aquí nacen los fallos mudos."},
        {"k": "nodos", "label": "Nodos del grafo", "pat": ["agente-determinismo.md", "agente-cuando-no.md"],
         "que": "Por dónde pasa una conversación. Pocos nodos y mucho `if` dentro significa que el grafo no está haciendo su trabajo."},
        {"k": "tools", "label": "Tools", "pat": ["agente-tools.md", "agente-hitl.md"],
         "que": "Lo que el agente puede hacer. Su descripción ES el prompt que decide si se llama."},
        {"k": "retrieval", "label": "Retrieval · RAG", "pat": ["agente-rag.md"],
         "que": "De dónde saca lo que dice. Un índice que acierta y una tool que lo estropea son dos números distintos: mide los dos."},
        {"k": "forma", "label": "Forma del sistema", "pat": ["agente-arquitecturas.md", "agente-evaluator-optimizer.md"],
         "que": "Un grafo, varios agentes o un supervisor. Se elige antes de escribir nodos, y casi siempre la respuesta es el más simple."},
        {"k": "observabilidad", "label": "Observabilidad", "pat": ["agente-observabilidad.md", "agente-panel-debug.md"],
         "que": "Si no puedes reconstruir qué tools llamó y por qué recorrió esos nodos, no tienes un agente: tienes una caja negra que a veces acierta."},
     ]},
]


def limpia_md(s: str) -> str:
    """El HTML pinta texto plano: el markdown crudo (**, backticks, enlaces) se lee peor
    que no ponerlo. Se quitan las marcas y se conserva el texto."""
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)     # [texto](enlace) -> texto
    s = re.sub(r"[*_`]{1,3}", "", s)                       # negrita, cursiva, código
    s = re.sub(r"^\s*[>#-]+\s*", "", s)
    return " ".join(s.split())


def lee_patrones(repo: Path) -> dict:
    """El molde: título, cuándo aplica, la regla en una frase y los bloques de código."""
    out = {}
    d = repo / ".claude" / "patterns" / "stack"
    if not d.is_dir():
        return out
    for f in d.glob("*.md"):
        txt = f.read_text(encoding="utf-8", errors="ignore")
        titulo = re.search(r"^#\s+(.+)$", txt, re.M)
        cuando = re.search(r"\*\*Cu[aá]ndo aplica.*?:\*\*\s*(.+)", txt)
        # La regla en una frase. Se busca el bloque de cita que sigue a "## La regla…" y se
        # queda con la PRIMERA línea de cita: las siguientes suelen ser matices, y un aviso
        # arrancado por la mitad se lee peor que no poner nada.
        regla = None
        m_sec = re.search(r"^##\s*La regla[^\n]*\n(.*?)(?=\n##\s)", txt, re.S | re.M)
        if m_sec:
            # Dos formatos conviven en los 38 documentos: cita (`> …`) y negrita (`**…**`).
            # Se acepta el primer párrafo con sustancia de cualquiera de los dos, y se para
            # ahí: lo que sigue suele ser el "por qué esta y no otra", que es otra cosa.
            bruto, buf = m_sec.group(1), []
            for linea in bruto.splitlines():
                s = linea.strip()
                if not s:
                    if buf:
                        break
                    continue
                if s.startswith("```"):
                    break
                buf.append(s.lstrip("> ").strip())
            frase = " ".join(buf).strip()
            if len(frase) > 15:
                regla = type("M", (), {"group": lambda self, _n, c=frase: c})()
        # el primer bloque de código con sustancia: el molde literal
        bloques = [b for b in re.findall(r"```(?:python|tsx?|ts|jsx?)?\n(.*?)```", txt, re.S)
                   if len(b.strip()) > 60]
        out[f.name] = {
            "file": f.name,
            "titulo": (titulo.group(1).strip() if titulo else f.stem),
            "cuando": (cuando.group(1).strip()[:220] if cuando else ""),
            "regla": (limpia_md(regla.group(1))[:300] if regla else ""),
            "molde": (bloques[0].strip()[:1400] if bloques else ""),
            "n_bloques": len(bloques),
            "lineas": txt.count("\n") + 1,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    a = ap.parse_args()
    plan = Path(a.plan).resolve()
    repo = plan.parents[2] if len(plan.parents) > 2 else plan

    patrones = lee_patrones(repo)
    inventarios, referencia = {}, {}
    # Los inventarios de REFERENCIA describen lo que un cuerpo ES, no lo que se decidio en un
    # plan — asi que su sitio es permanente (report-kit.md regla 5a, PV-3). Se leen primero de
    # .claude/patterns/referencia/inventarios/ y el plan puede sobreescribir uno concreto.
    permanente = repo / ".claude" / "patterns" / "referencia" / "inventarios"
    fuentes = [(permanente, referencia)] if permanente.is_dir() else []
    fuentes += [(plan / "proyectos/inventario", inventarios), (plan / "referencia", referencia)]
    for d, dest in fuentes:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            if f.name.endswith(".graph.json"):
                continue
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"aviso: {f.name} ilegible ({e})", file=sys.stderr)
                continue
            dest[(j.get("meta", {}) or {}).get("proyecto", f.stem)] = j

    if not inventarios and not referencia:
        print("aviso: sin inventarios — corre gen_inventario_stack.py primero", file=sys.stderr)
        return 1

    def totales(j):
        return (j.get("meta", {}) or {}).get("totales", {})

    bloques = []
    for b in BLOQUES:
        capas = []
        for c in b["capas"]:
            pats = [patrones[p] for p in c["pat"] if p in patrones]
            capas.append({**c, "patrones": pats,
                          "n_nuestro": {k: totales(v).get(c["k"], 0) for k, v in inventarios.items()},
                          "n_experto": {k: totales(v).get(c["k"], 0) for k, v in referencia.items()}})
        bloques.append({**b, "capas": capas})

    data = {"meta": {
        "source": "gen_stack_dataset.py — patterns/stack (el molde) + gen_inventario_stack.py (lo que hay)",
        "date": datetime.date.today().isoformat(),
        "proyectos": sorted(inventarios), "referencia": sorted(referencia),
        "n_patrones": len(patrones),
        "metodo": {k: (v.get("meta", {}) or {}).get("metodo", {}) for k, v in list(inventarios.items())[:1]},
    }, "bloques": bloques,
       "inventarios": {k: {kk: vv for kk, vv in v.items() if kk != "meta"} for k, v in inventarios.items()},
       "totales": {**{k: totales(v) for k, v in inventarios.items()},
                   **{k: totales(v) for k, v in referencia.items()}},
       "es_referencia": sorted(referencia),
       "patrones": patrones}

    out = plan / "stack-dataset.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {out}")
    print(f"   {len(patrones)} documentos de patrón · {len(inventarios)} proyectos · "
          f"{len(referencia)} repos de referencia")
    for k, v in data["totales"].items():
        vivos = {a: b for a, b in v.items() if b}
        print(f"     {k[:24]:26} " + " · ".join(f"{a}={b}" for a, b in list(vivos.items())[:6]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
