#!/usr/bin/env python3
"""Redactor de secretos COMPARTIDO: el único sitio donde se decide qué se tapa antes de escribir.

POR QUÉ EXISTE (SE-17 y la primera mitad de SE-4, sub-ola U.06). `audit-log.sh` guardaba cada comando
Bash tal cual en `~/.claude/audit/<proyecto>.jsonl`, y ese log es inmutable a propósito (cadena de
hashes): un `PGPASSWORD=…` que entra ya no se puede limpiar sin romper la cadena. La única forma de que
el log de evidencia no sea un almacén de credenciales es redactar EN ORIGEN, ANTES de calcular el hash.
Los tres hooks que escriben texto del agente o del Usuario (`audit-log.sh`, `capture-task.sh` vía
`tasks_registry.py`, `auto-progress-log.sh`) llaman a esta librería; ninguno lleva su propia regex.

QUÉ TAPA. Dos familias, y en las dos se conserva la CLAVE y se tapa solo el VALOR, para que el log siga
diciendo qué se hizo (`PGPASSWORD=[REDACTED:env-credential] psql …`):
  1. Formatos de proveedor (AWS, Anthropic, OpenAI, GitHub, Slack, Google, Stripe, Telegram, JWT,
     clave privada). Las regex NO se repiten aquí: se importan de `scan_secretos_diff.py`, que es el
     gate del pre-commit, para que lo que bloquea el commit y lo que se tapa en los logs sea lo mismo.
  2. Credenciales por CONTEXTO, que son las que aparecen en una línea de comandos y ningún formato de
     proveedor reconoce: variables de entorno con nombre de credencial (`PGPASSWORD=`, `DB_PASSWORD=`,
     `export API_TOKEN=`), opciones (`--password=x`, `--token x`), `mysql -p<pass>`, `sshpass -p`,
     `curl -u user:pass`, `Authorization: …`, `Bearer …`, `scheme://user:pass@host` y pares
     `"password": "valor"` de JSON/YAML.

QUÉ NO TAPA (límites declarados): un secreto sin nombre de credencial ni formato conocido
(`psql "host=x password=…"` sí; `./run.sh Kq7vP2mZr9w` no); uno partido en dos líneas o codificado; un
formato de proveedor nuevo. Las referencias (`$PGPASSWORD`, `${TOKEN}`, `<pass>`) no se tapan: no son
el valor. Tapar de más en un log es barato; por eso `redact()` NO aplica el filtro de «valor de
ejemplo» y `find_secrets()` (lo que usa el gate) SÍ, para no bloquear por un `xxxx` de documentación.

Fallo cerrado: si este módulo no se puede importar, los hooks no escriben el texto en claro, escriben
`[REDACTED:no-redactor]` (ver `audit-log.sh`).

Uso como CLI (para un hook en bash o para probar a mano):
    printf '%s' "$TEXTO" | python3 .claude/scripts/redactar.py          # texto redactado por stdout
    printf '%s' "$TEXTO" | python3 .claude/scripts/redactar.py --pii    # + correos, IBAN, DNI, teléfonos
    printf '%s' "$TEXTO" | python3 .claude/scripts/redactar.py --check  # exit 1 si había algo que tapar
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan_secretos_diff import EJEMPLO, PATRONES  # noqa: E402  (mismas regex que el pre-commit)

MARK = "[REDACTED:{}]"
# Nombres de variable / clave que dicen «esto es una credencial». PASS suelto entra por `PGPASS`,
# `SSHPASS`; a cambio tapa algún `TESTS_PASSED=3`, que en un log no cuesta nada.
_CRED_KEY = r"(?:PASSW(?:OR)?D|PASSWD|PASS|SECRET|TOKEN|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|AUTH_?KEY|CREDENTIALS?|_PWD)"
# Un valor «normal» de línea de comandos: hasta el siguiente espacio, comilla o separador de shell.
_VAL = r"""[^\s'"`;|&<>()]+"""
# El mismo valor admitiendo comillas: "con espacios" | 'simples' | suelto (tres grupos, en ese orden).
_QVAL = r"""(?:"([^"\n]+)"|'([^'\n]+)'|(""" + _VAL + r"))"
# Por encima de esto no se redacta el resto, se corta: las regex con prefijo de longitud variable son
# cuadráticas en una tirada larga sin espacios (medido por el verificador: 50 KB de «a.» → 33 s), y el
# hook de UserPromptSubmit es síncrono. Ningún hook escribe más de 260 caracteres de todos modos.
MAX_REDACT = 8000

# (tipo, regex, nº de grupo que contiene el VALOR a tapar). El orden importa: lo específico primero.
_CONTEXT_RULES: list[tuple[str, re.Pattern[str], int]] = [
    # scheme://user:pass@host → se conserva el usuario y el host
    ("url-credential", re.compile(r"(?<![a-z0-9+.-])[a-z][a-z0-9+.-]{0,30}://[^/\s:@\"']{1,200}:([^/\s@\"']{1,300})@", re.I), 1),
    # Authorization: Basic xxx / Authorization: token xxx / Authorization: xxx
    ("authorization-header", re.compile(r"(?i)\bauthorization\s*[:=]\s*(?:(?:basic|bearer|token|digest)\s+)?([^\s'\"]+)"), 1),
    ("bearer-token", re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._~+/=-]{8,})"), 1),
    # PGPASSWORD=x, export DB_PASSWORD="x", MY_API_KEY='x'
    # (el patrón arranca en la palabra clave, no en el principio del nombre: con un prefijo `[\w]*`
    # delante, cada posición del texto era un intento y una página HTML tardaba segundos)
    ("env-credential", re.compile(r"(" + _CRED_KEY + r"[A-Za-z0-9_]{0,40})=(?:\"([^\"]+)\"|'([^']+)'|(" + _VAL + r"))", re.I), 0),
    # --password=x, --password x, --api-key x, --token=x
    ("cli-credential", re.compile(r"(?i)(?<![\w-])--?[a-z0-9-]{0,30}(?:password|passwd|token|secret|api-?key|access-?key)[a-z0-9-]{0,30}(?:=|\s+)" + _QVAL), 0),
    # mysql/mysqldump/mariadb -pSECRETO (pegado; `mkdir -p` no entra porque exige el comando mysql)
    ("mysql-password", re.compile(r"(?i)\b(?:mysql\w*|mariadb\w*)\b[^\n|;&]{0,200}?\s-p" + _QVAL), 0),
    ("sshpass-password", re.compile(r"\bsshpass\s+-p\s*" + _QVAL), 0),
    # docker login -p x · redis-cli -a x
    ("docker-login-password", re.compile(r"\bdocker\s+login\b[^\n|;&]{0,200}?\s(?:-p|--password)[\s=]+" + _QVAL), 0),
    ("redis-password", re.compile(r"\bredis-cli\b[^\n|;&]{0,200}?\s-a\s+" + _QVAL), 0),
    # curl -u user:pass · -uuser:pass · --user user:pass · --user=user:pass
    ("basic-auth", re.compile(r"(?<![\w-])(?:-u\s*|--user[\s=]+)['\"]?[^\s:'\"]{1,100}:([^\s'\"]+)"), 1),
    # sk-/pk-/rk- con 16+ caracteres: más corto que el formato de OpenAI, pero en un prompt es una clave
    ("api-key-prefix", re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}"), 0),
    # "password": "x"  ·  password: x  ·  TOKEN = "x"  ·  contraseña = x  ·  'api_key' => 'x'
    ("assigned-credential", re.compile(r"""(?i)(?:passw(?:or)?d|passwd|contrase[ñn]a|secret|token|api[_-]?key|private[_-]?key)[a-z0-9_.-]{0,40}["']?\s*(?::|=>|=)\s*(?:"([^"]+)"|'([^']+)'|([^\s,'"}{]{4,}))"""), 0),
]

# Datos personales, solo con pii=True (lo usa el registro de peticiones, que guarda texto del Usuario).
_PII_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("iban", re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?\d{4}){4,7}\b")),
    ("dni", re.compile(r"(?i)\b(?:\d{8}[A-Z]|[XYZ]\d{7}[A-Z])\b")),
    ("phone", re.compile(r"(?<![\w.])(?:\+34[ ]?)?[6-9]\d{2}[ .-]?\d{3}[ .-]?\d{3}(?![\w.])")),
]

# `$X`, `${X}`, `$(cmd)`, `%(x)s`, `{{ x }}`, `<pass>` (la forma entera, no «empieza por <»)
_REFERENCE = re.compile(r"^(?:\$[\w{(]|%\(\w+\)s|\{\{.*\}\}$|<[\w .-]{1,40}>$)")
_BOOLISH = {"true", "false", "yes", "no", "on", "off", "none", "null", "0", "1"}

# Solo para el GATE (no para redactar): valores que en un documento o un parche son claramente otra
# cosa — una ruta, un color o un énfasis (`#6c6…`, `**`), una referencia o un nombre de código
# (`settings.OPENAI_API_KEY`, `max_tokens`), la variable siguiente de una línea (`KEY= OTRA=…`), una
# URL, una regex, una elipsis (`sk-lf-…`) o un valor de mentira en castellano (`sk-falsa-prueba`).
_NOT_A_SECRET = re.compile(
    r"""(?ix)^(?:[/~.#*]|https?:|[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)+[,;).]*$|[a-z_]+[,;).]*$
              |[a-z][a-z0-9_]*=|\s|.*[\[\]{}\\()|$\s])
        |…|fals[oa]|prueba|simulad|laborat|lab[-_]|experim|local[-_]|[-_]local|ficticio|inventad
        |no-se-usa|solo-""")
# Una línea sin ninguna de estas subcadenas no puede casar con ninguna regla: el gate se la salta
# sin pasarle las veinte regex (52 MB de .docs/ pasan de minutos a segundos).
_TRIGGER = re.compile(r"(?i)pass|secret|token|key|auth|bearer|://|sk-|gh[pousr]_|github_pat|xox|akia|asia|"
                      r"aiza|_live_|eyj|-----begin|\d{8,10}:|mysql|mariadb|-u\s|--user|contrase")


def _slug(kind: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kind.lower()).strip("-")


def _is_reference(value: str) -> bool:
    """Una referencia a la credencial (`$X`, `${X}`, `<pass>`, ya tapado) no es la credencial."""
    v = value.strip("\"'")
    return bool(not v or _REFERENCE.match(v) or v.startswith("[REDACTED") or v.lower() in _BOOLISH
                or v.startswith("/dev/"))


def _value_span(m: re.Match[str], group: int) -> tuple[int, int] | None:
    """Span del valor: el grupo pedido o, con group=0, el ÚLTIMO grupo que casó (las alternativas
    "entre comillas" | 'simples' | suelto van al final del patrón; el nombre, si se captura, va antes)."""
    if group:
        return m.span(group) if m.group(group) is not None else None
    for g in range(m.re.groups, 0, -1):
        if m.group(g) is not None:
            return m.span(g)
    return m.span() if not m.re.groups else None


def _iter_hits(text: str):
    """(tipo, inicio, fin) del VALOR de cada credencial, sin solaparse, en orden de aparición."""
    taken: list[tuple[int, int]] = []

    def free(a: int, b: int) -> bool:
        return all(b <= x or a >= y for x, y in taken)

    hits = []
    for kind, rx in PATRONES:
        if kind == "credenciales en una URL":
            continue  # la regla de contexto `url-credential` tapa solo la contraseña y deja el host
        for m in rx.finditer(text):
            if free(*m.span()):
                taken.append(m.span()); hits.append((_slug(kind), *m.span()))
    for kind, rx, group in _CONTEXT_RULES:
        for m in rx.finditer(text):
            span = _value_span(m, group)
            if not span or not free(*span) or _is_reference(text[span[0]:span[1]]):
                continue
            taken.append(span); hits.append((kind, *span))
    return sorted(hits, key=lambda h: h[1])


def _replace(text: str, hits) -> str:
    out, last = [], 0
    for kind, a, b in hits:
        out.append(text[last:a]); out.append(MARK.format(kind)); last = b
    out.append(text[last:])
    return "".join(out)


def redact(text: str, pii: bool = False) -> str:
    """Devuelve `text` con el VALOR de cada credencial sustituido por `[REDACTED:<tipo>]`.

    Nunca lanza: ante cualquier error devuelve un marcador entero, no el texto en claro.
    """
    if not text:
        return text or ""
    try:
        cut = len(text) > MAX_REDACT
        if cut:
            text = text[:MAX_REDACT]
        out = _replace(text, _iter_hits(text)) + (MARK.format("truncated") if cut else "")
        if pii:
            for kind, rx in _PII_RULES:
                out = rx.sub(MARK.format(kind), out)
        return out
    except Exception:  # defensive: un hook no puede caerse ni escribir en claro por un bug aquí
        return MARK.format("redactor-error")


def find_secrets(text: str) -> list[dict]:
    """Lo que el GATE cuenta como secreto (tipo y longitud, sin ningún carácter del valor): igual que `redact`, pero sin valores de aspecto de ejemplo
    (`xxxx`, `your_…`, `changeme`) ni palabras sueltas, para no bloquear por la documentación."""
    found = []
    if not text or not _TRIGGER.search(text):
        return found
    for kind, a, b in _iter_hits(text):
        value = text[a:b].strip("\"'")
        if kind != "clave-privada" and (EJEMPLO.search(value) or len(value) < 6
                                         or _NOT_A_SECRET.search(value)):
            continue
        found.append({"kind": kind, "length": len(value)})  # nunca un trozo del valor
    return found


def main(argv: list[str]) -> int:
    data = sys.stdin.read()
    if "--check" in argv:
        return 1 if find_secrets(data) else 0
    sys.stdout.write(redact(data, pii="--pii" in argv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
