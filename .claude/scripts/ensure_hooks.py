#!/usr/bin/env python3
"""ensure_hooks.py — registra en el settings.json de un proyecto los hooks del CORE que le faltan.

EL FALLO QUE CIERRA, y es de los silenciosos. `template_diff.py` copia `hooks/` como categoría, así
que el fichero `.sh` llega al proyecto. Pero el REGISTRO vive en `settings.json`, que NO se copia —
y con razón: es propio de cada proyecto, con sus permisos y sus rutas.

Resultado hasta ahora: **el hook llegaba copiado y muerto**. Un fichero presente que no corre es
peor que uno ausente, porque parece que está la protección.

QUÉ HACE: añade la entrada del hook al `settings.json` del destino **sin tocar nada más** —
respeta los hooks propios del proyecto, no reordena, y es idempotente (si ya está, no duplica).

QUÉ NO HACE: no activa hooks que el proyecto haya quitado a propósito. Si una entrada está
comentada o el proyecto la borró y añadió la suya, no se pisa: se avisa y decide una persona.
"""
import argparse, json, os, re, sys

# Los hooks que TODO proyecto derivado debe tener registrados, con su evento.
# Se añade aquí lo que sea estructural — no lo que sea del gusto de un proyecto.
CORE_HOOKS = [
    ("UserPromptSubmit", "capture-task.sh",
     "Registra cada petición del Usuario y reinyecta las pendientes. Sin él, lo que se pide "
     "entre veinte tareas se pierde — y eso falla siempre, no a veces."),
    ("UserPromptSubmit", "dispatch-hint.sh",
     "Inyecta qué piezas del harness aplican a lo que se acaba de pedir."),
    ("UserPromptSubmit", "yolo-politica.sh",
     "Si el modo YOLO del dashboard está activo, inyecta su política (alcance, tipo, git) y lo que "
     "sigue prohibido. Sin él, el interruptor cambia permisos pero el agente no sabe hasta dónde "
     "llega (T-101). Calla si está apagado; exit 0 siempre."),
    ("SessionStart", "otto-briefing.sh",
     "El estado al arrancar: tarea, git, sesión SpecKit, y en qué paso del proceso (13 estados) "
     "estamos y qué hay que teclear — para quien no conoce los comandos (T-240)."),
    # Con MATCHER, y no es un detalle: hasta el 2026-09-14 aquí iba `check-ram.sh` sin matcher, que es
    # doblemente malo — correría en CADA tool call (no solo en pytest) y su exit 1 no bloquea nada en
    # un PreToolUse (el único que bloquea es el 2). `gate-ram-pytest.sh` filtra por comando y traduce
    # 1→2 (`rules/harness-gotchas.md` §matchers). Los matchers de hook son regex sobre el NOMBRE de
    # la tool: «Bash», nunca «Bash(pytest*)».
    ("PreToolUse", "gate-ram-pytest.sh", "Gate de RAM antes de CADA pytest (llama a check-ram.sh y "
     "bloquea de verdad). OOM = fallo crítico.", "Bash"),
    ("SubagentStop", "agent-registry-log.sh",
     "Deja constancia de QUÉ agente corrió. Sin él, `agent_registry.py` depende de que alguien "
     "se acuerde de alimentarlo — y eso se hace dos veces y luego nunca. No bloquea: sale 0 "
     "siempre. Cosechado de /home/webs el 2026-08-22 (DER-1)."),
]

# Hooks que el template RETIRÓ y que un derivado puede seguir teniendo registrados. No se tocan
# (el settings.json es del proyecto: se avisa y decide una persona), pero se dice, porque un hook
# retirado y registrado o duplica trabajo o falla al arrancar en cuanto alguien borre el .sh.
RETIRED_HOOKS = {
    "siguiente-paso.sh": "lo hace otto-briefing.sh desde el 2026-10-19 (LI-25); con los dos "
                         "registrados, el paso del proceso sale dos veces",
}

# Un Stop hook BLOQUEANTE (exit 2) nunca entra en CORE_HOOKS: lo encendería en todo derivado sin
# que nadie lo haya decidido (`rules/governance.md` §2 y §6). El que había, el gate del informe,
# pasó dos meses sin registrar y se archivó el 2026-10-19 por decisión del Usuario (MO-D1): el
# informe se exigirá al cerrar el issue (`_archive/2026-10-19/README.md`).

# Variables de entorno que TODO proyecto derivado debe tener. Van aquí y no en template_diff.py
# porque `settings.json` NO se copia —es propio de cada proyecto, con sus rutas y sus permisos—,
# así que ponerlas en el settings del template no llegaba a ningún sitio. Es el mismo fallo que
# tenían los hooks: el fichero llegaba y el registro no.
CORE_ENV = {
    "CLAUDE_CODE_ENABLE_TODO_TOOLS": ("1",
        "Las tools de Task/TODO vienen DESACTIVADAS por defecto en los modelos recientes. Sin "
        "esto no hay lista de progreso en la terminal (Ctrl+T)."),
    # Sub-ola 2.01 (CL-7): los dos topes de concurrencia salen de hooks/check-ram.sh
    # (MB_PER_SESSION ÷ MB_PER_AGENT = 8) y check_mechanisms.py exige que cuadren. Son uno por
    # mecanismo: 8 subagentes a la vez y, aparte, 8 agentes en cada workflow que corra. El tope de
    # MEMORIA (CLAUDE_CODE_TOOL_MEMORY_LIMIT) NO va aquí a propósito: su cgroup es uno por usuario y
    # máquina (medido el 2026-10-21) y un valor por proyecto reescribiría el de todas las sesiones.
    "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": ("8",
        "Tope de subagentes a la vez en la sesión: 4 GB ÷ 512 MB (check-ram.sh --explain)."),
    "CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS": ("8",
        "Tope de agentes a la vez en cada workflow (aparte de los subagentes): el mismo reparto."),
    # CL-D2 (aprobado 2026-10-18): agent teams apagado por defecto en los derivados. «0» explícito
    # porque el `env` de un settings gana a la shell: con la clave ausente, una terminal que herede
    # `=1` lo encendería sin querer. Se enciende por sesión con --settings.
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": ("0",
        "Agent teams apagado: encendido cambia la delegación normal. Por sesión: --settings."),
}

# Variables que un derivado puede tener y que el template ya no quiere ahí. No se tocan (el
# settings.json es del proyecto: se avisa y decide una persona, como con RETIRED_HOOKS).
ENV_A_REVISAR = {
    ("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1"):
        "agent teams encendido para todo el proyecto: CL-D2 lo apaga por defecto (\"0\") y lo "
        "enciende por sesión con --settings",
    ("CLAUDE_CODE_TOOL_MEMORY_LIMIT", None):
        "el cgroup del tope es uno por usuario y máquina: un valor de proyecto reescribe el tope de "
        "todas las sesiones (rules/ram-pytest.md §Los topes que pone Claude Code)",
}

# Permisos de SOLO LECTURA que evitan que un workflow con fan-out pare N veces a preguntar por un
# `wc -l`. Es la alternativa al auto mode cuando no se quiere el clasificador (el «10-15 % de tokens
# extra» que se citaba aquí no tenía fuente: en Pro/Max/Team no se cobra; ver
# rules/research-driven-planning.md §Coste oculto 1, corregido 2026-10-20).
CORE_ALLOW = ["Bash(find*)", "Bash(grep*)", "Bash(rg*)", "Bash(wc*)", "Bash(head*)", "Bash(tail*)",
              "Bash(sort*)", "Bash(uniq*)", "Bash(cut*)", "Bash(tr*)", "Bash(diff*)", "Bash(jq*)",
              "Bash(free*)", "Bash(stat*)", "Bash(basename*)", "Bash(dirname*)", "Bash(echo*)"]


# ── sub-ola 2.29 (SE-41): datos reales en desarrollo ─────────────────────────────────────────
# Si el proyecto responde `datos_reales_desarrollo: si-…` en su CONFIGURACION.yaml, lo que decidió a
# mano develop (EvoPreven) pasa a ser el valor por defecto: capture-task NO se registra (escribiría
# cada prompt en un fichero compartido), los MCP de base de datos de su .mcp.json se apagan
# (`disabledMcpjsonServers`, que bloquea en todos los modos: security.md §MCP) y se deniegan los
# adjuntos del canal. Solo se AÑADE protección: un capture-task ya registrado no se quita (lo decide
# una persona, governance.md §2), se avisa, y el propio hook no escribe nada con esa respuesta.
RX_DATOS_REALES = re.compile(r"""^\s*datos_reales_desarrollo:\s*["']?(s[ií][\w-]*)""", re.M)
RX_MCP_BBDD = re.compile(r"postgres|mysql|mariadb|mongo|sqlite|supabase|dbhub|neon|planetscale|"
                         r"cockroach|bbdd|database", re.I)
ADJUNTOS_DEL_CANAL = ["mcp__plugin_telegram_telegram__download_attachment"]


def datos_reales(base):
    """La respuesta `si-…` de CONFIGURACION.yaml, o None. Sin PyYAML: el gate no puede depender de él."""
    try:
        txt = open(os.path.join(base, ".claude", "CONFIGURACION.yaml"), encoding="utf-8").read()
    except OSError:
        return None
    m = RX_DATOS_REALES.search(txt)
    return m.group(1) if m else None


def mcp_de_base_de_datos(base):
    """Los servidores de .mcp.json que hablan con una base de datos (por nombre, comando o args)."""
    try:
        servidores = (json.load(open(os.path.join(base, ".mcp.json"), encoding="utf-8"))
                      .get("mcpServers") or {})
    except (OSError, ValueError):
        return []
    return sorted(n for n, cfg in servidores.items() if RX_MCP_BBDD.search(n + json.dumps(cfg)))


def proteger_datos_reales(d, base):
    """Añade las protecciones al settings `d`. Devuelve lo que añadió (vacío si ya estaba)."""
    cambios = []
    for n in mcp_de_base_de_datos(base):
        apagados = d.setdefault("disabledMcpjsonServers", [])
        if n not in apagados:
            apagados.append(n)
            cambios.append(f"disabledMcpjsonServers += {n} (MCP de base de datos)")
    deny = d.setdefault("permissions", {}).setdefault("deny", [])
    for regla in ADJUNTOS_DEL_CANAL:
        if regla not in deny:
            deny.append(regla)
            cambios.append(f"deny += {regla} (adjuntos del canal)")
    return cambios
# ── fin 2.29 ─────────────────────────────────────────────────────────────────────────────────


def asegurar_env_y_allow(d):
    """Devuelve (env_añadidas, allow_añadidos). NO pisa lo que el proyecto ya declare."""
    env = d.setdefault("env", {})
    nuevas = [(k, v[1]) for k, (v0, _) in ((k, v) for k, v in CORE_ENV.items())
              for v in [CORE_ENV[k]] if k not in env]
    for k, (val, _) in CORE_ENV.items():
        env.setdefault(k, val)
    perms = d.setdefault("permissions", {})
    al = perms.setdefault("allow", [])
    add = [r for r in CORE_ALLOW if r not in al]
    al.extend(add)
    perms["allow"] = sorted(set(al))
    return nuevas, add


# ── MO-36: matchers muertos ────────────────────────────────────────────────────────────────
# `Bash(pytest*)` es sintaxis de `permissions`, no de `hooks`: el matcher de un hook es una regex sobre el
# NOMBRE de la tool, así que ese grupo no casa NUNCA y su hook no corre (harness-gotchas.md §matchers).
# Se vio en 4 proyectos; en musa convivía con el gate de RAM bueno. Como no dispara jamás, quitarlo no
# cambia lo que pasa hoy y deja de dar confianza falsa.
RX_MATCHER_MUERTO = re.compile(r"[A-Za-z]\(")


def quitar_matchers_muertos(d):
    """Quita de `hooks` los grupos con matcher «Tool(patrón)». Devuelve [(evento, matcher, comandos)]."""
    quitados = []
    for evento, grupos in list((d.get("hooks") or {}).items()):
        if not isinstance(grupos, list):
            continue
        vivos = []
        for g in grupos:
            m = g.get("matcher") or "" if isinstance(g, dict) else ""
            if RX_MATCHER_MUERTO.search(m):
                cmds = [h.get("command", "") for h in g.get("hooks") or []]
                quitados.append((evento, m, cmds))
            else:
                vivos.append(g)
        d["hooks"][evento] = vivos
    return quitados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proyecto")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    base = os.path.abspath(a.proyecto)
    sp = os.path.join(base, ".claude", "settings.json")
    if not os.path.exists(sp):
        print(f"✗ no hay {sp} — ¿es un proyecto con .claude/?"); return 2

    d = json.load(open(sp, encoding="utf-8"))
    env_nuevas, allow_nuevos = asegurar_env_y_allow(d)
    reales = datos_reales(base)                                        # sub-ola 2.29 (SE-41)
    protecciones = proteger_datos_reales(d, base) if reales else []
    hooks = d.setdefault("hooks", {})
    muertos = quitar_matchers_muertos(d)                              # MO-36
    añadidos, faltan_fichero, ya = [], [], []

    for entrada in CORE_HOOKS:
        evento, script, porque = entrada[:3]
        matcher = entrada[3] if len(entrada) > 3 else None
        if reales and script == "capture-task.sh":
            continue                                                   # sub-ola 2.29 (SE-41)
        ruta = os.path.join(base, ".claude", "hooks", script)
        if not os.path.exists(ruta):
            faltan_fichero.append(script)
            continue
        lista = hooks.setdefault(evento, [])
        if script in json.dumps(lista):
            ya.append(script); continue
        entrada_json = {"hooks": [{"type": "command",
                                   "command": f'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/{script}"'}]}
        if matcher:
            entrada_json = {"matcher": matcher, **entrada_json}
        lista.append(entrada_json)
        añadidos.append((evento, script, porque))

    retirados = [(h, por) for h, por in RETIRED_HOOKS.items() if h in json.dumps(hooks)]
    env_actual = d.get("env") or {}
    env_revisar = [(k, por) for (k, v), por in ENV_A_REVISAR.items()
                   if k in env_actual and (v is None or str(env_actual[k]) == v)]

    if a.dry_run:
        print(json.dumps(d.get("hooks", {}), ensure_ascii=False, indent=2)[:900])
    elif añadidos or env_nuevas or allow_nuevos or protecciones or muertos:
        # copia de seguridad antes de tocar el settings de nadie
        open(sp + ".bak", "w", encoding="utf-8").write(json.dumps(json.load(open(sp, encoding="utf-8")),
                                                                  ensure_ascii=False, indent=2))
        open(sp, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))

    for ev, m, cmds in muertos:
        print(f"  - {ev:<18} matcher muerto {m!r} (nunca casa): {', '.join(os.path.basename(c.split()[-1]) for c in cmds if c)}")
    for k, porque in env_nuevas:
        print(f"  + env  {k:<34} {porque[:62]}")
    if allow_nuevos:
        print(f"  + allow {len(allow_nuevos)} reglas de solo-lectura (evita que los workflows pregunten)")
    for e, s_, w in añadidos:
        print(f"  + {e:<18} {s_:<20} {w[:66]}")
    if ya:
        print(f"  = ya registrados: {', '.join(ya)}")
    if faltan_fichero:
        print(f"  ⚠ el .sh NO está en el proyecto (corre update-agent antes): {', '.join(faltan_fichero)}")
    for h, por in retirados:
        print(f"  ⚠ registrado y RETIRADO del template: {h} — {por}. Quítalo de settings.json "
              f"(no se hace solo: governance.md §2)")
    for k, por in env_revisar:
        print(f"  ⚠ env {k}={env_actual[k]!r}: {por}. No se cambia solo (governance.md §2)")
    if reales:                                                         # sub-ola 2.29 (SE-41)
        print(f"  = datos_reales_desarrollo: {reales} → capture-task no se registra")
        for c in protecciones:
            print(f"  + {c}")
        if "capture-task.sh" in json.dumps(hooks):
            print("  ⚠ capture-task.sh sigue registrado con datos reales en desarrollo: quítalo de "
                  "settings.json (no se hace solo: governance.md §2). Mientras, no escribe nada.")
    if not añadidos and not faltan_fichero and not env_nuevas and not allow_nuevos and not protecciones and not muertos:
        print("  OK: todos los hooks del CORE ya están registrados")
    elif (añadidos or env_nuevas or allow_nuevos or protecciones or muertos) and not a.dry_run:
        print(f"  → {sp} actualizado (copia en .bak)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
