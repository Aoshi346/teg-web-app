#!/usr/bin/env python3
"""pattern_check_frontend.py — Tier 0 del PATRÓN DE CASA frontend (React · TypeScript).

Hermano de `.claude/hooks/pattern-check.sh` (que cubre los patrones MEDIDOS de este repo:
skills, templates HTML, rules). Este cubre los patrones DECLARADOS del stack canónico y se
aplica a los proyectos DERIVADOS, donde sí hay código React.

Determinista, 0 tokens, sin dependencias (solo stdlib). Cada regla implementada aquí es la
columna "Cómo se comprueba" de un documento de `.claude/patterns/stack/`: si una regla no
está aquí (o en una regla de ESLint/axe citada por su nombre), NO está en el catálogo.

Uso:
    python3 pattern_check_frontend.py                    # ficheros cambiados (git)
    python3 pattern_check_frontend.py --all frontend/src # escaneo completo (medición/FPR)
    python3 pattern_check_frontend.py fichero.tsx …      # ficheros sueltos
    python3 pattern_check_frontend.py --all src --json    # salida para otro agente
    python3 pattern_check_frontend.py --list             # las reglas, su estado y su nivel
    python3 pattern_check_frontend.py --niveles          # reglas por NIVEL (imposible/editor/gate)
    python3 pattern_check_frontend.py --self-test        # FPR + sensibilidad (fixtures embebidos)

Política (idéntica a pattern-check.sh):
    ACTIVO → violación nueva = bloquea (exit 1)
    DÉBIL  → avisa, nunca bloquea (exit 0)
    Excepción auditable: una línea con `pattern-exempt: <id> — razón` en el propio fichero.

Convención de rutas (ajustable con --src-map si el proyecto difiere):
    componentes  *.tsx fuera de tests      stores  …/store(s)/…
    api client   …/api/… o …/services/…    tests   *.test.* / *.spec.*
    auth         cualquier .ts(x) que persista sesión o defina un logout
    e2e          …/e2e/…                   rutas   …/routes… o App.tsx
    stack        package.json              estilos *.css / *.module.css / *.vue / *.svelte
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

# --------------------------------------------------------------------------------------
# Clasificación de ficheros
# --------------------------------------------------------------------------------------

RE_TEST = re.compile(r"\.(test|spec)\.[tj]sx?$")
RE_E2E = re.compile(r"(^|/)(e2e|playwright)(/|\.)")
RE_STORE = re.compile(r"/stores?/")
RE_API = re.compile(r"/(api|services)/")
RE_HOOK = re.compile(r"/hooks?/")
RE_TOKENS = re.compile(r"(tokens|theme|tailwind\.config|\.css$)")
RE_TS = re.compile(r"\.[tj]sx?$")
RE_PKG = re.compile(r"(^|/)package\.json$")
# Hojas de estilo con ámbito propio: en Tailwind v4 NO ven las variables del tema sin `@reference`.
RE_SCOPED_STYLE = re.compile(r"(\.module\.(css|scss|sass|less)|\.(vue|svelte))$")
# Todo lo que este checker sabe leer. `walk()` y `changed_files()` filtran por aquí.
RE_SCANNABLE = re.compile(r"\.[tj]sx?$|(^|/)package\.json$|\.(css|scss|sass|less|vue|svelte)$")
# Dónde es legítimo declarar rutas: el módulo de rutas y el arranque de la app.
RE_ROUTES = re.compile(r"(^|/)(routes?|App|main|root)\.[tj]sx?$|/routes?/")


def is_test(p: str) -> bool:
    return bool(RE_TEST.search(p))


def is_e2e(p: str) -> bool:
    return bool(RE_E2E.search(p))


def is_unit_test(p: str) -> bool:
    return is_test(p) and not is_e2e(p)


def is_store(p: str) -> bool:
    return bool(RE_STORE.search(p)) and not is_test(p)


def is_api(p: str) -> bool:
    return bool(RE_API.search(p)) and not is_test(p)


def is_component(p: str) -> bool:
    return p.endswith(".tsx") and not is_test(p) and not is_e2e(p)


def is_view_layer(p: str) -> bool:
    """Donde NO puede haber HTTP: componentes, páginas, hooks y stores."""
    return (is_component(p) or bool(RE_HOOK.search(p)) or is_store(p)) and not is_api(p)


def is_pkg(p: str) -> bool:
    return bool(RE_PKG.search(p))


def is_scoped_style(p: str) -> bool:
    return bool(RE_SCOPED_STYLE.search(p))


def is_routes(p: str) -> bool:
    return bool(RE_ROUTES.search(p))


# --------------------------------------------------------------------------------------
# Utilidades de parseo (ligeras: sin AST, pero sin comentarios ni falsos positivos obvios)
# --------------------------------------------------------------------------------------

def strip_comments(src: str) -> str:
    """Quita /* … */ y // … dejando la longitud de línea intacta (para reportar líneas)."""
    out = []
    i, n = 0, len(src)
    in_block = in_line = False
    while i < n:
        c, nxt = src[i], src[i + 1] if i + 1 < n else ""
        if in_block:
            if c == "*" and nxt == "/":
                in_block = False
                out.append("  ")
                i += 2
                continue
            out.append("\n" if c == "\n" else " ")
        elif in_line:
            if c == "\n":
                in_line = False
                out.append("\n")
            else:
                out.append(" ")
        else:
            # `//` de una URL (http://) no abre comentario
            if c == "/" and nxt == "*":
                in_block = True
                out.append("  ")
                i += 2
                continue
            if c == "/" and nxt == "/" and not (i > 0 and src[i - 1] == ":"):
                in_line = True
                out.append("  ")
                i += 2
                continue
            out.append(c)
        i += 1
    return "".join(out)


def line_of(src: str, idx: int) -> int:
    return src.count("\n", 0, idx) + 1


def balanced_body(src: str, open_idx: int) -> tuple[str, int]:
    """Devuelve (cuerpo, idx_cierre) del bloque {...} que empieza en open_idx ('{')."""
    depth, i, n = 0, open_idx, len(src)
    while i < n:
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[open_idx + 1 : i], i
        i += 1
    return "", n


def blocks_after(src: str, keyword_re: re.Pattern) -> list[tuple[int, str]]:
    """Cuerpos de los bloques {...} que siguen a cada match de keyword_re. [(línea, cuerpo)]"""
    found = []
    for m in keyword_re.finditer(src):
        brace = src.find("{", m.end())
        if brace == -1:
            continue
        body, _ = balanced_body(src, brace)
        found.append((line_of(src, m.start()), body))
    return found


RE_USEQUERY = re.compile(r"\buseQuery\s*[(<]")   # NO useQueryClient
RE_CATCH = re.compile(r"\bcatch\s*(\([^)]*\))?\s*(?=\{)")
RE_USEEFFECT = re.compile(r"\buseEffect\s*\(\s*(?:async\s*)?\(\s*\)\s*=>\s*(?=\{)")
RE_CONSOLE_ONLY = re.compile(r"^(?:\s*console\.\w+\s*\([^;]*\)\s*;?\s*)+$", re.S)
RE_SET_STATE_ONLY = re.compile(r"^\s*set[A-Z]\w*\s*\([^;]*\)\s*;?\s*$", re.S)


# --------------------------------------------------------------------------------------
# Reglas.  (id, estado, capa, mensaje, fix)  →  cada una devuelve [(línea, detalle)]
# --------------------------------------------------------------------------------------

RULES: list[dict] = []

# Reglas de PROYECTO: no juzgan un fichero, juzgan el conjunto (p.ej. "¿existe un origen de
# tokens?"). Solo corren con --all, porque desde un diff de dos ficheros no se puede afirmar
# que al proyecto le falta algo. Reciben [(ruta, contenido)] y la raíz escaneada.
PROJECT_RULES: list[dict] = []


def rule(rid, estado, capa, msg, fix, applies):
    def deco(fn):
        RULES.append(
            dict(id=rid, estado=estado, capa=capa, msg=msg, fix=fix, applies=applies, fn=fn)
        )
        return fn

    return deco


def project_rule(rid, estado, capa, msg, fix):
    def deco(fn):
        PROJECT_RULES.append(dict(id=rid, estado=estado, capa=capa, msg=msg, fix=fix, fn=fn))
        return fn

    return deco


def todas_las_reglas() -> list[dict]:
    return RULES + PROJECT_RULES


# --------------------------------------------------------------------------------------
# NIVEL de cada regla (EST-3) — dónde se para el error, no dónde se documenta.
#
#   1 IMPOSIBLE   la estructura no deja cometerlo: si usas la pieza del patrón, el error no
#                 existe. Se comprueba igual, porque nada obliga a usar la pieza.
#   2 AL ESCRIBIR el compilador o el linter lo marcan en el editor, antes de guardar.
#   3 EN EL GATE  se caza después, al pasar el comprobador. Es el default y el más caro:
#                 el agente ya escribió mal y por la mañana hay trabajo pendiente.
#
# Subir una regla de 3 a 1 cuesta trabajo real (hay que escribir la pieza y adoptarla), así que
# solo se sube donde el incumplimiento sale caro. Esta tabla es la fuente única: el documento
# `frontend-a-prueba-de-errores.md` la explica, y `--niveles` la imprime.
# --------------------------------------------------------------------------------------

NIVEL_DE_ERROR: dict[str, tuple[int, str]] = {
    # ── nivel 1: hay una pieza del patrón que hace el error imposible ──────────────────
    "fe-timeout-obligatorio":      (1, "request() de src/api/client.ts ya lleva AbortSignal.timeout dentro"),
    "fe-tres-estados":             (1, "<Asincrono> exige los renderers de carga y error como props obligatorias"),
    "fe-submit-bloqueado":         (1, "<BotonDeEnvio> deriva `disabled` de isPending; no admite no hacerlo"),
    "fe-mutacion-invalida-cache":  (1, "recursoApi() devuelve la clave; invalidar con otra no compila"),
    "fe-token-no-en-localstorage": (1, "cookie HttpOnly: el token no llega nunca a JavaScript"),
    # ── nivel 2: el compilador o el linter lo marcan mientras escribes ─────────────────
    "fe-props-tipadas":            (2, "@typescript-eslint/no-explicit-any en error + tsconfig strict"),
    "fe-http-en-capa-api":         (2, "no-restricted-globals: fetch fuera de src/api/"),
    "fe-enlace-interno-con-link":  (2, "eslint react/forbid-elements o jsx-a11y sobre <a href> interno"),
    "fe-imagen-con-alt":           (2, "jsx-a11y/alt-text"),
    "fe-interactivo-semantico":    (2, "jsx-a11y/no-static-element-interactions"),
    "fe-iconos-tree-shakeable":    (2, "eslint no-restricted-imports sobre el import de espacio de nombres"),
    "fe-sin-espera-por-tiempo":    (2, "eslint testing-library/no-wait-for-timeout"),
    "fe-consulta-por-rol":         (2, "eslint testing-library/prefer-screen-queries + prefer-role"),
    "fe-sin-innerhtml":            (2, "eslint react/no-danger"),
    "fe-error-no-silencioso":      (2, "eslint no-empty (allowEmptyCatch: false)"),
}


def nivel_de(rid: str) -> tuple[int, str]:
    return NIVEL_DE_ERROR.get(rid, (3, "solo lo caza el comprobador, después de escribirlo"))


# ---- capa: llamadas a la API y errores -------------------------------------------------

@rule("fe-http-en-capa-api", "activo", "api",
      "HTTP fuera de la capa de API",
      "mueve la llamada a src/api/<recurso>.ts y consúmela con useQuery/useMutation",
      is_view_layer)
def _http_out_of_api(src, path):
    hits = []
    for m in re.finditer(r"\bfetch\s*\(|\baxios\s*[.(]|\bXMLHttpRequest\b", src):
        hits.append((line_of(src, m.start()), m.group(0).strip()))
    return hits


@rule("fe-tres-estados", "activo", "api",
      "vista con datos remotos sin los tres estados obligatorios",
      "renderiza cargando (isPending) y error (isError) antes de asumir data",
      is_component)
def _three_states(src, path):
    # `useQuery(` con paréntesis, no `in src`: `useQueryClient` contiene la subcadena y un
    # componente que solo crea una mutación no lee datos remotos.
    m = RE_USEQUERY.search(src)
    if not m:
        return []
    hits = []
    line = line_of(src, m.start())
    # `<Asincrono>` exige los dos renderers como props obligatorias, así que su presencia YA
    # garantiza los dos estados: es el nivel 1 de frontend-a-prueba-de-errores.md.
    if re.search(r"<Asincrono\b", src):
        return []
    if not re.search(r"\bisPending\b|status\s*===\s*['\"]pending['\"]|<Suspense", src):
        hits.append((line, "falta el estado de carga (isPending / Suspense)"))
    if not re.search(r"\bisError\b|status\s*===\s*['\"]error['\"]|<ErrorBoundary", src):
        hits.append((line, "falta el estado de error (isError / ErrorBoundary)"))
    return hits


@rule("fe-estado-vacio", "debil", "api",
      "lista renderizada sin estado vacío",
      "añade la rama `if (!data.length) return <Empty …/>` antes del .map",
      is_component)
def _empty_state(src, path):
    if not RE_USEQUERY.search(src) or ".map(" not in src:
        return []
    if re.search(r"\.length\s*===\s*0|!\w+\.length|\.length\s*\?|<Empty", src):
        return []
    return [(line_of(src, src.find(".map(")), "hay .map sobre datos remotos y ninguna rama de lista vacía")]


@rule("fe-error-no-silencioso", "activo", "api",
      "error tragado en un catch",
      "propaga, muestra al usuario o registra con contexto — un catch vacío borra la incidencia",
      lambda p: bool(RE_TS.search(p)) and not is_test(p))
def _swallowed(src, path):
    hits = []
    for line, body in blocks_after(src, RE_CATCH):
        clean = body.strip()
        if clean == "":
            hits.append((line, "catch vacío"))
        elif RE_CONSOLE_ONLY.match(clean):
            hits.append((line, "catch que solo hace console.*"))
    return hits


@rule("fe-error-traducido", "activo", "api",
      "error crudo del servidor renderizado al usuario",
      "pásalo por toUserMessage(error): el .message de un 500 puede ser HTML o un stack trace",
      is_component)
def _raw_error(src, path):
    # Solo errores de SERVIDOR. En un formulario, `{error.message}` es el mensaje de validación
    # de cliente (zod/RHF), que SÍ es texto para el usuario — exigir un fichero que hable con la
    # red evita ese falso positivo, que es frecuente.
    if not re.search(r"\buseQuery\b|\buseMutation\b|\bisError\b|\bApiError\b", src):
        return []
    hits = []
    for m in re.finditer(r"\{\s*(?:\w*[eE]rr\w*)\s*\.\s*message\s*\}", src):
        hits.append((line_of(src, m.start()), m.group(0).strip()))
    return hits


@rule("fe-mutacion-invalida-cache", "debil", "api",
      "mutación que no invalida ni actualiza la caché",
      "invalidateQueries(...) en onSuccess: si no, el usuario crea algo y la lista sigue mostrando lo viejo",
      is_component)
def _mutation_cache(src, path):
    if "useMutation" not in src:
        return []
    if re.search(r"invalidateQueries|setQueryData|\brefetch\b", src):
        return []
    return [(line_of(src, src.find("useMutation")), "useMutation sin invalidateQueries/setQueryData")]


@rule("fe-timeout-obligatorio", "activo", "api",
      "cliente HTTP sin timeout",
      "AbortSignal.timeout(ms) en el fetch base — sin él, una petición colgada congela la vista para siempre",
      is_api)
def _timeout(src, path):
    if not re.search(r"\bfetch\s*\(", src):
        return []
    if re.search(r"AbortSignal\.timeout|\btimeout\s*:", src):
        return []
    return [(line_of(src, src.find("fetch(")), "fetch sin AbortSignal.timeout ni opción timeout")]


@rule("fe-401-en-el-cliente", "activo", "api",
      "el cliente HTTP no dice qué hacer con un 401",
      "trata el 401 UNA vez en src/api/client.ts (limpiar sesión + mandar al login): con fetch "
      "nadie regala los interceptores de axios, y sin esa línea cada llamada gestiona la sesión "
      "caducada a su manera — o no la gestiona (stack/api-y-errores.md §las dos conductas)",
      is_api)
def _401_en_cliente(src, path):
    # Solo el fichero que construye la petición base: un módulo por recurso usa request() y no
    # tiene por qué hablar de códigos de estado.
    if not re.search(r"\bfetch\s*\(", src):
        return []
    if "401" in src:
        return []
    return [(line_of(src, src.find("fetch(")),
             "el cliente base no menciona el 401 en ninguna parte")]


RE_ESQUEMA_RESPUESTA = re.compile(r"\b(?:const|let|var)\s+(\w*ResponseSchema)\s*=")


@rule("fe-esquema-de-respuesta-usado", "debil", "api",
      "esquema de respuesta declarado y nunca aplicado",
      "pásale la respuesta: `return ResponseSchema.parse(await request(...))`. Un esquema que "
      "nadie ejecuta no valida nada y además engaña: da la impresión de que el endpoint está "
      "cubierto (stack/api-y-errores.md §validar la respuesta)",
      is_api)
def _esquema_respuesta_sin_usar(src, path):
    hits = []
    for m in RE_ESQUEMA_RESPUESTA.finditer(src):
        nombre = m.group(1)
        # Basta con que el nombre se REFERENCIE otra vez en el módulo: el uso real casi nunca es
        # `Schema.parse(...)` a secas — es `Schema.array().parse(...)`, `z.array(Schema)` o un
        # `z.infer<typeof Schema>`. Exigir `.parse` pegado al nombre marcaba código correcto.
        if len(re.findall(r"\b" + re.escape(nombre) + r"\b", src)) > 1:
            continue
        hits.append((line_of(src, m.start()),
                     f"{nombre} se declara y no se usa en ningún sitio de este módulo"))
    return hits


# ---- capa: auth ------------------------------------------------------------------------

RE_TOKEN_PERSISTIDO = re.compile(
    r"\b(?:localStorage|sessionStorage)\s*\.\s*setItem\s*\(\s*['\"`][^'\"`]*"
    r"(?:token|jwt|access|refresh|auth)[^'\"`]*['\"`]",
    re.I,
)
RE_DEFINE_LOGOUT = re.compile(r"\b(?:function\s+\w*[lL]ogout|\w*[lL]ogout\w*\s*[:=]\s*(?:async\s*)?\()")


@rule("fe-token-no-en-localstorage", "activo", "auth",
      "token de sesión guardado en localStorage",
      "cookie HttpOnly emitida por el backend: lo que está en localStorage lo lee cualquier script "
      "de la página, así que un solo XSS —propio o de una dependencia— se lleva la sesión entera "
      "(stack/frontend-auth.md)",
      lambda p: bool(RE_TS.search(p)) and not is_test(p))
def _token_persistido(src, path):
    return [(line_of(src, m.start()), m.group(0).strip()) for m in RE_TOKEN_PERSISTIDO.finditer(src)]


@rule("fe-logout-limpia-cache", "debil", "auth",
      "cerrar sesión sin vaciar la caché de queries",
      "queryClient.clear() al cerrar sesión: TanStack Query guarda en memoria lo que vio el usuario "
      "anterior, y sin vaciarla la siguiente persona que entra en el mismo navegador ve sus datos "
      "durante el instante previo al refetch (stack/frontend-auth.md)",
      lambda p: bool(RE_TS.search(p)) and not is_test(p))
def _logout_sin_limpiar(src, path):
    m = RE_DEFINE_LOGOUT.search(src)
    if not m:
        return []
    if re.search(r"queryClient\s*\.\s*(?:clear|removeQueries|resetQueries)\s*\(", src):
        return []
    return [(line_of(src, m.start()), "se define un logout y no se vacía la caché de queries")]


# ---- capa: estado ----------------------------------------------------------------------

@rule("fe-servidor-fuera-del-store", "activo", "estado",
      "estado del servidor dentro del store global",
      "el store guarda estado de UI; los datos del servidor son de la caché de queries",
      is_store)
def _server_in_store(src, path):
    hits = []
    for m in re.finditer(r"\bfetch\s*\(|\baxios\s*[.(]|\bawait\s+\w*[aA]pi\w*\.", src):
        hits.append((line_of(src, m.start()), m.group(0).strip()))
    return hits


@rule("fe-sin-fetch-en-useeffect", "activo", "estado",
      "carga de datos dentro de useEffect",
      "useQuery — el useEffect no cancela, no deduplica, no reintenta y provoca la cascada de peticiones",
      lambda p: is_component(p) or bool(RE_HOOK.search(p)))
def _effect_fetch(src, path):
    hits = []
    for line, body in blocks_after(src, RE_USEEFFECT):
        if re.search(r"\bfetch\s*\(|\baxios\s*[.(]|\w*[aA]pi\w*\.\w+\s*\(|\.then\s*\(", body):
            hits.append((line, "useEffect que llama a la red"))
    return hits


@rule("fe-sin-estado-derivado", "debil", "estado",
      "estado derivado duplicado en un useEffect",
      "calcúlalo durante el render (o useMemo si mide caro): copiarlo a estado añade un render de desfase",
      lambda p: is_component(p) or bool(RE_HOOK.search(p)))
def _derived_state(src, path):
    hits = []
    for line, body in blocks_after(src, RE_USEEFFECT):
        if RE_SET_STATE_ONLY.match(body.strip()):
            hits.append((line, "useEffect cuyo cuerpo es solo un setState"))
    return hits


@rule("fe-store-sin-react", "activo", "estado",
      "el store importa de React",
      "el store es lógica pura y testeable sin render; si necesita React, es un hook, no un store",
      is_store)
def _store_imports_react(src, path):
    hits = []
    for m in re.finditer(r"import[^;]*from\s*['\"](react|[^'\"]*\.tsx)['\"]", src):
        hits.append((line_of(src, m.start()), m.group(0).strip()[:60]))
    return hits


# ---- capa: componentes -----------------------------------------------------------------

@rule("fe-props-tipadas", "activo", "componentes",
      "tipado escapado (any / React.FC)",
      "interface Props exportada; para lo desconocido, `unknown` + estrechado",
      lambda p: bool(RE_TS.search(p)) and not is_test(p))
def _typing(src, path):
    hits = []
    for m in re.finditer(r"\bReact\.FC\b|:\s*any\b|<any>|\bas\s+any\b", src):
        hits.append((line_of(src, m.start()), m.group(0).strip()))
    return hits


@rule("fe-un-componente-por-fichero", "debil", "componentes",
      "el fichero no expone un solo componente con su nombre",
      "un componente por fichero, y el fichero se llama como él: el import dice dónde vive sin abrirlo",
      is_component)
def _one_component(src, path):
    names = re.findall(r"export\s+(?:default\s+)?(?:function|const)\s+([A-Z]\w*)", src)
    if not names:
        return []
    if len(names) > 1:
        return [(1, "exporta " + ", ".join(names))]
    base = os.path.basename(path)[: -len(".tsx")]
    if base in ("index", names[0]):
        return []
    return [(1, f"el fichero se llama {base}.tsx y el componente {names[0]}")]


@rule("fe-techo-200-lineas", "debil", "componentes",
      "componente por encima del techo de 200 líneas",
      "extrae la lógica a un hook o parte la vista: 200 líneas es el umbral, no una opinión",
      is_component)
def _size(src, path):
    n = src.count("\n") + 1
    return [(n, f"{n} líneas")] if n > 200 else []


@rule("fe-color-por-token", "activo", "componentes",
      "color literal en un componente",
      "consúmelo del origen de tokens del proyecto (la utilidad Tailwind del tema o var(--…)); "
      "si el valor no existe, se añade AL ORIGEN, no al componente — stack/frontend-design-system.md",
      lambda p: (p.endswith(".tsx") or p.endswith(".ts")) and not RE_TOKENS.search(p) and not is_test(p))
def _hex(src, path):
    hits = []
    for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", src):
        # #! de shebangs, #region y anclas href="#…" no son colores
        hits.append((line_of(src, m.start()), m.group(0)))
    # rgb()/hsl() con números literales. `rgb(var(--x))` NO se marca: eso es consumir el token,
    # que es justo lo que la regla quiere — por eso se exige un dígito tras el paréntesis.
    for m in re.finditer(r"\b(?:rgba?|hsla?)\(\s*[\d.][^)]{0,60}\)", src):
        hits.append((line_of(src, m.start()), m.group(0).strip()))
    return hits


# ---- capa: formularios -----------------------------------------------------------------

@rule("fe-esquema-unico", "activo", "formularios",
      "validación inline en vez de esquema",
      "un solo esquema zod por formulario (zodResolver): la regex inline se desincroniza del backend",
      lambda p: is_component(p))
def _inline_validation(src, path):
    if "useForm" not in src:
        return []
    hits = []
    for m in re.finditer(r"pattern\s*:\s*\{?\s*(value\s*:\s*)?/", src):
        hits.append((line_of(src, m.start()), "regla `pattern:` inline"))
    return hits


@rule("fe-submit-bloqueado", "activo", "formularios",
      "submit sin bloqueo durante el envío",
      "disabled={isSubmitting} — sin él, el doble clic duplica el pedido/cargo",
      is_component)
def _submitting(src, path):
    if not re.search(r"\bhandleSubmit\s*\(", src):
        return []
    # `<BotonDeEnvio>` deriva el disabled del estado de la mutación por dentro (nivel 1 de
    # frontend-a-prueba-de-errores.md): quien lo usa no puede olvidarse, y exigirle además el
    # isPending a mano sería marcar como error justo la forma más segura de escribirlo.
    if re.search(r"\bisSubmitting\b|\bisPending\b|<BotonDeEnvio\b", src):
        return []
    return [(line_of(src, src.find("handleSubmit")), "formulario sin isSubmitting/isPending")]


@rule("fe-errores-de-campo-del-backend", "debil", "formularios",
      "errores 400 del backend sin mapear a los campos",
      "en el catch, setError('campo', …) con el detalle del DRF: si no, el usuario ve «error» y no sabe qué corregir",
      is_component)
def _field_errors(src, path):
    if "useForm" not in src or "catch" not in src:
        return []
    if "setError" in src:
        return []
    return [(line_of(src, src.find("useForm")), "useForm con catch pero sin setError")]


# ---- capa: tests -----------------------------------------------------------------------

@rule("fe-consulta-por-rol", "activo", "tests",
      "test que consulta por testid o por el DOM",
      "getByRole/getByLabelText — el data-testid es el contrato del E2E (rules/verification.md §E2E-2), no del unitario",
      is_unit_test)
def _testid_in_unit(src, path):
    hits = []
    for m in re.finditer(r"(get|query|find)(All)?ByTestId|container\.querySelector", src):
        hits.append((line_of(src, m.start()), m.group(0)))
    return hits


@rule("fe-red-en-el-boundary", "activo", "tests",
      "el módulo de API está mockeado",
      "intercepta en la red (MSW): mockear el cliente deja sin probar serialización, status y errores",
      is_unit_test)
def _mock_api(src, path):
    hits = []
    for m in re.finditer(r"(vi|jest)\.mock\s*\(\s*['\"][^'\"]*(api|services)[^'\"]*['\"]", src):
        hits.append((line_of(src, m.start()), m.group(0)[:50]))
    return hits


@rule("fe-sin-snapshot-de-componente", "activo", "tests",
      "snapshot de componente",
      "asserta el comportamiento visible; el snapshot falla con cualquier cambio y se re-genera sin leerlo",
      is_unit_test)
def _snapshot(src, path):
    return [(line_of(src, m.start()), "toMatchSnapshot")
            for m in re.finditer(r"toMatchSnapshot\s*\(", src)]


@rule("fe-sin-espera-por-tiempo", "activo", "tests",
      "espera por tiempo en un test",
      "espera por condición (findBy*/waitFor con aserción). Ver rules/verification.md §E2E-3 para el E2E",
      is_unit_test)
def _sleep(src, path):
    hits = []
    for m in re.finditer(r"setTimeout\s*\(|\bsleep\s*\(|waitForTimeout\s*\(", src):
        hits.append((line_of(src, m.start()), m.group(0).strip()))
    return hits


@rule("fe-nivel-del-test", "activo", "tests",
      "el test está en el nivel equivocado",
      "unitario = render() sin navegador; E2E = page.goto() en tests/e2e/. Mezclarlos duplica coste y flakiness",
      lambda p: is_test(p))
def _level(src, path):
    hits = []
    if is_unit_test(path):
        for m in re.finditer(r"\bpage\.goto\s*\(|from\s*['\"]@playwright", src):
            hits.append((line_of(src, m.start()), "navegador en un test unitario"))
    elif is_e2e(path):
        for m in re.finditer(r"from\s*['\"]@testing-library/react['\"]", src):
            hits.append((line_of(src, m.start()), "render de RTL dentro del E2E"))
    return hits


# ---- capa: accesibilidad ---------------------------------------------------------------

@rule("fe-interactivo-semantico", "activo", "a11y",
      "elemento no interactivo con onClick",
      "<button>/<a>: un div con onClick no recibe foco ni responde a Enter/Espacio",
      is_component)
def _div_onclick(src, path):
    hits = []
    for m in re.finditer(r"<(div|span|li|td)\b[^>]*\bonClick=", src, re.S):
        hits.append((line_of(src, m.start()), f"<{m.group(1)} onClick>"))
    return hits


@rule("fe-imagen-con-alt", "activo", "a11y",
      "imagen sin alt",
      'alt="" si es decorativa, descriptivo si informa — sin el atributo el lector de pantalla lee la URL',
      is_component)
def _alt(src, path):
    hits = []
    for m in re.finditer(r"<img\b((?:[^>]|\n)*?)/?>", src):
        if not re.search(r"\balt\s*=", m.group(1)):
            hits.append((line_of(src, m.start()), "<img> sin alt"))
    return hits


@rule("fe-target-size-habilitado", "debil", "a11y",
      "axe corre sin la regla target-size",
      "target-size está DESACTIVADA por defecto en axe-core y su tag es wcag22aa: hay que habilitarla "
      "a mano con axe.configure/rules, o el gate de 24px no se comprueba nunca",
      is_test)
def _target_size(src, path):
    if not re.search(r"\baxe\s*\(|toHaveNoViolations|AxeBuilder", src):
        return []
    if re.search(r"target-size", src):
        return []
    return [(line_of(src, 0), "axe sin 'target-size': { enabled: true }")]


# El movimiento se comprueba a nivel de PROYECTO, no de fichero: que un componente anime no es un
# defecto — el defecto es que en TODO el árbol no haya un solo sitio donde apagarlo. Medido sobre
# el corpus real (3 frontends): el único que anima lo hace con utilidades CSS (51 ficheros con
# `animate-*`, 5 `@keyframes`) y lo apaga en UN bloque de su hoja global.
RE_ANIMA = re.compile(
    r"@keyframes\b|\banimation\s*:|\banimate-(?!none\b)[a-z]"
    r"|from\s*['\"](?:framer-motion|gsap|motion|@react-spring/[a-z]+)['\"]")
RE_REDUCE = re.compile(r"prefers-reduced-motion")


@project_rule("fe-movimiento-apagable", "debil", "a11y",
              "el proyecto anima y en ningún sitio se puede apagar el movimiento",
              "añade UN bloque `@media (prefers-reduced-motion: reduce)` en la hoja global que "
              "anule animaciones y transiciones (stack/accesibilidad.md §El movimiento, apagable "
              "en un sitio): apagarlo animación por animación se olvida en la siguiente que se "
              "escriba, y quien lo necesita no lo necesita a ratos")
def _movimiento_apagable(leidos, raiz):
    if not _es_proyecto_react(raiz):
        return []
    if any(RE_REDUCE.search(s) for _, s in leidos):
        return []
    animan = [p for p, s in leidos if RE_ANIMA.search(s)]
    if not animan:
        return []
    return [(sorted(animan)[0], 1,
             f"{len(animan)} fichero(s) animan y ninguno del árbol escaneado menciona "
             "prefers-reduced-motion")]


# ---- capa: stack (package.json) --------------------------------------------------------
# El canon vive en stack/frontend-stack.md. Aquí solo se comprueba que el package.json no
# contradiga esa decisión: ni una segunda librería para un papel ya resuelto, ni una major
# distinta de aquella para la que están escritos los documentos.

# papel → (librerías que lo duplican, la del canon)
ROLES_DUPLICADOS: dict[str, tuple[tuple[str, ...], str]] = {
    "estado de cliente": (("redux", "@reduxjs/toolkit", "mobx", "recoil", "jotai", "valtio"), "zustand"),
    "estado de servidor": (("swr",), "@tanstack/react-query"),
    "formularios": (("formik", "final-form", "react-final-form", "@tanstack/react-form"), "react-hook-form"),
    "validación": (("yup", "joi", "superstruct", "class-validator"), "zod"),
    "runner de tests": (("jest", "ts-jest", "@jest/globals", "karma"), "vitest"),
    "iconos": (("react-icons", "@heroicons/react", "@fortawesome/react-fontawesome"), "lucide-react"),
    "estilos": (("styled-components", "@emotion/styled", "sass", "less"), "tailwindcss"),
    "saneado de HTML": (("xss", "sanitize-html"), "dompurify"),
    # El canon es el PATRÓN shadcn: primitivas headless (Base UI en proyectos nuevos, Radix donde
    # ya esté) + CVA, con el componente COPIADO al repo. Una suite con estilos propios ocupa el
    # mismo papel y es la que se paga al rebrandear para un cliente.
    "componentes de UI": (("@mui/material", "@mantine/core", "@chakra-ui/react", "antd",
                           "react-bootstrap", "primereact"), "el patrón shadcn (copiado al repo)"),
}

# paquete → major del canon.  `react` se trata como MÍNIMO, el resto como exacto.
CANON_MAJOR: dict[str, int] = {
    "@tanstack/react-query": 5,
    "zod": 4,
    "react-router": 7,
    "react-router-dom": 7,
    "tailwindcss": 4,
    "react": 18,
}
MINIMO_NO_EXACTO = {"react"}


def _deps(src: str) -> dict[str, str]:
    try:
        pkg = json.loads(src)
    except Exception:
        return {}
    out: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        block = pkg.get(key)
        if isinstance(block, dict):
            out.update({k: str(v) for k, v in block.items()})
    return out


def _major(spec: str) -> int | None:
    """5 de '^5.62.0', 18 de '>=18', None de 'latest' o 'workspace:*'."""
    m = re.search(r"(\d+)", spec.split("||")[0])
    return int(m.group(1)) if m else None


def _pkg_line(src: str, name: str) -> int:
    m = re.search(r'"' + re.escape(name) + r'"\s*:', src)
    return line_of(src, m.start()) if m else 1


@rule("fe-stack-canonico", "debil", "stack",
      "segunda librería para un papel que el stack de casa ya tiene resuelto",
      "elige una: dos librerías para el mismo papel significan dos formas de hacer lo mismo en el "
      "mismo repo, y la revisión deja de poder decir cuál es la correcta (stack/frontend-stack.md)",
      is_pkg)
def _stack_canon(src, path):
    deps = _deps(src)
    hits = []
    for papel, (duplicados, canon) in ROLES_DUPLICADOS.items():
        for dup in duplicados:
            if dup in deps:
                hits.append((_pkg_line(src, dup),
                             f"{dup} cubre «{papel}», que en el canon es {canon}"))
    return hits


@rule("fe-version-mayor-del-canon", "debil", "stack",
      "major distinta de aquella para la que está escrito el patrón",
      "los documentos de stack/ usan la API de la major del canon (p.ej. isPending es de TanStack "
      "Query v5, no de v4): con otra major, seguir el patrón al pie de la letra no compila",
      is_pkg)
def _canon_major(src, path):
    deps = _deps(src)
    hits = []
    for name, esperado in CANON_MAJOR.items():
        spec = deps.get(name)
        if not spec:
            continue
        got = _major(spec)
        if got is None:
            continue
        desviado = got < esperado if name in MINIMO_NO_EXACTO else got != esperado
        if desviado:
            comparador = "mínimo " if name in MINIMO_NO_EXACTO else ""
            hits.append((_pkg_line(src, name),
                         f"{name}@{spec} — el canon es {comparador}v{esperado}"))
    return hits


# ---- capa: estilos (Tailwind + iconos) -------------------------------------------------

# Solo utilidades donde la escala de Tailwind es la respuesta y el valor arbitrario casi siempre
# es un descuido. `w-`/`h-` quedan fuera a propósito: un ancho fijo en px es legítimo a menudo.
RE_ARBITRARIO = re.compile(
    r"\b(?:p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|gap-x|gap-y|text|rounded|leading)"
    r"-\[\d+(?:\.\d+)?(?:px|rem)\]"
)


@rule("fe-escala-de-tailwind", "debil", "estilos",
      "valor arbitrario donde existe escala",
      "usa el peldaño de la escala (p-4, text-sm…): un p-[13px] suelto no se alinea con nada y "
      "nadie sabe si el 13 era intencionado",
      lambda p: p.endswith(".tsx") and not is_test(p))
def _tw_arbitrario(src, path):
    return [(line_of(src, m.start()), m.group(0)) for m in RE_ARBITRARIO.finditer(src)]


@rule("fe-clases-con-helper", "debil", "estilos",
      "clases condicionales concatenadas a mano",
      "cn()/clsx(): al concatenar, `px-2` y `px-4` acaban las dos en la clase y gana la que "
      "Tailwind puso última en la hoja, no la última del string",
      lambda p: p.endswith(".tsx") and not is_test(p))
def _tw_concat(src, path):
    if re.search(r"\b(cn|clsx|classNames|twMerge|cva)\s*\(", src):
        return []
    hits = []
    for m in re.finditer(r"className=\{`", src):
        start = m.end()
        end = src.find("`", start)
        if end == -1:
            continue
        tpl = src[start:end]
        if "${" in tpl and "?" in tpl:
            hits.append((line_of(src, m.start()), "className con plantilla condicional sin cn()"))
    return hits


@rule("fe-apply-con-reference", "debil", "estilos",
      "@apply en una hoja con ámbito propio sin @reference",
      'añade `@reference "../app.css";` arriba (o usa var(--color-…) directamente): en Tailwind v4 '
      "estas hojas se compilan aparte y no ven el tema, así que el @apply se queda sin resolver",
      is_scoped_style)
def _apply_sin_reference(src, path):
    if "@apply" not in src or "@reference" in src:
        return []
    m = re.search(r"@apply", src)
    return [(line_of(src, m.start()), "@apply sin @reference en hoja de ámbito propio")]


@rule("fe-iconos-tree-shakeable", "activo", "estilos",
      "importación de iconos que arrastra el paquete entero",
      "importa cada icono por su nombre (`import { Camera } from 'lucide-react'`); si el nombre se "
      "decide en ejecución, usa el mapa de imports dinámicos, no el namespace",
      lambda p: bool(RE_TS.search(p)) and not is_test(p))
def _iconos(src, path):
    hits = []
    for m in re.finditer(r"import\s+\*\s+as\s+(\w+)\s+from\s*['\"]lucide-react['\"]", src):
        hits.append((line_of(src, m.start()), f"import * as {m.group(1)} from 'lucide-react'"))
    for m in re.finditer(r"import\s*\{[^}]*\bicons\b[^}]*\}\s*from\s*['\"]lucide-react['\"]", src):
        hits.append((line_of(src, m.start()), "import { icons } — es el catálogo completo"))
    return hits


# ---- capa: estilos · regla de PROYECTO — el origen de tokens ---------------------------
# El template NO decide los valores (paleta, escala, tipografía): son del proyecto. Lo que sí
# impone es el contrato — que exista UN origen y que esté declarado. Ver frontend-design-system.md.

DOC_SISTEMA = os.path.join(".docs", "core", "design-system.md")


def _raiz_del_proyecto(inicio: str) -> str | None:
    """Sube desde `inicio` buscando la raíz (un .git o un .docs). None si no la encuentra."""
    p = os.path.abspath(inicio)
    if os.path.isfile(p):
        p = os.path.dirname(p)
    for _ in range(6):
        if os.path.isdir(os.path.join(p, ".git")) or os.path.isdir(os.path.join(p, ".docs")):
            return p
        padre = os.path.dirname(p)
        if padre == p:
            break
        p = padre
    return None


def _es_proyecto_react(inicio: str) -> bool:
    """¿Hay un package.json que declare react en `inicio` o por encima?"""
    p = os.path.abspath(inicio)
    if os.path.isfile(p):
        p = os.path.dirname(p)
    for _ in range(5):
        pkg = os.path.join(p, "package.json")
        if os.path.isfile(pkg):
            try:
                if "react" in _deps(open(pkg, encoding="utf-8", errors="replace").read()):
                    return True
            except OSError:
                pass
        padre = os.path.dirname(p)
        if padre == p:
            break
        p = padre
    return False


@project_rule("fe-origen-de-tokens", "debil", "estilos",
              "el proyecto no tiene un origen de tokens único y declarado",
              "declara los tokens en UN bloque @theme y describe el sistema en "
              ".docs/core/design-system.md (plantilla en stack/frontend-design-system.md)")
def _origen_tokens(leidos, raiz):
    # Guarda: si el árbol no pertenece a una app React, pedirle un @theme es ruido. Pasa en el
    # propio tech-lead-template, que no tiene app pero sí .tsx sueltos en repos vendorizados.
    # Se busca el package.json SUBIENDO desde la raíz escaneada, no entre los ficheros leídos:
    # el caso normal es `--all frontend/src`, y ahí el package.json está un nivel más arriba.
    if not _es_proyecto_react(raiz):
        return []

    hits = []
    con_theme = [p for p, s in leidos if re.search(r"^\s*@theme\b", s, re.M)]

    if not con_theme:
        hits.append((raiz, 1,
                     "no hay ningún bloque @theme en el árbol escaneado — CREA src/app.css con "
                     '`@import "tailwindcss";` y un bloque `@theme { … }` con los tokens del proyecto'))
    elif len(con_theme) > 1:
        # Varios orígenes = el bug que la regla existe para evitar: dos sitios que cambiar.
        for p in sorted(con_theme)[1:]:
            hits.append((p, 1, f"segundo origen de tokens (el primero es {sorted(con_theme)[0]})"))

    proyecto = _raiz_del_proyecto(raiz)
    if proyecto and not os.path.isfile(os.path.join(proyecto, DOC_SISTEMA)):
        hits.append((os.path.join(proyecto, DOC_SISTEMA), 1,
                     "falta el documento fundacional del sistema de diseño — CRÉALO copiando la "
                     "plantilla de .claude/patterns/stack/frontend-design-system.md"))
    return hits


# ---- capa: contrato con el backend (tipos generados desde OpenAPI) ---------------------

# Un fichero de tipos generado se reconoce por la cabecera que escribe el generador, no por su
# nombre: `openapi-typescript` emite "This file was auto-generated…", y la convención de casa es
# dejar además un `@generated`. Se acepta cualquiera de las dos marcas.
RE_BANNER_GENERADO = re.compile(r"@generated|auto-?generated|generado autom|DO NOT EDIT", re.I)
RE_SCRIPT_TIPOS = re.compile(r'"api:types"\s*:')
MANAGE_PY = ("manage.py", "backend/manage.py", "api/manage.py", "server/manage.py", "src/manage.py")


def _tiene_backend_django(raiz_proyecto: str, raiz_escaneada: str) -> bool:
    """¿Hay un manage.py cerca? El layout normal es repo/{backend,frontend} y se escanea
    `frontend/src`, así que se mira también desde la raíz escaneada hacia arriba: sin eso, un
    repo sin `.git` (un worktree exportado, una copia) no encontraría nunca el backend."""
    candidatas = [raiz_proyecto]
    p = os.path.abspath(raiz_escaneada)
    for _ in range(4):
        candidatas.append(p)
        padre = os.path.dirname(p)
        if padre == p:
            break
        p = padre
    return any(os.path.isfile(os.path.join(d, c)) for d in candidatas for c in MANAGE_PY)


def _package_json_cercano(inicio: str) -> str | None:
    """Contenido del package.json más cercano subiendo desde `inicio`. None si no hay."""
    p = os.path.abspath(inicio)
    if os.path.isfile(p):
        p = os.path.dirname(p)
    for _ in range(5):
        pkg = os.path.join(p, "package.json")
        if os.path.isfile(pkg):
            try:
                return open(pkg, encoding="utf-8", errors="replace").read()
            except OSError:
                return None
        padre = os.path.dirname(p)
        if padre == p:
            break
        p = padre
    return None


@project_rule("fe-contrato-generado", "debil", "api",
              "el contrato con el backend se mantiene a mano",
              "genera los tipos desde OpenAPI (drf-spectacular → openapi-typescript) con un script "
              "`api:types`, y versiona el fichero resultante: mientras la lista de campos se "
              "escriba a mano, renombrar un campo en Django no rompe nada en el front — solo deja "
              "la pantalla en blanco (stack/frontend-contrato-con-el-backend.md)")
def _contrato_generado(leidos, raiz):
    # Solo tiene sentido donde el backend es NUESTRO y es Django: contra una API de terceros no
    # hay ningún esquema que podamos regenerar, y el aviso sería ruido en cada escaneo.
    if not _es_proyecto_react(raiz):
        return []
    proyecto = _raiz_del_proyecto(raiz) or os.path.abspath(raiz)
    if not _tiene_backend_django(proyecto, raiz):
        return []

    generados = [p for p, s in leidos if RE_BANNER_GENERADO.search(s[:600])]
    if not generados:
        return [(proyecto, 1,
                 "hay backend Django y ningún fichero de tipos generado en el árbol escaneado — "
                 "añade el script `api:types` y versiona src/types/api.d.ts")]

    pkg = _package_json_cercano(raiz)
    if pkg and not RE_SCRIPT_TIPOS.search(pkg):
        return [(generados[0], 1,
                 "hay tipos generados pero ningún script `api:types` que los regenere — sin él "
                 "nadie sabe con qué comando ni contra qué esquema se rehacen")]
    return []


# Todo lo que empieza por VITE_ (o NEXT_PUBLIC_/REACT_APP_) se INCRUSTA en el bundle: no es una
# variable de servidor, es texto que cualquiera lee en el navegador. Medido en el corpus real: las
# 4 variables VITE_* que existen son URLs (VITE_API_URL, VITE_API_BASE_URL ×2, VITE_WS_BASE_URL) —
# ninguna es una credencial. Hermana frontend de `be-env-secreto-literal`.
RE_CREDENCIAL_BUNDLE = re.compile(
    r"import\.meta\.env\.VITE_[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)\b"
    r"|process\.env\.(?:NEXT_PUBLIC|REACT_APP)_[A-Z0-9_]*"
    r"(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)\b")


@rule("fe-credencial-en-el-bundle", "activo", "api",
      "credencial de un tercero leída desde el bundle",
      "el navegador no guarda secretos: mueve la llamada al backend y que sea él quien firme con "
      "la clave (stack/api-y-errores.md §El tercero se llama desde el backend). En el bundle solo "
      "van URLs",
      lambda p: bool(re.search(r"\.[tj]sx?$", p)) and not is_test(p) and not is_e2e(p))
def _credencial_en_bundle(src, path):
    return [(line_of(src, m.start()), m.group(0))
            for m in RE_CREDENCIAL_BUNDLE.finditer(src)]


RE_EN_FEATURE = re.compile(r"(?:^|/)features/([^/]+)/")


@project_rule("fe-feature-con-test", "debil", "tests",
              "feature sin ningún test dentro",
              "el molde de stack/frontend-nueva-pantalla.md genera el test junto a la feature: una "
              "feature entera sin un solo test es casi siempre una pantalla escrita a mano saltándose "
              "el molde, y es la que nadie se atreve a tocar seis meses después")
def _feature_sin_test(leidos, raiz):
    features: dict[str, str] = {}
    con_test: set[str] = set()
    for path, _ in leidos:
        m = RE_EN_FEATURE.search(path.replace(os.sep, "/"))
        if not m:
            continue
        nombre = m.group(1)
        if is_test(path):
            con_test.add(nombre)
        elif path.endswith(".tsx"):
            features.setdefault(nombre, path)
    return [(ruta, 1, f"la feature «{nombre}» no tiene ningún *.test.tsx dentro")
            for nombre, ruta in sorted(features.items()) if nombre not in con_test]


# ---- capa: rutas (react-router 7) ------------------------------------------------------

@rule("fe-enlace-interno-con-link", "activo", "rutas",
      "navegación interna con <a href>",
      "<Link to=…>: un <a> recarga la página entera, pierde el estado de la app y vacía la caché "
      "de queries — el usuario ve un parpadeo en blanco donde no debería haber ninguno",
      is_component)
def _anchor_interno(src, path):
    hits = []
    for m in re.finditer(r"<a\b((?:[^>]|\n)*?)>", src):
        attrs = m.group(1)
        if re.search(r"\btarget\s*=|\bdownload\b|rel\s*=\s*['\"][^'\"]*external", attrs):
            continue
        href = re.search(r"href\s*=\s*['\"](/(?!/)[^'\"]*)['\"]", attrs)
        if href:
            hits.append((line_of(src, m.start()), f'<a href="{href.group(1)}">'))
    return hits


@rule("fe-error-boundary-de-ruta", "activo", "rutas",
      "router sin ErrorBoundary",
      "ErrorBoundary en la ruta raíz: sin él, cualquier error de un loader o de un componente "
      "deja la pantalla en blanco y el usuario no tiene ni mensaje ni forma de volver",
      lambda p: bool(RE_TS.search(p)) and not is_test(p))
def _router_sin_boundary(src, path):
    m = re.search(r"\bcreateBrowserRouter\s*\(", src)
    if not m:
        return []
    if re.search(r"\bErrorBoundary\b|\berrorElement\b", src):
        return []
    return [(line_of(src, m.start()), "createBrowserRouter sin ErrorBoundary/errorElement")]


@rule("fe-rutas-en-un-sitio", "debil", "rutas",
      "ruta declarada fuera del módulo de rutas",
      "declara la ruta en el módulo de rutas: repartidas por los componentes, nadie puede "
      "responder «qué URLs tiene esta app» sin leerla entera",
      lambda p: is_component(p) and not is_routes(p))
def _rutas_dispersas(src, path):
    return [(line_of(src, m.start()), "<Route> fuera del módulo de rutas")
            for m in re.finditer(r"<Route\b", src)]


# ---- capa: saneado (DOMPurify) ---------------------------------------------------------

@rule("fe-html-saneado", "activo", "saneado",
      "HTML de terceros inyectado sin sanear",
      "DOMPurify.sanitize(html) justo antes de pintarlo: sin eso, cualquier texto que venga de la "
      "API o del usuario puede traer un <script> o un onerror= y ejecutarse con la sesión de quien mira",
      lambda p: bool(RE_TS.search(p)) and not is_test(p))
def _html_sin_sanear(src, path):
    # Exige la forma de atributo JSX (`={`). El nombre pelado aparece en prompts, checklists y
    # documentación —el propio workflow /review-branch lo cita como cosa que buscar— y marcarlo
    # ahí es un falso positivo que enseña a ignorar la regla.
    m = re.search(r"dangerouslySetInnerHTML\s*=\s*\{", src)
    if not m:
        return []
    if re.search(r"DOMPurify|\bsanitize\s*\(|\bsanitize[A-Z]\w*\s*\(", src):
        return []
    return [(line_of(src, m.start()), "dangerouslySetInnerHTML sin DOMPurify.sanitize")]


@rule("fe-sin-innerhtml", "activo", "saneado",
      "HTML escrito directamente en el DOM",
      "renderiza con React (o sanea y usa dangerouslySetInnerHTML): innerHTML se salta el escapado "
      "de React, que es justo lo que impide que un texto de usuario se ejecute como marcado",
      lambda p: bool(RE_TS.search(p)) and not is_test(p))
def _innerhtml(src, path):
    hits = []
    for m in re.finditer(r"\.innerHTML\s*=\s*(.{0,4})", src):
        # `.innerHTML = ''` solo vacía un nodo: no inyecta nada.
        if re.match(r"""(['"`])\1""", m.group(1)):
            continue
        hits.append((line_of(src, m.start()), ".innerHTML ="))
    for m in re.finditer(r"\binsertAdjacentHTML\s*\(|\bdocument\.write\s*\(", src):
        hits.append((line_of(src, m.start()), m.group(0).strip()))
    return hits

# ---- capa: formato de fechas e importes (UX-14, cosechado de accounting_AMC) -------------
# En AMC se midieron 15 sitios que pintaban fechas del servidor en crudo, con 4 formatos en una
# misma tarjeta («2026-04-02T09:00:00Z», «3 sept», «12/9/2026, 9:04:33»…). Lo arregló un gate suyo
# (`gate_fechas.py`); aquí va dentro del comprobador de patrones, que ya corre en todos los React.
RE_FORMATEADOR = re.compile(r"(^|/)(format\w*|formato\w*|fechas?|dates?|money|moneda|importes?|i18n)"
                            r"(/|\.[jt]sx?$)", re.I)
CAMPO_FECHA_IMPORTE = (r"(?:created|updated|deleted|due|paid|sent|issued)_at|\w*_date|date|"
                       r"fecha\w*|\w+_fecha|\w+_el|\w+_en|price|precio\w*|importe\w*|amount|monto")
# `(?<!=)`: `key={v.fecha}` es un atributo, no algo que se pinta.
RE_CAMPO_CRUDO = re.compile(r"(?<!=)\{\s*[A-Za-z_$][\w$?.]*\.(?!without_|sin_|no_)(" + CAMPO_FECHA_IMPORTE + r")\s*\}")
RE_OPCIONES_NUMERICAS = re.compile(r"FractionDigits|useGrouping|style\s*:\s*[\"'](?:decimal|percent|unit)")
RE_FORMATO_A_MANO = re.compile(r"\.toLocale(?:Date|Time)?String\s*\(|\bnew\s+Intl\.(?:DateTimeFormat|NumberFormat)\s*\("
                               r"|\.toFixed\s*\(")


@rule("fe-fecha-importe-por-helper", "debil", "componentes",
      "fecha o importe pintado sin pasar por el formateador del proyecto",
      "pásalo por el helper de formato (src/lib/format.ts: formatDate, formatMoney…): una sola "
      "función por formato, o la misma tarjeta acaba con cuatro — stack/componentes.md §Fechas e importes",
      lambda p: p.endswith(".tsx") and not is_test(p) and not RE_FORMATEADOR.search(p))
def _fecha_importe_crudo(src, path):
    hits = []
    for m in RE_CAMPO_CRUDO.finditer(src):
        hits.append((line_of(src, m.start()), m.group(0)))
    for m in RE_FORMATO_A_MANO.finditer(src):
        # toLocaleString con opciones numéricas (porcentajes, horas) es deliberado: AMC lo exime igual.
        if "toLocaleString" in m.group(0) and RE_OPCIONES_NUMERICAS.search(src[m.end():m.end() + 160]):
            continue
        hits.append((line_of(src, m.start()), m.group(0).strip()))
    return hits


# --------------------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------------------

def changed_files() -> list[str]:
    cmds = [
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    out: set[str] = set()
    for c in cmds:
        try:
            out |= set(subprocess.run(c, capture_output=True, text=True).stdout.split())
        except Exception:
            pass
    return sorted(f for f in out if RE_SCANNABLE.search(f))


def walk(root: str) -> list[str]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"node_modules", "dist", "build", ".git",
                       # ver la nota de pattern_check_agente.py: `resources` son los
                       # CUERPOS DE REFERENCIA vendorizados, codigo de terceros.
                       "resources", ".venv", "venv", "site-packages"}]
        for f in filenames:
            if RE_SCANNABLE.search(f):
                found.append(os.path.join(dirpath, f))
    return sorted(found)


def scan(files: list[str], only: str | None = None, raiz: str | None = None) -> list[dict]:
    """Corre las reglas sobre `files`. Devuelve los hallazgos, sin imprimir nada.

    `raiz` activa además las reglas de PROYECTO (PROJECT_RULES). Se pasa solo cuando se ha
    escaneado un árbol entero (--all): desde un diff no se puede afirmar que falta algo.
    """
    findings: list[dict] = []
    leidos: list[tuple[str, str]] = []
    for path in files:
        if not os.path.isfile(path):
            continue
        try:
            raw = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        leidos.append((path, raw))
        # package.json es JSON: no tiene comentarios que quitar y `//` de una URL no debe tocarse.
        src = raw if is_pkg(path) else strip_comments(raw)
        for r in RULES:
            if only and r["capa"] != only:
                continue
            if not r["applies"](path):
                continue
            if re.search(r"pattern-exempt:\s*" + re.escape(r["id"]), raw):
                continue
            for line, detail in r["fn"](src, path):
                findings.append(dict(id=r["id"], estado=r["estado"], capa=r["capa"],
                                     file=path, line=line, msg=r["msg"],
                                     detail=detail, fix=r["fix"]))

    if raiz is not None:
        for r in PROJECT_RULES:
            if only and r["capa"] != only:
                continue
            # La exención de una regla de proyecto se escribe en cualquier fichero del árbol.
            if any(re.search(r"pattern-exempt:\s*" + re.escape(r["id"]), s) for _, s in leidos):
                continue
            for file, line, detail in r["fn"](leidos, raiz):
                findings.append(dict(id=r["id"], estado=r["estado"], capa=r["capa"],
                                     file=file, line=line, msg=r["msg"],
                                     detail=detail, fix=r["fix"]))
    return findings


# --------------------------------------------------------------------------------------
# Self-test: fixtures embebidos.  CONFORME mide falsos positivos (debe dar 0);
# INFRACTOR mide sensibilidad (toda regla del catálogo debe disparar al menos una vez).
# Van embebidos y no en `_fixtures/` a propósito: esa carpeta es del checker de backend y
# este set se materializa en un temporal, así que ningún barrido del repo lo ve nunca.
# --------------------------------------------------------------------------------------

_GIANT = "export function Giant() {\n  return (\n    <ul>\n" + "      <li>fila</li>\n" * 210 + "    </ul>\n  );\n}\n"

FIXTURES_CONFORME: dict[str, str] = {
    # Marca de que el backend es NUESTRO y es Django: es lo que activa `fe-contrato-generado`.
    "manage.py": "#!/usr/bin/env python\n",
    "package.json": """{
  "name": "app-conforme",
  "scripts": {
    "api:types": "openapi-typescript ../backend/schema.yml -o src/types/api.d.ts"
  },
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "react-router": "^7.9.0",
    "@tanstack/react-query": "^5.62.0",
    "zustand": "^5.0.0",
    "react-hook-form": "^7.54.0",
    "@hookform/resolvers": "^5.0.0",
    "zod": "^4.0.0",
    "lucide-react": "^0.547.0",
    "dompurify": "^3.2.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^3.0.0",
    "openapi-fetch": "^0.17.0",
    "openapi-react-query": "^0.5.4"
  },
  "devDependencies": {
    "tailwindcss": "^4.1.0",
    "typescript": "^5.9.3",
    "vite": "^8.3.0",
    "@vitejs/plugin-react": "^6.1.0",
    "vitest": "^5.0.0",
    "jsdom": "^30.1.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/dom": "^10.4.0",
    "msw": "^3.0.0",
    "@playwright/test": "^1.50.0",
    "openapi-typescript": "^7.13.0",
    "@types/react": "^19.1.0",
    "@types/react-dom": "^19.1.0"
  }
}
""",
    "src/api/client.ts": """export class ApiError extends Error {
  constructor(readonly status: number, readonly fields: Record<string, string[]> = {}) {
    super(`api ${status}`);
  }
}

const BASE = import.meta.env.VITE_API_URL;

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: 'include',
    signal: AbortSignal.timeout(15_000),
    headers: { 'Content-Type': 'application/json', ...init.headers },
  });
  if (res.status === 401) {
    onSesionCaducada();
    throw new ApiError(401);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    onErrorDeRed(res.status);
    throw new ApiError(res.status, body as Record<string, string[]>);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
""",
    "src/api/orders.ts": """import { z } from 'zod';
import { request } from './client';

export const OrderResponseSchema = z.object({ id: z.string(), reference: z.string() });

export const ordersApi = {
  list: async () => OrderResponseSchema.array().parse(await request<unknown>('/orders/')),
};

export const orderKeys = { all: ['orders'] as const };
""",
    "src/types/api.d.ts": """/**
 * @generated by openapi-typescript desde backend/schema.yml — NO EDITAR A MANO.
 * Se regenera con `npm run api:types`.
 */
export interface paths {
  '/api/orders/': { get: { responses: { 200: { content: { 'application/json': unknown } } } } };
}
""",
    "src/features/auth/useAuth.ts": """import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../../api/auth';

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      queryClient.clear();
    },
  });
}
""",
    "src/stores/uiStore.ts": """import { create } from 'zustand';

export interface UiState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
""",
    "src/hooks/useOrders.ts": """import { useQuery } from '@tanstack/react-query';
import { ordersApi, orderKeys } from '../api/orders';

export function useOrders() {
  return useQuery({ queryKey: orderKeys.all, queryFn: ordersApi.list });
}
""",
    "src/components/OrderList.tsx": """import { useQuery } from '@tanstack/react-query';
import { Camera } from 'lucide-react';
import { Link } from 'react-router';
import { ordersApi, orderKeys } from '../api/orders';
import { toUserMessage } from '../api/errors';

export interface OrderListProps {
  onSelect: (id: string) => void;
}

export function OrderList({ onSelect }: OrderListProps) {
  const { isPending, isError, error, data } = useQuery({
    queryKey: orderKeys.all,
    queryFn: ordersApi.list,
  });

  if (isPending) return <ListSkeleton rows={5} />;
  if (isError) return <ErrorState message={toUserMessage(error)} />;
  if (data.length === 0) return <EmptyState title="Aun no hay pedidos" />;

  return (
    <ul className="flex flex-col gap-4 p-4">
      {data.map((order) => (
        <li key={order.id}>
          <Camera aria-hidden="true" />
          <img src={order.thumbnail} alt="" />
          <Link to={`/orders/${order.id}`}>{order.reference}</Link>
          <button type="button" onClick={() => onSelect(order.id)}>Ver detalle</button>
        </li>
      ))}
    </ul>
  );
}
""",
    "src/routes.tsx": """import { createBrowserRouter } from 'react-router';
import { RootErrorBoundary } from './components/RootErrorBoundary';

export const router = createBrowserRouter([
  {
    path: '/',
    ErrorBoundary: RootErrorBoundary,
    lazy: () => import('./pages/Home'),
  },
]);
""",
    "src/features/orders/components/OrderForm.tsx": """import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { orderSchema, type OrderInput } from '../schemas/order';
import { ApiError } from '../../../api/client';
import { ordersApi } from '../../../api/orders';

export interface OrderFormProps {
  onCreated: () => void;
}

export function OrderForm({ onCreated }: OrderFormProps) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<OrderInput>({ resolver: zodResolver(orderSchema) });

  async function onSubmit(values: OrderInput) {
    try {
      await ordersApi.create(values);
      onCreated();
    } catch (err) {
      if (err instanceof ApiError) {
        for (const [field, msgs] of Object.entries(err.fields)) {
          setError(field as keyof OrderInput, { message: msgs[0] });
        }
        return;
      }
      setError('root', { message: 'No pudimos guardar el pedido.' });
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <label htmlFor="reference">Referencia</label>
      <input id="reference" {...register('reference')} aria-invalid={!!errors.reference} />
      {errors.reference && <p role="alert">{errors.reference.message}</p>}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Guardando' : 'Guardar'}
      </button>
    </form>
  );
}
""",
    "src/components/OrderList.test.tsx": """import { render, screen } from '@testing-library/react';
import { axe } from 'vitest-axe';
import { server, mockOrders } from '../../tests/msw/server';
import { OrderList } from './OrderList';

test('muestra el estado vacio cuando no hay pedidos', async () => {
  server.use(mockOrders([]));
  render(<OrderList onSelect={() => {}} />, { wrapper: QueryWrapper });
  expect(await screen.findByText('Aun no hay pedidos')).toBeVisible();
});

test('no tiene violaciones de accesibilidad', async () => {
  const { container } = render(<OrderList onSelect={() => {}} />, { wrapper: QueryWrapper });
  const results = await axe(container, { rules: { 'target-size': { enabled: true } } });
  expect(results).toHaveNoViolations();
});
""",
    "src/features/orders/components/OrderForm.test.tsx": """import { render, screen } from '@testing-library/react';
import { server, mockOrders } from '../../../tests/msw/server';
import { OrderForm } from './OrderForm';

test('avisa cuando falta la referencia', async () => {
  server.use(mockOrders([]));
  render(<OrderForm onDone={() => {}} />, { wrapper: QueryWrapper });
  await userEvent.click(screen.getByRole('button', { name: /guardar/i }));
  expect(await screen.findByText('La referencia es obligatoria')).toBeVisible();
});
""",
    "e2e/checkout.spec.ts": """import { test, expect } from '@playwright/test';

test('el camino feliz de la compra', async ({ page }) => {
  await page.goto('/checkout');
  await expect(page.getByTestId('checkout-submit')).toBeEnabled();
});
""",
    # El ÚNICO origen de tokens. Los valores son de relleno a propósito: el template no decide
    # la paleta de nadie (decisión del Usuario, EST-2) — solo exige que el origen exista.
    "src/app.css": """@import "tailwindcss";

@theme {
  --color-bg: #ffffff;
  --color-fg: #1a1a1a;
  --radius-card: 0.75rem;
}

@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* El unico sitio donde se apaga el movimiento, para todo el proyecto. */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
""",
    "src/styles/card.module.css": """@reference "../app.css";

.card {
  @apply rounded-xl border p-5;
}
""",
    "src/lib/format.ts": """const fecha = new Intl.DateTimeFormat("es-ES", { dateStyle: "medium" });
const euros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });

export const formatDate = (iso: string): string => fecha.format(new Date(iso));
export const formatMoney = (centimos: number): string => euros.format(centimos / 100);
""",
    "src/components/InvoiceRow.tsx": """import { formatDate, formatMoney } from "../lib/format";

interface InvoiceRowProps {
  invoice: { number: string; issued_at: string; amount: number };
}

export function InvoiceRow({ invoice }: InvoiceRowProps) {
  return (
    <li>
      {invoice.number} · {formatDate(invoice.issued_at)} · {formatMoney(invoice.amount)}
    </li>
  );
}
""",
}

FIXTURES_INFRACTOR: dict[str, str] = {
    "package.json": """{
  "name": "app-infractor",
  "dependencies": {
    "react": "^17.0.2",
    "react-router": "^6.20.0",
    "@tanstack/react-query": "^4.36.1",
    "formik": "^2.4.6",
    "yup": "^1.4.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "jest": "^29.7.0"
  }
}
""",
    "manage.py": "#!/usr/bin/env python\n",
    "src/api/client.ts": """export async function request(path: string) {
  try {
    const res = await fetch(`/api${path}`);
    return res.json();
  } catch (e) {
  }
}
""",
    "src/api/reports.ts": """import { z } from 'zod';
import { request } from './client';

export const ReportResponseSchema = z.object({ total: z.number() });

// El bundle es publico: esta clave la lee cualquiera con el inspector abierto.
const CRM_KEY = import.meta.env.VITE_CRM_API_KEY;

export const reportsApi = {
  summary: () => request('/reports/summary/'),
  crmHeaders: () => ({ Authorization: `Bearer ${CRM_KEY}` }),
};
""",
    "src/features/auth/useAuth.ts": """import { useMutation } from '@tanstack/react-query';
import { authApi } from '../../api/auth';

export async function login(email: string, password: string) {
  const { access_token } = await authApi.login(email, password);
  localStorage.setItem('access_token', access_token);
}

export function logout() {
  localStorage.removeItem('access_token');
  window.location.href = '/login';
}
""",
    "src/stores/dataStore.ts": """import { useState } from 'react';
import { create } from 'zustand';

export const useDataStore = create((set) => ({
  orders: [],
  load: async () => {
    const res = await fetch('/api/orders');
    set({ orders: await res.json() });
  },
}));
""",
    "src/hooks/useOrders.ts": """import { useEffect, useState } from 'react';

export function useOrders(users) {
  const [orders, setOrders] = useState([]);
  const [count, setCount] = useState(0);

  useEffect(() => {
    fetch('/api/orders').then((r) => r.json()).then(setOrders);
  }, []);

  useEffect(() => {
    setCount(users.length);
  }, [users]);

  return { orders, count };
}
""",
    "src/components/panel.tsx": """import * as Icons from 'lucide-react';
import { Route } from 'react-router';
import { useQuery, useMutation } from '@tanstack/react-query';

export function UserPanel({ userId, users }: any) {
  const { data, error } = useQuery({ queryKey: ['u'], queryFn: load });
  const mutation = useMutation({ mutationFn: save });

  function paint(el: HTMLElement, html: string) {
    el.innerHTML = html;
  }

  return (
    <div onClick={() => paint(document.body, userId)} style={{ color: '#ff0044', background: 'rgb(255, 0, 68)' }}>
      <p>{error.message}</p>
      <img src="/avatar.png" />
      <a href="/orders">Pedidos</a>
      <Route path="/x" />
      <Icons.Camera />
      <span className={`p-[13px] ${users ? 'bg-red-500' : 'bg-gray-500'}`} />
      <div dangerouslySetInnerHTML={{ __html: userId }} />
      {users.map((u) => <li key={u.id}>{u.name}</li>)}
    </div>
  );
}

export function UserBadge() {
  return <b>badge</b>;
}
""",
    "src/components/Giant.tsx": _GIANT,
    "src/routes.tsx": """import { createBrowserRouter } from 'react-router';
import { Home } from './pages/Home';

export const router = createBrowserRouter([{ path: '/', Component: Home }]);
""",
    "src/features/orders/components/OrderForm.tsx": r"""import { useForm } from 'react-hook-form';

export function OrderForm() {
  const { register, handleSubmit } = useForm();

  async function onSubmit(values) {
    try {
      await fetch('/api/orders', { method: 'POST', body: JSON.stringify(values) });
    } catch (err) {
      console.log(err);
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('phone', { pattern: { value: /^[6789]\d{8}$/, message: 'Telefono invalido' } })} />
      <button type="submit">Enviar</button>
    </form>
  );
}
""",
    "src/components/OrderList.test.tsx": """import { render, screen } from '@testing-library/react';
import { chromium } from '@playwright/test';
import { axe } from 'vitest-axe';

vi.mock('../api/orders');

test('renders', async () => {
  const { container } = render(<Widget />);
  expect(container.querySelector('.title')).toBeTruthy();
  expect(screen.getByTestId('widget-root')).toBeVisible();
  await new Promise((r) => setTimeout(r, 500));
  expect(container).toMatchSnapshot();
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
""",
    "src/styles/card.module.css": """.card {
  @apply rounded-xl border p-5;
  animation: card-in 320ms ease-out;
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
""",
    "src/components/InvoiceRowCrudo.tsx": """interface InvoiceRowCrudoProps {
  invoice: { number: string; issued_at: string; amount: number };
}

export function InvoiceRowCrudo({ invoice }: InvoiceRowCrudoProps) {
  return (
    <li>
      {invoice.number} · {invoice.issued_at} · {invoice.amount.toFixed(2)} €
    </li>
  );
}
""",
}


def _materialize(root: str, files: dict[str, str]) -> list[str]:
    out = []
    for rel, src in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src)
        out.append(path)
    return out


def self_test() -> int:
    import tempfile

    ok = True
    with tempfile.TemporaryDirectory(prefix="fe-pattern-") as tmp:
        conformes = _materialize(os.path.join(tmp, "conforme"), FIXTURES_CONFORME)
        infractores = _materialize(os.path.join(tmp, "infractor"), FIXTURES_INFRACTOR)

        raiz_c = os.path.join(tmp, "conforme")
        raiz_i = os.path.join(tmp, "infractor")

        falsos = scan(conformes, raiz=raiz_c)
        print(f"── FPR: {len(falsos)} hallazgo(s) sobre {len(conformes)} ficheros CONFORMES")
        for f in falsos:
            print(f'     ✗ {os.path.relpath(f["file"], tmp)}:{f["line"]} — {f["id"]}: {f["detail"]}')
            ok = False

        disparan = {f["id"] for f in scan(infractores, raiz=raiz_i)}
        total = todas_las_reglas()
        print(f"── Sensibilidad: {len(disparan)}/{len(total)} reglas disparan sobre los fixtures INFRACTORES")
        for r in total:
            if r["id"] not in disparan:
                print(f'     ✗ sin cobertura en los fixtures: {r["id"]}')
                ok = False

    # La tabla de niveles (EST-3) es texto suelto: una regla renombrada la deja apuntando a un id
    # que ya no existe y nadie se entera. Aquí sí se entera.
    ids = {r["id"] for r in todas_las_reglas()}
    huerfanas = sorted(set(NIVEL_DE_ERROR) - ids)
    print(f"── Niveles: {len(NIVEL_DE_ERROR)} reglas con nivel declarado, "
          f"{len(ids) - len(NIVEL_DE_ERROR)} en el nivel 3 por defecto")
    for rid in huerfanas:
        print(f"     ✗ NIVEL_DE_ERROR declara un id que no existe: {rid}")
        ok = False

    print("self-test: OK" if ok else "self-test: FALLA")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="ficheros a comprobar")
    ap.add_argument("--all", metavar="RAIZ", help="escanea todo el árbol (medición / FPR)")
    ap.add_argument("--json", action="store_true", help="salida JSON")
    ap.add_argument("--only", help="filtra por capa: api|auth|estado|componentes|formularios|tests|"
                                   "a11y|stack|estilos|rutas|saneado")
    ap.add_argument("--list", action="store_true", help="lista las reglas, su estado y su nivel")
    ap.add_argument("--niveles", action="store_true",
                    help="las reglas agrupadas por NIVEL (imposible / editor / gate) — EST-3")
    ap.add_argument("--self-test", dest="self_test", action="store_true",
                    help="FPR + sensibilidad sobre los fixtures embebidos")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if args.list:
        proyecto = {r["id"] for r in PROJECT_RULES}
        for r in sorted(todas_las_reglas(), key=lambda x: (x["capa"], x["id"])):
            ambito = " [proyecto]" if r["id"] in proyecto else ""
            print(f'{r["estado"]:<7} n{nivel_de(r["id"])[0]}  {r["capa"]:<12} '
                  f'{r["id"]:<32} {r["msg"]}{ambito}')
        print(f"\n{len(todas_las_reglas())} reglas "
              f"({len(RULES)} por fichero + {len(PROJECT_RULES)} de proyecto, solo con --all)")
        print("nivel: n1 imposible por construcción · n2 lo marca el editor · n3 solo el gate "
              "(detalle: --niveles)")
        return 0

    if args.niveles:
        etiquetas = {1: "1 · IMPOSIBLE por construcción",
                     2: "2 · lo marca el editor (tipos / lint)",
                     3: "3 · solo lo caza el gate, después de escribirlo"}
        for n in (1, 2, 3):
            reglas = [r for r in sorted(todas_las_reglas(), key=lambda x: x["id"])
                      if nivel_de(r["id"])[0] == n]
            print(f'\n── nivel {etiquetas[n]}  ({len(reglas)} reglas)')
            for r in reglas:
                print(f'   {r["id"]:<32} {nivel_de(r["id"])[1]}')
        print("\nSubir una regla de 3 a 1 cuesta escribir la pieza y adoptarla: se hace solo con "
              "las que salen caras.\nCriterio y mecanismos: .claude/patterns/stack/"
              "frontend-a-prueba-de-errores.md")
        return 0

    files = args.files or (walk(args.all) if args.all else changed_files())
    if not files:
        # `--json` tiene que emitir JSON SIEMPRE, tambien cuando no hay nada que mirar:
        # una linea de texto plano aqui rompe la tuberia
        #   comprobador --json | pattern_baseline.py check --from -
        # y el que la monta lo descubre en produccion, no aqui.
        if getattr(args, "json", False):
            print("[]")
        else:
            print("pattern-check-frontend: sin ficheros que comprobar")
        return 0

    findings = scan(files, args.only, raiz=args.all)
    fail = any(f["estado"] == "activo" for f in findings)
    warn = any(f["estado"] != "activo" for f in findings)

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            tag = "✗ [ACTIVO]" if f["estado"] == "activo" else "⚠ [débil] "
            print(f'{tag} {f["file"]}:{f["line"]} — {f["msg"]} ({f["id"]})')
            print(f'   {f["detail"]}  ·  fix: {f["fix"]}')
        if fail:
            print("\npattern-check-frontend: violaciones ACTIVAS — detalle en .claude/patterns/stack/")
        elif warn:
            print("pattern-check-frontend: avisos de patrones débiles (no bloquean)")
        else:
            print(f"pattern-check-frontend: OK ({len(files)} ficheros)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
