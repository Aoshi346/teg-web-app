#!/usr/bin/env python3
"""block_git_writes.py — la lógica del hook `block-git-writes.sh`: el agente no commitea donde commitea el Usuario.

QUÉ ES (AN-7, sub-ola 3.09). Cosechado de EvoPreven (`hooks/block-git-writes.sh`, 14-10), donde la
regla del Usuario es absoluta: commits, merges y push los hace él. Allí el hook estuvo meses sin hacer
nada (matcher con sintaxis de permisos y exit 1, que no bloquea) y nadie lo vio; por eso aquí viene
con `--self-test` y control negativo.

LEE LA POLÍTICA DEL PROYECTO (`.claude/CONFIGURACION.yaml`, MO-16), no la trae fija:
    git_commit: usuario   → bloquea git commit · merge · push y gh pr create|merge
    git_merge:  usuario   → bloquea git merge y gh pr merge
    otra cosa o sin fichero → no bloquea nada (exit 0)

Lo legítimo con esas palabras pasa: `git stash push`, `git merge-base|merge-tree|merge-file`, y
leer (`git log`, `git status`, `git diff`). Límite conocido (heredado y aceptado): una palabra
prohibida dentro de un argumento de git (`git log --grep commit`) bloquea; se reformula.

Entrada: el JSON del PreToolUse por stdin. Salida: 2 bloquea (motivo por stderr) · 0 deja pasar.
    python3 .claude/scripts/block_git_writes.py --self-test
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import tempfile

NEUTRAL = [(re.compile(r"stash\s+push"), "stash_guardar"),
           (re.compile(r"merge-(base|tree|file)"), "merge_lectura")]
GIT_WORD = r"\bgit\b[^&|;\n]*\b({words})\b"
GH = r"\bgh\s+pr\s+({words})\b"


def policy(project: pathlib.Path) -> dict:
    conf = project / ".claude" / "CONFIGURACION.yaml"
    out = {}
    if conf.is_file():
        text = conf.read_text(encoding="utf-8", errors="replace")
        for key in ("git_commit", "git_merge"):
            m = re.search(rf"^\s*{key}:\s*[\"']?([\w-]+)", text, re.M)
            if m:
                out[key] = m.group(1)
    return out


def blocked(command: str, pol: dict) -> str | None:
    if pol.get("git_commit") == "usuario":
        git_words, gh_words, why = "push|commit|merge", "create|merge", "git_commit: usuario"
    elif pol.get("git_merge") == "usuario":
        git_words, gh_words, why = "merge", "merge", "git_merge: usuario"
    else:
        return None
    norm = command
    for rx, sub in NEUTRAL:
        norm = rx.sub(sub, norm)
    if re.search(GIT_WORD.format(words=git_words), norm, re.I) or re.search(GH.format(words=gh_words), norm, re.I):
        return why
    return None


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (data.get("tool_input") or {}).get("command") or ""
    if not command:
        return 0
    project = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")
    why = blocked(command, policy(project))
    if not why:
        return 0
    print(f"BLOQUEADO ({why} en .claude/CONFIGURACION.yaml): en este proyecto los commits, merges y "
          "push los hace el Usuario, aunque se pida en el chat. Deja los cambios en el árbol y PROPÓN "
          "el mensaje y los comandos exactos, con rutas explícitas (/cerrar-issue paso 7).", file=sys.stderr)
    return 2


def self_test() -> int:
    blocks = ["git commit -m x", "git -C repo commit -m x", "cd a && git push", "git -c user.name=x commit",
              "git merge develop", "gh pr create --fill", "gh pr merge 3", "git commit --amend"]
    passes = ["git status", "git -C repo log --oneline", "git stash push -m wip", "git merge-base a b",
              "git diff develop...HEAD", "ls", "echo commit"]
    merge_only_blocks = ["git merge develop", "gh pr merge 3"]
    merge_only_passes = ["git commit -m x", "git push", "gh pr create"]
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / ".claude").mkdir()
        conf = root / ".claude" / "CONFIGURACION.yaml"
        cases = []
        conf.write_text("respuestas:\n  git_commit: usuario\n  git_merge: usuario\n", encoding="utf-8")
        cases += [(c, 2, "usuario") for c in blocks] + [(c, None, "usuario") for c in passes]
        for cmd, want, label in cases:
            got = blocked(cmd, policy(root))
            ok = bool(got) == bool(want)
            bad += not ok
            print(f"{'OK ' if ok else 'MAL'} [{label}] {'bloquea' if got else 'pasa   '} {cmd}")
        conf.write_text("respuestas:\n  git_commit: 'usuario'\n", encoding="utf-8")
        got = blocked("git push", policy(root))
        bad += not got
        print(f"{'OK ' if got else 'MAL'} [comillas simples] {'bloquea' if got else 'pasa   '} git push")
        conf.write_text("respuestas:\n  git_commit: agente\n  git_merge: usuario\n", encoding="utf-8")
        for cmd in merge_only_blocks + merge_only_passes:
            got = blocked(cmd, policy(root))
            ok = bool(got) == (cmd in merge_only_blocks)
            bad += not ok
            print(f"{'OK ' if ok else 'MAL'} [solo merge] {'bloquea' if got else 'pasa   '} {cmd}")
        # control negativo: la política de la casa (agente) no bloquea nada
        conf.write_text("respuestas:\n  git_commit: agente\n  git_merge: agente-con-ok\n", encoding="utf-8")
        for cmd in blocks:
            got = blocked(cmd, policy(root))
            bad += bool(got)
            print(f"{'MAL' if got else 'OK '} [agente] {'bloquea' if got else 'pasa   '} {cmd}")
        conf.unlink()
        got = blocked("git commit -m x", policy(root))
        bad += bool(got)
        print(f"{'MAL' if got else 'OK '} [sin CONFIGURACION.yaml] {'bloquea' if got else 'pasa'}")
    print("self-test:", "OK" if not bad else f"{bad} MAL")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
