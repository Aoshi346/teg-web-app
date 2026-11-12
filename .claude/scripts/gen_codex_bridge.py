#!/usr/bin/env python3
"""gen_codex_bridge.py — las reglas críticas de la casa, para Codex, con un comando (AN-21, 3.22).

Codex lee `AGENTS.md` y `.agents/skills/` del repositorio; no pasa por los hooks ni los permisos de
Claude Code. Tres proyectos reescribieron a mano las reglas críticas para Codex (elvion: seis skills)
y esas copias ya divergen de las rules. Este script las GENERA desde `templates/codex-bridge/`:

  · un bloque entre marcadores en el `AGENTS.md` del proyecto (lo de fuera del bloque, lo propio del
    proyecto, no se toca; si no hay `AGENTS.md`, se crea con un hueco para eso);
  · una skill por regla crítica en `.agents/skills/<nombre>/SKILL.md`, con una marca de «generada».

Cada pieza está atada en `manifest.json` a las secciones de las rules de las que sale, con el sha de
cada sección cuando se escribió. Si una rule cambia, `--check` sale 1 hasta que alguien revisa la
pieza y corre `--rehash`: así la copia para Codex no se queda atrás sin que nadie lo vea.

Lo que NO pisa nunca: una skill del mismo nombre sin la marca (escrita a mano en el proyecto), ni una
skill de `replaces` (el nombre con el que el proyecto ya la escribió a mano): las dos se avisan.

    python3 .claude/scripts/gen_codex_bridge.py --dest /home/x/proyecto      # escribe
    python3 .claude/scripts/gen_codex_bridge.py --dest /home/x/proyecto --dry-run
    python3 .claude/scripts/gen_codex_bridge.py --check --dest /home/x/proyecto   # ¿copia al día?
    python3 .claude/scripts/gen_codex_bridge.py --check            # ¿alguna rule cambió sin revisar?
    python3 .claude/scripts/gen_codex_bridge.py --rehash           # tras revisar las piezas
    python3 .claude/scripts/gen_codex_bridge.py --self-test

Parámetros del proyecto: `{{pytest}}` sale de `codex_bridge.pytest` en su `.claude/CONFIGURACION.yaml`
(por ejemplo `poetry run pytest`); si no está, `pytest`. `--pytest` lo sobrescribe en una ejecución
(y entonces `--check --dest` necesita el mismo valor: mejor dejarlo en el YAML).

Salida: 0 al día · 1 desfase (rule cambiada sin revisar, copia distinta, description > 1.024) ·
2 no se pudo medir (falta el manifiesto, una rule o una sección, o PyYAML).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLAUDE = ROOT / ".claude"
TEMPLATES = CLAUDE / "templates" / "codex-bridge"
BEGIN = "<!-- CODEX-CRITICAS:BEGIN — generado por .claude/scripts/gen_codex_bridge.py desde las rules del template; no se edita aquí: se edita la rule y se regenera -->"
END = "<!-- CODEX-CRITICAS:END -->"
GEN_MARK = "<!-- gen_codex_bridge: generada desde las rules del template; no se edita aquí -->"
DESC_LIMIT = 1024  # Codex descarta en silencio una skill con la description más larga (check_skills_codex.py)


class Unmeasurable(Exception):
    """Falta algo para medir: salida 2."""


def section_text(rule: Path, heading: str) -> str:
    """Texto de la sección `heading` de `rule` hasta el siguiente encabezado de su nivel o superior.

    Ignora las líneas con «#» dentro de bloques de código (los comentarios de bash no son encabezados).
    """
    if not rule.exists():
        raise Unmeasurable(f"no existe {rule}")
    lines = rule.read_text(encoding="utf-8").splitlines()
    fence = False
    start = level = None
    out: list[str] = []
    for line in lines:
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if start is None:
            if m and m.group(2) == heading:
                start, level = True, len(m.group(1))
                out.append(line)
            continue
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    if start is None:
        raise Unmeasurable(f"{rule.name}: no hay una sección «{heading}»")
    return "\n".join(out).strip() + "\n"


def section_sha(claude_dir: Path, ref: str) -> str:
    path, _, heading = ref.partition("#")
    return hashlib.sha256(section_text(claude_dir / path, heading).encode()).hexdigest()[:12]


def load_manifest(tpl: Path) -> dict:
    f = tpl / "manifest.json"
    if not f.exists():
        raise Unmeasurable(f"no existe {f}")
    return json.loads(f.read_text(encoding="utf-8"))


def project_params(dest: Path, manifest: dict, pytest_cmd: str | None) -> dict:
    params = dict(manifest.get("params", {}))
    conf = dest / ".claude" / "CONFIGURACION.yaml"
    if conf.exists():
        try:
            import yaml
        except ImportError as e:
            raise Unmeasurable("falta PyYAML para leer CONFIGURACION.yaml") from e
        data = yaml.safe_load(conf.read_text(encoding="utf-8")) or {}
        params.update((data.get("codex_bridge") or {}) if isinstance(data, dict) else {})
    if pytest_cmd:
        params["pytest"] = pytest_cmd
    return params


def render(text: str, params: dict) -> str:
    for k, v in params.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def block_text(tpl: Path, manifest: dict, params: dict) -> str:
    body = render((tpl / manifest["block"]["file"]).read_text(encoding="utf-8"), params).strip()
    return f"{BEGIN}\n\n{body}\n\n{END}"


def skill_text(tpl: Path, name: str, params: dict) -> str:
    src = (tpl / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n.*?\n---\n", src, re.S)
    if not m:
        raise Unmeasurable(f"skill {name}: sin frontmatter")
    return render(src[: m.end()] + GEN_MARK + "\n" + src[m.end():], params)


def description_of(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    for line in (m.group(1) if m else "").splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip()
    return ""


def merge_agents(current: str | None, block: str) -> str:
    """El AGENTS.md con el bloque puesto: sustituido si ya estaba, al final si no; nuevo si no hay."""
    if current is None:
        return ("# Instrucciones para el agente\n\n"
                "> Lo propio del proyecto va aquí, fuera del bloque generado: qué es, cómo se arranca,\n"
                "> cómo se comprueba que algo funciona y lo que ya se sabe roto.\n\n" + block + "\n")
    if BEGIN.split(" —")[0] in current and END in current:
        head = current[: current.index(BEGIN.split(" —")[0])]
        tail = current[current.index(END) + len(END):]
        return head + block + tail
    return current.rstrip("\n") + "\n\n" + block + "\n"


def plan(dest: Path, tpl: Path, manifest: dict, params: dict, force: bool) -> tuple[dict, list[str]]:
    """Qué ficheros deberían quedar (ruta → contenido, None = borrar) y los avisos."""
    files: dict[Path, str | None] = {}
    notes: list[str] = []
    agents = dest / "AGENTS.md"
    current = agents.read_text(encoding="utf-8") if agents.exists() else None
    files[agents] = merge_agents(current, block_text(tpl, manifest, params))
    skills_dir = dest / ".agents" / "skills"
    for name, spec in manifest["skills"].items():
        target = skills_dir / name / "SKILL.md"
        alias = next((a for a in spec.get("replaces", []) if (skills_dir / a).exists()), None)
        if alias and not force:
            notes.append(f"{name}: no se genera — el proyecto la tiene a mano como «{alias}» "
                         f"(bórrala allí para adoptar la generada, o --force)")
            continue
        if (target.exists() or (skills_dir / name).is_symlink()) and not force:
            if (skills_dir / name).is_symlink() or GEN_MARK not in target.read_text(encoding="utf-8"):
                notes.append(f"{name}: existe escrita a mano en el proyecto — no se pisa")
                continue
        files[target] = skill_text(tpl, name, params)
    if skills_dir.exists():
        for d in sorted(skills_dir.iterdir()):
            md = d / "SKILL.md"
            if (d.name not in manifest["skills"] and not d.is_symlink() and md.exists()
                    and GEN_MARK in md.read_text(encoding="utf-8")):
                files[md] = None
                notes.append(f"{d.name}: generada y ya no está en el manifiesto — se retira")
    return files, notes


def check_template(claude_dir: Path, tpl: Path, manifest: dict) -> list[str]:
    problems = []
    pieces = [("bloque de AGENTS.md", manifest["block"]["sources"])]
    pieces += [(f"skill {n}", s["sources"]) for n, s in manifest["skills"].items()]
    for label, sources in pieces:
        for s in sources:
            now = section_sha(claude_dir, s["ref"])
            if now != s.get("sha"):
                problems.append(f"{label}: la sección «{s['ref']}» cambió ({s.get('sha') or 'sin sha'} → "
                                f"{now}). Revisa la pieza y corre --rehash")
    for name in manifest["skills"]:
        md = tpl / "skills" / name / "SKILL.md"
        if not md.exists():
            raise Unmeasurable(f"falta {md}")
        text = md.read_text(encoding="utf-8")
        if not re.search(rf"^name:\s*{re.escape(name)}\s*$", text, re.M):
            problems.append(f"skill {name}: el `name:` del frontmatter no es el de la carpeta")
        if len(description_of(text)) > DESC_LIMIT:
            problems.append(f"skill {name}: description de {len(description_of(text))} > {DESC_LIMIT} "
                            f"(Codex la descartaría sin avisar)")
    return problems


def rehash(claude_dir: Path, tpl: Path, manifest: dict) -> int:
    changed = 0
    for sources in [manifest["block"]["sources"]] + [s["sources"] for s in manifest["skills"].values()]:
        for s in sources:
            now = section_sha(claude_dir, s["ref"])
            if s.get("sha") != now:
                s["sha"], changed = now, changed + 1
    (tpl / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    return changed


def run(args: argparse.Namespace, claude_dir: Path = CLAUDE, tpl: Path = TEMPLATES) -> int:
    manifest = load_manifest(tpl)
    if args.rehash:
        n = rehash(claude_dir, tpl, manifest)
        print(f"manifest.json: {n} sha actualizados")
        return 0
    if not args.dest:
        problems = check_template(claude_dir, tpl, manifest)
        for p in problems:
            print(f"✗ {p}")
        if not problems:
            print(f"✓ codex-bridge al día: {len(manifest['skills'])} skills y el bloque, atados a sus rules")
        return 1 if problems else 0
    dest = Path(args.dest).resolve()
    if not dest.is_dir():
        raise Unmeasurable(f"no existe el proyecto {dest}")
    files, notes = plan(dest, tpl, manifest, project_params(dest, manifest, args.pytest), args.force)
    for n in notes:
        print(f"· {n}")
    stale = []
    for path, content in files.items():
        now = path.read_text(encoding="utf-8") if path.exists() else None
        if now != content:
            stale.append(path)
    if args.check:
        for p in stale:
            print(f"✗ desfasado: {p.relative_to(dest)}")
        if not stale:
            print(f"✓ {dest.name}: AGENTS.md y .agents/skills/ al día")
        return 1 if stale else 0
    for path in stale:
        rel = path.relative_to(dest)
        if args.dry_run:
            print(f"(dry-run) escribiría {rel}" if files[path] is not None else f"(dry-run) borraría {rel}")
            continue
        if files[path] is None:
            shutil.rmtree(path.parent)
            print(f"borrado {rel.parent}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(files[path], encoding="utf-8")
            print(f"escrito {rel}")
    if not stale:
        print(f"✓ {dest.name}: nada que cambiar")
    return 0


def self_test() -> int:
    """Los casos que el generador tiene que distinguir, sobre copias en un directorio temporal."""
    ok = True

    def expect(label: str, got, want) -> None:
        nonlocal ok
        good = got == want
        ok &= good
        print(f"{'✓' if good else '✗'} {label}: {got!r}" + ("" if good else f" (esperado {want!r})"))

    def ns(**kw) -> argparse.Namespace:
        base = dict(dest=None, check=False, rehash=False, dry_run=False, force=False, pytest=None)
        base.update(kw)
        return argparse.Namespace(**base)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        claude = tmp / "tpl" / ".claude"
        shutil.copytree(CLAUDE / "rules", claude / "rules")
        tpl = claude / "templates" / "codex-bridge"
        shutil.copytree(TEMPLATES, tpl)
        quiet = lambda a: _quiet(run, a, claude, tpl)  # noqa: E731
        quiet(ns(rehash=True))
        expect("1 plantilla recién rehasheada → --check", quiet(ns()), 0)
        rule = claude / "rules" / "ram-pytest.md"
        rule.write_text(rule.read_text().replace("pytest --cov", "pytest --cov  # sabotaje"))
        expect("2 sabotaje: la rule cambia sin revisar la skill → --check", quiet(ns()), 1)
        rule.write_text(rule.read_text().replace("## Si ocurre OOM", "## Si ocurre un OOM"))
        expect("3 sabotaje: la sección citada desaparece → no se pudo medir", quiet(ns()), 2)

        proj = tmp / "proj"
        (proj / ".agents" / "skills" / "sin-push-merge-deploy").mkdir(parents=True)
        (proj / ".agents" / "skills" / "sin-push-merge-deploy" / "SKILL.md").write_text("a mano\n")
        (proj / ".agents" / "skills" / "local-only-network").mkdir()
        (proj / ".agents" / "skills" / "local-only-network" / "SKILL.md").write_text("propia\n")
        (proj / "AGENTS.md").write_text("# Proyecto X\n\nCómo se arranca: make up.\n")
        (proj / ".claude").mkdir()
        (proj / ".claude" / "CONFIGURACION.yaml").write_text("codex_bridge:\n  pytest: poetry run pytest\n")
        tpl_ok = tmp / "tpl_ok"
        shutil.copytree(TEMPLATES, tpl_ok)
        gen = lambda a: _quiet(run, a, CLAUDE, tpl_ok)  # noqa: E731
        expect("4 proyecto sin generar → --check --dest", gen(ns(dest=proj, check=True)), 1)
        expect("5 escribir", gen(ns(dest=proj)), 0)
        agents = (proj / "AGENTS.md").read_text()
        expect("6 lo propio del AGENTS.md se conserva", "Cómo se arranca: make up." in agents, True)
        expect("7 el parámetro del proyecto llega", "poetry run pytest <ruta-del-modulo>/" in agents, True)
        expect("8 la skill a mano con su alias no se duplica",
               (proj / ".agents/skills/no-push-merge-deploy").exists(), False)
        expect("9 la skill a mano del mismo nombre no se pisa",
               (proj / ".agents/skills/local-only-network/SKILL.md").read_text(), "propia\n")
        expect("10 la generada lleva la marca",
               GEN_MARK in (proj / ".agents/skills/ram-before-pytest/SKILL.md").read_text(), True)
        expect("11 recién escrito → --check --dest", gen(ns(dest=proj, check=True)), 0)
        gen(ns(dest=proj))
        expect("12 segunda pasada idempotente (un solo bloque)",
               (proj / "AGENTS.md").read_text().count("CODEX-CRITICAS:BEGIN"), 1)
        md = proj / ".agents/skills/ram-before-pytest/SKILL.md"
        md.write_text(md.read_text() + "\nretoque a mano\n")
        expect("13 sabotaje: la copia generada se edita → --check --dest", gen(ns(dest=proj, check=True)), 1)
        orphan = proj / ".agents/skills/vieja"
        orphan.mkdir()
        (orphan / "SKILL.md").write_text("---\nname: vieja\n---\n" + GEN_MARK + "\n")
        gen(ns(dest=proj))
        expect("14 generada que salió del manifiesto → se retira", orphan.exists(), False)
        expect("15 tras regenerar → --check --dest", gen(ns(dest=proj, check=True)), 0)
    print("self-test:", "OK" if ok else "FALLA")
    return 0 if ok else 1


def _quiet(fn, args, claude, tpl):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            return fn(args, claude, tpl)
        except Unmeasurable:
            return 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dest", help="raíz del proyecto donde se escribe AGENTS.md y .agents/skills/")
    ap.add_argument("--check", action="store_true", help="no escribe: sale 1 si algo está desfasado")
    ap.add_argument("--rehash", action="store_true", help="apunta el sha actual de cada sección citada")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="genera aunque haya una versión a mano")
    ap.add_argument("--pytest", help="cómo se lanza pytest en el proyecto (p. ej. «poetry run pytest»)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    try:
        return run(args)
    except Unmeasurable as e:
        print(f"⛔ NO SE PUDO MEDIR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
