#!/usr/bin/env python3
"""domain_lint.py — gate del dominio del proyecto y de los paquetes de sector (NE-13, sub-ola 3.54).
(El plan y NE-13 lo llaman `dominio_lint.py`; el fichero va en inglés, `rules/code-style.md` §Idioma.)

POR QUÉ EXISTE. Para el negocio del cliente ya hay `canon_lint.py`. Para el dominio del producto no
había nada: un KPI podía salir en una pantalla sin definición, un término del glosario no decía a qué
cosa del sistema se refiere, y una regla de oro vivía en prosa sin decir dónde se hace cumplir. Una
regla en prosa es *advisory*; con su candado nombrado se puede comprobar.

QUÉ LEE. `.docs/domain/domain.yaml` del proyecto (molde `templates/domain.yaml`) y, si declara
`kpis_file`, las fichas de KPI (formato de `templates/fichas-kpi/kpis.yaml`). Con `--pack`, la
`seed.yaml` de un paquete de `.claude/domains/<sector>/`.

LOS CINCO CASOS (cada uno sale con 1):
  D1  un KPI de `kpis:` (los que salen en pantalla) sin ficha, o con la ficha sin `formula`,
      `ventana`, `fuente_datos`, `unidad`, `poblacion`, `agregacion` o `sin_dato`; o la ficha sin la
      función que la implementa.
  D2  un término de `glossary:` cuya `entity` no es ninguna de `entities:`.
  D3  una sección con `[PERSONALIZAR]` (o vacía) que la semilla del sector SÍ trae: se siembra, no
      se deja el hueco. La semilla se busca en `.claude/skills/domain-<sector>/seed.yaml` (donde la
      instala `domain_packs.py`) y, si no, en `.claude/domains/<sector>/` del template.
  D4  una regla de oro sin candado: `lock` (constraint · validator · test · gate · permission),
      `lock_where` (dónde vive) y `not_enforced_in` (por dónde NO pasa; «ninguno» se escribe).
  D5  un dato con contenido y sin `evidence` válida (documentado · recordado · supuesto · desconocido).

Un `domain.yaml` recién copiado, con todo vacío, pasa: un hueco declarado no es un error (como
`desconocido` en el canon). Lo que no pasa es un dato que dice algo sin respaldo.

USO
    python3 .claude/scripts/domain_lint.py <proyecto | domain.yaml> [--json]
    python3 .claude/scripts/domain_lint.py --pack .claude/domains/<sector>
    python3 .claude/scripts/domain_lint.py --autoprueba

SALIDA: 0 bien · 1 hallazgos (o la autoprueba no ve caer un sabotaje) · 2 no se pudo medir (no hay
`domain.yaml`, no parsea, o `kpis_file` apunta a un fichero que no existe).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import yaml

EXIT_OK, EXIT_FALLO, EXIT_NO_MEDIDO = 0, 1, 2
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ".docs/domain/domain.yaml"
EVIDENCE = {"documentado", "recordado", "supuesto", "desconocido"}
LOCK_KINDS = {"constraint", "validator", "test", "gate", "permission"}
KPI_FIELDS = ("formula", "ventana", "fuente_datos", "unidad", "poblacion", "agregacion", "sin_dato")
PLACEHOLDER = "[PERSONALIZAR]"
META_KEYS = {"version", "sector", "updated", "kpis_file"}


class NoMedible(Exception):
    pass


def _load(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        raise NoMedible(f"{path} no se puede leer: {e}") from e
    if not isinstance(data, dict):
        raise NoMedible(f"{path} no es un mapa")
    return data


def _empty(v) -> bool:
    return v in (None, "", [], {})


def _has_content(item) -> bool:
    if isinstance(item, dict):
        return any(not _empty(v) for k, v in item.items() if k != "evidence")
    return not _empty(item)


def _items(section) -> list:
    if isinstance(section, dict):
        return [section]
    return list(section or []) if isinstance(section, list) else [section]


def _mentions_placeholder(v) -> bool:
    return PLACEHOLDER in json.dumps(v, ensure_ascii=False, default=str)


def _seed_for(sector: str, project: Path | None) -> dict | None:
    if not sector or sector == "ninguno":
        return None
    candidates = []
    if project:
        candidates.append(project / ".claude" / "skills" / f"domain-{sector}" / "seed.yaml")
    candidates.append(ROOT / ".claude" / "domains" / sector / "seed.yaml")
    for c in candidates:
        if c.is_file():
            return _load(c)
    return None


def lint(domain: dict, base: Path, project: Path | None, check_seed: bool = True) -> list[dict]:
    out: list[dict] = []

    def add(rule: str, where: str, what: str, fix: str) -> None:
        out.append({"id": rule, "where": where, "what": what, "fix": fix})

    # D5 — evidencia en todo dato con contenido
    for key, section in domain.items():
        if key in META_KEYS:
            continue
        for i, item in enumerate(_items(section)):
            if isinstance(item, dict) and _has_content(item) and item.get("evidence") not in EVIDENCE:
                add("D5", f"{key}[{i}]", "dato con contenido sin grado de evidencia válido",
                    f"evidence: uno de {sorted(EVIDENCE)}")

    # D2 — glosario contra entidades
    entities = {str(e.get("name", "")).strip().lower()
                for e in _items(domain.get("entities")) if isinstance(e, dict) and e.get("name")}
    for i, term in enumerate(_items(domain.get("glossary"))):
        if not isinstance(term, dict) or not _has_content(term):
            continue
        ent = str(term.get("entity", "")).strip().lower()
        if not ent or ent not in entities:
            add("D2", f"glossary[{i}] «{term.get('term', '?')}»",
                f"el término no apunta a ninguna entidad declarada ({term.get('entity') or 'vacío'})",
                "entity: el `name` de una de `entities:`, o añade la entidad")

    # D4 — candado de cada regla de oro
    for i, rule in enumerate(_items(domain.get("golden_rules"))):
        if not isinstance(rule, dict) or _empty(rule.get("rule")):
            continue
        missing = [k for k in ("lock", "lock_where", "not_enforced_in") if _empty(rule.get(k))]
        if rule.get("lock") and rule.get("lock") not in LOCK_KINDS:
            missing.append(f"lock ∉ {sorted(LOCK_KINDS)}")
        if missing:
            add("D4", f"golden_rules[{i}] «{str(rule.get('rule'))[:50]}»",
                f"regla sin candado: falta {', '.join(missing)}",
                "lock: constraint|validator|test|gate|permission · lock_where: fichero o nombre · "
                "not_enforced_in: por dónde NO pasa (o «ninguno»)")

    # D1 — KPIs en pantalla con ficha completa
    shown = [k for k in _items(domain.get("kpis")) if isinstance(k, dict) and k.get("id")]
    if shown:
        kfile = domain.get("kpis_file")
        if not kfile:
            add("D1", "kpis", "hay KPIs en pantalla y no hay `kpis_file` con sus fichas",
                "kpis_file: ruta a kpis.yaml (molde templates/fichas-kpi/)")
        else:
            kpath = (base / kfile).resolve()
            if not kpath.is_file():
                raise NoMedible(f"kpis_file apunta a {kpath}, que no existe")
            cards = {c.get("id"): c for c in _items(_load(kpath).get("kpis"))
                     if isinstance(c, dict)}
            for k in shown:
                card = cards.get(k["id"])
                if card is None:
                    add("D1", f"kpis «{k['id']}»", "KPI en pantalla sin ficha en kpis_file",
                        "ficha + función + test (skill metricas-dominio)")
                    continue
                missing = [f for f in KPI_FIELDS if _empty(card.get(f))]
                if _empty(card.get("implementacion")):
                    missing.append("implementacion")
                if missing:
                    add("D1", f"kpis «{k['id']}»", f"ficha incompleta: falta {', '.join(missing)}",
                        "rellena la ficha antes de enseñar el número")

    # D3 — huecos que la semilla del sector sabe rellenar
    if check_seed:
        seed = _seed_for(str(domain.get("sector", "")), project)
        for key, section in domain.items():
            if key in META_KEYS or not seed:
                continue
            seed_items = [s for s in _items(seed.get(key)) if _has_content(s)]
            if not seed_items:
                continue
            filled = [s for s in _items(section) if _has_content(s) and not _mentions_placeholder(s)]
            if _mentions_placeholder(section) or not filled:
                add("D3", key, f"hueco que la semilla del sector «{domain.get('sector')}» trae "
                               f"({len(seed_items)} dato(s))",
                    "siémbralo desde la semilla en `supuesto` y confírmalo con el Usuario")
    return out


def run_project(target: Path) -> list[dict]:
    path = target if target.is_file() else target / SOURCE
    if not path.is_file():
        raise NoMedible(f"no hay {SOURCE} en {target}")
    project = path.parents[2] if path.name == "domain.yaml" and path.parent.name == "domain" else None
    return lint(_load(path), path.parent, project)


def run_pack(pack: Path) -> list[dict]:
    seed = pack / "seed.yaml"
    if not seed.is_file():
        raise NoMedible(f"{pack} no tiene seed.yaml")
    return lint(_load(seed), pack, None, check_seed=False)


# ── autoprueba ────────────────────────────────────────────────────────────────────────────

KPIS_OK = """
kpis:
  - id: ticket_medio
    formula: "Σ importe / count(pedidos)"
    ventana: "7 días naturales"
    fuente_datos: [pedido.importe]
    unidad: pedido
    poblacion: "pedidos pagados no sintéticos"
    agregacion: cociente_de_sumas
    sin_dato: "None si no hay importes"
    implementacion: kpis.py::ticket_medio
"""

DOMAIN_OK = {
    "version": 1, "sector": "juguete", "updated": "2026-10-31", "kpis_file": "kpis.yaml",
    "entities": [{"name": "Pedido", "recognized_by": "número de pedido", "evidence": "documentado"}],
    "glossary": [{"term": "ticket", "means": "importe medio por pedido", "entity": "Pedido",
                  "evidence": "recordado"}],
    "golden_rules": [{"rule": "un pedido pagado no se cobra dos veces", "source": "dueño",
                      "lock": "constraint", "lock_where": "orders.Order unique(payment_id)",
                      "not_enforced_in": "importación CSV del ERP", "evidence": "recordado"}],
    "kpis": [{"id": "ticket_medio", "screen": "panel · Hoy", "evidence": "documentado"}],
    "limits": [{"what": "líneas por pedido", "value": "200", "evidence": "supuesto"}],
    "tone": {},
}

SEED = {"version": 1, "sector": "juguete",
        "limits": [{"what": "líneas por pedido", "value": "200", "evidence": "supuesto"}]}


def _case(mutate) -> tuple[dict, str]:
    d = json.loads(json.dumps(DOMAIN_OK))
    kpis = KPIS_OK
    r = mutate(d)
    if isinstance(r, str):
        kpis = r
    return d, kpis


def _set(path: list, value):
    def f(d):
        node = d
        for p in path[:-1]:
            node = node[p]
        node[path[-1]] = value
    return f


def _pop(path: list, key: str):
    def f(d):
        node = d
        for p in path:
            node = node[p]
        node.pop(key)
    return f


CASES = [
    ("correcto: pasa", lambda d: None, set(), EXIT_OK),
    ("vacío recién copiado: pasa (un hueco declarado no es error)",
     lambda d: d.clear() or d.update({"version": 1, "sector": "ninguno",
                                      "golden_rules": [{"rule": "", "evidence": "desconocido"}],
                                      "kpis": [], "glossary": [{"term": "", "evidence":
                                                                "desconocido"}]}), set(), EXIT_OK),
    ("D1: la ficha pierde la fórmula", lambda d: KPIS_OK.replace(
        '    formula: "Σ importe / count(pedidos)"\n', ""), {"D1"}, EXIT_FALLO),
    ("D1: la ficha pierde `sin_dato`", lambda d: KPIS_OK.replace(
        '    sin_dato: "None si no hay importes"\n', ""), {"D1"}, EXIT_FALLO),
    ("D1: KPI en pantalla sin ficha", _set(["kpis", 0, "id"], "conversion"), {"D1"}, EXIT_FALLO),
    ("D1: KPI en pantalla sin función", lambda d: KPIS_OK.replace(
        "    implementacion: kpis.py::ticket_medio\n", ""), {"D1"}, EXIT_FALLO),
    ("D2: término sin entidad", _set(["glossary", 0, "entity"], "Cesta"), {"D2"}, EXIT_FALLO),
    ("D3: hueco con [PERSONALIZAR] que la semilla trae",
     _set(["limits"], [{"what": "[PERSONALIZAR]", "evidence": "desconocido"}]), {"D3"}, EXIT_FALLO),
    ("D4: regla de oro sin candado", _pop(["golden_rules", 0], "lock"), {"D4"}, EXIT_FALLO),
    ("D4: candado sin «dónde NO»", _pop(["golden_rules", 0], "not_enforced_in"),
     {"D4"}, EXIT_FALLO),
    ("D4: tipo de candado inventado", _set(["golden_rules", 0, "lock"], "promesa"), {"D4"},
     EXIT_FALLO),
    ("D5: dato sin evidencia", _pop(["entities", 0], "evidence"), {"D5"}, EXIT_FALLO),
    ("D5: evidencia que no es un grado", _set(["limits", 0, "evidence"], "seguro"), {"D5"},
     EXIT_FALLO),
    ("no medible: kpis_file que no existe", _set(["kpis_file"], "no-esta.yaml"), set(),
     EXIT_NO_MEDIDO),
]


def autoprueba() -> int:
    global ROOT
    ok_total = 0
    with tempfile.TemporaryDirectory(prefix="dominio-lint-autoprueba-") as tmp:
        tmp_root = Path(tmp)
        seed_dir = tmp_root / "tpl" / ".claude" / "domains" / "juguete"
        seed_dir.mkdir(parents=True)
        (seed_dir / "seed.yaml").write_text(yaml.safe_dump(SEED, allow_unicode=True))
        real_root, ROOT = ROOT, tmp_root / "tpl"
        try:
            for i, (name, mutate, expected, exit_expected) in enumerate(CASES):
                d, kpis = _case(mutate)
                proj = tmp_root / f"p{i}"
                (proj / ".docs" / "domain").mkdir(parents=True)
                (proj / ".docs" / "domain" / "domain.yaml").write_text(
                    yaml.safe_dump(d, allow_unicode=True, sort_keys=False))
                (proj / ".docs" / "domain" / "kpis.yaml").write_text(kpis)
                try:
                    got = {f["id"] for f in run_project(proj)}
                    exit_got = EXIT_FALLO if got else EXIT_OK
                except NoMedible:
                    got, exit_got = set(), EXIT_NO_MEDIDO
                ok = got == expected and exit_got == exit_expected
                ok_total += ok
                print(f"{'✅' if ok else '❌'} {name}: exit {exit_got} · {sorted(got) or '—'}"
                      + ("" if ok else f" (esperado {exit_expected} · {sorted(expected)})"))
        finally:
            ROOT = real_root
    # El molde del template y la semilla de ejemplo tienen que pasar tal cual.
    for label, fn in (("molde templates/domain.yaml",
                       lambda: lint(_load(ROOT / ".claude/templates/domain.yaml"), ROOT, None)),
                      ("semilla domains/_template", lambda: run_pack(ROOT / ".claude/domains/_template"))):
        got = {f["id"] for f in fn()}
        ok = not got
        ok_total += ok
        print(f"{'✅' if ok else '❌'} {label}: {sorted(got) or 'pasa'}")
    total = len(CASES) + 2
    print(f"\nautoprueba: {ok_total}/{total}")
    return EXIT_OK if ok_total == total else EXIT_FALLO


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gate del dominio del proyecto (NE-13).")
    ap.add_argument("target", nargs="?", help="proyecto o ruta a domain.yaml")
    ap.add_argument("--pack", help="carpeta de un paquete de .claude/domains/")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--autoprueba", action="store_true")
    a = ap.parse_args(argv)
    if a.autoprueba:
        return autoprueba()
    if not a.target and not a.pack:
        ap.error("falta <proyecto>, --pack o --autoprueba")
    try:
        findings = run_pack(Path(a.pack)) if a.pack else run_project(Path(a.target))
    except NoMedible as e:
        print(json.dumps({"status": "no_medible", "why": str(e)}, ensure_ascii=False) if a.json
              else f"⚠ no se pudo medir: {e}")
        return EXIT_NO_MEDIDO
    if a.json:
        print(json.dumps({"status": "fallo" if findings else "ok", "findings": findings},
                         ensure_ascii=False, indent=1))
    else:
        for f in findings:
            print(f"✗ {f['id']} {f['where']} — {f['what']}\n    → {f['fix']}")
        print(f"\n{len(findings)} hallazgo(s)" if findings else "✅ dominio coherente")
    return EXIT_FALLO if findings else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
