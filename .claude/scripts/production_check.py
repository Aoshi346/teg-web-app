#!/usr/bin/env python3
"""production_check.py — el control NEGATIVO de cada gate: ¿producción sigue intacta?

POR QUÉ (AN-20, cosechado de la pizarra de elvion: `control_produccion.sh`). Cuando se desarrolla en
la misma máquina donde corre producción, cada gate de un frente tiene que poder decir «y producción
no la he tocado». No compara ids de contenedor (producción se redespliega varias veces al día y eso es
legítimo): mide lo que importa.
  1. cada contenedor de producción pertenece al proyecto compose y a la carpeta que se declararon,
     y hay al menos los que se esperan;
  2. ningún contenedor de OTRO proyecto publica un puerto de producción;
  3. la URL pública responde 200 (si se declara).
Salida: 0 intacta · 1 algo la tocó · 2 NO SE PUDO MEDIR (sin docker, sin config). El 2 no es un 0: un
instrumento que no llega al sujeto aborta (`rules/verification.md`).

Config, en el proyecto: `.claude/production.json`
    {"container_prefix": "shop_", "compose_project": "shop", "working_dir": "/srv/shop",
     "min_containers": 4, "ports": [5432, 6379, 8000], "url": "https://shop.example.com"}

Uso:
    production_check.py [--config .claude/production.json]
    production_check.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

FMT = '{{.Names}}\t{{.Label "com.docker.compose.project"}}\t{{.Label "com.docker.compose.project.working_dir"}}\t{{.Ports}}'


def docker_ps() -> list[list[str]] | None:
    if not shutil.which("docker"):
        return None
    r = subprocess.run(["docker", "ps", "-a", "--format", FMT], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return None
    return [(ln.split("\t") + ["", "", "", ""])[:4] for ln in r.stdout.splitlines() if ln.strip()]


def http_code(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310 — URL declarada por el proyecto
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except (OSError, ValueError):
        return 0


def check(cfg: dict, rows: list[list[str]] | None, code_of=http_code) -> tuple[int, list[str]]:
    if rows is None:
        return 2, ["NO SE PUDO MEDIR: sin docker o `docker ps` falló"]
    out, bad = [], False
    pref = cfg.get("container_prefix", "")
    mine = [r for r in rows if pref and r[0].startswith(pref)]
    for name, proj, wdir, _ in mine:
        if (cfg.get("compose_project") and proj != cfg["compose_project"]) or \
           (cfg.get("working_dir") and wdir != cfg["working_dir"]):
            out.append(f"❌ {name} no es de producción (proyecto={proj or '—'} carpeta={wdir or '—'})")
            bad = True
    if len(mine) < int(cfg.get("min_containers", 1)):
        out.append(f"❌ solo {len(mine)} contenedores {pref}* (se esperaban {cfg.get('min_containers', 1)})")
        bad = True
    ports = {int(p) for p in cfg.get("ports", [])}
    for name, proj, _, published in rows:
        if proj == cfg.get("compose_project") or (pref and name.startswith(pref)):
            continue
        for p in ports:
            if f":{p}->" in published:
                out.append(f"❌ {name} (proyecto {proj or '—'}) publica el puerto de producción {p}")
                bad = True
    if cfg.get("url"):
        c = code_of(cfg["url"])
        if c != 200:
            out.append(f"❌ {cfg['url']} → {c or 'sin respuesta'}")
            bad = True
    if not bad:
        out.append(f"✅ producción intacta: {len(mine)} contenedores {pref}* suyos"
                   + (" · URL 200" if cfg.get("url") else ""))
    return (1 if bad else 0), out


def self_test() -> int:
    cfg = {"container_prefix": "shop_", "compose_project": "shop", "working_dir": "/srv/shop",
           "min_containers": 2, "ports": [5432], "url": "https://x"}
    ok_rows = [["shop_db", "shop", "/srv/shop", "127.0.0.1:5432->5432/tcp"], ["shop_web", "shop", "/srv/shop", ""],
               ["dev_db", "plat", "/home/dev", "127.0.0.1:5439->5432/tcp"]]
    cases = [
        ("todo en orden → 0", ok_rows, 200, 0),
        ("un frente publica el 5432 → 1", ok_rows + [["plat_db", "plat", "/home/dev", "0.0.0.0:5432->5432/tcp"]], 200, 1),
        ("un contenedor de producción levantado desde otra carpeta → 1",
         [["shop_db", "shop", "/home/dev/wt", ""], ok_rows[1]], 200, 1),
        ("falta un contenedor → 1", ok_rows[1:], 200, 1),
        ("la URL da 502 → 1", ok_rows, 502, 1),
        ("sin docker → 2 (no es un 0)", None, 200, 2),
    ]
    failures = 0
    for name, rows, code, want in cases:
        rc, _ = check(cfg, rows, lambda _u, c=code: c)
        failures += rc != want
        print(f"  {'✓' if rc == want else '✗'} {name}: {rc}")
    d = tempfile.mkdtemp()
    rc = main_with(["--config", os.path.join(d, "no-existe.json")])
    failures += rc != 2
    print(f"  {'✓' if rc == 2 else '✗'} sin config → 2: {rc}")
    print("self-test:", "OK" if not failures else f"{failures} FALLO(S)")
    return 1 if failures else 0


def main_with(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default=os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".claude", "production.json"))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    try:
        with open(a.config, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as e:
        print(f"NO SE PUDO MEDIR: sin config legible en {a.config} ({e.__class__.__name__})")
        return 2
    rc, lines = check(cfg, docker_ps())
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main_with(sys.argv[1:]))
