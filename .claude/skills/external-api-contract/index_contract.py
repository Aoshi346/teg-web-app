#!/usr/bin/env python3
"""index_contract.py — el contrato REAL de una API de terceros, indexado y consultable (AN-23, 3.22).

Una colección de Postman de 13 MB no se «lee»: por eso, a mitad de un diagnóstico, nadie la abre y se
decide de memoria que un endpoint «no existe». Este script la convierte en un índice que se consulta
en segundos, y deja al lado el fichero de gotchas del proveedor.

Formatos: colección de Postman 2.0/2.1 (JSON) · OpenAPI 3.x · Swagger 2.0 (JSON o YAML).

    python3 index_contract.py <contrato> --search diary            # la receta: ¿existe? ¿qué pide?
    python3 index_contract.py <contrato> --search "client history" # todas las palabras, en cualquier orden
    python3 index_contract.py <contrato> --provider flowww --out integrations/flowww/contract/
    python3 index_contract.py --self-test

Con `--out` escribe `contract.md` (el índice por grupo: método, ruta, nombre, campos del cuerpo y de
la respuesta de ejemplo), `contract-index.json` (lo mismo para un script) y, **si no existe**,
`gotchas.md` desde la plantilla (el que haya no se toca nunca: es memoria acumulada).

Salida: 0 hay endpoints (con --search: hay coincidencias) · 1 --search sin coincidencias (eso es «no
aparece en ESTE contrato», nunca «la API no lo soporta») · 2 no se pudo leer: formato desconocido, YAML
sin PyYAML o un contrato con 0 endpoints (un índice vacío no demuestra que nada exista).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOTCHAS_TEMPLATE = HERE / "gotchas-template.md"
METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


class Unreadable(Exception):
    """El contrato no se pudo leer: salida 2."""


def load(path: Path) -> dict:
    if not path.exists():
        raise Unreadable(f"no existe {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        import yaml
    except ImportError as e:
        raise Unreadable("no es JSON y falta PyYAML para leerlo como YAML") from e
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise Unreadable(f"ni JSON ni YAML válido: {e}") from e
    if not isinstance(data, dict):
        raise Unreadable("el contrato no es un objeto")
    return data


def _short(text, limit: int) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()[:limit]


def _json_keys(raw) -> list[str]:
    """Las claves de primer nivel de un ejemplo JSON (o del primer elemento si es una lista)."""
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return []
    if isinstance(data, list) and data:
        data = data[0]
    return list(data.keys())[:40] if isinstance(data, dict) else []


def from_postman(c: dict) -> list[dict]:
    out: list[dict] = []

    def walk(items, group):
        for it in items or []:
            if "item" in it:
                walk(it["item"], f"{group}/{it.get('name', '')}".strip("/"))
                continue
            r = it.get("request") or {}
            if isinstance(r, str):
                r = {"url": r, "method": "GET"}
            u = r.get("url") or ""
            if isinstance(u, dict):
                path = "/" + "/".join(str(p) for p in u.get("path") or []) if u.get("path") else u.get("raw", "")
            else:
                path = str(u)
            path = re.sub(r"^\{\{[^}]+\}\}", "", path)  # {{baseUrl}}/x → /x
            body = (r.get("body") or {}).get("raw") or ""
            resp = (it.get("response") or [{}])[0] or {}
            out.append({
                "group": group, "name": it.get("name", ""), "method": str(r.get("method", "GET")).upper(),
                "path": path or "?", "description": _short(r.get("description"), 600),
                "body_fields": _json_keys(body), "body_example": _short(body, 400),
                "response_fields": _json_keys(resp.get("body")), "response_example": _short(resp.get("body"), 500),
                "required": [],
            })

    walk(c.get("item"), "")
    return out


def _resolve(spec: dict, node):
    seen = 0
    while isinstance(node, dict) and "$ref" in node and seen < 10:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return {}
        node = spec
        for part in ref[2:].split("/"):
            node = node.get(part, {}) if isinstance(node, dict) else {}
        seen += 1
    return node if isinstance(node, dict) else {}


def _schema_fields(spec: dict, schema, mode: str = "body") -> tuple[list[str], list[str]]:
    """Campos y obligatorios; en el cuerpo sin los readOnly, en la respuesta sin los writeOnly."""
    s = _resolve(spec, schema or {})
    if s.get("type") == "array":
        s = _resolve(spec, s.get("items") or {})
    for combo in ("allOf", "oneOf", "anyOf"):
        if combo in s and not s.get("properties"):
            props, req = [], []
            for part in s[combo]:
                p, r = _schema_fields(spec, part, mode)
                props += p
                req += r
            return props, req
    skip = "readOnly" if mode == "body" else "writeOnly"
    props = [k for k, v in (s.get("properties") or {}).items()
             if not (isinstance(v, dict) and _resolve(spec, v).get(skip))]
    return props, [r for r in s.get("required") or [] if r in props]


def from_openapi(spec: dict) -> list[dict]:
    out = []
    for path, ops in (spec.get("paths") or {}).items():
        ops = _resolve(spec, ops)
        for method, op in ops.items():
            if method not in METHODS or not isinstance(op, dict):
                continue
            if "requestBody" in op:  # OpenAPI 3
                content = _resolve(spec, op["requestBody"]).get("content") or {}
                schema = next(iter(content.values()), {}).get("schema")
            else:  # Swagger 2: parámetro in=body
                schema = next((p.get("schema") for p in op.get("parameters") or []
                               if isinstance(p, dict) and p.get("in") == "body"), None)
            body, required = _schema_fields(spec, schema)
            responses = op.get("responses") or {}
            ok = next((responses[k] for k in sorted(responses) if str(k).startswith("2")), {})
            ok = _resolve(spec, ok)
            rschema = ok.get("schema") or next(iter((ok.get("content") or {}).values()), {}).get("schema")
            resp, _ = _schema_fields(spec, rschema, "response")
            params = [p.get("name") for p in op.get("parameters") or [] if isinstance(p, dict) and p.get("in") != "body"]
            out.append({
                "group": (op.get("tags") or [""])[0], "name": op.get("operationId") or op.get("summary") or "",
                "method": method.upper(), "path": path,
                "description": _short(op.get("description") or op.get("summary"), 600),
                "body_fields": body, "body_example": "", "required": required,
                "response_fields": resp, "response_example": "", "params": [p for p in params if p],
            })
    return out


def parse(data: dict) -> tuple[str, list[dict]]:
    if "openapi" in data or "swagger" in data:
        kind = f"OpenAPI {data.get('openapi')}" if "openapi" in data else f"Swagger {data.get('swagger')}"
        eps = from_openapi(data)
    elif "item" in data and ("info" in data or isinstance(data.get("item"), list)):
        kind = "Postman"
        eps = from_postman(data)
    else:
        raise Unreadable("formato desconocido: ni colección de Postman ni OpenAPI/Swagger")
    if not eps:
        raise Unreadable(f"{kind} sin endpoints: un índice vacío no demuestra que nada exista")
    return kind, eps


def search(eps: list[dict], term: str) -> list[dict]:
    words = [w.lower() for w in term.split()]
    hits = []
    for e in eps:
        hay = " ".join([e["group"], e["name"], e["path"], e["description"]]).lower()
        if all(re.search(r"(?<![a-z0-9])" + re.escape(w), hay) for w in words):  # inicio de palabra
            hits.append(e)
    return hits


def print_endpoint(e: dict) -> None:
    print(f"── {e['method']} {e['path']}   «{e['name']}»  [{e['group'] or '-'}]")
    if e["description"]:
        print(f"   desc: {e['description']}")
    if e.get("params"):
        print(f"   parámetros: {', '.join(e['params'])}")
    if e["body_fields"]:
        req = set(e.get("required") or [])
        print("   cuerpo: " + ", ".join(f"{f}*" if f in req else f for f in e["body_fields"]))
    elif e["body_example"]:
        print(f"   cuerpo (ejemplo): {e['body_example']}")
    if e["response_fields"]:
        print(f"   respuesta: {', '.join(e['response_fields'])}")
    elif e["response_example"]:
        print(f"   respuesta (ejemplo): {e['response_example']}")


def write_out(out: Path, provider: str, source: Path, kind: str, eps: list[dict]) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    lines = [f"# Contrato de {provider} — índice generado", "",
             f"> Generado por `index_contract.py` desde `{source.name}` ({kind}, {len(eps)} endpoints).",
             "> No se edita: se regenera desde el contrato. Lo aprendido va en `gotchas.md`.",
             "> Consultar: `python3 .claude/skills/external-api-contract/index_contract.py <contrato> --search <palabra>`",
             ""]
    for group in sorted({e["group"] for e in eps}):
        lines += [f"## {group or '(sin grupo)'}", "", "| Método | Ruta | Nombre | Cuerpo | Respuesta |",
                  "|---|---|---|---|---|"]
        for e in (x for x in eps if x["group"] == group):
            req = set(e.get("required") or [])
            body = ", ".join(f"{f}*" if f in req else f for f in e["body_fields"][:12])
            resp = ", ".join(e["response_fields"][:12])
            cell = lambda s: str(s).replace("|", "\\|")  # noqa: E731
            lines.append(f"| {e['method']} | `{cell(e['path'])}` | {cell(e['name'])} | {cell(body)} | {cell(resp)} |")
        lines.append("")
    (out / "contract.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "contract-index.json").write_text(
        json.dumps({"provider": provider, "source": source.name, "kind": kind, "endpoints": eps},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    written += ["contract.md", "contract-index.json"]
    gotchas = out / "gotchas.md"
    if not gotchas.exists():
        gotchas.write_text(GOTCHAS_TEMPLATE.read_text(encoding="utf-8").replace("<proveedor>", provider),
                           encoding="utf-8")
        written.append("gotchas.md (nuevo, desde la plantilla)")
    return written


def self_test() -> int:
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"{'✓' if good else '✗'} {label}: {got!r}" + ("" if good else f" (esperado {want!r})"))

    postman = {"info": {"schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
               "item": [{"name": "Diary", "item": [
                   {"name": "Move Appointment", "request": {
                       "method": "POST", "url": {"raw": "{{apigeeURL}}/diary/:id/move", "path": ["diary", ":id", "move"]},
                       "description": "DiaryGStart es el número de franjas",
                       "body": {"raw": json.dumps({"DiaryGStart": 3, "DiaryGCabinetNum": 1})}},
                    "response": [{"body": json.dumps({"ok": True, "AppointmentID": 9})}]}]},
                   {"name": "Client history", "request": {"method": "GET", "url": "{{apigeeURL}}/client/:id/history"}}]}
    openapi = {"openapi": "3.0.3", "paths": {"/v1/calls/": {"post": {
        "operationId": "calls_create", "tags": ["calls"],
        "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Call"}}}},
        "responses": {"201": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Call"}}}}}}}},
        "components": {"schemas": {"Call": {"type": "object", "required": ["phone", "id"],
                                            "properties": {"phone": {}, "notes": {}, "id": {"readOnly": True},
                                                           "pin": {"writeOnly": True}}}}}}
    swagger = {"swagger": "2.0", "paths": {"/pets": {"get": {"operationId": "listPets",
               "parameters": [{"name": "limit", "in": "query"}], "responses": {"200": {"schema": {
                   "type": "array", "items": {"properties": {"id": {}, "name": {}}}}}}}}}}

    kind, eps = parse(postman)
    expect("1 Postman: endpoints", len(eps), 2)
    expect("2 Postman: la ruta pierde {{baseUrl}}", eps[0]["path"], "/diary/:id/move")
    expect("3 Postman: campos del cuerpo", eps[0]["body_fields"], ["DiaryGStart", "DiaryGCabinetNum"])
    expect("4 --search por dos palabras en cualquier orden", [e["name"] for e in search(eps, "history client")],
           ["Client history"])
    expect("5 --search sin coincidencias", search(eps, "prescription"), [])
    expect("5b --search por inicio de palabra («ove» no casa con «move»)", search(eps, "ove"), [])
    _, eps = parse(openapi)
    expect("6 OpenAPI: $ref resuelto, obligatorio marcado y sin readOnly en el cuerpo",
           (eps[0]["body_fields"], eps[0]["required"]), (["phone", "notes", "pin"], ["phone"]))
    expect("6b OpenAPI: sin writeOnly en la respuesta", eps[0]["response_fields"], ["phone", "notes", "id"])
    _, eps = parse(swagger)
    expect("7 Swagger 2: respuesta de una lista", eps[0]["response_fields"], ["id", "name"])
    for label, bad in [("8 formato desconocido → 2", {"hola": 1}), ("9 contrato sin endpoints → 2", {"openapi": "3.1.0", "paths": {}})]:
        try:
            parse(bad)
            expect(label, 0, 2)
        except Unreadable:
            expect(label, 2, 2)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "contract"
        kind, eps = parse(postman)
        write_out(out, "acme", Path("acme.json"), kind, eps)
        expect("10 escribe el índice y la plantilla de gotchas",
               sorted(p.name for p in out.iterdir()), ["contract-index.json", "contract.md", "gotchas.md"])
        (out / "gotchas.md").write_text("G-01 ya aprendido\n")
        write_out(out, "acme", Path("acme.json"), kind, eps)
        expect("11 regenerar NO pisa los gotchas", (out / "gotchas.md").read_text(), "G-01 ya aprendido\n")
    print("self-test:", "OK" if ok else "FALLA")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("contract", nargs="?", help="colección de Postman, OpenAPI o Swagger (JSON/YAML)")
    ap.add_argument("--search", help="palabras que deben aparecer en grupo, nombre, ruta o descripción")
    ap.add_argument("--provider", help="nombre del proveedor (con --out)")
    ap.add_argument("--out", help="carpeta donde dejar contract.md, contract-index.json y gotchas.md")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.contract:
        ap.error("falta el contrato (o --self-test)")
    try:
        kind, eps = parse(load(Path(a.contract)))
    except Unreadable as e:
        print(f"⛔ NO SE PUDO LEER: {e}", file=sys.stderr)
        return 2
    print(f"{kind}: {len(eps)} endpoints en {Path(a.contract).name}")
    if a.out:
        if not a.provider:
            ap.error("--out necesita --provider")
        for w in write_out(Path(a.out), a.provider, Path(a.contract), kind, eps):
            print(f"escrito {Path(a.out) / w.split(' ')[0]}" + (" (nuevo, desde la plantilla)" if "nuevo" in w else ""))
    if a.search:
        hits = search(eps, a.search)
        for e in hits:
            print_endpoint(e)
        if not hits:
            print(f"«{a.search}»: no aparece en ESTE contrato. Antes de decir «la API no lo soporta», prueba "
                  f"sinónimos y el dominio (p. ej. diary/agenda/appointment) y mira gotchas.md.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
