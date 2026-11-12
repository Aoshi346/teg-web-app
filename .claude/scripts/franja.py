#!/usr/bin/env python3
"""franja.py — los datos y los puertos PROPIOS de cada checkout (worktree o principal) de un repo.

    python3 .claude/scripts/franja.py                 # escribe .env.franja de ESTE checkout
    python3 .claude/scripts/franja.py --comprobar     # choques, puertos, local = producción (1/2)
    python3 .claude/scripts/franja.py --listar        # las franjas y los reclamos del repo
    python3 .claude/scripts/franja.py crear-bd        # crea la BD de la franja si falta
    python3 .claude/scripts/franja.py clonar-bd --desde <bd>   # pg_dump | psql, ON_ERROR_STOP=1
    python3 .claude/scripts/franja.py reclamar "<recurso>" --motivo "<para qué>" [--horas 4]
    python3 .claude/scripts/franja.py soltar "<recurso>"
    python3 .claude/scripts/franja.py liberar [--podar]   # suelta la de aquí (o las huérfanas)

## Por qué (MO-39, sub-ola 2.20)

Un worktree separa los ficheros y **por eso engaña**: los dos frentes escriben en la misma base de
datos, la misma caché de Redis y el mismo broker, y el segundo servidor no arranca porque el
puerto ya está cogido (Postgres lleno tres veces, el broker de Celery en otra instancia, un usuario
de QA reseteado por otro frente en elvion, un `manage.py` local que escribía en producción en
autoparte). evolution lo resolvió con su `scripts/franja.py`; este es el mismo método sin nada de
un proyecto: lo que cambia por proyecto va en `.claude/franjas.json`.

## Cómo reparte

- **El registro** vive en el directorio común de git (`git rev-parse --git-common-dir`, fichero
  `tl-franjas.json`): lo ven todos los worktrees y sesiones del repo, y no se versiona. El
  checkout principal es la franja 0; cada worktree coge la primera libre y la conserva.
- **Franja n**: base de datos `<bd>` (n = 0) o `<bd>_<nombre del worktree>`; índices de Redis
  `n·k … n·k+k-1`; vhost del broker `/` o `<proyecto>_<nombre>`; cada puerto, `base + n·paso`.
- **Las variables** las define el proyecto con plantillas (`{bd}`, `{redis0}`, `{vhost}`,
  `{puerto:8031}`, `{n}`, `{nombre}`, `{compose}`); `${VAR}` se toma del entorno al escribir. Si
  es una credencial queda en `.env.franja`, que nace 600 y que git tiene que ignorar: si no lo
  ignora, el script lo añade a `info/exclude` del repo (y si ya está en el índice, se para).
- **Reclamos de datos** (`reclamar`): un usuario de servicio, un tenant de pruebas, una tabla que
  se recarga… Quedan en el mismo registro; reclamar lo que otro frente tiene sale con 1. Es el
  «file claim» de lo que no es un fichero (`rules/parallelization.md` §file claims).
- **Local = producción**: si el `.env` del checkout o la franja apuntan a algo de `produccion`
  (nombre de BD, host o puerto), `--comprobar` sale con 2.

`.claude/franjas.json` (ejemplo mínimo):

    {"proyecto": "miapp", "env": ".env.franja", "paso_puertos": 10,
     "postgres": {"host": "127.0.0.1", "puerto": 5460, "usuario": "miapp", "bd": "miapp",
                  "contenedor": "miapp_postgres"},
     "redis": {"indices_por_franja": 3}, "broker": {"tipo": "rabbitmq"},
     "produccion": {"bd": ["miapp_prod"], "hosts": ["db.miapp.es"], "puertos": [5432],
                    "contenedores": ["miapp_prod_postgres"]},
     "variables": {
       "DATABASE_URL": "postgres://miapp:${POSTGRES_PASSWORD}@127.0.0.1:5460/{bd}",
       "REDIS_URL": "redis://127.0.0.1:6384/{redis0}",
       "CELERY_BROKER_URL": "amqp://miapp:${RABBITMQ_PASSWORD}@127.0.0.1:5681/{vhost}",
       "RUNSERVER_PORT": "{puerto:8031}", "CONN_MAX_AGE": "0"}}

Salida: 0 bien · 1 choque, puerto ocupado, reclamo de otro o fallo de BD · 2 local = producción
o falta la configuración.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

REGISTRO = "tl-franjas.json"


def git(*args: str, cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                       env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    if r.returncode != 0:
        sys.exit(f"✗ git {' '.join(args)}: {r.stderr.strip()} (¿es un repo git?)")
    return r.stdout.strip()


def checkout(cwd: Path) -> tuple[Path, Path, bool]:
    """(raíz de este checkout, directorio común de git, ¿es el principal?)."""
    raiz = Path(git("rev-parse", "--show-toplevel", cwd=cwd)).resolve()
    comun = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=cwd)).resolve()
    return raiz, comun, comun == (raiz / ".git").resolve()


def config(raiz: Path) -> dict:
    f = raiz / ".claude" / "franjas.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"✗ falta o no se lee {f} ({e}): sin él no sé qué aislar", file=sys.stderr)
        sys.exit(2)


@contextmanager
def registro(comun: Path):
    """El registro compartido, con cerrojo (dos worktrees no cogen la misma franja a la vez) y
    escritura atómica. Si está roto, se para: vaciarlo en silencio repartía la misma franja dos
    veces (verificador 2.20, #14)."""
    ruta = comun / REGISTRO
    with open(comun / (REGISTRO + ".lock"), "a+", encoding="utf-8") as cerrojo:
        fcntl.flock(cerrojo, fcntl.LOCK_EX)
        texto = ruta.read_text(encoding="utf-8") if ruta.exists() else ""
        try:
            datos = json.loads(texto) if texto.strip() else {}
            if not isinstance(datos, dict):
                raise ValueError("no es un objeto")
        except ValueError as e:
            print(f"✗ el registro {ruta} está roto ({e}): es JSON, arréglalo a mano o bórralo y "
                  "vuelve a correr franja.py en CADA checkout (cada uno recupera la franja que "
                  "dice su .env.franja); no lo vacío yo porque se repartiría la misma franja dos "
                  "veces", file=sys.stderr)
            sys.exit(1)
        datos.setdefault("franjas", {})
        datos.setdefault("reclamos", [])
        yield datos
        tmp = ruta.with_name(REGISTRO + ".tmp")
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        os.replace(tmp, ruta)


def nombre_de(raiz: Path, principal: bool) -> str:
    return "principal" if principal else re.sub(r"[^a-z0-9_]", "_", raiz.name.lower())[:40]


def franja_en_disco(raiz: Path, cfg: dict) -> tuple[int, str] | None:
    """El `FRANJA_N` y el `FRANJA` (el nombre, que es lo que da la BD) que dice el `.env.franja`
    de este checkout: lo que usa la aplicación."""
    try:
        texto = (raiz / cfg.get("env", ".env.franja")).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
    n = re.search(r"^FRANJA_N=(\d+)\s*$", texto, re.M)
    nombre = re.search(r"^FRANJA=([a-z0-9_]+)\s*$", texto, re.M)
    return (int(n.group(1)), nombre.group(1)) if n and nombre else None


def asignar(datos: dict, raiz: Path, principal: bool,
            preferida: tuple[int, str] | None = None) -> dict:
    """La franja de este checkout: la del registro; si no está, la de su `.env.franja` si sigue
    libre (un registro borrado y recreado no reparte las franjas en otro orden); si no, la primera
    libre."""
    clave = str(raiz)
    if clave in datos["franjas"]:
        return datos["franjas"][clave]
    usados = {f["n"] for f in datos["franjas"].values()}
    nombres = {f["nombre"] for f in datos["franjas"].values()}
    if (not principal and preferida and preferida[0] not in usados
            and preferida[1] not in nombres):  # recupera número Y nombre (el nombre da la BD)
        datos["franjas"][clave] = {"n": preferida[0], "nombre": preferida[1],
                                   "desde": time.strftime("%Y-%m-%d %H:%M")}
        return datos["franjas"][clave]
    n = 0 if principal else next(i for i in range(1, 1000) if i not in usados)
    nombre = nombre_de(raiz, principal)
    if nombre in nombres:
        nombre = f"{nombre}_{n}"  # mismo nombre de carpeta en otro sitio: que no compartan BD
    datos["franjas"][clave] = {"n": n, "nombre": nombre, "desde": time.strftime("%Y-%m-%d %H:%M")}
    return datos["franjas"][clave]


def recursos(cfg: dict, f: dict) -> dict:
    """Lo que ocupa la franja: BD, índices de Redis, vhost, puertos y COMPOSE_PROJECT_NAME."""
    n, nombre, proy = f["n"], f["nombre"], cfg.get("proyecto", "app")
    bd_base = (cfg.get("postgres") or {}).get("bd", proy)
    k = int((cfg.get("redis") or {}).get("indices_por_franja", 0))
    res = {"bd": bd_base if n == 0 else f"{bd_base}_{nombre}"[:63],
           "redis": list(range(n * k, n * k + k)),
           "vhost": "/" if n == 0 else f"{proy}_{nombre}",
           "compose": proy if n == 0 else f"{proy}_{nombre}",
           "puertos": {}}
    paso = int(cfg.get("paso_puertos", 10))
    for plantilla in (cfg.get("variables") or {}).values():
        for base in re.findall(r"\{puerto:(\d+)\}", str(plantilla)):
            res["puertos"][base] = int(base) + n * paso
    return res


def valores(cfg: dict, f: dict, res: dict) -> tuple[dict, list[str]]:
    faltan: list[str] = []
    tabla = {"bd": res["bd"], "vhost": res["vhost"], "compose": res["compose"], "n": str(f["n"]),
             "nombre": f["nombre"]}
    tabla.update({f"redis{i}": str(x) for i, x in enumerate(res["redis"])})

    def sustituye(m: re.Match) -> str:
        if m.group(1):
            return str(res["puertos"][m.group(1)])
        return tabla.get(m.group(2), m.group(0))

    def entorno(m: re.Match) -> str:
        if m.group(1) in os.environ:
            return os.environ[m.group(1)]
        faltan.append(m.group(1))
        return m.group(0)

    out = {"FRANJA": f["nombre"], "FRANJA_N": str(f["n"])}
    for clave, plantilla in (cfg.get("variables") or {}).items():
        v = re.sub(r"\{puerto:(\d+)\}|\{([a-z0-9]+)\}", sustituye, str(plantilla))
        out[clave] = re.sub(r"\$\{([A-Z_][A-Z0-9_]*)\}", entorno, v)
    if cfg.get("compose"):
        out["COMPOSE_PROJECT_NAME"] = res["compose"]
    return out, sorted(set(faltan))


def puerto_libre(p: int) -> bool:
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", p))
        return True
    except OSError:
        return False
    finally:
        s.close()


def leer_env(fichero: Path, claves: set[str]) -> dict:
    """Solo las claves que el proyecto declara en `variables`; nada más del `.env` (secretos)."""
    out = {}
    try:
        for linea in fichero.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", linea)
            if m and m.group(1) in claves:
                out[m.group(1)] = m.group(2).strip("'\"")
    except OSError:
        pass
    return out


def produccion(cfg: dict, textos: dict[str, str]) -> list[str]:
    """Qué valor apunta a producción. `textos`: origen → valor (las contraseñas no se enseñan)."""
    p = cfg.get("produccion") or {}
    malos = []
    for origen, v in textos.items():
        oculto = re.sub(r"://([^:/@]+):[^@]*@", r"://\1:***@", v)
        for bd in p.get("bd", []):
            if re.search(rf"(^|/){re.escape(bd)}(\?|$)", v) or v == bd:
                malos.append(f"{origen} = {oculto} → la BD «{bd}» es de producción")
        for h in p.get("hosts", []):
            if re.search(rf"[@/]{re.escape(h)}[:/]", v) or v == h:
                malos.append(f"{origen} = {oculto} → el host «{h}» es de producción")
        for pu in p.get("puertos", []):
            if re.search(rf":{pu}(/|$)", v):
                malos.append(f"{origen} = {oculto} → el puerto {pu} es el de producción")
    return malos


def comprobar(raiz: Path, comun: Path, principal: bool, cfg: dict) -> int:
    peor = 0
    with registro(comun) as datos:
        f = asignar(datos, raiz, principal, franja_en_disco(raiz, cfg))
        todas = {k: recursos(cfg, v) | {"nombre": v["nombre"]} for k, v in datos["franjas"].items()}
        ahora = time.strftime("%Y-%m-%d %H:%M")
        reclamos = [r for r in datos["reclamos"] if r.get("hasta", "9") > ahora]
    mia = todas[str(raiz)]
    en_disco = franja_en_disco(raiz, cfg)
    if en_disco is not None and en_disco != (f["n"], f["nombre"]):
        print(f"✗ el {cfg.get('env', '.env.franja')} de aquí es de la franja {en_disco[0]} "
              f"«{en_disco[1]}» y el registro dice {f['n']} «{f['nombre']}»: la aplicación usa los "
              "datos de otra franja. Vuelve a correr franja.py")
        peor = max(peor, 1)
    print(f"franja {f['n']} «{f['nombre']}» · BD {mia['bd']} · redis {mia['redis']} · "
          f"vhost {mia['vhost']} · puertos {sorted(mia['puertos'].values())}")
    for k, otra in todas.items():
        if k == str(raiz):
            continue
        choques = []
        if otra["bd"] == mia["bd"]:
            choques.append(f"BD {mia['bd']}")
        if set(otra["redis"]) & set(mia["redis"]):
            choques.append(f"redis {sorted(set(otra['redis']) & set(mia['redis']))}")
        if otra["vhost"] == mia["vhost"] and cfg.get("broker"):
            choques.append(f"vhost {mia['vhost']}")
        comunes = set(otra["puertos"].values()) & set(mia["puertos"].values())
        if comunes:
            choques.append(f"puertos {sorted(comunes)}")
        if choques:
            print(f"✗ CHOCA con «{otra['nombre']}» ({k}): {', '.join(choques)}")
            peor = max(peor, 1)
        if not Path(k).exists():
            print(f"⚠ la franja «{otra['nombre']}» es de un checkout que ya no existe ({k}): "
                  "`liberar --podar`")
    if max(mia["redis"], default=0) > 15:
        print(f"✗ los índices de Redis {mia['redis']} pasan de 15 (Redis trae 16): menos índices "
              "por franja")
        peor = max(peor, 1)
    for base, p in sorted(mia["puertos"].items()):
        if not puerto_libre(p):  # se mira ANTES de levantar (con el propio ya arriba, también sale)
            print(f"✗ el puerto {p} (base {base}) ya está escuchando: este frente no arrancaría "
                  "ahí (si es tu propio servidor, ya está levantado; si no, cambia base o paso)")
            peor = max(peor, 1)
    vals, _ = valores(cfg, f, mia)
    claves = set((cfg.get("variables") or {}).keys())
    env_proyecto = leer_env(raiz / ".env", claves)
    malos = produccion(cfg, {f".env.franja:{k}": v for k, v in vals.items()}
                       | {f"entorno:{k}": os.environ[k] for k in claves if k in os.environ})
    # Un valor de producción en el `.env` que la franja TAPA (misma clave, valor limpio) es un
    # aviso; uno que la franja no tapa es local = producción: cualquier `manage.py` lo usaría.
    tapados = {k for k in env_proyecto if k in vals and not produccion(cfg, {k: vals[k]})}
    for k, v in env_proyecto.items():
        for m in produccion(cfg, {f".env:{k}": v}):
            if k in tapados:
                print(f"⚠ {m} — lo tapa .env.franja: que se cargue SIEMPRE después de .env")
            else:
                malos.append(m)
    for m in malos:
        print(f"✗ LOCAL = PRODUCCIÓN: {m}")
    if malos:
        print("  Un comando local escribiría en producción. Quita ese valor del .env de desarrollo "
              "o declara la variable en franjas.json para que .env.franja la tape.")
        peor = 2
    for r in reclamos:
        dueno = "tú" if r["franja"] == f["nombre"] else f"«{r['franja']}»"
        print(f"· reclamo de {dueno}: {r['recurso']} — {r['motivo']} (hasta {r['hasta']})")
    if peor == 0:
        print("✓ sin choques")
    return peor


def fuera_de_git(raiz: Path, comun: Path, destino: Path) -> bool:
    """`.env.franja` puede llevar una contraseña (`${POSTGRES_PASSWORD}` sustituida): no puede
    acabar en un commit. Si git no lo ignora, se añade a `info/exclude` del repo (local, vale para
    todos los worktrees, no se versiona) y se vuelve a mirar; si ya está en el índice, se para."""
    rel = str(destino.relative_to(raiz))
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    if subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel], cwd=raiz, env=env,
                      capture_output=True).returncode == 0:
        print(f"✗ {rel} ya está en el índice de git: sácalo (`git rm --cached {rel}`) antes de "
              "escribirlo, que lleva credenciales", file=sys.stderr)
        return False

    def ignorado() -> bool:
        return subprocess.run(["git", "check-ignore", "-q", "--", rel], cwd=raiz,
                              env=env).returncode == 0

    if ignorado():
        return True
    excluir = comun / "info" / "exclude"
    excluir.parent.mkdir(parents=True, exist_ok=True)
    with open(excluir, "a", encoding="utf-8") as fh:
        fh.write(f"\n# franja.py: el .env de cada franja no va a git (puede llevar credenciales)\n"
                 f"{destino.name}\n")
    if ignorado():
        print(f"· {rel} no lo ignoraba git: añadido a {excluir} (local, no se versiona)")
        return True
    print(f"✗ {rel} sigue sin estar ignorado por git: no lo escribo", file=sys.stderr)
    return False


def escribir(raiz: Path, comun: Path, principal: bool, cfg: dict) -> int:
    with registro(comun) as datos:
        f = asignar(datos, raiz, principal, franja_en_disco(raiz, cfg))
    res = recursos(cfg, f)
    vals, faltan = valores(cfg, f, res)
    destino = raiz / cfg.get("env", ".env.franja")
    if not fuera_de_git(raiz, comun, destino):
        return 1
    cab = [f"# {destino.name} — franja {f['n']} «{f['nombre']}». GENERADO por "
           ".claude/scripts/franja.py:", "# no se edita a mano ni va a git. Se carga DESPUÉS de "
           ".env y le gana."]
    tmp = destino.with_name(destino.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)  # 600 desde que nace
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(cab + [f"{k}={v}" for k, v in vals.items()]) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, destino)
    print(f"✓ {destino.name}: franja {f['n']} «{f['nombre']}» · BD {res['bd']} · "
          f"puertos {sorted(res['puertos'].values())} · redis {res['redis']}")
    for v in faltan:
        print(f"⚠ ${{{v}}} no está en el entorno: queda sin sustituir en {destino.name}")
    return 0


def psql(cfg: dict, *args: str, entrada: subprocess.Popen | None = None) -> list[str]:
    pg = cfg.get("postgres") or {}
    base = ["-U", pg.get("usuario", "postgres")]
    if pg.get("contenedor"):
        return ["docker", "exec", "-i", pg["contenedor"], *args[:1], *base, *args[1:]]
    return [*args[:1], "-h", pg.get("host", "127.0.0.1"), "-p", str(pg.get("puerto", 5432)), *base,
            *args[1:]]


def correr(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    """subprocess.run que, si no existe `psql`/`docker`, lo dice en vez de soltar una traza."""
    try:
        return subprocess.run(cmd, **kw)
    except FileNotFoundError:
        print(f"✗ no encuentro `{cmd[0]}`: instala el cliente de Postgres o declara "
              "`postgres.contenedor` en franjas.json", file=sys.stderr)
        sys.exit(1)


def existe_bd(cfg: dict, bd: str) -> bool:
    # El nombre va como variable de psql (:'nombre'), no pegado en el SQL.
    r = correr(psql(cfg, "psql", "-d", "postgres", "-tA", "-v", f"nombre={bd}"),
               input="SELECT 1 FROM pg_database WHERE datname = :'nombre';\n",
               capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"✗ no puedo hablar con Postgres: {r.stderr.strip()}")
    return r.stdout.strip() == "1"


def mi_bd(raiz: Path, comun: Path, principal: bool, cfg: dict) -> str:
    with registro(comun) as datos:
        f = asignar(datos, raiz, principal, franja_en_disco(raiz, cfg))
    bd = recursos(cfg, f)["bd"]
    if not re.fullmatch(r"[A-Za-z0-9_]{1,63}", bd):
        print(f"✗ nombre de BD raro ({bd!r}): solo letras, números y _", file=sys.stderr)
        sys.exit(2)
    pg = cfg.get("postgres") or {}
    # El SERVIDOR también: con `postgres.host` de producción, crear o clonar escribiría allí. Con
    # `contenedor`, se habla por `docker exec` y lo que cuenta es el contenedor, no host y puerto.
    malos = produccion(cfg, {"bd de la franja": bd})
    if pg.get("contenedor"):
        # Hablando por `docker exec`, host y puerto no dicen nada: hay que declarar qué contenedores
        # son de producción (aquí la producción corre en contenedores locales). Sin la lista, no.
        prod = (cfg.get("produccion") or {}).get("contenedores")
        if prod is None:
            malos.append("con `postgres.contenedor` hay que declarar `produccion.contenedores` (la "
                         "lista de contenedores de producción; [] si no hay)")
        elif pg["contenedor"] in prod:
            malos.append(f"el contenedor «{pg['contenedor']}» es de producción")
    else:
        servidor = f"postgres://{pg.get('host', '127.0.0.1')}:{pg.get('puerto', 5432)}/{bd}"
        malos += produccion(cfg, {"servidor de la franja": servidor})
    if malos:
        print(f"✗ LOCAL = PRODUCCIÓN, no toco la BD: {'; '.join(malos)}", file=sys.stderr)
        sys.exit(2)
    return bd


def crear_bd(raiz: Path, comun: Path, principal: bool, cfg: dict) -> int:
    bd = mi_bd(raiz, comun, principal, cfg)
    if existe_bd(cfg, bd):
        print(f"· la BD {bd} ya existía")
        return 0
    r = correr(psql(cfg, "createdb", bd), capture_output=True, text=True)
    print(f"✓ creada la BD {bd}" if r.returncode == 0 else f"✗ createdb {bd}: {r.stderr.strip()}")
    return 0 if r.returncode == 0 else 1


def clonar_bd(raiz: Path, comun: Path, principal: bool, cfg: dict, desde: str,
              reemplazar: bool) -> int:
    """pg_dump de `desde` → psql en la BD de la franja, con ON_ERROR_STOP=1: un error para.

    (El `db-clone.sh` de EvoPreven/develop usa ON_ERROR_STOP=0: un CREATE que falla se traga y el
    clon
    sale «Listo» a medias — MO-39.) Si falla, se borra la BD a medio hacer."""
    bd = mi_bd(raiz, comun, principal, cfg)
    if principal and not reemplazar:
        print("✗ esta es la franja 0 (el checkout principal): clonar encima pide --reemplazar",
              file=sys.stderr)
        return 1
    if bd == desde:
        print(f"✗ origen y destino son la misma BD ({bd})", file=sys.stderr)
        return 1
    if existe_bd(cfg, bd):
        if not reemplazar:
            print(f"✗ la BD {bd} ya existe: --reemplazar para tirarla y clonar de nuevo",
                  file=sys.stderr)
            return 1
        r = correr(psql(cfg, "dropdb", "--if-exists", bd), capture_output=True, text=True)
        if r.returncode != 0:  # p. ej. la BD está en uso: se dice, sin traza
            print(f"✗ dropdb {bd}: {r.stderr.strip()}", file=sys.stderr)
            return 1
    r = correr(psql(cfg, "createdb", bd), capture_output=True, text=True)
    if r.returncode != 0:
        print(f"✗ createdb {bd}: {r.stderr.strip()}", file=sys.stderr)
        return 1
    volcado = subprocess.Popen(psql(cfg, "pg_dump", "--no-owner", "--no-privileges", desde),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    carga = subprocess.run(psql(cfg, "psql", "-q", "-v", "ON_ERROR_STOP=1", "-d", bd),
                           stdin=volcado.stdout, capture_output=True, text=True)
    volcado.stdout.close()
    err_dump = volcado.stderr.read().decode(errors="replace").strip()
    volcado.wait()
    if volcado.returncode != 0 or carga.returncode != 0:
        subprocess.run(psql(cfg, "dropdb", "--if-exists", bd), capture_output=True)
        print(f"✗ clon fallido (pg_dump exit {volcado.returncode}, psql exit {carga.returncode}); "
              f"la BD {bd} a medias se ha borrado.\n  {(err_dump or carga.stderr.strip())[:400]}",
              file=sys.stderr)
        return 1
    print(f"✓ {desde} → {bd} clonada (ON_ERROR_STOP=1: ningún error tragado)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("accion", nargs="?", default="escribir",
                    choices=["escribir", "crear-bd", "clonar-bd", "reclamar", "soltar", "liberar"])
    ap.add_argument("recurso", nargs="?")
    ap.add_argument("--comprobar", action="store_true")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--desde")
    ap.add_argument("--reemplazar", action="store_true")
    ap.add_argument("--motivo", default="")
    ap.add_argument("--horas", type=float, default=4)
    ap.add_argument("--podar", action="store_true")
    ap.add_argument("-C", dest="cwd", default=".", help="trabajar como si estuviera en esta ruta")
    a = ap.parse_args()
    raiz, comun, principal = checkout(Path(a.cwd))
    if a.listar:
        with registro(comun) as datos:
            pass
        cfg = config(raiz)
        for k, f in sorted(datos["franjas"].items(), key=lambda x: x[1]["n"]):
            r = recursos(cfg, f)
            vivo = "" if Path(k).exists() else "  (HUÉRFANA: el checkout ya no existe)"
            print(f"{f['n']:>3} {f['nombre']:<24} BD {r['bd']:<28} redis {r['redis']} "
                  f"vhost {r['vhost']} puertos {sorted(r['puertos'].values())}{vivo}")
        for r in datos["reclamos"]:
            print(f"    reclamo: {r['recurso']} · {r['franja']} · {r['motivo']} · "
                  f"hasta {r['hasta']}")
        return 0
    cfg = config(raiz)
    if a.comprobar:
        return comprobar(raiz, comun, principal, cfg)
    if a.accion == "escribir":
        return escribir(raiz, comun, principal, cfg)
    if a.accion == "crear-bd":
        return crear_bd(raiz, comun, principal, cfg)
    if a.accion == "clonar-bd":
        if not a.desde:
            print("✗ clonar-bd necesita --desde <bd>", file=sys.stderr)
            return 2
        return clonar_bd(raiz, comun, principal, cfg, a.desde, a.reemplazar)
    with registro(comun) as datos:
        f = asignar(datos, raiz, principal, franja_en_disco(raiz, cfg))
        ahora = time.strftime("%Y-%m-%d %H:%M")
        datos["reclamos"] = [r for r in datos["reclamos"] if r.get("hasta", "9") > ahora]
        if a.accion == "liberar":
            if a.podar:
                fuera = [k for k in datos["franjas"] if not Path(k).exists()]
            else:
                fuera = [str(raiz)]
            for k in fuera:
                nombre = datos["franjas"].pop(k, {}).get("nombre")
                datos["reclamos"] = [r for r in datos["reclamos"] if r["franja"] != nombre]
                print(f"✓ liberada la franja de {k}")
            return 0
        if not a.recurso:
            print(f"✗ {a.accion} necesita el recurso (p. ej. \"usuario qa_ui\")", file=sys.stderr)
            return 2
        otro = next((r for r in datos["reclamos"]
                     if r["recurso"] == a.recurso and r["franja"] != f["nombre"]), None)
        if a.accion == "reclamar":
            if otro:
                print(f"✗ «{a.recurso}» lo tiene «{otro['franja']}» ({otro['motivo']}, hasta "
                      f"{otro['hasta']}): habla con ese frente antes de tocarlo", file=sys.stderr)
                return 1
            hasta = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + a.horas * 3600))
            datos["reclamos"] = [r for r in datos["reclamos"] if r["recurso"] != a.recurso]
            datos["reclamos"].append({"recurso": a.recurso, "franja": f["nombre"],
                                      "motivo": a.motivo, "desde": ahora, "hasta": hasta})
            print(f"✓ reclamado «{a.recurso}» por «{f['nombre']}» hasta {hasta}")
            return 0
        antes = len(datos["reclamos"])
        datos["reclamos"] = [r for r in datos["reclamos"]
                             if not (r["recurso"] == a.recurso and r["franja"] == f["nombre"])]
        soltado = len(datos["reclamos"]) < antes
        print(f"✓ soltado «{a.recurso}»" if soltado else f"· «{a.recurso}» no era tuyo")
        return 0


if __name__ == "__main__":
    sys.exit(main())
