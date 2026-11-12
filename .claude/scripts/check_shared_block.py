#!/usr/bin/env python3
"""check_shared_block.py — bloques que DEBEN ser idénticos en varios ficheros.

Comprueba tres grupos (todos con marcadores SHARED:BEGIN/END, cada uno en su sintaxis):

  1. report-kit  — el bloque CSS de las 5 plantillas de `templates/report_kit/`.
  2. security-qa — el production-scope guard de `agents/sofia-pentester.md` y
     `agents/marco-qa-breaker.md`.
  3. no-confirmado — «lo no confirmado y dónde miré» (`rules/verdict-contract.md` regla 6) en
     TODOS los agentes que auditan: cualquier `agents/*.md` con `name:` salvo los de
     NO_AUDITORS, que hacen y no juzgan. Un agente nuevo nace dentro: o lleva el bloque, o se
     declara aquí con su porqué.

Uso:
  python3 .claude/scripts/check_shared_block.py            # check: exit 1 si alguno diverge
  python3 .claude/scripts/check_shared_block.py --sync <plantilla-fuente>
        # solo report-kit: copia el bloque de la plantilla fuente a las otras 4
  python3 .claude/scripts/check_shared_block.py --sync-auditors <ficha-fuente>
        # grupo 3: copia el bloque de esa ficha a los auditores; si a uno le falta, lo inserta
        # antes de su `## Related` (o al final)
  python3 .claude/scripts/check_shared_block.py --self-test
        # control negativo del grupo 3: un auditor sin bloque y uno divergente tienen que fallar

Por qué existe el grupo 1: CSS divergente entre las 5 páginas fue la causa raíz de los findings
"×N" del QA-loop TPL1-W3 iter-1 (H1 ×3, badge ×2, eyebrow ×3…) — G2 de Pol. Rule:
rules/report-kit.md.

Por qué existe el grupo 2 (2026-08-22): el protocolo del par Sofía+Marco está escrito ENTERO en
cada ficha a propósito — un subagente solo recibe el cuerpo de su propio fichero, así que un
protocolo guardado aparte es advisory y puede no llegarle. La contrapartida es que las dos copias
se pueden separar sin que nadie lo note, y la pieza que no puede fallar es justo esta: el guard que
aborta si el objetivo parece producción. El contrato estaba escrito en `security-qa-bundle.md`
("bumpear `shared_utils_version` en ambos"), un fichero sin frontmatter que el harness no cargaba
nunca; al archivarlo, el contrato baja de prosa a comprobador (`rules/layer-decision.md`).
"""
import hashlib
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1] / "templates" / "report_kit"
# Los marcadores admiten texto dentro del comentario: /* SHARED:BEGIN — lo que sea */
BEGIN_RX = r"/\*\s*SHARED:BEGIN[^*]*\*/"
END_RX = r"/\*\s*SHARED:END[^*]*\*/"
BEGIN, END = "/* SHARED:BEGIN */", "/* SHARED:END */"  # forma canónica para --sync

AGENTS = Path(__file__).resolve().parents[1] / "agents"
# Grupo 2: markdown, así que los marcadores van en comentario HTML.
MD_BEGIN_RX = r"<!--\s*SHARED:BEGIN[^>]*-->"
MD_END_RX = r"<!--\s*SHARED:END[^>]*-->"
PARES_MD = [("security-qa-guard", ["sofia-pentester.md", "marco-qa-breaker.md"])]

# Grupo 3: agentes que NO auditan (implementan, redactan o solo leen) y por eso no llevan el bloque.
NO_AUDITORS = {
    "desarrollador-backend": "implementa",
    "especialista-widget-embebido": "construye el widget; lo juzga la skill widget-embed-test",
    "rafa-retrieval-engineer": "implementa el retrieval",
    "captacion-prospectos": "redacta borradores",
    "analista-negocio": "sintetiza; quien juzga su salida es auditor-evidencia",
    "lector-web": "solo lee para los workflows de research",
    "desarrollador-frontend": "implementa; lo juzgan el patrón, ux-reviewer y el /qa-loop",
}
AUDITOR_BLOCK = "no-confirmado"


def block_of(p: Path) -> str | None:
    m = re.search(BEGIN_RX + r"(.*?)" + END_RX, p.read_text(encoding="utf-8"), re.S)
    return m.group(1) if m else None


def bloque_md(p: Path) -> str | None:
    m = re.search(MD_BEGIN_RX + r"(.*?)" + MD_END_RX, p.read_text(encoding="utf-8"), re.S)
    return m.group(1) if m else None


def named_block(text: str, name: str) -> re.Match | None:
    """El bloque SHARED de markdown cuyo marcador de inicio empieza por `name`."""
    rx = r"<!--\s*SHARED:BEGIN\s+" + re.escape(name) + r"\b[^>]*-->(.*?)" + MD_END_RX
    return re.search(rx, text, re.S)


def auditors(agents_dir: Path) -> list[Path]:
    """Fichas con `name:` en el frontmatter que no están en NO_AUDITORS."""
    out = []
    for p in sorted(agents_dir.glob("*.md")):
        head = p.read_text(encoding="utf-8").split("\n---", 1)[0]
        if not re.search(r"^name:\s*\S", head, re.M):
            continue
        if p.stem not in NO_AUDITORS:
            out.append(p)
    return out


def check_auditors(agents_dir: Path = AGENTS) -> bool:
    """True si todos los auditores llevan el bloque no-confirmado y es idéntico."""
    files = auditors(agents_dir)
    if not files:
        print(f"SIN AUDITORES en {agents_dir}: el grupo {AUDITOR_BLOCK} no mide nada")
        return False
    blocks = {}
    missing = []
    for p in files:
        m = named_block(p.read_text(encoding="utf-8"), AUDITOR_BLOCK)
        if m is None:
            missing.append(p.stem)
        else:
            blocks[p.stem] = hashlib.sha256(m.group(1).encode()).hexdigest()[:12]
    ok = True
    if missing:
        print(f"AUDITORES SIN BLOQUE {AUDITOR_BLOCK} ({len(missing)}): {', '.join(missing)}")
        print("  → --sync-auditors <ficha-buena>, o declara el agente en NO_AUDITORS con su porqué")
        ok = False
    if len(set(blocks.values())) > 1:
        print(f"DIVERGEN ({AUDITOR_BLOCK}):")
        for n, h in sorted(blocks.items()):
            print(f"  {h}  agents/{n}.md")
        ok = False
    if ok:
        print(f"OK: bloque {AUDITOR_BLOCK} idéntico en {len(files)} auditores "
              f"({next(iter(blocks.values()))}; {len(NO_AUDITORS)} declarados no-auditores)")
    return ok


def sync_auditors(src: Path, agents_dir: Path = AGENTS) -> None:
    """Copia el bloque de `src` a todos los auditores; lo inserta donde falte."""
    m = named_block(src.read_text(encoding="utf-8"), AUDITOR_BLOCK)
    if m is None:
        sys.exit(f"ERROR: {src} no tiene bloque SHARED {AUDITOR_BLOCK}")
    full = m.group(0)
    for p in auditors(agents_dir):
        if p.resolve() == src.resolve():
            continue
        txt = p.read_text(encoding="utf-8")
        cur = named_block(txt, AUDITOR_BLOCK)
        if cur is not None:
            if cur.group(0) == full:
                continue
            new = txt.replace(cur.group(0), full)
        else:
            rel = re.search(r"^## (Related|Relacionad[oa]s?)\b.*$", txt, re.M)
            if rel:
                new = txt[:rel.start()] + full + "\n\n" + txt[rel.start():]
            else:
                new = txt.rstrip("\n") + "\n\n" + full + "\n"
        p.write_text(new, encoding="utf-8")
        print(f"SYNC agents/{p.name}")


def self_test() -> None:
    """Control negativo: un auditor sin bloque y otro divergente tienen que dar False."""
    import tempfile
    block = "<!-- SHARED:BEGIN no-confirmado -->\nTexto.\n<!-- SHARED:END -->"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "a.md").write_text(f"---\nname: a\n---\n# A\n{block}\n## Related\n", encoding="utf-8")
        (root / "b.md").write_text("---\nname: b\n---\n# B\n## Related\n", encoding="utf-8")
        (root / "desarrollador-backend.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        assert not check_auditors(root), "un auditor sin bloque debía fallar"
        sync_auditors(root / "a.md", root)
        assert check_auditors(root), "tras --sync-auditors los dos debían coincidir"
        assert "SHARED:BEGIN no-confirmado" in (root / "b.md").read_text().split("## Related")[0]
        (root / "b.md").write_text((root / "b.md").read_text().replace("Texto.", "Otro."), encoding="utf-8")
        assert not check_auditors(root), "un bloque divergente debía fallar"
    print("self-test OK: falta y divergencia detectadas; --sync-auditors inserta antes de Related")


def check_pares_md() -> bool:
    """True si todos los pares de markdown coinciden. Imprime el detalle."""
    ok = True
    for nombre, ficheros in PARES_MD:
        rutas = [AGENTS / f for f in ficheros]
        faltan = [r.name for r in rutas if not r.exists()]
        if faltan:
            print(f"FALTA EL FICHERO ({nombre}): {', '.join(faltan)}")
            ok = False
            continue
        bloques = {r.name: bloque_md(r) for r in rutas}
        sin_marcador = [n for n, b in bloques.items() if b is None]
        if sin_marcador:
            print(f"SIN MARCADORES SHARED ({nombre}): {', '.join(sin_marcador)}")
            ok = False
            continue
        hashes = {n: hashlib.sha256(b.encode()).hexdigest()[:12] for n, b in bloques.items()}
        if len(set(hashes.values())) == 1:
            print(f"OK: bloque {nombre} idéntico en {len(rutas)} fichas ({next(iter(hashes.values()))})")
        else:
            print(f"DIVERGEN ({nombre}):")
            for n, h in sorted(hashes.items()):
                print(f"  {h}  agents/{n}")
            print("  → cópialo de la buena a la otra Y sube shared_utils_version en los dos frontmatter")
            ok = False
    return ok


def main():
    if "--self-test" in sys.argv:
        self_test()
        return
    if "--sync-auditors" in sys.argv:
        sync_auditors(Path(sys.argv[sys.argv.index("--sync-auditors") + 1]))
        return
    pages = sorted(KIT.glob("*.template.html"))
    if not pages:
        sys.exit(f"ERROR: no hay plantillas en {KIT}")
    blocks = {p.name: block_of(p) for p in pages}
    missing = [n for n, b in blocks.items() if b is None]

    if "--sync" in sys.argv:
        src = Path(sys.argv[sys.argv.index("--sync") + 1])
        canon = block_of(src)
        if canon is None:
            sys.exit(f"ERROR: {src} no tiene bloque SHARED")
        for p in pages:
            if p.resolve() == src.resolve():
                continue
            txt = p.read_text(encoding="utf-8")
            if re.search(BEGIN_RX, txt):
                new = re.sub(BEGIN_RX + r".*?" + END_RX,
                             BEGIN + canon + END, txt, flags=re.S)
                p.write_text(new, encoding="utf-8")
                print(f"SYNC {p.name}")
            else:
                print(f"SKIP {p.name}: sin marcadores SHARED (añádelos a mano)")
        return

    if missing:
        print(f"SIN BLOQUE SHARED: {', '.join(missing)}")
        sys.exit(1)
    hashes = {n: hashlib.sha256(b.encode()).hexdigest()[:12] for n, b in blocks.items() if b is not None}
    ok = True
    if len(set(hashes.values())) == 1:
        print(f"OK: bloque SHARED idéntico en {len(pages)} plantillas ({next(iter(hashes.values()))})")
    else:
        print("DIVERGEN:")
        for n, h in sorted(hashes.items()):
            print(f"  {h}  {n}")
        print(f"Re-sincronizar: python3 {Path(__file__).name} --sync <plantilla-buena>")
        ok = False

    if not check_pares_md():
        ok = False
    if not check_auditors():
        ok = False
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
