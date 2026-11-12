#!/usr/bin/env python3
"""avisar.py — el aviso al Usuario por el canal que SÍ existe en esta máquina: Telegram.

    python3 .claude/scripts/avisar.py "DONE proyecto: tarea"   # manda el texto; exit 1 si no llega
    python3 .claude/scripts/avisar.py --simulacro "texto"      # qué mandaría y a cuántos, sin red
    python3 .claude/scripts/avisar.py --comprobar [--red]      # ¿hay canal? (--red: getMe)
    python3 .claude/scripts/avisar.py --hook --proyecto <dir>  # lo llama hooks/notify-telegram.sh

## Por qué existe (MO-14, sub-ola 2.20)

La regla crítica 4 de `CLAUDE.md` manda notificar al terminar o al bloquearse. El hook que lo
hacía, `notify-gateway.sh`, llamaba a una herramienta de aviso que no está instalada aquí y salía
en silencio: un aviso registrado que no avisaba a nadie (retirado a `_archive/2026-10-20/hooks/`).
El plugin `telegram` sí está operativo; este script manda por la API de bots de Telegram con **su**
token y **su** lista de acceso, leídos y nunca escritos.

## Qué lee y qué no toca

- El token: `TELEGRAM_BOT_TOKEN` del entorno o, si no está, la línea `TELEGRAM_BOT_TOKEN=` de
  `$TELEGRAM_STATE_DIR/.env` (por defecto `~/.claude/channels/telegram/.env`, el del plugin). No
  carga ninguna otra variable de ese fichero.
- A quién: `TL_AVISO_CHAT` (ids separados por comas) o, si no está, `allowFrom` de `access.json`
  del plugin: los mismos chats a los que el plugin deja contestar. **No** escribe `access.json`, no
  aprueba pairings y no llama a `getUpdates` (no compite con el sondeo del plugin).
- El token **no sale nunca**: va solo en la URL dentro del proceso (ni en `argv`, ni en stdout, ni
  en stderr, ni en el registro). Cualquier texto de error pasa por `_limpia()` antes de salir.

## Fallar sin romper el turno, y sin callar

En modo `--hook` el script sale SIEMPRE con 0 (un Stop no debe bloquear ni reabrir el turno) y, si
el aviso no llega, lo dice con `systemMessage`: en un hook síncrono Claude Code lo enseña al Usuario
(en uno `async` solo le llegaría a Claude en el turno siguiente — doc de hooks, «How async hooks
execute» —, por eso el hook ya no es `async`). Cada intento queda en
`${XDG_STATE_HOME:-~/.local/state}/tl-aviso/aviso.log`, fuera del repo.

Solo avisa en la **transición** de `PROGRESS.json` a `completed` (DONE) o a `blocked` (BLOCKED), una
vez por estado: la primera vez que ve un proyecto apunta el estado y no manda nada (activar el hook
no dispara un aviso viejo). `TL_AVISO=off` lo apaga del todo.

Pruebas: `TL_AVISO_API` cambia la URL base de la API (un servidor falso en 127.0.0.1); así se probó
sin mandar ningún mensaje real (`_archive/2026-10-20/medicion-2.20/`).
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.telegram.org"
LIMITE = 3500  # Telegram corta en 4096; dejamos margen para el prefijo
TIMEOUT = 5.0  # por petición
PLAZO = 10.0  # para todo el envío: el hook tiene 15 s y tiene que poder escribir el estado
ESTADOS_QUE_AVISAN = {"completed": "DONE", "done": "DONE", "blocked": "BLOCKED"}
TOKEN_RE = re.compile(r"\d{5,}:[A-Za-z0-9_-]{20,}")


def _dir_estado() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local",
                                                              "state")
    return Path(base) / "tl-aviso"


def _dir_plugin() -> Path:
    if os.environ.get("TELEGRAM_STATE_DIR"):
        return Path(os.environ["TELEGRAM_STATE_DIR"])
    conf = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return Path(conf) / "channels" / "telegram"


def _token() -> str | None:
    """El token del bot: el entorno gana (como en el plugin); si no, su `.env`. Nunca se imprime."""
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        return os.environ["TELEGRAM_BOT_TOKEN"].strip()
    try:
        texto = (_dir_plugin() / ".env").read_bytes().decode("utf-8")
    except (OSError, ValueError):  # ilegible (también un byte que no es UTF-8) = no hay token
        return None
    for linea in texto.splitlines():
        m = re.match(r"^\s*TELEGRAM_BOT_TOKEN\s*=\s*(.*?)\s*$", linea)
        if m:
            return m.group(1).strip().strip("'\"") or None
    return None


def _destinos() -> list[str]:
    """A quién se avisa: `TL_AVISO_CHAT` o la `allowFrom` del plugin (solo lectura)."""
    if os.environ.get("TL_AVISO_CHAT"):
        return [c.strip() for c in os.environ["TL_AVISO_CHAT"].split(",") if c.strip()]
    try:
        acceso = json.loads((_dir_plugin() / "access.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    lista = acceso.get("allowFrom") if isinstance(acceso, dict) else None
    if isinstance(lista, (str, int)):  # un id suelto, no una lista: no se recorre letra a letra
        lista = [lista]
    return [str(c).strip() for c in lista or [] if isinstance(c, (str, int)) and str(c).strip()]


def _limpia(texto: str, token: str | None) -> str:
    """Quita el token de cualquier texto que vaya a salir (errores de red, cuerpos de respuesta)."""
    if token:
        texto = texto.replace(token, "<token>")
    return TOKEN_RE.sub("<token>", texto)


def _registra(linea: str) -> Path:
    """Una línea por intento en el registro, fuera del repo. Si no se puede escribir, se sigue."""
    ruta = _dir_estado() / "aviso.log"
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {linea}\n")
    except OSError:
        pass
    return ruta


def _llamada(token: str, metodo: str, datos: dict | None, plazo: float = TIMEOUT) -> dict:
    """POST (o GET sin datos) a la API de bots. Devuelve el JSON; cualquier fallo sale como
    RuntimeError con el texto ya limpio (sin token)."""
    base = os.environ.get("TL_AVISO_API", API).rstrip("/")
    if not re.match(r"^https?://", base):
        raise RuntimeError(f"TL_AVISO_API no es una URL http(s): {base!r}")
    url = f"{base}/bot{token}/{metodo}"
    cuerpo = json.dumps(datos).encode() if datos is not None else None
    req = urllib.request.Request(url, data=cuerpo, method="POST" if cuerpo else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=max(0.5, plazo)) as r:
            resp = json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        detalle = ""
        try:
            detalle = json.loads(e.read().decode("utf-8", "replace")).get("description", "")
        except Exception:  # noqa: BLE001 — el cuerpo del error es opcional
            pass
        raise RuntimeError(_limpia(f"HTTP {e.code} {detalle}".strip(), token)) from None
    except Exception as e:  # noqa: BLE001 — red, protocolo (BadStatusLine…), JSON: «no llegó»
        motivo = getattr(e, "reason", None) or f"{type(e).__name__}: {e}"
        raise RuntimeError(_limpia(f"sin respuesta de Telegram: {motivo}", token)) from None
    if not isinstance(resp, dict) or not resp.get("ok"):
        desc = resp.get("description", resp) if isinstance(resp, dict) else resp
        raise RuntimeError(_limpia(f"Telegram dijo que no: {desc}", token))
    return resp


def enviar(texto: str, fin: float | None = None) -> tuple[bool, str]:
    """Manda `texto` a todos: (True, resumen) si llegó a todos; (False, motivo) si no. Todo el
    envío cabe en PLAZO segundos: con la API colgada, el destino que no cabe cuenta como fallo."""
    token = _token()
    if not token:
        return False, f"falta el token del bot (TELEGRAM_BOT_TOKEN o {_dir_plugin()}/.env)"
    destinos = _destinos()
    if not destinos:
        return False, (f"sin destinatarios (TL_AVISO_CHAT o allowFrom de "
                       f"{_dir_plugin()}/access.json)")
    texto = texto if len(texto) <= LIMITE else texto[: LIMITE - 1] + "…"
    fin = fin if fin is not None else time.monotonic() + PLAZO  # el hook pasa uno para todo
    fallos = []
    for chat in destinos:
        queda = fin - time.monotonic()
        if queda <= 0.5:
            fallos.append(f"sin tiempo para avisar a {chat} (plazo de {PLAZO:.0f} s agotado)")
            continue
        try:
            _llamada(token, "sendMessage",
                     {"chat_id": chat, "text": texto, "disable_web_page_preview": True},
                     min(TIMEOUT, queda))
        except RuntimeError as e:
            fallos.append(str(e))
    if fallos:
        return False, f"{len(fallos)} de {len(destinos)} destino(s) sin aviso: {fallos[0]}"
    return True, f"enviado a {len(destinos)} destino(s)"


def _estado_de(progreso: dict) -> str:
    return str(progreso.get("status") or "").strip().lower()


def _mensaje_de(progreso: dict, proyecto: str) -> str | None:
    """El texto del aviso según el estado de PROGRESS.json (el formato de notify-gateway.sh)."""
    estado = _estado_de(progreso)
    if estado not in ESTADOS_QUE_AVISAN:
        return None
    tarea = str(progreso.get("task") or "sin tarea")
    lista = progreso.get("checklist") if isinstance(progreso.get("checklist"), list) else []
    hechas = sum(1 for i in lista if isinstance(i, dict) and i.get("done") is True)
    cuenta = f" ({hechas}/{len(lista)})" if lista else ""
    if ESTADOS_QUE_AVISAN[estado] == "BLOCKED":
        notas = progreso.get("notes") if isinstance(progreso.get("notes"), list) else []
        nota = str(notas[-1]) if notas else "sin detalles"
        return f"BLOCKED {proyecto}: {tarea}{cuenta} — {nota}"
    return f"DONE {proyecto}: {tarea}{cuenta} ✅"


def _vigilados(raiz: Path, progreso: dict) -> dict[str, dict]:
    """Qué estados se vigilan. Un PROGRESS.json «de sesión» es uno (clave «_»). Uno que es el
    ÍNDICE de planes (`progress_index.py`: lleva `planes[]`) vale `in_progress` mientras haya dos
    planes vivos, así que ahí se vigila el PROGRESS.json de cada plan, leído de su `ruta`."""
    planes = progreso.get("planes")
    if not isinstance(planes, list):
        return {"_": progreso}
    out = {}
    for p in planes:
        if not isinstance(p, dict) or not p.get("plan"):
            continue
        propio = None
        ruta = p.get("ruta")
        if isinstance(ruta, str) and not ruta.startswith("/") and ".." not in ruta:
            try:
                propio = json.loads((raiz / ruta).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                propio = None
        out[str(p["plan"])] = propio if isinstance(propio, dict) else p
    return out


def _decide(raiz: Path, nombre: str, previo: dict | None) -> tuple[dict, list[str]] | None:
    """Las firmas de ahora y los textos a mandar (solo transiciones, nunca la primera vez). None si
    `PROGRESS.json` no se puede leer (eso lo avisa validate-progress.sh)."""
    try:
        progreso = json.loads((raiz / "PROGRESS.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(progreso, dict):
        return None
    firmas, textos = {}, []
    antes = (previo or {}).get("firmas") or {}
    vieja = bool((previo or {}).get("_vieja"))  # marca de 91271561: su firma no llevaba el texto

    def comparable(firma: str) -> str:
        return "|".join(firma.split("|")[:2]).lower() if vieja else firma

    for clave, datos in _vigilados(raiz, progreso).items():
        quien = nombre if clave == "_" else f"{nombre} · {clave}"
        texto = _mensaje_de(datos, quien)
        firmas[clave] = f"{_estado_de(datos)}|{datos.get('task')}|{texto or ''}"
        if (previo is not None and clave in antes and texto
                and comparable(antes[clave]) != comparable(firmas[clave])):
            textos.append(texto)
    return firmas, textos


class _Ilegible(Exception):
    """PROGRESS.json no se puede leer: no hay nada que decidir (y se conservan las firmas)."""


def modo_hook(proyecto: str) -> int:
    """Stop: decide si toca avisar, avisa y, si falla, lo dice con systemMessage. Siempre exit 0,
    y pase lo que pase (también un error inesperado) deja el estado escrito y lo dice."""
    try:
        sys.stdin.read()  # el JSON del evento: no hace falta, pero no se deja la tubería a medias
    except (OSError, ValueError):
        pass
    if os.environ.get("TL_AVISO", "").lower() == "off":
        return 0
    raiz = Path(proyecto)
    if not (raiz / "PROGRESS.json").is_file():
        return 0  # sin PROGRESS.json: lo avisa validate-progress.sh, no este hook
    nombre = raiz.name
    marca = _dir_estado() / f"{hashlib.sha1(proyecto.encode()).hexdigest()[:16]}.json"
    salida = None
    try:
        marca.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(marca, os.O_RDWR | os.O_CREAT, 0o600)
    except OSError as e:
        print(json.dumps({"systemMessage": f"⚠ aviso por Telegram: no puedo guardar el estado "
                                           f"({e})"}, ensure_ascii=False))
        return 0
    with os.fdopen(fd, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # dos sesiones en el mismo repo no mandan el aviso dos veces
        try:
            previo = json.loads(f.read() or "null")
            previo = previo if isinstance(previo, dict) else None
        except ValueError:
            previo = None
        if previo is not None and "firmas" not in previo and "firma" in previo:
            previo["firmas"] = {"_": previo["firma"]}  # la marca de la primera versión (91271561)
            previo["_vieja"] = True
        firmas = (previo or {}).get("firmas") or {}
        try:
            decision = _decide(raiz, nombre, previo)
            if decision is None:
                raise _Ilegible
            firmas, textos = decision
            resultado = "primera vez: estado apuntado, sin aviso" if previo is None else "nada"
            fallos, hechos = [], []
            fin = time.monotonic() + PLAZO  # un plazo para TODOS los avisos de esta respuesta
            for texto in textos:
                ok, detalle = enviar(texto, fin)
                (hechos if ok else fallos).append((texto, detalle))
                _registra(f"{nombre} · {'ok' if ok else 'FALLO'} {detalle} · «{texto[:160]}»")
            if fallos:
                texto, detalle = fallos[0]
                resultado = f"FALLO {detalle}"
                mas = f" (y {len(fallos) - 1} aviso(s) más sin enviar)" if len(fallos) > 1 else ""
                salida = (f"⚠ Aviso por Telegram NO enviado — {detalle}. Texto: «{texto[:120]}»"
                          f"{mas}. Registro: {_dir_estado() / 'aviso.log'}. "
                          "Para apagarlo: TL_AVISO=off.")
            elif hechos:
                resultado = f"ok {hechos[0][1]}"
                salida = (f"✓ Aviso por Telegram {hechos[0][1]}: «{hechos[0][0][:120]}»"
                          + (f" (y {len(hechos) - 1} más)" if len(hechos) > 1 else ""))
        except _Ilegible:
            resultado = "PROGRESS.json ilegible: nada que decidir"  # lo avisa validate-progress.sh
        except Exception as e:  # noqa: BLE001 — un fallo propio tampoco puede callar ni repetirse
            resultado = _limpia(f"ERROR {type(e).__name__}: {e}", _token())
            _registra(f"{nombre} · {resultado}")
            salida = (f"⚠ Aviso por Telegram: el hook falló ({resultado[:160]}). "
                      f"Registro: {_dir_estado() / 'aviso.log'}.")
        f.seek(0)
        f.truncate()
        f.write(json.dumps({"firmas": firmas, "visto": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "proyecto": proyecto, "resultado": resultado}, ensure_ascii=False))
    if salida:
        print(json.dumps({"systemMessage": salida}, ensure_ascii=False))
    return 0


def modo_comprobar(red: bool) -> int:
    token = _token()
    destinos = _destinos()
    print(f"canal: telegram (plugin) · estado del plugin en {_dir_plugin()}")
    print(f"  token: {'sí' if token else 'NO'} · destinatarios: {len(destinos)}"
          f" · API: {os.environ.get('TL_AVISO_API', API)}"
          f" · TL_AVISO={os.environ.get('TL_AVISO', '(on)')}")
    if not token or not destinos:
        print("✗ sin canal: el aviso no llegaría a nadie", file=sys.stderr)
        return 1
    if red:
        try:
            yo = _llamada(token, "getMe", None).get("result", {})
            print(f"  getMe: ok (@{yo.get('username', '?')}) — no se ha mandado ningún mensaje")
        except RuntimeError as e:
            print(f"✗ el bot no responde: {e}", file=sys.stderr)
            return 1
    print("✓ hay canal")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "--hook":
        proyecto = (argv[argv.index("--proyecto") + 1] if "--proyecto" in argv
                    else os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        return modo_hook(proyecto)
    if argv[0] == "--comprobar":
        return modo_comprobar("--red" in argv)
    if argv[0] == "--simulacro":
        texto = " ".join(argv[1:]).strip()
        destinos = _destinos()
        print(f"simulacro: «{texto}» → telegram, {len(destinos)} destino(s), "
              f"token {'sí' if _token() else 'NO'} (no se manda nada)")
        return 0 if texto and destinos and _token() else 1
    texto = " ".join(argv).strip()
    if os.environ.get("TL_AVISO", "").lower() == "off":
        print("TL_AVISO=off: no se manda nada", file=sys.stderr)
        return 1
    ok, detalle = enviar(texto)
    _registra(f"{Path(os.getcwd()).name} · manual · {'ok' if ok else 'FALLO'} {detalle} · "
              f"«{texto[:160]}»")
    if ok:
        print(f"✓ aviso {detalle}")
        return 0
    print(f"✗ aviso NO enviado: {detalle}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
