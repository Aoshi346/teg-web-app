#!/usr/bin/env python3
"""deny_destructive_migration.py — una migración destructiva no se ESCRIBE sin aprobación en su cabecera.

POR QUÉ (AN-19, cosechado de cold_calling_coach). `governance.md` §2 pide aprobación para `DROP`,
`ALTER ... DROP` y `DELETE` masivo. En prosa se olvida; aquí es un bloqueo. `guarda_destructivos.py`
ya pregunta al EJECUTAR `migrate`; esto mira el FICHERO al escribirlo, que es donde se ve qué hace.

La versión de origen leía `$CLAUDE_TOOL_FILE` y `$CLAUDE_TOOL_INPUT`, variables que Claude Code no
pone: el hook nunca bloqueó nada (el mismo fallo que elvion #17). Aquí se lee el JSON de stdin y se
juzga el fichero TAL COMO QUEDARÍA (Write: el contenido nuevo; Edit y MultiEdit: el actual con los
cambios aplicados), porque en PreToolUse el disco todavía tiene la versión vieja.

Cómo se aprueba: una línea en el fichero de migración
    # migration-approved-by: <quién> <AAAA-MM-DD> <ref del plan o ADR>

Uso:
    (hook PreToolUse, matcher «Write|Edit|MultiEdit»; envoltorio: hooks/deny-destructive-migration.sh)
    python3 .claude/scripts/deny_destructive_migration.py --self-test
Salida: 0 deja pasar · 2 bloquea (motivo por stderr).
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile

# Django, Alembic y SQL suelto. Solo lo que pierde datos: renombrar o añadir no está aquí.
DESTRUCTIVE = re.compile(
    r"\b(DeleteModel|RemoveField|RemoveIndex|RemoveConstraint|op\.drop_(table|column|index|constraint))\b"
    r"|\bDROP\s+(TABLE|COLUMN|SCHEMA|DATABASE)\b|\bTRUNCATE\b|\bDELETE\s+FROM\b",
    re.IGNORECASE,
)
APPROVAL = re.compile(r"^\s*#\s*migration-approved-by:\s*\S+", re.MULTILINE)
MIGRATION_PATH = re.compile(r"(^|/)(migrations|alembic/versions|versions)/[^/]+\.(py|sql)$")


def resulting_content(tool: str, tin: dict) -> str | None:
    """El fichero como quedaría tras la tool. None si no se puede saber (se deja pasar)."""
    path = tin.get("file_path") or ""
    if tool == "Write":
        return tin.get("content", "")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        text = ""
    edits = tin.get("edits") if tool == "MultiEdit" else [tin]
    for e in edits or []:
        old, new = e.get("old_string", ""), e.get("new_string", "")
        if e.get("replace_all"):
            text = text.replace(old, new)
        else:
            text = text.replace(old, new, 1) if old else new + text
    return text


def decide(event: dict) -> tuple[int, str]:
    tool = event.get("tool_name", "")
    tin = event.get("tool_input") or {}
    path = tin.get("file_path") or ""
    if tool not in ("Write", "Edit", "MultiEdit") or not MIGRATION_PATH.search(path):
        return 0, ""
    text = resulting_content(tool, tin)
    if text is None or not DESTRUCTIVE.search(text) or APPROVAL.search(text):
        return 0, ""
    op = DESTRUCTIVE.search(text).group(0)
    msg = (
        f"BLOQUEADO: '{path}' quedaría con una operación destructiva de esquema ({op}) sin aprobar.\n"
        "Falta una línea en la cabecera del fichero:\n"
        "    # migration-approved-by: <quién aprueba> <AAAA-MM-DD> <ref del plan o del ADR>\n"
        "Antes de escribirla: governance.md §2 pide aprobación para migraciones destructivas y\n"
        "refactor-progresivo.md la estrategia expand-migrate-contract."
    )
    return 2, msg


def self_test() -> int:
    d = tempfile.mkdtemp()
    mig = os.path.join(d, "app", "migrations", "0002_x.py")
    os.makedirs(os.path.dirname(mig))
    with open(mig, "w", encoding="utf-8") as f:
        f.write("operations = [migrations.AddField('a', 'b', None)]\n")
    cases = [
        ("Write con RemoveField sin aprobar", {"tool_name": "Write", "tool_input": {
            "file_path": mig, "content": "operations=[migrations.RemoveField('a','b')]"}}, 2),
        ("Write con RemoveField aprobado", {"tool_name": "Write", "tool_input": {
            "file_path": mig, "content": "# migration-approved-by: ana 2026-10-31 ADR-7\n"
                                         "operations=[migrations.RemoveField('a','b')]"}}, 0),
        ("Edit que mete un DROP en el fichero real", {"tool_name": "Edit", "tool_input": {
            "file_path": mig, "old_string": "AddField('a', 'b', None)",
            "new_string": "RunSQL('DROP TABLE a')"}}, 2),
        ("Edit aditivo", {"tool_name": "Edit", "tool_input": {
            "file_path": mig, "old_string": "None", "new_string": "models.TextField()"}}, 0),
        ("RemoveField fuera de migrations/", {"tool_name": "Write", "tool_input": {
            "file_path": os.path.join(d, "app", "views.py"), "content": "RemoveField"}}, 0),
        ("Alembic op.drop_column", {"tool_name": "Write", "tool_input": {
            "file_path": os.path.join(d, "alembic", "versions", "a1.py"),
            "content": "op.drop_column('t','c')"}}, 2),
        ("Bash no se mira aquí", {"tool_name": "Bash", "tool_input": {"command": "rm x"}}, 0),
    ]
    failures = 0
    for name, ev, expected in cases:
        rc, _ = decide(ev)
        ok = rc == expected
        failures += not ok
        print(f"  {'✓' if ok else '✗'} {name}: {rc} (esperado {expected})")
    print("self-test:", "OK" if not failures else f"{failures} FALLO(S)")
    return 1 if failures else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    rc, msg = decide(event)
    if msg:
        print(msg, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
