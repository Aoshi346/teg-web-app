#!/usr/bin/env python3
"""run.py — cada pieza cosechada en las sub-olas 3.20 y 3.21 corre contra su fixture, con su sabotaje.

(Las dos de la 3.21 que necesitan docker van aparte: access_audit.py y compose_wrapper.py.)

    python3 .claude/smoke/harvest/run.py            # todo; exit 1 si algo no da lo esperado
    python3 .claude/smoke/harvest/run.py --solo hooks

Sin modelo, sin red y sin tocar nada fuera de un directorio temporal. Cada caso dice qué espera y
qué sale; un caso de control (lo que NO debe saltar) acompaña a cada bloqueo.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

CL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .claude/
H, S = os.path.join(CL, "hooks"), os.path.join(CL, "scripts")
FAILURES: list[str] = []


def run(argv: list[str], stdin: str = "", env: dict | None = None, cwd: str | None = None):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run(argv, input=stdin, capture_output=True, text=True, env=e, cwd=cwd, timeout=120)


def check(name: str, rc: int, expected: int, extra: str = "") -> None:
    ok = rc == expected
    print(f"  {'✓' if ok else '✗'} {name}: rc={rc} (esperado {expected}){' · ' + extra if extra else ''}")
    if not ok:
        FAILURES.append(name)


def hook(name: str, event: dict, **kw):
    return run(["bash", os.path.join(H, name)], json.dumps(event), **kw)


def hooks() -> None:
    print("AN-19 · hooks opcionales")
    t = tempfile.mkdtemp()
    os.makedirs(os.path.join(t, "app", "migrations"))
    mig = os.path.join(t, "app", "migrations", "0003_x.py")
    w = lambda c: {"tool_name": "Write", "tool_input": {"file_path": mig, "content": c}}  # noqa: E731
    check("migración con RemoveField sin aprobar → bloquea",
          hook("deny-destructive-migration.sh", w("ops=[migrations.RemoveField('a','b')]")).returncode, 2)
    check("control: la misma, aprobada → pasa", hook("deny-destructive-migration.sh", w(
        "# migration-approved-by: ana 2026-10-31 ADR-1\nops=[migrations.RemoveField('a','b')]")).returncode, 0)
    check("control: migración aditiva → pasa",
          hook("deny-destructive-migration.sh", w("ops=[migrations.AddField('a','b',None)]")).returncode, 0)

    os.makedirs(os.path.join(t, ".claude"), exist_ok=True)
    with open(os.path.join(t, ".claude", "PROVIDERS.json"), "w", encoding="utf-8") as f:
        json.dump({"providers": [{"interface": "stt", "env": "TL_SMOKE_FAKE_KEY"}]}, f)
    bash = lambda c: {"tool_name": "Bash", "tool_input": {"command": c}}  # noqa: E731
    env = {"CLAUDE_PROJECT_DIR": t, "TL_SMOKE_FAKE_KEY": ""}
    r = hook("check-provider-fixtures.sh", bash("pytest -m live tests/"), env=env)
    check("pytest -m live sin la clave → bloquea", r.returncode, 2)
    check("control: pytest normal → pasa",
          hook("check-provider-fixtures.sh", bash("pytest tests/"), env=env).returncode, 0)
    check("control: con la clave puesta → pasa", hook("check-provider-fixtures.sh", bash(
        "pytest -m live tests/"), env={"CLAUDE_PROJECT_DIR": t, "TL_SMOKE_FAKE_KEY": "x"}).returncode, 0)

    r = hook("hint-affected-tests.sh", {"tool_input": {"file_path": "/p/backend/apps/billing/models.py"}})
    check("hint tras tocar apps/billing/models.py → avisa", 0 if "pytest apps/billing" in r.stdout else 1, 0)
    r = hook("hint-affected-tests.sh", {"tool_input": {"file_path": "/p/frontend/src/App.tsx"}})
    check("control: fichero de frontend → calla", 0 if not r.stdout.strip() else 1, 0)

    g = tempfile.mkdtemp()
    run(["git", "init", "-q", g])
    os.makedirs(os.path.join(g, "schemas"))
    with open(os.path.join(g, "schemas", "finding.json"), "w") as f:
        f.write("{roto")
    run(["git", "-C", g, "add", "schemas/finding.json"])
    check("pre-commit con un JSON Schema roto → bloquea",
          run(["bash", os.path.join(H, "check-contracts.sh")], cwd=g).returncode, 1)
    with open(os.path.join(g, "schemas", "finding.json"), "w") as f:
        f.write('{"type": "object"}')
    run(["git", "-C", g, "add", "schemas/finding.json"])
    check("control: el JSON Schema válido → pasa",
          run(["bash", os.path.join(H, "check-contracts.sh")], cwd=g).returncode, 0)

    root = tempfile.mkdtemp()
    genv = {"CLAUDE_PROJECT_DIR": root}
    check("sin modo declarado, git commit → pasa",
          hook("governance-gate.sh", bash("git commit -m x"), env=genv).returncode, 0)
    run([sys.executable, os.path.join(S, "governance_mode.py"), "--root", root, "--modo", "asistido",
         "--razon", "smoke"])
    check("modo asistido, git commit → bloquea",
          hook("governance-gate.sh", bash("git commit -m x"), env=genv).returncode, 2)
    check("control: modo asistido, git status → pasa",
          hook("governance-gate.sh", bash("git status"), env=genv).returncode, 0)
    run([sys.executable, os.path.join(S, "governance_mode.py"), "--root", root, "--quitar"])
    check("tras --quitar, git commit → pasa (reversible)",
          hook("governance-gate.sh", bash("git commit -m x"), env=genv).returncode, 0)


def scripts_selftest() -> None:
    print("Self-tests de los scripts cosechados")
    for argv, name in [
        (["deny_destructive_migration.py", "--self-test"], "deny_destructive_migration (AN-19)"),
        (["governance_mode.py", "--self-test"], "governance_mode (AN-19)"),
        (["sabotage.py", "--self-test"], "sabotage: un sabotaje cazado y uno que escapa (AN-24)"),
        (["check_unique_ids.py", "--self-test"], "check_unique_ids (AN-24)"),
        (["fork_drift.py", "--self-test"], "fork_drift: fork atrasado, al día y divergente (AN-17)"),
        (["module_split.py", "--self-test"], "module_split: solape de claims y registro sin dueño (AN-D6)"),
        (["check_topology.py", "--self-test"], "check_topology: puerto declarado sin nadie escuchando (AN-25)"),
        (["production_check.py", "--self-test"], "production_check: 0 intacta · 1 tocada · 2 sin medir (AN-20)"),
        (["adoption_backup_check.py", "--self-test"], "adoption_backup_check: copia rota, vacía o en el origen (AN-16)"),
        (["../patterns/stack/integration_check.py", "--self-test"],
         "integration_check: IC1, IC2 y CA1 saboteados (AN-18)"),
        (["gen_codex_bridge.py", "--self-test"], "gen_codex_bridge: rule cambiada, copia retocada, a mano intacta (AN-21)"),
        (["../skills/external-api-contract/index_contract.py", "--self-test"],
         "index_contract: Postman, OpenAPI y Swagger; 0 endpoints → 2 (AN-23)"),
        (["../skills/verify-ticket/verify_ticket.py", "--self-test"],
         "verify_ticket: ticket inválido → 2, auditores, pedido y revisión de capturas (WA-4)"),
        (["db_guard.py", "--self-test"], "db_guard: HOST vacío con OPTIONS/NAME, ENGINE falso y caché remota (4.16)"),
    ]:
        p = os.path.join(S, argv[0])
        if not os.path.exists(p):
            check(name, 127, 0, "no existe")
            continue
        r = run([sys.executable, p, *argv[1:]])
        check(name, r.returncode, 0, "" if r.returncode == 0 else r.stdout[-300:] + r.stderr[-300:])
    for sh, name in [("launch_front.sh", "launch_front: tronco sucio y 4 guardas más (AN-20)"),
                       ("pytest_turn.sh", "pytest_turn: turno ocupado y check-ram en rojo (AN-20)")]:
        p = os.path.join(S, sh)
        if not os.path.exists(p):
            check(name, 127, 0, "no existe")
            continue
        r = run(["bash", p, "--self-test"])
        check(name, r.returncode, 0, "" if r.returncode == 0 else r.stdout[-400:] + r.stderr[-300:])


def main() -> int:
    only = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    if only in (None, "hooks"):
        hooks()
    if only in (None, "scripts"):
        scripts_selftest()
    print(f"\n{'OK' if not FAILURES else str(len(FAILURES)) + ' FALLO(S): ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
