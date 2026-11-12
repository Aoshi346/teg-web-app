#!/usr/bin/env python3
"""¿Están los documentos base antes de escribir código? — el gate de las 5 fases de `/arrancar`.

POR QUÉ EXISTE. El Usuario preguntó el 2026-09-12 por qué al arrancar un proyecto nadie le
preguntaba nada. La causa medida: `.specify/scripts/` no existía y 8 de los 9 comandos de SpecKit
morían en su primer paso; y los 7 gates de `rules/plan-gates.md` eran prosa, los siete. Una norma
escrita que se incumple no se arregla subiendo el tono — se BAJA DE CAPA (`rules/layer-decision.md`).
Esto es esa capa.

QUÉ COMPRUEBA, Y QUÉ NO. Comprueba que cada documento **exista, tenga contenido propio, traiga su
estructura mínima y esté firmado**. NO comprueba que sea correcto: un PRD impecablemente formado y
lleno de disparates pasa. Es el mismo límite que declara `gate_datos_salud.py` en su cabecera, y no
se disimula. Lo que sí caza, y es lo que ningún gate de casa cazaba: **la plantilla renombrada**.
«Firmado» quiere decir, desde la 2.17: en el frontmatter, con una fecha que existe y no es futura, y
por una persona — no por el agente que lo escribió (`revisa_firma`).

TRES DESENLACES, NUNCA DOS (`rules/verification.md` §el instrumento que no puede medir):
    cumple · no_cumple · no_medible   — y `no_medible` JAMÁS cuenta como verde.
Un chequeo que no puede llegar al sujeto aborta; no devuelve cero.

    python3 .claude/scripts/gate_arranque.py <proyecto>              # informe legible
    python3 .claude/scripts/gate_arranque.py <proyecto> --explica    # + qué falta y cómo se arregla
    python3 .claude/scripts/gate_arranque.py <proyecto> --fase prd   # una sola fase
    python3 .claude/scripts/gate_arranque.py <proyecto> --hook       # solo la PRIMERA que falla
    python3 .claude/scripts/gate_arranque.py <proyecto> --json

Exit: 0 cumple · 1 violación real · 2 no se pudo medir · 3 sin contexto (no hay plan de arranque).
El hook `gate-arranque.sh` traduce {1,2,3} → 2, que es el único que bloquea en PreToolUse.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys

# Se IMPORTAN, no se recopian: si mañana cambia el verbo normativo, cambia en un solo sitio.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from spec_lint import ACCEPT, NORMATIVE  # noqa: E402
except ImportError:                                            # pragma: no cover
    NORMATIVE = re.compile(r"\b(DEBE(R[ÁA])?N?|NO DEBE|SHALL|MUST)\b", re.I)
    ACCEPT = re.compile(r"(criterios? de aceptaci|acceptance criteria|dado que|given\b)", re.I)
    sys.stderr.write("aviso: no se pudo importar spec_lint — usando copias locales de las regex\n")

CUMPLE, NO_CUMPLE, NO_MEDIBLE, NO_APLICA = "cumple", "no_cumple", "no_medible", "no_aplica"

# Huecos de plantilla sin rellenar. DOS regex, y la separación no es cosmética:
#   · MARCAS va SIN re.I a propósito. Con `re.I`, `\bTODO\b` y `\bPENDIENTE\b` casan con las
#     palabras españolas normales «todo» y «pendiente», así que CUALQUIER documento en español
#     fallaba el gate. Lo encontró el sabotaje S-01b, no la lectura del código.
#   · HUECOS son marcadores inequívocos: no existen en prosa normal, así que no necesitan el caso.
MARCAS = re.compile(r"\bTODO\b|\bPENDIENTE\b|\bXXX\b|\bTBD\b|\bFIXME\b")
HUECOS = re.compile(r"<[a-zñáéíóú ][^>]{2,40}>|\[rellenar\]|\[PERSONALIZAR\]|\bLorem ipsum\b", re.I)

# ── La firma (sub-ola 2.17: MO-61 y PV-76) ────────────────────────────────────────────────────────
# Antes eran dos regex sobre TODO el documento, y fallaban de tres formas medidas:
#   · `reviewed_by:` vacío pasaba: con re.M, `\s*` cruza el salto de línea y la línea siguiente
#     (`---`) hacía de firmante. Y `reviewed: 2026-13-45` pasaba: `\d{4}-\d{2}-\d{2}` no es una
#     fecha.
#   · Ganaba la PRIMERA clave que apareciera, y `autor:` va antes que `reviewed_by:` en el PRD de
#     fitapp: el gate leía «Tech Lead (agente) · borrador para que lo confirme el Usuario» como
#     firma.
#   · Un agente podía firmar lo que había escrito él.
# Ahora la firma se lee del FRONTMATTER, por claves y en orden de autoridad: quien revisó
# (`reviewed_by`, `revisado_por`) antes que quien escribió (`autor`, que es lo que trae la plantilla
# del PRD). La primera clave PRESENTE manda aunque esté vacía: un `reviewed_by:` vacío es un
# documento sin revisar, no una invitación a mirar el `autor`.
CLAVES_FECHA = ("reviewed", "revisado")
CLAVES_FIRMANTE = ("reviewed_by", "revisado_por", "autor")
# Firma quien REVISA, no quien escribe. Las mismas reglas que `gate_amenazas.py` (que las endureció
# en cuatro pasadas de verificador en la 2.25), más «Tech Lead», que en este harness es el agente.
# Van copiadas y no importadas porque la medición de mutantes de la 2.25 muta su texto en aquel
# fichero.
FIRMA_GENERICA = re.compile(
    r"^\W*(el |la |un |una )?(propi[oa] )?(agente|ia|llm|modelo|asistente|bot)\b", re.I)
AYUDA = re.compile(r"\b(con (la )?ayuda de|asistid[oa] por|apoyad[oa] en)\b.*$", re.I)
PERSONA = re.compile(r"(?-i:\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)")
FIRMA_AGENTE = re.compile(
    r"\b(agente|subagente|llm|chatgpt|gpt[\w.-]*|copilot|gemini|codex|sonnet|opus|haiku|fable|"
    r"mistral|llama|deepseek|qwen|anthropic|openai|autom[áa]tic\w*)\b|"
    r"\bclaude\b(?!\s+(?-i:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b)|"
    r"\bclaude[\s-]+(code|opus|sonnet|haiku)\b|"
    r"(?-i:^[a-z0-9]+(?:-[a-z0-9]+)+$)",
    re.I,
)
# Un nombre de pila delante hace de «Claude» un nombre compuesto: «Jean Claude», «Jean-Claude
# Pérez», «Anne Claude» firman personas (tercera pasada del verificador de la 2.17). No es nombre la
# palabra que hace de Claude el modelo: «Asistente Claude», «Por Claude», «Revisado por Claude».
# Límite declarado: un nombre de pila que esté en esa lista, o la firma en minúsculas («jean
# claude»), se sigue leyendo como agente.
NOMBRE_Y_CLAUDE = re.compile(
    r"(?-i:\b(?!(?:Por|Con|De|Del|Para|Según|Vía|Agente|Asistente|Modelo|Bot|Usuario|Sesión|"
    r"Revisión|Revisado|Revisada|Generado|Firmado)\b)[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)(?:\s+|-)claude\b",
    re.I)
# «Tech Lead» a secas es el agente; «Ana Ruiz, Tech Lead de Proxera» es una persona con su cargo.
TECH_LEAD = re.compile(r"\btech[\s-]?lead\b|(?-i:\bTL\b)", re.I)
# Una sesión de agente firmando: «directora `elvion-platform-consolidation`», «la sesión X».
# «sesión» solo al EMPEZAR la firma: «Miller en la sesión del 2 de octubre» la firma Miller
# (verificador de la 2.17, segunda pasada). Un identificador kebab cuenta entre comillas invertidas
# o con dos guiones.
SESION_AGENTE = re.compile(
    r"`[a-z0-9]+(?:-[a-z0-9]+)+`|^\W*(la |una )?sesi[óo]n\b|"
    r"(?-i:\b[a-z0-9]+(?:-[a-z0-9]+){2,}\b)", re.I)
FIRMA_RELLENO = re.compile(
    r"\b(pendiente|nadie|tbd|sin (firmar|revisar|asignar)|"
    r"por (revisar|firmar|asignar|definir|decidir)|a revisar)\b",
    re.I,
)
# Un estado final es lo que hace que el trabajo pueda terminar. Sin él, la máquina es un bug.
ESTADO_FINAL = re.compile(r"\|\s*\*{0,2}fin\*{0,2}\s*\||\bfinal\b|\bcerrado\b|\bterminad", re.I)

RATIO_PLANTILLA = 0.85   # ≥ esto ⇒ es la plantilla con el título cambiado

# id → (ruta relativa al plan, plantilla de referencia, bytes mínimos, comprobaciones extra)
#
# Los mínimos están CALIBRADOS CONTRA UN CONTROL NEGATIVO, no puestos a ojo: un PRD real, corto y
# completo (problema con su frecuencia · quién decide · métrica medida · fuera de alcance) pesa
# ~1.100 B, y con el umbral en 1.200 fallaba. Un gate que castiga la concisión enseña a rellenar
# con paja, que es lo contrario de lo que se busca. El suelo descarta esqueletos, nada más.
FASES = {
    "prd": [
        ("prd", "arranque/01-prd.md", ".claude/templates/prd-template.md", 800, ("metrica",)),
    ],
    "requisitos": [
        ("requisitos", "arranque/02-requisitos.md", ".claude/templates/requisito-template.md",
         1200, ("normativo", "gherkin", "estado_final")),
    ],
    "datos": [
        ("modelo", "arranque/03-modelo-datos.md", None, 600, ()),
        # 60 B y no 120: en un JSON el tamaño no mide contenido — un modelo correcto con dos
        # entidades pesa ~90 B y fallaba (control negativo N-03). Lo que lo valida de verdad
        # es el check `personal`, que mira campo por campo.
        ("entidades", "arranque/entidades.json", None, 60, ("personal",)),
        ("flujos", "arranque/04-flujos.md", None, 400, ()),
    ],
    "stack": [
        ("stack", "arranque/05-stack.md", None, 500, ("stack_completo",)),
    ],
    "etica": [
        ("etica", "arranque/06-etica-privacidad.md", None, 500, ("base_legal",)),
    ],
    "seguridad": [
        ("superficie", "arranque/07-superficie.md", None, 600, ("defensas",)),
    ],
}
ORDEN = ["prd", "requisitos", "datos", "stack", "etica", "seguridad"]

ARREGLO = {
    "prd":        "/arrancar → fase 1 (3 tandas: el problema · quién manda · éxito y recorte)",
    "requisitos": "/arrancar → fase 1b (3 tandas por requisito, los 11 apartados)",
    "datos":      "/arrancar → fase 2 (4 tandas: las cosas · relaciones · sensibilidad · flujos)",
    "stack":      "/arrancar → fase 3 (3 tandas: stack · comprar-o-construir · bordes)",
    "etica":      "/arrancar → fase 4 (base legal · retención · encargados)",
    "seguridad":  "/arrancar → fase 4b (quién entra · por dónde se entra · las defensas decididas)",
}


def _norm(t: str) -> list[str]:
    return [re.sub(r"\s+", " ", l).strip() for l in t.splitlines() if l.strip()]


def frontmatter(txt: str) -> dict[str, str]:
    """Las claves del frontmatter (`---` … `---` al principio), en minúsculas y sin comillas.

    Lo justo de YAML para leer una firma: comentarios (`# …`, también en línea, como trae la
    plantilla del PRD), el valor plegado (`clave: >` con las líneas sangradas debajo), el valor en
    la línea siguiente o en lista (`- Ana Ruiz`), y las comillas antes que el comentario
    (`"Ana #2 Ruiz"` es Ana #2 Ruiz).
    """
    m = re.match(r"﻿?\s*---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", txt, re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    plegada = None
    for l in m.group(1).splitlines():
        if plegada and (l[:1] in (" ", "\t") or not l.strip()):
            trozo = re.sub(r"^-\s+", "", l.strip())
            out[plegada] = f"{out[plegada]} {trozo}".strip()
            continue
        plegada = None
        if l.lstrip().startswith("#") or ":" not in l:
            continue
        k, v = l.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        q = re.match(r"""^(["'])(.*?)\1""", v)
        v = q.group(2).strip() if q else re.sub(r"\s+#.*$", "", v).strip()
        if v in (">", "|", ">-", "|-", ">+", "|+", ""):
            out[k], plegada = "", k
            continue
        out[k] = v
    return out


def _firma_vacia(s: str) -> bool:
    """«—», «-», «?», «n/a», «x»… no son nadie."""
    s = re.sub(r"[\s*_`.\-—–·…?¿!\"']+", " ", s).strip().lower()
    return not re.search(r"[a-záéíóúñ0-9]", s) or s in {"n/a", "na", "x", "xx", "ninguno", "no",
                                                          "null", "none", "nil"}


def es_agente(firmante: str) -> bool:
    """¿El firmante es un agente o un modelo, y no una persona?

    Se mira la CABEZA de la firma, lo que va antes del primer «—», «(», «,» o «;»: lo de detrás es
    el contexto. «Miller (revisión con el agente de stack)» lo firma Miller; «Tech Lead (agente) ·
    borrador…», el agente (verificador de la 2.17).
    """
    s = AYUDA.sub("", firmante).strip()
    cabeza = re.split(r"\s+[—–-]\s+|\s*[(,;·]", s, maxsplit=1)[0].strip() or s
    if FIRMA_AGENTE.search(NOMBRE_Y_CLAUDE.sub(" ", cabeza)):
        return True
    sin_rol = TECH_LEAD.sub(" ", cabeza)
    generico = (FIRMA_GENERICA.match(cabeza) or TECH_LEAD.search(cabeza)
                or SESION_AGENTE.search(cabeza))
    return bool(generico) and not PERSONA.search(SESION_AGENTE.sub(" ", sin_rol))


def revisa_firma(txt: str) -> tuple[str | None, dict]:
    """(motivo del rechazo o None, lo medido). La firma sale del frontmatter y tiene que ser de
    verdad: una fecha que existe y no es futura, y una persona que no es la que lo escribió."""
    fm = frontmatter(txt)
    if not fm:
        return ("sin firmar: no hay frontmatter (`---` al principio) con `reviewed:` y "
                "`reviewed_by:` — un documento que nadie firma no obliga a nadie"), {}
    clave_f = next((k for k in CLAVES_FECHA if k in fm), None)
    clave_q = next((k for k in CLAVES_FIRMANTE if k in fm), None)
    if clave_f is None:
        return "sin firmar: falta la fecha `reviewed:` en el frontmatter", {}
    valor = fm[clave_f]
    m = re.match(r"(\d{4}-\d{2}-\d{2})(?!\d)", valor)        # «2026-10-01T10:00» vale
    try:
        fecha = datetime.date.fromisoformat(m.group(1)) if m else None
    except ValueError:
        fecha = None
    if fecha is None:
        return f"sin firmar: `{clave_f}: {valor or '(vacío)'}` no es una fecha que exista", {}
    if fecha > datetime.date.today():
        return f"sin firmar: `{clave_f}: {valor}` es una fecha futura — nadie firma mañana", {}
    medido = {"reviewed": fecha.isoformat()}
    if clave_q is None:
        return "sin firmar: falta `reviewed_by:` (quién lo revisó) en el frontmatter", medido
    quien = fm[clave_q]
    if _firma_vacia(quien):
        return f"sin firmar: `{clave_q}:` está vacío — falta quién lo revisó", medido
    if FIRMA_RELLENO.search(quien):
        return f"sin firmar: «{quien}» en `{clave_q}:` no es quién lo revisó", medido
    if es_agente(quien):
        return (f"sin firmar: «{quien}» en `{clave_q}:` es un agente — firma la persona que lo "
                "revisó, no quien lo escribió (añade `reviewed_by:` con su nombre)"), medido
    medido["reviewed_by"] = quien
    medido["firma_en"] = clave_q
    return None, medido


# ── El stack ELEGIDO, no el que se miró y se descartó (MO-61) ────────────────────────────────────
# En fitapp, quitando «Postgres» de 05-stack.md la fase seguía en verde: la regex de «base de datos»
# casaba con «Mongo», que solo aparecía en «Única, sin Mongo» y en la columna «Alternativas
# miradas». Se quitan las secciones y columnas de alternativas, el ~~tachado~~ y la mención negada.
# Lo que se miró y NO se eligió. Una COLUMNA o una LÍNEA sale si EMPIEZA por la palabra
# («Alternativas miradas», «- Descartado: MongoDB»); un ENCABEZADO, también si la dice en cualquier
# sitio («## Opciones descartadas», «## Por qué descartamos MongoDB»). Y nunca si dice lo que SÍ se
# eligió: «## Stack elegido y alternativas descartadas», «## Alternativas y decisión final» o la
# columna «Decisión (vs. alternativas)» son lo elegido (verificadores de la 2.17).
EMPIEZA_ALTERNATIVA = re.compile(
    r"^\W*(alternativas?|opciones (descartad|mirad|considerad)\w*|descartad\w*|rechazad\w*|"
    r"desechad\w*|descartamos|rechazamos|desechamos|no elegid\w*|por qu[ée] no|"
    r"en (vez|lugar) de)\b", re.I)
DICE_DESCARTE = re.compile(
    r"descartad|descartamos|rechazad|desechad|no eleg|por qu[ée] (no|descart)", re.I)
ELEGIDO = re.compile(r"\belegid|\bdecisi[óo]n|\belecci[óo]n|\bfinal\b", re.I)
# Una LÍNEA que empieza por lo descartado lo pierde hasta el final de SU cláusula, no entera: un
# «.» o un «;» con espacio detrás («16.2» o «Node.js» no cortan), o una coma, unos dos puntos, una
# raya o una «y» antes de lo que se elige («usamos», «nos quedamos con», «se usa»), o el paréntesis
# con el que empieza. «Descartado MongoDB; usamos PostgreSQL», «Descartado Mongo: usaremos
# PostgreSQL» y «Rechazadas MongoDB y MySQL. Base: SQLite» declaran la base. Y en «En lugar de
# MongoDB usamos PostgreSQL» no se quita nada: lo descartado es solo el nombre de detrás, y eso ya
# lo niega NIEGA (tercera pasada del verificador de la 2.17: se borraba la línea entera).
# Una lista ABIERTA con dos puntos no se cierra con el «;», que ahí separa sus elementos
# («Descartadas: MongoDB por el esquema; también MySQL, por la licencia»), y sin los dos puntos
# sigue si el trozo de después lo dice («; también MySQL», «; 2) MySQL»). Tras el «.» no: en
# «Rechazado: Kubernetes. PostgreSQL en Docker» lo de después es lo elegido (verificadores de M-1).
# Límites: otra coma no cierra la cláusula, porque también separa la lista de lo descartado; con los
# dos puntos, lo elegido tras un «;» tiene que decirse («; elegida PostgreSQL», «; usamos…»), y una
# lista partida con puntos («Descartados: MongoDB por X. MySQL por Y») solo pierde su primer trozo.
SUSTITUYE = re.compile(r"^\W*en (vez|lugar) de\b", re.I)
_ELIGE = (r"(?:(?:así que|por eso|por lo que|pero|y)[ \t]+)?(?:nos[ \t]+)?"
          r"(?:us|utiliz|emple|eleg|elij|opt|prefer|apost|despleg|mont|qued|v)\w*"
          r"(?:amos|emos|imos)\b"
          r"|se[ \t]+(?:us|utiliz|emple|elig|eleg|opt|prefier|despliega|monta|queda)\w*"
          r"|(?:la|el)[ \t]+(?:base(?:[ \t]+de[ \t]+datos)?|bd|despliegue|backend|frontend|"
          r"lenguaje|framework)[ \t]+(?:es|será|va|irá)\b")
FIN_CLAUSULA = re.compile(
    rf"[.;](?=\s|\Z)|(?:[,:]|[ \t]+[—–-]|[ \t]+y)(?=[ \t]+(?:{_ELIGE}))", re.I)
SIGUE_LISTA = re.compile(r"[ \t]*(?:también|tampoco|y|e|ni|\d+[.)]|[a-z]\))(?=[ \t])", re.I)
ELIGE_TRAS = re.compile(rf"[ \t]+(?:{_ELIGE})", re.I)     # «…; usamos PostgreSQL» cierra la lista
# Una etiqueta sola («Descartadas:», «**Alternativas miradas:**») deja fuera las viñetas de debajo.
ETIQUETA_DESCARTE = re.compile(EMPIEZA_ALTERNATIVA.pattern + r"[\w \t]*:[*_\s]*$", re.I)
VINETA = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
# PEGADA a la mención (como mucho un artículo y un infinitivo en medio): «sin Mongo», «no usamos
# MongoDB», «en vez de la nube», «se ha descartado usar MongoDB». Con dos palabras de holgura se
# comía lo que venía detrás: «En lugar de MongoDB usamos PostgreSQL» dejaba sin base de datos, y «no
# relacional MongoDB», también.
# Y lo coordinado comparte la negación: «Descartamos MySQL y MongoDB», «por decidir (MongoDB o
# MySQL)» niegan las dos (hasta cuatro nombres seguidos). Con comas, solo si la lista se cierra con
# una conjunción (COMA_FINAL, más abajo): en «En vez de Mongo, Postgres» o «No hay MongoDB,
# PostgreSQL sí» lo de después de la coma es lo elegido.
# El punto solo DENTRO del nombre («Node.js», «16.2»): con «Docker.» la lista cruzaba a la frase
# siguiente.
_NOMBRE = r"[\w+#-]+(?:\.[\w+#-]+)*"
_Y = r"(?:[ \t]*,[ \t]*|[ \t]+(?:y|e|o|u|ni)[ \t]+)"
_ENLACE = (r"[ \t]*(?:(?:la[ \t]+)?(?:base(?:[ \t]+de[ \t]+datos)?|bd)[ \t]*)?"
           r"[(:]?[ \t]*(?:entre[ \t]+)?(?:(?:el|la|los|las|un|una)[ \t]+)?"
           r"(?:(?:usar|utilizar|emplear|montar|meter|tener|incluir|elegir)[ \t]+)?")
# La palabra que niega acaba en límite de palabra: sin él, «MongoDB descartado, PostgreSQL» leía
# «descarta» + «do» y negaba PostgreSQL, y «Node, PostgreSQL», «no» + «de» (segundo verificador).
NIEGA = re.compile(
    r"\b(?:sin|no|ni|nada de|salvo|excepto|evitamos|en vez de|en lugar de|frente a|antes que|"
    r"mejor que|descart\w*|rechaz\w*|desech\w*|qued\w*[ \t]+fuera|"
    # sin decidir: «por decidir», «por definir», «a elegir entre», «dudamos entre», «TBD»,
    # «pendiente», «no hemos elegido», «aún no está decidida» (tercer verificador: daban la base
    # por elegida)
    r"(?:por|sin|a)[ \t]+(?:decidir|definir|confirmar|elegir)|pendiente(?:[ \t]+de[ \t]+decidir)?|"
    r"dudamos|tbd|no[ \t]+(?:(?:hemos|est[áa])[ \t]+)?(?:decidid|elegid)\w*|"
    r"no[ \t]+(?:se[ \t]+)?(?:(?:vamos|van?)[ \t]+a[ \t]+)?"
    r"(?:us|utiliz|emple|eleg|elig|necesit|hay|habr|llev|ten|tien|inclu)\w*)\b"
    rf"{_ENLACE}(?:{_NOMBRE}{_Y}){{0,4}}"
    # sin cruzar línea, y con \Z: «$» también casa antes del salto final («descartadas\n»)
    r"\Z", re.I)
# Detrás: «MongoDB (descartado)», «MongoDB, descartado por coste», «MongoDB no se usa», «MongoDB
# queda fuera», «MongoDB (no)» — pero no «PostgreSQL (descartados MySQL y MongoDB)»: ahí lo
# descartado es lo que viene detrás. Y detrás de una LISTA, con el verbo en plural: «MongoDB y MySQL
# descartados», «MongoDB, MySQL y SQLite: descartados», «MongoDB y MySQL se descartan» niegan
# todas; «Django, PostgreSQL y Docker, descartado Kubernetes», ninguna. La lista va como en
# castellano, comas y una sola conjunción al final: en «Elegidas PostgreSQL y Redis, MongoDB y MySQL
# descartadas» la coma abre otra lista y PostgreSQL queda elegida. Sin cruzar un punto: en
# «PostgreSQL. No usamos MongoDB» lo negado es MongoDB (tercera pasada del verificador de la 2.17).
_PAUSA = r"[^\w.;!?\n]{0,3}"
_CUANTO = r"(?:ambas|ambos|todas|todos|las dos|los dos)\b"   # «MongoDB y MySQL, ambas descartadas»
_NO_CUANTO = rf"(?!{_CUANTO})"
TRAS_NIEGA = re.compile(
    rf"^(?P<lista>(?:[ \t]*,[ \t]*{_NO_CUANTO}{_NOMBRE}){{0,3}}"
    rf"(?:[ \t]+(?:y|e|o|u|ni)[ \t]+{_NOMBRE})?)"
    rf"{_PAUSA}(?:{_CUANTO}[ \t]+)?(?P<verbo>"
    r"(?:(?:qued\w*|fue|fueron|est[áa]n?|son|es|(?:se[ \t]+)?han?(?:[ \t]+(?:sido|quedado))?)"
    r"[ \t]+)?(?:descartad|rechazad|desechad)[oa]s?\b"
    r"|se[ \t]+(?:descart|rechaz|desech)\w*"
    r"|no[ \t]+(?:se|l[oa]s?)[ \t]+(?:van?[ \t]+a[ \t]+)?(?:us|utiliz|emple|necesit|inclu)\w*"
    r"|(?:ya[ \t]+)?no[ \t]+(?:es|son)[ \t]+(?:una[ \t]+)?opci[óo]n(?:es)?\b"
    r"|no[ \t]+hacen?[ \t]+falta\b"
    r"|(?:a|por|sin)[ \t]+(?:decidir|definir|confirmar|elegir)\b|tbd\b"
    # «(pendiente)», «pendiente de decidir»; no «PostgreSQL, pendiente de migrar a la 16»
    r"|pendientes?(?:[ \t]+de[ \t]+(?:decidir|elegir|definir|confirmar))?(?![ \t]*\w)"
    r"|(?:han?[ \t]+)?(?:se[ \t]+)?qued\w*[ \t]+fuera\b"
    r"|no\b(?![ \t]*\w))"
    # y si detrás viene un nombre o un artículo, lo descartado es eso: «Docker, queda fuera
    # Kubernetes», «PostgreSQL (descartados MySQL y MongoDB)»
    r"(?!\s+(?:(?-i:[A-ZÁÉÍÓÚ])|y\b|las?\b|los\b|el\b|otr))", re.I)
PLURAL = re.compile(r"(?:[oa]s|[ae]n|aron|ar[áa]n)\b|\bson\b|opciones|^no$|"
                    r"decidir|definir|confirmar|elegir|pendiente|tbd", re.I)   # sin número
# Tras una negación, una lista con comas solo coordina si se cierra con una conjunción: «No usamos
# MySQL, MongoDB ni SQLite» niega las tres; «No hay MongoDB, PostgreSQL sí», solo MongoDB.
COMA_FINAL = re.compile(r",[ \t]*\Z")
CIERRA_DETRAS = re.compile(rf"(?:[ \t]*,[ \t]*{_NOMBRE})*[ \t]+(?:y|e|o|u|ni)[ \t]+{_NOMBRE}", re.I)
# ...salvo que ya estuviera cerrada antes de la coma: «Sin MongoDB ni MySQL, PostgreSQL y Redis».
CERRADA = re.compile(r"[ \t]+(?:y|e|o|u|ni)[ \t]+[^,]*,[ \t]*\Z", re.I)
PARTICIPIO = re.compile(r"(?:descartad|rechazad|desechad)\w*|no[ \t]+se\b", re.I)
POSPUESTA = re.compile(r"(?:(?-i:[A-ZÁÉÍÓÚ])[\w.+#-]*|postgres\w*|mysql|mariadb|sqlite|mongo\w*)"
                       r"[ \t]*,?[ \t]*\Z", re.I)
Y_ANTES = re.compile(r"[ \t]+(?:y|e|o|u|ni)[ \t]+\Z", re.I)    # «… y Docker»: cierra una lista
FIN = r"(?![a-záéíóúñ])"   # «Python3», «SQLite3», «Postgres16», «Vue3», «Node20» cuentan
SIN_BD = re.compile(r"\bsin base de datos\b|\bno (usa|lleva|tiene|necesita) base de datos\b", re.I)
STACK = (
    ("lenguaje", r"\b(python|javascript|typescript|node(?:\.?js)?|golang|go(?![-a-záéíóúñ])|ruby|"
                 r"php|java|kotlin|rust)" + FIN),
    ("framework", r"\b(django|fastapi|flask|react|vue|next(?:\.?js)?|nuxt|svelte(?:kit)?|rails|"
                  r"laravel|express|nestjs|spring|wordpress)" + FIN),
    ("base de datos", r"\b(postgres(?:ql)?|mysql|mariadb|sqlite|mongo(?:db)?)" + FIN),
    ("despliegue", r"\b(docker|vps|cloud\w*|aws|gcp|azure|coolify|on-?premise|kubernetes|k8s)"
                   + FIN),
)


def texto_elegido(txt: str) -> str:
    """El documento sin lo que se miró y no se eligió (mismas líneas, para no mover nada)."""
    out, nivel_fuera, cols_fuera, vinetas_fuera = [], None, None, False
    for l in txt.splitlines():
        h = re.match(r"^(#{1,6})\s+(.*)$", l)
        if h:
            n = len(h.group(1))
            if nivel_fuera is not None and n <= nivel_fuera:
                nivel_fuera = None
            titulo = h.group(2)
            if nivel_fuera is None and not ELEGIDO.search(titulo) \
               and (EMPIEZA_ALTERNATIVA.match(titulo) or DICE_DESCARTE.search(titulo)):
                nivel_fuera = n
            cols_fuera = None
            out.append("" if nivel_fuera else l)
        elif nivel_fuera is not None:
            out.append("")
        elif l.lstrip().startswith("|"):
            celdas = l.strip().strip("|").split("|")
            if cols_fuera is None:                     # la cabecera de la tabla
                cols_fuera = {i for i, c in enumerate(celdas)
                              if EMPIEZA_ALTERNATIVA.match(c) and not ELEGIDO.search(c)}
            else:
                celdas = ["" if i in cols_fuera else c for i, c in enumerate(celdas)]
            out.append("|" + "|".join(celdas) + "|")
        elif vinetas_fuera and VINETA.match(l):
            out.append("")
        else:
            cols_fuera = None
            vinetas_fuera = bool(ETIQUETA_DESCARTE.match(l)) and not ELEGIDO.search(l)
            out.append(_sin_lo_descartado(l))
    return re.sub(r"~~.*?~~", "", "\n".join(out))


def _sin_lo_descartado(linea: str) -> str:
    """La línea sin la cláusula descartada con la que empieza, si empieza por una."""
    m = EMPIEZA_ALTERNATIVA.match(linea)
    if not m or SUSTITUYE.match(linea):
        return linea
    if linea.lstrip().startswith("("):                 # «(Descartado MongoDB) PostgreSQL 16»
        cierre = linea.find(")")
        corte = cierre + 1 if cierre >= 0 else len(linea)
    else:
        # «Descartadas: A por X; B por Y», y en plural sin los dos puntos: «Descartados A, …; B, …»
        abierta = linea[m.end():].lstrip().startswith(":") or m.group(1).lower().endswith("s")
        corte, pos = len(linea), m.end()
        while fin := FIN_CLAUSULA.search(linea, pos):
            pos = fin.end()
            sigue = re.split(r"[.;](?=\s|\Z)", linea[pos:], maxsplit=1)[0]
            if fin.group() == ";" and (abierta or SIGUE_LISTA.match(linea, pos)) \
               and not ELEGIDO.search(sigue) and not ELIGE_TRAS.match(linea, pos):
                continue
            corte = pos
            break
    return linea if ELEGIDO.search(linea[:corte]) else linea[corte:]


def _negada_detras(tras: str, cierra_lista: bool = False) -> bool:
    """¿Lo que sigue a la mención la niega? Detrás de una lista, solo un verbo en plural; y si la
    mención ya cerraba una con «y», la coma de detrás abre otra lista, no sigue esta."""
    m = TRAS_NIEGA.match(tras)
    # la guarda de TRAS_NIEGA, también en minúsculas: en «postgres y redis, descartados mongo» o
    # «Docker, descartado kubernetes» lo descartado es lo de detrás
    if not m or any(re.match(r"[ \t]+" + rx, tras[m.end():], re.I) for _, rx in STACK):
        return False
    lista = m.group("lista")
    if not lista:
        return True
    if cierra_lista and lista.lstrip().startswith(","):
        return False
    return bool(PLURAL.search(m.group("verbo")))


def _declarado(rx: str, txt: str) -> bool:
    """¿Alguna mención que no esté negada ni marcada como descartada?"""
    for m in re.finditer(rx, txt, re.I):
        cierra = bool(Y_ANTES.search(txt[max(0, m.start() - 6):m.start()]))
        ini = max(0, m.start() - 120)
        niega = NIEGA.search(txt[ini:m.start()])
        if niega and COMA_FINAL.search(niega.group()) and (
                not CIERRA_DETRAS.match(txt, m.end()) or CERRADA.search(niega.group())):
            niega = None
        # «MongoDB y MySQL descartadas: PostgreSQL» — el participio va DETRÁS de lo descartado y los
        # dos puntos presentan lo elegido (tercer verificador)
        if niega and ":" in niega.group() and PARTICIPIO.match(niega.group()) \
           and POSPUESTA.search(txt[ini:ini + niega.start()]):
            niega = None
        if niega or _negada_detras(txt[m.end():m.end() + 80], cierra):
            continue
        return True
    return False


def _ratio_plantilla(txt: str, tpl: pathlib.Path | None) -> float | None:
    """Qué fracción de las líneas del documento son idénticas a las de su plantilla.

    Es la regla que `gate_datos_salud.py` no tenía y la que caza el fraude real: copiar el molde,
    cambiar el título y dejarlo. Ni el suelo de tamaño ni la búsqueda de huecos ven eso.
    """
    if tpl is None or not tpl.exists():
        return None
    try:
        base = set(_norm(tpl.read_text(encoding="utf-8", errors="replace")))
    except OSError:
        return None
    lineas = _norm(txt)
    if not lineas:
        return 1.0
    return sum(1 for l in lineas if l in base) / len(lineas)


def _extra(check: str, txt: str, ruta: str) -> tuple[str, str]:
    """Las comprobaciones de estructura por tipo de documento."""
    if check == "normativo":
        n = len(NORMATIVE.findall(txt))
        return (CUMPLE, f"{n} verbos normativos") if n else \
               (NO_CUMPLE, "ningún DEBE/DEBERÁ/SHALL/MUST: sin verbo normativo no hay contrato, "
                           "hay un deseo (la tanda R.1 lo pregunta a propósito)")
    if check == "gherkin":
        if not ACCEPT.search(txt):
            return NO_CUMPLE, "sin criterios de aceptación ni un solo «Dado que»"
        trios = len(re.findall(r"dado que[\s\S]{0,600}?cuando[\s\S]{0,600}?entonces", txt, re.I))
        return (CUMPLE, f"{trios} criterios completos") if trios else \
               (NO_CUMPLE, "hay «Dado que» pero ningún trío completo Dado/Cuando/Entonces")
    if check == "estado_final":
        if re.search(r"m[áa]quina de estados", txt, re.I) and not ESTADO_FINAL.search(txt):
            return NO_CUMPLE, ("hay máquina de estados y ningún estado FINAL: el trabajo no puede "
                               "terminar nunca, y eso es un fallo de diseño, no de redacción")
        return CUMPLE, "con estado final"
    if check == "metrica":
        return (CUMPLE, "métrica con valor") if re.search(r"\d", txt) and \
            re.search(r"m[ée]trica|kpi|objetivo", txt, re.I) else \
            (NO_CUMPLE, "sin ninguna métrica con su valor de hoy: «lo sabremos cuando lo veamos» "
                        "no es un criterio de éxito")
    if check == "personal":
        try:
            d = json.loads(txt)
        except json.JSONDecodeError as e:
            return NO_MEDIBLE, f"no es JSON válido ({e.msg} en la línea {e.lineno})"
        ents = d.get("entidades") or []
        if not ents:
            return NO_CUMPLE, "sin entidades declaradas"
        sin = [f"{e.get('nombre','?')}.{c.get('nombre','?')}"
               for e in ents for c in (e.get("campos") or []) if "personal" not in c]
        if sin:
            return (NO_CUMPLE, f"{len(sin)} campos sin `personal: true|false` "
                               f"({', '.join(sin[:4])}{'…' if len(sin) > 4 else ''}) — ese campo es "
                               "el que hace que la fase 4 se derive en vez de volver a preguntarse")

        # La FUENTE DE VERDAD. Se exige por el mismo camino que `personal` porque es el mismo tipo de
        # fallo: un dato sin fuente declarada no falla al escribirlo, falla meses despues cuando dos
        # sitios discrepan y arreglar el sintoma lo devuelve en la siguiente sincronizacion.
        # Caso medido (elvion, 2026-08): el precio vivia en tres sitios sin fuente declarada y el
        # cociente padre/variacion era 0,7196 CONSTANTE en 476 productos — un valor derivado que
        # alguien calculo una vez y que se servia como real. 31 de 50 fallos de conversacion.
        # Peticion del Usuario del 2026-09-17: que esta pregunta este en el proceso, no en la memoria
        # de quien lo monte.
        VALIDAS = {"propia", "externa", "derivada"}
        MIN_DETALLE = 10          # "x" no es un detalle; "WooCommerce del comercio" si

        malas, sin_detalle = [], []
        for e in ents:
            nom = e.get("nombre", "?")
            f = (e.get("fuente") or "").strip().lower()
            if f not in VALIDAS:
                malas.append(nom)
            elif f != "propia" and len((e.get("fuente_detalle") or "").strip()) < MIN_DETALLE:
                sin_detalle.append(nom)
            # Un campo puede declarar una fuente DISTINTA de la de su entidad (el precio derivado
            # del padre es justo ese caso). Si la declara, tambien tiene que decir de donde.
            for c in (e.get("campos") or []):
                cf = (c.get("fuente") or "").strip().lower()
                if not cf:
                    continue
                etq = f"{nom}.{c.get('nombre','?')}"
                if cf not in VALIDAS:
                    malas.append(etq)
                elif cf != "propia" and len((c.get("fuente_detalle") or "").strip()) < MIN_DETALLE:
                    sin_detalle.append(etq)

        if malas:
            return (NO_CUMPLE,
                    f"{len(malas)} sin `fuente: propia|externa|derivada` "
                    f"({', '.join(malas[:4])}{'…' if len(malas) > 4 else ''}) — un dato sin fuente "
                    "declarada no es un dato, es una discusion pendiente")
        if sin_detalle:
            return (NO_CUMPLE,
                    f"{len(sin_detalle)} declaran fuente externa o derivada y no dicen DE QUE "
                    f"({', '.join(sin_detalle[:4])}{'…' if len(sin_detalle) > 4 else ''}) — "
                    "`fuente_detalle` con el sistema o el campo concreto")

        # Tanda 2.5 (3.52, NE-9): si el producto escribe por iniciativa propia, consentimiento,
        # exclusión y exposición con control nacen en el diseño (patterns/stack/campaigns.md).
        # Elvion lo descubrió con las campañas ya hechas y su envío real sigue en simulación.
        mp = d.get("mensajes_propios")
        if not isinstance(mp, bool):
            return (NO_CUMPLE, "sin `mensajes_propios: true|false` (tanda 2.5): ¿el producto mandará "
                               "mensajes a clientes sin que ellos empiecen la conversación?")
        if mp:
            patrones = {(e.get("patron") or "").strip().upper() for e in ents}
            faltan = [p for p in ("D-1", "D-2", "D-6") if p not in patrones]
            if faltan:
                return (NO_CUMPLE, f"`mensajes_propios: true` sin las entidades {', '.join(faltan)} "
                                   "(`\"patron\"`; consentimiento, exclusión y exposición con control de "
                                   "patterns/stack/campaigns.md): añadirlas con envíos ya hechos obliga a "
                                   "tirar el historial")

        derivadas = sum(1 for e in ents if (e.get("fuente") or "").lower() != "propia")
        return (CUMPLE, f"{len(ents)} entidades, todos los campos clasificados, "
                        f"{derivadas} con fuente de fuera o derivada y su origen dicho"
                        + (", y las tablas de mensajes propios (D-1, D-2, D-6)" if mp else ""))
    if check == "stack_completo":
        # Solo cuenta lo ELEGIDO (texto_elegido) y lo que no va negado (_declarado). Y con límites
        # de palabra: antes «go» casaba dentro de «Django», «algo» o «luego», así que el lenguaje
        # salía declarado en cualquier documento en castellano.
        elegido = texto_elegido(txt)
        falta = [q for q, rx in STACK
                 if not (_declarado(rx, elegido)
                         or (q == "base de datos" and SIN_BD.search(elegido)))]
        return (CUMPLE, "lenguaje, framework, datos y despliegue declarados") if not falta else \
               (NO_CUMPLE, "sin declarar en el stack elegido: " + ", ".join(falta) +
                " (lo que va en alternativas, tachado o negado —«sin Mongo»— no cuenta)")
    if check == "defensas":
        # El mínimo de `rules/security.md` §autenticación web, que sale del incidente medido del
        # 2026-09-11: entraron por la puerta buena con una contraseña válida, 258 IPs distintas
        # contra wp-login en 14 días. Se exige que cada defensa esté DECIDIDA por escrito —a favor
        # o en contra con su razón—, no que esté implementada: eso lo comprueba sofia atacando.
        minimo = {
            "2fa":         r"2fa|doble factor|segundo factor|mfa|totp|autenticaci[óo]n en dos",
            "intentos":    r"l[íi]mite de intentos|bloqueo de cuenta|fuerza bruta|rate.?limit|"
                           r"intentos fallidos|lockout",
            "exposicion":  r"0\.0\.0\.0|127\.0\.0\.1|proxy inverso|nginx|t[úu]nel|no se publica|"
                           r"puerto|expone",
            "logs":        r"logs?|registr[oa]|auditor[íi]a|traza",
        }
        falta = [k for k, rx in minimo.items() if not re.search(rx, txt, re.I)]
        if falta:
            return NO_CUMPLE, ("sin decidir: " + ", ".join(falta) + " — cada una se decide por "
                               "escrito (a favor o en contra con su razón). Una defensa que nadie "
                               "decidió no es una que se descartó: es una que nadie miró")
        # Un documento que promete robustez SOLO con límite por IP promete lo que el dato no sostiene.
        if re.search(r"l[íi]mite por ip|fail2ban|limit_req", txt, re.I) and \
           not re.search(r"2fa|doble factor|mfa|totp", txt, re.I):
            return NO_CUMPLE, ("confía la defensa del login al límite por IP y no menciona 2FA — "
                               "el ataque medido venía de 258 IPs para 406 intentos, diseñado para "
                               "quedar bajo cualquier umbral por IP. Eso mitiga; no resuelve")
        return CUMPLE, "las 4 defensas del mínimo, decididas"

    if check == "base_legal":
        if not re.search(r"datos personales", txt, re.I):
            return NO_CUMPLE, "no dice ni si trata datos personales"
        # `\btrata\b` NO casaba con «Tratamos datos personales», que es como se escribe en
        # castellano — así que un documento sin base legal PASABA. Lo cazó el sabotaje S-11.
        if re.search(r"\bs[íi]\b|\btrata\w*\b|\brecoge\w*\b|\bguarda\w*\b|"
                     r"\balmacena\w*\b|\bmaneja\w*\b", txt, re.I) and not re.search(
                r"consentimiento|contrato|obligaci[óo]n legal|inter[ée]s leg[íi]timo|"
                r"misi[óo]n de inter[ée]s|intereses vitales", txt, re.I):
            return NO_CUMPLE, "declara datos personales y ninguna base legal del art. 6"
        return CUMPLE, "con base legal declarada"
    return NO_MEDIBLE, f"comprobación desconocida: {check}"


def revisa_doc(raiz: pathlib.Path, plan: pathlib.Path, doc) -> dict:
    did, rel, tpl_rel, minimo, extras = doc
    p = plan / rel
    r = {"id": did, "file": str(p.relative_to(raiz)) if p.is_relative_to(raiz) else str(p)}

    if not p.exists():
        return {**r, "estado": NO_CUMPLE, "por_que": f"no existe {rel}"}
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        # No es lo mismo que falte a que no se pueda leer. Colapsarlos destruye el diagnóstico.
        return {**r, "estado": NO_MEDIBLE, "por_que": f"existe y no se puede leer: {e}"}

    n = len(txt.encode("utf-8"))
    r["medido"] = {"bytes": n}
    if n < minimo:
        return {**r, "estado": NO_CUMPLE,
                "por_que": f"{n} B (mínimo {minimo}) — es un esqueleto, no un documento"}

    huecos = [h if isinstance(h, str) else h[0] for h in HUECOS.findall(txt)] + MARCAS.findall(txt)
    if huecos:
        return {**r, "estado": NO_CUMPLE,
                "por_que": f"{len(huecos)} hueco(s) sin rellenar: {', '.join(huecos[:4])}"}

    ratio = _ratio_plantilla(txt, (raiz / tpl_rel) if tpl_rel else None)
    if ratio is not None:
        r["medido"]["solapamiento_plantilla"] = round(ratio, 2)
        if ratio >= RATIO_PLANTILLA:
            return {**r, "estado": NO_CUMPLE,
                    "por_que": f"el {ratio:.0%} de sus líneas son idénticas a {tpl_rel} — "
                               "es la plantilla con el título cambiado"}

    for check in extras:
        est, det = _extra(check, txt, rel)
        if est != CUMPLE:
            return {**r, "estado": est, "por_que": det}
        r.setdefault("detalle", []).append(det)

    # Un fichero de DATOS no se firma: la firma va en el documento legible que lo acompaña
    # (`03-modelo-datos.md` para `entidades.json`). Exigir frontmatter `reviewed:` dentro de un
    # JSON suspendía un dataset perfectamente válido — lo cazó el control negativo N-03, y de
    # paso enmascaraba el S-09: el JSON roto fallaba por «sin firmar» en vez de por «no medible».
    if p.suffix == ".json":
        return {**r, "estado": CUMPLE}

    motivo, firma = revisa_firma(txt)
    r["medido"].update(firma)
    if motivo:
        return {**r, "estado": NO_CUMPLE, "por_que": motivo}
    # Aviso, no bloqueo: el propio documento dice que el Usuario no lo ha confirmado y a la vez
    # lleva firma. En fitapp pasa en 4 de 7 (campo viejo que nadie actualizó tras la firma); si
    # bloqueara, el gate se degradaría por ruido, que es justo lo que MO-61 quiere evitar.
    if frontmatter(txt).get("confirmado_por_usuario", "").lower() in {"no", "false", "pendiente"}:
        r["avisos"] = ["el frontmatter dice `confirmado_por_usuario: no` y el documento está "
                       "firmado: una de las dos cosas es falsa — corrige la que no lo sea"]
    return {**r, "estado": CUMPLE}


def _arranque_empezado(d: pathlib.Path) -> bool:
    """¿Hay un arranque EN CURSO aquí, o solo una carpeta que dejó un generador?

    La diferencia importa mucho y se vio en pantalla: `gen_trazas.py` y `gen_modelo_datos.py`
    escriben una SEMILLA en `arranque/` cuando no encuentran datos. Eso creaba la carpeta, el
    gate la tomaba por un arranque empezado, no hallaba ningún documento y pintaba las 7 fases
    en ROJO. Pero rojo significa «lo hiciste mal» y gris «no lo has hecho»: aquí lo cierto era
    lo segundo, y decir lo primero es acusar a alguien de un trabajo que nunca empezó.

    Empezado = hay al menos UN documento de verdad: un `.md` de los que produce la entrevista,
    o un `.json` al que ya le han quitado la marca `_semilla`.
    """
    a = d / "arranque"
    if not a.is_dir():
        return False
    if any(a.glob("0*.md")) or any(a.glob("1*.md")):
        return True
    for j in a.glob("*.json"):
        try:
            if '"_semilla"' not in j.read_text(encoding="utf-8", errors="replace")[:400]:
                return True
        except OSError:
            continue
    return False


def localiza_plan(raiz: pathlib.Path) -> pathlib.Path | None:
    """El plan con un arranque EMPEZADO, más reciente por nombre. Nunca por mtime: regenerar un
    informe viejo no lo convierte en el plan activo (misma regla que `tasks_registry.py`)."""
    base = raiz / ".docs" / "plans"
    if not base.is_dir():
        return None
    cands = sorted((d for d in base.iterdir() if _arranque_empezado(d)), key=lambda d: d.name)
    return cands[-1] if cands else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Gate de los documentos base de /arrancar")
    ap.add_argument("proyecto", nargs="?", default=".")
    ap.add_argument("--fase", choices=ORDEN)
    ap.add_argument("--hook", action="store_true", help="solo la PRIMERA fase que falla")
    ap.add_argument("--explica", action="store_true", help="añade cómo se arregla")
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args()

    raiz = pathlib.Path(a.proyecto).resolve()
    plan = localiza_plan(raiz)
    if plan is None:
        # Sin contexto se ABORTA. "No hay nada que comprobar" NO significa que se cumpla.
        sys.stderr.write(
            "GATE DE ARRANQUE · exit 3 — no hay ningún plan con `arranque/` en .docs/plans/.\n"
            "  Eso NO significa que el arranque esté hecho: significa que no se puede comprobar.\n"
            "  Empieza con:  /arrancar\n")
        return 3

    fases = [a.fase] if a.fase else ORDEN
    res, peor = [], CUMPLE
    for fid in fases:
        docs = [revisa_doc(raiz, plan, d) for d in FASES[fid]]
        est = (NO_CUMPLE if any(d["estado"] == NO_CUMPLE for d in docs)
               else NO_MEDIBLE if any(d["estado"] == NO_MEDIBLE for d in docs) else CUMPLE)
        res.append({"fase": fid, "estado": est, "docs": docs, "como_se_arregla": ARREGLO[fid]})
        if est == NO_CUMPLE:
            peor = NO_CUMPLE
        elif est == NO_MEDIBLE and peor == CUMPLE:
            peor = NO_MEDIBLE
        if a.hook and est != CUMPLE:
            break

    code = {CUMPLE: 0, NO_CUMPLE: 1, NO_MEDIBLE: 2}[peor]
    if a.as_json:
        print(json.dumps({"plan": str(plan.relative_to(raiz)), "veredicto": peor,
                          "exit": code, "fases": res}, ensure_ascii=False, indent=2))
        return code

    salida = sys.stderr if code else sys.stdout
    icono = {CUMPLE: "✓", NO_CUMPLE: "✗", NO_MEDIBLE: "?", NO_APLICA: "·"}
    print(f"GATE DE ARRANQUE · plan {plan.name}", file=salida)
    for f in res:
        print(f"\n  {icono[f['estado']]} FASE {f['fase'].upper()}", file=salida)
        for d in f["docs"]:
            print(f"      {icono[d['estado']]} {d['id']:11} {d.get('por_que', 'OK')}", file=salida)
            if d["estado"] == CUMPLE and d.get("medido"):
                print(f"        {d['medido']}", file=salida)
            for av in d.get("avisos", []):
                print(f"        ⚠ {av}", file=salida)
        if f["estado"] != CUMPLE and (a.explica or a.hook):
            print(f"      → cómo se arregla: {f['como_se_arregla']}", file=salida)
    if code == 0:
        print("\nOK: los documentos base están, tienen contenido propio y están firmados.\n"
              "    (esto NO dice que sean correctos — solo que existen y no son la plantilla)",
              file=salida)
    elif code == 2:
        print("\nexit 2 — hay comprobaciones que NO SE PUDIERON HACER. Eso no es un aprobado.",
              file=salida)
    return code


if __name__ == "__main__":
    sys.exit(main())
