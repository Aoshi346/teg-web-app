#!/usr/bin/env python3
"""El ERD de DISEÑO — el modelo de datos antes de que exista una línea de código.

EL HUECO QUE CIERRA, medido el 2026-09-12: nada dibujaba el modelo de datos antes de programarlo.
`/visual-map` lee `models.py` —necesita que el código exista— y `/schema` delega su id `er` en
`/visual-map`. Resultado: los datos se decidían escribiéndolos, que es justo cuando cambiarlos
deja de ser gratis. `/producto` capa 10 prometía un `06-data-model.md` que ningún generador sabía
producir.

NO SE INVENTA UN FORMATO. Se emite el MISMO contrato `ENTITIES`/`RELATIONS` que ya declara
`workflows/visual-map-datos.js`, con la MISMA plantilla `templates/html/data-model.html`:

    entidades.json (la entrevista, /arrancar fase 2) ─┐
                                                      ├─► ENTITIES/RELATIONS ─► data-model.html
    models.py (el código, /visual-map) ───────────────┘

Dos productores, un contrato, una plantilla. Por eso las dos páginas son comparables, y por eso
existe `--diff`.

    python3 gen_modelo_datos.py <plan>            # el ERD de diseño
    python3 gen_modelo_datos.py <plan> --diff     # diseñado vs construido
    python3 gen_modelo_datos.py <plan> --init     # escribe la semilla de entidades.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

TPL = pathlib.Path(__file__).resolve().parents[1] / "templates" / "html" / "data-model.html"

SEMILLA = {
    "_semilla": True,   # quien la rellene quita esta línea; mientras esté, NO se publica
    "_doc": ("Las «cosas» del negocio, tal como salen de la tanda 2.1 de /arrancar. "
             "`personal` es OBLIGATORIO en cada campo: de ahí se deriva la fase 4 (ética) "
             "sin volver a preguntar. `fuente` es OBLIGATORIO en cada entidad "
             "(propia | externa | derivada) y lleva `fuente_detalle` cuando el dato no nace "
             "aquí: un dato sin fuente declarada no es un dato, es una discusión pendiente. "
             "`al_borrar`: cascada | huerfano | prohibido. `mensajes_propios` (tanda 2.5): "
             "true si el producto escribe a clientes por iniciativa propia; entonces nacen las "
             "entidades con `patron` D-1, D-2 y D-6 de patterns/stack/campaigns.md."),
    "mensajes_propios": None,
    "entidades": [
        {"nombre": "Cliente", "como_la_llama_una_persona": "el cliente", "grupo": "core",
         "evidencia": "recordado", "fuente": "propia",
         "campos": [
             {"nombre": "id", "tipo": "id", "pk": True, "personal": False},
             {"nombre": "nombre", "tipo": "texto", "obligatorio": True, "personal": True},
             {"nombre": "nif", "tipo": "texto", "obligatorio": True, "personal": True,
              "sensible": None, "retencion": "6 años (obligación fiscal)"},
         ]},
        {"nombre": "Factura", "como_la_llama_una_persona": "la factura", "grupo": "core",
         "evidencia": "recordado", "fuente": "propia",
         "campos": [
             {"nombre": "id", "tipo": "id", "pk": True, "personal": False},
             {"nombre": "cliente_id", "tipo": "fk", "fk": "Cliente", "personal": False},
             {"nombre": "importe", "tipo": "decimal", "obligatorio": True, "personal": False,
              "fuente": "derivada",
              "fuente_detalle": "suma de las líneas — así se escribe un campo cuyo valor NO es "
                                "su propia fuente. Es el caso que evita el fallo del 0,7196"},
         ]},
        # La tercera entidad de la semilla existe para ENSEÑAR el caso que más duele: un dato que
        # viene de fuera. Sin un ejemplo, `fuente: externa` se rellena como «propia» por inercia.
        {"nombre": "Producto", "como_la_llama_una_persona": "el producto", "grupo": "catalogo",
         "evidencia": "recordado", "fuente": "externa",
         "fuente_detalle": "EJEMPLO — sustitúyelo: «la tienda del cliente, por sincronización cada "
                           "N horas». NO se edita aquí: lo que se edite se pierde en la siguiente "
                           "pasada",
         "campos": [
             {"nombre": "id", "tipo": "id", "pk": True, "personal": False},
             {"nombre": "precio", "tipo": "decimal", "obligatorio": True, "personal": False},
         ]},
    ],
    # Solo si el producto RESPONDE con información (asistente, buscador, cualquier cosa con
    # recuperación): el inventario de fuentes de conocimiento, con UN dueño cada una y qué manda
    # sobre qué cuando dos se contradicen. El gate no lo exige; la tanda 2.1b sí lo pregunta.
    "fuentes_de_conocimiento": [
        {"nombre": "EJEMPLO — catálogo", "almacen": "PostgreSQL", "dueno": "el cliente",
         "manda_sobre": "precio y existencias", "regenerable": False,
         "nota": "es la fuente; lo demás de esta lista es índice o complemento"},
        {"nombre": "EJEMPLO — índice de vectores", "almacen": "Qdrant", "dueno": "derivado",
         "manda_sobre": "nada", "regenerable": True,
         "nota": "si discrepa de la fuente, la fuente tiene razón"},
    ],
    "relaciones": [
        {"de": "Cliente", "a": "Factura", "cardinalidad": "1-N", "al_borrar": "prohibido",
         "etiqueta": "emite"},
    ],
}


def cargar(f: pathlib.Path) -> dict | None:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: {f.name} no es JSON válido: {e.msg} (línea {e.lineno})")


def a_contrato(d: dict) -> tuple[list, list, list]:
    """entidades.json → ENTITIES/RELATIONS, más los avisos de lo que falta declarar."""
    ents, avisos = [], []
    por_nombre = {}
    for i, e in enumerate(d.get("entidades", [])):
        nom = e.get("nombre") or f"Entidad{i}"
        eid = re.sub(r"[^a-z0-9]+", "-", nom.lower()).strip("-")
        por_nombre[nom] = eid
        campos = []
        for c in e.get("campos", []):
            if "personal" not in c:
                avisos.append(f"{nom}.{c.get('nombre','?')} sin `personal: true|false`")
            marca = " ·p" if c.get("personal") else ""
            if c.get("sensible"):
                marca = f" ·{c['sensible']}"
            campos.append({"name": c.get("nombre", "?"),
                           "type": (f"FK→{c['fk']}" if c.get("fk") else c.get("tipo", "?")) + marca,
                           **({"pk": True} if c.get("pk") else {}),
                           **({"fk": True} if c.get("fk") else {})})
        # x/y se calculan después, en `colocar()`: la fila depende de la caja más alta de la anterior
        ents.append({"id": eid, "label": nom, "group": e.get("grupo", "core"),
                     "desc": (e.get("como_la_llama_una_persona", "") +
                              (f" · evidencia: {e['evidencia']}" if e.get("evidencia") else "")),
                     "fields": campos})
        if e.get("evidencia") == "supuesto":
            avisos.append(f"{nom}: evidencia «supuesto» — nadie lo ha confirmado")

    rels = []
    for r in d.get("relaciones", []):
        de, a = por_nombre.get(r.get("de")), por_nombre.get(r.get("a"))
        if not de or not a:
            avisos.append(f"relación {r.get('de')}→{r.get('a')}: alguna entidad no existe")
            continue
        et = r.get("etiqueta", "")
        if r.get("al_borrar"):
            et = f"{et} · al borrar: {r['al_borrar']}".strip(" ·")
        else:
            avisos.append(f"relación {r.get('de')}→{r.get('a')} sin `al_borrar`")
        rels.append({"from": de, "to": a, "kind": r.get("cardinalidad", "1-N"), "label": et})
    return ents, rels, avisos


# Las medidas de la caja son las de la plantilla (`W`, `HEAD`, `ROW` en su <script>): si cambian
# allí, cambian aquí. Con ellas se sabe cuánto mide cada caja ANTES de pintarla.
CAJA_W, CAJA_HEAD, CAJA_ROW = 180, 24, 15
COLS, PASO_X, HUECO_Y, MARGEN = 4, 265, 70, 40
# Un color por grupo, en el orden en que aparecen. La plantilla solo conocía core/content/tax, y
# cualquier otro grupo salía con el trazo `undefined` (negro) y sin leyenda.
PALETA = ["#1b2a4a", "#6d28d9", "#15803d", "#b45309", "#0e7490", "#be123c", "#4d7c0f", "#7c2d12",
          "#334155", "#a21caf"]


def colocar(ents: list) -> tuple[int, int]:
    """Rejilla de COLS columnas; cada fila empieza bajo la caja más alta de la anterior.

    Antes las filas iban cada 230 px fijos y el lienzo era un `viewBox` fijo de 760×540: con 6
    entidades no se notaba; con 46 (medido en el arranque de Elvion, 2026-09-29) se veían dos filas
    y el resto quedaba fuera, y las cajas de 15 campos se montaban sobre la fila siguiente.
    """
    y = MARGEN
    for i in range(0, len(ents), COLS):
        fila = ents[i:i + COLS]
        for j, e in enumerate(fila):
            e["x"], e["y"] = MARGEN + j * PASO_X, y
        y += max(CAJA_HEAD + len(e["fields"]) * CAJA_ROW + 6 for e in fila) + HUECO_Y
    ancho = MARGEN + (min(COLS, max(len(ents), 1)) - 1) * PASO_X + CAJA_W + MARGEN
    return ancho, y - HUECO_Y + MARGEN


def render(ents: list, rels: list, out: pathlib.Path, avisos: list,
           proyecto: str = "", fecha: str = "") -> None:
    t = TPL.read_text(encoding="utf-8")
    ancho, alto = colocar(ents)
    # Se sustituye el bloque de ejemplo de la plantilla, no se escribe un HTML nuevo: así la
    # página de diseño y la de /visual-map son la MISMA página con otros datos.
    nuevo = ("  const ENTITIES=" + json.dumps(ents, ensure_ascii=False) + ";\n"
             "  const RELATIONS=" + json.dumps(rels, ensure_ascii=False) + ";")
    t2 = re.sub(r"  const ENTITIES=\[.*?\];\s*\n\s*const RELATIONS=\[.*?\];",
                nuevo.replace("\\", "\\\\"), t, count=1, flags=re.S)
    if t2 == t:
        sys.exit("ERROR: no se encontró el bloque ENTITIES/RELATIONS en la plantilla")
    t2 = re.sub(r'viewBox="0 0 \d+ \d+"', f'viewBox="0 0 {ancho} {alto}"', t2, count=1)
    grupos = list(dict.fromkeys(e["group"] for e in ents))
    colores = {g: PALETA[i % len(PALETA)] for i, g in enumerate(grupos)}
    t2 = re.sub(r"  const COLORS=\{.*?\};", lambda _: "  const COLORS=" + json.dumps(colores) + ";",
                t2, count=1)
    leyenda = "".join(f'\n    <span><i style="background:{c}"></i>{g}</span>' for g, c in colores.items())
    t2 = re.sub(r'(<div class="legend">).*?(\n    <span><i style="background:#c2410c"></i>PK</span>)',
                lambda m: m.group(1) + leyenda + m.group(2), t2, count=1, flags=re.S)
    if proyecto:
        t2 = t2.replace("[PROYECTO]", proyecto)
    if fecha:
        t2 = t2.replace("[FECHA]", fecha)
    banda = ('<div style="background:#eff6ff;border:1px solid #bfdbfe;padding:10px 14px;'
             'border-radius:8px;margin:10px 0;font-size:13px">'
             '<b>Modelo de DISEÑO</b> — sale de la entrevista de <code>/arrancar</code>, no del '
             'código. Cuando el backend exista, <code>gen_modelo_datos.py --diff</code> compara '
             'lo previsto con lo construido.'
             + (f'<br><b>{len(avisos)} avisos:</b> ' + " · ".join(avisos[:3]) +
                ("…" if len(avisos) > 3 else "") if avisos else "") + '</div>')
    t2 = t2.replace("<body>", "<body>\n" + banda, 1)
    out.write_text(t2, encoding="utf-8")


def diff(dis: dict, vm: pathlib.Path) -> int:
    """Diseñado vs construido. ADVISORY, nunca exit 1."""
    t = vm.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"const ENTITIES=(\[.*?\]);", t, re.S)
    if not m:
        print("· no se pudo leer ENTITIES de la página construida — nada que comparar")
        return 2
    try:
        constr = json.loads(m.group(1))
    except json.JSONDecodeError:
        print("· la página construida tiene ENTITIES en JS no parseable (normal si se editó a mano)")
        return 2
    n = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower()).rstrip("s")
    d_set = {n(e["nombre"]): e for e in dis.get("entidades", [])}
    c_set = {n(e.get("label", e.get("id", ""))): e for e in constr}

    falta = sorted(set(d_set) - set(c_set))
    sobra = sorted(set(c_set) - set(d_set))
    print(f"  diseñadas: {len(d_set)} · construidas: {len(c_set)}")
    if falta:
        print("\n  PREVISTAS Y NO CONSTRUIDAS:")
        for k in falta:
            print(f"    · {d_set[k]['nombre']}")
    if sobra:
        print("\n  CONSTRUIDAS Y NO PREVISTAS  ← el caso peligroso:")
        for k in sobra:
            print(f"    · {c_set[k].get('label', k)}")
        print("    Aquí es donde suelen aparecer los datos personales que nadie declaró.")
    pers = [f"{e['nombre']}.{c['nombre']}" for e in dis.get("entidades", [])
            for c in e.get("campos", []) if c.get("personal") and n(e["nombre"]) in c_set]
    if pers:
        print(f"\n  {len(pers)} campos personales previstos en entidades que SÍ existen: "
              f"{', '.join(pers[:5])}{'…' if len(pers) > 5 else ''}")
        print("    Compruébalos contra la fase 4 (ética) — no los deriva este script.")
    print("\n  Es ADVISORY: /visual-map sintetiza con un LLM, no parsea el ORM, así que los\n"
          "  nombres no coinciden literalmente. Una lista para revisar, nunca un gate.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="El ERD de diseño")
    ap.add_argument("plan")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()
    plan = pathlib.Path(a.plan).resolve()
    f = plan / "arranque" / "entidades.json"

    if a.init or not f.exists():
        if f.exists():
            print(f"· ya existe {f.name} — no se toca"); return 0
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(SEMILLA, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"· escrita la SEMILLA en {f.relative_to(plan)}. Rellénala en /arrancar fase 2 y\n"
              f"  quita la línea `_semilla`. No se publica un ejemplo inventado.")
        return 0

    d = cargar(f)
    if d.get("_semilla"):
        print(f"· {f.name} sigue siendo la SEMILLA (`_semilla: true`). Rellénala y quita esa línea.")
        return 0

    if a.diff:
        vm = plan / "data-model.html"
        if not vm.exists():
            print("· no hay data-model.html construido todavía — corre /visual-map primero")
            return 2
        return diff(d, vm)

    ents, rels, avisos = a_contrato(d)
    if not ents:
        print("· entidades.json sin entidades — no se genera"); return 0
    out = plan / "data-model.html"
    meta = d.get("meta") or {}
    render(ents, rels, out, avisos, proyecto=meta.get("producto") or plan.name,
           fecha=meta.get("revisado") or meta.get("fecha") or "")
    print(f"OK {out}  ({len(ents)} entidades, {len(rels)} relaciones"
          + (f", {len(avisos)} avisos" if avisos else "") + ")")
    for x in avisos[:6]:
        print(f"   ⚠ {x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
