#!/usr/bin/env python3
"""gate_datos_reales.py — el candado de datos reales: ¿tiene una PERSONA derecho a abrirlo?

Cosechado de `accounting_AMC` (`.claude/scripts/gate_datos_reales.py` + `backend/core/seguridad/
candado.py` + el paso de su CI que demuestra que bloquea; invariante 2, «sin DPA firmado no se tocan
datos reales de AMC»), generalizado en la sub-ola 2.29 de la revisión integral (SE-49) para todo
proyecto que trate datos de TERCEROS: los de un cliente (la gestoría de AMC) o de sus pacientes
(EvoPreven). El patrón entero: `.claude/patterns/stack/backend-candado-datos-reales.md`; las piezas
que se copian al proyecto: `.claude/templates/candado-datos-reales/`.

QUÉ COMPRUEBA

  Siempre, el ESTADO (`.claude/estado-datos-reales.json`; acepta el `estado-dpa.json` de AMC): cada
  condición cerrada con `ok: true` Y quién la cerró —una persona, no un agente—, cuándo —una fecha
  que existe y no es futura— y con qué evidencia —una ruta del repo que existe o un enlace—. Un
  `ok: true` sin eso es un fichero editado a mano, no un permiso. Un estado sin condiciones no es
  verde. Y si la variable que abre el candado está a 1 con el estado en rojo, lo dice aparte.

  Con `--completo`, además, que el estado está PROTEGIDO —un `Edit(<ruta>)` (o `Read`) en el `deny`
  de `.claude/settings.json`; un `Write(...)` no se consulta nunca— y que el candado está CABLEADO:
  hay un `comprobar_candado()` en el código y alguien lo llama desde un `ready()`.

  Con `--demostrar` (y el python del proyecto), lo que en AMC hace su CI en cada PR: arranca
  `manage.py check` con una integración en `real` y la variable a 0, y tiene que NEGARSE; y con todo
  en mock, tiene que arrancar (si no arranca ni así, no se pudo medir). Es lo único que caza un
  candado cuya app no está en INSTALLED_APPS: su `ready()` no corre nunca y lo estático no lo ve.

QUÉ NO COMPRUEBA: que el contrato diga lo que tiene que decir (eso lo valida un DPD o un abogado);
que la evidencia sea la que dice ser (que exista, sí); las puertas por las que entran datos A MANO
(una subida de ficheros): ahí el candado no bloquea, avisa (`hay_datos_reales()`); y que el `deny`
se aplique —sin confianza del workspace, o con un script que abre el fichero por su cuenta, no se
aplica (`rules/security.md` §Un deny no se aplica siempre)—.

USO
    python3 .claude/scripts/gate_datos_reales.py [<proyecto>] [--json]
    python3 .claude/scripts/gate_datos_reales.py <proyecto> --completo
    python3 .claude/scripts/gate_datos_reales.py <proyecto> --demostrar --python <py> [--modo CRM_MODE]
    python3 .claude/scripts/gate_datos_reales.py --autoprueba [--python <py con Django>]

Sin <proyecto>, el repo donde está instalado el script (el de AMC lo usaba así desde su hook de
SessionStart). La variable que abre el candado sale del campo `variable` del estado, o de
`--variable`; la integración para `--demostrar`, de `--modo` o de `MODOS` en el candado.py.

SALIDA: 0 se puede (y con --completo, además protegido y cableado) · 1 no se puede, o falta una
defensa · 2 no se pudo medir (estado ilegible, proyecto que no arranca ni en mock). El 2 es
deliberado (`rules/verification.md` §El instrumento que no puede medir debe ABORTAR).

Nunca escribe: el estado lo pone una persona, con su evidencia. `--autoprueba` monta sus casos en
una carpeta temporal y la borra.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

EXIT_OK, EXIT_FALLO, EXIT_NO_MEDIDO = 0, 1, 2
ESTADOS = (Path(".claude") / "estado-datos-reales.json", Path(".claude") / "estado-dpa.json")
VARIABLE_POR_DEFECTO = "DATOS_REALES"
PODA = {".git", ".venv", "venv", "env", "node_modules", "site-packages", "__pycache__",
        "migrations", ".claude", ".docs", "dist", "build", "_archive"}
TIEMPO = 180
AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI.parent / "templates" / "candado-datos-reales"

sys.path.insert(0, str(AQUI))
try:                                   # la misma vara que la firma de los documentos de arranque
    from gate_arranque import _firma_vacia, es_agente  # noqa: E402
    FIRMA_COMPLETA = True
except ImportError:                    # pragma: no cover — un proyecto con un gate_arranque viejo
    FIRMA_COMPLETA = False
    _RX_AGENTE = re.compile(r"\b(agente|claude|tech lead|ia|bot|asistente|modelo|sesi[oó]n)\b", re.I)

    def es_agente(firmante: str) -> bool:
        return bool(_RX_AGENTE.search(firmante))

    def _firma_vacia(s: str) -> bool:
        return not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9]", s or "")


class NoMedible(Exception):
    """El gate no puede llegar al sujeto. Sale con 2, nunca con 0."""


# ── el estado ────────────────────────────────────────────────────────────────────────────


def buscar_estado(raiz: Path, declarado: str | None) -> Path | None:
    if declarado:
        return raiz / declarado
    for rel in ESTADOS:
        if (raiz / rel).exists():
            return raiz / rel
    return None


def _fecha(v) -> tuple[date | None, str]:
    s = str(v or "").strip()
    if not s:
        return None, "sin fecha"
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date(), ""
    except ValueError:
        return None, f"«{s[:20]}» no es una fecha que exista (YYYY-MM-DD)"


def _evidencia(raiz: Path, v) -> tuple[str | None, str]:
    """(id del hallazgo o None, detalle)."""
    s = str(v or "").strip()
    if not s:
        return "CANDADO-VERDE-SIN-FIRMA", "sin evidencia"
    if re.match(r"^[a-z][a-z0-9+.-]*://\S+$", s, re.I):
        return None, f"enlace {s[:60]}"
    if " " not in s and (s.startswith("/") or ".." in Path(s).parts):
        return "CANDADO-EVIDENCIA-NO-EXISTE", f"la evidencia {s} no es una ruta DEL REPO (relativa, sin «..»)"
    if " " not in s and ("/" in s or re.search(r"\.\w{2,5}$", s)):
        return (None, f"fichero {s}") if (raiz / s).exists() else \
               ("CANDADO-EVIDENCIA-NO-EXISTE", f"la evidencia {s} no existe en el repo")
    return "CANDADO-EVIDENCIA-NO-VERIFICABLE", (f"«{s[:40]}» no es una ruta del repo ni un enlace: "
                                                 "nadie puede abrirla para comprobarla")


def evaluar_estado(raiz: Path, ruta: Path | None, hoy: date | None = None) -> tuple[list, dict]:
    """(hallazgos, datos). Un hallazgo es (id, lugar, qué)."""
    hoy = hoy or date.today()
    if ruta is None or not ruta.exists():
        return [("CANDADO-SIN-ESTADO", str(ESTADOS[0]),
                 "no existe el estado: sin él no se puede afirmar que haya permiso para tocar datos "
                 "reales (plantilla: templates/candado-datos-reales/estado-datos-reales.json)")], {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise NoMedible(f"el estado {ruta} no se puede leer: {e}") from e
    if not isinstance(datos, dict) or not isinstance(datos.get("condiciones", {}), dict):
        raise NoMedible(f"el estado {ruta} no tiene la forma esperada ({{\"condiciones\": {{…}}}})")
    conds = datos.get("condiciones") or {}
    hall = []
    if not conds:
        hall.append(("CANDADO-SIN-CONDICIONES", ruta.name,
                     "el estado no declara ninguna condición: un permiso sin condiciones no es "
                     "un verde, es un estado sin rellenar"))
    for nombre, c in conds.items():
        lugar = f"condición {nombre}"
        if not isinstance(c, dict):
            hall.append(("CANDADO-CONDICION-PENDIENTE", lugar, "mal formada (no es un objeto)"))
            continue
        if c.get("ok") is not True:
            hall.append(("CANDADO-CONDICION-PENDIENTE", lugar,
                         f"pendiente{' · ' + c['que'] if c.get('que') else ''}"))
            continue
        quien = str(c.get("quien") or "").strip()
        if _firma_vacia(quien):
            hall.append(("CANDADO-VERDE-SIN-FIRMA", lugar, "ok: true sin quién la cerró"))
        elif es_agente(quien):
            hall.append(("CANDADO-FIRMA-DE-AGENTE", lugar,
                         f"la cierra «{quien[:40]}», que es un agente: el permiso lo da una persona"))
        f, error = _fecha(c.get("fecha"))
        if f is None:
            hall.append(("CANDADO-VERDE-SIN-FIRMA" if error == "sin fecha" else
                         "CANDADO-FECHA-INVALIDA", lugar, f"ok: true {error}"))
        elif f > hoy:
            hall.append(("CANDADO-FECHA-FUTURA", lugar, f"cerrada con fecha futura ({f})"))
        id_ev, det = _evidencia(raiz, c.get("evidencia"))
        if id_ev:
            hall.append((id_ev, lugar, f"ok: true pero {det}"))
    return hall, datos


# ── protección del estado y cableado del candado ─────────────────────────────────────────


def _cubre(regla: str, rel: str) -> bool:
    m = re.fullmatch(r"(Edit|Read)\((.+)\)", regla.strip())
    if not m:
        return False
    patron = m.group(2).strip()
    for prefijo in ("./", "/"):
        if patron.startswith(prefijo) and not patron.startswith("//"):
            patron = patron[len(prefijo):]
    return fnmatch.fnmatch(rel, patron) or fnmatch.fnmatch(rel, patron.replace("**/", ""))


def comprobar_proteccion(raiz: Path, estado: Path) -> list:
    rel = estado.relative_to(raiz).as_posix()
    reglas, solo_write = [], False
    for nombre in ("settings.json", "settings.local.json"):
        p = raiz / ".claude" / nombre
        if not p.exists():
            continue
        try:
            deny = (json.loads(p.read_text(encoding="utf-8")).get("permissions") or {}).get("deny") or []
        except ValueError:
            continue
        reglas += [str(r) for r in deny]
    if any(_cubre(r, rel) for r in reglas):
        return []
    solo_write = any(re.fullmatch(rf"Write\(\.?/?{re.escape(rel)}\)", r.strip()) for r in reglas)
    extra = (" (hay un Write(), y esas reglas no se consultan nunca: solo Edit y Read)"
             if solo_write else "")
    return [("CANDADO-ESTADO-SIN-PROTEGER", ".claude/settings.json",
             f"ningún deny cubre {rel}{extra}: cualquier agente puede ponerlo en verde. "
             f"Añade \"Edit({rel})\" al deny (y un hook PreToolUse si de verdad importa: "
             "rules/security.md §Un deny no se aplica siempre)")]


def _ficheros(raiz: Path):
    for p in sorted(raiz.rglob("*.py")):
        if any(parte in PODA for parte in p.relative_to(raiz).parts[:-1]):
            continue
        rel = p.relative_to(raiz)
        if any(x in ("tests", "test") for x in rel.parts[:-1]) or rel.name.startswith("test_"):
            continue
        yield p


def comprobar_cableado(raiz: Path) -> tuple[list, Path | None]:
    definido, llamado = None, []
    for p in _ficheros(raiz):
        try:
            arbol = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(arbol):
            if isinstance(n, ast.FunctionDef) and n.name == "comprobar_candado" and definido is None:
                definido = p
            if isinstance(n, ast.FunctionDef) and n.name == "ready":
                for c in ast.walk(n):
                    if isinstance(c, ast.Call) and (
                            getattr(c.func, "id", None) == "comprobar_candado"
                            or getattr(c.func, "attr", None) == "comprobar_candado"):
                        llamado.append(p.relative_to(raiz).as_posix())
    if definido is None:
        return [("CANDADO-AUSENTE", "código",
                 "no hay candado en el código (ninguna función comprobar_candado): el estado dice "
                 "quién puede, pero nada impide arrancar con datos reales. Copia "
                 "templates/candado-datos-reales/candado.py")], None
    if not llamado:
        return [("CANDADO-SIN-CABLEAR", definido.relative_to(raiz).as_posix(),
                 "el candado existe y ningún ready() lo llama: no se ejecuta nunca. Llámalo desde "
                 "el ready() de una app que esté en INSTALLED_APPS")], definido
    return [], definido


def _modos_del_candado(candado: Path | None) -> list[str]:
    if candado is None:
        return []
    try:
        arbol = ast.parse(candado.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    for n in arbol.body:
        destino = n.target if isinstance(n, ast.AnnAssign) else (
            n.targets[0] if isinstance(n, ast.Assign) and len(n.targets) == 1 else None)
        if isinstance(destino, ast.Name) and destino.id == "MODOS" and n.value is not None:
            try:
                return [str(x) for x in ast.literal_eval(n.value)]
            except ValueError:
                return []
    return []


def _manage(raiz: Path) -> Path:
    for cand in (raiz / "manage.py", raiz / "backend" / "manage.py"):
        if cand.is_file():
            return cand
    raise NoMedible(f"--demostrar necesita manage.py en {raiz} o en {raiz}/backend")


def demostrar(raiz: Path, python: str, variable: str, modo: str, settings: str | None) -> list:
    manage = _manage(raiz)
    base = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if settings:
        base["DJANGO_SETTINGS_MODULE"] = settings

    def correr(extra: dict):
        env = dict(base, **extra)
        try:
            return subprocess.run([python, str(manage), "check"], cwd=manage.parent, env=env,
                                  capture_output=True, text=True, timeout=TIEMPO)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise NoMedible(f"--demostrar no pudo lanzar manage.py: {e}") from e

    control = correr({variable: "0", modo: "mock"})
    if control.returncode != 0:
        cola = " ".join((control.stdout + control.stderr).strip().splitlines()[-3:])[:300]
        raise NoMedible("el proyecto no arranca ni con todo en mock: no se puede ver si el candado "
                        f"bloquea ({cola})")
    real = correr({variable: "0", modo: "real"})
    salida = real.stdout + real.stderr
    if real.returncode != 0 and (variable in salida or "gate_datos_reales" in salida):
        return []
    return [("CANDADO-NO-BLOQUEA", f"manage.py check con {modo}=real y {variable}=0",
             "arrancó (o falló por otra cosa): el candado no está en el camino de arranque. ¿La app "
             "que lo llama en ready() está en INSTALLED_APPS?")]


# ── medir ────────────────────────────────────────────────────────────────────────────────


def medir(raiz: Path, completo=False, demostrar_con: str | None = None, modo: str | None = None,
          estado: str | None = None, variable: str | None = None, settings: str | None = None,
          hoy: date | None = None, entorno: dict | None = None) -> dict:
    raiz = raiz.resolve()
    env = os.environ if entorno is None else entorno
    ruta = buscar_estado(raiz, estado)
    hall, datos = evaluar_estado(raiz, ruta, hoy)
    var = variable or datos.get("variable") or VARIABLE_POR_DEFECTO
    pendientes = sorted({h[1].removeprefix("condición ") for h in hall
                         if h[1].startswith("condición ")} | ({"(estado)"} if any(
                             h[0] in ("CANDADO-SIN-ESTADO", "CANDADO-SIN-CONDICIONES") for h in hall)
                             else set()))
    if hall and env.get(var, "0") == "1":
        hall.append(("CANDADO-VARIABLE-ABIERTA-EN-ROJO", f"entorno: {var}=1",
                     f"{var}=1 con el estado en rojo: alguien abrió el candado sin permiso. Ponla a 0"))
    puede = not hall
    candado = None
    if completo or demostrar_con:
        if ruta is not None and ruta.exists():
            hall += comprobar_proteccion(raiz, ruta)
        cab, candado = comprobar_cableado(raiz)
        hall += cab
    if demostrar_con:
        modos = [modo] if modo else _modos_del_candado(candado)
        if not modos:
            raise NoMedible("--demostrar necesita saber qué variable pone una integración en real: "
                            "--modo <VARIABLE> (o MODOS en el candado.py)")
        hall += demostrar(raiz, demostrar_con, var, modos[0], settings)
    return dict(proyecto=str(raiz), estado=str(ruta) if ruta else None, variable=var,
                valor_variable=env.get(var, "0"), puede_tocar_datos_reales=puede,
                pendientes=pendientes, completo=bool(completo or demostrar_con),
                demostrado=bool(demostrar_con), firma_completa=FIRMA_COMPLETA,
                hallazgos=[dict(id=i, lugar=lugar, que=q) for i, lugar, q in hall])


def imprimir(res: dict) -> None:
    print(f"── Candado de datos reales · {res['proyecto']}")
    print(f"   estado: {res['estado'] or 'NO EXISTE'} · variable {res['variable']}="
          f"{res['valor_variable']}{' · completo' if res['completo'] else ''}"
          f"{' · demostrado con manage.py check' if res['demostrado'] else ''}")
    if not res["firma_completa"]:
        print("   (firma de agente: comprobación mínima — este gate_arranque.py no trae es_agente)")
    for h in res["hallazgos"]:
        print(f"  ✗ {h['id']}  {h['lugar']}\n      {h['que']}")
    if res["hallazgos"]:
        print(f"\n⛔ BLOQUEADO — {len(res['hallazgos'])} hallazgo(s). Se trabaja con fixtures/ y mocks/ "
              "(patterns/stack/backend-candado-datos-reales.md).")
    else:
        print("\n✓ Vía libre. Aun así: solo el alcance acordado, y el contenido de lo firmado lo valida "
              "un DPD o un abogado, no este gate.")


# ── autoprueba ───────────────────────────────────────────────────────────────────────────

FIRMA = {"quien": "Ana Ruiz (DPD del cliente)", "fecha": "2026-01-15",
         "evidencia": "docs/cumplimiento/encargo.pdf"}
APPS_PY = '''from django.apps import AppConfig


class NucleoConfig(AppConfig):
    name = "nucleo"

    def ready(self):
        from nucleo.candado import comprobar_candado
        comprobar_candado()
'''
SETTINGS_PY = '''SECRET_KEY = "solo-para-la-autoprueba-del-candado-de-datos-reales"
DEBUG = False
ALLOWED_HOSTS = ["x.test"]
INSTALLED_APPS = ["django.contrib.contenttypes", "nucleo"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
'''
MANAGE_PY = '''#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
'''


def _montar(dst: Path, condiciones=None, deny=None, cableado=True, estado_rel=ESTADOS[0]) -> None:
    (dst / ".claude").mkdir(parents=True)
    (dst / "docs" / "cumplimiento").mkdir(parents=True)
    (dst / "docs" / "cumplimiento" / "encargo.pdf").write_text("%PDF-1.4 de juguete\n")
    conds = condiciones if condiciones is not None else {
        k: dict(ok=True, **FIRMA) for k in ("encargo_firmado", "subencargados_declarados")}
    (dst / estado_rel).write_text(json.dumps({"variable": "DATOS_REALES", "condiciones": conds}),
                                  encoding="utf-8")
    reglas = deny if deny is not None else [f"Edit({estado_rel.as_posix()})"]
    (dst / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": reglas}}),
                                                   encoding="utf-8")
    (dst / "config").mkdir()
    (dst / "config" / "__init__.py").write_text("")
    (dst / "config" / "settings.py").write_text(SETTINGS_PY)
    (dst / "manage.py").write_text(MANAGE_PY)
    (dst / "nucleo").mkdir()
    (dst / "nucleo" / "__init__.py").write_text("")
    txt = (PLANTILLA / "candado.py").read_text(encoding="utf-8")
    txt = txt.replace('NIVELES_HASTA_LA_RAIZ = 3', 'NIVELES_HASTA_LA_RAIZ = 1')
    (dst / "nucleo" / "candado.py").write_text(txt, encoding="utf-8")
    apps = APPS_PY if cableado else APPS_PY.replace("        comprobar_candado()\n", "        pass\n")
    (dst / "nucleo" / "apps.py").write_text(apps, encoding="utf-8")


def _cond(**cambios):
    c = dict(ok=True, **FIRMA)
    c.update(cambios)
    return {"encargo_firmado": c}


# (nombre, montaje, opciones de medir, esperados, exit)
CASOS = [
    ("limpio (completo)", {}, dict(completo=True), set(), 0),
    ("una condición pendiente", dict(condiciones=_cond(ok=False)), dict(completo=True),
     {"CANDADO-CONDICION-PENDIENTE"}, 1),
    ("ok: true sin evidencia", dict(condiciones=_cond(evidencia="")), dict(completo=True),
     {"CANDADO-VERDE-SIN-FIRMA"}, 1),
    ("ok: true sin quién", dict(condiciones=_cond(quien="")), dict(completo=True),
     {"CANDADO-VERDE-SIN-FIRMA"}, 1),
    ("la cierra un agente", dict(condiciones=_cond(quien="Tech Lead (agente)")),
     dict(completo=True), {"CANDADO-FIRMA-DE-AGENTE"}, 1),
    ("fecha futura", dict(condiciones=_cond(fecha="2099-01-01")), dict(completo=True),
     {"CANDADO-FECHA-FUTURA"}, 1),
    ("fecha imposible", dict(condiciones=_cond(fecha="2026-13-45")), dict(completo=True),
     {"CANDADO-FECHA-INVALIDA"}, 1),
    ("evidencia que no existe", dict(condiciones=_cond(evidencia="docs/no-esta.pdf")),
     dict(completo=True), {"CANDADO-EVIDENCIA-NO-EXISTE"}, 1),
    ("evidencia fuera del repo", dict(condiciones=_cond(evidencia="/etc/hostname")),
     dict(completo=True), {"CANDADO-EVIDENCIA-NO-EXISTE"}, 1),
    ("evidencia de palabra", dict(condiciones=_cond(evidencia="firmado por correo")),
     dict(completo=True), {"CANDADO-EVIDENCIA-NO-VERIFICABLE"}, 1),
    ("estado sin condiciones", dict(condiciones={}), dict(completo=True),
     {"CANDADO-SIN-CONDICIONES"}, 1),
    ("sin estado", dict(condiciones="@@SIN@@"), dict(completo=True), {"CANDADO-SIN-ESTADO"}, 1),
    ("estado sin proteger", dict(deny=[]), dict(completo=True), {"CANDADO-ESTADO-SIN-PROTEGER"}, 1),
    ("protegido solo con Write()", dict(deny=["Write(.claude/estado-datos-reales.json)"]),
     dict(completo=True), {"CANDADO-ESTADO-SIN-PROTEGER"}, 1),
    ("candado sin cablear", dict(cableado=False), dict(completo=True), {"CANDADO-SIN-CABLEAR"}, 1),
    ("sin candado en el código", dict(cableado="@@SIN@@"), dict(completo=True),
     {"CANDADO-AUSENTE"}, 1),
    ("variable abierta con el estado en rojo", dict(condiciones=_cond(ok=False)),
     dict(completo=True, entorno={"DATOS_REALES": "1"}),
     {"CANDADO-CONDICION-PENDIENTE", "CANDADO-VARIABLE-ABIERTA-EN-ROJO"}, 1),
    # controles
    ("control · evidencia como enlace", dict(condiciones=_cond(evidencia="https://firma.ejemplo/doc/1")),
     dict(completo=True), set(), 0),
    ("control · protegido con un glob", dict(deny=["Edit(.claude/estado-*.json)"]),
     dict(completo=True), set(), 0),
    ("control · protegido con Read() (también bloquea Edit)",
     dict(deny=["Read(./.claude/estado-datos-reales.json)"]), dict(completo=True), set(), 0),
    ("control · sin --completo solo mira el estado", dict(cableado="@@SIN@@", deny=[]), {}, set(), 0),
    ("control · el estado-dpa.json de AMC", dict(estado_rel=ESTADOS[1]), dict(completo=True),
     set(), 0),
    ("control · firma de persona que nombra al agente",
     dict(condiciones=_cond(quien="Ana Ruiz, revisado con el agente de cumplimiento")),
     dict(completo=True), set(), 0),
    # no medido
    ("no medido · estado ilegible", dict(condiciones="@@ROTO@@"), dict(completo=True), set(), 2),
]


def _caso(tmp: Path, i: int, montaje: dict) -> Path:
    dst = tmp / f"caso{i:02d}"
    m = dict(montaje)
    sin_estado = m.get("condiciones") == "@@SIN@@"
    roto = m.get("condiciones") == "@@ROTO@@"
    sin_candado = m.get("cableado") == "@@SIN@@"
    if sin_estado or roto:
        m.pop("condiciones")
    if sin_candado:
        m["cableado"] = True
    _montar(dst, **m)
    rel = m.get("estado_rel", ESTADOS[0])
    if sin_estado:
        (dst / rel).unlink()
    if roto:
        (dst / rel).write_text('{"condiciones": {"encargo_firmado": {"ok": tr', encoding="utf-8")
    if sin_candado:
        (dst / "nucleo" / "candado.py").unlink()
        (dst / "nucleo" / "apps.py").write_text(APPS_PY.replace(
            "        from nucleo.candado import comprobar_candado\n        comprobar_candado()\n",
            "        pass\n"), encoding="utf-8")
    return dst


def _candado_puro(tmp: Path) -> list:
    """Las reglas del candado.py de la plantilla, sin Django: (nombre, ok, detalle)."""
    spec = importlib.util.spec_from_file_location("candado_plantilla", PLANTILLA / "candado.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    verde, roja, sin_firma, vacia = (tmp / n for n in ("verde", "roja", "sinfirma", "vacia"))
    for d, conds in ((verde, _cond()), (roja, _cond(ok=False)), (sin_firma, {"e": {"ok": True}})):
        (d / ".claude").mkdir(parents=True)
        (d / ".claude" / "estado-datos-reales.json").write_text(json.dumps({"condiciones": conds}))
    vacia.mkdir()
    kw = dict(modos=("CRM_MODE",))
    filas = []

    def debe(nombre, lanza, env, raiz, **extra):
        try:
            mod.comprobar_candado(env, raiz=raiz, **kw, **extra)
            ok, det = not lanza, "no lanza"
        except mod.CandadoCerrado as e:
            ok, det = lanza, str(e).splitlines()[0][:90]
        filas.append((f"candado · {nombre}", ok, det))

    debe("modo real con la variable a 0 → se niega", True, {"CRM_MODE": "real"}, vacia)
    debe("variable a 1 con el estado en rojo → se niega", True, {"DATOS_REALES": "1"}, roja)
    debe("variable a 1 con un verde sin firma → se niega", True, {"DATOS_REALES": "1"}, sin_firma)
    debe("requisito ausente con datos reales → se niega", True, {"DATOS_REALES": "1"}, verde,
         requisitos=("CLAVE_PROPIA",))
    debe("control · todo en mock → arranca", False, {"CRM_MODE": "mock"}, vacia)
    debe("control · variable a 1 con el estado en verde → arranca", False,
         {"DATOS_REALES": "1", "CRM_MODE": "real"}, verde)
    debe("control · sin estado (producción) con la variable a 1 → arranca", False,
         {"DATOS_REALES": "1"}, vacia)
    rota = tmp / "rota"
    (rota / ".claude").mkdir(parents=True)
    (rota / ".claude" / "estado-datos-reales.json").write_text('{"condiciones": {"e": {"ok": tr')
    debe("estado a medias con la variable a 1 → se niega (no es producción)", True,
         {"DATOS_REALES": "1", "CRM_MODE": "real"}, rota)
    filas.append(("candado · hay_datos_reales() lee la variable",
                  mod.hay_datos_reales({"DATOS_REALES": "1"}) and not mod.hay_datos_reales({}),
                  "True con 1, False sin ella"))
    return filas


def autoprueba(python: str | None, como_json: bool) -> int:
    filas = []
    hoy = date(2026, 10, 21)          # fijo: «fecha futura» no puede depender del día que se corre
    with tempfile.TemporaryDirectory(prefix="candado-autoprueba-") as tmp:
        tmp = Path(tmp)
        for i, (nombre, montaje, opciones, esperados, exit_esperado) in enumerate(CASOS):
            dst = _caso(tmp, i, montaje)
            opciones = dict(opciones)
            entorno = opciones.pop("entorno", {})
            try:
                res = medir(dst, hoy=hoy, entorno=entorno, **opciones)
                obtenido = {h["id"] for h in res["hallazgos"]}
                exit_obtenido = EXIT_FALLO if obtenido else EXIT_OK
                det = "; ".join(f"{h['id']} ({h['lugar']})" for h in res["hallazgos"])
            except NoMedible as e:
                obtenido, exit_obtenido, det = set(), EXIT_NO_MEDIDO, str(e)[:120]
            filas.append((nombre, exit_obtenido == exit_esperado and obtenido == esperados,
                          f"exit {exit_obtenido} · {det or '—'}"))
        filas += _candado_puro(tmp / "puro")
        if python:
            chequeo = subprocess.run([python, "-c", "import django"], capture_output=True)
            if chequeo.returncode != 0:
                raise NoMedible(f"--python {python} no tiene Django: --demostrar no se puede probar")
            for nombre, montaje, esperados, exit_esperado in (
                    ("demostrar · cableado: manage.py check se niega", {}, set(), 0),
                    ("demostrar · su app fuera de INSTALLED_APPS: lo estático no lo ve",
                     {"fuera": True}, {"CANDADO-NO-BLOQUEA"}, 1),
                    ("demostrar · el proyecto no arranca ni en mock", {"roto": True}, set(), 2)):
                dst = tmp / f"dem-{len(filas)}"
                _montar(dst)
                if montaje.get("fuera"):
                    st = dst / "config" / "settings.py"
                    st.write_text(st.read_text().replace(', "nucleo"]', "]"))
                if montaje.get("roto"):
                    st = dst / "config" / "settings.py"
                    st.write_text(st.read_text() + "import modulo_que_no_existe\n")
                try:
                    res = medir(dst, demostrar_con=python, hoy=hoy, entorno={})
                    obtenido = {h["id"] for h in res["hallazgos"]}
                    exit_obtenido = EXIT_FALLO if obtenido else EXIT_OK
                except NoMedible as e:
                    obtenido, exit_obtenido = set(), EXIT_NO_MEDIDO
                filas.append((nombre, exit_obtenido == exit_esperado and obtenido == esperados,
                              f"exit {exit_obtenido} · {', '.join(sorted(obtenido)) or '—'}"))
        else:
            filas.append(("demostrar · (sin --python con Django: no probado)", True, "saltado"))
    bien = sum(ok for _, ok, _ in filas)
    if como_json:
        print(json.dumps({"autoprueba": [dict(caso=n, ok=ok, detalle=d) for n, ok, d in filas],
                          "bien": bien, "total": len(filas)}, ensure_ascii=False, indent=1))
    else:
        print("Candado de datos reales · autoprueba de gate_datos_reales.py y del candado.py de la "
              "plantilla\n  (cada sabotaje cae por SU hallazgo, ni uno más; los controles no caen)\n")
        for n, ok, d in filas:
            print(f"  {'✓' if ok else '✗'} {n}" + ("" if ok else f"\n      {d}"))
        print(f"\n═══ {bien}/{len(filas)} casos como se esperaba")
    return EXIT_OK if bien == len(filas) else EXIT_FALLO


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="El candado de datos reales (ver la cabecera)")
    ap.add_argument("proyecto", nargs="?")
    ap.add_argument("--completo", action="store_true",
                    help="además: el estado protegido por el deny y el candado cableado")
    ap.add_argument("--demostrar", action="store_true",
                    help="además: manage.py check con una integración en real tiene que negarse")
    ap.add_argument("--python", help="el python del proyecto (para --demostrar y --autoprueba)")
    ap.add_argument("--modo", help="la variable que pone una integración en real (CRM_MODE…)")
    ap.add_argument("--settings", help="DJANGO_SETTINGS_MODULE para --demostrar")
    ap.add_argument("--estado", help="ruta del estado, relativa al proyecto")
    ap.add_argument("--variable", help="la variable que abre el candado (si el estado no la dice)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--autoprueba", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.autoprueba:
            return autoprueba(a.python, a.json)
        if a.demostrar and not a.python:
            raise NoMedible("--demostrar necesita --python <el python del proyecto, con Django>")
        raiz = Path(a.proyecto) if a.proyecto else AQUI.parents[1]
        res = medir(raiz, completo=a.completo, demostrar_con=a.python if a.demostrar else None,
                    modo=a.modo, estado=a.estado, variable=a.variable, settings=a.settings)
    except NoMedible as e:
        if a.json:
            print(json.dumps({"no_medido": str(e)}, ensure_ascii=False))
        else:
            print(f"✗ NO MEDIDO: {e}", file=sys.stderr)
        return EXIT_NO_MEDIDO
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        imprimir(res)
    return EXIT_FALLO if res["hallazgos"] else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
