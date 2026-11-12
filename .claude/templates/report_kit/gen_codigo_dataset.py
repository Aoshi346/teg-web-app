#!/usr/bin/env python3
"""codigo-dataset.json — el esquema EXPLICADO de cómo está montado, por capas.

DOS COSAS DISTINTAS, y confundirlas fue el fallo que originó este generador:
  · el HARNESS  -> skills, agentes, rules: el sistema de Claude Code (gen_harness_graph.py)
  · el PROYECTO -> modelos, vistas, componentes, el grafo del agente (gen_proyecto_graph.py)
Publicar el primero cuando alguien pregunta "¿cómo está montado mi proyecto?" no responde
nada: no contiene una sola línea del proyecto. Esta página muestra LOS DOS, separados y
con un selector, para que nunca vuelvan a pasar por lo mismo.

POR QUE NO BASTA `structure.html`. Aquella lleva escrito en su cabecera "Página técnica --
puedes saltártela tranquilamente": es el grafo navegable, para quien programa. Esta es la
versión que se le enseña a quien decide: qué capas hay, qué hace cada una, qué la gobierna.

NO INVENTA DESCRIPCIONES. Si una capa o una pieza no tiene texto, sale sin él y se marca.
Rellenar con prosa plausible es como una página de arquitectura empieza a mentir.

USO:
    python3 gen_codigo_dataset.py <plan-dir>

Lee <plan>/graph-dataset.json (el harness, opcional), <plan>/proyectos/*.json (los
proyectos, opcional) y <plan>/pattern-dataset.json (para colgar el patrón de cada capa).
"""
import argparse, json, sys, datetime
from pathlib import Path

# Qué gobierna cada capa. Se declara aquí porque es criterio de esta casa, no un dato que
# salga del código. Una capa sin entrada sale sin texto — y se ve que le falta.
GOBIERNO = {
    # --- harness ---
    "rule":     ("Lo que el agente DEBERÍA hacer", "Advisory: el modelo puede ignorarlo. Por eso lo crítico no vive aquí."),
    "hook":     ("Lo que el agente NO PUEDE evitar", "Determinista: lo ejecuta el harness y puede bloquear la acción."),
    "skill":    ("Procedimientos repetibles", "Se cargan cuando el modelo las encuentra por su descripción."),
    "agente":   ("Criterio independiente", "Contexto limpio: verifican sin arrastrar la conversación."),
    "command":  ("Lo que tecleas tú", "La única capa que usa un perfil no técnico."),
    "workflow": ("Orquestación determinista", "Un script: igual en cada ejecución, y resumible."),
    "pattern":  ("Cómo se escribe el código aquí", "Con su comprobador; el estado de cada regla, en la pestaña Patrón."),
    "script":   ("Los gates que se pueden correr", "Salen con código distinto de cero: son los que de verdad frenan."),
    "plugin":   ("Capacidad empaquetada de terceros", "Se instala; revisar su código es obligatorio antes."),
    # --- proyecto: agente IA ---
    "agente-grafo":  ("El grafo del agente", "Nodos y aristas: por dónde pasa una conversación. Aquí se decide el flujo."),
    "agente-tool":   ("Lo que el agente puede hacer", "Cada tool es una API cuyo cliente se equivoca: su descripción ES el prompt que la elige."),
    "agente-estado": ("Qué recuerda entre turnos", "El State y el checkpointer. Sus fallos no dan excepción (agente-memoria.md §1b)."),
    # --- proyecto: backend ---
    "modelo":     ("Los datos y sus reglas", "Lo más caro de cambiar: cada migración arrastra lo que ya está guardado."),
    "serializer": ("El contrato con quien consume la API", "Cambiarlo rompe a alguien de fuera, aunque los tests pasen."),
    "vista":      ("Lo que responde a una petición", "Aquí entra lo de fuera: es la frontera donde se valida."),
    "api":        ("Las rutas", "El mapa de qué URL lleva a qué. Un cambio aquí es un cambio de contrato."),
    "servicio":   ("La lógica de negocio", "Lo que no es ni datos ni HTTP. Si crece sin forma, aquí es donde se nota."),
    "tarea":      ("Lo que corre en segundo plano", "Nadie está mirando cuando falla: por eso necesita registro propio."),
    # --- proyecto: frontend ---
    "pagina":      ("Las pantallas", "Lo que el usuario ve y por donde navega."),
    "componente":  ("Las piezas reutilizables", "Si dos pantallas lo usan, cambiarlo las cambia las dos."),
    "estado-fe":   ("El estado del cliente", "Stores y hooks: de dónde saca cada pantalla lo que enseña."),
    "cliente-api": ("Cómo habla con el backend", "El otro extremo del contrato de los serializers."),
    # --- común ---
    "test":    ("La red de seguridad", "Sin esto, ningún refactor es seguro por mecánico que parezca."),
    "config":  ("Configuración", "Lo que cambia entre entornos, y lo que nunca debe estar en el repo."),
    "entrada": ("Puntos de entrada", "Por dónde arranca todo."),
    "otro":    ("", "Sin clasificar: no encaja en ninguna convención conocida del framework."),
}


def capas_de(nodos, aristas, coms):
    """Agrupa las piezas por capa, con qué la gobierna y con quién se apoya."""
    out = []
    for gid in sorted({n.get("group") for n in nodos if n.get("group")}):
        piezas = sorted([n for n in nodos if n.get("group") == gid],
                        key=lambda n: -(n.get("fan_in", 0) + n.get("fan_out", 0)))
        ids = {n["id"] for n in piezas}
        grupo_de = {n["id"]: n.get("group") for n in nodos}
        destinos = {}
        for e in aristas:
            if e.get("from") in ids:
                dg = grupo_de.get(e.get("to"))
                if dg and dg != gid:
                    destinos[dg] = destinos.get(dg, 0) + 1
        que, matiz = GOBIERNO.get(gid, ("", ""))
        info = coms.get(gid, {})
        out.append({
            "id": gid, "label": info.get("label", gid), "color": info.get("color", "#6b6b6b"),
            "que": que, "matiz": matiz, "n": len(piezas),
            "loc": sum(n.get("loc", 0) or 0 for n in piezas),
            "habla_con": sorted(destinos.items(), key=lambda kv: -kv[1])[:4],
            "top": [{"id": n["id"], "label": n.get("label", n["id"]),
                     "desc": (n.get("desc") or "")[:220],
                     "fan_in": n.get("fan_in", 0), "fan_out": n.get("fan_out", 0),
                     "files": (n.get("files") or [])[:2]} for n in piezas[:6]],
            "sin_desc": sum(1 for n in piezas if not (n.get("desc") or "").strip()),
            "docs": [],
        })
    return out


def vista(nombre, tipo, g, patron=None):
    nodos, aristas = g.get("nodes", []), g.get("edges", [])
    coms = g.get("communities", {}) or {}
    capas = capas_de(nodos, aristas, coms)
    if patron and tipo == "harness":
        for c in capas:
            if c["id"] == "pattern":
                c["docs"] = [{"file": d["file"], "titulo": d["titulo"], "familia": d["familia"]}
                             for d in patron.get("docs", [])]
    m = g.get("meta", {}) or {}
    return {"nombre": nombre, "tipo": tipo, "capas": capas,
            "piezas": len(nodos), "relaciones": len(aristas),
            "sha": m.get("sha", ""), "date": m.get("date", ""),
            "source": m.get("source", ""), "reduced": bool(m.get("reduced")),
            "ficheros_por_capa": m.get("ficheros_por_capa", {})}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    a = ap.parse_args()
    plan = Path(a.plan).resolve()

    patron = None
    pp = plan / "pattern-dataset.json"
    if pp.exists():
        patron = json.loads(pp.read_text(encoding="utf-8"))

    vistas = []
    # 1) los PROYECTOS primero: es lo que se pregunta cuando se pregunta "cómo está montado"
    pdir = plan / "proyectos"
    if pdir.is_dir():
        for pf in sorted(pdir.glob("*.json")):
            try:
                g = json.loads(pf.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"aviso: {pf.name} ilegible ({e})", file=sys.stderr)
                continue
            if not g.get("nodes"):
                print(f"aviso: {pf.name} sin nodos — se omite", file=sys.stderr)
                continue
            vistas.append(vista((g.get("meta", {}) or {}).get("proyecto", pf.stem),
                                "proyecto", g, patron))
    # 2) y el harness al final, que es el sistema, no el producto
    gp = plan / "graph-dataset.json"
    if gp.exists():
        g = json.loads(gp.read_text(encoding="utf-8"))
        if g.get("nodes"):
            vistas.append(vista("El harness (Claude Code)", "harness", g, patron))

    if not vistas:
        print("aviso: ni proyectos/ ni graph-dataset.json — sin datos que explicar", file=sys.stderr)
        return 1

    data = {"meta": {
        "source": "gen_codigo_dataset.py — gen_proyecto_graph.py (proyectos) + gen_harness_graph.py (harness)",
        "date": datetime.date.today().isoformat(),
        "n_vistas": len(vistas),
        "n_proyectos": sum(1 for v in vistas if v["tipo"] == "proyecto"),
        "con_patron": bool(patron),
        "reglas_activas": (patron or {}).get("meta", {}).get("por_estado", {}).get("activo", 0),
        "reglas_total": (patron or {}).get("meta", {}).get("reglas_total", 0),
    }, "vistas": vistas}

    out = plan / "codigo-dataset.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {out}")
    for v in vistas:
        print(f"   {v['tipo']:9} {v['nombre'][:26]:28} {len(v['capas']):2} capas · "
              f"{v['piezas']:4} piezas · {v['relaciones']:4} relaciones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
