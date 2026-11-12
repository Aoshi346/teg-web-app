#!/usr/bin/env python3
"""Auditoría de la configuración EJECUTABLE que entra con el repo (SE-47, 2026-10-22).

Hasta hoy `audit-incoming-config.sh` hasheaba solo `settings*.json` y `.mcp.json`. Un hook
manipulado (`.claude/hooks/x.sh`), una skill con `allowed-tools: Bash(*)` y un hook en su
frontmatter, un agente con `mcpServers:` o un plugin (`.claude-plugin/`) ejecutan código igual que
un settings, y no cambian `settings.json`: pasaban sin aviso (ASI05). Esto amplía la cobertura sin
tocar la parte que ya funcionaba (el escaneo de settings/.mcp sigue en el shell).

Dos usos:

  audit_config.py auditar --root R --baseline B [--force]
      Sesión que empieza: calcula la huella de CADA fichero ejecutable, la compara con la guardada,
      imprime qué cambió y qué patrones de riesgo hay, y deja la huella nueva. Sale siempre 0 (como
      el hook de shell: avisa, no bloquea).

  audit_config.py revisar FICHERO [--source S]
      Lo llama el hook ConfigChange: ¿el contenido NUEVO de este fichero baja una defensa? Sale 2
      (bloquea el cambio) si sí, 0 si no. Fuente `policy_settings`: no se bloquea (Claude Code no lo
      permite) y se avisa.

Qué mira, y qué NO:
  · Patrones FUERTES (siempre, en todo fichero ejecutable): `curl|sh`, `base64 -d|sh`, `eval $(curl)`,
    `/dev/tcp`, `nc -e`, `bash -i >&`.
  · Patrones DÉBILES (solo en ficheros nuevos o cambiados; en la primera pasada, una línea por
    fichero): salida a red de un hook (`curl`, `wget`, `nc`, `scp`, `ssh`), lectura de credenciales
    (`~/.ssh`, `.aws/credentials`, `.credentials.json`), y en el frontmatter de skills, agentes y
    comandos: `hooks:`, `mcpServers:`, `allowed-tools` con `Bash` sin acotar, `bypassPermissions`.
  · NO es un muro: es un buscador de patrones, y se rodea partiendo la cadena. Su valor es el DELTA:
    que algo cambie en un hook y alguien lo vea.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

PROFUNDIDAD = 4
PODA = {".git", "node_modules", "venv", ".venv", "dist", "build", "__pycache__"}

FUERTES = [
    ("RCE", re.compile(r"(curl|wget)[^\n\"']*\|\s*(sudo\s+)?(ba|z)?sh\b"), "descarga y ejecuta"),
    ("RCE", re.compile(r"base64\s+(-d|--decode)[^\n]*\|\s*(ba)?sh\b"), "decodifica y ejecuta"),
    ("RCE", re.compile(r"eval\s+[\"']?\$\(\s*(curl|wget)"), "evalúa lo descargado"),
    ("EXF", re.compile(r"/dev/tcp/"), "socket crudo (shell inversa o exfiltración)"),
    ("EXF", re.compile(r"\b(nc|ncat|netcat)\b[^\n]*\s-e\b|bash\s+-i\s*>&"), "shell inversa"),
]
DEBILES_HOOK = [
    ("NET", re.compile(r"(?<![\w-])(curl|wget|ncat|scp|ssh)\s+[-\w$\"'/@:.]"), "sale a red"),
    ("CRED", re.compile(r"\.ssh/|\.aws/credentials|\.credentials\.json|id_rsa|\.netrc|\.npmrc"),
     "toca credenciales"),
]
SOLO_HABLA = re.compile(r"^\s*(?:\w+=\$\(\s*|\w+=\"?\$\(\s*)?(?:e?grep|rg|scan)\s|re\.compile\(|^\s*\w+\s*=\s*re\.compile|\$\{?NOT_A_RULE|\bFUERTES\b")
CLAVES_PELIGROSAS_SETTINGS = {
    "disableAllHooks": "apaga todos los hooks",
    "skipDangerousModePermissionPrompt": "salta el aviso del modo peligroso",
    "enableAllProjectMcpServers": "auto-aprueba los MCP del repo",
}


def _dic(x) -> dict:
    return x if isinstance(x, dict) else {}


def _lista(x) -> list:
    return x if isinstance(x, list) else []


def _sha(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return "?"


def _texto(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _recorre(raiz: Path):
    """(ruta, profundidad) de todos los ficheros hasta PROFUNDIDAD, sin entrar en lo podado."""
    base = len(raiz.parts)
    for dp, dn, fn in os.walk(raiz):
        dn[:] = [d for d in dn if d not in PODA]
        prof = len(Path(dp).parts) - base
        if prof >= PROFUNDIDAD + 4:           # holgura para .claude/skills/x/SKILL.md y plugins
            dn[:] = []
        for f in fn:
            yield Path(dp) / f, prof


def tipo_de(raiz: Path, p: Path) -> str | None:
    """Qué clase de configuración ejecutable es este fichero, o None si no lo es."""
    rel = p.relative_to(raiz).as_posix()
    nombre = p.name
    if nombre == ".mcp.json" or re.fullmatch(r"(.*/)?\.claude/settings(\.local)?\.json", rel):
        return "settings"
    m = re.match(r"(?:.*/)?\.claude/(hooks|skills|agents|commands)/(.+)$", rel)
    if m and (rel.count("/") <= PROFUNDIDAD + 3):
        clase, resto = m.group(1), m.group(2)
        if clase == "hooks" and nombre.endswith((".sh", ".py", ".js", ".json")):
            return "hook"
        if clase == "skills" and nombre == "SKILL.md":
            return "skill"
        if clase == "agents" and nombre.endswith(".md") and "/" not in resto:
            return "agente"
        if clase == "commands" and nombre.endswith(".md") and "/" not in resto:
            return "comando"
        return None
    if re.search(r"(^|/)\.claude-plugin/", rel) and nombre.endswith((".json", ".sh", ".py", ".js", ".md")):
        return "plugin"
    return None


def ficheros_ejecutables(raiz: Path) -> dict[str, str]:
    """{ruta_relativa: clase} de lo que puede ejecutar código o cambiar permisos."""
    salida = {}
    for p, prof in _recorre(raiz):
        t = tipo_de(raiz, p)
        if t:
            salida[p.relative_to(raiz).as_posix()] = t
    return salida


def frontmatter(texto: str) -> str:
    m = re.match(r"---\r?\n(.*?)\r?\n---", texto, re.S)
    return m.group(1) if m else ""


def hallazgos_de(raiz: Path, rel: str, clase: str, debiles: bool) -> list[str]:
    """Líneas de aviso de un fichero. `debiles`: incluir los patrones que dan ruido en lo estable."""
    texto = _texto(raiz / rel)
    out = []
    if clase != "settings":          # los settings los escanea el shell (con su filtro de reglas)
        lineas = texto.splitlines()
        for etiqueta, rx, nota in FUERTES:
            for m in rx.finditer(texto):
                n = texto.count("\n", 0, m.start()) + 1
                # Un comentario o una línea que ES un buscador de patrones (el propio auditor, un
                # gate) habla del patrón, no lo ejecuta: se autodenunciaría en cada sesión.
                linea = lineas[n - 1] if n <= len(lineas) else ""
                if re.match(r"\s*(#|//|\*)", linea) or SOLO_HABLA.search(linea):
                    continue
                out.append(f"{etiqueta}  {rel}:{n}  <- {nota}")
                break
    if not debiles:
        return out
    if clase in ("hook", "plugin"):
        for etiqueta, rx, nota in DEBILES_HOOK:
            m = rx.search(texto)
            if m:
                n = texto.count("\n", 0, m.start()) + 1
                out.append(f"{etiqueta}  {rel}:{n}  <- {nota}")
    if clase in ("skill", "agente", "comando"):
        fm = frontmatter(texto)
        if re.search(r"^hooks\s*:", fm, re.M):
            out.append(f"HOOK  {rel}  <- registra hooks en su frontmatter")
        if re.search(r"^mcpServers\s*:", fm, re.M):
            out.append(f"MCP  {rel}  <- declara servidores MCP en su frontmatter")
        if re.search(r"bypassPermissions", fm):
            out.append(f"PRM  {rel}  <- pide bypassPermissions")
        at = re.search(r"^allowed-tools\s*:\s*(.+(?:\n\s+-.*)*)", fm, re.M)
        if at and re.search(r"(?<![\w(])Bash(?!\()|Bash\(\*\)", at.group(1)):
            out.append(f"TOOLS  {rel}  <- allowed-tools con Bash sin acotar")
    return out


# ── auditar ───────────────────────────────────────────────────────────────────────────────────
def auditar(raiz: Path, baseline: Path, forzar: bool) -> int:
    ficheros = ficheros_ejecutables(raiz)
    # settings/.mcp los hashea y escanea el shell; aquí se hashean TAMBIÉN para que el delta sea uno
    actual = {r: _sha(raiz / r) for r in ficheros}
    previo = {}
    hay_base = False
    try:
        for linea in baseline.read_text(encoding="utf-8").splitlines():
            sha, _, ruta = linea.partition("  ")
            if ruta:
                previo[ruta] = sha
        hay_base = bool(previo)         # el formato antiguo era UNA huella sola: cuenta como sin base
    except (OSError, ValueError):          # ilegible o binario: se trata como «sin base» y se reescribe
        previo, hay_base = {}, False
    try:
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text("".join(f"{s}  {r}\n" for r, s in sorted(actual.items())),
                            encoding="utf-8")
    except OSError:
        pass

    # Copia de los settings tal como están hoy: ConfigChange compara el cambio contra esto
    for rel, clase in ficheros.items():
        if clase == "settings" and re.fullmatch(r"\.claude/settings(\.local)?\.json", rel):
            try:
                snap = raiz / ".claude" / ".config-snapshot" / Path(rel).name
                snap.parent.mkdir(parents=True, exist_ok=True)
                snap.write_text(_texto(raiz / rel), encoding="utf-8")
            except OSError:
                pass
    cambiados = sorted(r for r, s in actual.items() if previo.get(r) != s) if hay_base else []
    borrados = sorted(set(previo) - set(actual)) if hay_base else []
    avisos = []
    for rel, clase in sorted(ficheros.items()):
        avisos += hallazgos_de(raiz, rel, clase,
                               debiles=(not hay_base) or rel in cambiados)
    # Cuántos de cada clase, para que la primera pasada diga qué ha mirado
    por_clase = {}
    for clase in ficheros.values():
        por_clase[clase] = por_clase.get(clase, 0) + 1

    if hay_base and not cambiados and not borrados and not avisos:
        return 0
    marca = "[audit-incoming-config]"
    if hay_base and (cambiados or borrados):
        nom = ", ".join(cambiados[:5]) + (f" y {len(cambiados) - 5} más" if len(cambiados) > 5 else "")
        extra = f"; borrados: {', '.join(borrados[:3])}" if borrados else ""
        print(f"{marca} {len(cambiados)} fichero(s) ejecutable(s) cambiaron desde la última sesión: "
              f"{nom or '(ninguno)'}{extra}.")
    if not hay_base:
        resumen = ", ".join(f"{v} {k}" for k, v in sorted(por_clase.items()))
        print(f"{marca} primera pasada: huella de {len(ficheros)} ficheros ejecutables ({resumen}).")
    if avisos and (forzar or cambiados or not hay_base or any(a.startswith(("RCE", "EXF")) for a in avisos)):
        print(f"{marca} ⚠️  PATRONES DE RIESGO en hooks, skills, agentes o plugins — revísalos:")
        for a in avisos:
            print(f"  {a}")
        print(f"{marca}  RCE=ejecución remota · EXF=exfiltración · NET=sale a red · CRED=credenciales · "
              "HOOK/MCP/PRM/TOOLS=frontmatter")
        print(f"{marca}  Contexto y qué hacer: .claude/rules/agent-security.md §4")
    return 0


# ── revisar (ConfigChange) ────────────────────────────────────────────────────────────────────
def razones_de_bloqueo(ruta: Path) -> list[str]:
    texto = _texto(ruta)
    razones = []
    if ruta.suffix == ".json":
        try:
            d = json.loads(texto)
        except json.JSONDecodeError:
            return []                    # un JSON roto no lo juzgamos: Claude Code ya lo rechaza
        if isinstance(d, dict):
            for k, nota in CLAVES_PELIGROSAS_SETTINGS.items():
                if d.get(k) is True:
                    razones.append(f"`{k}: true` {nota}")
            if _dic(d.get("permissions")).get("defaultMode") == "bypassPermissions":
                razones.append("`defaultMode: bypassPermissions` salta todos los permisos")
            env = _dic(d.get("env"))
            for v in ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"):
                if v in env:
                    razones.append(f"`env.{v}` redirige la API o deja una credencial a la vista")
            if d.get("apiKeyHelper"):
                razones.append("`apiKeyHelper` ejecuta un programa para sacar la credencial")
            for bloques in _dic(d.get("hooks")).values():
                for b in _lista(bloques):
                    for h in _lista(_dic(b).get("hooks")):
                        cmd = str(_dic(h).get("command", ""))
                        for _, rx, nota in FUERTES:
                            if rx.search(cmd):
                                razones.append(f"un hook ejecuta algo que {nota}: {cmd[:60]}")
    else:
        for _, rx, nota in FUERTES:
            if rx.search(texto):
                razones.append(f"el contenido {nota}")
    return sorted(set(razones))


NOMBRE_DE_FUENTE = {"project_settings": "settings.json", "local_settings": "settings.local.json"}


def _hooks_de(d: dict) -> set:
    return {str(_dic(h).get("command", "")) for bl in _dic(d.get("hooks")).values() for b in _lista(bl)
            for h in _lista(_dic(b).get("hooks"))}


def razones_de_retirada(nuevo: dict, viejo: dict) -> list[str]:
    """Defensas que el contenido NUEVO quita respecto a lo último que se vio: es lo que cambia en un
    ataque que no añade nada raro, solo borra la puerta (el `deny`, el registro del guard, el sandbox)."""
    r = []
    perm_n, perm_v = _dic(nuevo.get("permissions")), _dic(viejo.get("permissions"))
    quitadas = [x for x in _lista(perm_v.get("deny")) if x not in _lista(perm_n.get("deny"))]
    if quitadas:
        r.append(f"quita {len(quitadas)} regla(s) `deny` (p. ej. `{quitadas[0]}`)")
    perdidos = _hooks_de(viejo) - _hooks_de(nuevo)
    if perdidos:
        r.append(f"quita {len(perdidos)} hook(s) registrado(s) (p. ej. `{sorted(perdidos)[0][:60]}`)")
    if _dic(viejo.get("sandbox")).get("enabled") is True and _dic(nuevo.get("sandbox")).get("enabled") is not True:
        r.append("apaga el sandbox")
    ancho = ("Bash", "Bash(*)", "Bash(**)")
    if any(x in ancho for x in _lista(perm_n.get("allow"))) and not any(x in ancho for x in _lista(perm_v.get("allow"))):
        r.append("añade `Bash(*)` al allow")
    return r


def revisar(fichero: str, fuente: str, raiz: Path | None = None) -> int:
    ruta = Path(fichero)
    razones = razones_de_bloqueo(ruta) if fichero else []
    nombre = NOMBRE_DE_FUENTE.get(fuente)
    snap = (raiz / ".claude" / ".config-snapshot" / nombre) if (raiz and nombre) else None
    if fichero and snap is not None:
        try:
            nuevo = json.loads(_texto(ruta))
            viejo = json.loads(snap.read_text(encoding="utf-8")) if snap.exists() else None
        except ValueError:
            nuevo = viejo = None
        if isinstance(nuevo, dict):
            if isinstance(viejo, dict):
                razones = sorted(set(razones + razones_de_retirada(nuevo, viejo)))
            if not razones:                     # se acepta: el siguiente cambio se compara con éste
                try:
                    snap.parent.mkdir(parents=True, exist_ok=True)
                    snap.write_text(json.dumps(nuevo), encoding="utf-8")
                except OSError:
                    pass
    if not razones:
        return 0
    cuerpo = "\n".join(f"  · {r}" for r in razones)
    if fuente == "policy_settings":
        print(f"[config-change-guard] AVISO (política gestionada, no se puede bloquear):\n{cuerpo}",
              file=sys.stderr)
        return 0
    print("[config-change-guard] BLOQUEADO: el contenido nuevo baja una defensa.\n"
          f"{cuerpo}\n"
          "  Si el cambio es legítimo, hazlo tú a mano fuera de la sesión (o pídele al Usuario que lo "
          "apruebe: governance.md §2). No lo repitas con otra forma.", file=sys.stderr)
    return 2


def main() -> int:
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] == "auditar":
        def val(flag):
            return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else None
        raiz = Path(val("--root") or ".").resolve()
        base = Path(val("--baseline") or raiz / ".claude" / ".incoming-config-ejecutables.tsv")
        return auditar(raiz, base, "--force" in a)
    if a[0] == "revisar":
        fuente = a[a.index("--source") + 1] if "--source" in a and a.index("--source") + 1 < len(a) else ""
        archivo = next((x for x in a[1:] if not x.startswith("--") and x != fuente), "")
        raiz = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
        return revisar(archivo, fuente, raiz)
    print(f"subcomando desconocido: {a[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
