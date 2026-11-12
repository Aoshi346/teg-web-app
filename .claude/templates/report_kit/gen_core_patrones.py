#!/usr/bin/env python3
"""core-patrones.html — el estado del patrón de código del REPO, como capa permanente.

POR QUE EN EL CORE Y NO SOLO EN EL PLAN. `patron.html` cuenta que se incumple en ESTE
plan y se congela con el. Pero "como se escribe el codigo en esta casa" no muere cuando
un plan se cierra: es de lo mas permanente que hay. Por eso la misma plantilla se
publica dos veces con dos datasets distintos (regla 5a de rules/report-kit.md).

Reutiliza `gen_patron_dataset.py` y `patron.template.html` -- no hay segunda plantilla
que mantener, que es como dos vistas del mismo dato acaban divergiendo.

USO (lo llama build.py con la firma de los generadores del core):
    python3 gen_core_patrones.py <plan-dir> --out <.docs/core>

OJO si lo corres suelto: escribe la pagina SIN topnav, igual que los demas
generadores del core. Quien la pinta es `render_nav.py --scope core`, y build.py
lo llama despues. Corriendo esto a mano hay que repetir ese paso, o la pagina
queda sin menu y no se puede salir de ella.
"""
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build import inject                      # noqa: E402  (misma inyección que el resto del kit)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    plan, out = Path(a.plan).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    repo = subprocess.run(["git", "-C", str(plan), "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip()
    if not repo:
        print("core-patrones: no estamos en un repo git", file=sys.stderr)
        return 1

    # dataset del REPO entero, en un temporal REAL: el del plan describe otra cosa y no se pisa,
    # y el Core no es sitio donde dejar ficheros de trabajo.
    with tempfile.TemporaryDirectory(prefix="patron-core-") as td:
        r = subprocess.run([sys.executable, str(HERE / "gen_patron_dataset.py"), td,
                            "--repo", repo], capture_output=True, text=True)
        ds = Path(td) / "pattern-dataset.json"
        if r.returncode or not ds.exists():
            print(f"core-patrones: no se pudo medir el patron — "
                  f"{(r.stderr or r.stdout).strip()[-200:]}", file=sys.stderr)
            return 1
        data = json.loads(ds.read_text(encoding="utf-8"))
    data["meta"]["permanente"] = True
    meta = {"project": os.path.basename(repo), "plan_id": "core",
            "title": "Patrón de código", "round": None, "generated": data["meta"].get("date")}
    inject(str(HERE / "patron.template.html"), data, str(out / "core-patrones.html"), meta=meta)
    m = data["meta"]
    print(f"OK {out / 'core-patrones.html'} — {m['docs_total']} documentos · "
          f"{m['reglas_total']} reglas · {m['bloquean']} hallazgos que bloquean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
