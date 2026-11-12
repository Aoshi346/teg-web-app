#!/bin/bash
# notify-telegram.sh — Stop (síncrono, timeout 15 s): avisa por Telegram cuando PROGRESS.json pasa
# a `completed` (DONE) o a `blocked` (BLOCKED). Sustituye a notify-gateway.sh, que llamaba a una
# herramienta de aviso no instalada y salía en silencio (MO-14, sub-ola 2.20; el viejo, en
# _archive/2026-10-20/hooks/).
#
# Aquí solo va la VÍA RÁPIDA, porque Stop salta en cada respuesta: si PROGRESS.json no ha cambiado
# desde la última mirada, sale sin arrancar Python. La decisión, el envío y el aviso de fallo los
# hace `scripts/avisar.py --hook` (sale siempre con 0; si el aviso no llega, lo dice con
# systemMessage, que en un hook síncrono ve el Usuario).
#
# NO es `async` a propósito: el systemMessage de un hook async no se enseña al Usuario (solo le
# llega a Claude en el turno siguiente) y en `claude -p` un hook async se mata al cerrar.
#
# Apagarlo: TL_AVISO=off. Probarlo sin mandar nada: TL_AVISO_API=http://127.0.0.1:<puerto>
# (una API falsa; en el template, _archive/2026-10-20/medicion-2.20/telegram_falso.py).

P="${CLAUDE_PROJECT_DIR:-$PWD}"
[ "${TL_AVISO:-}" = "off" ] && exit 0
[ -f "$P/PROGRESS.json" ] || exit 0
if [ ! -f "$P/.claude/scripts/avisar.py" ]; then  # registrado y sin su script: que se vea
  printf '{"systemMessage": "%s"}\n' "⚠ notify-telegram.sh: falta .claude/scripts/avisar.py; \
el aviso por Telegram no está montado (TL_AVISO=off para callarlo)"
  exit 0
fi

CLAVE=$(printf '%s' "$P" | sha1sum | cut -c1-16)
MARCA="${XDG_STATE_HOME:-$HOME/.local/state}/tl-aviso/$CLAVE.json"
if [ -f "$MARCA" ] && [ ! "$P/PROGRESS.json" -nt "$MARCA" ]; then
  # Un PROGRESS.json que es el índice de planes (progress_index.py) no cambia cuando cambia un
  # plan: entonces se mira también el PROGRESS.json de cada plan.
  grep -q '"planes"' "$P/PROGRESS.json" 2>/dev/null || exit 0
  [ -n "$(find "$P/.docs/plans" "$P/.specify/sessions" -maxdepth 2 -name PROGRESS.json \
          -newer "$MARCA" -print -quit 2>/dev/null)" ] || exit 0
fi

exec python3 -I "$P/.claude/scripts/avisar.py" --hook --proyecto "$P"
