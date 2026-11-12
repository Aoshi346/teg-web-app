#!/usr/bin/env bash
# compose-wrapper.sh — el único punto de entrada de UN entorno compose (stage, dev, una herramienta).
#
# Se copia a la raíz del proyecto con el nombre del entorno (`./stage`, `./langfuse`), se rellena el
# bloque CONFIG y, desde ese día, nadie escribe `docker compose` a pelo para ese entorno.
#
# Por qué: en un servidor con varios entornos, un `docker compose` lanzado desde la carpeta
# equivocada, sin `--env-file` o sin `-p`, recrea los contenedores de OTRO entorno —producción
# incluida— con la configuración de este. Compose interpola con el `.env` de la carpeta del FICHERO
# compose, no de donde estás; y con un `container_name: ${PREFIJO:-prod}_db`, olvidar el
# `--env-file` cae al valor por defecto. Fijar el `-p` correcto NO basta. Este guion fija las tres
# cosas y, antes de cada orden, mira lo que compose VA a hacer (`docker compose config`).
#
# Uso:   ./stage up -d · ./stage logs -f backend · ./stage ps · ./stage check
#        ./stage net-connect <contenedor> <red> [alias]   (la red, por nombre EXACTO)
# Exit:  lo de docker compose · 1 si la guarda se niega · 2 si falta docker o la config.
# Lo cita: commands/deploy.md §Montar el proyecto en un servidor NUEVO y rules/security.md.
# Prueba: python3 .claude/smoke/harvest/compose_wrapper.py
set -euo pipefail
cd "$(dirname "$0")"

# ── CONFIG (lo único que se toca al copiarlo) ────────────────────────────────────────────────────
PROJECT="miapp-stage"                          # el -p: nombre de proyecto propio de este entorno
ENV_FILE=".env"                                # el que interpola; ruta relativa a este guion
FILES=(infra/docker-compose.yml infra/docker-compose.stage.yml)
PROFILES=()                                    # p. ej. (mocks): si en este entorno no son opcionales
MARKERS=("APP_ENV=stage" "STACK_PREFIX=miapp_stage")   # líneas EXACTAS que tiene que traer ENV_FILE
NAME_PREFIX="miapp_stage"                      # todo container_name, red y volumen con nombre
EXTERNAL_NETWORKS=()                           # redes externas permitidas, por nombre exacto
# ── fin CONFIG ───────────────────────────────────────────────────────────────────────────────────

command -v docker >/dev/null || { echo "compose-wrapper: no hay docker" >&2; exit 2; }
[ -f "$ENV_FILE" ] || { echo "ABORTADO: falta $ENV_FILE en $(pwd)" >&2; exit 2; }
for m in "${MARKERS[@]}"; do
  grep -qxF -- "$m" "$ENV_FILE" || { echo "ABORTADO: $ENV_FILE no trae la línea «$m»" >&2; exit 1; }
done

COMPOSE=(docker compose --env-file "$ENV_FILE" --project-name "$PROJECT")
for p in "${PROFILES[@]}"; do COMPOSE+=(--profile "$p"); done
for f in "${FILES[@]}"; do COMPOSE+=(-f "$f"); done

guard() {
  local rendered
  rendered=$("${COMPOSE[@]}" config --format json) || { echo "ABORTADO: compose config falla" >&2; return 2; }
  CW_PROJECT="$PROJECT" CW_PREFIX="$NAME_PREFIX" CW_EXTERNAL="${EXTERNAL_NETWORKS[*]:-}" \
    python3 -c '
import json, os, subprocess, sys
cfg = json.load(sys.stdin)
project, prefix = os.environ["CW_PROJECT"], os.environ["CW_PREFIX"]
external_ok = set(os.environ["CW_EXTERNAL"].split())
bad = []
def owner(name):
    r = subprocess.run(["docker", "inspect", "-f",
                        "{{index .Config.Labels \"com.docker.compose.project\"}}", name],
                       capture_output=True, text=True)
    return None if r.returncode else r.stdout.strip()
for svc, s in (cfg.get("services") or {}).items():
    name = s.get("container_name")
    if not name:
        continue
    if not name.startswith(prefix):
        bad.append(f"servicio {svc}: container_name «{name}» no empieza por «{prefix}»")
    o = owner(name)
    if o is not None and o != project:
        who = o or "ninguno (no lo creó compose)"
        bad.append(f"servicio {svc}: «{name}» ya existe y es del proyecto «{who}»")
for kind in ("networks", "volumes"):
    for key, n in (cfg.get(kind) or {}).items():
        n = n or {}
        name = n.get("name", "")
        if n.get("external"):
            if kind == "networks" and name not in external_ok:
                bad.append(f"red externa «{name}» no está en EXTERNAL_NETWORKS")
            elif kind == "volumes":
                bad.append(f"volumen externo «{name}»: un entorno no monta volúmenes de otro")
        elif name and not name.startswith(prefix) and not name.startswith(project + "_"):
            bad.append(f"{kind[:-1]} «{name}» no empieza por «{prefix}»")
for b in bad:
    print(f"ABORTADO: {b}", file=sys.stderr)
sys.exit(1 if bad else 0)
' <<<"$rendered"
}

case "${1:-}" in
  "") sed -n '2,18p' "$0" | sed 's/^# \?//'; exit 0 ;;
  -*) echo "ABORTADO: las opciones globales (-p, -f, --env-file…) las fija el guion" >&2; exit 1 ;;
  check) guard && echo "compose-wrapper: $PROJECT en orden"; exit $? ;;
  net-connect)
    [ $# -ge 3 ] || { echo "uso: $0 net-connect <contenedor> <red> [alias]" >&2; exit 2; }
    # Por nombre EXACTO: un grep de redes casa con las de stage, dev y producción a la vez.
    docker network inspect --format '{{.Name}}' "$3" 2>/dev/null | grep -qxF -- "$3" \
      || { echo "ABORTADO: no hay una red llamada exactamente «$3»" >&2; exit 1; }
    # Y el contenedor tiene que ser de ESTE proyecto: conectar uno de producción a otra red tampoco.
    owner=$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$2" 2>/dev/null) \
      || { echo "ABORTADO: no hay un contenedor «$2»" >&2; exit 1; }
    [ "$owner" = "$PROJECT" ] \
      || { echo "ABORTADO: «$2» es del proyecto «${owner:-ninguno}», no de $PROJECT" >&2; exit 1; }
    exec docker network connect ${4:+--alias "$4"} "$3" "$2" ;;
esac
guard
exec "${COMPOSE[@]}" "$@"
