#!/usr/bin/env bash
# TesisFar — instalador del servidor (Ubuntu dentro de WSL2, en el PC con Windows).
#
# Se ejecuta UNA vez, dentro de Ubuntu, con tu usuario normal (no root):
#   curl -fsSLo instalar.sh https://raw.githubusercontent.com/Aoshi346/teg-web-app/master/deploy/windows-server/install.sh
#   bash instalar.sh
#
# Volver a ejecutarlo es seguro: lo que ya está hecho se respeta (clave secreta, base de datos,
# administrador) y solo se rehacen la configuración y los servicios.
#
# Opciones: --branch <rama>   (por defecto master)   --repo <url de git>
set -Eeuo pipefail

BRANCH="master"
REPO_URL="https://github.com/Aoshi346/teg-web-app.git"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    --repo) REPO_URL="$2"; shift 2 ;;
    *) echo "Opción desconocida: $1" >&2; exit 2 ;;
  esac
done
GITHUB_REPO="$(sed -E 's#^https://github.com/##; s#\.git$##' <<<"$REPO_URL")"

BASE="$HOME/tesisfar"
TAILSCALE_NAME="tesisfar"

paso() { printf '\n\033[1;34m▶ %s\033[0m\n' "$*"; }
ok() { printf '\033[0;32m  ✓ %s\033[0m\n' "$*"; }
aviso() { printf '\033[0;33m  ! %s\033[0m\n' "$*"; }
error() { printf '\033[0;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
trap 'error "Algo falló en la línea $LINENO. Copia lo de arriba y pásaselo a quien te ayude."' ERR

# ── 1. Comprobaciones ───────────────────────────────────────────────────────────────────────
paso "1/10 Comprobando el entorno"
[[ $EUID -ne 0 ]] || error "Ejecútalo con tu usuario normal, sin sudo (el script pide sudo cuando lo necesita)."
grep -qi microsoft /proc/version || aviso "No parece WSL; sigo igualmente."
sudo -v || error "Hace falta tu contraseña de Ubuntu para instalar paquetes."

if [[ "$(ps -p 1 -o comm=)" != "systemd" ]]; then
  if ! grep -qs '^systemd=true' /etc/wsl.conf; then
    printf '[boot]\nsystemd=true\n' | sudo tee -a /etc/wsl.conf >/dev/null
  fi
  aviso "He activado systemd en WSL; hace falta reiniciar Ubuntu una vez:"
  echo "    1. Cierra esta ventana."
  echo "    2. En PowerShell escribe:   wsl --shutdown"
  echo "    3. Abre Ubuntu otra vez y vuelve a ejecutar:   bash instalar.sh"
  exit 0
fi
ok "WSL con systemd"

# ── 2. Paquetes ─────────────────────────────────────────────────────────────────────────────
paso "2/10 Instalando paquetes (Python, Node.js, Caddy, Tailscale) — puede tardar varios minutos"
sudo apt-get update -qq
sudo apt-get install -y -qq git curl ca-certificates gnupg sqlite3 python3 python3-venv >/dev/null

if ! command -v node >/dev/null || (( $(node -p 'process.versions.node.split(".")[0]') < 20 )); then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - >/dev/null
  sudo apt-get install -y -qq nodejs >/dev/null
fi
ok "Node.js $(node -v)"

if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' |
    sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' |
    sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
  sudo apt-get update -qq && sudo apt-get install -y -qq caddy >/dev/null
fi
sudo systemctl disable --now caddy.service >/dev/null 2>&1 || true   # usamos nuestro propio servicio
ok "Caddy $(caddy version | cut -d' ' -f1)"

if ! command -v tailscale >/dev/null; then
  curl -fsSL https://tailscale.com/install.sh | sh >/dev/null
fi
sudo systemctl enable --now tailscaled >/dev/null
ok "Tailscale instalado"

# ── 3. Tailscale ────────────────────────────────────────────────────────────────────────────
paso "3/10 Conectando con tu cuenta de Tailscale"
if ! sudo tailscale status >/dev/null 2>&1; then
  echo "  Se mostrará un enlace: ábrelo en el navegador de Windows e inicia sesión con tu cuenta de Tailscale."
  sudo tailscale up --hostname="$TAILSCALE_NAME"
fi
PUBLIC_HOST="$(sudo tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')"
[[ -n "$PUBLIC_HOST" ]] || error "No pude leer el nombre del equipo en Tailscale."
ok "Este PC en Tailscale: $PUBLIC_HOST"

# ── 4. Carpetas y configuración ─────────────────────────────────────────────────────────────
paso "4/10 Preparando carpetas y configuración en $BASE"
mkdir -p "$BASE"/{releases,state,logs,backups,data/media,data/django-static,data/cache}
chmod 700 "$BASE"

cat >"$BASE/deploy.conf" <<EOF
REPO_URL=$REPO_URL
BRANCH=$BRANCH
GITHUB_REPO=$GITHUB_REPO
PUBLIC_HOST=$PUBLIC_HOST
EOF

ENV_FILE="$BASE/tesisfar.env"
if [[ -f "$ENV_FILE" ]]; then
  SECRET_KEY="$(sed -n 's/^SECRET_KEY=//p' "$ENV_FILE")"
else
  SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
fi
umask 077
cat >"$ENV_FILE" <<EOF
DJANGO_ENV=production
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$PUBLIC_HOST,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://$PUBLIC_HOST
DATABASE_PATH=$BASE/data/db.sqlite3
MEDIA_ROOT=$BASE/data/media
STATIC_ROOT=$BASE/data/django-static
STATIC_URL=/django-static/
CACHE_DIR=$BASE/data/cache
EOF
umask 022
ok "Configuración escrita (la clave secreta se conserva entre ejecuciones)"

# ── 5. Código ───────────────────────────────────────────────────────────────────────────────
paso "5/10 Descargando el código de GitHub ($GITHUB_REPO, rama $BRANCH)"
if [[ -d "$BASE/repo/.git" ]]; then
  git -C "$BASE/repo" fetch --quiet origin "$BRANCH"
  git -C "$BASE/repo" checkout --quiet --force "origin/$BRANCH"
else
  git clone --quiet --branch "$BRANCH" "$REPO_URL" "$BASE/repo"
fi
ln -sfn current/deploy/windows-server "$BASE/bin"
KIT="$BASE/repo/deploy/windows-server"
ok "Código en $BASE/repo"

# ── 6. Servicios ────────────────────────────────────────────────────────────────────────────
paso "6/10 Registrando los servicios del sistema"
render() { sed -e "s#@USER@#$USER#g" -e "s#@BASE@#$BASE#g" -e "s#@PUBLIC_HOST@#$PUBLIC_HOST#g" "$1"; }
for unit in tesisfar-backend.service tesisfar-frontend.service tesisfar-proxy.service \
            tesisfar-update.service tesisfar-update.timer tesisfar-backup.service tesisfar-backup.timer; do
  render "$KIT/templates/$unit" | sudo tee "/etc/systemd/system/$unit" >/dev/null
done
render "$KIT/templates/sudoers" >"$BASE/state/sudoers.tmp"
sudo visudo -cf "$BASE/state/sudoers.tmp" >/dev/null
sudo install -m 440 -o root -g root "$BASE/state/sudoers.tmp" /etc/sudoers.d/tesisfar
rm -f "$BASE/state/sudoers.tmp"
render "$KIT/templates/Caddyfile" >"$BASE/Caddyfile"
caddy validate --config "$BASE/Caddyfile" --adapter caddyfile >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now tesisfar-proxy.service >/dev/null
sudo systemctl enable tesisfar-backend.service tesisfar-frontend.service >/dev/null 2>&1
ok "Servicios registrados"

# ── 7. Primera versión ──────────────────────────────────────────────────────────────────────
paso "7/10 Compilando y arrancando la app (la primera vez tarda 5-15 minutos)"
if [[ -L "$BASE/current" ]]; then
  ok "Ya hay una versión en marcha; el actualizador automático se encarga de las siguientes"
else
  "$KIT/update.sh" --force || error "La primera compilación falló. Registro: $BASE/logs/deploy.log"
  ok "App en marcha"
fi

# ── 8. Administrador ────────────────────────────────────────────────────────────────────────
paso "8/10 Cuenta de Administrador"
manage() {
  # shellcheck source=/dev/null
  (cd "$BASE/current/backend" && set -a && source "$ENV_FILE" && set +a &&
    .venv/bin/python manage.py "$@")
}
if [[ "$(manage shell -c "from api.models import User; print(User.objects.filter(role='Administrador').exists())")" == "True" ]]; then
  ok "Ya existe un Administrador"
else
  echo "  Crea la primera cuenta de Administrador (con ella entrarás en la web):"
  read -rp "    Correo: " ADMIN_EMAIL
  read -rp "    Nombre: " ADMIN_FIRST
  read -rp "    Apellido: " ADMIN_LAST
  while true; do
    read -rsp "    Contraseña (mín. 8, no se ve al escribir): " ADMIN_PASSWORD; echo
    read -rsp "    Repite la contraseña: " ADMIN_PASSWORD2; echo
    [[ "$ADMIN_PASSWORD" == "$ADMIN_PASSWORD2" ]] && break
    aviso "No coinciden; otra vez."
  done
  ADMIN_EMAIL="$ADMIN_EMAIL" ADMIN_FIRST="$ADMIN_FIRST" ADMIN_LAST="$ADMIN_LAST" ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  manage shell -c "
import os
from django.contrib.auth.password_validation import validate_password
from api.models import User
email = os.environ['ADMIN_EMAIL'].strip().lower()
validate_password(os.environ['ADMIN_PASSWORD'])
User.objects.create_superuser(
    email=email, password=os.environ['ADMIN_PASSWORD'],
    first_name=os.environ['ADMIN_FIRST'], last_name=os.environ['ADMIN_LAST'],
    role='Administrador', status='active',
)
print('ok')" >/dev/null || error "No se pudo crear el Administrador (¿contraseña demasiado simple o correo repetido?). Vuelve a ejecutar el instalador."
  unset ADMIN_PASSWORD ADMIN_PASSWORD2
  ok "Administrador creado"
fi

# ── 9. Publicar en internet ─────────────────────────────────────────────────────────────────
paso "9/10 Publicando en internet con Tailscale Funnel"
echo "  Si Tailscale muestra un enlace para activar Funnel/HTTPS, ábrelo, actívalo y vuelve aquí."
sudo tailscale funnel --bg 8080
ok "Publicado en https://$PUBLIC_HOST"

# ── 10. Automático ──────────────────────────────────────────────────────────────────────────
paso "10/10 Activando actualizaciones automáticas y copias de seguridad"
sudo systemctl enable --now tesisfar-update.timer tesisfar-backup.timer >/dev/null
ok "Busca versiones nuevas en '$BRANCH' cada 5 minutos · copia de seguridad diaria a las 03:30"

if [[ -d /mnt/c ]]; then
  mkdir -p /mnt/c/TesisFar && cp "$KIT/install-windows.ps1" /mnt/c/TesisFar/
fi

printf '\n\033[1;32m✅ Listo. TesisFar está en:  https://%s\033[0m\n\n' "$PUBLIC_HOST"
echo "Pendiente (una vez), en Windows — PowerShell COMO ADMINISTRADOR:"
echo "    powershell -ExecutionPolicy Bypass -File C:\\TesisFar\\install-windows.ps1"
echo "  y después el inicio de sesión automático (guía, paso 4)."
if [[ ! -f "$BASE/mail.env" ]]; then
  echo "  • Avisos por correo (opcional, cuando tengas la contraseña de aplicación de Gmail):"
  echo "        bash $BASE/bin/configure-email.sh"
  echo "    Mientras tanto, los avisos quedan en $BASE/logs/avisos.log"
fi
