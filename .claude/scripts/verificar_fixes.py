#!/usr/bin/env python3
"""verificar_fixes.py — ¿el fix que se declaró aplicado existe de verdad?

EL HUECO QUE CIERRA, que es el mejor documentado del bucle de QA
(`rules/qa-loop.md` §2b, hueco nº2): Ignacio cazó **3 fixes que el fixer declaró
aplicados y no lo estaban**, y los cazó DE FORMA INCIDENTAL, mirando otra cosa.
Ocurrió en 1 de cada 3 rondas. No tenía dueño: existía como una línea en su memoria.

No hace falta un auditor nuevo para esto. Hace falta un script, porque la pregunta
es binaria y se puede comprobar:

  🔎 ¿el `git diff` entre la iteración anterior y esta TOCA el fichero citado?
  👁 ¿el predicado que el propio fixer declaró se cumple en el build congelado?

Las dos mitades son obligatorias (`rules/verdict-contract.md`): con una sola, el
veredicto es `partial`. Un diff que toca el fichero no demuestra que el efecto
ocurra, y un efecto correcto sin diff significa que ya estaba y el fix es humo.

POR QUÉ ES P0 Y DETIENE LA RONDA: si un fix declarado no está aplicado, estamos
midiendo un build cuyos cambios no son los que se dijo. Promediar eso es peor que
no medir — mismo razonamiento que el build congelado de §1b.

ENTRADA (la escribe quien arregla, y es el único coste real):
    .docs/feedback/qa-loop/<WAVE>/iter-<n>/fixes/fixes-declarados.json
    [{"finding_id": "F-012",
      "archivos": ["src/tokens.css"],
      "sha_anterior": "abc123", "sha_actual": "def456",
      "como_verificarlo": {"tipo": "computed", "url": "http://127.0.0.1:8000/",
                           "selector": ".stbtn", "prop": "color",
                           "espera_contraste_min": 4.5}}]

    `tipo` admite: computed (estilo computado) · existe (el selector está) ·
    ausente (el selector ya NO está) · texto (el selector contiene X) ·
    manual (no hay predicado: cae en la relectura de Ignacio, y se dice)

DESENLACES (rules/verification.md §«el instrumento que no puede medir debe ABORTAR»):
    0  medido, todos los fixes declarados están aplicados
    1  medido, hay al menos un `notdone` o `partial`   → P0, la ronda no se promedia
    2  NO SE PUDO MEDIR (falta el fichero de entrada, no hay navegador, no es un repo git)
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FEEDBACK = RAIZ / ".docs" / "feedback" / "qa-loop"


def abortar(motivo: str) -> None:
    print(f"⛔ NO SE PUDO MEDIR: {motivo}", file=sys.stderr)
    print("   No se imprime «todos aplicados»: no haber podido comprobar no es estar bien.",
          file=sys.stderr)
    sys.exit(2)


def diff_toca(sha_a: str, sha_b: str, archivos: list) -> tuple:
    """🔎 La mitad de código: ¿el diff entre los dos sha toca estos ficheros?"""
    try:
        r = subprocess.run(["git", "diff", "--name-only", f"{sha_a}..{sha_b}", "--"] + archivos,
                           cwd=RAIZ, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        abortar(f"git no pudo comparar {sha_a}..{sha_b}: {e}")
    if r.returncode != 0:
        return False, f"git diff falló: {r.stderr.strip()[:120]}"
    tocados = [x for x in r.stdout.split("\n") if x.strip()]
    if not tocados:
        return False, f"el diff {sha_a}..{sha_b} NO toca {', '.join(archivos)}"
    return True, f"{sha_a}..{sha_b} toca {', '.join(tocados)}"


def sonda(pred: dict) -> tuple:
    """👁 La mitad en vivo: evaluar el predicado declarado contra la página."""
    tipo = pred.get("tipo")
    if tipo == "manual":
        return None, "sin predicado automático — va a la relectura de Ignacio"
    url, sel = pred.get("url"), pred.get("selector")
    if not url or not sel:
        return None, "el predicado no trae url o selector: no se puede comprobar"
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        abortar("Playwright no está instalado y hay predicados que exigen navegador")

    # El binario del sistema: la caché de Playwright está vacía en esta máquina (medido 2026-09-18)
    chrome = next((p for p in ("/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
                               "/usr/bin/chromium-browser", "/usr/bin/chromium") if Path(p).exists()), None)
    if not chrome:
        abortar("no hay navegador: ni google-chrome ni chromium en el sistema")

    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
        pg = b.new_page()
        try:
            pg.goto(url, wait_until="load", timeout=20000)
        except Exception as e:
            b.close()
            return False, f"no se pudo abrir {url}: {str(e)[:100]}"
        try:
            if tipo == "existe":
                ok = pg.locator(sel).count() > 0
                det = f"{sel} {'está' if ok else 'NO está'} en la página"
            elif tipo == "ausente":
                ok = pg.locator(sel).count() == 0
                det = f"{sel} {'ya no está' if ok else 'SIGUE estando'}"
            elif tipo == "texto":
                txt = pg.locator(sel).first.inner_text() if pg.locator(sel).count() else ""
                ok = pred.get("espera", "") in txt
                det = f"{sel} dice «{txt[:60]}»"
            elif tipo == "computed":
                if pg.locator(sel).count() == 0:
                    ok, det = False, f"{sel} no existe: no se puede leer {pred.get('prop')}"
                else:
                    val = pg.eval_on_selector(
                        sel, "(el, p) => getComputedStyle(el)[p]", pred.get("prop"))
                    esperado = pred.get("espera")
                    ok = (val == esperado) if esperado is not None else True
                    det = f"{sel} · {pred.get('prop')} = {val}" + (f" (esperado {esperado})" if esperado else "")
            else:
                ok, det = None, f"tipo de predicado desconocido: {tipo}"
        finally:
            b.close()
    return ok, det


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    wave, it = sys.argv[1], sys.argv[2]
    carpeta = FEEDBACK / wave / f"iter-{it}" / "fixes"
    entrada = carpeta / "fixes-declarados.json"
    if not entrada.exists():
        abortar(f"no existe {entrada.relative_to(RAIZ)} — quien arregla tiene que declarar sus fixes")
    if not (RAIZ / ".git").exists():
        abortar("esto no es un repositorio git: no hay diff que comprobar")

    fixes = json.loads(entrada.read_text())
    resultados, hay_fallo = [], False

    for f in fixes:
        fid = f.get("finding_id", "?")
        ok_code, det_code = diff_toca(f.get("sha_anterior", "HEAD~1"),
                                      f.get("sha_actual", "HEAD"), f.get("archivos", []))
        ok_vivo, det_vivo = sonda(f.get("como_verificarlo", {"tipo": "manual"}))

        if ok_code and ok_vivo:
            verdict = "done"
        elif ok_vivo is None:
            verdict = "review"          # sin predicado: no es un fallo, es que no se puede automatizar
        elif ok_code or ok_vivo:
            verdict = "partial"
        else:
            verdict = "notdone"
        if verdict in ("notdone", "partial"):
            hay_fallo = True

        resultados.append({
            "finding_id": fid, "verdict": verdict,
            "evidencia_codigo": det_code, "evidencia_viva": det_vivo,
            "nota": (f"🔎 Código: {det_code}\n👁 En vivo: {det_vivo}\n"
                     f"💥 Impact: {'—' if verdict == 'done' else 'se estaría midiendo un build cuyos cambios no son los declarados'}"),
        })

    salida = {"estado_instrumento": "medido", "wave": wave, "iter": it,
              "total": len(fixes),
              "por_verdict": {v: sum(1 for r in resultados if r["verdict"] == v)
                              for v in ("done", "partial", "notdone", "review")},
              "fixes": resultados}

    if "--json" in sys.argv:
        print(json.dumps(salida, ensure_ascii=False, indent=1))
    else:
        print(f"verificar_fixes · {wave} iter-{it} · {len(fixes)} fix(es) declarados")
        for r in resultados:
            icono = {"done": "✓", "partial": "◐", "notdone": "✗", "review": "?"}[r["verdict"]]
            print(f"  {icono} {r['finding_id']:8s} {r['verdict']}")
            print(f"      🔎 {r['evidencia_codigo']}")
            print(f"      👁 {r['evidencia_viva']}")
        if hay_fallo:
            print("\n⛔ Hay fixes declarados que NO están aplicados → P0. La ronda NO se promedia:")
            print("   se estaría midiendo un build cuyos cambios no son los que se dijo.")

    (carpeta / "fixes-verificados.json").write_text(
        json.dumps(salida, ensure_ascii=False, indent=1) + "\n")
    return 1 if hay_fallo else 0


if __name__ == "__main__":
    sys.exit(main())
