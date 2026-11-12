#!/usr/bin/env python3
"""audit_sistema_ia.py — cruza lo que el CÓDIGO de un proyecto ES con lo que su HARNESS TIENE.

EL HUECO QUE CIERRA. Ya teníamos dos mitades y ningún puente:
  · `template_diff.py` dice "te falta la skill X porque el template la tiene"  → indiscriminado
  · `code-graph` / graphify dibujan el código                                   → no miran .claude/
Ninguno responde la pregunta útil: **¿qué piezas le tocan a ESTE proyecto por lo que hace?**
Un backend con LangGraph necesita observabilidad y evaluación aunque el template no haya cambiado;
un CRUD interno no necesita el auditor de sesgo por mucho que exista.

TRES SALIDAS, y las tres son distintas a propósito:
  1. FALTA      — el código pide una pieza que el proyecto no tiene   (la que nadie calculaba)
  2. DESFASADO  — la tiene, pero el template la ha movido             (esto ya lo hacía template_diff)
  3. COSECHABLE — el proyecto tiene algo propio que el template no    (el bucle de vuelta)

Y un cuarto que es el gate: SOBRA — piezas instaladas que su código no justifica. No se borran
solas; se listan, porque una skill que no aplica compite por atención con las que sí
(`self-improvement-loop.md` §5, criterio 30/60).

CÓMO DETECTA. Por SEÑALES en el código, no por adivinación: una expresión regular concreta sobre
ficheros concretos, y cada hallazgo trae su `fichero:línea` para poder comprobarlo. Si no hay cita,
no hay hallazgo — la misma regla de `verdict-contract.md` que exigimos a los auditores.

LÍMITE HONESTO, dicho antes de que alguien se fíe de más: esto detecta lo que sabe buscar. Un stack
que no esté en SEÑALES no se ve, y por eso la tabla vive aquí arriba, legible y ampliable, en vez de
enterrada. No sustituye a leer el proyecto: acota por dónde empezar.

Uso:
  python3 audit_sistema_ia.py <proyecto> [--template DIR] [--json salida.json] [--gate]
  --gate → exit 1 si hay piezas FALTA de prioridad alta (para un hook o un CI)
"""
import argparse, json, os, re, subprocess, sys
from collections import defaultdict
from datetime import date
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────────────────────
# LA TABLA. Señal observable en el código → piezas del harness que le corresponden.
# Se amplía aquí. Cada entrada: (regex, en qué ficheros, qué piezas, prioridad, por qué).
# La prioridad ALTA significa "sin esto, el proyecto tiene un agujero conocido", no "estaría bien".
# ─────────────────────────────────────────────────────────────────────────────────────────────
SENALES = [
    dict(id="langgraph", rx=r"StateGraph|from langgraph|add_node\(|ToolNode", ext=(".py",),
         prio="alta", piezas=["skills/instrumentar-agente", "skills/langgraph-debug",
                              "patterns/stack/agente-observabilidad.md",
                              "patterns/stack/agente-determinismo.md",
                              "agents/ivan-agent-runtime", "skills/agent-evals"],
         porque="Un grafo de agente sin trazas es una caja negra: cuando falla, nadie sabe qué nodo "
                "ni con qué estado. El checkpointer suele estar puesto y nadie lo lee."),
    # Auditados los 3 agentes de la casa el 2026-08-26: los 6 bugs de mayor impacto eran de ESTADO,
    # y ninguno daba señal. Un checkpointer sin poda declarada es la firma de ese grupo.
    dict(id="agente-estado", rx=r"checkpointer|MemorySaver|PostgresSaver|SqliteSaver|Annotated\[.*add",
         ext=(".py",), prio="alta",
         piezas=["patterns/stack/agente-memoria.md", "agents/ivan-agent-runtime",
                 "patterns/stack/detect_estado_huerfano.py"],
         porque="Los fallos de estado no lanzan excepción: un reducer equivocado duplica el "
                "historial y una clave que el State no declara se descarta en silencio "
                "(langgraph/graph/state.py:962). Se detectan midiendo, no leyendo."),
    # Una tool que escribe fuera y ningún interrupt() = el bot puede ejecutar algo sin vuelta atrás.
    dict(id="agente-sin-puerta",
         rx=r"@tool[\s\S]{0,400}?def\s+(book|reserva|cancel|anula|delete|borra|pay|paga|cobra|"
            r"refund|reembolsa|send|envia|create_order|create_invoice|transfer|publish)",
         ext=(".py",), prio="alta",
         piezas=["patterns/stack/agente-hitl.md"],
         porque="Hay tools que escriben en sistemas de terceros. Si no hay una puerta de aprobación "
                "en el grafo, lo único que separa al bot de una acción sin vuelta atrás es una "
                "frase en mayúsculas del prompt."),
    # Un bucle de reintento sin criterio de salida es donde se va el presupuesto sin que nadie mire.
    dict(id="agente-reintento", rx=r"retry|reintent|rephrase_count|recursion_limit|max_attempts",
         ext=(".py",), prio="media", min_ficheros=2,
         piezas=["patterns/stack/agente-evaluator-optimizer.md", "skills/eval-estadistica"],
         porque="Un ciclo de auto-corrección sin contador en el estado ni nodo de rendición "
                "termina en una excepción de recursión, que es la peor forma de rendirse."),
    dict(id="tools-llm", rx=r"@tool\b|tools\s*=\s*\[|bind_tools\(|function_call", ext=(".py",),
         prio="alta", piezas=["patterns/stack/agente-tools.md", "patterns/stack/agente-cuando-no.md"],
         porque="La `description` de una tool ES el prompt que decide si se llama. Sin patrón, "
                "cada tool se escribe distinta y el modelo elige mal."),
    dict(id="rag", rx=r"qdrant|pinecone|weaviate|chromadb|embeddings?\.|vector_store|similarity_search",
         ext=(".py",), prio="alta",
         piezas=["agents/rafa-retrieval-engineer", "skills/vector-db"],
         porque="El retrieval falla en silencio: devuelve algo plausible y equivocado. Sin golden "
                "set y sin auditar la integridad del vector store, no se detecta."),
    dict(id="chatbot", rx=r"system_prompt|chat_completion|ChatOpenAI|ChatAnthropic",
         ext=(".py",), prio="media", min_ficheros=2,
         piezas=["agents/nadia-chatbot-evaluator", "agents/teo-llm-redteam",
                 "skills/disenar-conversacion"],
         porque="Calidad conversacional, alucinación y coste por conversación no los mide ningún "
                "test unitario."),
    dict(id="comercio", rx=r"\bprecio\b|\bstock\b|descuento|checkout|carrito|\bpvp\b", ext=(".py", ".ts", ".tsx"),
         prio="alta", min_ficheros=3, piezas=["agents/dario-commerce-guardrails"],
         porque="Un bot que inventa un precio o promete stock genera responsabilidad legal real."),
    dict(id="datos-salud", rx=r"\bclinic\w*|paciente|patient|historia_clinica|sanitari", ext=(".py",),
         prio="alta", min_ficheros=3, piezas=["agents/priya-privacy-auditor", "rules/fairness-audit.md"],
         porque="Datos de salud son categoría especial (RGPD Art. 9). La base legal y el borrado "
                "downstream no son opcionales."),
    dict(id="pagos", rx=r"stripe|paypal|redsys|payment_intent|\bcobro\b", ext=(".py", ".ts"),
         prio="alta", piezas=["agents/sofia-pentester", "rules/security.md"],
         porque="Donde hay dinero hay incentivo. IDOR y control de acceso roto son el top de OWASP."),
    dict(id="django", rx=r"from django|DJANGO_SETTINGS|models\.Model", ext=(".py",),
         prio="media", piezas=["agents/desarrollador-backend", "skills/django-orm",
                               "patterns/stack/pattern_check_backend.py"],
         porque="El patrón de casa para Django ya está destilado; sin el comprobador, cada módulo "
                "deriva por su cuenta."),
    dict(id="react", rx=r"from ['\"]react['\"]|useState|useEffect", ext=(".tsx", ".jsx", ".ts"),
         prio="media", piezas=["skills/nueva-pantalla", "skills/disenar-pantalla",
                               "patterns/stack/pattern_check_frontend.py"],
         porque="Idem frontend, y además ahí vive el diseño de pantallas."),
    dict(id="e2e", rx=r"playwright|cypress|selenium|page\.goto\(", ext=(".py", ".ts", ".js"),
         prio="media", piezas=["rules/verification.md", "skills/visual-regression"],
         porque="Un E2E intermitente es peor que no tenerlo: entrena al equipo a ignorar el rojo."),
    dict(id="celery", rx=r"from celery|@shared_task|\.delay\(|apply_async", ext=(".py",),
         prio="baja", piezas=["commands/deploy.md", "patterns/stack/backend-celery.md"],
         porque="Las tareas asíncronas fallan donde nadie mira."),
    dict(id="ui", rx=r"className=|<div|styled\.", ext=(".tsx", ".jsx"),
         prio="media", piezas=["rules/qa-loop.md", "agents/vera-art-director", "agents/lidia-naive-tester"],
         porque="Toda wave con UI cierra con el bucle de auditores; sin ellos el gate no existe."),
]

# `.claude` FALTABA aquí, y era el fallo: el barrido de señales pregunta «¿qué pide el CÓDIGO de
# este proyecto?», y el harness no es código del proyecto. Como el CORE le copia a cada derivado la
# tabla de señales de este mismo fichero, el detector la leía y la reportaba como evidencia SOBRE el
# proyecto. Medido el 2026-08-26 en `elvion-autoparte-demo`: 5 de 12 recomendaciones eran falsas,
# **incluidas las dos de prioridad ALTA** —`quim-data-integrity` por «qdrant» y `sofia-pentester`
# por «stripe»— con CERO menciones de ninguna de las dos en `apps/`, `frontend/src/` ni el proyecto
# Django. Se atienden primero justo las que estaban mal.
#
# Lo delator es que `.docs` sí estaba: alguien pensó en el directorio de documentación y se dejó el
# del harness. El inventario NO se rompe por esto — `instaladas()` recorre `.claude/` por su cuenta
# con su propio `glob`, que es otra pregunta («¿qué TIENE instalado?») y otro bucle.
IGNORAR = re.compile(r"(^|/)(node_modules|\.git|\.venv|venv|__pycache__|dist|build|migrations|"
                     r"graphify-out|\.docs|\.claude|_archive)/")

def escanear(raiz: Path, max_ficheros=4000):
    """Recorre el código UNA vez contando apariciones por señal y por fichero.

    Cuenta en vez de parar en el primer match A PROPÓSITO: la primera aparición de "catalog" suele
    estar en un `celery.py` (es el nombre de una app) y como cita no demuestra nada. Lo que
    demuestra es la CONCENTRACIÓN — y de paso permite exigir un mínimo de ficheros a las señales
    con palabras de uso común, que es de donde salen los falsos positivos."""
    crudo = defaultdict(list)                      # señal → [(fichero, línea, texto, nº apariciones)]
    exts = {e for s in SENALES for e in s["ext"]}
    rx = [(s, re.compile(s["rx"], re.IGNORECASE)) for s in SENALES]
    n = 0
    for p in raiz.rglob("*"):
        if n >= max_ficheros: break
        if not p.is_file() or p.suffix not in exts: continue
        rel = str(p.relative_to(raiz))
        if IGNORAR.search("/" + rel): continue
        n += 1
        try: texto = p.read_text(errors="ignore")
        except OSError: continue
        for s, r in rx:
            if p.suffix not in s["ext"]: continue
            ms = list(r.finditer(texto))
            if ms:
                m = ms[0]
                crudo[s["id"]].append((rel, texto[:m.start()].count("\n") + 1, m.group(0)[:40], len(ms)))

    hits = {}
    for s in SENALES:
        lista = crudo.get(s["id"], [])
        if len(lista) < s.get("min_ficheros", 1):   # umbral por señal: filtra la coincidencia suelta
            continue
        lista.sort(key=lambda t: -t[3])             # el fichero con más apariciones va primero
        hits[s["id"]] = [(f, l, t) for f, l, t, _ in lista[:3]]
    return hits, n

def retiradas(tpl: Path):
    """Lo que el template TUVO y ya no tiene: `_archive/` y `_deprecated/`.

    POR QUÉ HACE FALTA, y es un falso positivo que se vio en cuanto se archivó de verdad: un
    proyecto derivado conserva las piezas que nosotros acabamos de jubilar, así que al compararlo
    contra `agents/` salen como «propias del proyecto» y el informe propone COSECHARLAS DE VUELTA.
    Con 20 agentes retirados en una tarde, eso son 20 propuestas de deshacer lo que se decidió.

    Retirado ≠ nuestro-nunca: es nuestro y con fecha de baja. Si un proyecto lo sigue teniendo, la
    acción correcta es retirarlo allí también —o dejarlo a propósito—, jamás traerlo de vuelta."""
    fuera = set()
    for base in (tpl / "_archive", tpl / ".claude" / "_archive",
                 tpl / ".claude" / "agents" / "_deprecated",
                 tpl / ".claude" / "skills" / "_deprecated"):
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            # Los PLANES archivados (`_archive/<fecha>/planes-*/`, LI-30 2026-10-19) no son piezas:
            # mismo criterio que `template_diff.retiradas()`. Además se evita recorrer sus kits (70 MB).
            dirnames[:] = [d for d in dirnames if not d.startswith("planes-")]
            fuera.update(dirnames)
            for fn in filenames:
                stem, ext = os.path.splitext(fn)
                if ext in (".md", ".py", ".js", ".sh"):
                    fuera.add(stem)
    # Archivada y VUELTA a la vida no es retirada: `director`, `business-manager`, `django-orm-*`
    # y `entrevistador-negocio` se archivaron el 2026-08-22 y volvieron, y el cruce seguía
    # llamándolas «ya retiradas» en cada proyecto (aiatech-web, 2026-09-28). Manda el disco vivo.
    vivas = {Path(x).name for x in instaladas(tpl / ".claude")} | {Path(x).stem for x in instaladas(tpl / ".claude")}
    return {x for x in fuera if x not in ("README", "readme") and x not in vivas}


def instaladas(cdir: Path):
    """Qué piezas tiene el .claude/ del proyecto, en el vocabulario de la tabla."""
    tiene = set()
    for cat, pat in (("skills", "*/SKILL.md"), ("agents", "*.md"), ("rules", "*.md"),
                     ("patterns/stack", "*"), ("workflows", "*.js"), ("commands", "*.md")):
        base = cdir / cat
        if not base.exists(): continue
        for f in base.glob(pat):
            nombre = f.parent.name if pat.endswith("SKILL.md") else f.name
            tiene.add(f"{cat}/{nombre}")
            tiene.add(f"{cat}/{Path(nombre).stem}")
    return tiene

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proyecto")
    ap.add_argument("--template", default=os.environ.get("TL_TEMPLATE_DIR") or str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--json"); ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()

    proy, tpl = Path(a.proyecto).resolve(), Path(a.template).resolve()
    cdir_p, cdir_t = proy / ".claude", tpl / ".claude"
    if not proy.exists(): print(f"✗ no existe: {proy}"); return 2
    # Sin template no hay cruce: ABORTA, no devuelve un número (rules/verification.md). Antes, con
    # la ruta por defecto inexistente, `tiene_t` quedaba vacío y TODO el harness salía «propio del
    # proyecto, cosechable» — 184 piezas en aiatech-web el 2026-09-28. Y si template y proyecto son
    # el mismo directorio, el cruce se hace consigo mismo y tampoco mide nada.
    if not cdir_t.is_dir():
        print(f"✗ template no encontrado: {cdir_t}\n  Pasa --template <ruta> o exporta TL_TEMPLATE_DIR.",
              file=sys.stderr); return 2
    if tpl == proy:
        print(f"✗ template y proyecto son el mismo directorio ({proy}): el cruce no mide nada.\n"
              "  Pasa --template <ruta-del-template>.", file=sys.stderr); return 2

    hits, n_fich = escanear(proy)
    tiene_p = instaladas(cdir_p) if cdir_p.exists() else set()
    tiene_t = instaladas(cdir_t) if cdir_t.exists() else set()

    falta, ok, sobra_cand = [], [], set()
    for s in SENALES:
        if s["id"] not in hits or not hits[s["id"]]: continue
        for pieza in s["piezas"]:
            clave = pieza if "/" in pieza else pieza
            presente = clave in tiene_p or Path(clave).name in {Path(x).name for x in tiene_p}
            registro = dict(senal=s["id"], pieza=pieza, prio=s["prio"], porque=s["porque"],
                            evidencia=[f"{f}:{l} → {t}" for f, l, t in hits[s["id"]]])
            (ok if presente else falta).append(registro)

    justificadas = {p for s in SENALES if hits.get(s["id"]) for p in s["piezas"]}
    justificadas |= {Path(p).name for p in justificadas}
    def canon(x):
        """Un `<pieza>.md` y un `<pieza>` sin extensión son la MISMA pieza: una clave, no dos."""
        d, _, n = x.rpartition("/")
        return f"{d}/{n[:-3] if n.endswith('.md') else n}"

    just_c = {canon(p) for p in justificadas} | {Path(p).stem for p in justificadas}
    tiene_t_c = {canon(x) for x in tiene_t} | {Path(x).stem for x in tiene_t}
    RUIDO = ("README", "shared", "__init__")

    # PROPIO del proyecto: lo que NO viene del template. Se mira aparte y NUNCA cuenta como
    # "sobra" — si el proyecto se molestó en escribir un agente a medida y esta tabla no lo
    # conoce, la conclusión es que falta una señal AQUÍ, no que el agente sobre allí.
    JUBILADAS = retiradas(tpl)
    cosechable = sorted({canon(x) for x in tiene_p
                         if canon(x) not in tiene_t_c and Path(x).stem not in tiene_t_c
                         and Path(x).stem not in JUBILADAS
                         and x.startswith(("skills/", "agents/", "workflows/", "patterns/"))
                         and Path(x).stem not in RUIDO})
    # Cuarta salida: lo que el proyecto conserva y NOSOTROS ya retiramos. No se cosecha ni se
    # borra solo — se decide, porque puede estar ahí a propósito.
    jubiladas_aqui = sorted({canon(x) for x in tiene_p
                             if Path(x).stem in JUBILADAS
                             and x.startswith(("skills/", "agents/", "workflows/", "patterns/"))})
    cos_c = set(cosechable) | {Path(c).stem for c in cosechable}

    # SIN JUSTIFICAR: solo piezas HEREDADAS del template que el código de este proyecto no pide.
    # Son candidatas a poda (self-improvement-loop.md §5), no a borrado automático.
    sobra = sorted({canon(x) for x in tiene_p
                    if x.startswith(("agents/", "patterns/stack/")) and "/" in x
                    and canon(x) not in just_c and Path(x).stem not in just_c
                    and canon(x) not in cos_c and Path(x).stem not in cos_c
                    and Path(x).stem not in RUIDO})

    res = dict(meta=dict(proyecto=str(proy), template=str(tpl), fecha=date.today().isoformat(),
                         ficheros_escaneados=n_fich, senales_activas=sorted(k for k in hits if hits[k]),
                         tiene_claude=cdir_p.exists()),
               falta=sorted(falta, key=lambda r: {"alta": 0, "media": 1, "baja": 2}[r["prio"]]),
               ok=ok, sobra=sobra[:20], cosechable=cosechable[:20],
               retiradas_en_template=jubiladas_aqui[:20])

    if a.json: Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1))

    print(f"\n  {proy.name} — {n_fich} ficheros · señales: {', '.join(res['meta']['senales_activas']) or 'ninguna'}")
    if not cdir_p.exists(): print(f"  ⚠ el proyecto NO tiene .claude/ — todo saldrá como FALTA\n")
    alta = [f for f in res["falta"] if f["prio"] == "alta"]
    print(f"\n  FALTA {len(res['falta'])} (alta: {len(alta)}) · YA TIENE {len(ok)} · "
          f"sin justificar {len(sobra)} · cosechable {len(cosechable)}\n")
    for f in res["falta"][:14]:
        print(f"  [{f['prio']:<5}] {f['pieza']:<46} ← señal '{f['senal']}'")
        print(f"          {f['evidencia'][0]}")
    if sobra:      print(f"\n  sin justificar por el código: {', '.join(Path(s).name for s in sobra[:8])}")
    if cosechable: print(f"  propio del proyecto (cosechable al template): {', '.join(Path(c).name for c in cosechable[:8])}")
    if jubiladas_aqui:
        print(f"\n  ⚠ el proyecto conserva {len(jubiladas_aqui)} pieza(s) que el template YA RETIRÓ:")
        print(f"      {', '.join(Path(x).name for x in jubiladas_aqui[:10])}")
        print("      No son cosechables: son nuestras y con fecha de baja. Ver _archive/<fecha>/README.md")

    if a.gate and alta:
        print(f"\n  ✗ GATE: {len(alta)} piezas de prioridad ALTA sin instalar"); return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
