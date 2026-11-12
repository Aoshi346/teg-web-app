#!/usr/bin/env python3
"""Rellena los `[PERSONALIZAR]` de los auditores desde el dominio del proyecto.

Sub-ola 3.57, item NE-14.

POR QUÉ EXISTE. Los agentes copiados del template llegan con huecos `[PERSONALIZAR…]` que nadie
rellena (23-35 por proyecto medido). Marco audita sin «reglas de oro» ni «transiciones prohibidas»
y Sofía sin saber «qué protege este sistema», aunque el proyecto lo tenga escrito en otro sitio.

CÓMO. Lee `<proyecto>/.docs/domain/domain.yaml` (molde: `.claude/templates/domain.yaml`; lo
siembra `arrancar` desde el paquete del sector) y escribe un fichero por auditor en
`<proyecto>/.docs/domain/agents/<agente>.md`, que la ficha del agente lee antes de empezar.

POR QUÉ NO SE ESCRIBE EN LA FICHA. Una ficha editada en el proyecto pasa a «divergente» para
`template_diff.py` y `propagar.py` deja de actualizarla para siempre (MO-11, el arreglo #17 de
elvion). El fichero aparte es la misma solución que MO-58 da a las rules: la del template intacta,
lo propio al lado.

    python3 gen_agent_domain.py [<proyecto>]          # escribe (por defecto, el repo del script)
    python3 gen_agent_domain.py [<proyecto>] --check  # exit 1 si un fichero no refleja domain.yaml
    python3 gen_agent_domain.py --autoprueba          # juguete, con un sabotaje que debe fallar

Salida: 0 al día · 1 desfasado (--check) · 2 no hay `.docs/domain/domain.yaml` que leer.
"""
from __future__ import annotations

import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ".docs/domain/domain.yaml"
OUT_DIR = ".docs/domain/agents"
EMPTY_EVIDENCE = {"desconocido"}

#: auditor → [(sección de domain.yaml, título, qué hueco [PERSONALIZAR] cubre)]
AGENTS: dict[str, list[tuple[str, str, str]]] = {
    "marco-qa-breaker": [
        ("states", "Estados y transiciones prohibidas", "Scope · máquina de estados"),
        ("one_time_actions", "Acciones «una sola vez»", "Scope · acciones únicas"),
        ("limits", "Límites de entrada", "Scope · límites"),
        ("time_windows", "Ventanas temporales", "Scope · condiciones temporales"),
        ("golden_rules", "Reglas de oro", "Contexto del proyecto"),
    ],
    "sofia-pentester": [("protects", "Activos a proteger (orden de criticidad)",
                         "Activos a proteger")],
    "priya-privacy-auditor": [("sensitive_data", "Datos personales y sensibles",
                               "qué PII maneja")],
    "lidia-naive-tester": [("personas", "La persona", "la persona real del proyecto")],
    "nadia-chatbot-evaluator": [("tone", "Tono y voz", "Tono / brand")],
    "pol-product-advisor": [("personas", "Personas del producto", "usuarios reales")],
}


def _filled(item) -> bool:
    if isinstance(item, dict):
        if item.get("evidence") in EMPTY_EVIDENCE:
            return False
        return any(v not in (None, "", [], {}) for k, v in item.items() if k != "evidence")
    return item not in (None, "", [], {})


def _items(domain: dict, section: str, agent: str) -> list:
    raw = domain.get(section)
    # Un texto suelto es un dato, no una lista de caracteres.
    items = [raw] if isinstance(raw, (dict, str)) else list(raw or [])
    items = [i for i in items if _filled(i)]
    return items[:1] if (agent == "lidia-naive-tester" and section == "personas") else items


def _line(item) -> str:
    if not isinstance(item, dict):
        return f"- {item}"
    ev = item.get("evidence", "sin evidencia declarada")
    parts = []
    for k, v in item.items():
        if k == "evidence" or v in (None, "", [], {}):
            continue
        parts.append(f"**{k}:** {', '.join(map(str, v)) if isinstance(v, list) else v}")
    flag = (" ⚠ *supuesto: hipótesis, confírmala antes de tratarla como regla*"
            if ev == "supuesto" else "")
    return f"- {' · '.join(parts)} `({ev})`{flag}"


def render(domain: dict, agent: str) -> tuple[str, int, int]:
    """(texto, huecos cubiertos, huecos totales)."""
    out = [f"# Dominio del proyecto para `{agent}`", "",
           f"> GENERADO por `.claude/scripts/gen_agent_domain.py` desde `{SOURCE}` — no se edita",
           "> aquí: se cambia el YAML y se regenera. Rellena los `[PERSONALIZAR]` de la ficha del",
           "> agente y gana sobre sus ejemplos. Lo marcado ⚠ es supuesto, no acuerdo.", "",
           f"Sector: `{domain.get('sector', 'ninguno')}` · "
           f"actualizado: {domain.get('updated', '—')}", ""]
    covered = 0
    for section, title, slot in AGENTS[agent]:
        items = _items(domain, section, agent)
        out += [f"## {title}", f"*(cubre: {slot})*", ""]
        if items:
            covered += 1
            out += [_line(i) for i in items]
        else:
            out.append(f"- sin dato en `{section}`: el hueco `[PERSONALIZAR]` sigue abierto — "
                       "pregúntalo o márcalo como no auditado, nunca lo supongas")
        out.append("")
    return "\n".join(out).rstrip() + "\n", covered, len(AGENTS[agent])


def run(project: pathlib.Path, check: bool) -> int:
    src = project / SOURCE
    if not src.is_file():
        print(f"sin {SOURCE} en {project}: nada que generar "
              "(molde: .claude/templates/domain.yaml)")
        return 2
    domain = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
    stale, total_cov, total = [], 0, 0
    for agent in AGENTS:
        text, cov, n = render(domain, agent)
        total_cov, total = total_cov + cov, total + n
        dst = project / OUT_DIR / f"{agent}.md"
        if check:
            if not dst.is_file() or dst.read_text(encoding="utf-8") != text:
                stale.append(str(dst.relative_to(project)))
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        print(f"  {agent:<26} {cov}/{n} huecos cubiertos")
    if check:
        for s in stale:
            print(f"✗ desfasado o ausente: {s} "
                  "(regenera: python3 .claude/scripts/gen_agent_domain.py)")
        return 1 if stale else 0
    print(f"✓ {OUT_DIR}/: {total_cov}/{total} huecos [PERSONALIZAR] cubiertos desde {SOURCE}")
    return 0


def self_test() -> int:
    import tempfile
    fails = []
    with tempfile.TemporaryDirectory(prefix="gen-agent-domain-") as tmp:
        p = pathlib.Path(tmp)
        if run(p, check=True) != 2:
            fails.append("sin domain.yaml no sale 2")
        (p / ".docs/domain").mkdir(parents=True)
        (p / SOURCE).write_text(yaml.safe_dump({
            "sector": "tienda",
            "states": [{"entity": "pedido", "states": ["nuevo", "pagado"], "final": ["pagado"],
                        "forbidden": ["pagado -> nuevo"], "evidence": "documentado"}],
            "golden_rules": [{"rule": "un pedido pagado no se cobra dos veces",
                              "evidence": "supuesto"}],
            "protects": [{"asset": "", "evidence": "desconocido"}],
            "personas": [{"name": "Ana", "role": "dueña", "evidence": "recordado"},
                         {"name": "Luis", "role": "dependiente", "evidence": "supuesto"}]},
            allow_unicode=True))
        run(p, check=False)
        marco = (p / OUT_DIR / "marco-qa-breaker.md").read_text()
        if "pagado -> nuevo" not in marco or "un pedido pagado" not in marco:
            fails.append("Marco no recibe estados ni reglas de oro")
        if "supuesto: hipótesis" not in marco:
            fails.append("lo supuesto no llega marcado")
        if "sigue abierto" not in (p / OUT_DIR / "sofia-pentester.md").read_text():
            fails.append("un hueco con evidencia desconocida cuenta como cubierto")
        lidia = (p / OUT_DIR / "lidia-naive-tester.md").read_text()
        if "Ana" not in lidia or "Luis" in lidia:
            fails.append("Lidia no recibe solo la primera persona")
        if run(p, check=True) != 0:
            fails.append("--check en rojo recién generado")
        (p / SOURCE).write_text((p / SOURCE).read_text().replace("Ana", "Eva"))   # sabotaje
        if run(p, check=True) != 1:
            fails.append("--check no caza un domain.yaml cambiado sin regenerar")
    if "- no cobrar dos veces" not in render({"golden_rules": "no cobrar dos veces"},
                                             "marco-qa-breaker")[0]:
        fails.append("una sección escrita como texto se parte en caracteres")
    for f in fails:
        print(f"✗ {f}")
    print(f"autoprueba gen_agent_domain: {'OK' if not fails else f'{len(fails)} fallos'}")
    return 1 if fails else 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--autoprueba" in argv:
        return self_test()
    args = [a for a in argv if not a.startswith("--")]
    project = pathlib.Path(args[0]).resolve() if args else ROOT
    return run(project, "--check" in argv)


if __name__ == "__main__":
    sys.exit(main())
