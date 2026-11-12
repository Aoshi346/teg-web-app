#!/usr/bin/env python3
"""task_progress.py — progreso de tasks.md DERIVADO por aritmética, no declarado (SPEC-1).

Sustituye la disciplina manual de speckit-workflow.md §SpecKit Progress Tracking ("marca en vivo") por conteo real:
una regla que pide disciplina a un LLM en sesión larga es una regla que se incumple — esto no.

Cuenta checkboxes en uno o más tasks.md (formato del template: ` `=backlog · `>`=doing ·
`x`=done · `!`=blocked) y puede actuar de GATE: con --gate, exit 1 si quedan pendientes
(backlog+doing) — para que "cerrar wave" con [ ] abiertos sea imposible, no desaconsejado.

Lección robada del código de OpenSpec (task-progress.ts): la regex NO se ancla en columna 0 —
las subtareas indentadas contaban como invisibles y un change incompleto se archivaba como
"✓ Complete" sin aviso.

Uso:
  python3 task_progress.py <tasks.md|dir> [...]      # resumen humano (busca tasks.md en dirs)
  python3 task_progress.py <...> --gate              # exit 1 si hay backlog/doing (blocked avisa, no bloquea)
  python3 task_progress.py <...> --gate --wave "Wave 3"   # gate solo sobre la sección cuyo H2 contiene el texto
  python3 task_progress.py <...> --json
"""
import json
import os
import re
import sys

BOX = re.compile(r"^\s*[-*]\s*\[([ xX>!])\]\s*(.+)")  # sin anclar a col 0 (subtareas indentadas)
H2 = re.compile(r"^##+\s+(.+)")
LABEL = {" ": "backlog", ">": "doing", "x": "done", "!": "blocked"}
# Cualquier OTRA marca de una sola letra entre corchetes. Antes no casaba con BOX y la línea se
# volvía invisible: en aquila-erp, tres `[/]` y dos `[~]` (tareas a medias) desaparecían del
# recuento, ERP-2 decía «doing 0» con tres en curso y un gate de wave podía cerrar con ellas
# abiertas (2026-09-28). Un instrumento que no sabe leer una línea ABORTA, no la salta
# (`rules/verification.md` §«El instrumento que no puede medir»).
OTRA = re.compile(r"^\s*[-*]\s*\[([^\]])\]\s*(.+)")


class MarcaDesconocida(Exception):
    pass


def scan(path: str, wave: str | None):
    counts = {"backlog": 0, "doing": 0, "done": 0, "blocked": 0}
    pending_lines = []
    in_wave = wave is None
    section = ""
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        h = H2.match(line)
        if h:
            section = h.group(1).strip()
            # Casa por PREFIJO hasta un separador, no por subcadena: con `in`, el filtro
            # «Wave 1» arrastraba «Wave 10» y «Wave 4» arrastraba «Wave 4b», así que el gate
            # de una wave no se podía satisfacer mientras la otra siguiera abierta. Un gate
            # imposible no protege: quema turnos y se acaba ignorando (verification.md §nivel 3).
            in_wave = wave is None or bool(
                re.match(re.escape(wave.strip()) + r"(?:\s|$|[—–\-:.])", section.strip(), re.I))
            continue
        m = BOX.match(line)
        if not m:
            o = OTRA.match(line)
            if o:
                raise MarcaDesconocida(
                    f"{path}:{n}: marca «[{o.group(1)}]» desconocida — usa [ ] [>] [x] [!] "
                    f"(speckit-workflow.md §SpecKit Progress Tracking). Línea: {o.group(2).strip()[:70]}")
            continue
        if not in_wave:
            continue
        st = LABEL[m.group(1).lower() if m.group(1) in "xX" else m.group(1)]
        counts[st] += 1
        if st in ("backlog", "doing"):
            pending_lines.append(f"{os.path.basename(path)}:{n} [{m.group(1)}] {m.group(2).strip()[:90]}")
    return counts, pending_lines


def main():
    args = sys.argv[1:]
    gate = "--gate" in args
    as_json = "--json" in args
    wave = None
    if "--wave" in args:
        wave = args[args.index("--wave") + 1]
    paths = []
    skip = set()
    for i, a in enumerate(args):
        if a == "--wave":
            skip.add(i + 1)
        if a.startswith("--") or i in skip:
            continue
        if os.path.isdir(a):
            for dirpath, dirnames, filenames in os.walk(a):
                dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
                if "tasks.md" in filenames:
                    paths.append(os.path.join(dirpath, "tasks.md"))
        elif os.path.isfile(a):
            paths.append(a)
    if not paths:
        sys.exit(__doc__)

    total = {"backlog": 0, "doing": 0, "done": 0, "blocked": 0}
    pending = []
    for p in sorted(set(paths)):
        try:
            c, pl = scan(p, wave)
        except MarcaDesconocida as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(2)
        for k in total:
            total[k] += c[k]
        pending += pl

    n = sum(total.values())
    done_pct = round(100 * total["done"] / n) if n else 0
    if as_json:
        print(json.dumps({"files": len(set(paths)), "wave": wave, "total": n, "pct_done": done_pct,
                          **total, "pending": pending}, ensure_ascii=False, indent=1))
    else:
        scope = f" · filtro wave: «{wave}»" if wave else ""
        print(f"{total['done']}/{n} done ({done_pct}%) · doing {total['doing']} · backlog {total['backlog']} · blocked {total['blocked']}{scope}")
        for line in pending[:30]:
            print("  ", line)
        if len(pending) > 30:
            print(f"   … y {len(pending)-30} más")

    if gate:
        if total["backlog"] or total["doing"]:
            print(f"GATE: NO CERRAR — {total['backlog']+total['doing']} tareas sin terminar", file=sys.stderr)
            sys.exit(1)
        if total["blocked"]:
            print(f"GATE: cerrable con {total['blocked']} bloqueadas — documenta el porqué de cada [!]", file=sys.stderr)
        print("GATE: OK")


if __name__ == "__main__":
    main()
