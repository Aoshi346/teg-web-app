#!/usr/bin/env python3
"""Gate F — ¿cruza este plan una frontera de confianza? Y si la cruza, ¿está modelada?

POR QUÉ EXISTE (sub-ola 2.25, SE-19). El template no tenía modelado de amenazas: `/arrancar` 4b
pregunta por la web y `gate_arranque.py` solo mira que `07-superficie.md` exista y diga «defensas».
El Gate F de `rules/plan-gates.md` pide un modelo de UNA página (skill `modelado-amenazas`) solo
cuando el plan crea o cambia una frontera: endpoint público, subida de ficheros, webhook, tool de
agente con efecto, tenant nuevo, integración externa o datos personales nuevos. Acotarlo es lo que
impide que se vuelva un trámite (el criterio del Gate E); escrito en prosa, nadie lo comprobaba.

QUÉ COMPRUEBA, Y QUÉ NO.
  · La DETECCIÓN es léxica: en un plan, lo que se describe es lo que se va a construir, así que
    basta la mención de una frontera (también en una cabecera); se salta lo que no se construye
    (secciones «fuera de alcance» y de estado actual, la frontera negada o que ya existe —mirando
    las palabras pegadas a ella—, preguntas, filas «hecho») y en un arreglo solo cuenta la novedad
    explícita. plan.md y spec.md se leen por separado, cada uno con su título. Da CANDIDATOS con su
    línea; si se equivoca, el plan lo dice por escrito (`Gate F: no aplica — <razón>`) y el gate lo
    respeta. Nunca adivina en silencio: o hay modelo, o hay razón escrita. Medido sobre 39 planes
    reales el 2026-10-20: `_archive/2026-10-20/medicion-2.25/`.
  · El MODELO se valida en forma: fronteras con id, una fila STRIDE por frontera como mínimo,
    respuesta de las cuatro de OWASP, defensa y prueba en lo que se mitiga, **ids de ASVS 5.0.0 que
    existen** y **cartas de LINDDUN GO que existen** (un LLM inventa ambas con facilidad), y la Rule
    of Two con control cuando un agente tiene las tres propiedades. NO comprueba que la defensa sea
    buena ni que cumpla el requisito citado: eso lo hacen Sofía atacando y el auditor leyendo.

TRES DESENLACES (`rules/verification.md`): cumple · no_cumple · no_medible — y no_medible no es
verde.

    python3 .claude/scripts/gate_amenazas.py <carpeta-del-plan | plan.md>  # el Gate F
    python3 .claude/scripts/gate_amenazas.py --modelo <modelo-amenazas.md>  # solo el modelo
    python3 .claude/scripts/gate_amenazas.py --asvs L2 [--con jwt,oauth] [--extra v5.0.0-8.3.3]
    python3 .claude/scripts/gate_amenazas.py --tipo salud [--resumen]  # nivel y lista del tipo
    python3 .claude/scripts/gate_amenazas.py --autoprueba              # sabotajes y controles
    … --json

Exit: 0 cumple o no aplica · 1 no cumple · 2 no se pudo medir.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Se IMPORTAN de gate_arranque, no se recopian: el hueco de plantilla es el mismo. La firma NO: la
# de gate_arranque daba por buena una firma vacía (arreglado en la 2.17, PV-76, con estas mismas
# reglas copiadas allí); esta conserva la suya porque `mutar_gate_amenazas.py` (2.25) muta su texto.
# (Sin el solapamiento con la plantilla de gate_arranque: aquí los huecos `<…>` de la plantilla lo
# adelantan siempre, y un modelo bien rellenado conserva a propósito la prosa de la plantilla.)
from gate_arranque import (  # noqa: E402
    CUMPLE,
    HUECOS,
    MARCAS,
    NO_APLICA,
    NO_CUMPLE,
    NO_MEDIBLE,
)

CLAUDE = pathlib.Path(__file__).resolve().parent.parent
REFS = CLAUDE / "skills" / "modelado-amenazas" / "references"
ASVS_JSON = REFS / "asvs-5.0.0.json"
LINDDUN_MD = REFS / "linddun-go.md"
ASVS_TIPOS_MD = REFS / "asvs-por-tipo.md"
PLANTILLA = CLAUDE / "templates" / "modelo-amenazas.md"
NOMBRE_MODELO = "modelo-amenazas.md"

# ── Nivel ASVS por tipo de proyecto (SE-D14). La tabla legible está en
#    references/asvs-por-tipo.md y la autoprueba comprueba que dice lo mismo que esto. Los extras
#    son requisitos de un nivel superior que se suman.
L3_SALUD = [
    "8.1.3",
    "8.1.4",
    "8.2.4",
    "8.3.2",
    "8.3.3",
    "8.4.2",
    "14.2.5",
    "14.2.6",
    "14.2.7",
    "14.2.8",
    "16.5.4",
]
TIPOS = {
    "web-marketing": ("L1", []),
    "app": ("L2", []),
    "bot": ("L2", ["8.3.3"]),
    "salud": ("L2", L3_SALUD),
    "pentest": ("L2", []),
}
# El subconjunto Django + React: capítulos que casi todo proyecto de casa toca, y los que dependen
# de lo que tenga. V17 (WebRTC) solo con `--con webrtc`.
CAPITULOS_BASE = [1, 2, 3, 4, 5, 6, 7, 8, 13, 14, 15, 16]
CAPITULOS_SI = {"jwt": 9, "oauth": 10, "cripto": 11, "tls": 12, "webrtc": 17}

# ── Detección de fronteras en el plan ─────────────────────────────────────────────────────────────
# Los datos personales, UNA lista para el detector del plan y para la coherencia del modelo: con
# dos, «correo electrónico» o «datos de salud» disparaban el plan y pasaban en un modelo con
# `datos_personales: no` (verificador, 4.ª pasada; la misma lección que la O1 de la segunda).
# «paciente» va solo en el plan: un modelo sin datos personales puede hablar del paciente que
# reserva.
DATOS_PERSONALES = (
    r"datos personales|\bPII\b|\bDNI\b|\bNIF\b|tel[ée]fonos?|\be-?mails?\b|"
    r"correo electr[óo]nico|direcci[óo]n postal|datos de salud|historia cl[íi]nica|"
    r"menores de edad|biom[ée]tric|geolocalizaci|nombre y apellidos|"
    r"fecha de nacimiento|\balergi|\bmedicaci|diagn[óo]stic|\bIBAN\b|\bGPS\b|"
    r"ubicaci[óo]n (del|de la|de los) (usuarios?|clientes?|pacientes?)|"
    # «móvil» como dato, no como el aparato («se ve bien en su móvil»; verificador, 4.ª pasada).
    r"\bapellidos\b|\bn[úu]mero de m[óo]vil\b|"
    r"direcci[óo]n de (env[íi]o|entrega|facturaci[óo]n)|\bdomicilio\b|"
    r"\bmatr[íi]culas? del? (coches?|veh[íi]culos?)\b|n[úu]mero de (la )?tarjeta|"
    r"tarjetas? de (cr[ée]dito|d[ée]bito)|fotos? de (la cara|el rostro)|reconocimiento facial|"
    r"\bcurr[íi]cul"
)
FRONTERAS = {
    "endpoint_publico": r"endpoints? p[úu]blic|api p[úu]blica|ruta p[úu]blica|sin autenticar|"
    r"sin login|sin iniciar sesi[óo]n|\bAllowAny\b|acceso an[óo]nimo|formulario p[úu]blico|"
    r"public endpoint|sin autenticaci[óo]n|sin token|@csrf_exempt|permission_classes\s*=\s*\[\s*\]|"
    r"abiert[ao] (a internet|al p[úu]blico)|"
    # «sin registrarse», «no requiere login» (verificador, 3.ª pasada); «sin registrar su peso», no.
    r"sin registrarse\b|sin registro de usuarios?\b|sin darse de alta\b|"
    r"no requiere (login|registro|cuenta|autenticaci[óo]n|iniciar sesi[óo]n)",
    "ficheros": r"subida de (fichero|archivo|imagen|im[áa]genes|document|adjunt)|"
    r"\bsub(ir|e|en)\b[^.\n]{0,20}\b(fichero|archivo|imagen|document|adjunt|pdf|foto|"
    r"cv\b|curr[íi]cul)|"
    r"\bcarga(r)? de (fichero|archivo|document|foto)|\bcargar (fichero|archivo|document|foto)|"
    r"\bupload|FileField|ImageField|multipart|\badjunt(o|os|a|as|ar)\b",
    "webhook": r"webhook|url de (callback|retorno)|callback (de|del) (pago|proveedor|oauth|stripe|"
    r"redsys|paypal)|notificaci[óo]n entrante|\bIPN\b",
    "tool_efecto": r"@tool\b|ToolNode|servidor MCP|MCP server|herramientas? del agente|"
    r"function calling|\btools?\b[^.\n]{0,60}\b(escrib|crea|borr|elimin|env[íi]|cobr|pag|modific|"
    r"cancel|reserv|actualiz)|"
    # Sin la palabra «tool»: «el agente podrá cancelar pedidos» (verificador, 2.ª pasada).
    r"\b(agentes?|asistentes?|bots?|chatbots?)\b[^.\n]{0,60}\b(cancel|cobr|env[íi]|reserv|reembols|"
    r"borr|elimin|modific|emit|publica(r|n)?\b|"
    # Crear o actualizar, solo una cosa del negocio: «el asistente crea un resumen» no es un efecto,
    # «el asistente crea la cita» sí (verificador, 4.ª pasada).
    r"(crea(r|n)?|actualiza(r|n)?) (la|el|las|los|una|un|sus?) (citas?|reservas?|pedidos?|"
    r"facturas?|tickets?|eventos?|cuentas?|usuarios?|pagos?|cobros?|fichas?|clientes?|stock|"
    r"inventario|precios?|registros?|contactos?|leads?|devoluci\w*|tareas?|incidencias?)\b)",
    # Tenant NUEVO o cambio del aislamiento; no el adjetivo «multi-tenant» que describe el sistema
    # que ya existe (casaba en 6 sesiones de retrieval de elvion sin frontera nueva, 2026-10-20).
    "tenant_nuevo": r"tenants? nuevos?|nuevos? tenants?|nuevos? comercios?|comercios? nuevos?|"
    r"alta de (un )?(tenant|comercio)|"
    r"onboarding de (tenant|comercio)|"
    r"aislamiento entre (clientes|tenants|comercios|franquicias|empresas|tiendas|sedes)|"
    r"datos aislados|\baislad[oa]s? de (los|las) dem[áa]s\b|"
    r"(pasa a|hacer(lo)?|convertir(lo)? en) (ser )?multi-?tenant",
    # «integración con el frontend» o «con el resto del módulo» no es un tercero (auditor, 20-10).
    "integracion_externa": r"integraci[óo]n(es)? con(?! (el |la |los |las )?(frontend|backend|"
    r"m[óo]dulos?|panel|resto)\b)|integrar(lo|la)? con(?! (el |la )?(frontend|backend|resto)\b)|"
    r"\bintegrations?/|API (externa|de terceros|del proveedor)|\bsu API\b|sincroniz\w+ con|"
    r"\bOAuth\b|\bSSO\b|Stripe|PayPal|Redsys|"
    r"WooCommerce|Shopify|HubSpot|Pipedrive|WhatsApp|Twilio|\bCRM\b|clave de API|"
    r"proveedor externo|scraping|\braspa|\bIMAP\b|\bSMTP\b|Gmail|Microsoft Graph|"
    r"microsoft_graph|Outlook|Google (Drive|Calendar|Sheets|Workspace)|"
    r"API de (OpenAI|Anthropic|Gemini|Mistral)|proveedor (externo )?de (IA|LLM|modelos)|"
    # Login social, pasarelas y boletines que no decían «integración» (verificador, 3.ª pasada).
    r"cuenta de (Google|Microsoft|Apple|Facebook)|(login|acceso|entrar|inicio de sesi[óo]n) con "
    r"(Google|Microsoft|Apple|Facebook)|Mailchimp|Brevo|Sendinblue|Holded|Bizum|"
    r"pasarela de pago|\bTPV\b|\bAPI keys?\b|\bapi_key\b",
    "datos_personales": DATOS_PERSONALES + r"|\bpacientes?\b",
}
# Tipos cuyo patrón deja un hueco entre el sujeto y el verbo: ahí la negación va DENTRO de la
# mención («el bot NO cobra», XM-3 de musa, medido en la 3.ª pasada).
MENCION_CON_HUECO = {"tool_efecto", "ficheros"}
# En un plan, lo que se describe es lo que se va a construir: una spec dice «R4 — Webhook
# receiver: verifica firma», en presente y sin verbo de novedad. Exigir «añadir/nuevo» en la línea
# dejaba callado el Gate F en un plan de pagos con Stripe y webhook (XM-4 de musa, medido el
# 2026-10-20). Por eso basta la MENCIÓN, y se salta solo lo que NO se construye:
#   · las secciones «fuera de alcance» y las de estado actual o antecedentes;
#   · la frontera NEGADA («no se añade ningún webhook») o que describe lo que ya existe («hoy ya
#     hay un webhook»), mirando solo las palabras PEGADAS a esa frontera: con toda la cláusula,
#     «un webhook que actualiza los pedidos existentes» callaba (auditor, 20-10);
#   · la pregunta, y la cláusula que dice que algo queda fuera;
#   · el ARREGLO: en una línea —o en un plan cuyo título es un fix— solo cuenta la novedad
#     explícita («integración» o «implementación» no lo son: se arreglan también).
NOVEDAD_FUERTE = (
    r"nuev[oa]s?|añad|exp[oó]n|conect|habilit|incorpor|introduc|publica|\bmonta|\babr(e|ir)\b|"
    # Cambiar de proveedor también trae uno: «se migra el cobro a Stripe» (verificador, 3.ª pasada).
    r"\bmigra(r|n|mos)?\b|\bsustitu(ye|yen|ir|imos)\b|\breemplaz(a|an|ar|amos)\b"
)
# Rehacer, mover o partir lo que ya hay tampoco crea fronteras (verificador, 3.ª pasada); pero
# mover, partir o renombrar solo cuentan con un objeto de CÓDIGO cerca: «mover las citas desde el
# formulario público» o «partir el pago en tres plazos con Stripe» son producto (4.ª pasada).
OBJETO_CODIGO = (
    r"(?=[^.\n]{0,50}(`|\.py\b|\.tsx?\b|\.jsx?\b|\bficheros?\b|\barchivos?\b|\bm[óo]dulos?\b|"
    r"\bcarpetas?\b|\bclases?\b|\bfunci[óo]n(es)?\b|\bvistas?\b|\bviews?\b|\bapps?/))"
)
ARREGLO = (
    r"\b(arregl|corrig|corregir|fix|bugfix|hotfix|parche|refactor)|"
    r"(?:\b(?:mueve|mueven|mover|movemos|reorganiz\w*|renombr\w*)\b|(?<!a )\bpartir\b)"
    + OBJETO_CODIGO
)
NEGADORES = {"no", "sin", "ningún", "ningun", "ninguna", "ninguno", "nunca", "jamás", "jamas"}
# En un CONTROL niegan también estas (no en el plan: «falta el webhook» es trabajo por hacer).
NEGADORES_CONTROL = NEGADORES | {
    "asume",
    "supone",
    "presupone",
    "nadie",
    "falta",
    "faltan",
    "pendiente",
    "quita",
    "quitar",
    "elimina",
    "retira",
    "sustituye",
}
# Un control de la Rule of Two: `interrupt`, HITL o una sesión nueva valen solos; aprobar,
# confirmar, autorizar, validar o revisar, solo si lo hace una PERSONA. Dos formas (verificador,
# 3.ª y 4.ª pasadas): un sujeto que no es una máquina, pegado al verbo («el supervisor aprueba», «la
# enfermera confirma»; «el bot valida la petición del usuario» no), o el nombre con su persona
# detrás («confirmación del paciente», «revisión humana»; «validación del JSON del usuario» no).
HITL_FUERTE = re.compile(
    r"\binterrupt\b|\bHITL\b|\bhuman[- ]in[- ]the[- ]loop\b|"
    r"\bsesi[óo]n nueva\b|\bnueva sesi[óo]n\b",
    re.I,
)
VERBO_CONTROL = (
    r"(?:aprueba|aprueban|aprobar|apruebe|confirma|confirman|confirmar|confirme|autoriza|autorizan|"
    r"autorizar|autorice|valida|validan|validar|valide|revisa|revisan|revisar|revise|"
    r"da el visto bueno|dan el visto bueno)"
)
ACTOR = (
    r"(?:human[oa]s?|personas?|usuari[oa]s?|clientes?|gestor(?:a|es)?|operador(?:a|es)?|"
    r"encargad[oa]s?|pacientes?|comprador(?:a|es)?|responsables?|equipo|revisor(?:a|es)?|"
    r"administrador(?:a|es)?|profesional(?:es)?|m[ée]dic[oa]s?|abogad[oa]s?|dpo|dueñ[oa]s?|"
    r"titular(?:es)?|supervisor(?:a|es)?|gerentes?|jef[ea]s?|enfermer[oa]s?|alumn[oa]s?|"
    r"propietari[oa]s?|soci[oa]s?|recepcionistas?|emplead[oa]s?|trabajador(?:a|es)?|"
    r"t[ée]cnic[oa]s?|comercial(?:es)?|moderador(?:a|es)?|entrenador(?:a|es)?|monitor(?:a|es)?|"
    r"tutor(?:a|es)?|padres?|madres?|inquilin[oa]s?|vecin[oa]s?|director(?:a|es)?|"
    r"coordinador(?:a|es)?|docentes?|profesor(?:a|es)?|asesor(?:a|es)?|contables?|"
    r"auditor(?:a|es)?|farmac[ée]utic[oa]s?|veterinari[oa]s?|interesad[oa]s?|familiar(?:es)?)"
)
# Un sujeto no humano delante del verbo no hace control, aunque haya una persona en la frase.
NO_HUMANO = {
    "agente", "agentes", "subagente", "bot", "bots", "chatbot", "asistente", "asistentes",
    "modelo", "llm", "ia", "tool", "tools", "herramienta", "sistema", "servidor", "proceso",
    "script", "servicio", "api", "backend", "código", "programa", "flujo", "grafo", "workflow",
    "regla", "job", "cron", "worker", "middleware", "webhook", "json", "esquema", "validador",
    "pipeline", "motor", "plataforma", "app", "aplicación",
}  # fmt: skip
# Entre el sujeto y el verbo, esto lo deja en nada: «el usuario PUEDE revisar», «no confirma».
CLITICOS = {"lo", "la", "los", "las", "le", "les", "se"}
NO_OBLIGA = {"puede", "pueden", "podrá", "podrán", "podría", "quiere", "quieren", "suele", "no",
             "nunca", "jamás"}  # fmt: skip
SUJETO_VERBO = re.compile(
    r"\b(?:el|la|los|las|un|una)\s+(\w+)(?:\s+(\w+))?(?:\s+(?:de|del|de la|de los|de las)\s+\w+)?"
    r"\s+" + VERBO_CONTROL + r"\b",
    re.I,
)
INVERTIDO = re.compile(  # «lo aprueba la recepcionista», «el pago lo confirma la persona»
    r"\b(?:lo|la|los|las|le|les)\s+" + VERBO_CONTROL
    + r"\s+(?:el|la|los|las|un|una)\s+(?:propi[oa]\s+)?" + ACTOR + r"\b",
    re.I,
)
NOMBRE_CONTROL = re.compile(
    r"\b(?:aprobaci[óo]n|confirmaci[óo]n|autorizaci[óo]n|validaci[óo]n|revisi[óo]n|visto bueno)"
    r"(?:\s+(?:expl[íi]cita|expresa|previa|manual|escrita|obligatoria|personal|presencial))*"
    r"\s+(?:human[oa]s?\b|manual\b|(?:del|de la|de los|de las|de un|de una|por el|por la|por los|"
    r"por las|por un|por una|por parte del|por parte de la)\s+(?:propi[oa]\s+)?" + ACTOR + r"\b)",
    re.I,
)
# Detrás del control y en su misma frase, lo anula: «(todavía no implementada)», «por implementar
# en la v2», «automática», «opcional», «previsto», «si da tiempo», «: no».
CONTROL_DEBIL = re.compile(
    r"\b(todav[íi]a|a[úu]n no|pendiente|por implementar|sin implementar|implementar(emos|á|án)?|"
    r"implementemos|autom[áa]tic[oa]s?|opcional(es)?|desactivad[oa]s?|desactivable|"
    r"deshabilitad[oa]s?|impl[íi]cit[oa]s?|t[áa]cit[oa]s?|en el futuro|m[áa]s adelante|"
    r"(en|para) la v\d+|previst[oa]s?|planificad[oa]s?|roadmap|si (da|hay) tiempo|"
    r"cuando (se )?pueda|a veces|de vez en cuando|a posteriori|no (implementad[oa]|existe))\b|"
    r"^\W*(\w+\W+){0,2}no\W*$",
    re.I,
)
# …salvo el adjetivo que va negado o es una salvedad: «no automática», «incluso las automáticas».
ADJETIVO_DEBIL = re.compile(
    r"autom[áa]tic|opcional|desactiva|deshabilitad|impl[íi]cit|t[áa]cit", re.I
)
EXIME_DEBIL = {"no", "nunca", "sin", "ni", "incluso", "también", "hasta", "aun"}
FUERA_CLAUSULA = r"fuera de(l)? alcance|quedan? fuera|no entran? en (este|el) plan"
# «Fuera de alcance: Stripe y Holded» en la propia línea, y «**Fuera de alcance:**» en negrita, que
# abre la lista de debajo: el formato más común después de la cabecera (verificador, 3.ª pasada).
# Con los dos puntos PEGADOS: «No entran en este plan los reembolsos: el webhook se añade ya» ya
# dice qué queda fuera antes de los dos puntos, y lo de detrás sí se construye (verificador, 4.ª).
FUERA_LINEA = (
    r"^\W*(fuera de(l)? alcance|qu[ée] queda fuera|quedan? fuera|out of scope|no incluye|"
    r"no entran?|lo que no se hace)( (de|en|del) (este|el) plan)?\W*:"
)
FUERA_TITULO = (  # «**Fuera de alcance:**», «__Fuera de alcance:__», «Fuera de alcance:» a secas
    r"^\s*(?:[-*+]\s+)?[*_]{0,2}\s*(fuera de(l)? alcance|qu[ée] queda fuera|out of scope|"
    r"no incluye|no entra|lo que no se hace)\b[^*_:\n]{0,30}[*_]{0,2}\s*:?\s*[*_]{0,2}\s*$"
)
LISTA = r"^\s*([-*+]|\d+[.)])\s|^\s{2,}\S"
# «## Fuera de alcance» a mitad del plan y lo que sigue sin otra cabecera: «Y lo que sí se hace: …».
FUTURO = (
    r"(?![^.\n]{0,25}\b(v\d|m[áa]s adelante|despu[ée]s|otr[oa] (fase|plan|sprint|ola)|"
    r"siguiente))"
)
FIN_FUERA = (
    r"\blo que s[íi]\b" + FUTURO + r"|\bs[íi] (entra|se hace|se construye|incluye|forma parte)\b"
    + FUTURO
)
# «Sin dependencias externas salvo Stripe»: el «sin» no niega lo que va detrás del «salvo».
SALVEDAD = r"\b(?:salvo|excepto|menos|aparte de|except|(?:otr[oa]s?|m[áa]s)\s+\w+\s+que)\b"
ESTADO_ACTUAL = (  # «a partir de hoy» o «desde hoy» es futuro, no estado (verificador, 2.ª pasada)
    r"(?<!partir de )(?<!desde )\bhoy\b|\b(actualmente|ya (existe|existen|hay|tiene|tienen|est[áa]|"
    r"trae)|en producci[óo]n desde)\b"
)
ESTADO_DESPUES = r"^\W*(existentes?|actuales?|de siempre)\b"  # «el webhook existente»
# Una fila de estado «hecho» habla entera de lo que ya existe; un ✅ suelto («aprobado») no.
ESTADO_LINEA = (
    r"\*\*hecho\*\*|✅\s*(\*\*)?(hecho|done|ya existe|existente|cerrad)|"
    r":\s*(sin cambios|no cambia|igual que antes|se queda (igual|como est[áa]))\W*$"
)
SECCION_FUERA = (
    r"^#{1,6}\s*\W*(\d+[.)]?\s*)?(fuera de(l)? alcance|qu[ée] queda fuera|out of scope|"
    r"no incluye|no entra|lo que no se hace|estado actual|situaci[óo]n actual|qu[ée] hay hoy|"
    r"c[óo]mo est[áa] (ahora|hoy)|antecedentes)"
)
# Una cabecera de «fuera de alcance» que además anuncia algo nuevo («Estado actual y lo que se
# añade») no cierra la sección.
SECCION_MIXTA = r"\s(y|e)\s|añad|nuev|construi"
# Plan de arreglo: el título EMPIEZA por el arreglo; «Portal de clientes y arreglo del login» no.
TITULO_ARREGLO = (
    r"^#\s*(?:[^\s·:—–-]+\s*[·:—–-]\s*)?"
    r"(?:(fix|bugfix|hotfix|arregl\w*|correg\w*|correcci[óo]n|parche|refactor\w*)\b|"
    r"(?:partir|mover|mueve|reorganiz\w*|renombr\w*)\b" + OBJETO_CODIGO + ")"
)
CLAUSULA = re.compile(r"[.;:]\s|\s(?:pero|aunque|sino|mientras que)\s|\s[ye]\s(?=no\b)", re.I)
# Sin `\s` que cruce saltos de línea: con él, la «razón» era la línea SIGUIENTE (auditor, 20-10).
# Y la línea empieza como texto del plan: con 4 espacios es un bloque de código (verificador).
GATE_F_NO = re.compile(
    r"^ {0,3}(?:[-*>] ?)?\**Gate F[^\w\n]*[:·—–-][ \t]*no aplica\b[ \t]*[—–:.\-]*[ \t]*([^\n]*)$",
    re.I | re.M,
)
GATE_F_EN = re.compile(
    r"^ {0,3}(?:[-*>] ?)?\**Gate F[^\w\n]*[:·—–-][ \t]*modelo en[ \t]*`?([^`\s]+)`?", re.I | re.M
)
RAZON_MIN = 20

# ── El modelo ─────────────────────────────────────────────────────────────────────────────────────
ID_ASVS = re.compile(r"\bv5\.0\.0-(\d+\.\d+\.\d+)\b")
# ASVS 5.0.0 tiene tres niveles: «v5.0.0-8.2.2.1» se leía como 8.2.2 (verificador, 3.ª pasada).
ID_CUATRO = re.compile(r"\bv5\.0\.0-\d+\.\d+\.\d+\.\d+")
ID_ASVS_MAL = re.compile(r"(?<![\w.-])V?(\d{1,2}\.\d{1,2}\.\d{1,2})\b")  # «V8.2.2» sin versión
# Lo que ASVS no cubre: las amenazas DEL MODELO (inyección de prompt, agencia excesiva). Ahí vale el
# id del OWASP Top 10 for LLM Applications 2025 (genai.owasp.org/llm-top-10, LLM01-LLM10, leído el
# 2026-10-20) o del Top 10 for Agentic Applications 2026 (ASI01-ASI10, `rules/agent-security.md`
# §3).
REF_LLM = re.compile(r"\b(?:LLM(?:0[1-9]|10)(?::2025)?|ASI(?:0[1-9]|10))\b")
REF_LLM_TODAS = re.compile(r"\b(?:LLM|ASI)\d+\b")
RESPUESTAS = {"mitigar", "eliminar", "transferir", "aceptar"}
STRIDE_OK = re.compile(r"^[STRIDE](\s*[,·/+ ]\s*[STRIDE])*$")
SI = {"sí", "si", "yes", "true"}
NO = {"no", "false"}
# Relleno con palabras, al PRINCIPIO de la celda: «Pendiente de decidir», «Por definir», «sin test»,
# «se decidirá en el sprint 3» (verificador, 3.ª pasada). «validar el tipo (pendiente)» sí es una
# defensa, y «**pendiente (H2):** <la defensa>» también: decidida y sin hacer, con su hallazgo.
# «Pendiente» solo vale como `pendiente (H1): <la defensa>`, y lo de detrás tiene que ser una
# defensa («pendiente (H1): por decidir» no lo es; verificador, 4.ª pasada): eso lo mira `_vacia`.
RELLENO = re.compile(
    r"^(pendiente\b|"
    r"(a[úu]n |todav[íi]a |est[áa] )?por (decidir|definir|determinar|ver|hacer|escribir|"
    r"implementar|concretar|confirmar|asignar|revisar|firmar)|"
    r"a (decidir|definir|determinar|revisar|concretar)|"
    r"se (decidir|definir|determinar)\w*|se decide\b|se ver[áa]\b|"
    r"falta(n)? (decidir|definir|concretar|escribir|probar|revisar|firmar|el test|la prueba|tests?|"
    r"pruebas?)\b|"
    r"sin (tests?|probar|pruebas?|revisar|revisi[óo]n|decidir|definir|implementar|firmar|"
    r"asignar)\b|"
    r"no hay (tests?|pruebas?)\b|ningun[oa] (tests?|pruebas?)\b|no probad[oa]\b|"
    r"nadie lo ha probado|no decidid[oa]\b|sin concretar\b|a escribir\b|"
    r"(lo )?(vemos|veremos) m[áa]s adelante|ya veremos|"
    r"todav[íi]a no\W*$|ningun[oa] (todav[íi]a|a[úu]n)\W*$|"
    # «No se prueba en CI; se prueba a mano» sí dice cómo se prueba: solo la frase sola es relleno.
    r"no se (ha )?(probado|prueba|decidido|definido|sabe)( (todav[íi]a|a[úu]n))?\W*$|"
    r"(ningun[oa]?|nadie|nada|tbd|tbc)$)"
)
# Firma quien REVISA, no quien escribe: un agente o un modelo no firman (verificador, 3.ª y 4.ª).
# Al principio, las palabras que también son de personas («el asistente», «Bot García» sí es una);
# en cualquier parte, los nombres de agentes y modelos, y un identificador en kebab-case
# (`sofia-pentester`). «Claude Martin» es una persona: «claude» seguido de un apellido no cuenta.
FIRMA_GENERICA = re.compile(
    r"^\W*(el |la |un |una )?(propi[oa] )?(agente|ia|llm|modelo|asistente|bot)\b", re.I
)
# «Ana Ruiz, revisado con ayuda de Claude» lo firma Ana: la herramienta que la ayudó no cuenta.
AYUDA = re.compile(r"\b(con (la )?ayuda de|asistid[oa] por|apoyad[oa] en)\b.*$", re.I)
PERSONA = re.compile(r"(?-i:\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)")
FIRMA_AGENTE = re.compile(
    r"\b(agente|subagente|llm|chatgpt|gpt[\w.-]*|copilot|gemini|codex|sonnet|opus|haiku|anthropic|"
    r"openai)\b|\bclaude\b(?!\s+(?-i:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b)|"
    r"\bclaude[\s-]+(code|opus|sonnet|haiku)\b|"
    r"(?-i:^[a-z0-9]+(?:-[a-z0-9]+)+$)",
    re.I,
)
FIRMA_RELLENO = re.compile(  # «sin firmar», «por revisar», «revisión pendiente», «nadie aún»
    r"\b(pendiente|nadie|tbd|sin (firmar|revisar|asignar)|"
    r"por (revisar|firmar|asignar|definir|decidir)|a revisar)\b",
    re.I,
)
PII = re.compile(
    DATOS_PERSONALES + r"|\bnombre,|direcci[óo]n (del|de la)|\bCVs?\b|"
    r"\bnombre (del|de la) (cliente|usuari[oa]|paciente|soci[oa]|emplead[oa])",
    re.I,
)
LLM = re.compile(
    r"LangGraph|ToolNode|@tool|\bLLM\b|chatbot|bot conversacional|\bMCP\b|agente LLM|"
    r"modelo de lenguaje|\basistente\b|\bagente\b|\bIA\b|"
    r"\bGPT|\bClaude\b|OpenAI|\bGemini\b|Anthropic|\bMistral\b|\btools?\b|\bprompts?\b",
    re.I,
)
# En las AMENAZAS, solo lo inequívoco: «un agente de amenaza externo» o «el asistente de alta» no
# son un LLM (verificador, 4.ª pasada).
LLM_ESTRICTO = re.compile(
    r"LangGraph|ToolNode|@tool|\bLLM\b|chatbot|bot conversacional|\bMCP\b|agente LLM|"
    r"modelo de lenguaje|\bGPT|\bClaude\b|OpenAI|\bGemini\b|Anthropic|\bMistral\b|\bprompts?\b|"
    r"inyecci[óo]n de (prompt|instrucciones)",
    re.I,
)
# Un id de otra versión de ASVS («v4.0.3-8.3.1»): el catálogo es el de la 5.0.0.
ID_OTRA_VERSION = re.compile(r"\bv(\d+\.\d+(?:\.\d+)?)-\d+\.\d+\.\d+")
CODIGO = re.compile(r"`[^`\n]*`")


def _resultado(estado: str, por_que: str, **extra) -> dict:
    return {"estado": estado, "por_que": por_que, **extra}


# ── Catálogos ─────────────────────────────────────────────────────────────────────────────────────
def asvs() -> dict:
    return json.loads(ASVS_JSON.read_text(encoding="utf-8"))


def cartas_linddun(md: pathlib.Path = LINDDUN_MD) -> dict[str, str]:
    """Las cartas válidas salen de la tabla de references/linddun-go.md (fuente única)."""
    # Solo la tabla de las cartas: su título va en MAYÚSCULAS, como en la baraja. Las otras tablas
    # del fichero también empiezan por un código («| U1 | Priya ejes…») y pisaban el título.
    out: dict[str, str] = {}
    for l in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*((?:L|I|Nr|D|DD|U|Nc)\d)\s*\|\s*([A-Z][A-Z \-]+?)\s*\|", l)
        if m:
            out.setdefault(m.group(1), m.group(2))
    return out


# ── Markdown mínimo ───────────────────────────────────────────────────────────────────────────────
def frontmatter(txt: str) -> dict[str, str]:
    m = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n", txt, re.S)
    if not m:
        return {}
    out = {}
    for l in m.group(1).splitlines():
        if ":" in l and not l.lstrip().startswith("#"):
            k, v = l.split(":", 1)
            v = re.sub(r"\s+#.*$", "", v)  # el comentario en línea del ejemplo de la SKILL
            out[k.strip().lower()] = v.strip().strip("\"'").strip()
    return out


def _sin_bloques(txt: str) -> str:
    """El texto con los bloques ``` y ~~~ y los comentarios HTML vaciados (mismas líneas): lo de
    dentro es ejemplo o está escondido, no es el plan (verificador, 2.ª pasada)."""
    txt = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), txt, flags=re.S)
    out, valla = [], None
    for l in txt.splitlines():
        s = l.strip()
        if valla is None and s[:3] in ("```", "~~~"):
            valla = s[:3]
            out.append("")
        elif valla is not None and s.startswith(valla):
            valla = None
            out.append("")
        else:
            out.append("" if valla else l)
    return "\n".join(out)


def _vacia(celda: str) -> bool:
    """¿Celda de relleno? «—», «...», «n/a», «pendiente» a secas, y lo que dice que no está
    decidida («Pendiente de decidir», «sin test»: `RELLENO`), cuentan como vacías."""
    s = re.sub(r"[\s*_`.\-—–·…?¿!]+", " ", celda).strip().lower()
    pendiente = re.match(r"pendiente\s*\(h\d+\)\s*:?\s*(.*)$", s)
    if pendiente:
        return _vacia(pendiente.group(1))
    return not re.search(r"[a-záéíóúñ0-9]", s) or bool(RELLENO.match(s)) or s in {
        "n/a",
        "na",
        "pendiente",
        "no se prueba",
        "no aplica",
        "tbd",
        "por decidir",
        "x",
        "xx",
        "xxx",
    }


def _pocas_palabras(texto: str, n: int) -> bool:
    """Menos de n palabras de verdad (3 letras o más): «xxxxxxxxxxxxxxx» o «sí» no son una razón."""
    palabras = re.findall(r"[a-záéíóúñ]{3,}", texto, re.I)
    return len([p for p in palabras if not re.fullmatch(r"(.)\1+", p, re.I)]) < n


def _tablas(ts: list[dict], es) -> list[dict]:
    """Las tablas cuya cabecera (celdas en minúsculas) cumple `es`. TODAS, no solo la primera."""
    return [t for t in ts if t["cab"] and es(t["cab"])]


def _ventana(antes: str, n: int) -> str:
    """Las n últimas palabras antes de un match, sin cruzar una coma, un paréntesis ni un «salvo»
    («sin dependencias externas salvo Stripe» no niega a Stripe; verificador, 3.ª pasada)."""
    return " ".join(re.split(r"[,(]|" + SALVEDAD, antes, flags=re.I)[-1].split()[-n:])


def _negada(antes: str, negadores: set[str] = NEGADORES) -> bool:
    """¿Hay un «no / sin / ningún» en las 4 palabras pegadas por delante?"""
    palabras = [re.sub(r"[^\wáéíóúñ]", "", p.lower()) for p in _ventana(antes, 4).split()]
    return any(p in negadores for p in palabras)


def _ya_existe(antes: str, despues: str) -> bool:
    """¿La frontera es la que ya hay («hoy ya hay un webhook», «el webhook existente»)?"""
    return bool(
        re.search(ESTADO_ACTUAL, _ventana(antes, 6), re.I)
        or re.match(ESTADO_DESPUES, despues, re.I)
    )


def tablas(txt: str) -> list[dict]:
    """Cada tabla markdown: cabecera (en minúsculas) y filas de celdas. Salta la fila de guiones."""
    out, actual = [], None
    for l in txt.splitlines():
        s = l.strip()
        if s.startswith("|") and s.endswith("|"):
            celdas = [c.strip() for c in s.strip("|").split("|")]
            if actual is None:
                actual = {"cab": [c.lower() for c in celdas], "filas": []}
            elif all(re.fullmatch(r":?-{2,}:?", c) for c in celdas if c):
                continue
            else:
                actual["filas"].append(celdas)
        elif actual is not None:
            out.append(actual)
            actual = None
    if actual is not None:
        out.append(actual)
    return out


def _col(t: dict, palabra: str) -> int | None:
    for i, c in enumerate(t["cab"]):
        if palabra in c:
            return i
    return None


def _col_r2(t: dict, letra: str) -> int | None:
    """La columna [A], [B] o [C] de la Rule of Two, también sin corchetes o con su explicación:
    «[A] entrada no confiable», «A» (verificador, 3.ª y 4.ª pasadas)."""
    for i, c in enumerate(t["cab"]):
        if re.match(rf"^\[?{letra}\]?(\s|$)", c):
            return i
    return None


def _celda(fila: list[str], i: int | None) -> str:
    return fila[i].strip() if i is not None and i < len(fila) else ""


def _hay_control(celda: str) -> bool:
    """¿La celda nombra un control de verdad? `interrupt`, HITL o sesión nueva; o aprobar,
    confirmar, validar o revisar con una persona como sujeto o detrás del nombre. Ni negado delante
    («sin confirmación humana», «nadie lo aprueba»; auditor, 20-10), ni anulado detrás («(todavía no
    implementada)»; verificador, 3.ª y 4.ª pasadas)."""
    for rx in (HITL_FUERTE, SUJETO_VERBO, INVERTIDO, NOMBRE_CONTROL):
        for m in rx.finditer(celda):
            if rx is SUJETO_VERBO:
                sujeto, otra = m.group(1).lower(), (m.group(2) or "").lower()
                if sujeto in {"propio", "propia", "mismo", "misma"}:
                    sujeto, otra = otra, ""
                maquina = {sujeto, otra} & NO_HUMANO and not {sujeto, otra} & {"humano", "humana"}
                objeto = otra in CLITICOS and not re.fullmatch(ACTOR, sujeto, re.I)
                if otra in NO_OBLIGA or maquina or objeto:
                    continue
            if _control_negado(celda, m.start()):
                continue
            if _control_debil(re.split(r"[;.](?:\s|$)", celda[m.end() :])[0]):
                continue
            return True
    return False


def _control_negado(celda: str, inicio: int) -> bool:
    """¿Va negado («sin confirmación», «nadie lo aprueba», «falta la aprobación»)? Un «sin» con otra
    negación en la celda es un requisito, no una negación: «sin la aprobación del gestor no se anula
    nada» (verificador, 4.ª pasada)."""
    if not _negada(celda[:inicio], NEGADORES_CONTROL):
        return False
    palabras = {re.sub(r"[^\wáéíóúñ]", "", w.lower()) for w in _ventana(celda[:inicio], 4).split()}
    solo_sin = not (palabras & (NEGADORES_CONTROL - {"sin"}))
    doble = re.search(r"\bno\s+se\b|\bnada\b|\bnunca\b|\bning[úu]n\b", celda, re.I)
    return not (solo_sin and doble)


def _control_debil(frase: str) -> bool:
    """¿Lo que va detrás, en la misma frase, anula el control? «automática» no, si va negada o es
    una salvedad: «confirmación del usuario, no automática», «incluso las automáticas»."""
    corto = " ".join(frase.split()[:6])
    for m in CONTROL_DEBIL.finditer(corto):
        if ADJETIVO_DEBIL.match(m.group(0)):
            antes = {re.sub(r"[^\wáéíóúñ]", "", w.lower()) for w in corto[: m.start()].split()[-2:]}
            if antes & EXIME_DEBIL:
                continue
        return True
    return False


def _tapado(cl: str) -> list[tuple[int, int]]:
    """Los tramos de la cláusula que dicen que algo queda FUERA. Con sujeto propio, un paréntesis
    tapa solo su trozo («el webhook de Stripe (los reembolsos quedan fuera)»), y una relativa detrás
    de un «salvo», solo la salvedad («Holded, salvo las nóminas, que quedan fuera»); si no, la
    cláusula entera («Stripe y Holded quedan fuera»). Verificador, 3.ª pasada."""
    out = []
    for m in re.finditer(FUERA_CLAUSULA, cl, re.I):
        a = cl.rfind("(", 0, m.start())
        if a > cl.rfind(")", 0, m.start()) and re.search(r"\w", cl[a + 1 : m.start()]):
            b = cl.find(")", m.end())
            out.append((a, len(cl) if b == -1 else b + 1))
            continue
        comas = [c.start() for c in re.finditer(",", cl[: m.start()])]
        if (
            len(comas) >= 2
            and re.match(r"\s*(que|las? cuales|los cuales)\b", cl[comas[-1] + 1 :], re.I)
            and re.match(r"\s*" + SALVEDAD, cl[comas[-2] + 1 :], re.I)
        ):
            out.append((comas[-2], len(cl)))
            continue
        # «Se añade el webhook de Stripe y los reembolsos quedan fuera»: si lo de antes del «y» trae
        # novedad, el «quedan fuera» es de lo que va detrás (verificador, 4.ª pasada).
        ys = [y.start() for y in re.finditer(r"\s[ye]\s", cl[: m.start()])]
        if ys and re.search(NOVEDAD_FUERTE + r"|\bse\s+\w+", cl[: ys[-1]], re.I):
            out.append((ys[-1], len(cl)))
            continue
        out.append((0, len(cl)))
    return out


def _sino(v: str) -> bool | None:
    v = v.strip().lower().rstrip(".")
    primera = re.split(r"[\s:,(—–-]", v, maxsplit=1)[0] if v else ""
    return True if primera in SI else False if primera in NO else None


# ── Validación del modelo ─────────────────────────────────────────────────────────────────────────
def revisa_modelo(ruta: pathlib.Path) -> dict:
    r = {"fichero": str(ruta)}
    if not ruta.exists():
        return {**r, **_resultado(NO_CUMPLE, f"no existe {ruta.name}")}
    try:
        txt = ruta.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {**r, **_resultado(NO_MEDIBLE, f"existe y no se puede leer: {e}")}
    try:
        cat_asvs, cartas = asvs()["requisitos"], cartas_linddun()
    except (OSError, ValueError, KeyError) as e:
        return {
            **r,
            **_resultado(NO_MEDIBLE, f"no se pudieron leer los catálogos de la skill: {e}"),
        }

    sin_codigo = CODIGO.sub("", txt)
    huecos = [
        h if isinstance(h, str) else h[0] for h in HUECOS.findall(sin_codigo)
    ] + MARCAS.findall(sin_codigo)
    if huecos:
        return {
            **r,
            **_resultado(
                NO_CUMPLE,
                f"{len(huecos)} hueco(s) sin rellenar: {', '.join(huecos[:4])} (si es contenido "
                "—un payload, `<script>`— va entre comillas de código)",
            ),
        }

    # La firma, del FRONTMATTER y de verdad: con el regex de gate_arranque, `reviewed_by:` vacío
    # tomaba la línea siguiente como firmante y una fecha 2026-13-45 pasaba (auditor, 20-10).
    fm = frontmatter(txt)
    try:
        fecha_ok = datetime.date.fromisoformat(fm.get("reviewed", "")) <= datetime.date.today()
    except ValueError:
        fecha_ok = False
    errores: list[str] = []
    avisos: list[str] = []
    firmante = fm.get("reviewed_by", "")
    # La firma ya no corta: en rojo, se miran igual las tablas, y un modelo que solo espera su firma
    # lo dice así (el ejemplo de la skill, que escribió un agente).
    if not fecha_ok:
        errores.append("sin firmar: falta una fecha real, y no futura, en `reviewed:`")
    elif _vacia(firmante):
        errores.append("sin firmar: falta quién en `reviewed_by:`")
    elif FIRMA_AGENTE.search(AYUDA.sub("", firmante)) or (
        FIRMA_GENERICA.match(firmante) and not PERSONA.search(firmante)
    ):
        errores.append(
            f"sin firmar: «{firmante}» es un agente — firma una persona que lo revisó, no quien "
            "lo escribió"
        )
    elif FIRMA_RELLENO.search(firmante):
        errores.append(f"sin firmar: «{firmante}» no es quién lo revisó en `reviewed_by:`")
    nivel = fm.get("asvs_nivel", "").upper()
    if nivel not in {"L1", "L2", "L3"}:
        errores.append("`asvs_nivel` tiene que ser L1, L2 o L3 (references/asvs-por-tipo.md)")
    extra = fm.get("asvs_extra", "")
    ids_extra = set(ID_ASVS.findall(extra))
    for rid in sorted(ids_extra):
        if rid not in cat_asvs:
            errores.append(f"`asvs_extra` cita v5.0.0-{rid}, que no existe en ASVS 5.0.0")
    resto = re.sub(r"[,;·\s]+", " ", ID_ASVS.sub("", extra)).strip().lower()
    if resto not in ("", "ninguno", "ninguna", "—", "-", "no"):
        errores.append(
            f"`asvs_extra` tiene que ser «ninguno» o una lista de ids v5.0.0-x.y.z "
            f"(«{resto}» no lo es)"
        )
    pd, ag = _sino(fm.get("datos_personales", "")), _sino(fm.get("agentes_llm", ""))
    if pd is None:
        errores.append("`datos_personales` tiene que ser sí o no")
    if ag is None:
        errores.append("`agentes_llm` tiene que ser sí o no")

    ts = tablas(txt)
    # Cada tabla se reconoce por su CABECERA celda a celda, y cuentan TODAS: buscando subcadenas en
    # la cabecera unida, la de STRIDE («fronte-ra… str-ID-e») hacía de tabla de fronteras, y una
    # segunda tabla STRIDE no se miraba (verificador, 2.ª pasada).
    t_fr = _tablas(ts, lambda c: c[0] == "id" and any(x.startswith("frontera") for x in c))
    t_st = _tablas(
        ts,
        lambda c: c[0].startswith("frontera")
        and "stride" in c
        and any(x.startswith("respuesta") for x in c),
    )
    t_li = _tablas(ts, lambda c: c[0].startswith("carta"))
    # «[A] entrada no confiable…» también es cabecera de la Rule of Two (verificador, 3.ª pasada).
    t_r2 = _tablas(
        ts,
        lambda c: c[0].startswith("agente")
        and _col_r2({"cab": c}, "a") is not None
        and _col_r2({"cab": c}, "c") is not None,
    )

    fronteras: dict[str, str] = {}
    filas_fr = [(t, f) for t in t_fr for f in t["filas"]]
    # Sin la columna, sin la comprobación: «| Id | Frontera | Datos | Actor |» pasaba (verificador).
    for t in t_fr:
        for palabra, nombre in (("cruza", "Qué cruza"), ("otro lado", "Quién está al otro lado")):
            if _col(t, palabra) is None:
                errores.append(f"la tabla de fronteras sin la columna «{nombre}»")
    if not filas_fr:
        errores.append("sin tabla de fronteras (| Id | Frontera | Qué cruza | …) o vacía")
    for t, f in filas_fr:
        fid = _celda(f, 0)
        if not re.fullmatch(r"F\d+", fid):
            errores.append(f"frontera con id «{fid}»: tiene que ser F1, F2…")
            continue
        fronteras[fid] = " ".join(f[1:])
        for col, nombre in (
            (_col(t, "frontera"), "de dónde a dónde"),
            (_col(t, "cruza"), "qué cruza"),
            (_col(t, "otro lado"), "quién está al otro lado"),
        ):
            if col is not None and _vacia(_celda(f, col)):
                errores.append(f"la frontera {fid} sin «{nombre}»")

    cubiertas: set[str] = set()
    filas_st = [(t, f) for t in t_st for f in t["filas"]]
    if not filas_st:
        errores.append(
            "sin tabla STRIDE (| Frontera | STRIDE | Amenaza | Respuesta | Defensa | ASVS | …) "
            "o vacía"
        )
    for n, (t, f) in enumerate(filas_st, 1):
        c_fr, c_st, c_am = _col(t, "frontera"), _col(t, "stride"), _col(t, "amenaza")
        c_re, c_de, c_as, c_pr = (
            _col(t, "respuesta"),
            _col(t, "defensa"),
            _col(t, "asvs"),
            _col(t, "prueba"),
        )
        fr, st, re_ = _celda(f, c_fr), _celda(f, c_st), _celda(f, c_re).lower()
        de, as_, pr = _celda(f, c_de), _celda(f, c_as), _celda(f, c_pr)
        ids_f = re.findall(r"F\d+", fr)
        if not ids_f or any(i not in fronteras for i in ids_f):
            errores.append(
                f"STRIDE fila {n}: frontera «{fr}» no declarada en la tabla de fronteras"
            )
        cubiertas.update(ids_f)
        if not STRIDE_OK.match(st):
            errores.append(f"STRIDE fila {n}: «{st}» no es una letra de S T R I D E")
        if _vacia(_celda(f, c_am)):
            errores.append(f"STRIDE fila {n}: sin amenaza")
        if re_ not in RESPUESTAS:
            errores.append(
                f"STRIDE fila {n}: respuesta «{re_}» — tiene que ser mitigar, eliminar, "
                "transferir o aceptar"
            )
        for ref in REF_LLM_TODAS.findall(as_):
            if not REF_LLM.fullmatch(ref):
                errores.append(
                    f"STRIDE fila {n}: «{ref}» no existe (LLM01-LLM10 de 2025, ASI01-ASI10)"
                )
        # Los ids se validan en TODA fila, también en aceptar y transferir (verificador, 20-10),
        # y un id sin versión cuenta aunque haya uno válido al lado.
        ids, llm = ID_ASVS.findall(as_), REF_LLM.findall(as_)
        for rid in ids:
            if rid not in cat_asvs:
                errores.append(f"STRIDE fila {n}: v5.0.0-{rid} no existe en ASVS 5.0.0")
        mal = ID_ASVS_MAL.findall(ID_ASVS.sub("", as_))
        if mal:
            errores.append(
                f"STRIDE fila {n}: «{mal[0]}» sin la versión delante (se cita v5.0.0-{mal[0]})"
            )
        if re_ in {"mitigar", "eliminar"}:
            if _vacia(de):
                errores.append(
                    f"STRIDE fila {n}: {re_} sin defensa decidida (decidida y sin hacer: "
                    "«pendiente (H1): <la defensa>»)"
                )
            # Un riesgo LLM o ASI sustituye a ASVS solo si hay agente: con `agentes_llm: no`, una
            # IDOR citada como LLM02 pasaba (verificador, 3.ª pasada).
            if not ids and not mal:
                if llm and ag is False:
                    errores.append(
                        f"STRIDE fila {n}: «{llm[0]}» con `agentes_llm: no` — un riesgo LLM o ASI "
                        "sustituye a ASVS solo donde hay un agente"
                    )
                elif not llm:
                    errores.append(
                        f"STRIDE fila {n}: sin requisito ASVS citado como v5.0.0-x.y.z (o, si la "
                        "amenaza es del modelo, LLM01-LLM10 / ASI01-ASI10)"
                    )
            if _vacia(pr):
                errores.append(
                    f"STRIDE fila {n}: {re_} sin «cómo se prueba» — una defensa que no "
                    "se prueba es una declaración"
                )
        elif re_ in {"aceptar", "transferir"} and (
            _vacia(de) or len(de) < 15 or _pocas_palabras(de, 3)
        ):
            errores.append(f"STRIDE fila {n}: {re_} sin la razón escrita en la defensa")
    for fid in fronteras:
        if fid not in cubiertas:
            errores.append(f"la frontera {fid} no tiene ninguna fila STRIDE: declarada y sin mirar")
    # «aceptar» en una fila y «Nada.» en la §5 se contradicen (verificador, 3.ª pasada).
    aceptadas = [
        n
        for n, (t, f) in enumerate(filas_st, 1)
        if _celda(f, _col(t, "respuesta")).lower() == "aceptar"
    ]
    sec5 = re.search(r"^##\s*5\b[^\n]*\n(.*?)(?=^#{1,2}\s|\Z)", txt, re.S | re.M)
    if aceptadas and sec5 is None:
        errores.append(
            f"STRIDE fila {aceptadas[0]} acepta un riesgo y el modelo no tiene §5 (lo que se "
            "acepta, por escrito)"
        )
    elif aceptadas and sec5 is not None and (
        _vacia(sec5.group(1))
        or re.fullmatch(
            r"\W*(nada que aceptar|no se acepta (nada|ning[úu]n riesgo)|no hay riesgos? "
            r"aceptados?)\W*",
            sec5.group(1).strip(),
            re.I,
        )
    ):
        errores.append(
            f"STRIDE fila {aceptadas[0]} acepta un riesgo y la §5 dice que no se acepta nada: "
            "quién lo acepta y hasta cuándo va ahí"
        )

    texto_tablas = " ".join(fronteras.values())
    # La coherencia con el frontmatter, contra las fronteras Y las amenazas: «ve el email y el
    # teléfono de otro» en una fila STRIDE pasaba con `datos_personales: no` (verificador, 3.ª).
    texto_amenazas = " ".join(_celda(f, _col(t, "amenaza")) for t, f in filas_st)
    texto_coherencia = CODIGO.sub("", texto_tablas + " " + texto_amenazas)
    llm_visto = LLM.search(CODIGO.sub("", texto_tablas)) or LLM_ESTRICTO.search(
        CODIGO.sub("", texto_amenazas)
    )
    filas_li = [(t, f) for t in t_li for f in t["filas"]]
    if pd and not filas_li:
        errores.append(
            "`datos_personales: sí` y sin tabla de LINDDUN GO con alguna carta que aplique"
        )
    # La tabla de LINDDUN, como la de la Rule of Two, se valida SIEMPRE que esté.
    if pd is False and filas_li:
        errores.append(
            "`datos_personales: no`, y hay una tabla de LINDDUN GO: o hay datos personales, o la "
            "tabla sobra"
        )
    for n, (t, f) in enumerate(filas_li, 1):
        c_ca, c_fr, c_de, c_am = (
            _col(t, "carta"),
            _col(t, "frontera"),
            _col(t, "defensa"),
            _col(t, "amenaza"),
        )
        cod = re.match(r"\s*((?:Nr|Nc|DD|L|I|D|U)\d+)\b", _celda(f, c_ca))
        if not cod or cod.group(1) not in cartas:
            errores.append(
                f"LINDDUN fila {n}: «{_celda(f, c_ca)}» no es una carta de LINDDUN GO "
                "(references/linddun-go.md)"
            )
        else:
            # Si se escribe el nombre, tiene que ser el de la carta: «D4 CARTA QUE NO EXISTE»
            # pasaba con solo el código válido (verificador, 20-10).
            nombre = _celda(f, c_ca)[cod.end() :].strip(" -—–:·*")
            if nombre and nombre.upper() != cartas[cod.group(1)].upper():
                errores.append(
                    f"LINDDUN fila {n}: {cod.group(1)} se llama «{cartas[cod.group(1)]}», "
                    f"no «{nombre}»"
                )
        if not re.search(r"F\d+", _celda(f, c_fr)) or any(
            i not in fronteras for i in re.findall(r"F\d+", _celda(f, c_fr))
        ):
            errores.append(f"LINDDUN fila {n}: frontera no declarada")
        if c_am is not None and _vacia(_celda(f, c_am)):
            errores.append(f"LINDDUN fila {n}: sin amenaza concreta")
        if _vacia(_celda(f, c_de)):
            errores.append(f"LINDDUN fila {n}: sin defensa decidida")
        for rid in ID_ASVS.findall(" ".join(f)):
            if rid not in cat_asvs:
                errores.append(f"LINDDUN fila {n}: v5.0.0-{rid} no existe en ASVS 5.0.0")
    if pd is False and PII.search(texto_coherencia):
        errores.append(
            f"`datos_personales: no`, y el modelo habla de "
            f"«{PII.search(texto_coherencia).group(0)}»"
        )

    # La Rule of Two se valida SIEMPRE que haya tabla: con `agentes_llm: no`, tres «sí» sin control
    # pasaban (verificador, 2.ª pasada).
    filas_r2 = [(t, f) for t in t_r2 for f in t["filas"]]
    if ag and not filas_r2:
        errores.append(
            "`agentes_llm: sí` y sin tabla Rule of Two (| Agente | [A] | [B] | [C] | Control |)"
        )
    if ag is False and llm_visto:
        errores.append(f"`agentes_llm: no`, y el modelo habla de «{llm_visto.group(0)}»")
    for n, (t, f) in enumerate(filas_r2, 1):
        ca, cb, cc = (_col_r2(t, x) for x in "abc")
        cco = _col(t, "control")
        vals = [_sino(_celda(f, c)) for c in (ca, cb, cc)]
        if None in vals:
            errores.append(f"Rule of Two fila {n}: [A], [B] y [C] empiezan por sí o no")
            continue
        if ag is False and any(vals):
            errores.append(
                f"`agentes_llm: no`, y la tabla Rule of Two describe un agente («{_celda(f, 0)}»)"
            )
        if all(vals) and not _hay_control(_celda(f, cco)):
            errores.append(
                f"Rule of Two fila {n} («{_celda(f, 0)}»): tiene [A], [B] y [C] y ningún "
                "control — sin interrupt, confirmación humana o sesión nueva no opera en "
                "autónomo (Meta, 31-10-2025)"
            )

    # Un id con «V» delante y sin la versión, en cualquier parte (LINDDUN, prosa): «V14.9.9».
    for m in re.finditer(r"(?<![\w.-])V(\d{1,2}\.\d{1,2}\.\d{1,2})\b", ID_ASVS.sub("", txt)):
        if not any(f"«{m.group(1)}»" in e for e in errores):
            errores.append(f"«V{m.group(1)}» sin la versión delante (se cita v5.0.0-{m.group(1)})")

    for m in ID_OTRA_VERSION.finditer(txt):
        if m.group(1) != "5.0.0":
            errores.append(f"«{m.group(0)}» es de otra versión de ASVS: aquí se cita la 5.0.0")
    for c4 in sorted(set(ID_CUATRO.findall(txt))):
        errores.append(
            f"«{c4}» tiene cuatro niveles: ASVS 5.0.0 se cita con tres (capítulo.sección.requisito)"
        )

    # Cualquier id del fichero, también en la prosa de §5 y §6, tiene que existir; y uno de nivel
    # superior al del proyecto que no esté en `asvs_extra` es un AVISO (no bloquea): o se suma a
    # propósito, o el nivel declarado se queda corto.
    for rid in sorted(set(ID_ASVS.findall(txt))):
        if rid not in cat_asvs:
            if not any(f"v5.0.0-{rid} " in e for e in errores):
                errores.append(f"v5.0.0-{rid}, citado en el modelo, no existe en ASVS 5.0.0")
        elif (
            nivel in {"L1", "L2", "L3"}
            and cat_asvs[rid]["L"] > int(nivel[1])
            and rid not in ids_extra
        ):
            avisos.append(
                f"v5.0.0-{rid} es L{cat_asvs[rid]['L']} y el modelo es {nivel}: ponlo en "
                "`asvs_extra` "
                "si se suma a propósito"
            )

    medido = {
        "fronteras": len(fronteras),
        "nivel": nivel or None,
        "datos_personales": pd,
        "agentes_llm": ag,
    }
    if errores:
        return {
            **r,
            **_resultado(NO_CUMPLE, errores[0], errores=errores, medido=medido, avisos=avisos),
        }
    return {
        **r,
        **_resultado(
            CUMPLE,
            f"{len(fronteras)} frontera(s) modeladas, ASVS {nivel}",
            medido=medido,
            avisos=avisos,
        ),
    }


# ── El plan: ¿aplica el Gate F? ───────────────────────────────────────────────────────────────────
def leer_plan(ruta: pathlib.Path) -> tuple[pathlib.Path, list[tuple[str, str]]] | None:
    """(carpeta, [(fichero, texto)…]): `plan.md` y `spec.md` se leen POR SEPARADO, cada uno con su
    título y sus números de línea (juntos, el «# Fix» de uno callaba el webhook del otro)."""
    if ruta.is_file():
        return ruta.parent, [(ruta.name, ruta.read_text(encoding="utf-8", errors="replace"))]
    partes = [ruta / n for n in ("plan.md", "spec.md") if (ruta / n).is_file()]
    if not partes:
        return None
    return ruta, [(p.name, p.read_text(encoding="utf-8", errors="replace")) for p in partes]


def candidatos(txt: str, fichero: str = "") -> list[dict]:
    """Las líneas de UN fichero de plan que crean o cambian una frontera. Léxico: candidatos, no
    veredictos. Las cabeceras también cuentan («## 1. Webhook de Stripe»), salvo las que abren una
    sección de lo que no se construye."""
    titulo = next((l for l in txt.splitlines() if re.match(r"^#\s", l)), "")
    # Plan de arreglo, solo si el título EMPIEZA por el arreglo: «Portal de clientes y arreglo del
    # login» callaba el fichero entero (verificador, 2.ª pasada).
    plan_de_arreglo = bool(re.search(TITULO_ARREGLO, titulo, re.I))
    out, fuera, lista_fuera = [], False, False
    for n, l in enumerate(_sin_bloques(txt).splitlines(), 1):
        if lista_fuera:  # la lista que abre un «Fuera de alcance:» como título
            if not l.strip() or re.match(LISTA, l):
                continue
            lista_fuera = False
        if re.match(r"^#{1,6}\s", l):
            fuera = bool(re.search(SECCION_FUERA, l, re.I)) and not re.search(
                SECCION_MIXTA, l, re.I
            )
            if fuera:
                continue
        elif fuera and re.search(FIN_FUERA, l, re.I):
            fuera = False
        if re.search(FUERA_TITULO, l, re.I):
            lista_fuera = True
            continue
        if re.search(FUERA_LINEA, l, re.I):
            continue
        if fuera or GATE_F_NO.search(l) or GATE_F_EN.search(l) or re.search(ESTADO_LINEA, l, re.I):
            continue
        # Lo que va entre comillas de código SE MIRA: `backend/integrations/microsoft_graph/` o
        # `@tool` son las pistas más claras de una frontera (quitarlas callaba el COR-1 de AMC).
        # Lo que va entre ¿ y ? se borra (con espacios, para no mover las posiciones): la pregunta
        # no construye nada, pero el resto de la cláusula sí (verificador, 2.ª pasada).
        s = re.sub(r"¿[^?\n]*\?", lambda q: " " * len(q.group(0)), l)
        if "¿" in s:
            s = s[: s.index("¿")]
        for cl in CLAUSULA.split(s):
            if not cl.strip():
                continue
            if cl.rstrip(" *_|").endswith("?"):  # una pregunta sin «¿»
                continue
            novedad = bool(re.search(NOVEDAD_FUERTE, cl, re.I))
            tapado = _tapado(cl)
            # Si una mención es la que ya hay («el webhook existente»), las demás del mismo tipo en
            # la cláusula también, salvo novedad: la ruta `views/webhook.py` de al lado disparaba.
            existentes = {
                tipo
                for tipo, rx in FRONTERAS.items()
                for m in re.finditer(rx, cl, re.I)
                if _ya_existe(cl[: m.start()], cl[m.end() :])
            }
            for tipo, rx in FRONTERAS.items():
                if any(c["linea"] == n and c["tipo"] == tipo for c in out):
                    continue
                for m in re.finditer(rx, cl, re.I):
                    antes = cl[: m.start()]
                    if any(a <= m.start() < b for a, b in tapado):
                        continue
                    if _negada(antes) or _ya_existe(antes, cl[m.end() :]):
                        continue
                    # La negación, pegada al verbo de dentro: «el bot, si el cliente no paga en 15
                    # minutos, cancela» no está negado (verificador, 4.ª pasada).
                    if tipo in MENCION_CON_HUECO and _negada(m.group(0).rsplit(None, 1)[0]):
                        continue
                    if tipo in existentes and not novedad:
                        continue
                    # «Arreglar» cuenta si GOBIERNA esta frontera: va antes y en su misma cláusula
                    # («Se corrige el alta: ahora … un formulario público» dispara; verificador,
                    # 3.ª pasada), o el plan entero es un arreglo. «Webhook que corrige» no lo es.
                    arreglo = plan_de_arreglo or bool(re.search(ARREGLO, antes, re.I))
                    if arreglo and not novedad:
                        continue
                    out.append(
                        {
                            "fichero": fichero,
                            "linea": n,
                            "tipo": tipo,
                            "palabra": m.group(0),
                            "texto": l.strip()[:120],
                        }
                    )
                    break
    return out


def candidatos_de(ruta: pathlib.Path) -> list[dict] | None:
    """Los candidatos de todos los ficheros del plan (None si no hay plan que leer)."""
    leido = leer_plan(ruta)
    if leido is None:
        return None
    return [c for nombre, txt in leido[1] for c in candidatos(txt, nombre)]


def revisa_plan(ruta: pathlib.Path) -> dict:
    leido = leer_plan(ruta)
    if leido is None:
        return _resultado(NO_MEDIBLE, f"no hay plan.md ni spec.md en {ruta}", plan=str(ruta))
    carpeta, ficheros = leido
    cand = [c for nombre, txt in ficheros for c in candidatos(txt, nombre)]
    tipos = sorted({c["tipo"] for c in cand})
    base = {"plan": str(ruta), "candidatos": cand, "fronteras": tipos}
    if not cand:
        return {
            **base,
            **_resultado(NO_APLICA, "ningún cruce de frontera en el plan: el Gate F calla"),
        }
    # Las dos salidas escritas se buscan FUERA de los bloques de código: la línea de ejemplo de un
    # documento no es la decisión de este plan.
    txt = "\n".join(_sin_bloques(t) for _, t in ficheros)
    rutas = [carpeta / NOMBRE_MODELO, carpeta / "arranque" / NOMBRE_MODELO]
    no = GATE_F_NO.search(txt)
    if no:
        razon = no.group(1).strip(" *—–-:.\t")
        # Una razón de verdad: longitud, sin hueco, no entre corchetes y con palabras («........» o
        # «[pendiente de decidir]» pasaban; verificador, 2.ª pasada).
        relleno = (
            HUECOS.search(razon)
            or MARCAS.search(razon)
            or re.fullmatch(r"\W*\[.*\]\W*", razon)
            or _pocas_palabras(razon, 4)
        )
        if len(razon) < RAZON_MIN or relleno:
            return {
                **base,
                **_resultado(
                    NO_CUMPLE,
                    f"«Gate F: no aplica» sin una razón escrita en la misma línea (≥{RAZON_MIN} "
                    f"caracteres, cuatro palabras y sin huecos de plantilla) y el plan cruza: "
                    f"{', '.join(tipos)}",
                ),
            }
        # «No aplica» no tapa un modelo roto que está en la carpeta: o se arregla o se retira
        # (verificador, 3.ª pasada).
        hay = next((p for p in rutas if p.exists()), None)
        if hay is not None:
            rm = revisa_modelo(hay)
            if rm["estado"] != CUMPLE:
                return {
                    **base,
                    "modelo": rm,
                    **_resultado(
                        rm["estado"],
                        f"«Gate F: no aplica», pero {hay.name} está en la carpeta y no pasa: "
                        f"{rm['por_que']}",
                    ),
                }
        return {**base, **_resultado(NO_APLICA, f"declarado no aplica: {razon}")}
    en = GATE_F_EN.search(txt)
    if en:
        indicado = (carpeta / en.group(1)).resolve()
        # Solo un modelo del plan o del core del proyecto: apuntar al ejemplo de la skill (o a
        # cualquier modelo del repo) lo convertía en comodín (verificador, 2.ª pasada).
        docs = (CLAUDE.parent / ".docs").resolve()
        if not (indicado.is_relative_to(carpeta.resolve()) or indicado.is_relative_to(docs)):
            return {
                **base,
                **_resultado(
                    NO_CUMPLE,
                    f"«Gate F: modelo en {en.group(1)}» sale de la carpeta del plan y de `.docs/`",
                ),
            }
        if not indicado.is_file():
            return {
                **base,
                **_resultado(
                    NO_CUMPLE, f"«Gate F: modelo en {en.group(1)}» y ese fichero no existe"
                ),
            }
        modelo = indicado
    else:
        modelo = next((p for p in rutas if p.exists()), None)
    if modelo is None:
        lineas = ", ".join(f"{c['tipo']} {c['fichero']}:{c['linea']}" for c in cand[:5])
        return {
            **base,
            **_resultado(
                NO_CUMPLE,
                f"el plan cruza fronteras ({lineas}) y no hay "
                f"{NOMBRE_MODELO}: skill `modelado-amenazas`, o "
                f"«Gate F: no aplica — <razón>» si el detector se equivoca",
            ),
        }
    rm = revisa_modelo(modelo)
    base["modelo"] = rm
    if rm["estado"] != CUMPLE:
        return {**base, **_resultado(rm["estado"], f"{modelo.name}: {rm['por_que']}")}
    med = rm.get("medido", {})
    if "datos_personales" in tipos and med.get("datos_personales") is False:
        return {
            **base,
            **_resultado(
                NO_CUMPLE, "el plan trata datos personales y el modelo dice `datos_personales: no`"
            ),
        }
    if "tool_efecto" in tipos and med.get("agentes_llm") is False:
        return {
            **base,
            **_resultado(
                NO_CUMPLE,
                "el plan da tools con efecto a un agente y el modelo dice `agentes_llm: no`",
            ),
        }
    return {**base, **_resultado(CUMPLE, f"cruza {', '.join(tipos)} · {rm['por_que']}")}


# ── El subconjunto ASVS ───────────────────────────────────────────────────────────────────────────
def subconjunto(nivel: str, con: list[str], extra: list[str]) -> dict:
    d = asvs()
    tope = int(nivel[1])
    caps = list(CAPITULOS_BASE) + [CAPITULOS_SI[c] for c in con]
    ids = [
        rid
        for rid, v in d["requisitos"].items()
        if int(rid.split(".")[0]) in caps and v["L"] <= tope
    ]
    for e in extra:
        if e not in d["requisitos"]:
            raise ValueError(f"v5.0.0-{e} no existe en ASVS 5.0.0")
        if e not in ids:
            ids.append(e)
    return {
        "nivel": nivel,
        "capitulos": sorted(caps),
        "extra": extra,
        "total": len(ids),
        "ids": [f"v5.0.0-{i}" for i in ids],
        "por_capitulo": {
            f"V{c}": sum(1 for i in ids if int(i.split('.')[0]) == c) for c in sorted(caps)
        },
    }


# ── Autoprueba ────────────────────────────────────────────────────────────────────────────────────
MODELO_BUENO = """---
reviewed: 2026-10-20
reviewed_by: Ana Ruiz
asvs_nivel: L2
asvs_extra: v5.0.0-4.1.5, v5.0.0-8.3.3
datos_personales: sí
agentes_llm: sí
---
# Modelo de amenazas · reservas de la clínica con pago y asistente

## 1. Fronteras

| Id | Frontera (de → a) | Qué cruza | Quién está al otro lado |
|---|---|---|---|
| F1 | Paciente (navegador) → API de reservas | nombre, teléfono y email del paciente | cualquiera en internet |
| F2 | Stripe → webhook `/pagos/aviso/` | evento de pago firmado | un tercero, firmado |
| F3 | Asistente LLM → tool `reservar_cita` | la cita que propone el modelo | el modelo, que lee texto del paciente |

## 2. STRIDE

| Frontera | STRIDE | Amenaza | Respuesta | Defensa decidida | ASVS | Cómo se prueba |
|---|---|---|---|---|---|---|
| F1 | S | fuerza bruta contra el acceso del paciente | mitigar | límite de intentos y bloqueo con aviso | v5.0.0-6.3.1 | test_bloqueo_login |
| F1 | I | un paciente ve las citas de otro por id | mitigar | filtrar por el dueño en el queryset | v5.0.0-8.2.2 | test_idor_citas |
| F2 | T | aviso de pago falsificado | mitigar | firma `Stripe-Signature` comprobada | v5.0.0-4.1.5 | test_firma_mala |
| F3 | E | el modelo reserva a nombre de otro paciente | mitigar | el paciente sale del contexto, no del modelo; `interrupt()` antes de reservar | v5.0.0-8.3.3 | test_hitl_reserva |
| F3 | D | el modelo encadena 200 llamadas | aceptar | tope de 10 llamadas por turno ya en el grafo; se acepta el resto | — | — |

## 3. LINDDUN GO

| Carta | Frontera | Amenaza concreta | Defensa decidida | Base legal o ASVS |
|---|---|---|---|---|
| DD2 EXCESSIVE AMOUNT OF DATA COLLECTED | F1 | pedir DNI para una cita | no se pide DNI | RGPD art. 5.1.c |
| D4 DETECTABLE RECORDS | F1 | «ese email ya tiene cita» confirma que es paciente | misma respuesta exista o no | v5.0.0-6.3.8 |

## 4. Rule of Two

| Agente (sesión) | [A] | [B] | [C] | Control si son las tres |
|---|---|---|---|---|
| asistente de reservas | sí: texto del paciente | sí: agenda de la clínica | sí: crea la cita | `interrupt()` y confirmación del paciente |

## 5. Aceptado

La denegación de servicio por llamadas encadenadas, con el tope que ya hay.

## 6. Revisión

Lo revisa Sofía con los casos de la columna «Cómo se prueba» antes del merge.
"""

PLAN_MODULO = """# Plan · módulo nuevo de reservas

Módulo nuevo `apps/reservas/`: el paciente reserva desde la web y guarda nombre, teléfono y email.
Se añade un webhook para los avisos de pago de Stripe.
"""
PLAN_BUGFIX = """# Fix: el total del carrito redondea mal

Bugfix en `apps/cart/services.py`: el redondeo se hace antes de sumar el IVA. Un fichero, causa
clara.
"""
PLAN_BUGFIX_WEBHOOK = """# Fix: el webhook de pagos crea pedidos duplicados

Arreglar `apps/pagos/views.py`: el webhook de Stripe crea un pedido por cada reintento. Se corrige
con la clave de idempotencia que ya trae el evento.
"""
PLAN_NEGADO = """# Plan · rehacer el listado de productos

Se parte `views.py` en tres módulos. No se toca ningún dato personal y no se añade ningún webhook.
"""
PLAN_APP_NUEVA = """# Plan · app nueva de fichajes

Cada empleado tiene en su ficha el DNI y un teléfono de contacto.
"""
PLAN_TOOLS = """# Plan · el asistente cancela pedidos

Se añade al grafo una tool que cancela el pedido del cliente cuando lo pide.
"""
PLAN_FUERA = """# Plan · refactor del listado de productos

Partir `views.py` en tres módulos y añadir paginación al listado.

## Fuera de alcance

- La integración con Stripe y el webhook de pagos (otro plan).
"""


def _autoprueba() -> int:
    with tempfile.TemporaryDirectory(prefix="gate-amenazas-") as t:
        return _autoprueba_en(pathlib.Path(t))


def _autoprueba_en(tmp: pathlib.Path) -> int:
    casos: list[tuple[str, int, callable]] = []

    def plan(nombre: str, txt: str, modelo: str | None = None) -> pathlib.Path:
        d = tmp / nombre
        d.mkdir(parents=True, exist_ok=True)
        (d / "plan.md").write_text(txt, encoding="utf-8")
        if modelo is not None:
            (d / NOMBRE_MODELO).write_text(modelo, encoding="utf-8")
        return d

    def modelo(nombre: str, txt: str) -> pathlib.Path:
        p = tmp / f"{nombre}.md"
        p.write_text(txt, encoding="utf-8")
        return p

    def sale(r: dict) -> int:
        return 0 if r["estado"] in (CUMPLE, NO_APLICA) else 2 if r["estado"] == NO_MEDIBLE else 1

    def _dos_ficheros() -> dict:
        d = plan("f27", "# Fix: redondeo del carrito\n\nSe corrige el redondeo.\n")
        (d / "spec.md").write_text(
            "# Spec · pagos\n\nR4 — Webhook receiver de Stripe: verifica firma.\n", encoding="utf-8"
        )
        r = revisa_plan(d)
        if not any(c["fichero"] == "spec.md" and c["linea"] == 3 for c in r.get("candidatos", [])):
            return _resultado(CUMPLE, f"el candidato no sale como spec.md:3: {r.get('candidatos')}")
        return r

    def _modelo_fuera() -> dict:
        r = revisa_plan(
            plan("f31", PLAN_MODULO + "\nGate F: modelo en ../../../../../../../../etc/hostname\n")
        )
        if r["estado"] == NO_CUMPLE and "sale de la carpeta" not in r["por_que"]:
            return _resultado(CUMPLE, f"rojo, pero no por la ruta: {r['por_que']}")
        return r

    def _modelo_comodin() -> dict:
        ejemplo = REFS / "ejemplo-mcp-comercio.md"
        r = revisa_plan(plan("f46", PLAN_MODULO + f"\nGate F: modelo en {ejemplo}\n"))
        if r["estado"] == NO_CUMPLE and "sale de la carpeta" not in r["por_que"]:
            return _resultado(CUMPLE, f"rojo, pero no por la ruta: {r['por_que']}")
        return r

    def _dos_cambios(cambios: list[tuple[str, str]], motivo: str, base: str = MODELO_BUENO):
        def f() -> dict:
            txt = base
            for v, nv in cambios:
                assert v in txt, v
                txt = txt.replace(v, nv, 1)
            r = revisa_modelo(modelo("dos", txt))
            primero = (r.get("errores") or [r["por_que"]])[0]
            if r["estado"] == NO_CUMPLE and not any(
                motivo in e for e in r.get("errores", [primero])
            ):
                return _resultado(
                    CUMPLE, f"rojo por OTRO motivo: «{primero}» (esperaba «{motivo}»)"
                )
            return r

        return f

    def _modelo_en_no_existe() -> dict:
        r = revisa_plan(
            plan("f32", PLAN_MODULO + "\nGate F: modelo en otro/modelo.md\n", MODELO_BUENO)
        )
        if r["estado"] == NO_CUMPLE and "otro/modelo.md" not in r["por_que"]:
            return _resultado(CUMPLE, f"el mensaje no nombra la ruta indicada: {r['por_que']}")
        return r

    def _cv() -> dict:
        r = revisa_plan(
            plan("f66", "# Spec · empleo\n\n- **RF-01** Los candidatos suben su CV desde la web.\n")
        )
        if "ficheros" not in r.get("fronteras", []):
            return _resultado(CUMPLE, f"no sale como subida de ficheros: {r.get('fronteras')}")
        return r

    def sab(cambio: tuple[str, str]) -> str:
        viejo, nuevo = cambio
        assert viejo in MODELO_BUENO, f"el sabotaje no encuentra «{viejo}»"
        return MODELO_BUENO.replace(viejo, nuevo, 1)

    # Un modelo válido SIN datos personales ni agentes: sin F3, sin las secciones 3-4 ni el email.
    vacia = (
        "\n".join(l for l in MODELO_BUENO.split("## 3.")[0].splitlines() if "| F3 |" not in l)
        .replace("datos_personales: sí", "datos_personales: no")
        .replace("agentes_llm: sí", "agentes_llm: no")
        .replace("nombre, teléfono y email del paciente", "la fecha y la hora elegidas")
        + "\n"
    )

    def _aviso_nivel() -> dict:
        r = revisa_modelo(
            modelo(
                "c08",
                sab(("asvs_extra: v5.0.0-4.1.5, v5.0.0-8.3.3", "asvs_extra: v5.0.0-8.3.3")),
            )
        )
        if r["estado"] == CUMPLE and not any("4.1.5" in a for a in r.get("avisos", [])):
            return _resultado(NO_CUMPLE, "sin el aviso de nivel para v5.0.0-4.1.5")
        return r

    sin_linddun = (
        MODELO_BUENO[: MODELO_BUENO.index("## 3. LINDDUN GO")]
        + MODELO_BUENO[MODELO_BUENO.index("## 4. Rule of Two") :]
    )

    # — El Gate F: dispara donde debe y calla donde no —
    casos += [
        (
            "F-01 módulo nuevo con datos personales y webhook, sin modelo → rojo",
            1,
            lambda: revisa_plan(plan("f01", PLAN_MODULO)),
        ),
        (
            "F-02 el mismo plan con su modelo → verde",
            0,
            lambda: revisa_plan(plan("f02", PLAN_MODULO, MODELO_BUENO)),
        ),
        ("F-03 bugfix de un fichero → calla", 0, lambda: revisa_plan(plan("f03", PLAN_BUGFIX))),
        (
            "F-04 bugfix EN el webhook (no lo crea) → calla",
            0,
            lambda: revisa_plan(plan("f04", PLAN_BUGFIX_WEBHOOK)),
        ),
        (
            "F-05 la frontera solo en «Fuera de alcance» → calla",
            0,
            lambda: revisa_plan(plan("f05", PLAN_FUERA)),
        ),
        (
            "F-06 «Gate F: no aplica — razón» → se respeta",
            0,
            lambda: revisa_plan(
                plan(
                    "f06",
                    PLAN_MODULO + "\nGate F: no aplica — las reservas son de "
                    "prueba interna y se borran al acabar la demo\n",
                )
            ),
        ),
        (
            "F-07 «Gate F: no aplica» sin razón → rojo",
            1,
            lambda: revisa_plan(plan("f07", PLAN_MODULO + "\nGate F: no aplica\n")),
        ),
        (
            "F-08 el plan trata datos personales y el modelo (válido) dice que no → rojo",
            1,
            lambda: revisa_plan(plan("f08", PLAN_MODULO, vacia)),
        ),
        ("F-09 carpeta sin plan → no medible", 2, lambda: revisa_plan(tmp / "no-existe")),
        (
            "F-10 modelo en arranque/ (fase 4b de /arrancar) → se encuentra",
            0,
            lambda: (
                plan("f10", PLAN_MODULO),
                (tmp / "f10" / "arranque").mkdir(),
                (tmp / "f10" / "arranque" / NOMBRE_MODELO).write_text(
                    MODELO_BUENO, encoding="utf-8"
                ),
                revisa_plan(tmp / "f10"),
            )[-1],
        ),
        (
            "F-11 la frontera negada («no se añade ningún webhook») → calla",
            0,
            lambda: revisa_plan(plan("f11", PLAN_NEGADO)),
        ),
        (
            "F-11b la negación de otra cláusula no tapa la frontera → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f11b",
                    "# Plan · pagos\n\nNo se toca el login, pero se añade un "
                    "webhook para los avisos de Redsys.\n",
                )
            ),
        ),
        (
            "F-12 tool con efecto y el modelo (válido) dice que no hay agentes → rojo",
            1,
            lambda: revisa_plan(plan("f12", PLAN_TOOLS, vacia)),
        ),
        (
            "F-13 «app nueva» con datos personales, sin verbo de novedad en la línea → rojo",
            1,
            lambda: revisa_plan(plan("f13", PLAN_APP_NUEVA)),
        ),
        (
            "F-14 lo que ya existe («hoy ya hay un webhook») → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f14",
                    "# Plan · panel\n\nHoy ya hay un webhook de Stripe en producción; "
                    "este plan solo cambia los colores del panel.\n",
                )
            ),
        ),
        (
            "F-15 la frontera solo en «Estado actual» → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f15",
                    "# Plan · informes\n\n## Estado actual\n\nLos informes salen por "
                    "email con el CRM.\n\n## Qué se hace\n\nSe parte el generador en dos.\n",
                )
            ),
        ),
        (
            "F-16 plan cuyo título es un fix, el webhook sin verbo de arreglo → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f16",
                    "# Fix: pedidos duplicados\n\nEl webhook de Stripe recibe el "
                    "evento dos veces y el handler no mira la clave.\n",
                )
            ),
        ),
        (
            "F-18 una línea de arreglo en un plan que no es de arreglo → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f18",
                    "# Plan · pagos y panel\n\nArreglar el webhook de Redsys, que "
                    "duplica pedidos.\n\nRehacer los colores del panel.\n",
                )
            ),
        ),
        (
            "F-19 una pregunta abierta («¿hace falta un webhook?») → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f19",
                    "# Plan · pagos\n\n- ¿Hace falta un webhook de Stripe o basta el "
                    "enlace de pago?\n",
                )
            ),
        ),
        (
            "F-20 negación sin verbo («NO datos de salud») → calla",
            0,
            lambda: revisa_plan(
                plan("f20", "# Plan · citas\n\n- **#4 NO datos de salud** en la pantalla nueva\n")
            ),
        ),
        (
            "F-21 fila de estado «**Hecho**» → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f21",
                    "# Plan · cierre\n\n| #9 | Carrito | **Hecho** base: checkout "
                    "con WooCommerce |\n",
                )
            ),
        ),
        (
            "F-17 spec en presente, sin verbo de novedad (el caso XM-4 de musa) → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f17",
                    "# Spec · pagos\n\n4. **R4 — Webhook receiver** "
                    "`POST /api/payments/stripe/webhook/`: verifica firma y registra el pago.\n",
                )
            ),
        ),
        # — los de la primera ronda de auditores (20-10) —
        (
            "F-07b «no aplica» con la razón en la línea SIGUIENTE → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f07b",
                    PLAN_MODULO + "\nGate F: no aplica\n\nLas pruebas de carga se hacen el jueves "
                    "con datos sintéticos.\n",
                )
            ),
        ),
        (
            "F-07c «no aplica» con el marcador de la plantilla como razón → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f07c",
                    PLAN_MODULO
                    + "\nGate F: no aplica — <razón escrita por quien decide en el plan>\n",
                )
            ),
        ),
        (
            "F-07d «no aplica» dentro de un bloque de código → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f07d",
                    PLAN_MODULO + "\n```\nGate F: no aplica — las reservas son de prueba interna y "
                    "se borran\n```\n",
                )
            ),
        ),
        (
            "F-22 «pedidos existentes» no tapa el webhook nuevo → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f22",
                    "# Plan · pedidos\n\nSe añade un webhook de Stripe que actualiza los pedidos "
                    "existentes.\n",
                )
            ),
        ),
        (
            "F-23 «sin datos de sesión» no tapa el endpoint público → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f23",
                    "# Plan · contacto\n\nSe expone un endpoint público de contacto, sin datos de "
                    "sesión.\n",
                )
            ),
        ),
        (
            "F-24 «hoy» detrás no tapa la integración → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f24",
                    "# Plan · CRM\n\nIntegración con HubSpot para los contactos que hoy están "
                    "en el Excel.\n",
                )
            ),
        ),
        (
            "F-25 plan de arreglo: «implementación» no es novedad → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f25",
                    "# Fix: pedidos duplicados\n\nSe corrige la implementación del webhook de "
                    "Stripe.\n",
                )
            ),
        ),
        (
            "F-26 «integración con el frontend» no es un tercero → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f26",
                    "# Plan · panel\n\nMantener la integración con el frontend al partir el "
                    "módulo.\n",
                )
            ),
        ),
        (
            "F-27 plan.md de arreglo + spec.md con webhook: cada uno con su título → rojo",
            1,
            _dos_ficheros,
        ),
        (
            "F-28 la frontera solo en una cabecera → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f28",
                    "# Plan · cobro con Stripe y su webhook\n\n## 1. Webhook de Stripe\n\nSe hace "
                    "en dos pasos.\n",
                )
            ),
        ),
        (
            "F-29 datos de salud e identidad (pacientes, alergias) → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f29",
                    "# Plan · app nueva de fichas\n\nGuarda la fecha de nacimiento, las "
                    "alergias y la medicación.\n",
                )
            ),
        ),
        (
            "F-30 un tercero que no está en la lista, por «su API» → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f30",
                    "# Plan · facturas\n\nSincronizar las facturas con Quipu mediante su API "
                    "REST.\n",
                )
            ),
        ),
        ("F-31 «modelo en» una ruta fuera de la carpeta y del repo → rojo", 1, _modelo_fuera),
        (
            "F-33 «queda fuera de este plan» → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f33", "# Plan · panel\n\nLa integración con Stripe queda fuera de este plan.\n"
                )
            ),
        ),
        (
            "F-32 «modelo en» un fichero que no existe: el mensaje lo nombra → rojo",
            1,
            _modelo_en_no_existe,
        ),
        # — los de la segunda pasada del verificador (20-10) —
        (
            "F-34 una tool con efecto sin la palabra «tool» (el agente cancela) → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-34",
                    "# Plan · postventa\n\nEl agente podrá cancelar pedidos y emitir reembolsos.\n",
                )
            ),
        ),
        (
            "F-35 «arreglo» en medio del título no hace de plan de arreglo → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-35",
                    "# Portal de clientes y arreglo del login\n\nGuarda el DNI, el teléfono y la "
                    "dirección postal.\n",
                )
            ),
        ),
        (
            "F-36 «corrige» DESPUÉS de la frontera no es un arreglo → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-36",
                    "# Spec · pagos\n\nWebhook receiver de Stripe que corrige el estado del "
                    "pedido.\n",
                )
            ),
        ),
        (
            "F-37 una pregunta al final de la línea no calla la frontera → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-37",
                    "# Plan · cobros\n\n- R4: webhook de Stripe para los cobros (¿quién rota el "
                    "secreto?)\n",
                )
            ),
        ),
        (
            "F-38 un ✅ que es «aprobado», no «hecho» → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-38",
                    "# Plan · requisitos\n\n| R4 | Webhook de Redsys | ✅ aprobado por el cliente "
                    "|\n",
                )
            ),
        ),
        (
            "F-39 «## Estado actual y lo que se añade» no cierra la sección → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-39",
                    "# Plan · pagos\n\n## Estado actual y lo que se añade\n\nUn webhook de Redsys "
                    "para los avisos.\n",
                )
            ),
        ),
        (
            "F-40 «a partir de hoy» es futuro, no estado actual → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-40",
                    "# Plan · facturas\n\nA partir de hoy los clientes suben sus facturas en "
                    "PDF.\n",
                )
            ),
        ),
        (
            "F-41 «no aplica» dentro de un bloque ~~~ → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-41",
                    PLAN_MODULO
                    + "\n~~~\nGate F: no aplica — las reservas son de prueba interna y se "
                      "borran\n~~~\n",
                )
            ),
        ),
        (
            "F-42 «no aplica» dentro de un comentario HTML → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-42",
                    PLAN_MODULO
                    + "\n<!--\nGate F: no aplica — las reservas son de prueba interna y se "
                      "borran\n-->\n",
                )
            ),
        ),
        (
            "F-43 «no aplica» en un bloque indentado → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-43",
                    PLAN_MODULO
                    + "\n    Gate F: no aplica — las reservas son de prueba interna y se borran\n",
                )
            ),
        ),
        (
            "F-44 «no aplica» con una razón de relleno (xxxx) → rojo",
            1,
            lambda: revisa_plan(
                plan("f-44", PLAN_MODULO + "\nGate F: no aplica — xxxxxxxxxxxxxxxxxxxxxxxx\n")
            ),
        ),
        (
            "F-45 «no aplica» con una razón entre corchetes → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-45",
                    PLAN_MODULO + "\nGate F: no aplica — [pendiente de decidir con el cliente]\n",
                )
            ),
        ),
        (
            "F-47 «sin token» es un endpoint abierto → rojo",
            1,
            lambda: revisa_plan(
                plan("f-47", "# Plan · widget\n\nLa API del widget queda abierta, sin token.\n")
            ),
        ),
        (
            "F-48 «suben fotos» es una subida de ficheros → rojo",
            1,
            lambda: revisa_plan(
                plan("f-48", "# Plan · socios\n\nLos socios suben fotos del local desde la app.\n")
            ),
        ),
        (
            "F-49 un IBAN es un dato personal → rojo",
            1,
            lambda: revisa_plan(
                plan("f-49", "# Plan · cobros\n\nSe guarda el IBAN del socio para domiciliar.\n")
            ),
        ),
        (
            "F-50 la pregunta se borra y el resto de la línea cuenta → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f-50",
                    "# Plan · avisos\n\n- ¿Hace falta un webhook? Sí, se añade el webhook de "
                    "Stripe para los avisos.\n",
                )
            ),
        ),
        (
            "F-51 una pregunta sin cerrar → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f-51",
                    "# Plan · pagos\n\n- ¿Hace falta un webhook de Stripe o basta el enlace de "
                    "pago\n",
                )
            ),
        ),
        (
            "F-52 una pregunta sin «¿» → calla",
            0,
            lambda: revisa_plan(
                plan("f-52", "# Plan · pagos\n\n- Do we need a webhook from Stripe?\n")
            ),
        ),
        ("F-46 «modelo en» al ejemplo de la skill (comodín) → rojo", 1, _modelo_comodin),
        (
            "F-53 «no aplica» con cuatro palabras pero menos de 20 caracteres → rojo",
            1,
            lambda: revisa_plan(
                plan("f53", PLAN_MODULO + "\nGate F: no aplica — solo una demo así\n")
            ),
        ),
        # — los de la tercera pasada del verificador (21-10) —
        (
            "F-54 «(los reembolsos quedan fuera)» tapa solo su paréntesis → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f54",
                    "# Plan · cobros\n\nSe añade el webhook de Stripe para los avisos de pago "
                    "(los reembolsos quedan fuera).\n",
                )
            ),
        ),
        (
            "F-55 «…, salvo las nóminas, que quedan fuera» tapa solo la salvedad → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f55",
                    "# Plan · contabilidad\n\nIntegración con Holded para las facturas, salvo las "
                    "nóminas, que quedan fuera de este plan.\n",
                )
            ),
        ),
        (
            "F-56 «Stripe, Holded y el webhook, que quedan fuera de este plan» → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f56",
                    "# Plan · checkout\n\nPaginación del listado.\n\nStripe, Holded y el webhook "
                    "de pagos, que quedan fuera de este plan.\n",
                )
            ),
        ),
        (
            "F-57 «Sin dependencias externas salvo Stripe» → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f57",
                    "# Plan · checkout\n\nSin dependencias externas salvo Stripe, que cobra la "
                    "cuota mensual.\n",
                )
            ),
        ),
        (
            "F-58 «Se corrige el alta: ahora … DNI en un formulario público» → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f58",
                    "# Plan · admisión\n\nSe corrige el flujo de alta: ahora los pacientes "
                    "rellenan su DNI en un formulario público.\n",
                )
            ),
        ),
        (
            "F-59 un «# Fix» que migra el cobro a Stripe → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f59",
                    "# Fix: los pagos con tarjeta fallan desde el cambio del banco\n\nSe migra el "
                    "cobro a Stripe Checkout y se recibe su webhook.\n",
                )
            ),
        ),
        (
            "F-60 «## Fuera de alcance» y después «lo que sí se hace» → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f60",
                    "# Plan · pagos\n\n## Fuera de alcance\n\n- Reembolsos.\n\nY lo que sí se "
                    "hace: se añade el webhook de Stripe.\n",
                )
            ),
        ),
        (
            "F-61 «**Fuera de alcance:**» en negrita abre su lista → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f61",
                    "# Plan · paginación\n\nPaginación por cursor en el listado.\n\n**Fuera de "
                    "alcance:**\n\n- Los pagos con Stripe.\n- El webhook de Holded.\n",
                )
            ),
        ),
        (
            "F-62 «- Fuera de alcance: Stripe y …» en la propia línea → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f62",
                    "# Plan · paginación\n\nPaginación por cursor en el listado.\n\n- Fuera de "
                    "alcance: Stripe y el webhook de Holded.\n",
                )
            ),
        ),
        (
            "F-63 un «# Refactor ·» que nombra `views/webhook.py` → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f63",
                    "# Refactor del módulo de vistas\n\n- `views/webhook.py`: el webhook existente "
                    "se mueve sin cambios.\n",
                )
            ),
        ),
        (
            "F-64 «el webhook existente» calla también su ruta → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f64",
                    "# Plan · ordenar las vistas\n\nEl webhook existente queda en "
                    "`views/webhook.py`.\n",
                )
            ),
        ),
        (
            "F-65 «el bot NO cobra»: la negación va dentro de la mención → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f65",
                    "# Plan · guardarraíles del bot\n\n- **#5 el bot NO cobra**: solo da el enlace "
                    "de pago.\n",
                )
            ),
        ),
        ("F-66 «suben su CV» es una subida de ficheros → rojo", 1, _cv),
        (
            "F-80 «hoy ya hay un webhook» calla aunque la cláusula añada otra cosa → calla",
            0,
            lambda: revisa_plan(
                plan(
                    "f80",
                    "# Plan · pedidos\n\nHoy ya hay un webhook de Stripe y se añade un panel nuevo "
                    "de pedidos.\n",
                )
            ),
        ),
        (
            "F-79 «no aplica» no tapa un modelo roto que está en la carpeta → rojo",
            1,
            lambda: revisa_plan(
                plan(
                    "f79",
                    PLAN_MODULO
                    + "\nGate F: no aplica — el detector se equivoca en este plan concreto\n",
                    MODELO_BUENO.replace("v5.0.0-8.2.2", "v5.0.0-8.9.9", 1),
                )
            ),
        ),
    ]
    # Vocabulario de spec que no decía «integración», «público» ni «tool» (verificador, 3.ª pasada).
    vocabulario = [
        "Los empleados entran con su cuenta de Google.",
        "Cualquier visitante, sin registrarse, deja una reseña con su nombre.",
        "La ficha del socio guarda nombre, apellidos y móvil.",
        "El cobro se hace por la pasarela de pago del banco (TPV virtual).",
        "El cliente paga con Bizum al reservar.",
        "Las altas del boletín se envían a Mailchimp.",
        "El asistente crea la cita en la agenda del profesional.",
        "La página de seguimiento del pedido no requiere login: basta el número de pedido.",
        "Los partners consultan el stock con una API key propia.",
        "Cada franquicia tiene sus datos aislados de las demás.",
        "Se guarda la dirección de envío del cliente.",
        "El agente publica el post en LinkedIn cuando el cliente lo aprueba.",
    ]
    casos += [
        (
            f"F-{67 + i} «{fr}» → rojo",
            1,
            lambda fr=fr, i=i: revisa_plan(
                plan(f"f{67 + i}", f"# Spec · requisitos\n\n- **RF-01** {fr}\n")
            ),
        )
        for i, fr in enumerate(vocabulario)
    ]
    # — los de la cuarta pasada del verificador (21-10): 1 = dispara, 0 = calla —
    planes_4 = [
        ("F-81 «No entran en este plan los reembolsos: el webhook se añade ya»", 1,
         "No entran en este plan los reembolsos: el webhook de Stripe se añade ya."),
        ("F-82 «Fuera de alcance los reembolsos: aquí solo el webhook»", 1,
         "Fuera de alcance los reembolsos: aquí solo el webhook de Stripe."),
        ("F-83 «El bot, si el cliente no paga, cancela la reserva»: el «no» no es del bot", 1,
         "El bot, si el cliente no paga en 15 minutos, cancela la reserva."),
        ("F-84 «mover las citas desde el formulario público» no es un refactor", 1,
         "Se permite mover las citas desde el formulario público."),
        ("F-85 «partir el pago en tres plazos con Stripe» no es un refactor", 1,
         "El cliente puede partir el pago en tres plazos con Stripe."),
        ("F-86 «Se añade el webhook y los reembolsos quedan fuera»", 1,
         "Se añade el webhook de Stripe y los reembolsos quedan fuera."),
        ("F-87 «Se integra Holded y las nóminas quedan fuera»", 1,
         "Se integra Holded y las nóminas quedan fuera de este plan."),
        ("F-88 «Sin otros terceros que Stripe»", 1,
         "Sin otros terceros que Stripe, que cobra la cuota."),
        ("F-89 «Fuera de alcance:» a secas abre su lista", 0,
         "Paginación del listado.\n\nFuera de alcance:\n\n- Los pagos con Stripe.\n"
         "- El webhook de Holded."),
        ("F-90 «lo que sí entra en la v2» no reabre la sección", 0,
         "Paginación del listado.\n\n## Fuera de alcance\n\n- Lo que sí entra en la v2: el "
         "webhook de Stripe."),
        ("F-91 «un día sin registrar su peso» no es un endpoint abierto", 0,
         "Un día sin registrar su peso no rompe la racha."),
        ("F-92 «se ve bien en su móvil» no es un dato personal", 0,
         "La pantalla de progreso se ve bien en su móvil."),
        ("F-93 «el bot escribe la respuesta», «el asistente crea un resumen»: sin efecto", 0,
         "El bot escribe la respuesta con el tono de la marca.\n\nEl asistente crea un resumen "
         "de la conversación."),
        ("F-94 «su LinkedIn» en la ficha del ponente no es una integración", 0,
         "El ponente enlaza su LinkedIn en la ficha."),
        ("F-95 «- `pagos/webhook.py`: sin cambios» habla de lo que ya hay", 0,
         "Paginación del listado.\n\n- `pagos/webhook.py`: sin cambios."),
        ("F-96 «# Plan · partir views.py» que nombra el webhook existente", 0,
         "- `views/webhook.py`: el webhook existente se mueve sin cambios."),
        ("F-97 «los pacientes» son datos personales en un plan", 1,
         "Se lleva la agenda de los pacientes del centro."),
        ("F-98 la matrícula del coche y el número de tarjeta", 1,
         "Se guarda la matrícula del coche y el número de tarjeta del socio."),
    ]
    casos += [
        (
            f"{nombre} → {'rojo' if esperado else 'calla'}",
            esperado,
            lambda n=nombre, tx=texto: revisa_plan(
                plan(
                    n[:4].lower(),
                    ("# Plan · partir views.py" if n.startswith("F-96") else "# Plan · pedidos")
                    + "\n\n" + tx + "\n",
                )
            ),
        )
        for nombre, esperado, texto in planes_4
    ]
    # — El modelo: cada sabotaje tiene que caer —
    # Cada sabotaje: (trozo del modelo bueno, por qué se cambia, qué dice el PRIMER error).
    # Que salga rojo no basta: tiene que salir rojo por SU motivo, no por otro error que arrastró.
    sabotajes = {
        "M-01 ID de ASVS inventado": (
            "v5.0.0-8.2.2",
            "v5.0.0-8.9.9",
            "fila 2: v5.0.0-8.9.9 no existe",
        ),
        "M-02 ID de ASVS sin la versión delante": ("v5.0.0-8.2.2 |", "V8.2.2 |", "sin la versión"),
        "M-03 mitigar sin requisito ASVS": ("| v5.0.0-6.3.1 |", "| — |", "sin requisito ASVS"),
        "M-04 mitigar sin cómo se prueba": ("| test_idor_citas |", "| — |", "cómo se prueba"),
        "M-05 respuesta que no es de OWASP": (
            "| I | un paciente ve las citas de otro por id | mitigar",
            "| I | un paciente ve las citas de otro por id | revisar",
            "respuesta «revisar»",
        ),
        "M-06 letra que no es STRIDE": ("| F1 | S |", "| F1 | X |", "no es una letra"),
        "M-07 frontera declarada y sin fila STRIDE": (
            "| F2 | T | aviso de pago falsificado",
            "| F1 | T | aviso de pago falsificado",
            "F2 no tiene ninguna fila",
        ),
        "M-08 fila STRIDE con frontera sin declarar": (
            "| F3 | D |",
            "| F9 | D |",
            "«F9» no declarada",
        ),
        "M-09 carta de LINDDUN inventada": (
            "| DD2 EXCESSIVE",
            "| DD9 EXCESSIVE",
            "no es una carta",
        ),
        "M-10 datos personales sin LINDDUN": (MODELO_BUENO, sin_linddun, "sin tabla de LINDDUN"),
        "M-11 agente con [A][B][C] y sin control": (
            "| `interrupt()` y confirmación del paciente |",
            "| lo vigila el log |",
            "ningún control",
        ),
        "M-12 sin nivel ASVS": ("asvs_nivel: L2", "asvs_nivel: alto", "`asvs_nivel`"),
        "M-13 sin firmar": ("reviewed_by: Ana Ruiz\n", "", "sin firmar"),
        "M-14 un hueco de plantilla": ("asistente de reservas |", "<nombre> |", "hueco"),
        "M-15 aceptar sin razón": (
            "tope de 10 llamadas por turno ya en el grafo; se acepta el resto",
            "sí",
            "sin la razón",
        ),
        "M-16 dice que no hay agentes y la frontera es de un LLM": (
            "agentes_llm: sí",
            "agentes_llm: no",
            "agentes_llm: no`, y el modelo habla de",
        ),
        "M-17 dice que no hay datos personales y cruza un email": (
            "datos_personales: sí",
            "datos_personales: no",
            "`datos_personales: no`",
        ),
        "M-18 asvs_extra con un ID inventado": (
            "asvs_extra: v5.0.0-4.1.5, v5.0.0-8.3.3",
            "asvs_extra: v5.0.0-99.1.1",
            "`asvs_extra`",
        ),
        "M-19 carta LINDDUN en una frontera sin declarar": (
            "| DD2 EXCESSIVE AMOUNT OF DATA COLLECTED | F1 |",
            "| DD2 EXCESSIVE AMOUNT OF DATA COLLECTED | F7 |",
            "LINDDUN fila 1: frontera no declarada",
        ),
        "M-20 carta LINDDUN sin defensa": (
            "| no se pide DNI |",
            "| |",
            "LINDDUN fila 1: sin defensa",
        ),
        "M-21 fila STRIDE sin amenaza": (
            "| fuerza bruta contra el acceso del paciente |",
            "| |",
            "sin amenaza",
        ),
        "M-22 mitigar sin defensa": (
            "| límite de intentos y bloqueo con aviso |",
            "| |",
            "sin defensa decidida",
        ),
        "M-23 [A] que no es sí ni no": (
            "| sí: texto del paciente |",
            "| quizá |",
            "empiezan por sí o no",
        ),
        "M-24 datos_personales que no es sí ni no": (
            "datos_personales: sí",
            "datos_personales: a veces",
            "`datos_personales` tiene que ser",
        ),
        "M-25 frontera con id mal formado": ("| F2 | Stripe", "| P2 | Stripe", "«P2»"),
        "M-26 riesgo del modelo inventado (LLM11)": (
            "| v5.0.0-8.3.3 | test_hitl_reserva |",
            "| LLM11 | test_hitl_reserva |",
            "«LLM11» no existe",
        ),
        # — los de la primera ronda de auditores (20-10) —
        "M-27 control negado («sin confirmación humana»)": (
            "| `interrupt()` y confirmación del paciente |",
            "| ninguno: sin confirmación humana, opera solo |",
            "ningún control",
        ),
        "M-28 asvs_extra sin la versión": (
            "asvs_extra: v5.0.0-4.1.5, v5.0.0-8.3.3",
            "asvs_extra: 8.9.9",
            "`asvs_extra` tiene que ser",
        ),
        "M-29 firmante vacío": ("reviewed_by: Ana Ruiz", 'reviewed_by: ""', "sin firmar"),
        "M-30 fecha de firma imposible": (
            "reviewed: 2026-10-20",
            "reviewed: 2026-13-45",
            "fecha real",
        ),
        "M-31 id inventado en una fila «aceptar»": (
            "se acepta el resto | — |",
            "se acepta el resto | v5.0.0-2.4.9 |",
            "v5.0.0-2.4.9 no existe",
        ),
        "M-32 un id sin versión junto a uno válido": (
            "| v5.0.0-8.2.2 | test_idor_citas |",
            "| v5.0.0-8.2.2, V8.4.1 | test_idor_citas |",
            "«8.4.1» sin la versión",
        ),
        "M-33 id inventado en la prosa": (
            "La denegación de servicio por llamadas encadenadas",
            "La denegación de servicio (v5.0.0-2.4.9) por llamadas encadenadas",
            "v5.0.0-2.4.9, citado en el modelo, no existe",
        ),
        "M-34 la carta con un nombre que no es el suyo": (
            "| D4 DETECTABLE RECORDS |",
            "| D4 CARTA QUE NO EXISTE |",
            "se llama",
        ),
        # — los de la segunda pasada del verificador (20-10) —
        "M-35 sin tabla de fronteras (la de STRIDE no vale por ella)": (
            MODELO_BUENO,
            MODELO_BUENO[: MODELO_BUENO.index("| Id | Frontera")]
            + MODELO_BUENO[MODELO_BUENO.index("## 2. STRIDE") :],
            "sin tabla de fronteras",
        ),
        "M-36 una segunda tabla STRIDE también se mira": (
            "## 3. LINDDUN GO",
            "| Frontera | STRIDE | Amenaza | Respuesta | Defensa decidida | ASVS | Cómo se prueba "
            "|\n"
            "|---|---|---|---|---|---|---|\n"
            "| F1 | Q | otra amenaza | mitigar | otra defensa | v5.0.0-8.2.2 | test_otro |\n\n"
            "## 3. LINDDUN GO",
            "«Q» no es una letra",
        ),
        "M-38 control «opcional» no es control": (
            "| `interrupt()` y confirmación del paciente |",
            "| confirmación opcional |",
            "ningún control",
        ),
        "M-39 «nadie lo aprueba» no es control": (
            "| `interrupt()` y confirmación del paciente |",
            "| nadie lo aprueba, opera solo |",
            "ningún control",
        ),
        "M-49 «validación del JSON» no es un control humano": (
            "| `interrupt()` y confirmación del paciente |",
            "| validación del JSON de salida |",
            "ningún control",
        ),
        "M-40 mitigar con la defensa «—»": (
            "| límite de intentos y bloqueo con aviso |",
            "| — |",
            "sin defensa decidida",
        ),
        "M-41 mitigar con la prueba «n/a»": ("| test_idor_citas |", "| n/a |", "cómo se prueba"),
        "M-42 aceptar con una razón de puntos": (
            "tope de 10 llamadas por turno ya en el grafo; se acepta el resto",
            "...............",
            "sin la razón",
        ),
        "M-43 carta LINDDUN sin amenaza concreta": (
            "| pedir DNI para una cita |",
            "| — |",
            "LINDDUN fila 1: sin amenaza",
        ),
        "M-44 frontera sin «qué cruza»": (
            "| nombre, teléfono y email del paciente |",
            "| — |",
            "sin «qué cruza»",
        ),
        "M-45 un id «V14.9.9» sin versión en LINDDUN": (
            "| RGPD art. 5.1.c |",
            "| V14.9.9 |",
            "«V14.9.9» sin la versión",
        ),
        "M-47 firmante «—»": ("reviewed_by: Ana Ruiz", "reviewed_by: —", "sin firmar"),
        "M-48 fecha de firma futura": ("reviewed: 2026-10-20", "reviewed: 2099-01-01", "no futura"),
        # — los de la tercera pasada del verificador (21-10) —
        "M-50 defensa «Pendiente de decidir»": (
            "| límite de intentos y bloqueo con aviso |",
            "| Pendiente de decidir |",
            "sin defensa decidida",
        ),
        "M-51 prueba «sin test»": ("| test_idor_citas |", "| sin test |", "cómo se prueba"),
        "M-52 defensa «se decidirá en el sprint 3»": (
            "| filtrar por el dueño en el queryset |",
            "| se decidirá en el sprint 3 |",
            "sin defensa decidida",
        ),
        "M-53 firmante «pendiente de revisión»": (
            "reviewed_by: Ana Ruiz",
            "reviewed_by: pendiente de revisión",
            "sin firmar",
        ),
        "M-54 firmante «el propio agente»": (
            "reviewed_by: Ana Ruiz",
            "reviewed_by: el propio agente",
            "una persona",
        ),
        "M-55 control «confirmación humana (todavía no implementada)»": (
            "| `interrupt()` y confirmación del paciente |",
            "| confirmación humana (todavía no implementada) |",
            "ningún control",
        ),
        "M-56 control «el agente se confirma a sí mismo»": (
            "| `interrupt()` y confirmación del paciente |",
            "| el agente se confirma a sí mismo |",
            "ningún control",
        ),
        "M-57 control «aprobación automática del pago»": (
            "| `interrupt()` y confirmación del paciente |",
            "| aprobación automática del pago |",
            "ningún control",
        ),
        "M-58 control «interrupt() — por implementar en la v2»": (
            "| `interrupt()` y confirmación del paciente |",
            "| `interrupt()` — por implementar en la v2 |",
            "ningún control",
        ),
        "M-59 control «confirmación humana: no»": (
            "| `interrupt()` y confirmación del paciente |",
            "| confirmación humana: no |",
            "ningún control",
        ),
        "M-70 «falta la aprobación del gestor» no es control": (
            "| `interrupt()` y confirmación del paciente |",
            "| falta la aprobación del gestor |",
            "ningún control",
        ),
        "M-60 tabla de fronteras sin la columna «Qué cruza»": (
            "| Id | Frontera (de → a) | Qué cruza |",
            "| Id | Frontera (de → a) | Datos |",
            "sin la columna «Qué cruza»",
        ),
        "M-61 un id de cuatro niveles": (
            "| v5.0.0-8.2.2 |",
            "| v5.0.0-8.2.2.1 |",
            "cuatro niveles",
        ),
        "M-62 una fila «aceptar» y la §5 dice «Nada.»": (
            "La denegación de servicio por llamadas encadenadas, con el tope que ya hay.",
            "Nada.",
            "§5",
        ),
        "M-69 aceptar con «Pendiente de decidir quién lo acepta»": (
            "tope de 10 llamadas por turno ya en el grafo; se acepta el resto",
            "Pendiente de decidir quién lo acepta",
            "sin la razón",
        ),
    }
    # — los de la cuarta pasada (21-10): controles que no lo son, rellenos que lo son, firmas de
    # agente, la §5, ids de otra versión —
    for nombre, nuevo, motivo in [
        ("M-71 control «el bot valida la petición del usuario»", "el bot valida la petición del "
         "usuario", "ningún control"),
        ("M-72 control «el modelo autoriza al usuario según su historial»", "el modelo autoriza al "
         "usuario según su historial", "ningún control"),
        ("M-73 control «el usuario puede revisar el historial después»", "el usuario puede revisar "
         "el historial después", "ningún control"),
        ("M-74 control «revisión del equipo si da tiempo»", "revisión del equipo si da tiempo",
         "ningún control"),
        ("M-75 control «el agente confirma la reserva al usuario»", "el agente confirma la reserva "
         "al usuario por WhatsApp", "ningún control"),
        ("M-76 control «un segundo LLM revisa la respuesta»", "un segundo LLM revisa la respuesta "
         "antes de enviarla", "ningún control"),
        ("M-85 control «confirmación del usuario (planificada)»", "confirmación del usuario "
         "(planificada)", "ningún control"),
        ("M-90 control «se asume la aprobación del cliente»", "se asume la aprobación del "
         "cliente", "ningún control"),
        ("M-91 control «el pedido lo confirma el agente»", "el pedido lo confirma el agente",
         "ningún control"),
    ]:
        sabotajes[nombre] = (
            "| `interrupt()` y confirmación del paciente |",
            f"| {nuevo} |",
            motivo,
        )
    sabotajes.update(
        {
            "M-77 firmante «claude-opus-5-5»": (
                "reviewed_by: Ana Ruiz", "reviewed_by: claude-opus-5-5", "es un agente"
            ),
            "M-78 firmante «Tech Lead (agente)»": (
                "reviewed_by: Ana Ruiz", "reviewed_by: Tech Lead (agente)", "es un agente"
            ),
            "M-79 firmante «nadie aún»": (
                "reviewed_by: Ana Ruiz", "reviewed_by: nadie aún", "no es quién lo revisó"
            ),
            "M-80 defensa «pendiente (H1): por decidir»": (
                "| filtrar por el dueño en el queryset |",
                "| pendiente (H1): por decidir |",
                "sin defensa decidida",
            ),
            "M-81 prueba «No hay test»": (
                "| test_idor_citas |", "| No hay test |", "cómo se prueba"
            ),
            "M-82 una fila «aceptar» y la §5 «No se acepta ningún riesgo.»": (
                "La denegación de servicio por llamadas encadenadas, con el tope que ya hay.",
                "No se acepta ningún riesgo.",
                "§5",
            ),
            "M-83 un id de otra versión de ASVS": (
                "| RGPD art. 5.1.c |", "| v4.0.3-8.3.1 |", "otra versión de ASVS"
            ),
            "M-89 firmante «sofia-pentester»": (
                "reviewed_by: Ana Ruiz", "reviewed_by: sofia-pentester", "es un agente"
            ),
            "M-84 una fila «aceptar» y el modelo sin §5": (
                "## 5. Aceptado\n\nLa denegación de servicio por llamadas encadenadas, con el tope "
                "que ya hay.\n\n",
                "",
                "no tiene §5",
            ),
        }
    )
    for nombre, (viejo, nuevo, motivo) in sabotajes.items():

        def _sab(v=viejo, nv=nuevo, mo=motivo, n=nombre) -> dict:
            r = revisa_modelo(modelo(n[:4], sab((v, nv))))
            primero = (r.get("errores") or [r["por_que"]])[0]
            if r["estado"] == NO_CUMPLE and mo not in primero:
                return _resultado(CUMPLE, f"rojo por OTRO motivo: «{primero}» (esperaba «{mo}»)")
            return r

        casos.append((nombre + " → rojo por su motivo", 1, _sab))
    casos += [
        ("C-01 el modelo bueno → verde", 0, lambda: revisa_modelo(modelo("c01", MODELO_BUENO))),
        (
            "C-02 agente con solo dos de tres, sin control → verde",
            0,
            lambda: revisa_modelo(
                modelo(
                    "c02",
                    sab(
                        (
                            "| sí: crea la cita | `interrupt()` y confirmación del paciente |",
                            "| no: solo propone | — |",
                        )
                    ),
                )
            ),
        ),
        (
            "C-03 `<token>` dentro de código no es un hueco → verde",
            0,
            lambda: revisa_modelo(
                modelo(
                    "c03",
                    sab(
                        (
                            "firma `Stripe-Signature` comprobada",
                            "firma `Stripe-Signature: <token>` comprobada",
                        )
                    ),
                )
            ),
        ),
        (
            "C-04 sin datos personales ni agentes, sin sus tablas → verde",
            0,
            lambda: revisa_modelo(modelo("c04", vacia)),
        ),
        ("C-05 la plantilla tal cual → rojo (por sus huecos)", 1, lambda: revisa_modelo(PLANTILLA)),
        (
            "C-06 amenaza del modelo citada como LLM06:2025, sin ASVS → verde",
            0,
            lambda: revisa_modelo(
                modelo(
                    "c06",
                    sab(
                        (
                            "| v5.0.0-8.3.3 | test_hitl_reserva |",
                            "| LLM06:2025 | test_hitl_reserva |",
                        )
                    ),
                )
            ),
        ),
        (
            "C-07 frontmatter con comentarios en línea (el ejemplo de la SKILL) → verde",
            0,
            lambda: revisa_modelo(
                modelo("c07", sab(("asvs_nivel: L2", "asvs_nivel: L2                # del tipo")))
            ),
        ),
        ("C-08 un L3 citado y no declarado en asvs_extra → verde CON aviso", 0, _aviso_nivel),
        (
            "M-37 `agentes_llm: no` con una tabla Rule of Two que describe un agente → rojo",
            1,
            _dos_cambios(
                [
                    ("agentes_llm: sí", "agentes_llm: no"),
                    (
                        "| F3 | Asistente LLM → tool `reservar_cita` | la cita que propone el "
                        "modelo | "
                        "el modelo, que lee texto del paciente |",
                        "| F3 | Servicio de citas → agenda | la cita elegida | la agenda de la "
                        "clínica |",
                    ),
                ],
                "la tabla Rule of Two describe un agente",
            ),
        ),
        (
            "M-46 `datos_personales: no` y un IBAN en la frontera → rojo",
            1,
            _dos_cambios(
                [("la fecha y la hora elegidas", "el IBAN del paciente")],
                "`datos_personales: no`",
                vacia,
            ),
        ),
        # — los de la tercera pasada del verificador (21-10) —
        (
            "M-63 `agentes_llm: no` y la cabecera «[A] entrada no confiable…» → rojo",
            1,
            _dos_cambios(
                [
                    ("agentes_llm: sí", "agentes_llm: no"),
                    (
                        "| F3 | Asistente LLM → tool `reservar_cita` | la cita que propone el "
                        "modelo | el modelo, que lee texto del paciente |",
                        "| F3 | Servicio de citas → agenda | la cita elegida | la agenda de la "
                        "clínica |",
                    ),
                    (
                        "| Agente (sesión) | [A] | [B] | [C] |",
                        "| Agente (sesión) | [A] entrada no confiable | [B] datos privados | [C] "
                        "efecto |",
                    ),
                    ("| `interrupt()` y confirmación del paciente |", "| — |"),
                ],
                "la tabla Rule of Two describe un agente",
            ),
        ),
        (
            "M-64 `datos_personales: no` y una amenaza con el email y el teléfono → rojo",
            1,
            _dos_cambios(
                [
                    (
                        "un paciente ve las citas de otro por id",
                        "un paciente ve el email y el teléfono de otro",
                    )
                ],
                "`datos_personales: no`",
                vacia,
            ),
        ),
        (
            "M-65 `datos_personales: no` y una tabla de LINDDUN → rojo",
            1,
            _dos_cambios(
                [
                    (
                        "| test_firma_mala |",
                        "| test_firma_mala |\n\n## 3. LINDDUN GO\n\n| Carta | Frontera | Amenaza "
                        "concreta | Defensa decidida | Base legal o ASVS |\n|---|---|---|---|---|\n"
                        "| D4 DETECTABLE RECORDS | F1 | «ese día ya está cogido» delata una cita | "
                        "la misma respuesta siempre | RGPD art. 5.1.f |",
                    )
                ],
                "hay una tabla de LINDDUN",
                vacia,
            ),
        ),
        (
            "M-66 `datos_personales: no` y «número de móvil» en la frontera → rojo",
            1,
            _dos_cambios(
                [("la fecha y la hora elegidas", "la fecha elegida y su número de móvil")],
                "`datos_personales: no`",
                vacia,
            ),
        ),
        (
            "M-67 `agentes_llm: no` y un GPT al otro lado de la frontera → rojo",
            1,
            _dos_cambios(
                [("| cualquiera en internet |", "| el modelo GPT-4o, que lee la reserva |")],
                "`agentes_llm: no`",
                vacia,
            ),
        ),
        (
            "M-68 `agentes_llm: no` y una IDOR citada como LLM05 → rojo",
            1,
            _dos_cambios(
                [("| v5.0.0-8.2.2 |", "| LLM05 |")],
                "sustituye a ASVS solo donde hay un agente",
                vacia,
            ),
        ),
        (
            "C-09 «**pendiente (H1):** <la defensa>» es una defensa decidida → verde",
            0,
            lambda: revisa_modelo(
                modelo(
                    "c09",
                    sab(
                        (
                            "| filtrar por el dueño en el queryset |",
                            "| **pendiente (H1):** filtrar por el dueño en el queryset |",
                        )
                    ),
                )
            ),
        ),
        (
            "C-10 «el gestor de la clínica aprueba la cita» es un control → verde",
            0,
            lambda: revisa_modelo(
                modelo(
                    "c10",
                    sab(
                        (
                            "| `interrupt()` y confirmación del paciente |",
                            "| el gestor de la clínica aprueba la cita antes de crearla |",
                        )
                    ),
                )
            ),
        ),
        (
            "C-11 «confirmación humana: no se crea nada sin ella» es un control → verde",
            0,
            lambda: revisa_modelo(
                modelo(
                    "c11",
                    sab(
                        (
                            "| `interrupt()` y confirmación del paciente |",
                            "| confirmación humana: no se crea nada sin ella |",
                        )
                    ),
                )
            ),
        ),
        (
            "M-86 `agentes_llm: no` y una cabecera «| Agente | A | B | C |» sin corchetes → rojo",
            1,
            _dos_cambios(
                [
                    ("agentes_llm: sí", "agentes_llm: no"),
                    (
                        "| F3 | Asistente LLM → tool `reservar_cita` | la cita que propone el "
                        "modelo | el modelo, que lee texto del paciente |",
                        "| F3 | Servicio de citas → agenda | la cita elegida | la agenda de la "
                        "clínica |",
                    ),
                    ("| Agente (sesión) | [A] | [B] | [C] |", "| Agente (sesión) | A | B | C |"),
                    ("| `interrupt()` y confirmación del paciente |", "| — |"),
                ],
                "la tabla Rule of Two describe un agente",
            ),
        ),
        (
            "M-87 `datos_personales: no` y «correo electrónico» (la lista del plan) → rojo",
            1,
            _dos_cambios(
                [("la fecha y la hora elegidas", "la fecha y el correo electrónico")],
                "`datos_personales: no`",
                vacia,
            ),
        ),
        (
            "M-88 `agentes_llm: no` y una «inyección de prompt» en una amenaza → rojo",
            1,
            _dos_cambios(
                [
                    (
                        "fuerza bruta contra el acceso del paciente",
                        "inyección de prompt en el texto de la reserva",
                    )
                ],
                "`agentes_llm: no`",
                vacia,
            ),
        ),
        (
            "C-20 `agentes_llm: no` y «un agente de amenaza externo» en una amenaza → verde",
            0,
            lambda: revisa_modelo(
                modelo(
                    "c20",
                    vacia.replace(
                        "fuerza bruta contra el acceso del paciente",
                        "un agente de amenaza externo prueba contraseñas",
                    ),
                )
            ),
        ),
        (
            "C-12 `interrupt()` solo, sin persona nombrada, es un control → verde",
            0,
            lambda: revisa_modelo(
                modelo(
                    "c12",
                    sab(
                        (
                            "| `interrupt()` y confirmación del paciente |",
                            "| `interrupt()` antes de crear la cita |",
                        )
                    ),
                )
            ),
        ),
    ]
    ctrl = "| `interrupt()` y confirmación del paciente |"
    for nombre, cambio in [
        ("C-13 «el supervisor aprueba cada anulación»", (ctrl, "| el supervisor aprueba cada "
         "cita antes de crearla |")),
        ("C-14 «lo aprueba la recepcionista»", (ctrl, "| la cita la aprueba la recepcionista "
         "antes de crearla |")),
        ("C-15 «confirmación explícita del paciente, no automática»", (ctrl, "| confirmación "
         "explícita del paciente, no automática |")),
        ("C-16 «sin la aprobación del gestor no se crea ninguna cita»", (ctrl, "| sin la "
         "aprobación del gestor no se crea ninguna cita |")),
        ("C-17 «el agente humano de recepción revisa la cita»", (ctrl, "| el agente humano de "
         "recepción revisa la cita |")),
        ("C-18 firmante «Claude Martin», una persona", ("reviewed_by: Ana Ruiz",
         "reviewed_by: Claude Martin")),
        ("C-19 firmante «Ana Ruiz, revisado con ayuda de Claude»", ("reviewed_by: Ana Ruiz",
         "reviewed_by: Ana Ruiz, revisado con ayuda de Claude")),
        ("C-21 prueba «No se prueba en CI; se prueba a mano con curl»", ("| test_idor_citas |",
         "| No se prueba en CI; se prueba a mano con curl |")),
        ("C-22 firmante «Bot García», una persona", ("reviewed_by: Ana Ruiz",
         "reviewed_by: Bot García")),
    ]:
        casos.append(
            (
                nombre + " → verde",
                0,
                lambda c=cambio, n=nombre: revisa_modelo(modelo(n[:4], sab(c))),
            )
        )
    # — El subconjunto ASVS y los catálogos —
    d = asvs()

    def _asvs_casos() -> dict:
        l1, l2 = subconjunto("L1", [], []), subconjunto("L2", [], [])
        salud = subconjunto(*TIPOS["salud"][:1], [], TIPOS["salud"][1])
        ok = (
            l1["total"] < l2["total"]
            and salud["total"] == l2["total"] + len(L3_SALUD)
            and all(d["requisitos"][i]["L"] == 3 for i in L3_SALUD)
            and "v5.0.0-8.3.3" in subconjunto("L2", [], TIPOS["bot"][1])["ids"]
        )
        return _resultado(
            CUMPLE if ok else NO_CUMPLE,
            f"L1 {l1['total']} · L2 {l2['total']} · salud {salud['total']}",
        )

    def _catalogos() -> dict:
        cartas = cartas_linddun()
        # Y los títulos son los de la baraja: dos de control, uno al principio y otro al final.
        ok = (
            len(d["requisitos"]) == 345
            and len(cartas) == 33
            and d["version"] == "5.0.0"
            and cartas.get("L1") == "LINKED USER REQUESTS"
            and cartas.get("Nc4") == "INSUFFICIENT SECURITY OF PROCESSING"
            and cartas.get("U1") == "INSUFFICIENT TRANSPARENCY"
        )
        return _resultado(
            CUMPLE if ok else NO_CUMPLE, f"{len(d['requisitos'])} requisitos · {len(cartas)} cartas"
        )

    def _tabla_tipos() -> dict:
        """La tabla legible de asvs-por-tipo.md y TIPOS dicen lo mismo."""
        vistos = {}
        for l in ASVS_TIPOS_MD.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*`([a-z-]+)`\s*\|(.*)$", l)
            if m and m.group(1) in TIPOS:
                celdas = [c.strip() for c in m.group(2).split("|")]
                nivel = next(
                    (c for c in celdas if re.fullmatch(r"\*{0,2}L[123]\*{0,2}", c)), ""
                ).strip("*")
                vistos[m.group(1)] = (
                    nivel,
                    sorted(
                        ID_ASVS.findall(" ".join(celdas)),
                        key=lambda x: [int(y) for y in x.split(".")],
                    ),
                )
        esperado = {
            k: (v[0], sorted(v[1], key=lambda x: [int(y) for y in x.split(".")]))
            for k, v in TIPOS.items()
        }
        return _resultado(
            CUMPLE if vistos == esperado else NO_CUMPLE,
            "coinciden" if vistos == esperado else f"md {vistos} ≠ script {esperado}",
        )

    casos += [
        ("A-01 subconjuntos L1 < L2 < salud y extras de nivel 3", 0, _asvs_casos),
        ("A-02 catálogos: 345 requisitos ASVS 5.0.0 y 33 cartas", 0, _catalogos),
        ("A-03 la tabla de tipos del md = la del script", 0, _tabla_tipos),
    ]

    ok = ko = 0
    for nombre, esperado, f in casos:
        try:
            r = f()
            obtenido = sale(r)
        except Exception as e:  # noqa: BLE001 — la autoprueba informa
            r, obtenido = {"por_que": f"excepción: {e!r}"}, 3
        bien = obtenido == esperado
        ok, ko = ok + bien, ko + (not bien)
        print(
            f"  {'✓' if bien else '✗'} {nombre}"
            + ("" if bien else f"  (salió {obtenido}: {r.get('por_que')})")
        )
    print(f"\n═══ {ok}/{ok + ko} correctos · {ko} fallidos")
    return 0 if ko == 0 else 1


# ── CLI ───────────────────────────────────────────────────────────────────────────────────────────
def _imprime(r: dict) -> None:
    marca = {CUMPLE: "✓", NO_APLICA: "·", NO_CUMPLE: "✗", NO_MEDIBLE: "?"}[r["estado"]]
    print(f"{marca} Gate F · {r['estado']}: {r['por_que']}")
    for c in r.get("candidatos", [])[:8]:
        donde = f"{c.get('fichero') or ''}:{c['linea']}"
        print(f"    {donde:<14} {c['tipo']:<20} «{c['palabra']}»  {c['texto']}")
    for e in (r.get("modelo") or r).get("errores", [])[1:8]:
        print(f"    · {e}")
    for a in (r.get("modelo") or r).get("avisos", [])[:8]:
        print(f"    ⚠ {a}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ruta", nargs="?", help="carpeta del plan o plan.md")
    ap.add_argument("--modelo", help="valida solo un modelo-amenazas.md")
    ap.add_argument("--asvs", choices=["L1", "L2", "L3"], help="subconjunto ASVS de ese nivel")
    ap.add_argument("--tipo", choices=sorted(TIPOS), help="nivel y extras del tipo de proyecto")
    ap.add_argument("--con", default="", help=f"capítulos condicionales: {','.join(CAPITULOS_SI)}")
    ap.add_argument("--extra", default="", help="ids de nivel superior que se suman (v5.0.0-x.y.z)")
    ap.add_argument("--resumen", action="store_true", help="solo los recuentos por capítulo")
    ap.add_argument("--autoprueba", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.autoprueba:
        return _autoprueba()
    if a.asvs or a.tipo:
        con = [c for c in a.con.split(",") if c]
        malos = [c for c in con if c not in CAPITULOS_SI]
        if malos:
            print(
                f"--con desconocido: {', '.join(malos)} (válidos: {', '.join(CAPITULOS_SI)})",
                file=sys.stderr,
            )
            return 2
        nivel, extra = TIPOS[a.tipo] if a.tipo else (a.asvs, [])
        nivel = a.asvs or nivel
        extra = list(extra) + [
            e[len("v5.0.0-") :] if e.startswith("v5.0.0-") else e for e in a.extra.split(",") if e
        ]
        try:
            s = subconjunto(nivel, con, extra)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 1
        if a.json:
            print(json.dumps(s, ensure_ascii=False, indent=1))
        else:
            print(
                f"ASVS 5.0.0 · {nivel}{' · tipo ' + a.tipo if a.tipo else ''} · capítulos "
                f"{', '.join('V' + str(c) for c in s['capitulos'])} · {s['total']} requisitos"
            )
            print("  " + " · ".join(f"{k} {v}" for k, v in s["por_capitulo"].items()))
            if s["extra"]:
                print(
                    f"  + extra de nivel superior: {', '.join('v5.0.0-' + e for e in s['extra'])}"
                )
            if a.tipo == "salud":
                print(
                    "  ⚠ salud: es la vara de SEGURIDAD; no sustituye a `sara-salud-datos` (sus 7 "
                    "preguntas bloqueantes) ni, si hay IA, a `nora-ai-act-auditor`. Con historia "
                    "clínica, 14.2.7 clasifica: el plazo lo fija la ley sanitaria (Ley 41/2002 "
                    "art. 17.1, mínimo cinco años)"
                )
            if not a.resumen:
                d = asvs()
                for i in s["ids"]:
                    rid = i[len("v5.0.0-") :]
                    nivel_req = d["requisitos"][rid]["L"]
                    seccion = d["secciones"][rid.rsplit(".", 1)[0]]
                    print(f"  {i:<16} L{nivel_req}  {seccion}")
        return 0
    if a.modelo:
        r = revisa_modelo(pathlib.Path(a.modelo))
    elif a.ruta:
        r = revisa_plan(pathlib.Path(a.ruta))
    else:
        ap.print_help()
        return 2
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        _imprime(r)
    return 0 if r["estado"] in (CUMPLE, NO_APLICA) else 2 if r["estado"] == NO_MEDIBLE else 1


if __name__ == "__main__":
    sys.exit(main())
