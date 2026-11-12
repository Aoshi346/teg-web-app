#!/bin/bash
# Prueba REAL del detector de sockets, dentro de un namespace de red VACÍO (no toca la red de la máquina).
# Uso: unshare -rn bash socket_real.sh <0.0.0.0|127.0.0.1> <ruta de check_puertos_docker.py>
BIND="$1"; SCRIPT="$2"
ip link set lo up 2>/dev/null
python3 -m http.server 2222 --bind "$BIND" >/dev/null 2>&1 &
PID=$!
for _ in $(seq 1 50); do      # espera a que el puerto esté de verdad (con carga, 0,8 s no bastaba)
  ss -H -tln 2>/dev/null | grep -q ':2222 ' && break
  sleep 0.1
done
python3 "$SCRIPT" --solo-sockets
RC=$?
kill "$PID" 2>/dev/null
wait "$PID" 2>/dev/null
exit "$RC"
