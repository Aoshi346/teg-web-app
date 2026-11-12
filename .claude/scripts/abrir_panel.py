#!/usr/bin/env python3
"""abrir_panel.py — deja el panel del plan SERVIDO y dice cómo verlo desde fuera.

POR QUÉ EXISTE (PV-5). `templates/report_kit/` ya viaja en el CORE, así que las páginas llegan a
todo proyecto derivado. Pero **el servidor había que arrancarlo a mano y el puerto se elegía a
ojo**, así que en la práctica el panel llegaba y no lo veía nadie.

Es la lección que ya nos costó dos veces —el hook que llegaba sin registrar en `settings.json`, la
variable de entorno que no se propagaba porque `settings.json` no se copia—: **una pieza que llega
y no corre es peor que ausente, porque parece que está.**

SEGURIDAD, y no es negociable. Escucha SOLO en 127.0.0.1 y lo dice en voz alta. `http.server` (y
cualquier servidor con el bind por defecto) escucha en 0.0.0.0, y en una máquina con IP pública eso
publica el directorio en internet sin auth: el 2026-08-21 se encontraron servidores así abiertos
desde julio, sirviendo material de un cliente. Desde fuera se entra por un túnel SSH, nunca
exponiendo el puerto.

  python3 .claude/scripts/abrir_panel.py <plan>            arranca y verifica
  python3 .claude/scripts/abrir_panel.py <plan> --port N   con un puerto concreto
  python3 .claude/scripts/abrir_panel.py --listar          qué paneles hay ya sirviendo
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

RANGO = range(8830, 8900)


def libre(p):
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", p)); return True
        except OSError:
            return False


def responde(p, ruta="/api/health", t=1.5):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{p}{ruta}", timeout=t) as r:
            return r.status == 200
    except Exception:
        return False


def sirviendo():
    """Los paneles que ya están arriba, con el plan que sirve cada uno. Sin esto se acumulan:
    el mismo día se encontraron 12 servidores de informes vivos de sesiones anteriores."""
    out = []
    ps = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout
    for ln in ps.splitlines():
        if "server.py" not in ln or "grep" in ln:
            continue
        pid = ln.split()[0]
        try:
            cwd = os.path.realpath(f"/proc/{pid}/cwd")
        except OSError:
            cwd = "?"
        port = ""
        if "--port" in ln:
            t = ln.split("--port")[1].split()
            port = t[0] if t else ""
        out.append((pid, port or "?", cwd))
    return out


def main():
    argv = sys.argv[1:]
    if "--listar" in argv:
        v = sirviendo()
        print(f"paneles sirviendo: {len(v)}")
        for pid, port, cwd in v:
            print(f"  pid {pid:<9} puerto {port:<6} {cwd}")
        print("\nSe cierran con: kill <pid>. Un panel por informe, y se cierra al terminar:")
        print("estos sobreviven a la sesión que los lanzó y se acumulan.")
        return 0

    if not argv:
        sys.exit(__doc__)
    plan = os.path.abspath(argv[0])
    if not os.path.isdir(plan):
        sys.exit(f"ERROR: no existe {plan}")
    if not os.path.exists(os.path.join(plan, "server.py")):
        sys.exit(f"ERROR: {plan} no tiene server.py — constrúyelo antes:\n"
                 f"  python3 .claude/templates/report_kit/build.py {plan}")

    # ¿ya lo está sirviendo alguien? No se arranca un segundo: se dice cuál es.
    for pid, port, cwd in sirviendo():
        if cwd == plan and port.isdigit() and responde(int(port)):
            print(f"Ya estaba sirviéndose en el puerto {port} (pid {pid}).")
            puerto = int(port); break
    else:
        puerto = None
        if "--port" in argv:
            puerto = int(argv[argv.index("--port") + 1])
            if not libre(puerto):
                sys.exit(f"ERROR: el puerto {puerto} está ocupado")
        else:
            puerto = next((p for p in RANGO if libre(p)), None)
            if puerto is None:
                sys.exit(f"ERROR: ningún puerto libre en {RANGO.start}-{RANGO.stop-1}. "
                         f"Cierra alguno: python3 abrir_panel.py --listar")
        subprocess.Popen([sys.executable, "server.py", "--port", str(puerto)],
                         cwd=plan, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        for _ in range(20):
            time.sleep(0.25)
            if responde(puerto):
                break
        else:
            sys.exit(f"ERROR: arrancó pero no responde en {puerto}. Mira el log del plan.")

    # verificar que las páginas están de verdad, no solo el health
    faltan = [p for p in ("index.html", "dashboard.html")
              if not responde(puerto, "/" + p)]
    print(f"\n✅ Panel de {os.path.basename(plan)} sirviendo en 127.0.0.1:{puerto}")
    if faltan:
        print(f"   ⚠ pero no responden: {', '.join(faltan)} — reconstruye el informe")
    print(f"""
   Desde ESTA máquina:   http://127.0.0.1:{puerto}/dashboard.html
   Desde la tuya:        ssh -N -L {puerto}:127.0.0.1:{puerto} <usuario>@<servidor>
                         y abre http://127.0.0.1:{puerto}/dashboard.html

   Escucha SOLO en 127.0.0.1, a propósito. Para verlo desde fuera se usa el túnel de
   arriba — NUNCA se expone el puerto: el informe puede llevar material de cliente.

   Al terminar:  python3 .claude/scripts/abrir_panel.py --listar   (y kill <pid>)""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
