#!/usr/bin/env python3
"""eventos_harness.py — los cuatro hooks nuevos de la sub-ola 2.11 (CL-30, CL-39) y los avisos de CL-24.

Un solo programa y un subcomando por evento; los envoltorios están en `.claude/hooks/`:

  task-completed      TaskCompleted      gate de wave: si la tarea que se cierra se llama «Wave N …» y
                                         esa wave tiene casillas abiertas en el tasks.md activo, exit 2
                                         (la tarea no se cierra). Cualquier otra tarea pasa en silencio.
  pre-compact         PreCompact         copia el transcript a ~/.claude/harness/<proyecto>/precompact/
                                         antes de compactar (se conservan los últimos 15).
  permission-denied   PermissionDenied   registra la denegación del clasificador del modo auto y, UNA
                                         vez por orden y salvo lo destructivo, dice que se puede reintentar.
  instructions-loaded InstructionsLoaded registra qué rules/CLAUDE.md cargan, por qué y con qué fichero.
  aviso-modelo        PostModelSwitch    systemMessage: cambiar de modelo invalida la caché.
  aviso-claude-md     PostToolUse        systemMessage: un CLAUDE.md editado no rige hasta /clear.
  warn-plans-outside-repo PostToolUse    al escribir un .md en ~/.claude/plans/ (fuera del repo, se
                                         sobrescribe): avisa y da la ruta del repo donde guardarlo (AN-14).

LÍMITES HONESTOS
  · `onFailure: "block"` no aplica a TaskCompleted (doc de hooks), así que si ESTE script se rompe por
    dentro, la tarea se cierra: falla abierto. El gate es determinista cuando el script corre, no cuando no.
  · El gate solo mira tareas cuyo asunto empieza por «Wave N»: no inventa el vínculo entre una tarea suelta
    y un tasks.md. Si el tasks.md activo no tiene esa wave, pasa.
  · La raíz del proyecto es CLAUDE_PROJECT_DIR (no el cwd del evento, que cambia con un `cd`).
  · El «tasks.md activo» es el más recientemente modificado de `.specify/sessions/*/` que tenga esa wave.
  · `retry` es una indicación al modelo, no una orden: la denegación sigue en pie.

Informe de carga de rules:  python3 eventos_harness.py informe-rules [--dir <proyecto>]
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

WAVE = re.compile(r"^\s*(wave)\s*(\d+[a-z]?)\b", re.I)
DESTRUCTIVO = re.compile(
    r"\brm\s+-[a-zA-Z]*[rf]|\bgit\s+(push|reset\s+--hard|clean|branch\s+-D)|--force|\bdrop\s+(table|database)"
    r"|\bmkfs\b|\bdd\s+if=|0\.0\.0\.0|\bchmod\s+-R|\bsudo\b",
    re.I,
)
MANTENER_PRECOMPACT = 15


def proyecto() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def estado_dir(sub: str = "") -> Path:
    slug = re.sub(r"[^A-Za-z0-9_.-]", "-", proyecto().name) or "proyecto"
    base = Path(os.environ.get("CLAUDE_STATE_DIR") or Path.home() / ".claude" / "harness")
    d = base / slug / sub if sub else base / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def entrada() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}


def anadir_jsonl(nombre: str, obj: dict) -> None:
    obj = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **obj}
    with open(estado_dir() / nombre, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------ TaskCompleted
def task_completed(e: dict) -> int:
    import glob
    import subprocess
    m = WAVE.match(e.get("task_subject") or "")
    if not m:
        return 0
    wave = f"Wave {m.group(2)}"  # «wave3» / «WAVE 3» -> «Wave 3»
    # La raíz es la del proyecto, no el cwd del evento: tras un `cd src` el cwd ya no ve .specify/.
    raiz = Path(os.environ.get("CLAUDE_PROJECT_DIR") or e.get("cwd") or os.getcwd())
    candidatos = sorted(
        glob.glob(str(raiz / ".specify" / "sessions" / "*" / "tasks.md")),
        key=os.path.getmtime,
        reverse=True,
    )
    tp = Path(__file__).with_name("task_progress.py")
    for tasks in candidatos:
        r = subprocess.run(
            [sys.executable, str(tp), tasks, "--json", "--wave", wave],
            capture_output=True, text=True, timeout=20,
        )
        try:
            j = json.loads(r.stdout)
        except ValueError:
            continue
        if not j.get("total"):
            continue  # esta sesión no tiene esa wave: mira la siguiente
        pend = j["backlog"] + j["doing"]
        anadir_jsonl("task-completed.jsonl", {"tarea": e.get("task_subject"), "tasks": tasks, "pendientes": pend})
        if pend:
            lineas = "\n".join("  " + p for p in j["pending"][:8])
            print(
                f"GATE de wave: «{e.get('task_subject')}» no se cierra, quedan {pend} casillas abiertas en "
                f"{wave} de {os.path.relpath(tasks, raiz)}:\n{lineas}\n"
                "Termínalas (o márcalas [!] con su porqué) y vuelve a cerrar la tarea.",
                file=sys.stderr,
            )
            return 2
        return 0
    return 0


# ------------------------------------------------------------------ PreCompact
def pre_compact(e: dict) -> int:
    import shutil
    t = e.get("transcript_path")
    if not t or not os.path.isfile(t):
        return 0
    d = estado_dir("precompact")
    destino = d / f"{time.strftime('%Y%m%d-%H%M%S')}-{(e.get('session_id') or 'sin-sesion')[:8]}-{e.get('trigger', 'x')}.jsonl"
    shutil.copy2(t, destino)
    viejos = sorted(d.glob("*.jsonl"), key=os.path.getmtime, reverse=True)[MANTENER_PRECOMPACT:]
    for v in viejos:
        v.unlink()
    return 0


# ------------------------------------------------------------------ PermissionDenied
def permission_denied(e: dict) -> int:
    import hashlib
    herramienta = e.get("tool_name", "?")
    entrada_t = e.get("tool_input") or {}
    orden = entrada_t.get("command") or entrada_t.get("file_path") or json.dumps(entrada_t, ensure_ascii=False)[:200]
    firma = hashlib.sha1(f"{herramienta}|{orden}".encode()).hexdigest()[:12]
    visto = estado_dir() / "permission-denied.seen"
    previos = set(visto.read_text().split()) if visto.exists() else set()
    clave = f"{e.get('session_id', '')[:8]}:{firma}"
    repetida = clave in previos
    anadir_jsonl("permission-denied.jsonl", {
        "sesion": (e.get("session_id") or "")[:8], "tool": herramienta, "orden": str(orden)[:300],
        "motivo": e.get("reason"), "repetida": repetida,
    })
    if len(previos) > 500:
        previos = set(list(previos)[-200:])
    visto.write_text("\n".join(sorted(previos | {clave})))
    out = {"systemMessage": f"Modo auto denegó {herramienta}: {str(orden)[:120]}"}
    reintentable = not repetida and not DESTRUCTIVO.search(str(orden))
    if reintentable:
        out["hookSpecificOutput"] = {"hookEventName": "PermissionDenied", "retry": True}
    print(json.dumps(out, ensure_ascii=False))
    return 0


# ------------------------------------------------------------------ InstructionsLoaded
def instructions_loaded(e: dict) -> int:
    anadir_jsonl("instructions-loaded.jsonl", {
        "sesion": (e.get("session_id") or "")[:8], "file": e.get("file_path"), "tipo": e.get("memory_type"),
        "razon": e.get("load_reason"), "globs": e.get("globs"), "trigger": e.get("trigger_file_path"),
        "agent": e.get("agent_type"),
    })
    return 0


def paths_de_rule(texto: str) -> list[str]:
    """Lee `paths:` del frontmatter: lista con guiones, en línea ([a, b]) o un valor suelto."""
    fm = re.match(r"^---\n(.*?)\n---", texto, re.S)
    if not fm:
        return []
    m = re.search(r"^paths:[ \t]*(.*?)(?=^\S|\Z)", fm.group(1), re.S | re.M)
    if not m:
        return []
    cuerpo = m.group(1)
    primera, _, resto = cuerpo.partition("\n")
    primera = primera.strip()
    if primera.startswith("["):
        crudo = [x for x in primera.strip("[]").split(",")]
    elif primera:
        crudo = [primera]
    else:
        crudo = [re.sub(r"\s+#.*$", "", x) for x in re.findall(r"^\s*-\s*(.+)$", resto, re.M)]
    return [x.strip().strip("\"'") for x in crudo if x.strip().strip("\"'")]


def informe_rules(raiz: Path) -> int:
    reglas = {}
    for f in sorted((raiz / ".claude" / "rules").glob("*.md")):
        reglas[str(f)] = paths_de_rule(f.read_text(encoding="utf-8", errors="replace"))
    log = estado_dir() / "instructions-loaded.jsonl"
    cargadas: dict[str, dict] = {}
    if log.exists():
        for linea in log.read_text().splitlines():
            try:
                j = json.loads(linea)
            except ValueError:
                continue
            f = j.get("file") or ""
            c = cargadas.setdefault(f, {"n": 0, "razones": set()})
            c["n"] += 1
            c["razones"].add(j.get("razon"))
    con_paths = [r for r, p in reglas.items() if p]
    sin_paths = [r for r, p in reglas.items() if not p]
    print(f"rules: {len(reglas)} ({len(con_paths)} con paths:, {len(sin_paths)} siempre cargadas) · "
          f"registro: {log} ({sum(c['n'] for c in cargadas.values())} cargas)")
    nunca = [r for r in con_paths if r not in cargadas]
    print(f"con paths: que NO han cargado nunca en el registro: {len(nunca)}")
    for r in nunca:
        print("  -", os.path.relpath(r, raiz), reglas[r])
    print("con paths: que SÍ han cargado:")
    for r in con_paths:
        if r in cargadas:
            print("  +", os.path.relpath(r, raiz), cargadas[r]["n"], sorted(x for x in cargadas[r]["razones"] if x))
    # una rule sin paths: que no carga en session_start no debería existir
    for r in sin_paths:
        if r not in cargadas and cargadas:
            print("  ! sin paths: y ausente del registro:", os.path.relpath(r, raiz))
    return 0


# ------------------------------------------------------------------ avisos (CL-24)
def aviso_modelo(e: dict) -> int:
    if e.get("source") == "resume" or not e.get("to_model"):
        return 0  # restaurar el modelo al reanudar no es un cambio del Usuario
    tok = e.get("context_tokens") or 0
    cuanto = f" (~{tok // 1000}k tokens de contexto)" if tok >= 1000 else ""
    print(json.dumps({"systemMessage": (
        f"Cambio de modelo {e.get('from_model', '?')} -> {e['to_model']}: la caché de prompt "
        f"(cada modelo tiene la suya) se invalida y el siguiente turno relee todo el contexto{cuanto} sin descuento. "
        "Mejor cambiar al empezar tarea, no a mitad.")}, ensure_ascii=False))
    return 0


def aviso_claude_md(e: dict) -> int:
    fp = (e.get("tool_input") or {}).get("file_path", "")
    if not fp.endswith("CLAUDE.md"):
        return 0
    print(json.dumps({"systemMessage": (
        f"Editaste {os.path.basename(os.path.dirname(fp)) or '.'}/CLAUDE.md: no se aplica hasta /clear, "
        "/compact o reiniciar la sesión (esta sesión sigue con el viejo).")}, ensure_ascii=False))
    return 0


def plans_dirs() -> list[Path]:
    """Dónde guarda Claude Code los planes: ~/.claude/plans (o $CLAUDE_CONFIG_DIR/plans)."""
    out = [Path.home() / ".claude" / "plans"]
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        out.append(Path(os.environ["CLAUDE_CONFIG_DIR"]) / "plans")
    return [d.resolve() for d in out]


def warn_plans_outside_repo(e: dict) -> int:
    fp = (e.get("tool_input") or {}).get("file_path", "")
    if not fp.endswith(".md"):
        return 0
    target = Path(fp).resolve()
    if not any(d == target.parent or d in target.parents for d in plans_dirs()):
        return 0
    root = proyecto().resolve()
    if root == target or root in target.parents:
        return 0  # el proyecto vive dentro de ~/.claude (raro): ya está en un repo
    slug = re.sub(r"[^a-z0-9-]+", "-", target.stem.lower()).strip("-") or "plan"
    dest = f".docs/plans/{time.strftime('%Y-%m-%d')}-{slug}/{slug}.md"
    msg = (f"{target} vive FUERA del repo y se puede sobrescribir (el plan mode reescribe su fichero; "
           f"en musa se perdió así un research). Si es un plan o una investigación que hay que conservar, cópialo al repo: "
           f"{dest} (o a la carpeta del plan en curso) y commitéalo. Si es solo el borrador del plan "
           "mode, basta con no dejar ahí lo único que hay.")
    print(json.dumps({"systemMessage": f"Plan fuera del repo: cópialo a {dest} si hay que conservarlo.",
                      "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}},
                     ensure_ascii=False))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "informe-rules":
        raiz = Path(sys.argv[sys.argv.index("--dir") + 1]) if "--dir" in sys.argv else proyecto()
        return informe_rules(raiz)
    tabla = {
        "task-completed": task_completed, "pre-compact": pre_compact, "permission-denied": permission_denied,
        "instructions-loaded": instructions_loaded, "aviso-modelo": aviso_modelo, "aviso-claude-md": aviso_claude_md,
        "warn-plans-outside-repo": warn_plans_outside_repo,
    }
    if cmd not in tabla:
        sys.exit(f"subcomando desconocido: {cmd}")
    try:
        return tabla[cmd](entrada())
    except Exception as exc:  # un hook de visibilidad nunca rompe un turno
        print(f"eventos_harness {cmd}: {exc!r}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
