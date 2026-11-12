#!/usr/bin/env python3
"""gate_tenant.py — G4: ¿puede la conexión de la app ver o escribir filas de otro tenant?

Es la capa de BASE DE DATOS del aislamiento multi-tenant. Junta dos piezas que en casa ya
existían por separado y nunca en un mismo sitio (r3-ciberseguridad-harness §2.5 y §6, items
SE-21 de la revisión integral):

  · de `elvion-autoparte-demo/tests/seguridad/inventario.py`, la regla que hace que un gate no
    envejezca: **el inventario se DESCUBRE, no se escribe a mano**. Aquí, las tablas que llevan la
    columna del tenant salen del catálogo de Postgres (por la columna, no por un prefijo ni por
    una lista), así que la tabla que alguien añada dentro de tres meses entra sola — también si la
    añade en otro esquema. Lo único que se escribe a mano son las EXCEPCIONES, cada una con su
    razón, y una excepción que ya no corresponde a ninguna tabla es un fallo (no crecen solas).
  · de `cold_calling_coach` (CI, «Crear el rol de aplicación (SIN BYPASSRLS)»), el porqué de la
    mitad que más se olvida: *«con superusuario, las políticas no se aplican y la suite de
    aislamiento pasaría entera sin probar absolutamente nada»*. Y su otra mitad: el DUEÑO de una
    tabla se salta sus propias políticas salvo `FORCE ROW LEVEL SECURITY`.

QUÉ COMPRUEBA (modo `rls`, el de por defecto)

  1. El rol con el que conecta la app NO es superusuario NI tiene BYPASSRLS.
  2. Cada tabla con la columna del tenant tiene RLS ENCENDIDO y FORZADO, y al menos una política
     permisiva de lectura que filtra por esa columna contra el ajuste de la sesión
     (`current_setting('app.tenant_id')`). Una política permisiva que NO filtra (`USING (true)`,
     un WITH CHECK abierto, o una que mira otro ajuste) es un fallo aunque haya otra buena al lado,
     porque las permisivas se suman con OR — salvo que una política RESTRICTIVA que sí filtra lo
     cierre (las restrictivas se suman con AND).
  3. Una vista con la columna del tenant que corre con los permisos de un dueño que se salta RLS
     (sin `security_invoker`) es un fallo: la vista devuelve las filas de todos.
  4. Una tabla con la columna del tenant FUERA del esquema medido es un fallo: o se mide ese
     esquema (`--esquema`) o se declara como excepción `esquema.tabla`.
  5. La SONDA de dos tenants sobre la MISMA conexión de la app (necesita `--dsn-admin`, un rol que
     ve todo, para CONTAR filas por tenant; nunca se lee contenido), en transacciones de solo
     lectura que se deshacen. Sin ámbito → 0 filas. Con el ámbito de A → ninguna fila ajena Y
     todas las de A (el control negativo: un filtro que no devuelve nada aprobaría siempre la
     primera mitad). Lo mismo con B, a continuación, en la misma conexión.
  6. Con `--sonda-escritura`, además, con el ámbito de A y en transacciones que SIEMPRE se
     deshacen: insertar una copia de una fila de A con el tenant de B, mover filas de A a B (UPDATE
     sin WHERE), y un DELETE que no puede tocar más filas que las de A. Es lo único que
     caza un WITH CHECK que nombra la columna y el ajuste sin compararlos (`tenant_id IS NOT NULL
     AND current_setting(…) IS NOT NULL`) o un USING de UPDATE/DELETE que no filtra. Escribe y
     deshace: úsalo en CI o en la base de test, no contra producción. `--exigir-escritura` hace
     que una escritura que la base rechaza por otra razón (un trigger) cuente como NO MEDIDO.

La lectura estática de las políticas (2) es LÉXICA: comprueba que la expresión nombra la columna y
el ajuste, no que los compare bien. Por eso en modo rls sin la sonda el gate sale 2 («no medido»),
no 0, salvo `--solo-estatico` explícito.

Modo `aplicacion` (autoparte: tenant compartido y filtro en el ORM, ADR-0002): aquí no hay RLS que
mirar y el aislamiento lo prueba la suite del ORM (`templates/seguridad-tenant/`). El gate solo
comprueba lo que la base sí puede garantizar: la columna del tenant es NOT NULL y es clave ajena.

QUÉ NO COMPRUEBA, y va dicho para que nadie lo dé por cubierto: que la app abra el ámbito con
`SET LOCAL` y no con `SET` (eso es código de la app: lo prueba la suite del ORM), la caché, las
colas ni los logs (OWASP Multi-Tenant los pide; aquí no llegan), las tablas sin la columna que se
protegen a través de su padre (`EXISTS` sobre el padre, como `enable_sql_indirecto` de CCC: no
entran en el inventario), ni una identidad que no sea la columna del tenant (un rol con
`SET ROLE` sí: ser miembro de un rol que se salta RLS cuenta como BYPASSRLS).

COSTE: la sonda cuenta cada tabla entera (un `GROUP BY` por tabla con el admin y cuatro `count(*)`
con la app). Es para CI o una base de test; contra producción es un barrido completo.

USO

    python3 .claude/scripts/gate_tenant.py --dsn "$APP" --dsn-admin "$ADMIN"     # lo completo
    python3 .claude/scripts/gate_tenant.py ... --exigir-sonda --sonda-escritura --exigir-escritura
                                                                              # en CI
    python3 .claude/scripts/gate_tenant.py --dsn "$APP" --solo-estatico          # sin sonda, dicho
    python3 .claude/scripts/gate_tenant.py --autoprueba --dsn-admin "$DSN_SUPERUSUARIO_DESECHABLE"

Los DSN se pueden pasar por entorno para que la contraseña no quede en la línea de comandos (la ve
cualquier usuario en `/proc/<pid>/cmdline`): `$GATE_TENANT_DSN` (o `$DATABASE_URL`) para la app y
`$GATE_TENANT_DSN_ADMIN` para el admin. `--dsn` es el de la APP, el mismo rol que usa en producción
(o en CI, el rol de aplicación). Si se pasa el del superusuario, el gate lo dice y sale 1.

El manifiesto (`--manifiesto`, por defecto `.claude/gate-tenant.json` si existe) fija el modo, la
columna, el ajuste y las excepciones:

    {"modo": "rls", "columna": "tenant_id", "ajuste": "app.tenant_id", "esquema": "public",
     "excepciones": {"tabla": "por qué esta tabla lleva la columna y no política",
                     "otro_esquema.tabla": "…"},
     "funciones_de_ambito": ["app_tenant_actual"]}

SALIDA: 0 todo medido y bien · 1 hay fuga o falta una defensa · 2 NO SE PUDO MEDIR (sin driver,
sin conexión, error del driver, inventario vacío, modo rls sin sonda, o `--exigir-sonda` sin datos
de dos tenants). El 2 es deliberado (`rules/verification.md` §El instrumento que no puede medir debe
ABORTAR): un inventario de cero tablas no es «limpio», es una columna mal escrita.

`--autoprueba` es el control negativo del propio gate: monta una base de juguete en un Postgres
DESECHABLE (solo 127.0.0.1, `localhost`, `::1` o socket), la mide limpia (tiene que salir 0) y con
cada sabotaje plantado (cada uno tiene que salir con SU hallazgo), y lo borra todo al terminar.

Nunca imprime el contenido de una fila ni la contraseña de un DSN: solo cuántas filas y de qué
tabla. Volcar el dato ajeno en un informe es filtrarlo por segunda vez.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
from dataclasses import asdict, dataclass, field
from urllib.parse import urlsplit, urlunsplit

EXIT_OK, EXIT_FALLO, EXIT_NO_MEDIDO = 0, 1, 2
MANIFIESTO_POR_DEFECTO = os.path.join(".claude", "gate-tenant.json")
RAZON_MINIMA = 15  # caracteres: «legacy» no es una razón
ESQUEMAS_DE_SISTEMA = ("pg_catalog", "information_schema")


class NoMedible(Exception):
    """El gate no puede llegar al sujeto. Sale con 2, nunca con 0."""


# ── conexión ──────────────────────────────────────────────────────────────────────────────


def _driver():
    try:
        import psycopg  # type: ignore

        return psycopg
    except ImportError:
        pass
    try:
        import psycopg2  # type: ignore

        return psycopg2
    except ImportError:
        return None


def _error_del_driver() -> tuple:
    mod = _driver()
    return (mod.Error,) if mod is not None and hasattr(mod, "Error") else ()


def conectar(dsn: str):
    mod = _driver()
    if mod is None:
        raise NoMedible(
            "falta el driver de Postgres: ni psycopg (3) ni psycopg2 están instalados en este "
            "intérprete. Córrelo con el Python del proyecto (`poetry run python …`)."
        )
    try:
        conn = mod.connect(dsn)
    except Exception as e:  # noqa: BLE001 — cualquier fallo de conexión es «no medible»
        raise NoMedible(f"no se pudo conectar a {redactar_dsn(dsn)}: {type(e).__name__}") from e
    conn.autocommit = False
    return conn


def _netloc(usuario: str | None, clave: str | None, host: str | None, puerto) -> str:
    h = host or ""
    if ":" in h:
        h = f"[{h}]"  # IPv6: `::1` sin corchetes no es un host, es un puerto mal escrito
    cred = ""
    if usuario:
        cred = usuario + (f":{clave}" if clave is not None else "") + "@"
    return f"{cred}{h}" + (f":{puerto}" if puerto else "")


def redactar_dsn(dsn: str) -> str:
    """El DSN SIN contraseña, para decir a qué se conectó sin filtrar la credencial.

    En URL se reconstruye con usuario, host, puerto y base, y la query se omite entera: libpq
    admite `?password=…` ahí, y redactar solo el netloc la dejaba pasar. En la forma clave=valor se
    tapa el valor, también entre comillas (`password='a b c'`).
    """
    if "://" in dsn:
        p = urlsplit(dsn)
        netloc = _netloc(p.username, "***" if p.password else None, p.hostname, p.port)
        return urlunsplit((p.scheme, netloc, p.path, "…" if p.query else "", ""))
    return re.sub(r"(password\s*=\s*)('(?:[^'\\]|\\.)*'|\S+)", r"\1***", dsn, flags=re.I)


def _ident(nombre: str) -> str:
    """Identificador SQL entrecomillado. Los nombres salen de pg_class, no de una petición."""
    return '"' + nombre.replace('"', '""') + '"'


def _uno(cur, sql: str, params=()):
    cur.execute(sql, params)
    return cur.fetchone()


def _todos(cur, sql: str, params=()):
    cur.execute(sql, params)
    return cur.fetchall()


# ── configuración ─────────────────────────────────────────────────────────────────────────


@dataclass
class Config:
    modo: str = "rls"
    columna: str = "tenant_id"
    ajuste: str = "app.tenant_id"
    esquema: str = "public"
    excepciones: dict = field(default_factory=dict)
    funciones_de_ambito: list = field(default_factory=list)
    exigir_sonda: bool = False
    solo_estatico: bool = False
    sonda_escritura: bool = False
    exigir_escritura: bool = False
    origen: str = "valores por defecto (sin manifiesto)"


SOLO_CLI = {"exigir_sonda", "solo_estatico", "sonda_escritura", "exigir_escritura", "origen"}


def cargar_config(args) -> Config:
    cfg = Config()
    ruta = args.manifiesto
    if ruta is None and os.path.exists(MANIFIESTO_POR_DEFECTO):
        ruta = MANIFIESTO_POR_DEFECTO
    if ruta:
        try:
            with open(ruta, encoding="utf-8") as f:
                datos = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise NoMedible(f"el manifiesto {ruta} no se puede leer: {e}") from e
        sobran = set(datos) - (set(Config.__dataclass_fields__) - SOLO_CLI)
        if sobran:
            # Un campo que nadie lee es indistinguible de uno que funciona (rules/verification.md
            # §Lo importante no es que FALTE algo: es que SOBRE algo).
            raise NoMedible(f"el manifiesto {ruta} trae claves que el gate no lee: "
                            f"{sorted(sobran)}")
        for k, v in datos.items():
            setattr(cfg, k, v)
        cfg.origen = ruta
    for k in ("modo", "columna", "ajuste", "esquema"):
        v = getattr(args, k, None)
        if v:
            setattr(cfg, k, v)
    if args.funcion_ambito:
        cfg.funciones_de_ambito = list(cfg.funciones_de_ambito) + list(args.funcion_ambito)
    cfg.exigir_sonda = bool(args.exigir_sonda)
    cfg.solo_estatico = bool(args.solo_estatico)
    cfg.sonda_escritura = bool(args.sonda_escritura or args.exigir_escritura)
    cfg.exigir_escritura = bool(args.exigir_escritura)
    if cfg.modo not in ("rls", "aplicacion"):
        raise NoMedible(f"modo desconocido: {cfg.modo!r} (rls | aplicacion)")
    return cfg


# ── resultado ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Hallazgo:
    id: str
    tabla: str
    que: str
    porque: str


@dataclass
class Resultado:
    veredicto: str = "ok"
    dsn: str = ""
    modo: str = ""
    config: str = ""
    rol: dict = field(default_factory=dict)
    tablas: list = field(default_factory=list)
    hallazgos: list = field(default_factory=list)
    sonda: dict = field(default_factory=dict)
    notas: list = field(default_factory=list)

    def falla(self, id_, tabla, que, porque):
        self.hallazgos.append(Hallazgo(id_, tabla, que, porque))

    def ids(self) -> set:
        return {h.id for h in self.hallazgos}


# ── lo que se lee del catálogo ────────────────────────────────────────────────────────────

SQL_INVENTARIO = """
SELECT n.nspname,
       c.relname,
       c.relkind,
       c.relrowsecurity,
       c.relforcerowsecurity,
       pg_get_userbyid(c.relowner) AS dueno,
       a.attnotnull,
       EXISTS (SELECT 1 FROM pg_constraint k
               WHERE k.conrelid = c.oid AND k.contype = 'f' AND a.attnum = ANY (k.conkey)) AS es_fk,
       COALESCE(array_to_string(c.reloptions, ','), '') AS opciones,
       format_type(a.atttypid, a.atttypmod) AS tipo_columna
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = %s AND a.attnum > 0 AND NOT a.attisdropped
WHERE c.relkind IN ('r', 'p', 'v', 'm')
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND n.nspname NOT LIKE 'pg_toast%%' AND n.nspname NOT LIKE 'pg_temp%%'
ORDER BY n.nspname, c.relname
"""

SQL_POLITICAS = """
SELECT tablename, policyname, permissive, array_to_string(roles, ','), cmd, qual, with_check
FROM pg_policies WHERE schemaname = %s
"""


def _rol(cur) -> dict:
    fila = _uno(
        cur,
        "SELECT current_user, r.rolsuper, r.rolbypassrls FROM pg_roles r "
        "WHERE r.rolname = current_user",
    )
    return {"nombre": fila[0], "superusuario": bool(fila[1]), "bypassrls": bool(fila[2])}


def _roles_que_aplican(cur) -> set:
    filas = _todos(cur, "SELECT rolname FROM pg_roles "
                        "WHERE pg_has_role(current_user, oid, 'MEMBER')")
    return {f[0] for f in filas} | {"public"}


def _supera_rls(cur, rol: str) -> bool:
    fila = _uno(cur, "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = %s", (rol,))
    return bool(fila and fila[0])


def _filtra_por_tenant(expr: str | None, cfg: Config) -> bool:
    """¿La expresión NOMBRA la columna del tenant y el ámbito de la sesión? Es léxico (ver el
    docstring del módulo)."""
    if not expr:
        return False
    if not re.search(rf"\b{re.escape(cfg.columna)}\b", expr):
        return False
    ajustes = re.findall(r"current_setting\(\s*'([^']+)'", expr)
    if cfg.ajuste in ajustes:
        return True
    return any(re.search(rf"\b{re.escape(fn)}\s*\(", expr) for fn in cfg.funciones_de_ambito)


def _check_efectivo(p: dict) -> str | None:
    """El WITH CHECK que de verdad aplica: si falta, ALL y UPDATE usan el USING (documentación
    de Postgres)."""
    if p["check"] is not None:
        return p["check"]
    return p["qual"] if p["cmd"] in ("ALL", "UPDATE") else None


# ── la medición ───────────────────────────────────────────────────────────────────────────


def medir(dsn: str, dsn_admin: str | None, cfg: Config) -> Resultado:
    res = Resultado(dsn=redactar_dsn(dsn), modo=cfg.modo, config=cfg.origen)
    conn = conectar(dsn)
    try:
        cur = conn.cursor()
        res.rol = _rol(cur)
        todas = _todos(cur, SQL_INVENTARIO, (cfg.columna,))
        filas = [f for f in todas if f[0] == cfg.esquema]
        fuera = [f for f in todas if f[0] != cfg.esquema]
        if not filas:
            raise NoMedible(
                f"0 tablas con la columna «{cfg.columna}» en el esquema «{cfg.esquema}» de "
                f"{res.dsn}" + (f" (sí hay {len(fuera)} en otros esquemas)" if fuera else "")
                + ". Un inventario vacío no es «limpio»: es la columna, el esquema o la base "
                "equivocados."
            )
        politicas = {}
        for t, nombre, permisiva, roles, cmd, qual, check in _todos(cur, SQL_POLITICAS,
                                                                     (cfg.esquema,)):
            politicas.setdefault(t, []).append(
                dict(nombre=nombre, permisiva=permisiva == "PERMISSIVE",
                     roles=set((roles or "").split(",")) - {""}, cmd=cmd, qual=qual, check=check)
            )
        aplican = _roles_que_aplican(cur)
        tablas = []
        for _esq, relname, relkind, rls, force, dueno, notnull, es_fk, opciones, tipo in filas:
            tablas.append(dict(tabla=relname, tipo={"r": "tabla", "p": "tabla", "v": "vista",
                                                     "m": "vista materializada"}[relkind],
                               rls=bool(rls), force=bool(force), dueno=dueno,
                               not_null=bool(notnull), es_fk=bool(es_fk), opciones=opciones,
                               tipo_columna=tipo, excepcion=relname in cfg.excepciones))
        res.tablas = tablas
        _comprobar_excepciones(res, cfg, {f"{f[0]}.{f[1]}" for f in fuera})
        _comprobar_fuera_del_esquema(res, cfg, fuera)
        if cfg.modo == "aplicacion":
            _comprobar_modo_aplicacion(res)
            res.notas.append(
                "modo aplicacion: sin RLS, el aislamiento lo prueba la suite del ORM "
                "(templates/seguridad-tenant/). Este gate solo mira NOT NULL y clave ajena."
            )
        else:
            _comprobar_rol(res, cur)
            _comprobar_rls(res, cfg, politicas, aplican, cur)
        conn.rollback()
        if cfg.modo == "rls":
            _sonda(res, conn, dsn_admin, cfg)
    finally:
        conn.close()
    res.veredicto = "fallo" if res.hallazgos else "ok"
    if res.veredicto == "ok" and cfg.modo == "rls":
        if not res.sonda.get("medida") and not cfg.solo_estatico:
            res.veredicto = "no_medido"
            res.notas.append("veredicto NO MEDIDO: lo estático está bien, pero la lectura de las "
                             "políticas es léxica y sin la sonda nadie ha visto filtrar. Pasa "
                             "--dsn-admin, o --solo-estatico si sabes lo que te dejas")
        elif cfg.exigir_sonda and res.sonda.get("no_medidas"):
            res.veredicto = "no_medido"
        elif cfg.exigir_escritura and res.sonda.get("escritura_no_medida"):
            res.veredicto = "no_medido"
    return res


def _comprobar_excepciones(res: Resultado, cfg: Config, fuera: set) -> None:
    en_inventario = {t["tabla"] for t in res.tablas} | fuera
    for tabla, razon in sorted(cfg.excepciones.items()):
        if tabla not in en_inventario:
            res.falla("G4-EXCEPCION-CADUCADA", tabla,
                      "excepción declarada para una tabla que ya no lleva la columna (o no existe)",
                      "una excepción que no corresponde a nada es una lista que crece sola: "
                      "quítala del manifiesto")
        if not isinstance(razon, str) or len(razon.strip()) < RAZON_MINIMA:
            res.falla("G4-EXCEPCION-SIN-RAZON", tabla,
                      "excepción sin una razón escrita",
                      "saltarse el aislamiento en una tabla es una decisión; sin su porqué, el "
                      "próximo que la lea no sabe si sigue valiendo")


def _comprobar_fuera_del_esquema(res: Resultado, cfg: Config, fuera: list) -> None:
    for fila in fuera:
        nombre = f"{fila[0]}.{fila[1]}"
        if nombre not in cfg.excepciones:
            res.falla("G4-FUERA-DEL-ESQUEMA", nombre,
                      f"lleva la columna {cfg.columna} y está fuera del esquema medido "
                      f"({cfg.esquema})",
                      "el inventario se descubre: una tabla en otro esquema también lo es. Mídela "
                      "con --esquema o declárala como excepción `esquema.tabla` con su razón")


def _comprobar_modo_aplicacion(res: Resultado) -> None:
    for t in res.tablas:
        if t["excepcion"] or t["tipo"] != "tabla":
            continue
        if not t["not_null"]:
            res.falla("G4-TENANT-NULLABLE", t["tabla"], "la columna del tenant admite NULL",
                      "una fila sin tenant no es de nadie, y un filtro `tenant_id = X` no la "
                      "ve pero un `IS NULL` olvidado la ve desde todos")
        if not t["es_fk"]:
            res.falla("G4-TENANT-SIN-FK", t["tabla"], "la columna del tenant no es clave ajena",
                      "sin FK, un tenant_id que no existe se guarda sin error")


def _comprobar_rol(res: Resultado, cur) -> None:
    if res.rol.get("superusuario"):
        res.falla("G4-ROL-SUPER", "-", f"la app conecta como superusuario ({res.rol['nombre']})",
                  "un superusuario se salta TODA política RLS: con este rol las tablas parecen "
                  "protegidas y no lo están (CCC, ADR-0003)")
    if res.rol.get("bypassrls"):
        res.falla("G4-ROL-BYPASS", "-", f"el rol de la app ({res.rol['nombre']}) tiene BYPASSRLS",
                  "es el otro camino para saltarse RLS y no coincide con ser superusuario")
    # Poder hacer `SET ROLE` a un rol que se salta RLS basta (verificador, N11). Desde PG 16 la
    # pertenencia puede ir sin la opción SET (`WITH SET FALSE`), y entonces no: se pregunta por SET
    # (3.ª pasada, O1). Antes de PG 16, ser miembro es poder hacer SET ROLE.
    privilegio = "SET" if int(_uno(cur, "SHOW server_version_num")[0]) >= 160000 else "MEMBER"
    heredados = [f[0] for f in _todos(
        cur, "SELECT r.rolname FROM pg_roles r WHERE (r.rolsuper OR r.rolbypassrls) "
             "AND r.rolname <> current_user AND pg_has_role(current_user, r.oid, %s)",
        (privilegio,))]
    if heredados:
        res.falla("G4-ROL-BYPASS", "-", f"el rol de la app es miembro de {sorted(heredados)}, que "
                  "se salta RLS", "con `SET ROLE` la app ve las filas de todos los tenants")


def _comprobar_rls(res: Resultado, cfg: Config, politicas: dict, aplican: set, cur) -> None:
    for t in res.tablas:
        if t["excepcion"]:
            continue
        nombre = t["tabla"]
        if t["tipo"] != "tabla":
            opciones = t["opciones"].lower()
            invoker = "security_invoker=true" in opciones or "security_invoker=on" in opciones
            if not invoker and _supera_rls(cur, t["dueno"]):
                res.falla("G4-VISTA-SIN-INVOKER", nombre,
                          f"{t['tipo']} sin security_invoker cuyo dueño ({t['dueno']}) "
                          "se salta RLS",
                          "la vista lee las tablas con los permisos de su dueño: devuelve las "
                          "filas de todos los tenants a quien la consulte")
            continue
        if not t["rls"]:
            res.falla("G4-RLS-APAGADO", nombre, "RLS no está activo",
                      "la tabla lleva la columna del tenant y la base no filtra nada")
        elif not t["force"]:
            res.falla("G4-RLS-SIN-FORCE", nombre, "RLS activo pero no FORZADO",
                      f"el dueño de la tabla ({t['dueno']}) se salta sus políticas; si la app es "
                      "la dueña (corre las migraciones), RLS se ve encendido y no filtra")
        propias = [p for p in politicas.get(nombre, []) if p["roles"] & aplican]
        permisivas = [p for p in propias if p["permisiva"]]
        restrictivas = [p for p in propias if not p["permisiva"]]
        if not permisivas:
            res.falla("G4-SIN-POLITICA", nombre,
                      "ninguna política permisiva aplica al rol de la app",
                      "o la app no ve ni sus filas, o algo fuera de la base hace el filtro: "
                      "declara la excepción con su razón o crea la política")
            continue
        # Una restrictiva que filtra se suma con AND: cierra lo que una permisiva abierta abra, pero
        # SOLO para los comandos que cubre. Una restrictiva FOR SELECT no cierra un FOR DELETE
        # USING (true): eso borró filas de B desde A (verificador de la 2.24, segunda pasada).
        def cierra(cmd: str, clausula: str, restrictivas: list = restrictivas) -> bool:
            cubiertos = {"ALL": ("SELECT", "UPDATE", "DELETE") if clausula == "USING"
                         else ("INSERT", "UPDATE")}.get(cmd, (cmd,))
            return all(any(r["cmd"] in ("ALL", c) and _filtra_por_tenant(
                r["qual"] if clausula == "USING" else _check_efectivo(r), cfg)
                for r in restrictivas) for c in cubiertos)

        cierra_lectura = cierra("SELECT", "USING")
        lee = [p for p in permisivas if p["cmd"] in ("ALL", "SELECT")]
        for p in permisivas:
            for cual, expr in (("USING", p["qual"]), ("WITH CHECK", p["check"])):
                cerrada = cierra(p["cmd"], cual)
                if expr is not None and not cerrada and not _filtra_por_tenant(expr, cfg):
                    res.falla("G4-POLITICA-ABIERTA", nombre,
                              f"la política «{p['nombre']}» ({p['cmd']}) tiene un {cual} que no "
                              f"filtra por {cfg.columna} contra {cfg.ajuste}",
                              "las políticas permisivas se suman con OR: una que no filtra abre "
                              "la tabla entera aunque haya otra buena al lado")
        lee_bien = bool(lee) and (cierra_lectura
                                  or any(_filtra_por_tenant(p["qual"], cfg) for p in lee))
        if not lee_bien and not any(h.tabla == nombre and h.id == "G4-POLITICA-ABIERTA"
                                    for h in res.hallazgos):
            res.falla("G4-SIN-POLITICA", nombre,
                      "ninguna política de lectura (ALL/SELECT) filtra por el tenant",
                      "la lectura queda sin política propia: la app no ve sus filas o las ve "
                      "por otra vía que este gate no controla")


def _sonda(res: Resultado, conn, dsn_admin: str | None, cfg: Config) -> None:
    """Dos tenants sobre la MISMA conexión de la app. Solo cuenta filas; todo se deshace."""
    objetivo = [t for t in res.tablas if not t["excepcion"]]
    if not dsn_admin:
        res.sonda = {"medida": False, "porque": "sin --dsn-admin no se sabe qué filas hay de "
                     "cada tenant", "no_medidas": [t["tabla"] for t in objetivo]}
        res.notas.append("SONDA no medida: pasa --dsn-admin (un rol que vea todo, solo para "
                         "contar) para probar dos tenants sobre la misma conexión")
        return
    admin = conectar(dsn_admin)
    try:
        acur = admin.cursor()
        rol_admin = _rol(acur)
        if not (rol_admin["superusuario"] or rol_admin["bypassrls"]):
            raise NoMedible(
                f"el DSN de admin ({rol_admin['nombre']}) no es superusuario ni tiene BYPASSRLS: "
                "sus recuentos estarían filtrados por RLS y la sonda compararía contra un "
                "número falso"
            )
        conteos = {}
        for t in objetivo:
            filas = _todos(acur, f"SELECT {_ident(cfg.columna)}::text, count(*) FROM "
                                 f"{_ident(cfg.esquema)}.{_ident(t['tabla'])} "
                                 f"WHERE {_ident(cfg.columna)} IS NOT NULL "
                                 "GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 2")
            conteos[t["tabla"]] = [(f[0], int(f[1])) for f in filas]
        admin.rollback()
    finally:
        admin.close()

    medibles = {k: v for k, v in conteos.items() if len(v) == 2}
    no_medidas = sorted(set(conteos) - set(medibles))
    cur = conn.cursor()
    detalle = {}

    def contar(tabla, ambito):
        """(total, ajenas) bajo un ámbito; ("error", tipo) si la consulta revienta."""
        try:
            # El driver abre la transacción con la primera sentencia; esta es la primera.
            cur.execute("SET TRANSACTION READ ONLY")
            if ambito is not None:
                cur.execute("SELECT set_config(%s, %s, true)", (cfg.ajuste, ambito))
            ajeno = ambito if ambito else ""
            cur.execute(
                f"SELECT count(*), count(*) FILTER (WHERE {_ident(cfg.columna)}::text "
                f"IS DISTINCT FROM %s) FROM {_ident(cfg.esquema)}.{_ident(tabla)}",
                (ajeno,),
            )
            total, ajenas = cur.fetchone()
            return int(total), int(ajenas)
        except Exception as e:  # noqa: BLE001 — un error aquí es «cerrado» o «dueño ciego»
            return ("error", type(e).__name__)
        finally:
            conn.rollback()

    # 1) Conexión recién abierta, el ajuste NUNCA fijado en esta sesión: tiene que ser 0. Va antes
    #    que nada porque, una vez fijado aunque sea LOCAL, el ajuste ya existe en la sesión vacío.
    for tabla in sorted(conteos):
        r = contar(tabla, None)
        detalle.setdefault(tabla, {})["nunca_fijado"] = r
        if isinstance(r[0], int) and r[0] > 0:
            res.falla("G4-SONDA-SIN-AMBITO", tabla,
                      f"sin ámbito la app ve {r[0]} fila(s)",
                      "«sin tenant» tiene que ser «sin datos», no «todos los datos»: un olvido "
                      "del ámbito se convierte en fuga")
    # 2) Ámbito vacío, A y B: en la MISMA conexión, una transacción detrás de otra.
    for tabla in sorted(conteos):
        r = contar(tabla, "")
        detalle[tabla]["ambito_vacio"] = r
        if isinstance(r[0], int) and r[0] > 0:
            res.falla("G4-SONDA-SIN-AMBITO", tabla, f"con el ámbito vacío la app ve {r[0]} fila(s)",
                      "el ámbito vacío tiene que significar «sin datos»")
    for tabla, pares in sorted(medibles.items()):
        for etiqueta, (tenant, esperadas) in zip(("A", "B"), pares, strict=True):
            r = contar(tabla, tenant)
            detalle[tabla][etiqueta] = {"visibles": r[0], "ajenas": r[1], "esperadas": esperadas}
            if not isinstance(r[0], int):
                res.falla("G4-SONDA-DUENO-CIEGO", tabla,
                          f"con el ámbito del tenant {etiqueta} la consulta da error ({r[1]})",
                          "el dueño tiene que poder leer sus filas; si no, la política está mal "
                          "y el aislamiento «perfecto» es un producto roto")
                continue
            if r[1] > 0:
                res.falla("G4-SONDA-FUGA", tabla,
                          f"con el ámbito del tenant {etiqueta} la app ve {r[1]} fila(s) de otro "
                          "tenant", "FUGA: el contenido no se imprime a propósito")
            elif r[0] < esperadas:
                res.falla("G4-SONDA-DUENO-CIEGO", tabla,
                          f"con el ámbito del tenant {etiqueta} la app ve {r[0]} de sus "
                          f"{esperadas} fila(s)",
                          "el control negativo: un filtro que no devuelve nada aprueba siempre "
                          "el test de fuga")
    if cfg.sonda_escritura:
        tipos = {t["tabla"]: t for t in res.tablas}
        for tabla, ((a, na), (b, _)) in sorted(medibles.items()):
            if tipos[tabla]["tipo"] != "tabla":
                continue
            detalle[tabla]["escritura"] = _sonda_escritura(res, conn, cfg, tabla,
                                                           tipos[tabla]["tipo_columna"], a, na, b,
                                                           dsn_admin)
    res.sonda.update({"medida": True, "tablas_medidas": sorted(medibles),
                      "no_medidas": no_medidas, "escritura": cfg.sonda_escritura,
                      "detalle": detalle})
    if no_medidas:
        res.notas.append(f"SONDA sin datos de dos tenants en {len(no_medidas)} tabla(s): "
                         f"{', '.join(no_medidas)} — ahí la sonda no prueba nada")


def _borrar_como_app(dsn_admin: str | None, app: str | None, cfg: Config, t: str,
                     a: str) -> int | str:
    """El DELETE sin WHERE de `alcance_delete`, desde el admin con las FK apagadas y como la app.

    Solo si el admin es superusuario (es el único que puede tocar `session_replication_role`).
    `SET LOCAL ROLE` a la app va después: desde ahí, RLS (y FORCE) se aplican como a la app.
    Devuelve las filas que borró —antes del rollback— o por qué no se pudo medir.
    """
    if not dsn_admin or not app:
        return "no medida (una FK inmediata lo impide y no hay admin con el que repetirlo)"
    admin = conectar(dsn_admin)
    try:
        cur = admin.cursor()
        if not _rol(cur)["superusuario"]:
            return ("no medida (una FK inmediata lo impide y el admin no es superusuario: no "
                    "puede apagar sus disparadores)")
        admin.rollback()
        cur.execute("SET LOCAL session_replication_role = replica")
        cur.execute(f"SET LOCAL ROLE {_ident(app)}")
        cur.execute("SELECT set_config(%s, %s, true)", (cfg.ajuste, a))
        cur.execute(f"DELETE FROM {t}")
        return cur.rowcount or 0
    except Exception as e:  # noqa: BLE001 — cualquier otra cosa es «no medida»
        return f"no medida desde el admin ({type(e).__name__})"
    finally:
        admin.rollback()
        admin.close()


ESCRITURAS = {
    "insertar": ("con el ámbito de A, la política dejó pasar una fila NUEVA con el tenant de B",
                 "el WITH CHECK no compara el tenant de la fila con el del ámbito"),
    "mover": ("con el ámbito de A, un UPDATE movió filas de A a B",
              "el WITH CHECK del UPDATE no compara el tenant de la fila nueva con el del ámbito"),
    "alcance_delete": ("con el ámbito de A, un DELETE alcanzó filas de B",
                       "el USING del DELETE no filtra por el tenant: A puede borrar datos de B"),
}


def _sonda_escritura(res: Resultado, conn, cfg: Config, tabla: str, tipo: str, a: str,
                     propias: int, b: str, dsn_admin: str | None = None) -> dict:
    """Con el ámbito de A, tres escrituras que la política tiene que impedir; todas se deshacen.

    - insertar: una copia de una fila de A con el tenant de B. Las columnas con valor por defecto
      se omiten (una serial pone la suya); las demás se copian. Postgres mira el WITH CHECK ANTES
      que la unicidad y las FK (medido el 20-10): un choque de clave significa que la política ya
      había dejado pasar la fila, así que cuenta como abierta.
    - mover: `UPDATE … SET tenant = B` SIN WHERE. Con WHERE, Postgres exige además que la fila
      nueva pase el USING de las políticas de SELECT y lo rechaza; sin WHERE, solo mira el WITH
      CHECK, y uno flojo deja mover (lo midió el verificador de la 2.24). Como en el INSERT, el
      WITH CHECK va antes que la unicidad: un choque de clave al mover también es «abierta».
    - alcance_delete: un DELETE sin WHERE no puede tocar más filas que las de A: si toca más, el
      USING del DELETE no filtra. Las FK diferibles se aplazan (`SET CONSTRAINTS ALL DEFERRED`; el
      rollback hace que no se comprueben nunca). Una FK INMEDIATA que otra tabla apunta revienta
      el DELETE aunque la política esté bien; entonces se repite desde el admin, si es
      superusuario, con los disparadores de FK apagados para esa transacción
      (`session_replication_role = replica`) y `SET ROLE` al rol de la app, que es quien pasa por
      RLS (3.ª pasada del verificador: con FK inmediatas el gate salía siempre 2).
    El UPDATE no necesita su propia prueba de alcance: tocar una fila de B solo pasa si el WITH
    CHECK es flojo, y entonces «mover» ya cae (lo midieron los mutantes).
    Un rechazo por otra razón (un trigger, una FK inmediata sin admin superusuario) es «no
    medida»: se anota, y con `--exigir-escritura` el veredicto pasa a NO MEDIDO.
    """
    cur = conn.cursor()
    col, t = _ident(cfg.columna), f"{_ident(cfg.esquema)}.{_ident(tabla)}"
    columnas = [f[0] for f in _todos(
        cur, "SELECT attname FROM pg_attribute WHERE attrelid = %s::regclass AND attnum > 0 "
             "AND NOT attisdropped AND attgenerated = '' AND attidentity = '' "
             "AND (NOT atthasdef OR attname = %s) ORDER BY attnum", (t, cfg.columna))]
    conn.rollback()
    lista = ", ".join(_ident(c) for c in columnas)
    # `tipo` sale de format_type() del catálogo, no de nadie: es seguro interpolarlo.
    valores = ", ".join(f"CAST(%s AS {tipo})" if c == cfg.columna else _ident(c) for c in columnas)
    pruebas = [
        ("insertar", f"INSERT INTO {t} ({lista}) SELECT {valores} FROM {t} "
                     f"WHERE {col}::text = %s LIMIT 1", (b, a), lambda n: n > 0),
        ("mover", f"UPDATE {t} SET {col} = CAST(%s AS {tipo})", (b,), lambda n: n > 0),
        ("alcance_delete", f"DELETE FROM {t}", (), lambda n: n > propias),
    ]
    resultados = {}
    for nombre, sql, params, abierta in pruebas:
        codigo = None
        try:
            if nombre == "alcance_delete":
                cur.execute("SET CONSTRAINTS ALL DEFERRED")
            cur.execute("SELECT set_config(%s, %s, true)", (cfg.ajuste, a))
            cur.execute(sql, params)
            estado = "ABIERTA" if abierta(cur.rowcount or 0) else "cerrada"
        except Exception as e:  # noqa: BLE001 — se clasifica abajo
            codigo = getattr(e, "sqlstate", None) or getattr(e, "pgcode", None)
            texto = str(e).lower()
            if "row-level security" in texto or "permission denied" in texto:
                estado = "cerrada por la política o el permiso"
            elif nombre in ("insertar", "mover") and codigo in ("23505", "23503"):
                estado = "ABIERTA"  # unicidad o FK: la política ya la había dejado pasar
            else:
                estado = f"no medida ({type(e).__name__})"
        finally:
            conn.rollback()
        if nombre == "alcance_delete" and codigo == "23503":
            n = _borrar_como_app(dsn_admin, (res.rol or {}).get("nombre"), cfg, t, a)
            if isinstance(n, int):
                estado = ("ABIERTA" if abierta(n)
                          else "cerrada (medida desde el admin: FK inmediata)")
            else:
                estado = n
        resultados[nombre] = estado
        if estado == "ABIERTA":
            que, porque = ESCRITURAS[nombre]
            res.falla("G4-SONDA-ESCRITURA", tabla, que + " (se ha deshecho)", porque)
        elif estado.startswith("no medida"):
            res.sonda.setdefault("escritura_no_medida", []).append(f"{tabla}:{nombre}")
            res.notas.append(f"sonda de escritura «{nombre}» en {tabla}: la base la rechazó por "
                             f"otra razón ({estado}); no se sabe si la política la habría parado")
    return resultados


# ── salida ────────────────────────────────────────────────────────────────────────────────


def imprimir(res: Resultado) -> None:
    print(f"G4 · gate_tenant · {res.dsn}")
    print(f"   modo {res.modo} · config: {res.config}")
    if res.rol:
        print(f"   rol de la app: {res.rol['nombre']} · superusuario={res.rol['superusuario']} · "
              f"bypassrls={res.rol['bypassrls']}")
    print(f"   inventario: {len(res.tablas)} relación(es) con la columna del tenant")
    for t in res.tablas:
        marca = "excepción" if t["excepcion"] else f"rls={t['rls']} force={t['force']}"
        print(f"     · {t['tabla']} ({t['tipo']}) · {marca}")
    if res.sonda.get("medida"):
        print(f"   sonda: {len(res.sonda['tablas_medidas'])} tabla(s) con dos tenants medidas"
              + (" · con escritura" if res.sonda.get("escritura") else ""))
    for n in res.notas:
        print(f"   nota: {n}")
    if res.hallazgos:
        print(f"\n✗ {len(res.hallazgos)} hallazgo(s):")
        for h in res.hallazgos:
            print(f"  [{h.id}] {h.tabla}: {h.que}\n      porque: {h.porque}")
    print(f"\nveredicto: {res.veredicto.upper()}")


def _a_json(res: Resultado) -> str:
    return json.dumps(asdict(res), ensure_ascii=False, indent=1)


# ── autoprueba: el gate se ve fallar ─────────────────────────────────────────────────────

ESQUEMA_JUGUETE = """
CREATE TABLE tenants (id uuid PRIMARY KEY, nombre text NOT NULL);
CREATE TABLE productos (id serial PRIMARY KEY,
                        tenant_id uuid NOT NULL REFERENCES tenants(id), nombre text NOT NULL);
CREATE TABLE pedidos (id serial PRIMARY KEY,
                      tenant_id uuid NOT NULL REFERENCES tenants(id),
                      producto_id int REFERENCES productos(id), total numeric NOT NULL);
"""

FILTRO = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
POLITICA = ("CREATE POLICY {t}_aislamiento ON {t} USING (" + FILTRO + ") WITH CHECK ("
            + FILTRO + ");")
RECREA_PEDIDOS = "DROP POLICY pedidos_aislamiento ON pedidos; "

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"

SEMILLA = f"""
INSERT INTO tenants VALUES ('{TENANT_A}', 'Repuestos A'), ('{TENANT_B}', 'Repuestos B');
INSERT INTO productos (tenant_id, nombre) VALUES
  ('{TENANT_A}', 'prueba-a1'), ('{TENANT_A}', 'prueba-a2'), ('{TENANT_A}', 'prueba-a3'),
  ('{TENANT_B}', 'prueba-b1'), ('{TENANT_B}', 'prueba-b2');
INSERT INTO pedidos (tenant_id, producto_id, total) VALUES
  ('{TENANT_A}', 1, 10), ('{TENANT_A}', 2, 20), ('{TENANT_B}', 4, 30);
"""

# (nombre, SQL extra tras el esquema limpio, cambios de config, cómo conecta la app,
#  ids esperados, opciones). Esperados vacío = tiene que salir verde y con la sonda medida.
# Opciones: {"sin_admin": True} mide sin --dsn-admin; {"veredicto": "no_medido"} lo exige.
SABOTAJES = [
    ("limpio (control: tiene que salir 0)", "", {}, "app", set(), {}),
    ("tabla nueva con tenant_id y sin RLS",
     f"CREATE TABLE facturas (id serial PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES "
     f"tenants(id), importe numeric NOT NULL); INSERT INTO facturas (tenant_id, importe) VALUES "
     f"('{TENANT_A}', 1), ('{TENANT_B}', 2); ALTER TABLE facturas OWNER TO {{app}};",
     {}, "app", {"G4-RLS-APAGADO", "G4-SIN-POLITICA", "G4-SONDA-FUGA", "G4-SONDA-SIN-AMBITO"}, {}),
    ("RLS sin FORCE con la app de dueña",
     "ALTER TABLE productos NO FORCE ROW LEVEL SECURITY;",
     {}, "app", {"G4-RLS-SIN-FORCE", "G4-SONDA-FUGA"}, {}),
    ("rol de la app con BYPASSRLS", "", {}, "bypass", {"G4-ROL-BYPASS", "G4-SONDA-FUGA"}, {}),
    ("la app conecta como superusuario", "", {}, "admin", {"G4-ROL-SUPER", "G4-SONDA-FUGA"}, {}),
    ("una política permisiva extra con USING (true)",
     "CREATE POLICY ver_todo ON productos FOR SELECT USING (true);",
     {}, "app", {"G4-POLITICA-ABIERTA", "G4-SONDA-FUGA"}, {}),
    ("una política FOR INSERT aparte con WITH CHECK (true)",
     "CREATE POLICY meter_todo ON productos FOR INSERT WITH CHECK (true);",
     {}, "app", {"G4-POLITICA-ABIERTA"}, {}),
    ("la política mira otro ajuste de sesión",
     RECREA_PEDIDOS + "CREATE POLICY pedidos_aislamiento ON pedidos "
     "USING (tenant_id = NULLIF(current_setting('app.otro', true), '')::uuid);",
     {}, "app", {"G4-POLITICA-ABIERTA", "G4-SONDA-DUENO-CIEGO"}, {}),
    ("solo hay política de INSERT: nadie filtra la lectura",
     RECREA_PEDIDOS + "CREATE POLICY pedidos_meter ON pedidos FOR INSERT WITH CHECK (" + FILTRO
     + ");", {}, "app", {"G4-SIN-POLITICA", "G4-SONDA-DUENO-CIEGO"}, {}),
    # Los tres siguientes pasan la lectura estática (la política nombra la columna y el ajuste) y
    # solo los caza la sonda. Van separados porque cada uno lo caza una pasada distinta: el
    # primero, la conexión en la que el ámbito NUNCA se fijó (una tarea de Celery que no lo
    # abre); el segundo, el ámbito abierto vacío; el tercero, la sonda de escritura.
    ("la política se abre si el ámbito nunca se fijó en la sesión (COALESCE sin NULLIF)",
     RECREA_PEDIDOS + "CREATE POLICY pedidos_aislamiento ON pedidos "
     "USING (tenant_id::text = COALESCE(current_setting('app.tenant_id', true), "
     "tenant_id::text));",
     {}, "app", {"G4-SONDA-SIN-AMBITO"}, {}),
    ("la política se abre con el ámbito vacío",
     RECREA_PEDIDOS + "CREATE POLICY pedidos_aislamiento ON pedidos "
     "USING (CASE WHEN current_setting('app.tenant_id', true) = '' THEN true "
     "ELSE tenant_id = current_setting('app.tenant_id', true)::uuid END);",
     {}, "app", {"G4-SONDA-SIN-AMBITO"}, {}),
    ("WITH CHECK que nombra la columna y el ajuste sin compararlos",
     RECREA_PEDIDOS + "CREATE POLICY pedidos_aislamiento ON pedidos USING (" + FILTRO + ") "
     "WITH CHECK (tenant_id IS NOT NULL AND current_setting('app.tenant_id', true) IS NOT NULL);",
     {}, "app", {"G4-SONDA-ESCRITURA"}, {}),
    ("la política revienta con el ámbito puesto",
     RECREA_PEDIDOS + "CREATE POLICY pedidos_aislamiento ON pedidos USING (tenant_id = "
     "(current_setting('app.tenant_id', true) || '-x')::uuid);",
     {}, "app", {"G4-SONDA-DUENO-CIEGO"}, {}),
    ("vista sin security_invoker de un dueño que se salta RLS",
     "CREATE VIEW resumen_pedidos AS SELECT tenant_id, total FROM pedidos; "
     "GRANT SELECT ON resumen_pedidos TO {app};",
     {}, "app", {"G4-VISTA-SIN-INVOKER", "G4-SONDA-FUGA"}, {}),
    ("tabla con tenant_id en otro esquema",
     "CREATE SCHEMA ventas; CREATE TABLE ventas.facturas (id serial PRIMARY KEY, tenant_id uuid "
     "NOT NULL REFERENCES tenants(id));",
     {}, "app", {"G4-FUERA-DEL-ESQUEMA"}, {}),
    ("excepción declarada para una tabla que ya no existe", "",
     {"excepciones": {"tabla_borrada": "se protegía por su padre, hasta que se borró en 2026"}},
     "app", {"G4-EXCEPCION-CADUCADA"}, {}),
    ("excepción sin razón",
     "CREATE TABLE notas (id serial PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id));"
     " ALTER TABLE notas OWNER TO {app};",
     {"excepciones": {"notas": "legacy"}}, "app", {"G4-EXCEPCION-SIN-RAZON"}, {}),
    ("modo aplicación con tenant_id que admite NULL",
     "ALTER TABLE pedidos ALTER COLUMN tenant_id DROP NOT NULL;",
     {"modo": "aplicacion"}, "app", {"G4-TENANT-NULLABLE"}, {}),
    ("modo aplicación con tenant_id que no es clave ajena",
     "ALTER TABLE pedidos DROP CONSTRAINT pedidos_tenant_id_fkey;",
     {"modo": "aplicacion"}, "app", {"G4-TENANT-SIN-FK"}, {}),
    # Controles de lo que NO debe salir rojo (falsos positivos medidos por el verificador).
    ("control: USING (true) para OTRO rol, que no es el de la app",
     "CREATE ROLE {app}_otro; CREATE POLICY ver_todo_otro ON productos FOR SELECT TO {app}_otro "
     "USING (true);", {}, "app", set(), {"limpiar_rol": "{app}_otro"}),
    ("control: permisiva USING (true) cerrada por una RESTRICTIVA que filtra",
     "CREATE POLICY abre ON productos FOR SELECT USING (true); CREATE POLICY cierra ON productos "
     "AS RESTRICTIVE FOR SELECT USING (" + FILTRO + ");", {}, "app", set(), {}),
    ("modo rls SIN --dsn-admin: lo estático no basta (NO MEDIDO)", "", {}, "app", set(),
     {"sin_admin": True, "veredicto": "no_medido"}),
    # Segunda pasada del verificador de la 2.24:
    ("FOR DELETE USING (true) con una restrictiva FOR SELECT que filtra (no la cierra)",
     "CREATE POLICY borrar_todo ON pedidos FOR DELETE USING (true); CREATE POLICY cierra ON "
     "pedidos AS RESTRICTIVE FOR SELECT USING (" + FILTRO + ");",
     {}, "app", {"G4-POLITICA-ABIERTA", "G4-SONDA-ESCRITURA"}, {}),
    ("FOR UPDATE USING (true) con una restrictiva FOR SELECT que filtra (no la cierra)",
     "CREATE POLICY tocar_todo ON pedidos FOR UPDATE USING (true); CREATE POLICY cierra ON "
     "pedidos AS RESTRICTIVE FOR SELECT USING (" + FILTRO + ");",
     {}, "app", {"G4-POLITICA-ABIERTA", "G4-SONDA-ESCRITURA"}, {}),
    ("políticas por comando con el WITH CHECK flojo solo en la de UPDATE (mueve filas a B)",
     RECREA_PEDIDOS + "CREATE POLICY ver ON pedidos FOR SELECT USING (" + FILTRO + "); "
     "CREATE POLICY meter ON pedidos FOR INSERT WITH CHECK (" + FILTRO + "); "
     "CREATE POLICY borrar ON pedidos FOR DELETE USING (" + FILTRO + "); "
     "CREATE POLICY cambiar ON pedidos FOR UPDATE USING (" + FILTRO + ") WITH CHECK "
     "(tenant_id IS NOT NULL AND current_setting('app.tenant_id', true) IS NOT NULL);",
     {}, "app", {"G4-SONDA-ESCRITURA"}, {}),
    ("WITH CHECK flojo solo en el INSERT, en una tabla cuya PK no tiene default (choca la clave)",
     "CREATE TABLE lineas (id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id), "
     f"cantidad int NOT NULL); INSERT INTO lineas VALUES (gen_random_uuid(), '{TENANT_A}', 1), "
     f"(gen_random_uuid(), '{TENANT_A}', 2), (gen_random_uuid(), '{TENANT_B}', 3); "
     "ALTER TABLE lineas ENABLE ROW LEVEL SECURITY; ALTER TABLE lineas FORCE ROW LEVEL SECURITY; "
     "CREATE POLICY ver ON lineas FOR SELECT USING (" + FILTRO + "); "
     "CREATE POLICY cambiar ON lineas FOR UPDATE USING (" + FILTRO + ") WITH CHECK ("
     + FILTRO + "); CREATE POLICY borrar ON lineas FOR DELETE USING (" + FILTRO + "); "
     "CREATE POLICY meter ON lineas FOR INSERT WITH CHECK (tenant_id IS NOT NULL AND "
     "current_setting('app.tenant_id', true) IS NOT NULL); ALTER TABLE lineas OWNER TO {app};",
     {}, "app", {"G4-SONDA-ESCRITURA"}, {}),
    ("el rol de la app es MIEMBRO de un rol con BYPASSRLS", "", {}, "app", {"G4-ROL-BYPASS"},
     {"antes": "GRANT {bypass} TO {app}", "despues": "REVOKE {bypass} FROM {app}"}),
    ("--exigir-sonda con una tabla sin datos de dos tenants (NO MEDIDO)",
     "CREATE TABLE vacia (id serial PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id)); "
     "ALTER TABLE vacia ENABLE ROW LEVEL SECURITY; ALTER TABLE vacia FORCE ROW LEVEL SECURITY; "
     "CREATE POLICY v ON vacia USING (" + FILTRO + ") WITH CHECK (" + FILTRO + "); "
     "ALTER TABLE vacia OWNER TO {app};",
     {"exigir_sonda": True}, "app", set(), {"veredicto": "no_medido"}),
    ("WITH CHECK flojo en el UPDATE de una tabla con UNIQUE: mover choca la clave (sigue abierta)",
     "DROP POLICY productos_aislamiento ON productos; "
     "CREATE POLICY ver ON productos FOR SELECT USING (" + FILTRO + "); "
     "CREATE POLICY meter ON productos FOR INSERT WITH CHECK (" + FILTRO + "); "
     "CREATE POLICY borrar ON productos FOR DELETE USING (" + FILTRO + "); "
     "CREATE POLICY cambiar ON productos FOR UPDATE USING (" + FILTRO + ") WITH CHECK "
     "(tenant_id IS NOT NULL AND current_setting('app.tenant_id', true) IS NOT NULL); "
     "ALTER TABLE productos ADD CONSTRAINT productos_nombre_unico UNIQUE (tenant_id, nombre); "
     f"INSERT INTO productos (tenant_id, nombre) VALUES ('{TENANT_B}', 'prueba-a1');",
     {}, "app", {"G4-SONDA-ESCRITURA"}, {}),
    ("un disparador rechaza toda escritura en pedidos: con --exigir-escritura es NO MEDIDO",
     "CREATE FUNCTION congelada() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION "
     "'tabla congelada'; END $$; CREATE TRIGGER congelada BEFORE INSERT OR UPDATE OR DELETE ON "
     "pedidos FOR EACH ROW EXECUTE FUNCTION congelada();",
     {}, "app", set(), {"veredicto": "no_medido"}),
    ("control: pertenencia a un rol con BYPASSRLS SIN la opción SET (PG 16+) no se lo salta",
     "", {}, "app", set(),
     {"antes": "GRANT {bypass} TO {app} WITH INHERIT FALSE, SET FALSE",
      "despues": "REVOKE {bypass} FROM {app}", "desde_pg": 160000}),
    ("control: permisiva FOR INSERT WITH CHECK (true) cerrada por una RESTRICTIVA FOR INSERT",
     "CREATE POLICY meter_todo ON productos FOR INSERT WITH CHECK (true); CREATE POLICY cierra ON "
     "productos AS RESTRICTIVE FOR INSERT WITH CHECK (" + FILTRO + ");", {}, "app", set(), {}),
]


def _con_base(dsn: str, base: str) -> str:
    p = urlsplit(dsn)
    return urlunsplit((p.scheme, p.netloc, "/" + base, p.query, p.fragment))


def _con_usuario(dsn: str, usuario: str, clave: str) -> str:
    p = urlsplit(dsn)
    netloc = _netloc(usuario, clave, p.hostname or "127.0.0.1", p.port)
    return urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment))


def autoprueba(dsn_admin: str, como_json: bool) -> int:
    if "://" not in dsn_admin:
        raise NoMedible("--autoprueba pide un DSN en forma de URL (postgres://…)")
    host = urlsplit(dsn_admin).hostname or ""
    if host not in ("127.0.0.1", "localhost", "::1", ""):
        raise NoMedible(f"--autoprueba solo corre contra un Postgres local y desechable "
                        f"(127.0.0.1/localhost); el DSN apunta a {host!r}")
    sufijo = secrets.token_hex(4)
    app, bypass = f"g4_app_{sufijo}", f"g4_bypass_{sufijo}"
    clave = secrets.token_hex(12)
    admin = conectar(dsn_admin)
    admin.autocommit = True
    acur = admin.cursor()
    if not _rol(acur)["superusuario"]:
        raise NoMedible("--autoprueba necesita un superusuario: crea bases y roles")
    version = int(_uno(acur, "SHOW server_version_num")[0])
    filas = []
    try:
        # La clave va en el SQL y no como parámetro: psycopg 3 enlaza en el servidor y CREATE ROLE
        # no admite parámetros. Es hexadecimal generado aquí, no viene de nadie.
        acur.execute(f"CREATE ROLE {app} LOGIN PASSWORD '{clave}' NOSUPERUSER NOBYPASSRLS")
        acur.execute(f"CREATE ROLE {bypass} LOGIN PASSWORD '{clave}' NOSUPERUSER BYPASSRLS")
        for i, (nombre, extra, cambios, quien, esperados, opciones) in enumerate(SABOTAJES):
            if version < opciones.get("desde_pg", 0):
                # Un CONTROL que esta versión no sabe escribir: se dice, no se cuenta como hecho.
                filas.append(dict(sabotaje=nombre, ok=True, esperados=[], obtenidos=[],
                                  veredicto=f"no aplica en PG {version} "
                                            f"(pide {opciones['desde_pg']})"))
                continue
            base = f"g4_auto_{sufijo}_{i}"
            acur.execute(f"CREATE DATABASE {base}")
            try:
                b = conectar(_con_base(dsn_admin, base))
                b.autocommit = True
                bc = b.cursor()
                bc.execute(ESQUEMA_JUGUETE)
                for t in ("productos", "pedidos"):
                    bc.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY; "
                               f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY; " + POLITICA.format(t=t))
                    bc.execute(f"ALTER TABLE {t} OWNER TO {app}")
                bc.execute(f"GRANT USAGE ON SCHEMA public TO {app}, {bypass}; "
                           f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {bypass}; "
                           f"GRANT SELECT ON tenants TO {app};")
                bc.execute(SEMILLA)
                if extra:
                    bc.execute(extra.format(app=app))
                bc.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {bypass}")
                b.close()
                # Con --exigir-escritura: un limpio con una prueba de escritura sin medir no es
                # un verde (3.ª pasada: el esquema de juguete, con su FK inmediata, salía 2).
                cfg = Config(sonda_escritura=True, exigir_escritura=True)
                for k, v in cambios.items():
                    setattr(cfg, k, v)
                cfg.origen = f"autoprueba · {nombre}"
                dsn_app = {"app": _con_usuario(_con_base(dsn_admin, base), app, clave),
                           "bypass": _con_usuario(_con_base(dsn_admin, base), bypass, clave),
                           "admin": _con_base(dsn_admin, base)}[quien]
                if opciones.get("antes"):
                    acur.execute(opciones["antes"].format(app=app, bypass=bypass))
                try:
                    r = medir(dsn_app, None if opciones.get("sin_admin")
                              else _con_base(dsn_admin, base), cfg)
                except NoMedible as e:
                    filas.append(dict(sabotaje=nombre, ok=False, esperados=sorted(esperados),
                                      obtenidos=[], veredicto=f"no_medido: {e}"))
                    continue
                obtenidos = r.ids()
                if esperados:
                    ok = esperados <= obtenidos
                elif "veredicto" in opciones:
                    ok = not obtenidos and r.veredicto == opciones["veredicto"]
                else:
                    ok = (not obtenidos and r.veredicto == "ok"
                          and bool(r.sonda.get("tablas_medidas")))
                filas.append(dict(sabotaje=nombre, ok=ok, esperados=sorted(esperados),
                                  obtenidos=sorted(obtenidos), veredicto=r.veredicto))
            finally:
                if opciones.get("despues"):
                    acur.execute(opciones["despues"].format(app=app, bypass=bypass))
                acur.execute(f"DROP DATABASE IF EXISTS {base} WITH (FORCE)")
                if opciones.get("limpiar_rol"):
                    acur.execute(f"DROP ROLE IF EXISTS {opciones['limpiar_rol'].format(app=app)}")
    finally:
        for rol in (app, bypass):
            acur.execute(f"DROP ROLE IF EXISTS {rol}")
        admin.close()
    bien = sum(f["ok"] for f in filas)
    if como_json:
        print(json.dumps({"autoprueba": filas, "bien": bien, "total": len(filas)},
                         ensure_ascii=False, indent=1))
    else:
        print("G4 · autoprueba de gate_tenant.py (cada sabotaje tiene que caer por SU hallazgo)\n")
        for f in filas:
            marca = "✓" if f["ok"] else "✗"
            print(f"  {marca} {f['sabotaje']}")
            if not f["ok"]:
                print(f"      esperaba {f['esperados']} · obtuvo {f['obtenidos']} "
                      f"({f['veredicto']})")
        print(f"\n═══ {bien}/{len(filas)} correctos")
    return EXIT_OK if bien == len(filas) else EXIT_FALLO


# ── main ──────────────────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dsn", help="DSN de la APP (o $GATE_TENANT_DSN, o $DATABASE_URL)")
    ap.add_argument("--dsn-admin", help="DSN de un rol que ve todo, solo para contar filas "
                                        "(o $GATE_TENANT_DSN_ADMIN)")
    ap.add_argument("--manifiesto",
                    help=f"JSON del proyecto (por defecto {MANIFIESTO_POR_DEFECTO})")
    ap.add_argument("--modo", choices=["rls", "aplicacion"])
    ap.add_argument("--columna")
    ap.add_argument("--ajuste")
    ap.add_argument("--esquema")
    ap.add_argument("--funcion-ambito", action="append",
                    help="función SQL que devuelve el tenant de la sesión (repetible)")
    ap.add_argument("--exigir-sonda", action="store_true",
                    help="sin datos de dos tenants en alguna tabla, sale 2 en vez de 0")
    ap.add_argument("--solo-estatico", action="store_true",
                    help="modo rls sin sonda: acepta el veredicto de la lectura estática")
    ap.add_argument("--sonda-escritura", action="store_true",
                    help="prueba además escribir en B desde A (escribe y deshace: CI o test)")
    ap.add_argument("--exigir-escritura", action="store_true",
                    help="implica --sonda-escritura; una escritura no medida sale 2")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--autoprueba", action="store_true")
    args = ap.parse_args(argv)
    dsn_admin = args.dsn_admin or os.environ.get("GATE_TENANT_DSN_ADMIN")
    try:
        try:
            if args.autoprueba:
                if not dsn_admin:
                    raise NoMedible("--autoprueba necesita --dsn-admin (superusuario de un "
                                    "Postgres local y desechable)")
                return autoprueba(dsn_admin, args.json)
            dsn = args.dsn or os.environ.get("GATE_TENANT_DSN") or os.environ.get("DATABASE_URL")
            if not dsn:
                raise NoMedible("falta --dsn (o $GATE_TENANT_DSN / $DATABASE_URL): ¿contra qué "
                                "base mido?")
            cfg = cargar_config(args)
            res = medir(dsn, dsn_admin, cfg)
        except _error_del_driver() as e:
            # «El chequeo se rompió» no es «hay fuga»: tres desenlaces, no dos.
            raise NoMedible(f"error de la base durante la medición: {type(e).__name__}: "
                            f"{str(e).splitlines()[0] if str(e) else ''}") from e
    except NoMedible as e:
        if args.json:
            print(json.dumps({"veredicto": "no_medido", "porque": str(e)}, ensure_ascii=False))
        else:
            print(f"NO MEDIDO: {e}", file=sys.stderr)
        return EXIT_NO_MEDIDO
    if args.json:
        print(_a_json(res))
    else:
        imprimir(res)
    return {"ok": EXIT_OK, "fallo": EXIT_FALLO, "no_medido": EXIT_NO_MEDIDO}[res.veredicto]


if __name__ == "__main__":
    sys.exit(main())
