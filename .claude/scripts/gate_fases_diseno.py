#!/usr/bin/env python3
"""gate_fases_diseno.py — no se escribe el backend de una UI con el mockup sin cerrar.

POR QUÉ EXISTE (sub-ola 3.67, UX-6). `CLAUDE.md` y `rules/motores-de-diseno.md` Parte F fijan el
orden marca → low-fi → high-fi → mockup con datos simulados → backend, y nada lo hacía cumplir. En
fitapp el TL invirtió el orden pese a tres normas escritas (proyectos-elevaiti.md, P-12). Una norma
que se incumple no se reescribe más fuerte: baja de capa (`rules/layer-decision.md`).

QUÉ MIRA. Un fichero que define el esquema del backend —`models.py`, `models/<x>.py` o una migración
`migrations/NNNN_*.py`— en un proyecto CON interfaz (hay `.docs/core/design-system.md` o un
`package.json` con React, Vue, Svelte o Next). Si el mockup no está cerrado, avisa.

«MOCKUP CERRADO» es un fichero, `.docs/diseno/mockup-cerrado.md`, con dos líneas:
    cerrado: 2026-11-01
    aprobado_por: <quién lo dio por bueno>
(y debajo, si se quiere, qué pantallas cubre). Lo escribe quien cierra la fase 4, no el agente que
quiere empezar el backend.

ESCAPE ANOTADO: `.docs/diseno/EXENCION-FASES.md` con `autorizado_por:`, `caduca: AAAA-MM-DD` y un
`motivo:` de 40 caracteres o más (p. ej. «el modelo de auth no tiene pantalla propia»). Caducado, no
vale.

HOY SOLO AVISA. Bloquear desde el primer día pararía proyectos sin UI o con escape legítimo. Cada
aviso se anota en `.docs/diseno/avisos-fases.jsonl` para contar cuántos eran falsas alarmas antes de
endurecerlo; con `TL_FASES_DISENO=bloquear` el hook pasa a bloquear (exit 2). Esa promoción es una
decisión con fecha y firma, no un cambio de variable a escondidas.

CÓDIGOS: 0 nada que decir (no es esquema, no hay UI, mockup cerrado o exención vigente) · 1 avisaría
(esquema de backend, UI y mockup sin cerrar) · 2 no se pudo mirar (proyecto inexistente).

USO:
    python3 .claude/scripts/gate_fases_diseno.py <proyecto> <fichero>   # lo que llama el hook
    python3 .claude/scripts/gate_fases_diseno.py --self-test            # se ve fallar en juguetes
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

SCHEMA_FILE = re.compile(r"(^|/)models\.py$|(^|/)models/[^/]+\.py$"
                         r"|(^|/)migrations/\d{4}_[^/]*\.py$")
NOT_PRODUCT = re.compile(r"(^|/)(tests?|\.claude|\.docs|node_modules|\.venv|venv)/")
UI_PACKAGES = re.compile(r'"(react|vue|svelte|next|@angular/core|preact)"\s*:')
CLOSED_FILE = ".docs/diseno/mockup-cerrado.md"
EXEMPTION_FILE = ".docs/diseno/EXENCION-FASES.md"
LOG_FILE = ".docs/diseno/avisos-fases.jsonl"
MIN_REASON = 40


def field(text: str, name: str) -> str:
    m = re.search(rf"^\s*{name}\s*:\s*(.+?)\s*$", text, re.M)
    return m.group(1).strip().strip('"') if m else ""


def has_ui(root: Path) -> str | None:
    """Por qué este proyecto tiene interfaz, o None."""
    if (root / ".docs" / "core" / "design-system.md").is_file():
        return ".docs/core/design-system.md"
    for pkg in ("package.json", "frontend/package.json", "web/package.json", "app/package.json"):
        f = root / pkg
        if f.is_file() and UI_PACKAGES.search(f.read_text(encoding="utf-8", errors="replace")):
            return pkg
    return None


def mockup_closed(root: Path) -> bool:
    f = root / CLOSED_FILE
    if not f.is_file():
        return False
    text = f.read_text(encoding="utf-8", errors="replace")
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", field(text, "cerrado"))
                and field(text, "aprobado_por"))


def valid_exemption(root: Path, today: str) -> str | None:
    f = root / EXEMPTION_FILE
    if not f.is_file():
        return None
    text = f.read_text(encoding="utf-8", errors="replace")
    who, expires, reason = (field(text, "autorizado_por"), field(text, "caduca"),
                            field(text, "motivo"))
    if who and len(reason) >= MIN_REASON and re.fullmatch(r"\d{4}-\d{2}-\d{2}", expires) \
            and expires >= today:
        return f"{who} · caduca {expires} · {reason[:80]}"
    return None


def relative(root: Path, file: str) -> str | None:
    p = Path(file)
    if not p.is_absolute():
        p = root / p
    try:
        rel = p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None                       # fuera del proyecto: no es su backend
    return re.sub(r"^\.claude/worktrees/[^/]+/", "", rel)


def evaluate(root: Path, file: str, today: str | None = None) -> tuple[int, str]:
    today = today or date.today().isoformat()
    if not root.is_dir():
        return 2, f"no existe el proyecto {root}"
    rel = relative(root, file)
    if not rel or NOT_PRODUCT.search(rel) or not SCHEMA_FILE.search(rel):
        return 0, ""
    ui = has_ui(root)
    if not ui:
        return 0, ""
    if mockup_closed(root):
        return 0, ""
    exemption = valid_exemption(root, today)
    if exemption:
        return 0, f"exención honrada: {exemption}"
    return 1, (f"Vas a tocar el esquema del backend ({rel}) y este proyecto tiene interfaz ({ui}) "
               f"con el mockup SIN cerrar: falta {CLOSED_FILE} (cerrado: <fecha> · "
               f"aprobado_por: <quién>). "
               f"El orden es marca → low-fi → high-fi → mockup con datos simulados → backend "
               f"(rules/motores-de-diseno.md §F1, §F3c). Si es legítimo (p. ej. un modelo sin "
               f"pantalla), anótalo en {EXEMPTION_FILE} con autorizado_por, caduca y motivo.")


def log_warning(root: Path, file: str, msg: str) -> None:
    f = root / LOG_FILE
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        with f.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                 "file": relative(root, file), "falsa_alarma": None},
                                ensure_ascii=False) + "\n")
    except OSError:
        pass                              # el aviso importa más que su contador


def self_test() -> int:
    failures = []
    with tempfile.TemporaryDirectory(prefix="gate-fases-") as tmp:
        root = Path(tmp)
        (root / "backend/apps/orders/migrations").mkdir(parents=True)
        model = "backend/apps/orders/models.py"
        cases = [("sin UI: un backend puro no recibe avisos", model, 0)]
        for what, f, expected in cases:
            rc, _ = evaluate(root, f)
            failures += [f"{what}: {rc} (esperado {expected})"] if rc != expected else []
        (root / "frontend").mkdir()
        (root / "frontend/package.json").write_text('{"dependencies": {"react": "19.0.0"}}')
        for what, f, expected in [
                ("con UI y sin mockup cerrado: models.py avisa", model, 1),
                ("con UI: una migración avisa", "backend/apps/orders/migrations/0002_x.py", 1),
                ("un test no es esquema", "backend/apps/orders/tests/models.py", 0),
                ("una vista no es esquema", "backend/apps/orders/views.py", 0),
                ("fuera del proyecto no es su backend", "/tmp/otro/models.py", 0),
                ("dentro de un worktree sí cuenta", ".claude/worktrees/w1/backend/models.py", 1)]:
            rc, _ = evaluate(root, f)
            if rc != expected:
                failures.append(f"{what}: {rc} (esperado {expected})")
        (root / ".docs/diseno").mkdir(parents=True)
        (root / CLOSED_FILE).write_text("cerrado: 2026-11-01\n")
        if evaluate(root, model)[0] != 1:
            failures.append("mockup-cerrado.md sin aprobado_por no debe valer")
        (root / EXEMPTION_FILE).write_text(
            "autorizado_por: Miller\ncaduca: 2026-12-31\nmotivo: corto\n")
        if evaluate(root, model, "2026-11-01")[0] != 1:
            failures.append("una exención con motivo corto no debe valer")
        (root / EXEMPTION_FILE).write_text(
            "autorizado_por: Miller\ncaduca: 2026-11-30\n"
            "motivo: el modelo de auditoría no tiene ninguna pantalla propia\n")
        if evaluate(root, model, "2026-11-01")[0] != 0:
            failures.append("una exención vigente y razonada debe valer")
        if evaluate(root, model, "2026-12-01")[0] != 1:
            failures.append("una exención caducada no debe valer")
        (root / EXEMPTION_FILE).unlink()
        (root / CLOSED_FILE).write_text("cerrado: 2026-11-01\naprobado_por: Miller\n")
        if evaluate(root, model)[0] != 0:
            failures.append("con el mockup cerrado y firmado no debe avisar")
        if evaluate(root / "no-existe", model)[0] != 2:
            failures.append("un proyecto inexistente debe dar 2")
    for f in failures:
        print(f"  ✗ {f}")
    verdict = f"FALLA ({len(failures)})" if failures else "OK"
    print(f"gate_fases_diseno.py --self-test: {verdict} — sin UI calla · UI sin mockup avisa en "
          "models y migraciones · tests, vistas y fuera del proyecto callan · worktree cuenta · "
          "cierre sin firma y exención corta o caducada no valen")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--self-test"]:
        return self_test()
    if len(argv) != 2:
        print(__doc__)
        return 2
    root, file = Path(argv[0]), argv[1]
    rc, msg = evaluate(root, file)
    if msg:
        print(msg)
    if rc == 1:
        log_warning(root, file, msg)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
