#!/usr/bin/env python3
"""check_plugins.py — inventario de plugins y marketplaces (política de mods y plugins, SE-D12).

Solo LEE `~/.claude/plugins/` (installed_plugins.json, known_marketplaces.json y la caché). No instala,
no borra, no toca nada. Lo que lista es lo que `rules/agent-security.md` §5 manda mirar:

  · marketplaces que NO son el oficial de Anthropic (un plugin de un tercero puede traer hooks y
    comandos; los de un mod pueden aprobar tool calls: política en §5);
  · plugins de esos marketplaces, con versión y commit (la versión fijada es lo que se revisó);
  · residuos `temp_git_*` / `temp_subdir_*` en la caché (instalaciones que se quedaron a medias).

    python3 .claude/scripts/check_plugins.py                       # inventario; exit 0
    python3 .claude/scripts/check_plugins.py --estricto            # exit 1 si hay terceros o residuos
    python3 .claude/scripts/check_plugins.py --permitidos openai-codex   # terceros ya revisados: no cuentan
    python3 .claude/scripts/check_plugins.py --home /ruta          # otro HOME (para probar)

Límite: el inventario dice QUÉ hay, no si es seguro. Revisar un plugin es leerlo entero (§5).
"""
import argparse
import json
import os
import sys

OFICIAL = "claude-plugins-official"


def cargar(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", default=os.path.expanduser("~"))
    ap.add_argument("--estricto", action="store_true")
    ap.add_argument("--permitidos", nargs="*", default=[])
    a = ap.parse_args()
    base = os.path.join(a.home, ".claude", "plugins")
    mk = cargar(os.path.join(base, "known_marketplaces.json"))
    ins = cargar(os.path.join(base, "installed_plugins.json"))
    if mk is None or ins is None:
        print("check_plugins: sin %s (¿no hay plugins instalados?)" % base)
        return 0
    terceros = sorted(m for m in mk if m != OFICIAL)
    print("Marketplaces: %d" % len(mk))
    for m, v in sorted(mk.items()):
        src = (v.get("source") or {})
        marca = "oficial" if m == OFICIAL else ("TERCERO (revisado)" if m in a.permitidos else "TERCERO")
        print("  · %-24s %-8s %s" % (m, src.get("source", "?"), src.get("repo") or src.get("url") or ""), "→", marca)
    print("Plugins instalados:")
    n3 = 0
    for k, v in sorted((ins.get("plugins") or {}).items()):
        mkt = k.split("@", 1)[-1]
        vers = sorted({"%s%s" % (x.get("version", "?"), ("@" + x["gitCommitSha"][:8]) if x.get("gitCommitSha") else "") for x in v})
        tercero = mkt != OFICIAL and mkt not in a.permitidos
        n3 += tercero
        print("  · %-45s %s%s" % (k, ", ".join(vers[:3]) + (" …" if len(vers) > 3 else ""), "   ← TERCERO sin revisar" if tercero else ""))
    cache = os.path.join(base, "cache")
    res = sorted(d for d in (os.listdir(cache) if os.path.isdir(cache) else []) if d.startswith(("temp_git_", "temp_subdir_")))
    print("Residuos de instalación en la caché: %d" % len(res))
    for d in res:
        print("  · " + d)
    if res:
        print("  (los borra el Usuario con `rm -r -- ~/.claude/plugins/cache/temp_*` tras mirar que ninguna sesión instala ahora)")
    sin_revisar = [m for m in terceros if m not in a.permitidos]
    print("\nResumen: %d marketplace(s) de terceros sin revisar, %d plugin(s) de terceros sin revisar, %d residuo(s)." % (len(sin_revisar), n3, len(res)))
    return 1 if (a.estricto and (sin_revisar or n3 or res)) else 0


if __name__ == "__main__":
    sys.exit(main())
