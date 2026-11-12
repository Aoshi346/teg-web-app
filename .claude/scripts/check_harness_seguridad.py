#!/usr/bin/env python3
"""G7 · ¿El PROPIO harness de este proyecto está bien armado? (SE-51, 2026-10-22)

Los hallazgos H4/H6/H7/H10/H15 de la revisión de ciberseguridad se descubrieron a mano, leyendo
`settings*.json` de 13 proyectos. Lo que se puede comprobar con un script no debe hacerlo un
agente, así que esto es el auditor del harness hecho script: lo llaman Otto, `update-agent` y
`smoke/seguridad/correr.sh`, y se puede correr sobre cualquier derivado.

Qué mira (cada comprobación lleva su identificador, que es también la clave de una excepción):

  H1  `sandbox` apagado o ausente                                        (aviso, es informativo)
  H2  `Bash(*)` en `allow` SIN sandbox: un `allow` de Bash amplio sin contención        (ALTO)
  H3  `IS_SANDBOX` en `env` SIN sandbox activo: engaña a quien lo lee y a Claude Code   (ALTO)
  H4  guard de secretos no registrado (aviso) · registrado pero su script no existe (ALTO)
      · registrado con `RUTAS_PROPIAS` vacías o que apuntan a rutas inexistentes (aviso)
  H5  hooks que registran el comando sin redactar secretos                          (aviso)
  H6  `deny` de la forma `Bash(*palabra*)` que tapan comandos legítimos             (aviso)
  H7  GitHub Actions sin fijar por SHA (de terceros: ALTO · `actions/*`: aviso)
  H8  servidores de `.mcp.json` con versión sin fijar (`@latest`: ALTO · sin versión: aviso)
  H9  plugins de marketplaces que no son de Anthropic                              (aviso)
  H10 `skipDangerousModePermissionPrompt`, `bypassPermissions`, `disableAllHooks`,
      `enableAllProjectMcpServers: true`, `ANTHROPIC_BASE_URL`/`ANTHROPIC_API_KEY` en `env` (ALTO)
  H11 `paths:` de una rule cuyos globs no encuentran NADA en este proyecto          (aviso)
  H12 un hook registrado cuyo script no existe                                      (ALTO)
  H13 el hook de git `pre-commit` no está instalado                                 (aviso)

Las excepciones se declaran con su razón en `.claude/harness-seguridad-declarado.json`:
    { "H2": "perfil yolo decidido por el Usuario el 2026-08-22, el modo auto lo apaga" }
Una excepción sin razón no cuenta (indistinguible de un descuido a los dos meses). Con detalle:
`"H6:Bash(*production*)": "…"`.

Solapes declarados: H7 y H8 miran lo mismo que `gate_deps.py` (S2/S1) y H12 lo que `check_mechanisms.py`
(hooks de settings); H11 lo que `check_instrucciones.py` («sin ancla viva»). Aquí se reúnen en UNA pasada
sobre cualquier derivado (`--root`), con severidad propia: puede no coincidir con la de esos gates.
Lo que NO mira, dicho para que nadie lo dé por cubierto: el contenido de los hooks (lo audita
`audit-incoming-config.sh`), las dependencias (`gate_deps.py`), los secretos en el código
(`scan_secretos_diff.py`), los puertos (`check_puertos_docker.py`) ni el código de la app.

Uso:
    python3 check_harness_seguridad.py [--root RUTA]... [--json]
Salida: 0 sin ALTO sin declarar · 1 hay ALTO · 2 NO SE PUDO MEDIR (la ruta no tiene `.claude/`, o un
settings/.mcp.json existe y no se entiende).
Límites: no ve `Bash(bash:*)`/`Bash(*:*)` en allow, `.github/actions/*/action.yml`, ni `paths:` escrito
como cadena; el pre-commit de git instalado como COPIA (no enlace) cuenta como instalado.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ALTO, AVISO = "ALTO", "aviso"
FICHERO_DECLARADO = ".claude/harness-seguridad-declarado.json"
# Marketplaces que publica Anthropic. El resto es código de terceros ejecutándose en la sesión.
MARKETPLACES_ANTHROPIC = {"claude-plugins-official", "claude-code-plugins", "anthropic-agent-skills"}
RX_SHA = re.compile(r"^[0-9a-f]{40}$")


ILEGIBLES: list[str] = []      # ficheros que existen y no se pudieron leer: el auditor ABORTA, no dice «limpio»


def _json(ruta: Path) -> dict | None:
    """El JSON como dict; None si no existe. Si EXISTE y no se entiende, se apunta en ILEGIBLES."""
    if not ruta.exists():
        return None
    try:
        d = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        ILEGIBLES.append(str(ruta))
        return None
    if not isinstance(d, dict):
        ILEGIBLES.append(str(ruta))
        return None
    return d


def _dic(x) -> dict:
    return x if isinstance(x, dict) else {}


def _lista(x) -> list:
    return x if isinstance(x, list) else []


def _ajustes(raiz: Path) -> list[tuple[str, dict]]:
    """settings.json y settings.local.json que existan y se entiendan."""
    salida = []
    for nombre in ("settings.json", "settings.local.json"):
        d = _json(raiz / ".claude" / nombre)
        if d is not None:
            salida.append((f".claude/{nombre}", d))
    return salida


def _comandos_de_hooks(ajuste: dict):
    """(evento, matcher, comando) de cada hook registrado."""
    for evento, bloques in _dic(ajuste.get("hooks")).items():
        for bloque in _lista(bloques):
            for h in _lista(_dic(bloque).get("hooks")):
                if isinstance(h, dict) and h.get("command"):
                    yield evento, (bloque.get("matcher") or ""), h["command"]


def _script_de(comando: str, raiz: Path) -> Path | None:
    """Ruta del script de un hook del proyecto (`$CLAUDE_PROJECT_DIR/.claude/hooks/x.sh`)."""
    # Solo si cuelga del proyecto: `~/.claude/hooks/x.sh` o una ruta absoluta de fuera no son suyos.
    m = re.search(r"(?:^|[\s\"'=])(?:\$CLAUDE_PROJECT_DIR/|\$\{CLAUDE_PROJECT_DIR\}/|\./)?(\.claude/[\w./-]+\.(?:sh|py))",
                  comando)
    return raiz / m.group(1) if m else None


def comprobar(raiz: Path) -> list[dict]:
    h: list[dict] = []

    def anota(id_: str, nivel: str, donde: str, que: str, arreglo: str, detalle: str = "") -> None:
        h.append({"id": id_, "nivel": nivel, "donde": donde, "que": que, "arreglo": arreglo,
                  "detalle": detalle})

    ajustes = _ajustes(raiz)
    sandbox_on = any((_dic(a.get("sandbox")).get("enabled") is True) for _, a in ajustes)

    for nombre, a in ajustes:
        perm = _dic(a.get("permissions"))
        allow = [x for x in _lista(perm.get("allow")) if isinstance(x, str)]
        deny = [x for x in _lista(perm.get("deny")) if isinstance(x, str)]
        env = _dic(a.get("env"))

        # H2 / H3
        if not sandbox_on and any(x in ("Bash", "Bash(*)", "Bash(**)") for x in allow):
            anota("H2", ALTO, nombre, "`Bash(*)` en `allow` y el sandbox no está activo: cualquier "
                  "comando corre con los permisos del usuario, sin contención.",
                  'activa `"sandbox": {"enabled": true}` o acota el allow; si es decisión tomada, '
                  f"decláralo con su razón en {FICHERO_DECLARADO}", "Bash(*)")
        if "IS_SANDBOX" in env and not sandbox_on:
            anota("H3", ALTO, nombre, "`IS_SANDBOX` en `env` con el sandbox apagado: la variable "
                  "afirma una contención que no existe.", "quítala, o activa el sandbox de verdad")
        # H10
        for clave in ("skipDangerousModePermissionPrompt", "disableAllHooks",
                      "enableAllProjectMcpServers"):
            if a.get(clave) is True:
                anota("H10", ALTO, nombre, f"`{clave}: true` baja una defensa de serie.",
                      "ponlo a false o quítalo", clave)
        if (perm.get("defaultMode") or "") == "bypassPermissions":
            anota("H10", ALTO, nombre, "`defaultMode: bypassPermissions` salta TODOS los permisos.",
                  "usa acceptEdits (desatendido) o auto (interactivo)", "bypassPermissions")
        for var in ("ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
            if var in env:
                anota("H10", ALTO, nombre, f"`{var}` en el `env` de un fichero que viaja con el repo: "
                      "redirige la API o deja una credencial a la vista (CVE-2026-21852).",
                      "sácalo del repo; la credencial va en el entorno del operador", var)
        # H6
        for d in deny:
            m = re.fullmatch(r"Bash\(\*([A-Za-z][A-Za-z-]{2,})\*\)", d)
            if m:
                anota("H6", AVISO, nombre, f"el deny `{d}` casa con CUALQUIER comando que contenga "
                      f"«{m.group(1)}» (`cat {m.group(1)}.md`, `ls {m.group(1)}/`…).",
                      "acótalo al comando real (`Bash(*deploy.sh*)`, `Bash(kubectl * apply*)`)", d)
        # H9
        for plug, activo in _dic(a.get("enabledPlugins")).items():
            _, _, mercado = str(plug).partition("@")
            if activo and mercado and mercado not in MARKETPLACES_ANTHROPIC:
                anota("H9", AVISO, nombre, f"el plugin `{plug}` viene de un marketplace que no es "
                      "de Anthropic: código de terceros dentro de la sesión.",
                      "revisa su código antes de habilitarlo o quítalo", str(plug))

        # H4 / H5 / H12: hooks
        guard_registrado = None
        for evento, matcher, cmd in _comandos_de_hooks(a):
            script = _script_de(cmd, raiz)
            if script is not None and not script.exists():
                anota("H12", ALTO, nombre, f"el hook {evento} apunta a `{script.relative_to(raiz)}` "
                      "y no existe: la protección que prometía no corre.",
                      "restaura el script o quita el registro", str(script.relative_to(raiz)))
            if "guard-secretos" in cmd:
                guard_registrado = script
        if guard_registrado is not None and guard_registrado.exists():
            propias = _rutas_propias(guard_registrado)
            if propias is not None:
                if not propias:
                    anota("H4", AVISO, str(guard_registrado.relative_to(raiz)),
                          "`RUTAS_PROPIAS` está vacío: el guard protege solo por la parte genérica, "
                          "o sea por casualidad.", "añade las rutas de secretos de ESTE proyecto")
                for r in propias:
                    if not (raiz / r).exists():
                        anota("H4", AVISO, str(guard_registrado.relative_to(raiz)),
                              f"`RUTAS_PROPIAS` incluye `{r}` y no existe aquí: media regla "
                              "apuntando al vacío.", "corrige la ruta o quítala", r)

    # H4 (no registrado): se mira una vez por proyecto, no por fichero de ajustes
    registrado = any("guard-secretos" in c for _, a in ajustes for _, _, c in _comandos_de_hooks(a))
    if ajustes and not registrado:
        anota("H4", AVISO, ".claude/settings.json", "ningún hook PreToolUse `guard-secretos` "
              "registrado: `deny Read(.env)` no cubre `grep`, `awk`, `base64` ni `curl -d @.env`.",
              "registra `.claude/hooks/guard-secretos.sh` (matcher `Bash|Read|Grep`)")

    # H1 informativo
    if ajustes and not sandbox_on:
        anota("H1", AVISO, ".claude/settings.json", "el sandbox de Bash no está activo "
              "(`sandbox.enabled`).", "valóralo por proyecto: contiene red y ficheros de los "
              "comandos, pero cambia cómo corren los tests y Docker")

    # H5: hooks que registran el comando sin redactar
    hooks_dir = raiz / ".claude" / "hooks"
    if hooks_dir.is_dir():
        for f in sorted(hooks_dir.glob("*.sh")):
            try:
                t = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            registra = re.search(r"tool_input[^\n]*command|\.command|\$CMD\b|\$COMANDO\b", t) and re.search(r">>\s*[\"$/]", t)
            if registra and not re.search(r"redact|REDACT|\[REDACTED\]|sanitiz|\\\*\\\*\\\*|sk-\[", t):
                anota("H5", AVISO, str(f.relative_to(raiz)), "escribe el comando o su entrada a un "
                      "log sin ninguna redacción: un token pasado por línea de comandos queda en "
                      "claro en el fichero.", "pasa el texto por un redactor antes de escribirlo",
                      f.name)

    # H7: Actions
    wf = raiz / ".github" / "workflows"
    if wf.is_dir():
        for f in sorted(list(wf.glob("*.yml")) + list(wf.glob("*.yaml"))):
            for n, linea in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                m = re.match(r"\s*-?\s*uses:\s*([^\s#]+)", linea)
                uso = m.group(1).strip("\"'") if m else ""
                if not uso or uso.startswith(("./", "docker://")):
                    continue
                accion, _, ref = uso.partition("@")
                if not RX_SHA.match(ref):
                    oficial = accion.startswith(("actions/", "github/"))
                    anota("H7", AVISO if oficial else ALTO, f"{f.relative_to(raiz)}:{n}",
                          f"`{uso}` no está fijada por SHA de 40 caracteres: quien controle "
                          "la etiqueta cambia lo que corre en tu CI.",
                          f"fija `{accion}@<sha>` (y deja la versión en un comentario)",
                          f"{f.name}:{accion}")

    # H8: MCP
    mcp = _json(raiz / ".mcp.json")
    for nombre, srv in _dic(_dic(mcp).get("mcpServers")).items():
        if not isinstance(srv, dict):
            continue
        cmd = str(srv.get("command", ""))
        args = [str(x) for x in (srv.get("args") or [])]
        if Path(cmd).name not in ("npx", "bunx", "pnpx", "uvx", "pipx", "dlx"):
            continue
        pkg = next((x for x in args if not x.startswith("-") and x not in ("run", "dlx", "exec")), "")
        if not pkg:
            continue
        if pkg.endswith("@latest") or pkg.endswith("@next"):
            anota("H8", ALTO, ".mcp.json", f"el servidor `{nombre}` usa `{pkg}`: se actualiza solo y "
                  "cada arranque puede traer código nuevo (cadena de suministro).",
                  "fija la versión (`paquete@1.2.3`)", nombre)
        elif not re.search(r"(?<=.)@\d|==\d", pkg):
            anota("H8", AVISO, ".mcp.json", f"el servidor `{nombre}` (`{pkg}`) no fija versión.",
                  "fija la versión (`paquete@1.2.3`)", nombre)

    # H11: globs de paths: que no encuentran nada
    rules = raiz / ".claude" / "rules"
    muertos = []
    if rules.is_dir():
        for f in sorted(rules.glob("*.md")):
            globs = _paths_de(f)
            if globs and not any(_hay(raiz, g) for g in globs):
                muertos.append((f.name, globs))
    for nombre, globs in muertos:
        anota("H11", AVISO, f".claude/rules/{nombre}", "ningún glob de su `paths:` encuentra un "
              f"fichero en este proyecto ({', '.join(globs[:3])}): la rule no se cargará nunca aquí.",
              "ajusta el glob, o quita la rule de este proyecto si no aplica", nombre)

    # H13: pre-commit de git
    if (raiz / ".git").exists() and not _precommit_instalado(raiz):
        anota("H13", AVISO, ".git/hooks/pre-commit", "el hook de git `pre-commit` no está instalado: "
              "`pre-commit-check.sh` (secretos, ficheros grandes, anti-mock) no corre al commitear.",
              "`ln -s ../../.claude/hooks/pre-commit-check.sh .git/hooks/pre-commit`")
    return h


def _rutas_propias(guard: Path) -> list[str] | None:
    """Entradas SIN comentar de `RUTAS_PROPIAS=( … )` del guard, con `$RAIZ/` quitado."""
    t = guard.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"RUTAS_PROPIAS=\((.*?)\n\)", t, re.S)
    if not m:
        return None
    salida = []
    for linea in m.group(1).splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        for tok in re.findall(r'"([^"]+)"', linea):
            salida.append(tok.replace("$RAIZ/", "").replace("${RAIZ}/", "").rstrip("/"))
    return salida


def _paths_de(rule: Path) -> list[str]:
    """Globs del `paths:` del frontmatter (lista YAML con guiones, o en una línea)."""
    t = rule.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    if not m:
        return []
    fm = m.group(1)
    p = re.search(r"^paths:[ \t]*(.*?)(?=^\S|\Z)", fm, re.S | re.M)
    if not p:
        return []
    cuerpo = p.group(1)
    if cuerpo.lstrip().startswith("["):                         # paths: ["a", "b"]
        return [x.strip().strip("\"'") for x in cuerpo.strip().strip("[]").split(",") if x.strip()]
    return [x.strip().strip("\"'") for x in re.findall(r"^\s*-\s*(.+)$", cuerpo, re.M)]


def _hay(raiz: Path, glob: str) -> bool:
    try:
        return next(iter(raiz.glob(glob)), None) is not None
    except (ValueError, NotImplementedError, OSError):
        return True      # glob que pathlib no sabe evaluar: no se acusa


def _precommit_instalado(raiz: Path) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(raiz), "rev-parse", "--git-path", "hooks/pre-commit"],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return True      # no se pudo preguntar: no se acusa
    ruta = Path(r.stdout.strip())
    if not ruta.is_absolute():
        ruta = raiz / ruta
    return r.returncode != 0 or ruta.exists()


def declaradas(raiz: Path) -> dict:
    d = _json(raiz / FICHERO_DECLARADO) or {}
    return {k: v for k, v in d.items() if isinstance(v, str) and v.strip()}


def auditar(raiz: Path) -> dict:
    decl = declaradas(raiz)
    hallazgos, ok = [], []
    for x in comprobar(raiz):
        clave = f"{x['id']}:{x['detalle']}" if x["detalle"] else x["id"]
        razon = decl.get(clave) or decl.get(x["id"])
        if razon:
            ok.append({**x, "declarado": razon})
        else:
            hallazgos.append(x)
    return {"raiz": str(raiz), "hallazgos": hallazgos, "declarados": ok}


def main() -> int:
    argv = sys.argv[1:]
    como_json = "--json" in argv
    raices = []
    for i, a in enumerate(argv):
        if a == "--root" and i + 1 < len(argv):
            raices.append(Path(argv[i + 1]).resolve())
        elif a.startswith("--root="):
            raices.append(Path(a.split("=", 1)[1]).resolve())
    if not raices:
        raices = [Path(".").resolve()]

    resultados, peor = [], 0
    for r in raices:
        if not (r / ".claude").is_dir():
            print(f"NO SE PUDO MEDIR: {r} no tiene .claude/ (¿ruta equivocada?). Un auditor que no "
                  "encuentra qué medir lo dice; no imprime «limpio».", file=sys.stderr)
            return 2
        del ILEGIBLES[:]
        res = auditar(r)
        if ILEGIBLES:
            print("NO SE PUDO MEDIR: no se entiende (JSON roto o de otra forma) "
                  + ", ".join(sorted(set(ILEGIBLES))) + ". Un auditor que no puede leer su sujeto "
                  "lo dice; no imprime «limpio».", file=sys.stderr)
            return 2
        resultados.append(res)
        if any(x["nivel"] == ALTO for x in res["hallazgos"]):
            peor = 1
    if como_json:
        print(json.dumps(resultados, indent=2, ensure_ascii=False))
        return peor
    for res in resultados:
        altos = [x for x in res["hallazgos"] if x["nivel"] == ALTO]
        avisos = [x for x in res["hallazgos"] if x["nivel"] == AVISO]
        print(f"  HIGIENE DEL HARNESS — {Path(res['raiz']).name}")
        print("  " + "─" * 62)
        for x in altos + avisos:
            marca = "❌" if x["nivel"] == ALTO else "⚠️ "
            print(f"  {marca} {x['id']:<4} {x['donde']}\n        {x['que']}\n        → {x['arreglo']}")
        for x in res["declarados"]:
            print(f"  ✅ {x['id']:<4} {x['donde']}  (declarado: {x['declarado'][:70]})")
        print("  " + "─" * 62)
        print(f"  {len(altos)} ALTO · {len(avisos)} aviso(s) · {len(res['declarados'])} declarado(s)\n")
    return peor


if __name__ == "__main__":
    sys.exit(main())
