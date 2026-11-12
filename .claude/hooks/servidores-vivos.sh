#!/bin/bash
# servidores-vivos.sh — SessionEnd: avisa de los servidores de informes que siguen escuchando al cerrar.
#
# POR QUÉ EXISTE. Cada informe se sirve con `server.py` o `http.server` en 127.0.0.1 y nadie los
# cerraba: el 17-10-2026 había 52 abiertos (revisión integral, T03 · LI-5). Sobreviven a la sesión,
# ocupan RAM y puertos, y uno en 0.0.0.0 publica material de cliente.
#
# SOLO AVISA: no cierra nada (decisión del Usuario, 18-10). Lista PID, puerto y carpeta para que se
# cierren a mano con `kill <PID>`. Si alguno escucha fuera de 127.0.0.1, lo marca aparte.

command -v ss >/dev/null 2>&1 || exit 0

VIVOS=""
FUERA=""
while read -r direccion pid; do
  [ -n "$pid" ] || continue
  cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null)
  cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null)
  # Un informe es un http.server, o un server.py lanzado desde la carpeta de un plan o un scratchpad.
  # Así no se confunde con otros server.py (mocks, servicios) que viven en otra parte.
  case "$cmd" in
    *http.server*) ;;
    *server.py*) case "$cwd" in *"/.docs/"*|*"/scratchpad"*|*"/tmp/claude"*) ;; *) continue ;; esac ;;
    *) continue ;;
  esac
  linea="  PID $pid · $direccion · ${cwd:-?}"
  case "$direccion" in
    127.0.0.1:*|\[::1\]:*) VIVOS="$VIVOS\n$linea" ;;
    *) FUERA="$FUERA\n$linea" ;;
  esac
done < <(${SERVIDORES_VIVOS_SS:-ss -tlnpH} 2>/dev/null | sed -nE 's/.*LISTEN +[0-9]+ +[0-9]+ +([^ ]+) .*pid=([0-9]+).*/\1 \2/p')

[ -z "$VIVOS$FUERA" ] && exit 0

if [ -n "$FUERA" ]; then
  echo "⚠️  Servidores de informes escuchando FUERA de 127.0.0.1 (exponen material):"
  printf "%b\n" "${FUERA#\\n}"
fi
if [ -n "$VIVOS" ]; then
  echo "ℹ️  Servidores de informes que siguen vivos al cerrar la sesión (ciérralos si ya no hacen falta):"
  printf "%b\n" "${VIVOS#\\n}"
fi
echo "   Para cerrar uno: kill <PID>"
exit 0
