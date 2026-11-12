#!/usr/bin/env bash
# TesisFar — copia de seguridad diaria (la lanza el timer tesisfar-backup).
# Guarda la BD y los ficheros subidos en ~/tesisfar/backups y, además, en el disco de Windows
# (C:\TesisFar\backups), para que sobrevivan aunque Ubuntu/WSL se rompa. Conserva 14 días.
set -Eeuo pipefail

BASE="${TESISFAR_BASE:-$HOME/tesisfar}"
KIT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
DATA="$BASE/data"
DEST="$BASE/backups/daily"
WINDOWS_DEST="/mnt/c/TesisFar/backups"
STAMP="$(date +%Y%m%d-%H%M)"
KEEP_DAYS=14
mkdir -p "$DEST"

fail() {
  python3 "$KIT/notify.py" error "Falló la copia de seguridad diaria" "$1" || true
  exit 1
}
trap 'fail "Error en la línea $LINENO de backup.sh"' ERR

python3 "$KIT/sqlite_backup.py" "$DATA/db.sqlite3" "$DEST/db-$STAMP.sqlite3"
tar -czf "$DEST/media-$STAMP.tar.gz" -C "$DATA" media

find "$DEST" -type f -mtime +"$KEEP_DAYS" -delete

if [[ -d /mnt/c ]]; then
  mkdir -p "$WINDOWS_DEST"
  cp "$DEST/db-$STAMP.sqlite3" "$DEST/media-$STAMP.tar.gz" "$WINDOWS_DEST/"
  find "$WINDOWS_DEST" -type f -mtime +"$KEEP_DAYS" -delete
fi
