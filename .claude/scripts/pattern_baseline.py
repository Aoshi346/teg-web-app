#!/usr/bin/env python3
"""pattern_baseline.py — el ratchet (trinquete) de la deuda de patrones.

Congela las infracciones que YA existen en un proyecto para que el gate de patrones no bloquee
contra código antiguo, y deja pasar el aviso SOLO en lo que se escribe a partir de ahora.

    # 1) medir el proyecto entero y congelar lo que hay hoy (una vez, al adoptar)
    python3 .claude/patterns/stack/pattern_check_backend.py --all --json > /tmp/f.json
    python3 .claude/scripts/pattern_baseline.py freeze --from /tmp/f.json

    # 2) el gate del día a día: solo lo que toca este cambio
    python3 .claude/patterns/stack/pattern_check_backend.py --json \\
      | python3 .claude/scripts/pattern_baseline.py check --from - --diff-scope

    # 3) cuánta deuda queda y qué ya se puede retirar
    python3 .claude/scripts/pattern_baseline.py status --from /tmp/f.json
    python3 .claude/scripts/pattern_baseline.py retire --from /tmp/f.json --apply

Lee la salida `--json` de cualquier comprobador de la casa. Los dos que existen hablan dialectos
distintos (backend: `rule`/`path` · frontend: `id`/`file`); aquí se normalizan los dos.

Formato del baseline: `.claude/patterns/baseline/<patron_id>.json` — el mismo que ya usaba
`rule-header.json`, sin schema nuevo (regla 1 de patterns/README.md).

Procedimiento completo y criterio de promoción: `.claude/rules/refactor-progresivo.md`.
Solo stdlib.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

BASELINE_DIR = ".claude/patterns/baseline"
BLOCKING = {"activo"}
# Regla de inversión (patterns/README.md §Reglas duras 2): si una regla marcaría más sitios que
# esto, el problema es la regla, no el código. Congelarla sería usar el baseline para blanquearla.
INVERSION_MAX_FILES = 30
NOTA = ("Deuda aceptada (ratchet). Solo un humano amplía esta lista. Migran por boy-scout: "
        "el fichero sale del baseline cuando alguien que ya lo estaba tocando lo deja limpio.")


# ─────────────────────────────────────────── utilidades

def repo_root() -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        return Path(out)
    except Exception:
        return Path.cwd()


def shortest(p: Path, root: Path) -> str:
    """Ruta relativa a la raíz si cuelga de ella; absoluta si no (--dir puede apuntar fuera)."""
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return str(p)


def norm(p: str, root: Path) -> str:
    """Ruta relativa a la raíz del repo, en POSIX. Es la clave del baseline."""
    q = Path(p)
    if not q.is_absolute():
        q = (root / q)
    try:
        return q.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path(p).as_posix()


class Finding:
    __slots__ = ("rule", "path", "line", "estado", "msg")

    def __init__(self, rule: str, path: str, line: int, estado: str, msg: str):
        self.rule, self.path, self.line, self.estado, self.msg = rule, path, line, estado, msg

    @property
    def blocks(self) -> bool:
        return self.estado in BLOCKING


def load_findings(src: str, root: Path) -> list[Finding]:
    """Lee la salida --json de un comprobador. Tolera los dos dialectos de la casa."""
    raw = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"✗ la entrada no es JSON válido ({e}). ¿Olvidaste el flag --json del comprobador?")
    if isinstance(data, dict):                       # por si algún comprobador envuelve la lista
        data = data.get("findings", data.get("hallazgos", []))
    out = []
    for d in data:
        rule = d.get("rule") or d.get("id") or d.get("patron_id")
        path = d.get("path") or d.get("file") or d.get("fichero")
        if not rule or not path:
            sys.exit(f"✗ finding sin regla o sin fichero: {d!r}")
        out.append(Finding(rule, norm(path, root), int(d.get("line") or 0),
                           d.get("estado") or "debil", d.get("msg") or ""))
    return out


def touched_lines(root: Path, base: str) -> dict[str, set[int]]:
    """Líneas AÑADIDAS o MODIFICADAS por el cambio actual, por fichero.

    Es lo que hace 'diff-scoped' posible: juzgar solo el código nuevo. Un fichero sin seguimiento
    (untracked) cuenta entero — todas sus líneas son nuevas.
    """
    touched: dict[str, set[int]] = {}
    try:
        diff = subprocess.run(["git", "diff", "-U0", base], cwd=root,
                              capture_output=True, text=True).stdout
        diff += subprocess.run(["git", "diff", "-U0", "--cached", base], cwd=root,
                               capture_output=True, text=True).stdout
    except Exception:
        diff = ""
    cur = None
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            tgt = ln[4:].strip()
            cur = None if tgt == "/dev/null" else norm(tgt[2:] if tgt.startswith("b/") else tgt, root)
        elif ln.startswith("@@") and cur:
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", ln)
            if m:
                start, count = int(m.group(1)), int(m.group(2) or 1)
                touched.setdefault(cur, set()).update(range(start, start + max(count, 1)))
    try:
        untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root,
                                   capture_output=True, text=True).stdout.split()
    except Exception:
        untracked = []
    for u in untracked:
        f = root / u
        if f.is_file():
            try:
                n = len(f.read_text(encoding="utf-8", errors="ignore").splitlines()) or 1
            except OSError:
                continue
            touched.setdefault(norm(u, root), set()).update(range(1, n + 2))
    return touched


# ─────────────────────────────────────────── baseline en disco

def bl_index(root: Path, d: str) -> dict[str, tuple[Path, dict]]:
    """patron_id → (fichero, contenido), leyendo el `patron_id` DE DENTRO de cada JSON.

    La convención es `<patron_id>.json`, pero el baseline histórico del repo se llama
    `rule-header.json` y declara `patron_id: rule-header-cuando-aplicar`. Indexar por el nombre
    del fichero lo dejaría invisible y crearía un duplicado al escribir; por eso manda el contenido.
    """
    idx: dict[str, tuple[Path, dict]] = {}
    dirp = root / d
    if not dirp.is_dir():
        return idx
    for f in sorted(dirp.glob("*.json")):
        try:
            bl = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"✗ baseline corrupto: {shortest(f, root)} ({e})")
        pid = bl.get("patron_id", f.stem)
        if pid in idx:
            sys.exit(f"✗ dos baselines declaran patron_id '{pid}': "
                     f"{shortest(idx[pid][0], root)} y {shortest(f, root)} — deja uno.")
        idx[pid] = (f, bl)
    return idx


def bl_load(root: Path, rule: str, d: str) -> dict | None:
    hit = bl_index(root, d).get(rule)
    return hit[1] if hit else None


def bl_violations(bl: dict | None) -> set[str]:
    """`violations` admite str (la forma canónica) u objeto {file, nota} — ambas se leen."""
    if not bl:
        return set()
    out = set()
    for v in bl.get("violations", []):
        out.add(v if isinstance(v, str) else v.get("file", ""))
    return {v for v in out if v}


def bl_save(root: Path, rule: str, d: str, payload: dict, path: Path | None = None) -> Path:
    """Escribe el baseline. Si ya existía, se reescribe SU fichero — nunca uno nuevo al lado."""
    f = path or (root / d / f"{rule}.json")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return f


def all_baselines(root: Path, d: str) -> list[tuple[str, dict, Path]]:
    return [(pid, bl, f) for pid, (f, bl) in sorted(bl_index(root, d).items())]


def group(findings: list[Finding]) -> dict[str, list[Finding]]:
    g: dict[str, list[Finding]] = {}
    for f in findings:
        g.setdefault(f.rule, []).append(f)
    return g


# ─────────────────────────────────────────── comandos

def cmd_freeze(a, root: Path) -> int:
    findings = load_findings(a.src, root)
    if a.only:
        keep = {r.strip() for r in a.only.split(",") if r.strip()}
        findings = [f for f in findings if f.rule in keep]
    if not findings:
        print("freeze: 0 hallazgos en la entrada — nada que congelar.")
        return 0

    idx = bl_index(root, a.dir)
    rc, wrote, refused = 0, 0, 0
    for rule, fs in sorted(group(findings).items()):
        files = sorted({f.path for f in fs})
        prev_path, prev = idx.get(rule, (None, None))
        if prev and not a.replace:
            print(f"⚠ {rule}: ya existe {shortest(prev_path, root)} "
                  f"con {len(bl_violations(prev))} entrada(s).")
            print("   El baseline NO se re-congela solo: crecería en silencio y perdería el historial.")
            print(f"   → para reducirlo: pattern_baseline.py retire --from <json> --apply")
            print(f"   → para rehacerlo a conciencia: añade --replace")
            refused += 1
            rc = max(rc, 2)
            continue
        if len(files) > a.max_files and not a.force:
            print(f"✗ {rule}: congelaría {len(files)} ficheros (> {a.max_files}).")
            print("   REGLA DE INVERSIÓN (patterns/README.md §2): si una regla marca tantos sitios,")
            print("   lo que está mal es la regla, no el código. Congelarla es blanquearla.")
            print("   → revisa el enunciado, acótalo, o déjala en 'sombra' y no la promuevas.")
            print(f"   → si aun así es correcta y lo asumes: añade --force (queda anotado en el fichero)")
            refused += 1
            rc = max(rc, 2)
            continue
        payload = {
            "patron_id": rule,
            "frozen_at": date.today().isoformat(),
            "frozen_by": f"pattern_baseline.py freeze --from {a.src}",
            "nota": NOTA,
            "migradas": (prev or {}).get("migradas", []),
            "violations": files,
        }
        if len(files) > a.max_files:
            payload["aviso_inversion"] = (
                f"Congelado con --force pese a superar el umbral de inversión ({len(files)} > "
                f"{a.max_files}). Revisar el enunciado de la regla antes de promoverla a 'activo'.")
        f = bl_save(root, rule, a.dir, payload, prev_path)
        print(f"✓ {rule}: {len(files)} fichero(s) congelados → {shortest(f, root)}")
        wrote += 1
    print(f"\nfreeze: {wrote} baseline(s) escritos, {refused} rechazado(s).")
    return rc


def cmd_check(a, root: Path) -> int:
    findings = load_findings(a.src, root)
    touched = touched_lines(root, a.base) if a.diff_scope else {}
    cache: dict[str, set[str]] = {}

    def congelado(f: Finding) -> bool:
        if f.rule not in cache:
            cache[f.rule] = bl_violations(bl_load(root, f.rule, a.dir))
        return f.path in cache[f.rule]

    nuevas: list[tuple[Finding, bool]] = []
    silenciadas: list[Finding] = []
    for f in findings:
        frozen = congelado(f)
        if a.diff_scope:
            # Solo se juzga lo que este cambio ha tocado. El baseline NO silencia aquí:
            # si has tocado la línea, es tuya (boy-scout). Una regla sin línea (line=0) juzga
            # el fichero entero, así que basta con que el fichero esté en el diff.
            lineas = touched.get(f.path, set())
            if (f.line and f.line in lineas) or (not f.line and f.path in touched):
                nuevas.append((f, frozen))
            else:
                silenciadas.append(f)
        elif frozen:
            silenciadas.append(f)
        else:
            nuevas.append((f, False))

    if a.json:
        print(json.dumps({
            "modo": "diff-scope" if a.diff_scope else "baseline",
            "nuevas": [dict(rule=f.rule, path=f.path, line=f.line, estado=f.estado,
                            msg=f.msg, en_baseline=fr) for f, fr in nuevas],
            "silenciadas": len(silenciadas),
        }, indent=2, ensure_ascii=False))
        return 1 if any(f.blocks for f, _ in nuevas) else 0

    for f, frozen in sorted(nuevas, key=lambda t: (t[0].path, t[0].line)):
        mark = "✗" if f.blocks else "⚠"
        tag = f.estado.upper() if f.blocks else f.estado
        deuda = "  [fichero con deuda congelada — la línea es nueva]" if frozen else ""
        print(f"{mark} [{tag}] {f.path}:{f.line} — {f.msg} ({f.rule}){deuda}")

    bloqueantes = [f for f, _ in nuevas if f.blocks]
    print()
    print(f"check ({'diff-scope' if a.diff_scope else 'baseline'}): "
          f"{len(nuevas)} nueva(s) · {len(silenciadas)} silenciada(s) por "
          f"{'estar fuera del cambio' if a.diff_scope else 'baseline'}")
    if bloqueantes:
        print(f"✗ {len(bloqueantes)} violación(es) de patrones ACTIVOS en código nuevo.")
        return 1
    print("✓ sin violaciones nuevas de patrones activos.")
    return 0


def cmd_status(a, root: Path) -> int:
    baselines = all_baselines(root, a.dir)
    if not baselines:
        print(f"status: no hay baselines en {a.dir}/")
        return 0
    actuales = group(load_findings(a.src, root)) if a.src else None

    print(f"{'patrón'.ljust(34)} {'congelado'.ljust(11)} {'deuda'.rjust(6)} "
          f"{'migradas'.rjust(9)} {'retirables'.rjust(11)}")
    print("─" * 76)
    total_deuda = total_retirable = 0
    detalle: list[tuple[str, list[str]]] = []
    for rule, bl, _ in baselines:
        viol = bl_violations(bl)
        retirables: list[str] = []
        if actuales is not None:
            aun = {f.path for f in actuales.get(rule, [])}
            retirables = sorted(viol - aun)
        total_deuda += len(viol)
        total_retirable += len(retirables)
        print(f"{rule[:34].ljust(34)} {str(bl.get('frozen_at', '?')).ljust(11)} "
              f"{str(len(viol)).rjust(6)} {str(len(bl.get('migradas', []))).rjust(9)} "
              f"{(str(len(retirables)) if actuales is not None else '—').rjust(11)}")
        if retirables:
            detalle.append((rule, retirables))
    print("─" * 76)
    print(f"{'TOTAL'.ljust(34)} {''.ljust(11)} {str(total_deuda).rjust(6)} "
          f"{''.rjust(9)} {(str(total_retirable) if actuales is not None else '—').rjust(11)}")

    for rule, files in detalle:
        print(f"\n{rule} — ya no infringen ({len(files)}); retirables del baseline:")
        for f in files[:20]:
            print(f"  · {f}")
        if len(files) > 20:
            print(f"  … y {len(files) - 20} más")
    if total_retirable:
        print(f"\n→ pattern_baseline.py retire --from {a.src} --apply")
    if actuales is None:
        print("\n(sin --from solo se lista la deuda; para saber qué es retirable, pasa la medición actual)")
    return 0


def cmd_retire(a, root: Path) -> int:
    actuales = group(load_findings(a.src, root))
    cambios = 0
    for rule, bl, path in all_baselines(root, a.dir):
        viol = bl_violations(bl)
        aun = {f.path for f in actuales.get(rule, [])}
        retirables = sorted(viol - aun)
        if not retirables:
            continue
        print(f"{rule}: retirar {len(retirables)} de {len(viol)}  ({shortest(path, root)})")
        for f in retirables:
            print(f"  − {f}")
        if a.apply:
            bl["violations"] = sorted(viol - set(retirables))
            bl.setdefault("migradas", []).extend(
                {"file": f, "fecha": date.today().isoformat(), "por": a.reason} for f in retirables)
            bl_save(root, rule, a.dir, bl, path)
        cambios += len(retirables)
    if not cambios:
        print("retire: nada que retirar — la deuda congelada sigue infringiendo.")
        return 0
    print(f"\nretire: {cambios} entrada(s) {'RETIRADAS' if a.apply else 'retirables (simulacro)'}.")
    if not a.apply:
        print("→ añade --apply para escribirlo.")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=BASELINE_DIR, help=f"directorio de baselines (default {BASELINE_DIR})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("freeze", help="congela la deuda actual como baseline")
    f.add_argument("--from", dest="src", required=True, help="JSON del comprobador ('-' = stdin)")
    f.add_argument("--only", default="", help="solo estas reglas (coma)")
    f.add_argument("--max-files", type=int, default=INVERSION_MAX_FILES,
                   help=f"umbral de la regla de inversión (default {INVERSION_MAX_FILES})")
    f.add_argument("--force", action="store_true", help="congelar aunque supere el umbral")
    f.add_argument("--replace", action="store_true", help="rehacer un baseline existente")
    f.set_defaults(fn=cmd_freeze)

    c = sub.add_parser("check", help="findings menos baseline = lo nuevo")
    c.add_argument("--from", dest="src", required=True, help="JSON del comprobador ('-' = stdin)")
    c.add_argument("--diff-scope", action="store_true",
                   help="juzgar SOLO las líneas que este cambio ha tocado")
    c.add_argument("--base", default="HEAD", help="referencia git para el diff (default HEAD)")
    c.add_argument("--json", action="store_true", help="salida JSON")
    c.set_defaults(fn=cmd_check)

    s = sub.add_parser("status", help="cuánta deuda queda y qué ya es retirable")
    s.add_argument("--from", dest="src", default="", help="medición actual (opcional)")
    s.set_defaults(fn=cmd_status)

    r = sub.add_parser("retire", help="saca del baseline lo que ya no infringe")
    r.add_argument("--from", dest="src", required=True, help="medición actual")
    r.add_argument("--apply", action="store_true", help="escribir (por defecto, simulacro)")
    r.add_argument("--reason", default="ya no infringe — retirado por pattern_baseline.py retire")
    r.set_defaults(fn=cmd_retire)

    a = ap.parse_args(argv)
    return a.fn(a, repo_root())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
