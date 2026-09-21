#!/usr/bin/env python3
"""trend_lint.py — gate determinista del `trend-delta.json` de un auditor-persona (AUD-7).

Por qué existe: las claves de salida de Lidia derivaron SOLAS entre rondas
(`score_avg`→`score`, `categorical_verdict`→`verdict_categorico`, `findings`→`findings_status`,
y hasta una dimensión: `cta_botones`→`cta`). Consecuencia: sus tres rondas **no son comparables
por máquina** y cualquier A/B automatizado se rompe en el parseo — después de haber gastado las
pasadas caras de navegador. Esto lo caza antes, y gratis.

Comprueba, además del esquema (`.claude/templates/trend-delta.schema.json`):
  · que la media declarada ES la media de las dimensiones (AUD-7) — las dos: raw y profiled
  · que el perfil de rúbrica y las dimensiones N/A son coherentes entre sí (AUD-8)
  · que la corrida dejó escrito con qué corrió: modelo, calibración, sha del objetivo,
    sha de la ficha y nº de pasada (AUD-9)
  · que cada hallazgo lleva ancla máquina-legible (AUD-10) — cobertura, como aviso
  · que el veredicto binario existe y es coherente con `passed` (AUD-11)

ERROR (exit 1) = el fichero no es comparable ni utilizable por un script.
warn  (exit 0) = falta contexto o calidad, pero el fichero se puede procesar.
Mismo contrato que `spec_lint.py` / `task_progress.py --gate`.

Uso:
  python3 trend_lint.py <fichero.json | directorio> [...]     # valida (recursivo en directorios)
  python3 trend_lint.py <f.json> --json                       # salida máquina
  python3 trend_lint.py <f.json> --normalize -o <salida.json> # migra un fichero legacy a v1
  python3 trend_lint.py <f.json> --normalize --in-place       # (destructivo: pisa el original)

`--normalize` NUNCA inventa una medición: lo que no consta se escribe como `"unknown"` y queda
listado en el bloque `_normalized` del propio fichero. Un `unknown` es un aviso permanente de que
esa corrida no registró su contexto, no un hueco que se tapa.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.normpath(os.path.join(HERE, "..", "templates", "trend-delta.schema.json"))

# Tolerancia de la comprobación aritmética. 0.05 = una cifra decimal: las rondas históricas
# declararon 6.6 donde la media exacta es 6.625, y ese redondeo NO es el problema que AUD-7
# viene a resolver. Con --strict se exige la igualdad a 2 decimales.
TOL = 0.05

ALIAS_TOP = {"score_avg": "score_raw", "score": "score_raw"}
ALIAS_DIM = {"cta_botones": "cta", "diseño": "diseno"}
LABEL_MAP = {
    "si": "si", "sí": "si", "yes": "si",
    "sola, sin ayuda": "si", "sola sin ayuda": "si", "contactaria": "si", "contactaría": "si",
    "con ayuda": "con_ayuda", "con_ayuda": "con_ayuda",
    "no": "no", "no contactaria": "no", "no contactaría": "no",
}
PAGE_VERDICT_MAP = {
    "claro": "claro", "algo claro": "algo_claro", "algo_claro": "algo_claro",
    "confuso": "confuso", "muy confuso": "muy_confuso", "muy_confuso": "muy_confuso",
}
STATUS_MAP = {
    "closed": "closed", "closed_stable": "closed_stable",
    "closed_but_superseded": "closed_but_superseded", "open": "open",
    "open_info": "open_info", "regression": "regression",
}
UNKNOWN_RUN = ["model_id", "calibration_version", "target_sha", "agent_sha"]


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _dims(schema):
    return list(schema["properties"]["rubric"]["required"])


def _enum(schema, *path):
    node = schema
    for p in path:
        node = node[p]
    return list(node["enum"])


# ---------------------------------------------------------------- validación

def validate(doc, schema, strict=False):
    errors, warns, stats = [], [], {}
    dims = _dims(schema)

    # 0) esquema completo, si hay jsonschema instalado (opcional a propósito: el gate no puede
    #    depender de un pip install para funcionar en un proyecto derivado recién clonado)
    try:
        import jsonschema  # noqa: PLC0415
        req, other = {}, []
        for err in sorted(jsonschema.Draft202012Validator(schema).iter_errors(doc),
                          key=lambda e: list(map(str, e.path))):
            loc = "/".join(str(p) for p in err.path) or "(raíz)"
            if err.validator == "required":
                # 7 hallazgos × 4 claves ausentes son 1 problema, no 28 líneas de ruido
                loc = loc.split("/")[0] + "[]" if loc[:1].isalpha() and "/" in loc else loc
                req.setdefault(loc, set()).add(err.message.split("'")[1])
            else:
                other.append(f"E-schema {loc}: {err.message}")
        for loc, keys in req.items():
            errors.append(f"E-schema {loc}: faltan claves obligatorias: {', '.join(sorted(keys))}")
        errors.extend(other)
    except ImportError:
        warns.append("W-dep jsonschema no instalado — solo se han corrido las reglas propias "
                     "(pip install jsonschema para la validación estructural completa)")

    # 1) claves muertas del esquema viejo: son EL fallo que motivó este validador
    for dead, alive in ALIAS_TOP.items():
        if dead in doc and alive not in doc:
            errors.append(f"E-drift clave muerta «{dead}» → usa «{alive}» (deriva de esquema AUD-7)")
    for dead in ("categorical_verdict", "findings_status", "final_verdict",
                 "gate_categorico_dimensiones"):
        if dead in doc:
            warns.append(f"W-drift clave del esquema viejo presente: «{dead}» — normaliza el fichero")
    rub = doc.get("rubric") or {}
    for dead, alive in ALIAS_DIM.items():
        if dead in rub:
            errors.append(f"E-drift dimensión muerta «{dead}» → «{alive}»")

    if not isinstance(rub, dict) or not rub:
        errors.append("E-rubric falta el bloque `rubric` — sin él no hay nada que comprobar")
        return errors, warns, stats

    missing = [d for d in dims if d not in rub]
    if missing:
        errors.append(f"E-rubric faltan dimensiones: {', '.join(missing)}")
    extra = [k for k in rub if k not in dims]
    if extra:
        errors.append(f"E-rubric dimensiones no reconocidas: {', '.join(extra)}")
    if missing or extra:
        return errors, warns, stats

    # 2) aritmética — el corazón del item: la media declarada ES la media
    scores = {}
    for d in dims:
        s = rub[d].get("score") if isinstance(rub[d], dict) else None
        if not isinstance(s, (int, float)):
            errors.append(f"E-rubric «{d}» sin `score` numérico (debe estar incluso si na=true, "
                          "es lo que mantiene comparable score_raw con el histórico)")
        else:
            scores[d] = float(s)
    if len(scores) != len(dims):
        return errors, warns, stats

    na_flags = {d for d in dims if isinstance(rub[d], dict) and rub[d].get("na") is True}
    na_decl = set(doc.get("na_dimensions") or [])
    if na_flags != na_decl:
        errors.append(f"E-profile `na_dimensions` {sorted(na_decl)} no coincide con las marcadas "
                      f"`na:true` en rubric {sorted(na_flags)}")
    if doc.get("profile") == "landing" and na_flags:
        errors.append("E-profile profile=landing con dimensiones N/A: en una landing L-D sí aplica "
                      "(si no hay foto humana, Fotos ≤4 — eso es un hallazgo, no un N/A)")
    if doc.get("profile") == "herramienta-interna" and "fotos_videos" not in na_flags:
        warns.append("W-profile profile=herramienta-interna pero fotos_videos NO está marcada N/A — "
                     "es justo el −0.6 fijo que AUD-8 viene a quitar")

    tol = 0.005 if strict else TOL
    raw_exact = sum(scores.values()) / len(scores)
    stats["score_raw_exact"] = round(raw_exact, 4)
    if abs(float(doc.get("score_raw", -1)) - raw_exact) > tol:
        errors.append(f"E-arith score_raw declarado {doc.get('score_raw')} ≠ media de las "
                      f"{len(scores)} dimensiones ({raw_exact:.3f}); tolerancia ±{tol}")

    appl = {d: v for d, v in scores.items() if d not in na_flags}
    prof_exact = sum(appl.values()) / len(appl) if appl else 0.0
    stats["score_profiled_exact"] = round(prof_exact, 4)
    stats["dims_applicable"] = len(appl)
    if abs(float(doc.get("score_profiled", -1)) - prof_exact) > tol:
        errors.append(f"E-arith score_profiled declarado {doc.get('score_profiled')} ≠ media de las "
                      f"{len(appl)} dimensiones aplicables ({prof_exact:.3f}); tolerancia ±{tol}")

    # 3) veredicto binario coherente (AUD-11: es el titular, no la media)
    v = doc.get("verdict_categorico") or {}
    if isinstance(v, dict) and "label" in v and "passed" in v:
        if v["passed"] is not (v["label"] == "si"):
            errors.append(f"E-verdict `passed`={v['passed']} incoherente con label={v['label']!r} "
                          "(`con_ayuda` NO es aprobado)")
    for pg, lab in (doc.get("pages_verdict") or {}).items():
        if lab not in PAGE_VERDICT_MAP.values():
            warns.append(f"W-verdict pages_verdict[{pg}]={lab!r} fuera del vocabulario canónico "
                         "(claro|algo_claro|confuso|muy_confuso)")

    # 4) contexto de corrida (AUD-9) — `unknown` es legítimo pero se dice en voz alta
    run = doc.get("run") or {}
    unk = [k for k in UNKNOWN_RUN if str(run.get(k, "")).lower() in ("", "unknown", "none")]
    if unk:
        warns.append(f"W-run sin registrar: {', '.join(unk)} — esa corrida no es reproducible ni "
                     "comparable en el tiempo (si el alias del modelo se mueve, no hay forma de saberlo)")
    if str(run.get("model_id", "")).lower() in ("sonnet", "opus", "haiku"):
        errors.append(f"E-run model_id={run['model_id']!r} es un ALIAS móvil, no un identificador "
                      "de modelo — apunta a un modelo distinto según la fecha")
    if run.get("build_frozen") is False:
        warns.append("W-run build_frozen=false — el objetivo se movió durante la ronda; esta "
                     "medición no describe un objeto coherente (AUD-3)")
    elif "build_frozen" not in run:
        warns.append("W-run sin `build_frozen`: no consta que el build estuviera congelado (AUD-3)")

    # 5) anclas (AUD-10) — se mide la cobertura, no se bloquea
    finds = doc.get("findings") or []
    anch = [f for f in finds if isinstance(f, dict) and f.get("anchor_type") not in (None, "none")]
    stats["findings"] = len(finds)
    stats["anchor_coverage_pct"] = round(100.0 * len(anch) / len(finds), 1) if finds else None
    if finds and len(anch) < len(finds):
        warns.append(f"W-anchor {len(finds) - len(anch)}/{len(finds)} hallazgos sin ancla resoluble "
                     "— esos hay que emparejarlos a mano, y ahí se cuela el sesgo de quien compara")
    unk_sev = [f.get("id") for f in finds if isinstance(f, dict) and f.get("severity") == "unknown"]
    if unk_sev:
        warns.append(f"W-sev severidad `unknown` en: {', '.join(str(i) for i in unk_sev)}")

    return errors, warns, stats


# ---------------------------------------------------------------- normalización

def _slug(x):
    return str(x).strip().lower()


def normalize(doc, schema, agent="lidia-naive-tester", profile="herramienta-interna",
              question="¿la usaría sola, sin ayuda?"):
    """Migra un trend-delta legacy al esquema v1. Devuelve (doc_nuevo, transformaciones)."""
    dims = _dims(schema)
    t = []
    out = {"schema_version": 1, "measures": "producto-auditado", "agent": agent}

    # identidad de la corrida
    session, iteration = doc.get("session"), doc.get("iteration")
    if not session and isinstance(doc.get("version"), str) and "/" in doc["version"]:
        session, _, it = doc["version"].partition("/")
        iteration = int("".join(c for c in it if c.isdigit()) or 1)
        t.append(f"version «{doc['version']}» → session={session} + iteration={iteration}")
    out["session"] = session or "unknown"
    out["iteration"] = iteration or 1
    for k in ("persona", "date", "app", "pages_tested", "viewports"):
        if k in doc:
            out[k] = doc[k]
    out.setdefault("date", "1970-01-01")

    # perfil de rúbrica (AUD-8)
    out["profile"] = profile
    na = ["fotos_videos"] if profile == "herramienta-interna" else []
    out["na_dimensions"] = na
    if na:
        t.append(f"profile={profile} → fotos_videos marcada N/A (AUD-8)")

    # contexto de corrida (AUD-9): lo que no consta, consta como unknown
    out["run"] = {k: "unknown" for k in UNKNOWN_RUN}
    out["run"]["run_index"] = doc.get("run_index", 1)
    t.append("run.{model_id,calibration_version,target_sha,agent_sha} = «unknown» "
             "(esa corrida no lo registró; AUD-9 nace de aquí)")

    # veredicto (AUD-11)
    v_in = doc.get("verdict_categorico") or {}
    raw_label = v_in.get("label") or doc.get("final_verdict") or ""
    label = LABEL_MAP.get(_slug(raw_label))
    if label is None:
        label = "con_ayuda"
        t.append(f"veredicto {raw_label!r} no reconocido → label=con_ayuda (revísalo a mano)")
    else:
        t.append(f"veredicto {raw_label!r} → label={label}")
    out["verdict_categorico"] = {
        "question": question,
        "label": label,
        "passed": label == "si",
        "explanation": (v_in.get("explanation") or doc.get("final_verdict_detail")
                        or "(no registrada en la corrida original)"),
    }
    for src, dst in (("gate_triggered", "gate_triggered"), ("gate_reason", "gate_reason")):
        if src in doc:
            out["verdict_categorico"][dst] = doc[src]
    if "prev_label" in v_in:
        pl = LABEL_MAP.get(_slug(v_in["prev_label"]))
        if pl:
            out["verdict_categorico"]["prev_label"] = pl

    pages = doc.get("gate_categorico_dimensiones") or doc.get("categorical_verdict") or {}
    if isinstance(pages, dict) and pages:
        pv = {}
        for k, val in pages.items():
            pv[k] = PAGE_VERDICT_MAP.get(_slug(val), _slug(val))
        out["pages_verdict"] = pv
        t.append(f"pages_verdict normalizado ({len(pv)} entradas)")

    # rúbrica
    rub_in = doc.get("rubric") or {}
    rub = {}
    for k, val in rub_in.items():
        key = ALIAS_DIM.get(k, k)
        if key != k:
            t.append(f"dimensión «{k}» → «{key}»")
        entry = dict(val) if isinstance(val, dict) else {"score": val, "note": ""}
        entry.setdefault("note", "")
        if key in na:
            entry["na"] = True
        rub[key] = entry
    out["rubric"] = {d: rub[d] for d in dims if d in rub}

    # medias (AUD-7)
    sc = {d: float(out["rubric"][d]["score"]) for d in out["rubric"]
          if isinstance(out["rubric"][d].get("score"), (int, float))}
    raw = sum(sc.values()) / len(sc) if sc else 0.0
    declared = doc.get("score_raw", doc.get("score", doc.get("score_avg")))
    if isinstance(declared, (int, float)) and abs(float(declared) - raw) <= TOL:
        out["score_raw"] = float(declared)          # se respeta el número histórico publicado
    else:
        out["score_raw"] = round(raw, 2)
        t.append(f"score_raw recalculado: {declared} → {out['score_raw']} (media exacta {raw:.3f})")
    appl = {d: s for d, s in sc.items() if d not in na}
    out["score_profiled"] = round(sum(appl.values()) / len(appl), 2) if appl else 0.0
    out["score_role"] = "diagnostico"
    t.append(f"score_profiled = {out['score_profiled']} sobre {len(appl)} dimensiones aplicables "
             f"(score_raw {out['score_raw']} sobre {len(sc)})")

    # hallazgos: fusiona los tres formatos que llegaron a convivir
    finds, seen = [], set()
    for src in ("findings", "findings_status", "new_findings"):
        for f in (doc.get(src) or []):
            if not isinstance(f, dict) or f.get("id") in seen:
                continue
            seen.add(f.get("id"))
            st = STATUS_MAP.get(_slug(f.get("status", "")), "unknown" if src == "findings_status" else "open")
            finds.append({
                "id": f.get("id", "X-000"),
                "severity": f.get("severity", "unknown"),
                "module": f.get("module", "unknown"),
                "desc": f.get("desc") or f.get("evidence") or "(sin descripción)",
                "status": st,
                "anchor_type": f.get("anchor_type", "none"),
                "anchor_value": f.get("anchor_value", ""),
                "viewport": f.get("viewport", "all"),
                **({"versions_seen": f["versions_seen"]} if "versions_seen" in f else {}),
            })
    out["findings"] = finds
    if finds:
        t.append(f"{len(finds)} hallazgos fusionados desde findings/findings_status/new_findings; "
                 "anchor_type=none en todos (AUD-10: no se registraron anclas)")
    for k in ("positive_findings", "console_errors", "notes"):
        if k in doc:
            out[k] = doc[k]

    out["_normalized"] = {
        "by": "trend_lint.py --normalize",
        "from_schema": "legacy (pre-AUD-7)",
        "transforms": t,
        "warning": "Los valores «unknown» NO son datos perdidos que se puedan recuperar: son la "
                   "prueba de que esa corrida no registró su contexto. No los rellenes a posteriori.",
    }
    return out, t


# ---------------------------------------------------------------- CLI

def iter_files(targets):
    for tgt in targets:
        if os.path.isdir(tgt):
            for root, _, files in os.walk(tgt):
                for f in sorted(files):
                    if f == "trend-delta.json" or f.endswith(".trend-delta.json"):
                        yield os.path.join(root, f)
        else:
            yield tgt


def main():
    argv = sys.argv[1:]
    flags = {a for a in argv if a.startswith("--")}
    targets = [a for a in argv if not a.startswith("-")]
    if "-o" in argv:
        oi = argv.index("-o")
        out_path = argv[oi + 1]
        targets = [t for t in targets if t != out_path]
    else:
        out_path = None
    if not targets:
        sys.exit(__doc__)

    schema = load_schema()
    strict = "--strict" in flags

    if "--normalize" in flags:
        src = targets[0]
        with open(src, encoding="utf-8") as fh:
            doc = json.load(fh)
        profile = "landing" if "--landing" in flags else "herramienta-interna"
        new, transforms = normalize(doc, schema, profile=profile)
        blob = json.dumps(new, ensure_ascii=False, indent=2) + "\n"
        dest = src if "--in-place" in flags else out_path
        if dest:
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(blob)
            print(f"normalizado → {dest}")
            for x in transforms:
                print("  ·", x)
        else:
            sys.stdout.write(blob)
        return 0

    results, rc = [], 0
    for path in iter_files(targets):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except Exception as exc:  # json roto es un error del gate, no una excepción del script
            results.append({"file": path, "errors": [f"E-json ilegible: {exc}"],
                            "warnings": [], "stats": {}, "ok": False})
            rc = 1
            continue
        errors, warns, stats = validate(doc, schema, strict=strict)
        results.append({"file": path, "errors": errors, "warnings": warns,
                        "stats": stats, "ok": not errors})
        rc = rc or (1 if errors else 0)

    if "--json" in flags:
        print(json.dumps({"ok": rc == 0, "results": results}, ensure_ascii=False, indent=1))
    else:
        for r in results:
            print(f"\n── {r['file']}")
            for e in r["errors"]:
                print("  ERROR ", e)
            for w in r["warnings"]:
                print("  warn  ", w)
            if r["stats"]:
                print("  stats  " + " · ".join(f"{k}={v}" for k, v in r["stats"].items()))
            if not r["errors"]:
                print("  OK — comparable por máquina" + (" (con avisos)" if r["warnings"] else ""))
        n_err = sum(len(r["errors"]) for r in results)
        print(f"\n{len(results)} fichero(s) · {n_err} error(es) · "
              f"{sum(len(r['warnings']) for r in results)} aviso(s)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
