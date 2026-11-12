#!/usr/bin/env python3
"""check_pii_logs.py — datos personales que entran EN CLARO en logs, errores, trazas y cassettes.

De dónde sale (SE-36, SE-59 y SE-D5; sub-ola 2.30 de la revisión integral, 2026-10-27). En EvoPreven
el log de auditoría guardaba `str(instance)` con nombres y los cuerpos POST con campos clínicos, y
la pantalla los ocultaba al mostrarlos: redactar al mostrar no protege el dato guardado, que sigue en
la base de logs, en sus copias y al alcance de quien la lea. Nadie lo cazó en revisión porque ni
`sara-salud-datos`, ni `priya-privacy-auditor`, ni `code-review-gate` lo buscaban. Este script es
la capa determinista que los tres corren; ellos juzgan lo que encuentra.

QUÉ BUSCA (cada regla dice su porqué en la salida):

    L1  logger que serializa un objeto entero: str(x)/repr(x)/f"{x}"/vars(x)/x.__dict__/model_to_dict
    L2  cuerpo de la petición en un log o guardado en un modelo de log (request.body/.data/.POST/.json)
    E1  sentry_sdk.init sin before_send, sin include_local_variables=False, o con send_default_pii=True
        (GlitchTip usa el mismo SDK: su filtro por defecto solo cubre contraseñas, tokens, cookies e IP)
    T1  cliente de Langfuse sin máscara en origen (`mask=`). Langfuse OSS no registra quién LEE una traza
    C1  cassette de LLM (vcrpy) con un dato personal o con la cabecera de autorización sin filtrar
    C2  configuración de vcrpy sin filter_headers / before_record_request
    D1  fichero de log (.log/.jsonl/.ndjson) con un dato personal: email, DNI/NIE con letra válida,
        teléfono +34, IBAN, o un campo clínico con valor

QUÉ NO HACE. No sabe si el dato es real o sintético: un email de `example.com`/`.test` se ignora y
todo lo demás se reporta. No sigue el flujo de datos: si el objeto se pasa a otra función que lo
loguea, no lo ve. No mira JavaScript. Un 0 dice «no encontré estas formas», no «no hay PII».

CÓMO SE USA

    python3 .claude/scripts/check_pii_logs.py <ruta> [<ruta>…]   # ficheros o carpetas
    python3 .claude/scripts/check_pii_logs.py $(git diff --name-only --diff-filter=d develop...)   # solo el diff
    python3 .claude/scripts/check_pii_logs.py <ruta> --health    # todo hallazgo pasa a BLOQUEANTE
    python3 .claude/scripts/check_pii_logs.py <ruta> --json
    python3 .claude/scripts/check_pii_logs.py --self-test        # se ve fallar con PII plantada
    python3 .claude/scripts/check_pii_logs.py --write-fixture <dir>   # esa PII, en disco, para un auditor

`--health` se activa solo si encuentra `cumplimiento-salud.yaml|yml|json` subiendo desde la ruta: es
la marca de «proyecto con datos de salud» que deja la skill `cumplimiento-salud`.

Salida: 0 sin hallazgos · 1 hay hallazgos · 2 no se pudo medir (la ruta no existe o no había ningún
fichero que mirar). Un alcance vacío NO es «limpio» (`rules/verification.md` §El instrumento que no
puede medir debe abortar).
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
import tempfile

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "_archive"}
LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
LOGGER_NAMES = re.compile(r"(^|_)(log|logger|logging|audit|auditlog)s?$", re.I)
DUMP_CALLS = {"str", "repr", "vars", "model_to_dict", "serialize"}
REQUEST_ATTRS = {"body", "data", "POST", "json", "form", "GET"}
# «Log» en CamelCase o «_log»: así `ActionLog` y `action_log` cuentan y `Catalog` o `Blog` no.
LOG_SINKS = re.compile(r"(Log|_log|^log|\.log|[Aa]udit|[Hh]istor|[Tt]race|[Ee]vent)")
TEXT_LOG_EXT = (".log", ".jsonl", ".ndjson")
CASSETTE_EXT = (".yaml", ".yml", ".json")

EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[a-z]{2,}", re.I)
SAFE_EMAIL = re.compile(r"@(([\w-]+\.)*example\.(com|org|net)|[\w.-]+\.(test|example|invalid|local))$",
                        re.I)
DNI = re.compile(r"\b(\d{8})([A-Z])\b")
NIE = re.compile(r"\b([XYZ])(\d{7})([A-Z])\b")
PHONE = re.compile(r"(?:\+34|0034)[\s.-]?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b")
IBAN = re.compile(r"\bES\d{2}(?:\s?\d{4}){5}\b")
CLINICAL_FIELD = re.compile(
    r"[\"']?(diagnos\w*|diagnóstico|tratamiento|medicaci[oó]n|alergias?|patolog[ií]a\w*|"
    r"analitica|analítica|baja_medica|sintomas|síntomas|historia_clinica)[\"']?\s*[:=]\s*[\"']?\w",
    re.I)
AUTH_HEADER = re.compile(r"^\s*-?\s*[\"']?(authorization|x-api-key|api[_-]key)[\"']?\s*:\s*(.+)$",
                         re.I | re.M)
DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

RULES = {
    "L1": "logger que serializa un objeto entero: el `__str__` de un modelo suele llevar nombres, y "
          "lo que entra al log queda en claro en la base de logs y sus copias",
    "L2": "cuerpo de la petición en un log: con datos de salud son campos clínicos en claro. El log "
          "guarda REFERENCIAS (id, campo), nunca valores",
    "E1": "SDK de errores (Sentry/GlitchTip) que puede mandar variables locales o PII: hace falta "
          "`before_send` e `include_local_variables=False`, y nunca `send_default_pii=True`",
    "T1": "Langfuse sin máscara en origen: la conversación entra entera y Langfuse OSS no registra "
          "quién la lee. Con datos de salud, la máscara (`mask=`) va antes de conectar",
    "C1": "cassette de LLM con un dato personal o con la clave de API: una cassette grabada de una "
          "conversación real es ese dato versionado en git. Solo conversaciones sintéticas",
    "C2": "vcrpy sin `filter_headers` ni `before_record_request`: la próxima grabación se lleva la "
          "cabecera de autorización y el prompt sin redactar",
    "D1": "fichero de log con un dato personal en claro",
}


def _dni_ok(num, letter):
    return DNI_LETTERS[int(num) % 23] == letter


def _nie_ok(prefix, num, letter):
    return DNI_LETTERS[int(str("XYZ".index(prefix)) + num) % 23] == letter


def pii_in_text(line):
    """Los datos personales que reconoce en una línea de texto, como lista de etiquetas."""
    hits = []
    for m in EMAIL.finditer(line):
        if not SAFE_EMAIL.search(m.group(0)):
            hits.append("email")
    hits += ["DNI" for m in DNI.finditer(line) if _dni_ok(*m.groups())]
    hits += ["NIE" for m in NIE.finditer(line) if _nie_ok(*m.groups())]
    hits += ["teléfono" for _ in PHONE.finditer(line)]
    hits += ["IBAN" for _ in IBAN.finditer(line)]
    hits += ["campo clínico" for _ in CLINICAL_FIELD.finditer(line)]
    return hits


def _name(node):
    """Nombre punteado de una expresión (`self.logger.info` → 'self.logger.info')."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return _name(node.func)
    return ""


def _is_log_call(call):
    if not isinstance(call.func, ast.Attribute) or call.func.attr not in LOG_METHODS:
        return False
    owner = _name(call.func.value).split(".")[-1]
    return bool(LOGGER_NAMES.search(owner))


def _is_request_payload(node):
    return (isinstance(node, ast.Attribute) and node.attr in REQUEST_ATTRS
            and _name(node.value).split(".")[-1] in ("request", "req"))


OBJECT_NAMES = {"instance", "obj", "object", "patient", "paciente", "worker", "trabajador",
                "user", "employee", "record", "model"}
# str(exc) en un log es el mensaje de la excepción, no un modelo: contarlo como volcado era el
# falso positivo más frecuente (verificador de la 2.30).
EXCEPTION_NAMES = {"e", "ex", "exc", "err", "error", "exception"}


def _last(node):
    return _name(node).split(".")[-1]


def _dumps_object(node):
    """¿La expresión vuelca un objeto entero? str(x), repr(x), f"{x}", vars(x), x.__dict__…"""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and _last(sub.func) in DUMP_CALLS and sub.args:
            arg = sub.args[0]
            if not isinstance(arg, (ast.Constant, ast.Call)) and _last(arg) not in EXCEPTION_NAMES:
                return True
        if isinstance(sub, ast.Attribute) and sub.attr == "__dict__":
            return True
        if isinstance(sub, ast.FormattedValue) and isinstance(sub.value, (ast.Name, ast.Attribute)):
            if _last(sub.value) in OBJECT_NAMES:
                return True
    return False


def _bare_object(node):
    """`logger.info("guardado %s", instance)`: logging llama a `__str__` por su cuenta. Es la forma
    más común de volcar un modelo y la primera versión no la veía (verificador de la 2.30)."""
    return isinstance(node, (ast.Name, ast.Attribute)) and _last(node) in OBJECT_NAMES


def scan_python(path, src):
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [dict(rule="ERR", file=path, line=e.lineno or 0, text="no se pudo parsear")]
    lines = src.splitlines()

    def add(rule, node, extra=""):
        ln = getattr(node, "lineno", 0)
        out.append(dict(rule=rule, file=path, line=ln,
                        text=(lines[ln - 1].strip() if 0 < ln <= len(lines) else "") + extra))

    vcr_used = "vcr" in src
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fname = _name(node.func)
        args = list(node.args) + [k.value for k in node.keywords]
        if _is_log_call(node):
            if any(_dumps_object(a) or _bare_object(a) for a in args):
                add("L1", node)
            if any(_is_request_payload(s) for a in args for s in ast.walk(a)):
                add("L2", node)
        elif fname.split(".")[-1] in ("create", "insert_one", "insert_many") \
                and LOG_SINKS.search(".".join(fname.split(".")[:-1])):
            # AuditLog.objects.create(body=request.data) · db.action_log.insert_one({...})
            if any(_is_request_payload(s) for a in args for s in ast.walk(a)):
                add("L2", node)
            elif any(_dumps_object(a) for a in args):
                add("L1", node)
        if fname in ("sentry_sdk.init", "init") and ("sentry" in src):
            kw = {k.arg: k.value for k in node.keywords if k.arg}
            if fname == "init" and not kw.get("dsn"):
                continue
            problems = []
            if "before_send" not in kw:
                problems.append("sin before_send")
            ilv = kw.get("include_local_variables")
            if not (isinstance(ilv, ast.Constant) and ilv.value is False):
                problems.append("include_local_variables no es False")
            sdp = kw.get("send_default_pii")
            if isinstance(sdp, ast.Constant) and sdp.value is True:
                problems.append("send_default_pii=True")
            if problems:
                add("E1", node, f"  ⟵ {', '.join(problems)}")
        if fname.split(".")[-1] == "Langfuse" and not any(k.arg == "mask" for k in node.keywords):
            add("T1", node)
        if vcr_used and fname.split(".")[-1] in ("VCR", "use_cassette"):
            kws = {k.arg for k in node.keywords}
            if not kws & {"filter_headers", "before_record_request"}:
                add("C2", node)
    return out


def scan_text(path, src, rule):
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        hits = pii_in_text(line)
        if rule == "C1":
            m = AUTH_HEADER.match(line)
            if m and not re.search(r"DUMMY|REDACTED|FILTERED|\*\*\*|<.*>|^\s*\[\s*\]\s*$|^\s*$",
                                   m.group(2), re.I):
                hits.append("cabecera de autorización")
        if hits:
            out.append(dict(rule=rule, file=path, line=i, text=f"{', '.join(sorted(set(hits)))}"))
    return out


def _is_cassette(path, src):
    return ("cassette" in path.lower() or "interactions:" in src[:2000]) and \
        path.endswith(CASSETTE_EXT)


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in files:
                    yield os.path.join(root, f)


def find_health_marker(paths):
    for p in paths:
        cur = os.path.abspath(p if os.path.isdir(p) else os.path.dirname(p) or ".")
        while True:
            if any(os.path.exists(os.path.join(cur, n)) for n in
                   ("cumplimiento-salud.yaml", "cumplimiento-salud.yml", "cumplimiento-salud.json")):
                return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    return None


def scan(paths):
    findings, scanned = [], 0
    for f in iter_files(paths):
        low = f.lower()
        if not (low.endswith(".py") or low.endswith(TEXT_LOG_EXT) or low.endswith(CASSETTE_EXT)):
            continue
        try:
            src = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        scanned += 1
        if low.endswith(".py"):
            findings += scan_python(f, src)
        elif low.endswith(TEXT_LOG_EXT):
            findings += scan_text(f, src, "D1")
        elif _is_cassette(f, src):
            findings += scan_text(f, src, "C1")
    return findings, scanned


# ─── autoprueba ────────────────────────────────────────────────────────────────────────────────

_PLANTED = {
    "app/audit.py": '''import logging
logger = logging.getLogger(__name__)
def on_save(instance, request):
    logger.info("guardado %s", str(instance))
    logger.info(f"cambio en {instance}")
    logger.info("borrado %s", instance)
    audit_logger.warning("POST %s", request.data)
    ActionLog.objects.create(user=request.user, body=request.body)
''',
    "app/settings_errors.py": '''import sentry_sdk
sentry_sdk.init(dsn="https://k@glitchtip.local/1", send_default_pii=True)
''',
    "app/tracing.py": '''from langfuse import Langfuse
lf = Langfuse(host="http://127.0.0.1:3100")
''',
    "tests/conftest.py": '''import vcr
rec = vcr.VCR(cassette_library_dir="tests/cassettes")
''',
    "tests/cassettes/chat.yaml": '''interactions:
- request:
    body: '{"messages":[{"role":"user","content":"soy Marta Ruiz, mi DNI es 12345678Z"}]}'
    headers:
      authorization: Bearer sk-live-abcdef0123456789
''',
    "logs/app.log": '''2026-10-27 10:00 INFO login marta.ruiz@gmail.com desde +34 612 345 678
2026-10-27 10:01 INFO {"worker": 41, "diagnostico": "hipertensión"}
''',
}

_CLEAN = {
    "app/audit.py": '''import logging
logger = logging.getLogger(__name__)
def on_save(instance, request):
    logger.info("guardado %s#%s", instance._meta.label, instance.pk)
    logger.error("fallo al guardar: %s", str(exc))
    ActionLog.objects.create(user_id=request.user.pk, model="worker", object_id=instance.pk)
''',
    "app/settings_errors.py": '''import sentry_sdk
sentry_sdk.init(dsn="https://k@glitchtip.local/1", before_send=scrub,
                include_local_variables=False)
''',
    "app/tracing.py": '''from langfuse import Langfuse
lf = Langfuse(host="http://127.0.0.1:3100", mask=mask_pii)
''',
    "tests/conftest.py": '''import vcr
rec = vcr.VCR(filter_headers=["authorization", "x-api-key"], before_record_request=scrub)
''',
    "tests/cassettes/chat.yaml": '''interactions:
- request:
    body: '{"messages":[{"role":"user","content":"soy Paciente Sintético, prueba@example.test"}]}'
    headers:
      authorization: REDACTED
''',
    "logs/app.log": '''2026-10-27 10:00 INFO login user_id=41 desde 127.0.0.1
2026-10-27 10:01 INFO {"worker": 41, "field": "diagnosis", "action": "read"}
''',
}

_EXPECTED = {"L1": 3, "L2": 2, "E1": 1, "T1": 1, "C1": 2, "C2": 1, "D1": 2}


def _write(root, files):
    for rel, txt in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(txt)


def self_test():
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, _PLANTED)
        found, n = scan([tmp])
        counts = {}
        for f in found:
            counts[f["rule"]] = counts.get(f["rule"], 0) + 1
        for rule, expected in _EXPECTED.items():
            passed = counts.get(rule, 0) >= expected
            ok &= passed
            print(f"  {'✅' if passed else '❌'} {rule} plantado: {counts.get(rule, 0)} de ≥{expected}")
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, _CLEAN)
        found, n = scan([tmp])
        passed = not found and n == len(_CLEAN)
        ok &= passed
        print(f"  {'✅' if passed else '❌'} control limpio: {len(found)} hallazgos en {n} ficheros"
              + "".join(f"\n       {f['rule']} {os.path.relpath(f['file'], tmp)}:{f['line']}"
                        for f in found))
    with tempfile.TemporaryDirectory() as tmp:
        found, n = scan([tmp])
        passed = n == 0
        ok &= passed
        print(f"  {'✅' if passed else '❌'} alcance vacío: {n} ficheros → el main sale con 2, no con 0")
    passed = _dni_ok("12345678", "Z") and not _dni_ok("12345678", "A")
    ok &= passed
    print(f"  {'✅' if passed else '❌'} letra del DNI validada (12345678Z sí, 12345678A no)")
    print(f"\nautoprueba: {'OK' if ok else 'FALLA'}")
    return 0 if ok else 1


def main(argv):
    if "--self-test" in argv:
        return self_test()
    if "--write-fixture" in argv:
        # El mismo proyecto con PII plantada de la autoprueba, en disco, para poner delante de un
        # auditor (Sara, Priya, code-review-gate) y ver si lo marca. Texto inventado.
        i = argv.index("--write-fixture")
        dst = argv[i + 1] if len(argv) > i + 1 else ""
        if not dst or (os.path.exists(dst) and os.listdir(dst)):
            print("uso: --write-fixture <carpeta vacía o inexistente>", file=sys.stderr)
            return 2
        _write(dst, _PLANTED)
        print(f"OK {dst}: {len(_PLANTED)} ficheros con PII plantada (esperado: {_EXPECTED})")
        return 0
    as_json = "--json" in argv
    health = "--health" in argv
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print(__doc__.split("CÓMO SE USA")[1].split("Salida:")[0].rstrip())
        return 2
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        print(f"⛔ no existe: {', '.join(missing)} — no se ha medido nada", file=sys.stderr)
        return 2
    marker = None if health else find_health_marker(paths)
    health = health or bool(marker)
    findings, scanned = scan(paths)
    if scanned == 0:
        print("⛔ ningún .py, .log/.jsonl ni cassette en el alcance: no se ha medido nada (exit 2)",
              file=sys.stderr)
        return 2
    sev = "BLOQUEANTE" if health else "HALLAZGO"
    if as_json:
        print(json.dumps({"scanned": scanned, "health": health, "severity": sev,
                          "findings": findings}, ensure_ascii=False, indent=1))
        return 1 if findings else 0
    print(f"\nPII en logs, errores, trazas y cassettes · {scanned} ficheros"
          + (f" · proyecto con datos de salud ({marker or '--health'})" if health else ""))
    for rule in sorted({f["rule"] for f in findings}):
        print(f"\n  {rule} · {RULES.get(rule, '')}")
        for f in (x for x in findings if x["rule"] == rule):
            print(f"     {sev} {f['file']}:{f['line']}  {f['text'][:110]}")
    if findings:
        print(f"\n✗ {len(findings)} hallazgo(s). Un hallazgo es un candidato: el auditor mira el "
              "Intent antes de condenar (`rules/verdict-contract.md`).")
        return 1
    print("\n✓ ninguna de estas formas. No es «no hay PII»: ver QUÉ NO HACE en la cabecera.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
