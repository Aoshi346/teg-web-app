#!/usr/bin/env python3
"""Avisos del servidor TesisFar: siempre al registro local y, si hay correo configurado, por email.

Uso: notify.py <ok|error|info> "<asunto>" "<cuerpo>"
El correo se configura con configure-email.sh (fichero mail.env, permisos 600). Sin él, los avisos
solo quedan en logs/avisos.log: así el servidor funciona aunque el correo aún no esté listo.
"""

import os
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

BASE = Path(os.environ.get("TESISFAR_BASE", Path.home() / "tesisfar"))
ICONS = {"ok": "✅", "error": "❌", "info": "ℹ️"}


def read_env(path):
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    return values


def main():
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    level, subject, body = sys.argv[1:]
    subject = f"{ICONS.get(level, '')} TesisFar: {subject}".strip()

    log_dir = BASE / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "avisos.log").open("a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {subject}\n{body}\n\n")

    mail = read_env(BASE / "mail.env")
    if not (mail.get("SMTP_USER") and mail.get("SMTP_PASSWORD")):
        return 0

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail["SMTP_USER"]
    msg["To"] = mail.get("MAIL_TO") or mail["SMTP_USER"]
    msg.set_content(body)
    host = mail.get("SMTP_HOST", "smtp.gmail.com")
    port = int(mail.get("SMTP_PORT", "465"))
    try:
        with smtplib.SMTP_SSL(
            host, port, context=ssl.create_default_context(), timeout=30
        ) as smtp:
            smtp.login(mail["SMTP_USER"], mail["SMTP_PASSWORD"])
            smtp.send_message(msg)
    except (OSError, smtplib.SMTPException) as exc:
        with (log_dir / "avisos.log").open("a", encoding="utf-8") as fh:
            fh.write(
                f"[{datetime.now():%Y-%m-%d %H:%M:%S}] (no se pudo enviar el correo: {exc})\n\n"
            )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
