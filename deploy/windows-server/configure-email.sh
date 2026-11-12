#!/usr/bin/env bash
# TesisFar — activa (o cambia) los avisos por correo. Se puede ejecutar en cualquier momento:
#   bash ~/tesisfar/bin/configure-email.sh
# Pide la cuenta de Gmail y su CONTRASEÑA DE APLICACIÓN (no la contraseña normal):
# https://myaccount.google.com/apppasswords
set -Eeuo pipefail

BASE="${TESISFAR_BASE:-$HOME/tesisfar}"
KIT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
MAIL_ENV="$BASE/mail.env"

read -rp "Cuenta de Gmail que envía los avisos: " smtp_user
read -rsp "Contraseña de aplicación de 16 letras (no se ve al escribir): " smtp_password
echo
smtp_password="${smtp_password// /}"
read -rp "¿A qué correo llegan los avisos? [Enter = $smtp_user]: " mail_to
mail_to="${mail_to:-$smtp_user}"

umask 077
cat >"$MAIL_ENV" <<EOF
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=$smtp_user
SMTP_PASSWORD=$smtp_password
MAIL_TO=$mail_to
EOF
chmod 600 "$MAIL_ENV"

if python3 "$KIT/notify.py" info "Correo configurado" "Los avisos del servidor TesisFar llegarán a $mail_to."; then
  echo "✅ Correo de prueba enviado a $mail_to. Revisa la bandeja (y el spam)."
else
  echo "❌ No se pudo enviar. Motivo en $BASE/logs/avisos.log. Revisa la contraseña de aplicación."
  exit 1
fi
