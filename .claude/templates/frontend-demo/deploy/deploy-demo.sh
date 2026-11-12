#!/usr/bin/env bash
# deploy-demo.sh — despliega la demo de PRUEBAS de un COMMIT (plantilla de templates/frontend-demo, AN-22).
#
# Uso:   sudo bash infra/deploy-demo.sh [ref-de-git] [--reset-db]        (por defecto: develop)
#        --reset-db   borra y recrea la base de la demo (solo datos sintéticos de seed_demo)
#
# Qué hace, y por qué así:
# - Despliega un COMMIT (`git archive`), nunca el árbol de trabajo: los agentes editan el árbol y un
#   reinicio a mitad serviría código a medias. El sha desplegado queda en $DEST/src/DEPLOYED.
# - Cambio casi atómico: el código nuevo se monta entero en src.new y se intercambia con dos `mv`
#   seguidos (sin `src` solo entre los dos; el servicio se reinicia después). Para atómico de verdad:
#   un enlace `current` y `ln -sfn` + `mv -T`.
# - Backend en 127.0.0.1:$API_PORT (systemd, usuario dinámico sin privilegios); solo nginx da la cara
#   (nginx/demo.conf). Nada nuevo escucha en 0.0.0.0 (rules/security.md).
# - Datos: SOLO los de seed_demo, sintéticos, y se vuelven a sembrar en cada despliegue (idempotente).
#   La demo envejece («hace 3 días» deja de serlo): seed_demo debe anclar las fechas a hoy al sembrar.
# - Los secretos se generan aquí la primera vez, fuera del repo y con 0600. Nunca en este fichero.
#
# Desplegar es acción con OK del Usuario (rules/governance.md §2), también para una demo.
set -euo pipefail

# ── Lo propio del proyecto: rellénalo ─────────────────────────────────────────────────────────
APP=miapp                                   # nombre corto: servicio, carpetas y base
DOMAIN=demo.ejemplo.es                      # el de nginx/demo.conf
API_PORT=8041                               # backend en 127.0.0.1:$API_PORT
DB_CONTAINER=miapp_dev-db-1                 # el Postgres de la franja (docker), o vacío si es del host
SETTINGS=config.settings.demo
SEED_CMDS=("migrate --no-input" "seed_demo")
# ──────────────────────────────────────────────────────────────────────────────────────────────

REF="develop"; RESET=0
for a in "$@"; do case "$a" in --reset-db) RESET=1 ;; *) REF="$a" ;; esac; done
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="/opt/$APP-demo"; WWW="/var/www/$APP-demo"; ETC="/etc/$APP-demo"; ENVFILE="$ETC/env"
DB="${APP}_demo"
SHA="$(git -C "$REPO" rev-parse --short "$REF")"
echo "▶ desplegando $REF ($SHA)"

# 1) Entorno, una sola vez: secretos generados aquí, fuera del repo.
install -d -m 700 "$ETC"
if [ ! -f "$ENVFILE" ]; then
  umask 077
  cat > "$ENVFILE" <<EOV
DJANGO_SETTINGS_MODULE=$SETTINGS
DJANGO_SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_urlsafe(50))')
DJANGO_ALLOWED_HOSTS=$DOMAIN,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://$DOMAIN
SESSION_COOKIE_SECURE=1
POSTGRES_DB=$DB
DEMO_PASSWORD=$(python3 -c 'import secrets;print(secrets.token_urlsafe(12))')
EOV
  echo "  entorno creado en $ENVFILE (añade a mano la conexión a la base; no va en el repo)"
fi

# 2) Código del commit, en una carpeta nueva.
install -d "$DEST"
rm -rf "$DEST/src.new" && mkdir -p "$DEST/src.new"
git -C "$REPO" archive "$REF" | tar -x -C "$DEST/src.new"
echo "$SHA" > "$DEST/src.new/DEPLOYED"

# 3) Dependencias del backend en un venv que se reutiliza.
[ -x "$DEST/venv/bin/python" ] || python3 -m venv "$DEST/venv"
"$DEST/venv/bin/pip" install -q -r "$DEST/src.new/backend/requirements.txt"

# 4) Frontend del mismo commit. Sin la maqueta: VITE_MOCKUP=0 deja los handlers fuera del bundle.
( cd "$DEST/src.new/frontend" && npm ci --no-audit --no-fund --loglevel=error >/dev/null \
  && VITE_MOCKUP="${VITE_MOCKUP:-0}" npm run -s build >/dev/null )

# 5) Intercambio (dos mv seguidos).
mv "$DEST/src" "$DEST/src.old" 2>/dev/null || true
mv "$DEST/src.new" "$DEST/src" && rm -rf "$DEST/src.old"

# 6) Base: crear si falta (o recrear con --reset-db), migrar y sembrar.
psql_admin() { if [ -n "$DB_CONTAINER" ]; then docker exec "$DB_CONTAINER" psql -U postgres -d postgres "$@"; else sudo -u postgres psql -d postgres "$@"; fi; }
if [ "$RESET" = 1 ]; then
  systemctl stop "$APP-demo" 2>/dev/null || true
  psql_admin -qc "DROP DATABASE IF EXISTS $DB WITH (FORCE);"
  echo "  base $DB borrada (--reset-db)"
fi
psql_admin -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -q 1 || psql_admin -qc "CREATE DATABASE $DB;"
manage() { ( set -a; . "$ENVFILE"; set +a; cd "$DEST/src/backend" && "$DEST/venv/bin/python" manage.py "$@" ); }
for cmd in "${SEED_CMDS[@]}"; do
  # shellcheck disable=SC2086  # la orden se parte en palabras a propósito
  manage $cmd | tail -1
done

# 7) Servicio systemd (idempotente).
cat > "/etc/systemd/system/$APP-demo.service" <<EOU
[Unit]
Description=$APP — demo de pruebas (gunicorn en 127.0.0.1:$API_PORT)
After=network-online.target

[Service]
EnvironmentFile=$ENVFILE
WorkingDirectory=$DEST/src/backend
ExecStart=$DEST/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:$API_PORT --workers 2 --timeout 120
DynamicUser=yes
StateDirectory=$APP-demo
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOU
systemctl daemon-reload
systemctl enable -q "$APP-demo"
systemctl restart "$APP-demo"

# 8) Estáticos del front.
install -d "$WWW"
rsync -a --delete "$DEST/src/frontend/dist/" "$WWW/"

# 9) Comprobación: por dentro y por fuera, y que se sirve lo que se desplegó.
for _ in $(seq 1 20); do curl -fsS "http://127.0.0.1:$API_PORT/" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS -o /dev/null "http://127.0.0.1:$API_PORT/" && echo "  backend 127.0.0.1:$API_PORT OK" \
  || { echo "  ⚠ backend NO responde (journalctl -u $APP-demo)"; exit 1; }
curl -fsS -o /dev/null -w "  https://$DOMAIN/ → %{http_code}\n" "https://$DOMAIN/"
echo "✔ demo en $SHA ($(cat "$DEST/src/DEPLOYED"))"
