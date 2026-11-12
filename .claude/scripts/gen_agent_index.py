#!/usr/bin/env python3
"""Genera el índice de la flota (§0) de .claude/agents/README.md desde el frontmatter de cada agente.

Uso:  python3 .claude/scripts/gen_agent_index.py [--check]
      --check: no escribe; sale 1 si el índice está desfasado respecto al disco.

Por qué existe (LI-32 / MAP-5, sub-ola 1.07). La tabla de §0 se escribía a mano: el 2026-10-20
nombraba 27 de los 29 agentes (faltaban hugo-vigilancia-diaria e ivan-agent-runtime) y daba `—` en
`error_cost`/`autonomy_phase` a 15 que ya los declaraban. Un índice escrito a mano miente en cuanto
alguien añade un agente; este se REGENERA, como `skills/README.md` (`gen_skill_index.py`).

Qué sale del disco y qué no:
  · agente      = `agents/*.md` con `name:` en el frontmatter (README.md no es un agente)
  · qué hace    = la `description` (lo único que lee el harness para enrutar), primera frase
  · ec · fase   = `error_cost` y `autonomy_phase` del frontmatter (`—` si no está)
  · familia     = `family:` del frontmatter si lo trae; si no, la tabla FAMILIAS de abajo. Es una
                  clasificación de lectura, no un dato del disco: por eso `--check` falla si un
                  agente no tiene familia o si la tabla nombra uno que ya no existe — así no puede
                  quedarse vieja en silencio.
Solo se reescribe lo que va entre los marcadores AGENT-INDEX; el resto del README (el contrato
del bundle visual y sus anexos) sigue escrito a mano.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # .claude/
AGENTS = ROOT / "agents"
OUT = AGENTS / "README.md"
BEGIN = "<!-- AGENT-INDEX:BEGIN — generado por .claude/scripts/gen_agent_index.py; no editar a mano -->"
END = "<!-- AGENT-INDEX:END -->"

# Familia de lectura de cada agente sin `family:` en su frontmatter. Las etiquetas son las de la
# tabla a mano que esto sustituye (2026-10-20).
FAMILIAS = {
    "aitor-a11y-auditor": "auditor-persona",
    "bruno-perf-cop": "auditor-persona",
    "conrado-cro-auditor": "auditor-persona",
    "dario-commerce-guardrails": "IA conversacional",
    "desarrollador-backend": "stack backend",
    "hugo-vigilancia-diaria": "vigilancia",
    "ignacio-roig": "bundle visual",
    "ivan-agent-runtime": "IA conversacional",
    "lena-i18n-auditor": "auditor-persona",
    "lidia-naive-tester": "bundle visual",
    "marco-qa-breaker": "bundle sec+QA",
    "nadia-chatbot-evaluator": "IA conversacional",
    "nora-ai-act-auditor": "cumplimiento",
    "pilar-impacto-produccion": "verificación",
    "pol-product-advisor": "producto",
    "priya-privacy-auditor": "cumplimiento",
    "rafa-retrieval-engineer": "IA / RAG",
    "rita-pattern-keeper": "patrones",
    "sara-salud-datos": "cumplimiento",
    "sofia-pentester": "bundle sec+QA",
    "teo-llm-redteam": "IA conversacional",
    "vera-art-director": "bundle visual",
    "desarrollador-frontend": "stack frontend",
    "nuria-aislamiento-tenant": "stack backend",
    "marta-revenue-attribution": "IA conversacional",
}


def frontmatter(path: Path) -> dict:
    """Campos planos del frontmatter (sin PyYAML: los derivados no siempre lo tienen)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm, out = m.group(1), {}
    for key in ("name", "error_cost", "autonomy_phase", "family"):
        km = re.search(rf"^{key}:\s*(.*?)\s*$", fm, re.M)
        if km:
            valor = re.sub(r"\s+#.*$", "", km.group(1))      # un comentario YAML no es el valor
            out[key] = valor.strip().strip('"').strip("'")
    bm = re.search(r"^description:\s*[|>][+-]?\s*\n((?:[ \t]+.*\n?)+)", fm, re.M)
    if bm:
        desc = " ".join(l.strip() for l in bm.group(1).splitlines() if l.strip())
    else:
        dm = re.search(r"^description:\s*(.*?)(?=\n[A-Za-z_]+:|\Z)", fm, re.S | re.M)
        desc = dm.group(1).strip() if dm else ""
        desc = desc.strip('"').strip("'")
    out["description"] = re.sub(r"\s+", " ", desc)
    return out


def que_hace(desc: str) -> str:
    """La primera frase de la description, sin el nombre de la persona que la encabeza."""
    d = desc
    nombre, sep, cola = d.partition(" — ")
    if sep and len(nombre) <= 28:              # «Aitor — auditor de …» → «auditor de …»
        d = cola
    frases = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡\[])", d)
    out = frases[0] if frases else d
    if len(out) < 70 and len(frases) > 1:     # demasiado corta para decir qué hace: una más
        out = f"{out} {frases[1]}"
    out = out.rstrip(".")
    if len(out) > 230:
        out = out[:229].rsplit(" ", 1)[0] + "…"
    return out.replace("|", "\\|")


def agentes():
    out = []
    for f in sorted(AGENTS.glob("*.md")):
        if f.name == "README.md":
            continue
        fm = frontmatter(f)
        if not fm.get("name"):
            continue
        out.append((f.stem, fm))
    return out


def bloque(lista) -> tuple[str, list[str]]:
    errores = []
    con_ambos = sum(1 for _, fm in lista if fm.get("error_cost") and fm.get("autonomy_phase"))
    filas = []
    for nombre, fm in lista:
        fam = fm.get("family") or FAMILIAS.get(nombre)
        if not fam:
            errores.append(f"agente sin familia: {nombre} (añádelo a FAMILIAS o pon `family:` en su frontmatter)")
            fam = "?"
        filas.append(f"| `{nombre}` | {fam} | {que_hace(fm.get('description', ''))} | "
                     f"{fm.get('error_cost') or '—'} | {fm.get('autonomy_phase') or '—'} |")
    sobran = sorted(set(FAMILIAS) - {n for n, _ in lista})
    for n in sobran:
        errores.append(f"FAMILIAS nombra un agente que ya no está en disco: {n}")
    L = [
        BEGIN,
        "",
        "### La tabla (generada)",
        "",
        f"**{len(lista)} agentes** en `.claude/agents/*.md` con `name:` en el frontmatter · "
        f"**{con_ambos}** declaran `error_cost` y `autonomy_phase` · "
        f"**{len(lista) - con_ambos}** no declaran alguno de los dos.",
        "",
        "`ec` = `error_cost` · `fase` = `autonomy_phase` · `—` = no declarado en el frontmatter. "
        "«Qué hace» es la primera frase de la `description`, que es lo que lee el harness para "
        "decidir cuándo lanzar el agente.",
        "",
        "| Agente | Familia | Qué hace | ec | fase |",
        "|---|---|---|:--:|:--:|",
        *filas,
        "",
        "Regenerar: `python3 .claude/scripts/gen_agent_index.py` · comprobar: `--check` (exit 1 si "
        "un agente está en disco y no aquí, o al revés).",
        "",
        END,
    ]
    return "\n".join(L), errores


def main():
    check = "--check" in sys.argv
    lista = agentes()
    nuevo, errores = bloque(lista)
    actual = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if BEGIN not in actual or END not in actual:
        print(f"ROTO: {OUT} no tiene los marcadores AGENT-INDEX; no sé dónde va el índice", file=sys.stderr)
        sys.exit(2)
    antes, resto = actual.split(BEGIN, 1)
    _, despues = resto.split(END, 1)
    contenido = antes + nuevo + despues
    for e in errores:
        print(f"⚠️  {e}", file=sys.stderr)
    if check:
        if contenido != actual or errores:
            print(f"DESFASADO: el índice de {OUT} no coincide con los {len(lista)} agentes reales")
            sys.exit(1)
        print(f"OK: {len(lista)} agentes indexados")
        return
    OUT.write_text(contenido, encoding="utf-8")
    print(f"Escrito {OUT} — {len(lista)} agentes")
    if errores:
        sys.exit(1)


if __name__ == "__main__":
    main()
