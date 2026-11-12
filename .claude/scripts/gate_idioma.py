#!/usr/bin/env python3
"""Gate: el CÓDIGO en inglés; los comentarios, los docstrings y los textos de pantalla, en castellano.

De dónde sale (MO-25, sub-ola 2.18 de la revisión integral, 2026-10-21). Es la petición más enfática
que tiene registrada el Usuario: *«todo lo de código debe estar en inglés. ¿Quién programa funciones
en español? Nadie.»* (06-09-2026) y, tras dos incumplimientos el mismo día con la regla ya en memoria,
*«esto debería estar prohibido, prohibido, prohibido»* (12-09-2026). La memoria sola falló dos veces,
así que la regla de `rules/code-style.md` §Idioma trae este mecanismo. Lo escribió y lo usa
accounting_AMC (`.claude/scripts/gate_idioma.py`, 12-09-2026); aquí va generalizado: el alcance, el
baseline y las palabras propias de AMC salen del código y pasan a argumentos.

## Qué comprueba, y qué NO

Mira los **nombres**: ficheros y carpetas, clases, funciones, argumentos, variables y campos (Python
por AST, TypeScript por la palabra clave de la declaración). Busca palabras castellanas de una lista
CERRADA —no adivina el idioma— y solo en identificadores. **No mira** comentarios, docstrings ni
cadenas: esos van en castellano y así se quedan. Tampoco mira los tests (`.test.`, `test_*.py`,
`tests/`): el nombre de un test es una frase que se lee en la salida de pytest.

## El heredado no se renombra en caliente

Lo que ya está en castellano se congela en `.claude/patterns/baseline/idioma.json` (el formato de
`rules/refactor-progresivo.md` §4.2): el gate lo conoce y no lo reporta. Con `--staged`, en un
fichero congelado se juzgan **solo las líneas que el commit añade o cambia** (boy-scout, §4.3).

    python3 .claude/scripts/gate_idioma.py                       # el alcance entero (informe)
    python3 .claude/scripts/gate_idioma.py --staged              # solo lo que va a entrar (pre-commit)
    python3 .claude/scripts/gate_idioma.py --dentro backend/,frontend/src/
    python3 .claude/scripts/gate_idioma.py --congelar            # crear el baseline (una persona, a mano)
    python3 .claude/scripts/gate_idioma.py --self-test           # se ve fallar con nombres plantados

Salida: 0 todo en inglés · 1 hay nombres nuevos en castellano · 2 no se pudo medir (no hay código en
el alcance, o el baseline no se lee). Un alcance vacío NO es «todo en inglés»: es un instrumento que
no llega al sujeto (`rules/verification.md` §El instrumento que no puede medir).

⚠️ Lo que este gate no evita: arreglar un nombre con un `sed` global, que se lleva por delante la prosa
de los comentarios. En un fichero con prosa se cambian LÍNEAS EXACTAS (lección de AMC, 12-09-2026).
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from datetime import date

BASELINE_REL = ".claude/patterns/baseline/idioma.json"

#: Alcance por defecto: el PRODUCTO, nunca el harness. Se usan las que existan. Con el repo entero, AMC
#: midió 25.612 hallazgos, casi todos en `.claude/scripts/`: la regla de inversión avisando de que el
#: alcance estaba mal, no el código (`rules/refactor-progresivo.md` §4.4).
DENTRO_POR_DEFECTO = ("backend/", "frontend/src/", "apps/", "src/")
FUERA = ("node_modules", "__pycache__", ".venv", "venv/", "migrations", "_archive", "dist/",
         "build/", "fixtures", ".claude/", "mocks/", "/tests/", "/test/")
EXTENSIONES = (".py", ".ts", ".tsx")

#: Palabras castellanas que aparecen en identificadores. Lista CERRADA a propósito: adivinar el idioma
#: da falsos positivos («data» es inglés, «dato» no; «final» es las dos cosas) y un gate con falsos
#: positivos se deja de leer. Ampliarla es barato. Es la de AMC, entera.
CASTELLANO = {
    # verbos
    "enviar", "obtener", "guardar", "buscar", "crear", "borrar", "actualizar", "leer",
    "escribir", "cargar", "mostrar", "pintar", "calcular", "comprobar", "validar",
    "puntear", "conciliar", "resolver", "confirmar", "decidir", "aprobar", "rechazar",
    "marcar", "limpiar", "generar", "parsear", "normalizar", "sembrar", "explicar",
    "cambiar", "elegir", "abrir", "cerrar", "contar", "sumar", "partir", "mover",
    "reprocesar", "importar", "exportar", "recoger", "avisar", "notificar", "revisar",
    "listar",
    # sustantivos del dominio y de programación
    "fecha", "hora", "importe", "cuenta", "cuentas", "factura", "facturas", "cliente",
    "clientes", "canal", "canales", "envio", "envios", "mensaje", "mensajes", "correo",
    "informe", "informes", "cuadre", "cuadres", "apunte", "apuntes", "movimiento",
    "movimientos", "cobro", "cobros", "pago", "pagos", "banco", "mayor", "extracto",
    "trimestre", "ejercicio", "estado", "estados", "modo", "modos", "resultado",
    "resultados", "detalle", "detalles", "cuerpo", "asunto", "destino", "destinatario",
    "remitente", "clave", "claves", "huella", "referencia", "fichero", "ficheros",
    "carpeta", "carpetas", "ruta", "rutas", "fila", "filas", "columna", "columnas",
    "nombre", "nombres", "usuario", "usuarios", "permiso", "permisos", "error",
    "errores", "aviso", "avisos", "fallo", "fallos", "motivo", "razon", "porque",
    "servicios", "vistas", "contrato", "dominio", "simulador", "tabla", "tablas",
    "pantalla", "pantallas", "boton", "botones", "campo", "campos", "valor", "valores",
    "cantidad", "total", "totales", "saldo", "diferencia", "tolerancia", "tolerancias",
    "plazo", "plazos", "vencimiento", "morosidad", "margen", "gasto", "gastos",
    "ingreso", "ingresos", "adjunto", "adjuntos", "buzon", "traza", "peticion",
    "respuesta", "cabecera", "cabeceras", "consulta", "consultas", "prueba", "pruebas",
    "pedido", "pedidos", "precio", "precios", "producto", "productos",
    # adjetivos y adverbios
    "nuevo", "nueva", "viejo", "vieja", "primero", "primera", "ultimo", "ultima",
    "pendiente", "pendientes", "valido", "valida", "invalido", "invalida", "vacio",
    "vacia", "lleno", "llena", "real", "falso", "falsa", "activo", "activa",
    "siguiente", "anterior", "actual", "todos", "todas", "cada", "algunos",
    # conectores que delatan una frase castellana en un identificador
    "para", "desde", "hasta", "entre", "segun", "sobre", "bajo", "tras", "ante",
    "cuando", "donde", "quien", "cual", "cuanto", "cuantos", "mientras", "aunque",
}

#: Palabras que PARECEN castellanas y no lo son, o siglas y nombres técnicos. Lo propio de cada
#: proyecto (marcas, siglas de su dominio) va en el baseline, clave `permitidas`, no aquí.
PERMITIDAS = {
    "data", "total", "final", "real", "error", "no", "id", "ok", "base", "instance",
    "iva", "irpf", "nif", "cif", "boe", "aeat",
    "django", "celery", "redis", "postgres", "vite", "zod", "csv", "xlsx", "pdf",
    "html", "json", "api", "url", "uuid", "sha", "utf", "iso",
}


def troceado(nombre: str) -> list[str]:
    """`nombre_canonico` → `[nombre, canonico]` · `ExplicarDiferencia` → `[explicar, diferencia]`."""
    trozos = []
    for p in re.split(r"[_\-.]", nombre):
        trozos += [t.lower() for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[a-z]+|\d+", p)]
    return [t for t in trozos if len(t) > 2]


def castellano(nombre: str, permitidas: set[str]) -> list[str]:
    """Las palabras castellanas de un identificador. Vacío si está en inglés."""
    return [t for t in troceado(nombre) if t in CASTELLANO and t not in permitidas]


def nombres_python(texto: str) -> list[tuple[int, str, str]]:
    """Clases, funciones, argumentos y asignaciones. Por AST: un comentario no es un identificador."""
    try:
        arbol = ast.parse(texto)
    except SyntaxError:
        return []
    out = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.ClassDef):
            out.append((n.lineno, "clase", n.name))
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append((n.lineno, "función", n.name))
            for a in [*n.args.args, *n.args.kwonlyargs]:
                if a.arg not in ("self", "cls"):
                    out.append((a.lineno, "argumento", a.arg))
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.append((n.lineno, "campo", n.target.id))
        elif isinstance(n, ast.Assign):
            for d in n.targets:
                if isinstance(d, ast.Name):
                    out.append((n.lineno, "variable", d.id))
    return out


def nombres_ts(texto: str) -> list[tuple[int, str, str]]:
    """Lo declarado en TypeScript. Regex, pero anclada a la palabra clave de la declaración."""
    patrones = [
        (r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", "función"),
        (r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)", "variable"),
        (r"^\s*(?:export\s+)?(?:interface|type|class|enum)\s+([A-Za-z_$][\w$]*)", "tipo"),
    ]
    out = []
    for i, linea in enumerate(texto.split("\n"), 1):
        for patron, que in patrones:
            if m := re.match(patron, linea):
                out.append((i, que, m.group(1)))
    return out


def es_test(rel: str) -> bool:
    nombre = pathlib.PurePosixPath(rel).name
    return ".test." in nombre or ".spec." in nombre or nombre.startswith("test_") or nombre == "conftest.py"


def en_alcance(rel: str, dentro: tuple[str, ...]) -> bool:
    return (rel.endswith(EXTENSIONES) and rel.startswith(dentro) and not es_test(rel)
            and not any(x in "/" + rel for x in FUERA))


def git(raiz: pathlib.Path, *a: str) -> str:
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=raiz).stdout


def lineas_nuevas(raiz: pathlib.Path, rel: str) -> set[int]:
    """Las líneas que el commit AÑADE o CAMBIA en un fichero, leídas del diff preparado."""
    lineas: set[int] = set()
    for l in git(raiz, "diff", "--cached", "--unified=0", "--", rel).split("\n"):
        if m := re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", l):
            desde, cuantas = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
            lineas.update(range(desde, desde + cuantas))
    return lineas


def medir(raiz: pathlib.Path, dentro: tuple[str, ...], staged: bool, viejos: set[str],
          permitidas: set[str]) -> tuple[int, list[tuple[str, int, str, str, list[str]]]]:
    """(ficheros revisados, hallazgos). Un fichero congelado se salta entero, salvo con `--staged`."""
    if staged:
        rels = [l for l in git(raiz, "diff", "--cached", "--name-only", "--diff-filter=ACMR").split("\n") if l]
    else:
        rels = sorted(str(p.relative_to(raiz)) for ext in EXTENSIONES for p in raiz.rglob(f"*{ext}"))
    revisados, hallazgos = 0, []
    for rel in rels:
        if not en_alcance(rel, dentro) or not (raiz / rel).is_file():
            continue
        try:
            texto = (raiz / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        revisados += 1
        congelado = rel in viejos
        if congelado and not staged:
            continue
        if not congelado:          # el nombre del fichero y de sus carpetas cuenta: `vistas.py`, `canales/`
            for parte in pathlib.PurePosixPath(rel).parts:
                if palabras := castellano(pathlib.PurePosixPath(parte).stem, permitidas):
                    hallazgos.append((rel, 0, "ruta", parte, palabras))
                    break
        tocadas = lineas_nuevas(raiz, rel) if congelado else None
        nombres = nombres_python(texto) if rel.endswith(".py") else nombres_ts(texto)
        for linea, que, nombre in nombres:
            if tocadas is not None and linea not in tocadas:
                continue
            if palabras := castellano(nombre, permitidas):
                hallazgos.append((rel, linea, que, nombre, palabras))
    return revisados, hallazgos


def leer_baseline(raiz: pathlib.Path) -> dict:
    f = raiz / BASELINE_REL
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf-8"))


def correr(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="El código en inglés; comentarios y pantalla en castellano.")
    ap.add_argument("--raiz", help="raíz del proyecto (por defecto, la del repo donde vive este script)")
    ap.add_argument("--dentro", help="alcance: carpetas separadas por comas (por defecto: "
                    + ", ".join(DENTRO_POR_DEFECTO) + ", las que existan, o las del baseline)")
    ap.add_argument("--staged", action="store_true", help="solo lo que va a entrar en el commit")
    ap.add_argument("--congelar", action="store_true", help="crea el baseline con lo que hay hoy")
    ap.add_argument("--reemplazar", action="store_true", help="con --congelar, rehace un baseline que ya existe")
    ap.add_argument("--self-test", action="store_true", help="se ve fallar con nombres plantados")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    raiz = pathlib.Path(a.raiz).resolve() if a.raiz else pathlib.Path(__file__).resolve().parents[2]
    try:
        base = leer_baseline(raiz)
    except (OSError, json.JSONDecodeError) as e:
        print(f"✗ no se puede leer {BASELINE_REL}: {e}")
        return 2
    if a.dentro:
        dentro = tuple(d.strip().rstrip("/") + "/" for d in a.dentro.split(",") if d.strip())
    elif base.get("dentro"):
        dentro = tuple(d.rstrip("/") + "/" for d in base["dentro"])
    else:
        dentro = tuple(d for d in DENTRO_POR_DEFECTO if (raiz / d).is_dir())
    if not dentro:
        print("✗ no hay código que medir: ninguna de " + ", ".join(DENTRO_POR_DEFECTO)
              + f" existe en {raiz}. Pasa --dentro <carpetas>; un alcance vacío no es «todo en inglés».")
        return 2
    permitidas = PERMITIDAS | {p.lower() for p in base.get("permitidas", [])}

    if a.congelar:
        destino = raiz / BASELINE_REL
        if destino.exists() and not a.reemplazar:
            print(f"✗ {BASELINE_REL} ya existe: congelar otra vez lo haría crecer en silencio "
                  "(el trinquete al revés). Si de verdad hay que rehacerlo, --reemplazar.")
            return 1
        revisados, hallazgos = medir(raiz, dentro, False, set(), permitidas)
        if not revisados:
            print(f"✗ el alcance ({', '.join(dentro)}) no tiene ficheros .py/.ts/.tsx: nada que congelar")
            return 2
        ficheros = sorted({h[0] for h in hallazgos})
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps({
            "patron_id": "codigo-en-ingles",
            "frozen_at": date.today().isoformat(),
            "nota": "Deuda aceptada (ratchet): lo heredado en castellano no se renombra en caliente. "
                    "Solo una persona amplía esta lista; lo nuevo se juzga con --staged.",
            "dentro": [d.rstrip("/") for d in dentro],
            "permitidas": sorted(base.get("permitidas", [])),
            "violations": ficheros,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✓ baseline congelado: {len(ficheros)} fichero(s) heredados de {revisados} en {BASELINE_REL}")
        return 0

    viejos = set(base.get("violations", []))
    revisados, hallazgos = medir(raiz, dentro, a.staged, viejos, permitidas)
    if not revisados and not a.staged:
        print(f"✗ el alcance ({', '.join(dentro)}) no tiene ficheros .py/.ts/.tsx: no se pudo medir")
        return 2
    if not revisados:              # --staged sin nada del alcance en el commit: no hay qué juzgar
        print(f"✓ el commit no trae código del alcance ({', '.join(dentro)}): no hay nombres que juzgar")
        return 0
    if hallazgos:
        print(f"✗ BLOQUEADO: {len(hallazgos)} nombre(s) en CASTELLANO en el código.\n")
        for rel, linea, que, nombre, palabras in sorted(hallazgos)[:40]:
            print(f"   {rel}:{linea}  {que} «{nombre}»  → {', '.join(palabras)}" if linea
                  else f"   {rel}  {que} «{nombre}»  → {', '.join(palabras)}")
        if len(hallazgos) > 40:
            print(f"   … y {len(hallazgos) - 40} más")
        print("\n  El CÓDIGO va en inglés: ficheros, clases, funciones, variables, campos y claves.")
        print("  Los COMENTARIOS, los docstrings y los textos de pantalla van en castellano: este gate")
        print("  no los mira (rules/code-style.md §Idioma). Si es código HEREDADO que ya estaba así, no")
        print(f"  se renombra en caliente: lo congela una persona en {BASELINE_REL}.")
        return 1
    print(f"✓ el código está en inglés ({revisados} fichero(s) · {len(viejos)} heredado(s) congelado(s)"
          f" · alcance {', '.join(dentro)})")
    return 0


def self_test() -> int:
    """Rojo y verde con ficheros plantados en un repo git temporal, incluido el boy-scout de --staged."""
    casos: list[tuple[str, bool, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        r = pathlib.Path(tmp)

        def escribe(rel: str, txt: str) -> None:
            (r / rel).parent.mkdir(parents=True, exist_ok=True)
            (r / rel).write_text(txt, encoding="utf-8")

        def mide(*extra: str) -> int:
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                return correr(["--raiz", str(r), *extra])

        casos.append(("alcance vacío → 2, no «todo en inglés»", mide() == 2, "sin backend/ ni src/"))
        escribe("backend/apps/orders/services.py",
                '"""Servicios de pedidos: aquí la prosa va en castellano."""\n\n'
                "def create_order(customer, total):\n    # crea el pedido y devuelve su id\n"
                "    message = 'Pedido creado'\n    return {'id': 1, 'msg': message}\n")
        escribe("frontend/src/orders/OrderList.tsx",
                "// la lista de pedidos, con sus tres estados\nexport function OrderList() {\n"
                "  const emptyText = 'Aún no hay pedidos';\n  return emptyText;\n}\n")
        escribe("backend/apps/orders/tests/test_pedidos.py", "def test_crear_pedido_valido():\n    pass\n")
        casos.append(("código en inglés con prosa y tests en castellano → 0", mide() == 0, "control"))
        escribe("backend/apps/orders/billing.py", "def obtener_cliente(nombre):\n    return nombre\n")
        casos.append(("función y argumento en castellano → 1", mide() == 1, "obtener_cliente(nombre)"))
        (r / "backend/apps/orders/billing.py").unlink()
        escribe("frontend/src/orders/dates.ts", "export const fechaLarga = (d: Date) => d.toISOString();\n")
        casos.append(("constante TS en castellano → 1", mide() == 1, "fechaLarga"))
        (r / "frontend/src/orders/dates.ts").unlink()
        escribe("backend/apps/orders/vistas.py", "def list_orders():\n    return []\n")
        casos.append(("fichero con nombre castellano → 1", mide() == 1, "vistas.py"))
        # Congelar el heredado y comprobar que lo nuevo SÍ se juzga con --staged
        subprocess.run(["git", "init", "-q"], cwd=r, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], cwd=r, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"], cwd=r, check=True)
        casos.append(("--congelar crea el baseline → 0", mide("--congelar") == 0, "vistas.py congelado"))
        casos.append(("--congelar otra vez sin --reemplazar → 1", mide("--congelar") == 1, "trinquete"))
        casos.append(("con el heredado congelado → 0", mide() == 0, "control"))
        with open(r / "backend/apps/orders/vistas.py", "a", encoding="utf-8") as f:
            f.write("\n\ndef buscar_pedido(order_id):\n    return order_id\n")
        subprocess.run(["git", "add", "-A"], cwd=r, check=True)
        casos.append(("línea nueva en castellano en un fichero congelado, --staged → 1",
                      mide("--staged") == 1, "buscar_pedido"))
    malos = 0
    for nombre, ok, detalle in casos:
        malos += not ok
        print(f"  {'✓' if ok else '✗'} {nombre}  ({detalle})")
    print(f"self-test: {len(casos) - malos}/{len(casos)}")
    return 1 if malos else 0


if __name__ == "__main__":
    raise SystemExit(correr(sys.argv[1:]))
