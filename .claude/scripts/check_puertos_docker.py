#!/usr/bin/env python3
"""¿Este docker-compose publica algo a internet sin querer?

Nace de un incidente real (2026-08-27): un `docker-compose` publicó phpMyAdmin y
quedó alcanzable desde fuera. La creencia de que «el servidor tiene firewall, así
que estamos a salvo» es FALSA, y lo dice la documentación de Docker con todas las
letras:

    «Docker and ufw use firewall rules in ways that make them incompatible with
    each other. When you publish a container's ports using Docker, traffic to and
    from that container gets diverted before it goes through the ufw firewall
    settings. Docker routes container traffic in the `nat` table, which means that
    packets are diverted before it reaches the INPUT and OUTPUT chains that ufw
    uses. Packets are routed before the firewall rules can be applied, effectively
    ignoring your firewall configuration.»
    — docs.docker.com/engine/network/packet-filtering-firewalls/

    «Publishing container ports is insecure by default.»
    — docs.docker.com/engine/network/port-publishing/

    OWASP Docker Security Cheat Sheet, RULE #5a: «Docker manages its own iptables
    and nftables rules directly and bypasses UFW entirely.»

Por eso la defensa NO puede estar en el firewall: tiene que estar aquí, en el
fichero, antes de desplegar.

LAS DOS DECISIONES DE DISEÑO, que son lo que hace que esto sirva:

1. **Se lee `docker compose config`, NUNCA el YAML a pelo.** `config` normaliza las
   dos sintaxis (corta y larga) e **interpola las variables**, que es donde el grep
   falla. Medido: con `ports: ["${BIND}:${PORT}:80"]` y `BIND=0.0.0.0` en el `.env`,
   `grep 0.0.0.0 docker-compose.yml` da CERO coincidencias y el puerto está abierto
   a internet.

2. **`host_ip` ausente significa `0.0.0.0`**, o sea todas las interfaces. Literal de
   docs.docker.com/reference/compose-file/services/#ports: «If you do not specify a
   host IP (such as 127.0.0.1), Docker binds to all interfaces (0.0.0.0)». Buscar la
   cadena «0.0.0.0» es exactamente lo que NO hay que hacer: el caso peligroso es el
   que no la lleva escrita.

Y la tercera, que es la que evita que el aviso se ignore: **un servidor web publica
80 y 443 a propósito**. Marcarlos sería chillar en cada proyecto, y un comprobador
que chilla siempre se aprende a saltar (`rules/agent-security.md` ASI09). Se
permiten por defecto; todo lo demás se declara con su razón o sale como hallazgo.

4. **El socket abierto es la verdad; el compose, solo la intención** (SE-22, 2026-10-22). Un
   contenedor con `network_mode: host` no pasa por `ports:`: se salta la regla «publicar en
   127.0.0.1» y abre lo que su proceso quiera en el host. Medido: un mock SFTP
   (`mollet-sftp-box`) escuchaba en 0.0.0.0:2222 con IP pública y ni este script ni Hugo lo
   habrían visto, porque solo leían lo que el compose publica. Ahora (a) un servicio con
   `network_mode: host` es hallazgo por sí mismo y (b) `--sockets` cruza con `ss -tlnp` real:
   cualquier socket en `0.0.0.0`, `*` o `[::]` que no sea 22/80/443 ni esté declarado sale, con su
   proceso y, si es de un contenedor, con su nombre.

Uso:
    python3 check_puertos_docker.py [ruta-del-proyecto]
    python3 check_puertos_docker.py . --json
    python3 check_puertos_docker.py . --sockets            # + sockets reales de la máquina (ss)
    python3 check_puertos_docker.py --solo-sockets         # sin compose: solo la máquina
    python3 check_puertos_docker.py --sockets --ss-fichero salida_ss.txt   # prueba (fixture)

Salida: 0 todo local o declarado · 1 hay algo expuesto sin declarar · 2 NO SE PUDO
MEDIR (falta docker, o el compose no es válido, o con --sockets falta `ss`). El 2 es deliberado: un comprobador
que no encuentra qué medir tiene que decirlo, no imprimir «(limpio)».
"""
from __future__ import annotations

import ipaddress
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Un servidor web publica esto a propósito. No son hallazgos.
PUERTOS_PUBLICOS_NORMALES = {80, 443}

# Lo que NUNCA debería salir a internet, ni declarado sin pensarlo mucho.
# El nombre es lo que se enseña en el aviso; el objetivo es que se lea el riesgo.
PUERTOS_DE_ALTO_RIESGO = {
    3306: "MySQL/MariaDB", 5432: "PostgreSQL", 27017: "MongoDB",
    6379: "Redis", 11211: "Memcached", 9200: "Elasticsearch",
    5672: "RabbitMQ", 15672: "RabbitMQ (panel)", 2375: "API de Docker SIN TLS",
    2376: "API de Docker", 9000: "phpMyAdmin/Portainer (habitual)",
    8081: "phpMyAdmin (habitual)", 1433: "SQL Server", 5900: "VNC", 22: "SSH",
}

FICHERO_EXCEPCIONES = ".claude/puertos-publicos-declarados.json"


def cargar_excepciones(raiz: Path) -> dict:
    """Excepciones declaradas: {"servicio:puerto": "por qué, y quién lo decidió"}.

    Se exige una razón NO vacía a propósito. Una excepción sin razón es
    indistinguible de un descuido a los dos meses.
    """
    f = raiz / FICHERO_EXCEPCIONES
    if not f.exists():
        return {}
    try:
        datos = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  {FICHERO_EXCEPCIONES} no se pudo leer ({e}). Se ignora: "
              f"ninguna excepción cuenta.", file=sys.stderr)
        return {}
    if not isinstance(datos, dict):
        print(f"⚠️  {FICHERO_EXCEPCIONES} debe ser un objeto {{\"servicio:puerto\": \"razón\"}}. Se ignora.",
              file=sys.stderr)
        return {}
    return {k: v for k, v in datos.items() if isinstance(v, str) and v.strip()}


def config_normalizada(raiz: Path, fichero: Path | None = None) -> dict | None:
    """`docker compose config` es la única lectura fiable. Ver el docstring."""
    try:
        r = subprocess.run(
            ["docker", "compose"] + (["-f", str(fichero)] if fichero else [])
            + ["config", "--format", "json"],
            cwd=raiz, capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError:
        print("NO SE PUDO MEDIR: no hay binario `docker` en esta máquina.\n"
              "  El fichero se lee con `docker compose config` y no con un grep, "
              "porque el grep no ve las variables interpoladas.", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("NO SE PUDO MEDIR: `docker compose config` no respondió en 60s.",
              file=sys.stderr)
        return None
    if r.returncode != 0:
        print(f"NO SE PUDO MEDIR: `docker compose config` falló.\n{r.stderr.strip()}",
              file=sys.stderr)
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        print(f"NO SE PUDO MEDIR: la salida de compose no es JSON válido ({e}).",
              file=sys.stderr)
        return None


def es_local(host_ip: str) -> bool:
    try:
        return ipaddress.ip_address(host_ip).is_loopback
    except ValueError:
        return False


def puerto_de(publicado) -> int | None:
    """`published` puede ser int, str, o un rango '9000-9002'. Del rango se toma
    el primero solo para poder nombrarlo; el veredicto no depende de eso."""
    if publicado is None:
        return None
    s = str(publicado).split("-")[0]
    return int(s) if s.isdigit() else None


def analizar(raiz: Path, fichero: Path | None = None) -> tuple[list[dict], list[dict]]:
    cfg = config_normalizada(raiz, fichero)
    if cfg is None:
        sys.exit(2)

    excepciones = cargar_excepciones(raiz)
    hallazgos, permitidos = [], []

    for servicio, definicion in sorted((cfg.get("services") or {}).items()):
        if str(definicion.get("network_mode", "")).strip() == "host":
            # Red de host: `ports:` ni se aplica ni protege. Lo que abra el proceso queda en el host.
            fila = {
                "servicio": servicio, "host_ip": "host", "publicado": "(red de host)",
                "destino": "—", "protocolo": "tcp",
                "fichero": fichero.name if fichero else "(por defecto)",
                "riesgo": "network_mode: host se salta el prefijo 127.0.0.1 del compose",
            }
            if f"{servicio}:host" in excepciones:
                fila["motivo"] = f"declarado: {excepciones[f'{servicio}:host']}"
                permitidos.append(fila)
            else:
                hallazgos.append(fila)
        for p in definicion.get("ports") or []:
            host_ip = p.get("host_ip") or "0.0.0.0"   # AUSENTE == todas las interfaces
            publicado = p.get("published")
            puerto = puerto_de(publicado)
            fila = {
                "servicio": servicio, "host_ip": host_ip,
                "publicado": str(publicado), "destino": p.get("target"),
                "protocolo": p.get("protocol", "tcp"),
                "fichero": fichero.name if fichero else "(por defecto)",
                "riesgo": PUERTOS_DE_ALTO_RIESGO.get(puerto),
            }
            if es_local(host_ip):
                fila["motivo"] = "solo local"
                permitidos.append(fila)
                continue
            clave = f"{servicio}:{publicado}"
            if clave in excepciones:
                fila["motivo"] = f"declarado: {excepciones[clave]}"
                permitidos.append(fila)
            elif puerto in PUERTOS_PUBLICOS_NORMALES and not fila["riesgo"]:
                fila["motivo"] = "puerto web estándar"
                permitidos.append(fila)
            else:
                hallazgos.append(fila)
    return hallazgos, permitidos


# ── Sockets reales (SE-22) ────────────────────────────────────────────────────────────────────
# Una línea de `ss -H -tlnp`:  LISTEN 0 4096 0.0.0.0:2222 0.0.0.0:* users:(("python3",pid=12,fd=3))
RX_PID = re.compile(r'\("([^"]+)",pid=(\d+)')


def _separa(local: str) -> tuple[str, int | None]:
    """'0.0.0.0:80' -> ('0.0.0.0', 80) · '*:3010' -> ('*', 3010) · '[::]:631' -> ('::', 631)
    · '127.0.0.53%lo:53' -> ('127.0.0.53', 53)."""
    host, _, puerto = local.rpartition(":")
    host = host.strip("[]").split("%")[0]
    return host, (int(puerto) if puerto.isdigit() else None)


def _es_publico(host: str) -> bool:
    """`*` y las direcciones sin especificar (0.0.0.0, ::) escuchan en TODAS las interfaces."""
    if host in ("*", ""):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return True          # no se entiende: mejor avisar que callar
    return not ip.is_loopback


def leer_ss(fichero: Path | None = None) -> str | None:
    """Salida de `ss -H -tlnp`. `fichero` permite probarlo con un fixture (control negativo)."""
    if fichero is not None:
        try:
            return fichero.read_text(encoding="utf-8")
        except OSError as e:
            print(f"NO SE PUDO MEDIR: no se lee {fichero} ({e}).", file=sys.stderr)
            return None
    if shutil.which("ss") is None:
        print("NO SE PUDO MEDIR los sockets: no hay `ss` en esta máquina (paquete iproute2).",
              file=sys.stderr)
        return None
    try:
        r = subprocess.run(["ss", "-H", "-tlnp"], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        print("NO SE PUDO MEDIR los sockets: `ss` no respondió en 30s.", file=sys.stderr)
        return None
    if r.returncode != 0:
        print(f"NO SE PUDO MEDIR los sockets: `ss` falló.\n{r.stderr.strip()}", file=sys.stderr)
        return None
    return r.stdout


def contenedores_en_marcha() -> dict[str, dict]:
    """{id_largo: {"nombre", "red"}} de los contenedores vivos. Vacío si no hay docker o no se puede
    hablar con él: la atribución a un contenedor es un extra, el socket abierto se reporta igual."""
    if shutil.which("docker") is None:
        return {}
    try:
        ids = subprocess.run(["docker", "ps", "-q", "--no-trunc"], capture_output=True, text=True,
                             timeout=20)
        if ids.returncode != 0 or not ids.stdout.split():
            return {}
        r = subprocess.run(["docker", "inspect", "-f",
                            "{{.Id}}|{{.Name}}|{{.HostConfig.NetworkMode}}"] + ids.stdout.split(),
                           capture_output=True, text=True, timeout=30)
    except (subprocess.TimeoutExpired, OSError):
        return {}
    salida = {}
    for linea in r.stdout.splitlines():
        partes = linea.split("|")
        if len(partes) == 3:
            salida[partes[0]] = {"nombre": partes[1].lstrip("/"), "red": partes[2]}
    return salida


def contenedor_de(pid: int, contenedores: dict[str, dict]) -> dict | None:
    """El contenedor al que pertenece un pid, por su cgroup (64 hex del id)."""
    try:
        texto = Path(f"/proc/{pid}/cgroup").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for cid in re.findall(r"[0-9a-f]{64}", texto):
        if cid in contenedores:
            return contenedores[cid]
    return None


def analizar_sockets(texto_ss: str, excepciones: dict, contenedores: dict[str, dict] | None = None
                     ) -> tuple[list[dict], list[dict]]:
    """Cruza los sockets en escucha con la política: lo que escucha fuera de loopback y no es un
    puerto web estándar ni está declarado, es hallazgo, venga del compose o de donde venga."""
    contenedores = contenedores or {}
    hallazgos, permitidos, vistos = [], [], set()
    for linea in texto_ss.splitlines():
        cols = linea.split()
        # LISTEN Recv-Q Send-Q Local Peer [Process]; con -H no hay cabecera
        if len(cols) < 5 or cols[0] != "LISTEN":
            continue
        host, puerto = _separa(cols[3])
        if puerto is None or not _es_publico(host):
            continue
        procs = RX_PID.findall(linea)
        proceso = procs[0][0] if procs else "(proceso no visible: ¿sin root?)"
        pid = int(procs[0][1]) if procs else None
        cont = contenedor_de(pid, contenedores) if pid else None
        # v4 y v6 del mismo puerto y proceso son UN servicio
        clave = (puerto, proceso)
        if clave in vistos:
            continue
        vistos.add(clave)
        fila = {"origen": "socket", "host_ip": host or "*", "publicado": str(puerto),
                "proceso": proceso, "pid": pid,
                "contenedor": cont["nombre"] if cont else None,
                "red_host": bool(cont and cont["red"] == "host"),
                "riesgo": PUERTOS_DE_ALTO_RIESGO.get(puerto)}
        etiqueta = f"socket:{puerto}"
        if etiqueta in excepciones:
            fila["motivo"] = f"declarado: {excepciones[etiqueta]}"
            permitidos.append(fila)
        elif puerto in PUERTOS_PUBLICOS_NORMALES and not fila["riesgo"]:
            fila["motivo"] = "puerto web estándar"
            permitidos.append(fila)
        elif puerto == 22:
            fila["motivo"] = "SSH de administración, lo limita ufw"
            permitidos.append(fila)
        else:
            hallazgos.append(fila)
    return hallazgos, permitidos


def _imprime_sockets(hallazgos: list[dict], permitidos: list[dict]) -> None:
    print("  SOCKETS EN ESCUCHA FUERA DE LOOPBACK (ss -tlnp)")
    print("  " + "─" * 62)
    for f in permitidos:
        print(f"  ✅ {f['host_ip']}:{f['publicado']:<6} {f['proceso']:<16} ({f['motivo']})")
    for f in hallazgos:
        de = ""
        if f["contenedor"]:
            de = f" · contenedor {f['contenedor']}" + (" (red de host)" if f["red_host"] else "")
        riesgo = f"  ⚠️  {f['riesgo']}" if f["riesgo"] else ""
        print(f"  ❌ {f['host_ip']}:{f['publicado']:<6} {f['proceso']:<16}{de}{riesgo}")
    print("  " + "─" * 62)
    if hallazgos:
        print(f"  {len(hallazgos)} socket(s) abierto(s) a todas las interfaces sin declarar.")
        print("  Arreglo: atar el proceso a 127.0.0.1 (su --bind / --host / listen), o en Docker")
        print('  "127.0.0.1:PUERTO:PUERTO"; un contenedor con network_mode: host se ata DENTRO,')
        print("  con la opción del propio servicio (el prefijo del compose no le llega).")
        print(f"  Si alguno DEBE ser público, decláralo en {FICHERO_EXCEPCIONES}:")
        print('      { "socket:%s": "por qué, y quién lo decidió, con fecha" }'
              % hallazgos[0]["publicado"])
    else:
        print("  Ningún socket abierto al exterior sin declarar.")


def _imprime_compose(raiz: Path, hallazgos: list[dict], permitidos: list[dict]) -> None:
    print(f"  PUERTOS PUBLICADOS — {raiz.name}")
    print("  " + "─" * 62)
    for f in permitidos:
        print(f"  ✅ {f['fichero']:<28} {f['servicio']:<18} {f['host_ip']}:{f['publicado']} → "
              f"{f['destino']}  ({f['motivo']})")
    for f in hallazgos:
        etiqueta = f"  ⚠️  {f['riesgo']}" if f["riesgo"] else ""
        print(f"  ❌ {f['fichero']:<28} {f['servicio']:<18} {f['host_ip']}:{f['publicado']} → "
              f"{f['destino']}{etiqueta}")

    if not hallazgos:
        print("  " + "─" * 62)
        print("  Nada publicado al exterior sin declarar.")
        return

    print("  " + "─" * 62)
    print(f"  {len(hallazgos)} puerto(s) al alcance de internet.\n")
    print("  ⚠️  Y NO te protege el firewall del servidor: Docker mete sus reglas")
    print("      en la tabla `nat`, antes de las cadenas donde mira ufw. Está en")
    print("      docs.docker.com/engine/network/packet-filtering-firewalls/")
    print("      «Packets are routed before the firewall rules can be applied,")
    print("       effectively ignoring your firewall configuration.»\n")
    publicados = [f for f in hallazgos if f["host_ip"] != "host"]
    if publicados:
        print("  El arreglo es el prefijo, en el propio compose:")
        for f in publicados[:3]:
            print(f'      {f["servicio"]}:  ports: ["127.0.0.1:{f["publicado"]}:{f["destino"]}"]')
        print("\n  Y para llegar desde fuera, túnel SSH:")
        p0 = publicados[0]["publicado"]
        print(f"      ssh -N -L {p0}:127.0.0.1:{p0} <usuario>@<servidor>\n")
    if len(publicados) < len(hallazgos):
        print("  Un servicio con `network_mode: host` no tiene prefijo que ponerle: se ata dentro,")
        print("  con el --bind/--host del propio servicio, y se comprueba con `--sockets`.\n")
    f0 = hallazgos[0]
    clave = f"{f0['servicio']}:{f0['publicado'] if f0['host_ip'] != 'host' else 'host'}"
    print(f"  Si alguno DEBE ser público, decláralo en {FICHERO_EXCEPCIONES}")
    print('      { "%s": "por qué, y quién lo decidió, con fecha" }' % clave)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    como_json = "--json" in sys.argv
    solo_sockets = "--solo-sockets" in sys.argv
    con_sockets = "--sockets" in sys.argv or solo_sockets
    ss_fichero = None
    if "--ss-fichero" in sys.argv:
        k = sys.argv.index("--ss-fichero")
        if k + 1 >= len(sys.argv):
            print("--ss-fichero necesita una ruta.", file=sys.stderr)
            return 2
        ss_fichero = Path(sys.argv[k + 1])
        args = [a for a in args if a != sys.argv[k + 1]]
    raiz = Path(args[0] if args else ".").resolve()

    hallazgos, permitidos, ficheros = [], [], []
    if not solo_sockets:
        # TODOS los compose de la raíz, no solo el nombre por defecto. Hasta 2026-10-14 solo se
        # miraban docker-compose.yml/compose.yml: un proyecto con docker-compose.dev.yml (EvoPreven
        # tiene cinco) salía «nada que comprobar» con exit 0 — un gate de seguridad que no midió y
        # dijo limpio.
        ficheros = sorted({f for pat in ("docker-compose*.yml", "docker-compose*.yaml", "compose*.yml",
                                         "compose*.yaml") for f in raiz.glob(pat) if f.is_file()})
        if not ficheros and not con_sockets:
            if not como_json:
                print(f"Sin fichero de compose en {raiz} — nada que comprobar.")
            return 0
        for f in ficheros:
            h, pm = analizar(raiz, f)
            hallazgos += h
            permitidos += pm

    h_s, p_s = [], []
    if con_sockets:
        texto = leer_ss(ss_fichero)
        if texto is None:
            return 2
        if texto.strip() and not any(l.split()[:1] == ["LISTEN"] for l in texto.splitlines()):
            print("NO SE PUDO MEDIR: la salida de `ss` no trae ninguna línea LISTEN que se entienda "
                  "(¿formato distinto? se espera `ss -H -tlnp`).", file=sys.stderr)
            return 2
        # Con un fixture no se pregunta a docker: la prueba no depende de lo que corra la máquina.
        conts = contenedores_en_marcha() if ss_fichero is None else {}
        h_s, p_s = analizar_sockets(texto, cargar_excepciones(raiz), conts)

    if como_json:
        print(json.dumps({"expuestos": hallazgos, "permitidos": permitidos,
                          "sockets_expuestos": h_s, "sockets_permitidos": p_s},
                         indent=2, ensure_ascii=False))
        return 1 if (hallazgos or h_s) else 0

    if ficheros:
        _imprime_compose(raiz, hallazgos, permitidos)
    if con_sockets:
        if ficheros:
            print()
        _imprime_sockets(h_s, p_s)
    return 1 if (hallazgos or h_s) else 0


if __name__ == "__main__":
    sys.exit(main())
