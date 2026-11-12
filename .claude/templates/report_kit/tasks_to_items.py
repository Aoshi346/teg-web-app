#!/usr/bin/env python3
"""tasks_to_items.py — convierte un tasks.md (checkboxes) en report.json del report-kit.

Uso:
    python3 tasks_to_items.py [DIR] [--project SLUG] [--plan-id SLUG] [--title "Nombre"] \
                              [--profile proyecto|diseño|incidencia|minimo|issue] [--round N]
      DIR = carpeta con tasks.md (por defecto: cwd). Escribe DIR/report.json.

Formato en tasks.md (flexible, compatible con el del speckit_dashboard legacy):
    # Título del plan                  → meta.title
    ## Wave 1 — Backend                → grupo/página (code = slug) y epic W1
    - [ ] `API-1` [B/P0/M] Implementa el endpoint   → item
      goal: los tests de apps/api pasan en verde     → item.goal (línea indentada opcional)
      desc: texto largo…                             → item.desc (línea indentada opcional)
  Casillas: ` `=backlog · `>`=doing · `x`=done · `!`=blocked (mismo vocabulario que
  speckit-workflow.md §SpecKit Progress Tracking). Vocabulario ÚNICO de status: backlog|doing|review|done|blocked.

Líneas indentadas de UNA línea (opcionales, sin continuación):
      blocks: API-2, API-3        → item.blocks[] — alimenta las flechas y el camino crítico del Gantt
      start: 2026-09-01           → item.start — fecha REAL (si falta, el Gantt la deriva de effort)
      due:   2026-09-05           → item.due
      prereq: backend levantado   → manual_test.prereq (pruebas.html)
      url:   /clientes/nuevo      → manual_test.url
      ref:   Título — https://…   → refs[] (repetible: la investigación que lo sustenta)
      si_si: qué pasa si se aprueba → consecuencias.si
      si_no: qué pasa si NO         → consecuencias.no
      test: Pulsa «Guardar» → el cliente aparece en la lista   → manual_test.steps[] (Cuando → Entonces)
      case: "quiero cita" → propone 3 huecos y pide confirmar  → manual_test.cases[] (chatbot)
      nocturno: si — el gate es golden_eval, verificable solo  → item.nocturno {apto, razon}
                     Valores: si | no | revisar. La RAZÓN es obligatoria de facto: sin ella
                     nadie puede auditar por qué algo se dejó correr sin supervisión.
                     Criterios de elegibilidad: rules/goal-vs-loop.md §Modo noche

IDEMPOTENTE: si DIR/report.json existe, preserva por id los campos KEEP **completos**
(status, decision, note, severity, effort, evidence, tested, nocturno) + CARRY (verdict/why/
howto/history…). Los campos REFRESH (desc, goal, rec, auditor, blocks, start, due, manual_test)
NO se heredan: se releen SIEMPRE del fichero, y si el fichero ya no los declara, se vacían —
corregir el informe se hace editando dashboard.md, nunca borrando report.json.
`status` es la excepción: lo manda el fichero salvo que el Usuario lo cambiara a mano (MO-D5,
meta.tasks_status; MANUAL.md §Quién es dueño de cada campo al regenerar).
Al subir --round N, añade a item.history la foto de la ronda anterior.

Schema: .claude/templates/report_kit/item.schema.json (x-keep) · rule: rules/report-kit.md
"""
import datetime
import json
import os
import re
import sys

STATUSES = ["backlog", "doing", "review", "done", "blocked"]
DECISIONS = ["aprobar", "modificar", "aplazar", "descartar"]
KEEP = ("status", "decision", "note", "severity", "effort", "evidence", "tested", "nocturno")
# `nocturno` va en KEEP —y no en CARRY— porque quien decide qué corre sin supervisión es el
# Usuario en el dashboard, no el autor del tasks.md. Lo que se escribe en tasks.md es la
# PROPUESTA; lo que el Usuario marca, manda, y sobrevive a las regeneraciones.
NOCTURNO_VALUES = {"si", "no", "revisar"}
# Sugerencia del revisor (≠ decisión del Usuario). "no-aprobar" con guion para que sobreviva al
# split por "-" del formato "valor — razón": por eso la razón se separa con — / – / -- / : y NUNCA
# con un guion simple, a diferencia de `nocturno`.
REC_VALUES = {"aprobar", "duda", "no-aprobar"}
CARRY = ("verdict", "confidence", "precision_pct", "why", "howto", "history", "created",
         "agent", "tags", "tl_rec")
# CARRY = generado-pero-editable en el tablero: se hereda del report.json previo porque
# dashboard.md no lo declara.
REFRESH = ("desc", "goal", "rec", "auditor", "blocks", "start", "due", "manual_test",
           "refs", "consecuencias")
# REFRESH = SIEMPRE viene de dashboard.md, **incluso cuando el fichero ya no lo declara**.
# Sustituye al antiguo CARRY_IF_EMPTY, que solo hacía ganar a lo DECLARADO: bastaba con borrar
# o vaciar una línea `rec:` para que el informe siguiera publicando la recomendación vieja para
# siempre, y el único apaño era borrar el report.json entero — que se lleva por delante las
# decisiones del Usuario. Medido el 2026-08-22 (bug RKT-1, tercera vuelta): con `rec:` retirado
# del fichero, el item seguía saliendo con `rec: aprobar — razón vieja` y `auditor:` viejo.
# La frontera es de PROPIEDAD, no de comodidad: REFRESH lo escribe el AGENTE en dashboard.md,
# así que el fichero manda; `decision`, `note`, `nocturno`, `tested` y `evidence` los escribe el
# USUARIO en el tablero y NO se tocan jamás (siguen en KEEP).
SEV = {"P0", "P1", "P2", "P3"}
EFF = {"S", "M", "L", "XL"}
WAVE_COLORS = ["#1b2a4a", "#2563eb", "#6d28d9", "#15803d", "#b45309", "#0e7490", "#be123c", "#4338ca"]


def slug(s):
    return (re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "gen")[:24]


def parse_args(argv):
    opts = {"project": None, "plan-id": None, "title": None, "profile": "proyecto", "round": 1}
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--project", "--plan-id", "--title", "--profile", "--round") and i + 1 < len(argv):
            key = a[2:]
            opts[key] = int(argv[i + 1]) if key == "round" else argv[i + 1]
            i += 2
        else:
            rest.append(a)
            i += 1
    return opts, rest


def main():
    opts, rest = parse_args(sys.argv[1:])
    target = os.path.abspath(rest[0]) if rest else os.getcwd()
    # `dashboard.md` es el nombre nuevo; `tasks.md` el viejo, y el fallback se queda.
    # POR QUÉ SE RENOMBRÓ: convivía con `TASKS.md` (las peticiones del Usuario) en la misma
    # carpeta, y en macOS y Windows —sin distinción de mayúsculas— SON EL MISMO FICHERO. No era
    # una confusión de nombres: era una colisión real al clonar el repo.
    tasks_path = os.path.join(target, "dashboard.md")
    if not os.path.exists(tasks_path):
        tasks_path = os.path.join(target, "tasks.md")
    if not os.path.exists(tasks_path):
        sys.exit("ERROR: no existe %s (necesito un tasks.md con checkboxes)" % tasks_path)

    title = opts["title"]
    epics, pages, pageset, items = {}, [], set(), []
    pagename = {}   # code → nombre, para detectar colisiones de código entre secciones distintas
    cur_page = ("GEN", "General")
    cur_epic = "A"
    cur_field, pending_break = None, False
    n = 0
    for line in open(tasks_path, encoding="utf-8"):
        h1 = re.match(r"#\s+(.+)", line)
        if h1 and not title:
            title = h1.group(1).strip()
        h2 = re.match(r"##+\s+(.+)", line)
        if h2:
            name = h2.group(1).strip()
            # El código es el slug recortado a 8, así que dos secciones que empiezan igual
            # ("Agentes existentes" / "Agentes técnicos de élite") colisionaban EN SILENCIO:
            # la segunda no creaba página y sus items se mezclaban con los de la primera.
            # Se desambigua con sufijo numérico y se avisa, porque un plan al que le falta
            # una página entera no se nota mirándolo — se nota contando.
            base = slug(name).upper()[:8]
            code, k = base, 2
            while code in pageset and pagename.get(code) != name:
                code = "%s%d" % (base[:7], k)
                k += 1
            cur_page = (code, name)
            if code not in pageset:
                if code != base:
                    sys.stderr.write("AVISO: '%s' colisionaba con '%s' → código %s\n"
                                     % (name, pagename.get(base, base), code))
                pageset.add(code)
                pagename[code] = name
                pages.append({"code": code, "name": name, "slug": slug(name)})
            # "Ola" es como se dice aquí; "Wave" viene del formato de SpecKit. Los dos cuentan:
            # sin esto, un plan en español dejaba TODOS los items en el epic por defecto
            # ("A") y el filtro por epic del dashboard no servía para nada.
            wm = re.search(r"(?:wave|ola)\s*(\d+)", name, re.I)
            if wm:
                cur_epic = "W" + wm.group(1)
                epics.setdefault(cur_epic, {"name": name, "color": WAVE_COLORS[int(wm.group(1)) % len(WAVE_COLORS)]})
            continue
        # líneas indentadas goal:/desc: pertenecen al último item
        gm = re.match(r"\s+(goal|desc):\s*(.+)", line)
        if gm and items:
            cur_field = gm.group(1)
            items[-1][cur_field] = gm.group(2).strip()
            continue
        # líneas indentadas de UNA sola línea (sin continuación): dependencias, fechas reales y el
        # guion de prueba manual. Declarar una dependencia tiene que costar una línea o nadie la
        # escribe y el Gantt sale plano (aviso del TL en US-1: hoy blocks[] está vacío en todo).
        om = re.match(r"\s+(blocks|start|due|prereq|url|test|case|nocturno|rec|auditor|ref|si_si|si_no):\s*(.+)", line)
        if om and items:
            cur_field, pending_break = None, False
            key, val = om.group(1), om.group(2).strip()
            it = items[-1]
            if key in ("si_si", "si_no"):
                # LAS CONSECUENCIAS de decidir, que es lo que faltaba para poder decidir.
                # Petición del Usuario (2026-08-26): "poner qué pasaría si se aprueba, a qué
                # afectaría, y también qué pasaría si no se aprueba". Un item con recomendación
                # pero sin consecuencias solo se puede obedecer, no contrastar — el mismo
                # argumento por el que `rec` lleva razón obligatoria.
                it.setdefault("consecuencias", {})["si" if key == "si_si" else "no"] = val
            elif key == "ref":
                # REFERENCIA de la investigación que sustenta el item: de dónde sale lo que afirma.
                # Repetible — una línea por fuente. Sintaxis:
                #     ref: <qué es> — <url o ruta>
                #     ref: <tipo> | <qué es> — <url o ruta>     (tipo explícito)
                # Ejemplos:
                #     ref: Cómo LangGraph descarta claves no declaradas — https://…
                #     ref: repo-interno | El reducer medido — elvion/core/state/flexible_state.py:97
                # El TIPO se infiere si no se declara, y sale del vocabulario que ya pinta el
                # dashboard: doc-oficial | libreria | repo-interno | articulo | norma.
                # Va en REFRESH, no en CARRY: lo escribe el agente en el fichero, así que borrar
                # la línea tiene que borrar la referencia. Si se heredara, corregir el fichero
                # no serviría de nada — es el mordisco de RKT-1 otra vez.
                tipo = ""
                resto = val
                m_tipo = re.match(r"\s*(doc-oficial|libreria|librería|repo-interno|articulo|"
                                  r"artículo|norma)\s*\|\s*(.+)", val, re.I)
                if m_tipo:
                    tipo = m_tipo.group(1).lower().replace("í", "i")
                    resto = m_tipo.group(2)
                partes = re.split(r"\s*(?:—|–|\|)\s*", resto, maxsplit=1)
                if len(partes) == 2:
                    que, url = partes[0].strip(), partes[1].strip()
                else:
                    url = resto.strip()
                    que = re.sub(r"^https?://(www\.)?", "", url).split("?")[0][:70]
                if not tipo:
                    if re.match(r"^https?://", url):
                        tipo = "doc-oficial" if re.search(
                            r"docs?\.|/docs/|readthedocs|developer\.", url) else "articulo"
                    else:
                        tipo = "repo-interno"
                it.setdefault("refs", []).append({"tipo": tipo, "que": que, "url": url})
            elif key == "auditor":
                # ANÁLISIS del auditor: la evidencia detrás de la recomendación, para los items
                # donde `rec` dice "duda" y una línea no basta. Va en CARRY —lo escribe el agente—
                # y NUNCA en `note`, que es del Usuario y no se toca.
                it["auditor"] = val
            elif key == "rec":
                # Sugerencia del REVISOR: "aprobar — razón" / "duda: razón" / "no-aprobar - razón".
                # NO es la decisión del Usuario (esa es `decision`, y solo la escribe él en el
                # tablero): es lo que recomienda quien analizó, para poder aceptarlo en bloque
                # o discreparlo item a item. La razón es obligatoria en la práctica — una
                # recomendación sin porqué no se puede contrastar, solo obedecer.
                parts = re.split(r"\s*(?:—|–|--|:)\s*", val, maxsplit=1)
                rec = parts[0].strip().lower().replace(" ", "-").replace("_", "-")
                if rec not in REC_VALUES:
                    sys.stderr.write(
                        "AVISO: %s tiene rec:'%s' — valores válidos: aprobar|duda|no-aprobar. Ignorado.\n"
                        % (it["id"], parts[0].strip()))
                else:
                    it["rec"] = {"rec": rec,
                                 "razon": (parts[1].strip() if len(parts) > 1 else "")}
            elif key == "nocturno":
                # "si — razón" / "no: razón" / "revisar - razón". La razón es lo que hace
                # auditable la marca; sin ella queda vacía y el dashboard lo señala.
                parts = re.split(r"\s*(?:—|–|--|-|:)\s*", val, maxsplit=1)
                apto = parts[0].strip().lower().replace("sí", "si")
                if apto not in NOCTURNO_VALUES:
                    sys.stderr.write(
                        "AVISO: %s tiene nocturno:'%s' — valores válidos: si|no|revisar. Ignorado.\n"
                        % (it["id"], parts[0].strip()))
                else:
                    it["nocturno"] = {"apto": apto,
                                      "razon": (parts[1].strip() if len(parts) > 1 else "")}
            elif key == "blocks":
                it["blocks"] = [x.strip().strip("`") for x in re.split(r"[,;]", val) if x.strip()]
            elif key in ("start", "due"):
                it[key] = val
            elif key in ("prereq", "url"):
                it.setdefault("manual_test", {})[key] = val
            else:  # test / case — "lo que haces → lo que debe pasar"
                parts = re.split(r"\s*(?:→|->)\s*", val, maxsplit=1)
                left, right = parts[0], (parts[1] if len(parts) > 1 else "")
                mt = it.setdefault("manual_test", {})
                if key == "test":
                    steps = mt.setdefault("steps", [])
                    steps.append({"id": "%s-s%d" % (it["id"], len(steps) + 1),
                                  "action": left.strip(), "expect": right.strip()})
                else:
                    cases = mt.setdefault("cases", [])
                    cases.append({"id": "%s-c%d" % (it["id"], len(cases) + 1),
                                  "input": left.strip().strip('"“”'), "expected": right.strip()})
            continue
        m = re.match(r"\s*[-*]\s*\[([ xX>!])\]\s*(.+)", line)
        if not m:
            # CONTINUACIÓN de un goal/desc multilínea: línea indentada que no abre campo ni item.
            # Sin esto el parser se quedaba con la PRIMERA línea y perdía el resto — que con el
            # formato de 4 bloques (📍 cómo está · 🎯 qué queremos · 🔧 cómo · 🧭 por qué) es casi todo.
            # Línea en blanco dentro del bloque = separación de párrafo.
            if cur_field and items:
                if not line.strip():
                    pending_break = True
                elif line[:1] in (" ", "\t"):
                    sep = "\n\n" if pending_break else " "
                    items[-1][cur_field] = (items[-1][cur_field] + sep + line.strip()).strip()
                    pending_break = False
                else:
                    cur_field = None
            continue
        cur_field, pending_break = None, False
        box, text = m.group(1), m.group(2).strip()
        n += 1
        idm = re.search(r"`([^`]+)`", text)
        iid = idm.group(1) if idm else "T%d" % n
        if idm:
            text = text.replace(idm.group(0), "", 1).strip()
        epic, sev, eff = cur_epic, "P1", "M"
        tm = re.search(r"\[([^\]]+)\]", text)
        if tm:
            for p in [p.strip() for p in re.split(r"[/,]", tm.group(1))]:
                if p in SEV:
                    sev = p
                elif p in EFF:
                    eff = p
                elif p:
                    epic = p[:2].upper()
            text = text.replace(tm.group(0), "", 1).strip()
        if cur_page[0] not in pageset:
            pageset.add(cur_page[0])
            pages.append({"code": cur_page[0], "name": cur_page[1], "slug": slug(cur_page[1])})
        epics.setdefault(epic, {"name": "Epic " + epic, "color": "#2563eb"})
        status = "done" if box.lower() == "x" else "blocked" if box == "!" else "doing" if box == ">" else "backlog"
        items.append({
            "id": iid, "page": cur_page[0], "epic": epic, "severity": sev, "effort": eff,
            "clarity": "claro", "title": text, "desc": "", "goal": "",
            "status": status, "blocks": [], "agent": "", "tags": [],
            "decision": None, "note": "",
            "verdict": None, "confidence": None, "precision_pct": None, "why": "", "howto": "",
            "evidence": [], "history": [],
            "start": "", "due": "", "manual_test": {}, "tested": {}, "nocturno": {},
            "created": datetime.date.today().isoformat(),
            "updated": datetime.date.today().isoformat(),
        })

    if not pages:
        pages = [{"code": "GEN", "name": "General", "slug": "general"}]

    # Lo que dice el FICHERO de cada item, antes de mezclar con el report.json previo. Se guarda en
    # meta.tasks_status para que la siguiente regeneración sepa si el status lo cambió el Usuario a
    # mano (difiere de lo que el fichero decía la última vez) o sigue siendo el del fichero.
    file_status = {it["id"]: it["status"] for it in items}
    out_path = os.path.join(target, "report.json")
    prev_meta = {}
    if os.path.exists(out_path):
        try:
            prev_doc = json.load(open(out_path, encoding="utf-8"))
            prev_meta = prev_doc.get("meta", {})
            prev = {x["id"]: x for x in prev_doc.get("items", [])}
            prev_round = prev_meta.get("round", 1)
            new_round = opts["round"]
            prev_file = prev_meta.get("tasks_status")
            for it in items:
                p = prev.get(it["id"])
                if not p:
                    continue
                skip = set(REFRESH)
                # QUIÉN MANDA EN `status` (MO-D5, decisión del Usuario del 18-10, elvion #20): el
                # fichero (tasks.md / dashboard.md), SALVO que el Usuario lo haya cambiado a mano en
                # el dashboard. «A mano» se sabe comparando el status guardado con lo que el fichero
                # decía en la regeneración anterior (meta.tasks_status): si coinciden, nadie lo tocó
                # y gana el fichero —también `[>]` y `[ ]`, que antes nunca llegaban al informe—.
                # Si difieren, lo movió el Usuario y se conserva, excepto ante una casilla `[x]` o
                # `[!]` NUEVA en el fichero: es una afirmación explícita posterior (hecho/bloqueado).
                prev_said = prev_file.get(it["id"]) if isinstance(prev_file, dict) else None
                if prev_said is not None:
                    by_hand = p.get("status") != prev_said
                    file_moved = it["status"] != prev_said
                    if not by_hand or (file_moved and it["status"] in ("done", "blocked")):
                        skip.add("status")
                # Sin meta.tasks_status (report.json de antes de la 2.14) no se puede saber quién
                # cambió qué: se mantiene la regla anterior. EXCEPCIÓN al KEEP de `status`: una casilla
                # `[x]` o `[!]` en el fichero es una AFIRMACIÓN EXPLÍCITA (hecho / bloqueado) y gana
                # sobre el status heredado; `[ ]` y `[>]` no pisan. La siguiente regeneración ya
                # tiene la foto y aplica la regla nueva.
                elif it.get("status") in ("done", "blocked") and p.get("status") != it["status"]:
                    skip.add("status")

                # KEEP completo — el bug histórico era conservar solo status/decision/note
                for k in KEEP + CARRY:
                    if k in skip:
                        continue
                    if p.get(k) not in (None, "", [], {}):
                        it[k] = p[k]
                # cambio de ronda → snapshot de la anterior al historial
                if new_round > prev_round:
                    hist = it.get("history") or []
                    hist.append({"round": prev_round, "date": prev_meta.get("generated", ""),
                                 "status": p.get("status"), "verdict": p.get("verdict"),
                                 "note": p.get("note", "")})
                    it["history"] = hist
        except Exception as e:
            print("aviso: no pude leer report.json previo (%s); regenero limpio" % e)

    project = opts["project"] or prev_meta.get("project") or slug(os.path.basename(os.path.dirname(target)) or "proyecto")
    plan_id = opts["plan-id"] or prev_meta.get("plan-id") or prev_meta.get("plan_id") or slug(os.path.basename(target))
    meta = {
        "project": project, "plan_id": plan_id,
        "title": title or "Plan", "profile": opts["profile"] if opts["profile"] else prev_meta.get("profile", "proyecto"),
        "round": opts["round"], "generated": datetime.date.today().isoformat(),
        # La HORA, que hasta ahora no se guardaba en ningún sitio. Sin ella el selector de plan
        # solo puede ordenar por la fecha del NOMBRE, y dos planes del mismo día empatan. No se
        # deduce del mtime del fichero a posteriori: eso diría cuándo se regeneró el informe, no
        # cuándo se trabajó — es el mismo error que ya rompió la elección del plan activo.
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
        "schema_version": "1.0", "site": prev_meta.get("site", ""), "shots": "shots/",
        "epics": epics, "pages": pages, "statuses": STATUSES, "decisions": DECISIONS,
        "tasks_status": file_status,
    }
    # meta escrita a mano fuera del parser (otto, closed_at, demo, nombres de epic…) NO se pisa al
    # regenerar: el parser solo es dueño de las claves que él calcula. Sin esto, cada re-run borraba
    # la sección de Otto y los nombres de epic (bug cazado en el plan ai4dev, 2026-08-07).
    for k, v in prev_meta.items():
        if k not in meta:
            meta[k] = v
    for code, prev_epic in (prev_meta.get("epics") or {}).items():
        if code in epics and prev_epic.get("name", "").strip() and not prev_epic["name"].startswith("Epic "):
            epics[code] = prev_epic
    data = {"meta": meta, "items": items}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("Escrito %s — %d items, %d páginas, ronda %s" % (out_path, len(items), len(pages), opts["round"]))


if __name__ == "__main__":
    main()
