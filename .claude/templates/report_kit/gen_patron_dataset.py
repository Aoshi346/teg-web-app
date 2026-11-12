#!/usr/bin/env python3
"""pattern-dataset.json — el estado del patrón de código de un repo, como hechos.

POR QUE UN FICHERO DE HECHOS Y NO CAMPOS EN EL ITEM. El estado del patron sobrevive
a los planes: una regla que hoy esta en sombra seguira ahi cuando este plan se cierre.
Meterlo como campos del item lo ataria a un plan concreto. Mismo precedente que
`graph-dataset.json`: fichero propio, generador determinista y sello de frescura.

QUE JUNTA. Tres fuentes que ya existian por separado y nadie cruzaba:
  1. catalog.yaml           -> que reglas hay, su estado, su dominancia MEDIDA
  2. pattern_check_*.py     -> que incumple HOY, con fichero y linea (--json)
  3. baseline/<id>.json     -> la deuda congelada (el trinquete)

LIMITE DECLARADO: no mide calidad de codigo. Mide conformidad con lo que ESTA CASA
decidio, que es otra cosa. Una regla en `sombra` no bloquea nada, y eso se pinta.

USO:
    python3 gen_patron_dataset.py <plan-dir> [--repo <ruta>]
"""
import argparse, json, os, re, subprocess, sys, datetime
from pathlib import Path

AQUI = Path(__file__).resolve()
RAIZ = AQUI.parents[3]                       # .claude/templates/report_kit/x.py -> repo
CHECKERS = {"backend": "pattern_check_backend.py",
            "frontend": "pattern_check_frontend.py",
            "agente": "pattern_check_agente.py"}
ESTADO_ORDEN = {"activo": 0, "debil": 1, "sombra": 2, "retirado": 3}


def lee_catalogo(repo: Path) -> list:
    """catalog.yaml sin dependencias: el formato es estable y plano a proposito."""
    f = repo / ".claude" / "patterns" / "catalog.yaml"
    if not f.exists():
        return []
    reglas, cur = [], None
    for ln in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-\s+id:\s*(\S+)", ln)
        if m:
            cur = {"id": m.group(1), "enunciado": "", "eje": "", "mecanismo": "",
                   "ambito": "", "dominancia": "", "estado": "", "baseline": None, "doc": ""}
            reglas.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"\s+(enunciado|eje|mecanismo|ambito|dominancia|estado|doc|baseline):\s*(.*)", ln)
        if m:
            k, v = m.group(1), m.group(2).strip().strip('"').split("  #")[0].strip()
            cur[k] = None if v in ("null", "") and k == "baseline" else v
    return reglas


def corre(repo: Path, script: str) -> list:
    """Un comprobador en modo --json. Si peta, se dice y se sigue: un dataset a medias
    con la ausencia declarada vale mas que ninguno."""
    p = repo / ".claude" / "patterns" / "stack" / script
    if not p.exists():
        return [{"_error": f"no existe {script}"}]
    try:
        out = subprocess.run([sys.executable, str(p), "--all", "--json"], cwd=repo,
                             capture_output=True, text=True, timeout=600)
        return json.loads(out.stdout) if out.stdout.strip() else []
    except subprocess.TimeoutExpired:
        return [{"_error": f"{script} tardo mas de 600s"}]
    except Exception as e:
        return [{"_error": f"{script}: {e}"}]


def lee_baselines(repo: Path) -> dict:
    d = repo / ".claude" / "patterns" / "baseline"
    out = {}
    if not d.is_dir():
        return out
    for f in d.glob("*.json"):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
            out[j.get("patron_id", f.stem)] = {
                "congeladas": len(j.get("violations", [])),
                "migradas": len(j.get("migradas", [])),
                "frozen_at": j.get("frozen_at", ""),
                "nota": j.get("nota", "")}
        except Exception:
            pass
    return out


def docs_de_stack(repo: Path) -> list:
    """Los documentos de patron y si tienen regla comprobable. El numero que importa:
    cuantos documentos hay frente a cuantas reglas de verdad bloquean algo."""
    d = repo / ".claude" / "patterns" / "stack"
    out = []
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.md")):
        if f.name == "README.md":
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^#\s+(.+)$", txt, re.M)
        cuando = re.search(r"\*\*Cu[aá]ndo aplica.*?:\*\*\s*(.+)", txt)
        out.append({"file": f.name,
                    "titulo": (m.group(1).strip() if m else f.stem),
                    "cuando": (cuando.group(1).strip()[:190] if cuando else ""),
                    "familia": ("agentes" if f.name.startswith("agente-")
                                else "frontend" if f.name.startswith("frontend-") or f.name in
                                ("estilos.md", "componentes.md", "formularios.md", "estado.md", "accesibilidad.md")
                                else "backend"),
                    "lineas": txt.count("\n") + 1})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--repo", default=str(RAIZ))
    a = ap.parse_args()
    repo, plan = Path(a.repo).resolve(), Path(a.plan).resolve()
    plan.mkdir(parents=True, exist_ok=True)

    reglas = lee_catalogo(repo)
    base = lee_baselines(repo)
    hall, errores = {}, []
    for fam, script in CHECKERS.items():
        res = corre(repo, script)
        for h in res:
            if "_error" in h:
                errores.append(h["_error"]); continue
            h["familia"] = fam
            hall.setdefault(h.get("rule", "?"), []).append(h)

    for r in reglas:
        rid = r["id"]
        r["hallazgos"] = len(hall.get(rid, []))
        r["ejemplos"] = [{"path": h.get("path", ""), "line": h.get("line", 0),
                          "msg": (h.get("msg", "") or "")[:280]} for h in hall.get(rid, [])[:6]]
        r["baseline_info"] = base.get(rid)
        r["familia"] = ("agentes" if rid.startswith("ag-")
                        else "frontend" if rid.startswith("fe-") else "backend")
    reglas.sort(key=lambda r: (ESTADO_ORDEN.get(r["estado"], 9), -r["hallazgos"]))

    huerfanas = sorted(set(hall) - {r["id"] for r in reglas})
    docs = docs_de_stack(repo)
    sha = ""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo,
                             capture_output=True, text=True).stdout.strip()
    except Exception:
        pass

    data = {
        "meta": {
            "source": "gen_patron_dataset.py — catalog.yaml + pattern_check_*.py --json + baseline/",
            "repo": repo.name, "sha": sha,
            "date": datetime.date.today().isoformat(),
            "errores": errores,
            "docs_total": len(docs),
            "reglas_total": len(reglas),
            "por_estado": {e: sum(1 for r in reglas if r["estado"] == e)
                           for e in ("activo", "debil", "sombra", "retirado")},
            "hallazgos_total": sum(len(v) for v in hall.values()),
            "bloquean": sum(len(hall.get(r["id"], [])) for r in reglas if r["estado"] == "activo"),
        },
        "reglas": reglas, "docs": docs, "huerfanas": huerfanas,
    }
    out = plan / "pattern-dataset.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    m = data["meta"]
    print(f"OK {out}")
    print(f"   {m['docs_total']} documentos · {m['reglas_total']} reglas "
          f"({m['por_estado']['activo']} activo · {m['por_estado']['debil']} débil · "
          f"{m['por_estado']['sombra']} sombra) · {m['hallazgos_total']} hallazgos "
          f"({m['bloquean']} bloquean)")
    for e in errores:
        print(f"   ⚠ {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
