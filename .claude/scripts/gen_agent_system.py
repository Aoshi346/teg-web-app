#!/usr/bin/env python3
"""Genera .claude/AGENT-SYSTEM.md — el mapa de posibilidades del harness.

Uso:  python3 .claude/scripts/gen_agent_system.py [--check]
      python3 .claude/scripts/gen_agent_system.py --scenario frontend
      python3 .claude/scripts/gen_agent_system.py --detect "añade la pantalla de pedidos"

  --check     no escribe; sale 1 si el mapa está desfasado (gate de verificación).
  --scenario  imprime SOLO la ficha de ese escenario (lo usa la skill /otto, modo catálogo;
              antes la skill /sistema, fusionada en otto el 2026-10-19).
  --detect    detecta el escenario de un prompt e imprime su ficha (lo usa el hook
              dispatch-hint.sh). Silencio + exit 1 si no reconoce el dominio.

POR QUÉ EXISTE: el template tenía las piezas y no tenía despachador. INDEX.md dice qué
LEER; esto dice qué USAR, con las cuatro capas juntas (agentes · skills · plugins · workflows).
Se REGENERA, no se edita a mano: un mapa escrito a mano se desincroniza en tres semanas,
que es exactamente el fallo que vino a arreglar.

La detección de dominio vive AQUÍ y no en el hook, a propósito: un solo sitio que mantener.
"""
import re, sys, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # .claude/
REPO = ROOT.parent
OUT  = ROOT / "AGENT-SYSTEM.md"

# ─────────────────────────────────────────────────────────────────────────────
# 1. La matriz de capas — el criterio, no el inventario. Fuente: rules/layer-decision.md
# ─────────────────────────────────────────────────────────────────────────────
LAYERS = [
    ("Que el modelo **sepa** un dato del proyecto", "`CLAUDE.md`",
     "Es contexto, no procedimiento. Y es *advisory*: se puede ignorar."),
    ("Un **procedimiento** que repetiré ≥3 veces", "**Skill**",
     "Su cuerpo carga solo cuando se usa; la `description` es lo que dispara."),
    ("Que algo ocurra **siempre**, pase lo que pase", "**Hook**",
     "Es la única capa que no se puede ignorar. Si duele que se salte, va aquí."),
    ("Un **juicio independiente** con contexto limpio", "**Subagente**",
     "El que hizo el trabajo no es escéptico honesto de sí mismo."),
    ("**Varios** juicios en paralelo, orquestación repetible", "**Workflow**",
     "Determinista, resumible, con presupuesto. Un loop es un nodo de un grafo."),
    ("Que los agentes **se hablen** entre sí", "**agent-teams**",
     "Solo si necesitan REBATIR. Si basta con enterarse → pizarra (`parallelization.md` §Pizarra)."),
    ("Capacidad **empaquetada y versionada** de terceros", "**Plugin**",
     "Doc oficial: standalone en `.claude/` para iterar; plugin para compartir/versionar."),
    ("Acceso **gobernado** a un sistema externo", "**MCP**",
     "Scope y permisos explícitos. Nunca un `bash` suelto (`security.md`)."),
]


# ─────────────────────────────────────────────────────────────────────────────
# 1b. Las ETAPAS — el otro eje. El dominio dice QUÉ piezas; la etapa dice QUÉ TOCA AHORA.
#     Sin este eje, nada avisa de "esto es definición: ¿SpecKit?" ni de "esto pide varios
#     juicios: ¿workflow?". Se detectan juntas y se inyectan juntas.
# ─────────────────────────────────────────────────────────────────────────────
ETAPAS = {
 "arranque": dict(
   nombre="Arranque — un proyecto que todavía no existe",
   triggers=["arranca","arrancar","arrancamos","empieza","empecemos","empezamos",
             "proyecto nuevo","nuevo proyecto","quiero arrancar","quiero construir",
             "quiero hacer una app","quiero hacer una web","vamos a hacer","de cero",
             "desde cero","idea nueva","no sé por dónde","no se por donde",
             "empezar el proyecto","monta el proyecto","start the project","new project"],
   toca="**skill `arrancar`** (pregunta por tandas) · `templates/prd-template.md` · "
        "`/schema lean-canvas` · `pol-product-advisor` · `/producto` si hay pantallas",
   gate="**No se escribe código hasta cerrar las 6 fases** (producto · requisitos · datos · stack · "
        "ética · superficie de ataque). Se comprueba: `python3 .claude/scripts/gate_arranque.py . --explica`, y el estado del flujo entero con `flow_state.py`. "
        "`/speckit.specify` NO vale aquí: trae orden de *no preguntar* (\"make informed "
        "guesses\"). SpecKit entra DESPUÉS, solo para ejecutar."),
 "definicion": dict(
   nombre="Definición — qué construimos y por qué",
   triggers=["qué construimos","que construimos","requisitos","alcance",
             "qué hace falta","no sé qué necesito","qué necesito","qué entra y qué no"],
   toca="`/producto` (las 12 capas) · `/schema lean-canvas` · `pol-product-advisor`",
   gate="**¿SpecKit?** Feature multi-módulo o refactor grande → sí (`governance.md` §1). "
        "Y **Gate 0b**: enumera lo que te falta saber y pregúntalo ANTES de comprometer nada."),
 "diseno": dict(
   nombre="Diseño — cómo va a ser",
   triggers=["cómo debería","como deberia","diseña","disena","arquitectura","maqueta",
             "wireframe","boceto","estructura del","cómo lo planteo"],
   toca="`disenar-pantalla` · `disenar-conversacion` · `/visual-map` · `/schema` · "
        "`modelado-amenazas` si cruza una frontera",
   gate="**ADR si toca arquitectura, schema o un contrato de API** (`rules/adr.md`, Gate D): "
        "el plan no cierra sin él, y se escribe con la decisión fresca. **Modelo de amenazas si "
        "crea una frontera** —endpoint público, ficheros, webhook, tool con efecto, tenant, "
        "integración o datos personales— (Gate F): `python3 .claude/scripts/gate_amenazas.py "
        "<carpeta-del-plan>`."),
 "construccion": dict(
   nombre="Construcción — escribirlo",
   triggers=["implementa","implementar","añade","anade","monta","crea el","escribe el",
             "programa","codifica","haz el endpoint","haz la pantalla"],
   toca="lo que diga el DOMINIO (abajo) · `prompt-contracts` si toca >3 ficheros",
   gate="Commit por paso. Con **baja confianza** en el enfoque, elicita antes de andamiar "
        "(`plan-gates.md` §1b)."),
 "verificacion": dict(
   nombre="Verificación — ¿está bien?",
   triggers=["revisa","revisar","verifica","comprueba","está bien","esta bien","prueba",
             "testea","antes del merge","pre-merge","qa"],
   toca="`code-review-gate` · `/review-branch` · `/qa-loop` si hay UI · `verdict-contract.md`",
   gate="**Doble evidencia**: 🔎 código (`file:line`) + 👁 en vivo. Con una sola es `partial`. "
        "Y el verificador va con **contexto limpio**: quien escribió el código no es su juez."),
 "entrega": dict(
   nombre="Entrega — sacarlo",
   triggers=["deploy","desplegar","a producción","a produccion","release","publicar",
             "subir a","lanzar la versión"],
   toca="`/deploy` · `verification.md` (§Ciclo de producción · §Smoke testing)",
   gate="**Deploy a producción y merge a main SIEMPRE requieren aprobación** "
        "(`governance.md` §2). No se relaja porque corra prisa."),
 # Sub-ola 2.25 (SE-19): la etapa que OFRECE el Gate F. No compite con las demás: `ofrece_frontera`
 # la añade como aviso a la etapa ganadora cuando el prompt nombra una frontera concreta.
 "frontera": dict(
   nombre="Frontera de confianza — algo de fuera entra o algo nuestro sale",
   triggers=["webhook","endpoint público","endpoint publico","api pública","api publica",
             "sin login","formulario público","formulario publico","formulario de contacto",
             "subida de ficheros","subir ficheros","subida de archivos","upload","adjuntos",
             "servidor mcp","tool con efecto","herramienta del agente","integración con",
             "integracion con","su api","por su api","sincroniza","sincronizar","stripe",
             "redsys","paypal","oauth","whatsapp","tenant nuevo","nuevo tenant",
             "datos personales","datos de salud","pacientes","dni","teléfono de los",
             "email de los clientes"],
   toca="skill **`modelado-amenazas`** (una página: STRIDE por frontera, LINDDUN GO si hay datos "
        "personales, Rule of Two si hay agente) · `sofia-pentester` y `priya-privacy-auditor` atacan "
        "y auditan contra ese modelo",
   gate="**Gate F** (`rules/plan-gates.md`), si la tarea es grande: modelo de amenazas antes de "
        "comprometer el plan, y `python3 .claude/scripts/gate_amenazas.py <carpeta-del-plan>` en "
        "verde. En un bugfix de 1-3 ficheros no aplica."),
 "operacion": dict(
   nombre="Operación — ya está fuera y algo pasa",
   triggers=["falla en producción","no sé qué pasó","no se que paso","se colgó","se colgo",
             "va lento","error en producción","el bot hizo","por qué respondió",
             "por que respondio","incidente","no se registra"],
   toca="`instrumentar-agente` · `langgraph-debug` · `patterns/stack/agente-observabilidad.md` "
        "· `harness-telemetry` · `backend-observabilidad.md`",
   gate="**Si no puedes reconstruir qué pasó, el problema no es el bug: es que no hay señal.** "
        "Instrumenta antes de seguir adivinando."),
}


def detect_etapa(prompt):
    """La etapa del prompt. Mismo criterio que el dominio: especificidad y palabra completa."""
    p = prompt.lower()
    best, score = None, 0.0
    for k, e in ETAPAS.items():
        if k == "frontera":          # no compite: va como aviso aparte (ofrece_frontera)
            continue
        sc = sum(len(t) for t in e["triggers"] if _casa(t, p))
        if sc > score: best, score = k, sc
    return best if score >= 5 else None


# La frontera NO compite con las demás etapas: compitiendo, «revisa la integración con stripe» o
# «el webhook se colgó» perdían su ficha de verificación u operación (auditor, sub-ola 2.25). Se
# AÑADE a la ganadora cuando la tarea crea algo; no cuando se revisa, se opera, se entrega o se
# arregla lo que ya hay.
NO_OFRECE_FRONTERA = {"verificacion", "operacion", "entrega"}
ARREGLO_PROMPT = re.compile(r"\b(arregla|arreglar|corrige|corregir|fix|bug|hotfix)\b", re.I)
# Un retoque visual o de texto no crea fronteras aunque nombre una («el botón de pagar con stripe»).
RETOQUE_PROMPT = re.compile(r"\b(color(es)?|estilos?|css|tipograf\w*|margen|padding|icono|"
                            r"renombr\w*|typo|errata)\b", re.I)


def ofrece_frontera(prompt, etapa):
    p = prompt.lower()
    if etapa in NO_OFRECE_FRONTERA:
        return False
    # El prompt, POR PARTES («arregla X y crea Y», «…; además, …»): la parte que arregla o retoca
    # no crea fronteras, las demás sí pueden (verificador, 3.ª y 4.ª pasadas: un arreglo callaba el
    # prompt entero, el mismo patrón que se quitó del gate).
    partes = [x for x in re.split(r"\s+(?:y|e)\s+|;|\badem[áa]s\b", p) if x.strip()]
    limpias = [x for x in partes if not (ARREGLO_PROMPT.search(x) or RETOQUE_PROMPT.search(x))]
    if not limpias:
        return False
    # El MISMO detector que el Gate F (verificador, 2.ª pasada: dos vocabularios se separan
    # solos). La lista de disparadores de la etapa queda de respaldo, por si no se puede cargar.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from gate_amenazas import candidatos
        return bool(candidatos("\n".join(limpias)))
    except Exception:  # defensive: el despacho no puede romperse porque falte o falle el detector
        return any(_casa(t, x) for x in limpias for t in ETAPAS["frontera"]["triggers"])


def ficha_etapa(k):
    e = ETAPAS[k]
    return (f"**Etapa: {e['nombre']}**\n"
            f"- **Qué toca:** {e['toca']}\n"
            f"- ⚠️ {e['gate']}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Los escenarios — QUÉ TIENES para cada tipo de trabajo.
#    Curado a mano (es criterio), VERIFICADO contra disco (es inventario).
# ─────────────────────────────────────────────────────────────────────────────
SCENARIOS = {
 "arranque-producto": dict(
  titulo="Arrancar un producto desde cero (definir ANTES de construir)",
  triggers=["arranca","arrancar","empieza","empecemos","proyecto nuevo","nuevo proyecto",
            "quiero arrancar","quiero construir","quiero hacer una app","quiero hacer una web",
            "de cero","desde cero","idea nueva","prd","historias de usuario","user stories",
            "modelo de datos","lean canvas","requisitos del producto","monta el proyecto"],
  agentes=["pol-product-advisor","priya-privacy-auditor","nora-ai-act-auditor"],
  skills=["arrancar","marca","producto","otto","cumplimiento-salud","disenar-conversacion",
          "modelado-amenazas"],
  workflows=[],
  plugins=[],
  # `/arrancar` es la skill de arriba (el comando del mismo nombre se retiró el 2026-10-19, LI-11).
  comandos=["/siguiente","/marca","/schema","/visual-map","/speckit.plan","/speckit.tasks",
            "/speckit.converge"],
  rules=["plan-gates.md","plan-docs-structure.md","adr.md","verdict-contract.md",
         "ai-assistant-risk.md"],
  orden="**Si no sabes qué toca, `/siguiente`** (mide el proceso y dice el comando). "
        "**`arrancar` primero, todo lo demás después.** Las 5 fases en orden: producto (PRD + "
        "requisitos con Gherkin) → datos y flujos (el ERD de DISEÑO, antes de que haya código) → "
        "stack + C4 + ADR + comprar-o-construir → ética y privacidad ANTES de construir → SpecKit "
        "solo para ejecutar. `/speckit.specify` y `/speckit.clarify` quedan fuera: el primero trae "
        "orden de *no preguntar*, el segundo solo corre si lo tecleas."),

 "cumplimiento": dict(
  titulo="Cumplimiento legal: RGPD, datos de salud y Reglamento de IA",
  triggers=["rgpd","gdpr","proteccion de datos","protección de datos","datos personales","aepd",
            "lopdgdd","datos de salud","historia clinica","historia clínica","paciente","clinica",
            "clínica","clinicas","clínicas","consulta médica","consulta medica",
            "ai act","reglamento de ia","ley de ia","ley europea de inteligencia artificial",
            "ley europea de ia","ley de inteligencia artificial","pacientes","datos medicos",
            "datos médicos","sanitario","sanitaria","historiales","secreto profesional",
            "cumplimiento legal","auditoria legal","auditoría legal","dpd","delegado de proteccion",
            "evaluacion de impacto","evaluación de impacto","eipd","deepfake","contenido sintetico"],
  agentes=["priya-privacy-auditor","sara-salud-datos","nora-ai-act-auditor"],
  skills=["feedback-audit"],
  plugins=[],
  workflows=["research-normativo"],
  comandos=["/fairness-audit"],
  rules=["verdict-contract.md","ai-assistant-risk.md","fairness-audit.md","security.md"],
  orden="**Las tres son necesarias y ninguna cubre a las otras**: un chatbot de clinica con IA las "
        "necesita las tres. **Priya** el RGPD general y deriva - **Sara** datos de salud Espana "
        "(art. 9.3, LOPDGDD, Ley 41/2002) - **Nora** el Reglamento de IA. Las tres PREGUNTAN antes "
        "de auditar (la clasificacion depende del USO, no de la arquitectura) y sin respuesta el "
        "veredicto es `blocked`. Las tres tienen error_cost FALSE-POSITIVE: ante la duda, `review`. "
        "La normativa CADUCA: el calendario del Reglamento de IA cambio el 27-07-2026. Relanza "
        "el workflow de research antes de fiarte de la rubrica."),
 "harness-proyecto": dict(
  titulo="Actualizar o auditar el SISTEMA AI (.claude/) de un proyecto",
  # Los triggers se escriben como la gente HABLA, no como se documenta. Medido: "actualízame este
  # proyecto", "pon este proyecto al día" y "qué le falta a este proyecto" NO casaban con la lista
  # anterior, que estaba escrita en infinitivo y con "al" en vez de "a este". Un despachador que
  # solo entiende la forma canónica no despacha.
  triggers=["actualiza el sistema","actualizar el sistema ai","mapea el proyecto","mapear el proyecto",
            "actualiza este proyecto","actualizame","actualízame","actualiza el proyecto",
            "está actualizado","esta actualizado","al día","al dia","ponlo al día","ponlo al dia",
            "qué le falta","que le falta","qué falta","que falta",
            "sincroniza con el template","sincronizar con el template","trae lo nuevo",
            "audita el harness","el .claude","sistema de agentes","harness del proyecto",
            "revisa la configuración","revisa la configuracion"],
  agentes=[],
  skills=["otto","mapear-sistema","update-agent","check-agent","code-graph"],
  plugins=[],
  workflows=["cruzar-codigo-harness"],
  comandos=["/consolidate-agent-learnings"],
  rules=["self-improvement-loop.md","layer-decision.md","governance.md"],
  orden="**mapear ANTES de copiar** → `mapear-sistema` cruza lo que el código ES con lo que el harness "
        "TIENE (motor: `scripts/audit_sistema_ia.py`) · con ≥6 candidatos lanza el workflow "
        "`cruzar-codigo-harness` para verificarlos en paralelo · **aplicar** → `update-agent` (staging: "
        "un solo permiso) · **lo propio del proyecto** vuelve al template por "
        "`/consolidate-agent-learnings`. Gate: `audit_sistema_ia.py <proy> --gate`."),
 "frontend": dict(
  titulo="Tocar UI / frontend (diseñar, montar o cambiar una pantalla)",
  triggers=["frontend","css","tailwind","react","componente","responsive","maqueta",
            "botón","boton","modal","estilos","este componente","la interfaz",
            # marca y estética: sin estos, la skill `marca` nacía invisible y el aviso de
            # "los diseños salen feos" no enrutaba a ninguna parte (medido el 2026-09-12)
            "marca","identidad visual","guía de marca","guia de marca","kit de marca",
            "brand","logo","logotipo","paleta","colores","tipografía","tipografia",
            "salen feos","son feos","genérico","generico","parece una plantilla",
            "moodboard","referencias visuales","diseño visual","design system",
            "wireframe","boceto","low fidelity","alta fidelidad","mockup"],
  # ignacio-roig faltaba en esta fila aunque `rules/qa-loop.md` lo EXIGE en el bucle de cierre
  # (estaba solo en las filas de review y de QA). Medido y corregido el 2026-09-18.
  agentes=["vera-art-director","ignacio-roig","aitor-a11y-auditor","conrado-cro-auditor",
           "lidia-naive-tester","desarrollador-frontend"],
  skills=["producto","marca","direcciones-de-arte","disenar-pantalla",
          "movimiento","nueva-pantalla","design","ux-reviewer","visual-regression",
          "capturas-responsive","naive-user-playthrough","html-suelto"],
  # 2026-09-18: el estado se escribe MEDIDO, no supuesto. `marca` y `fases-diseno` afirmaban que
  # superdesign estaba «instalado y activo» cuando no lo estaba, y frontend-design estaba instalado
  # a nivel de usuario pero sin declarar en el template, así que salía `disabled` en cada proyecto.
  plugins=["frontend-design ✔ activo (oficial, 71 líneas)","superdesign ✔ activo",
           "playwright","chrome-devtools-mcp ⚠ NO instalado",
           "typescript-lsp ⚠ en disco pero DESACTIVADO"],
  workflows=[], comandos=["/qa-loop"],
  rules=["motores-de-diseno.md","qa-loop.md","verification.md",
         "html-output.md"],
  orden="**¿landing o panel? El PERFIL decide el camino entero** (`patterns/diseno/perfiles.yaml`): "
        "una web de cliente pasa por `direcciones-de-arte` —varios mundos con nombre, galería, y el "
        "ranking lo haces TÚ—; un panel va directo a `disenar-pantalla`. · "
        "**antes de nada, `python3 .claude/scripts/check_design_login.py`** — si sale 1, el Usuario tiene que teclear `/design-login` para poder comprobar si ya existe un sistema en la web de Claude Design (cierra el 14-12-2026); si sale 2, NO se pudo medir (o la web ya cerró) y no se le manda a ningún login · **si no hay marca (ni identidad, ni paleta, ni tokens), empieza por `marca`** — si no, el boceto sale en grises por diseño · **si son ≥2 pantallas o hay un embudo, `/producto`** · **decidir la forma** → `disenar-pantalla` (2-3 variantes comparables) · "
        "**escribirla** → `nueva-pantalla` (molde de 10 ficheros) · "
        "**cerrar** → `python3 .claude/scripts/gate_diseno.py <build>` (determinista, va ANTES de gastar "
        "un auditor) + screenshot + `ux-reviewer`, y si es wave → `/qa-loop`. · "
        "**el gusto vive en `patterns/diseno/` y NUNCA bloquea**; quién manda cuando dos "
        "herramientas se contradicen: `rules/motores-de-diseno.md`."),
 "backend": dict(
  titulo="Backend / API / modelos / queries",
  triggers=["backend","django","api","endpoint","modelo","migracion","migración","orm",
            "serializer","viewset","query","celery","drf","postgres"],
  agentes=["desarrollador-backend",
           "nuria-aislamiento-tenant","pilar-impacto-produccion"],
  skills=["django-orm",
          "migration-integrity-checks","multi-tenant-context","escribir-tests"],
  plugins=["pyright-lsp","claude-security"],
  workflows=[], comandos=[],
  rules=["ram-pytest.md","governance.md","verification.md"],
  orden="**RAM antes de tests** (`check-ram.sh`) · el endpoint nuevo **se llama de verdad** "
        "antes de DONE (`verification.md` §Smoke testing) · migración destructiva = aprobación · "
        "**multi-tenant con `tenant_id` → G4**: la suite `templates/seguridad-tenant/` (modelos "
        "descubiertos, dos tenants por modelo) y `gate_tenant.py` (rol sin BYPASSRLS, RLS forzado, "
        "políticas, y las sondas de lectura y de escritura: necesitan el DSN de admin o sale 2) · "
        "con migraciones o un manager/permiso compartido, **Pilar** saca la foto antes de programar "
        "(`clasificar_migraciones.py --diff <base>`)."),
 "revision": dict(
  titulo="Revisar código / pre-merge / auditar un diff",
  triggers=["review","revisa","revisar","pre-merge","merge","pull request","pr ","diff",
            "auditar el código","code review","refactor","clean code","mantenible",
            "ya existía","reutiliza"],
  agentes=["roberto-clean-code","pilar-impacto-produccion","rita-pattern-keeper","ignacio-roig"],
  skills=["code-review-gate","pattern-gate","security-review",
          "practices-manifesto"],
  plugins=["code-review","pr-review-toolkit","claude-security"],  # sin coderabbit: EQ-D19, revisión local
  workflows=["/review-branch","/bug-sweep"],
  comandos=[],
  rules=["verdict-contract.md","audit-team.md","trunk-based-flow.md","refactor-progresivo.md","governance.md"],
  orden="`/review-branch` hace el grafo entero (dimensiones en paralelo + verificación "
        "adversarial). El juicio independiente exige **contexto limpio**: no reutilices "
        "la sesión que escribió el código."),
 "plan": dict(
  titulo="Planificar una tarea grande (>3 ficheros, feature, refactor, módulo nuevo)",
  triggers=["planifica","plan ","planear","diseña el plan","speckit","feature nueva",
            "módulo nuevo","modulo nuevo","arquitectura","cómo lo hacemos","roadmap"],
  agentes=["pol-product-advisor"],
  skills=["otto","prompt-contracts","project-setup","code-graph"],
  plugins=[], workflows=["/plan-research"], comandos=["/visual-map","/schema"],
  rules=["plan-gates.md","speckit-workflow.md","research-driven-planning.md",
         "report-kit.md","adr.md"],
  orden="**Gate 0b** (¿qué me falta saber?) → **Gate 0: corre `/otto`** → "
        "gates A/B (research · mapa visual) → C buy-vs-build si es módulo nuevo → "
        "D ADR si toca arquitectura → E vía de datos si lee de fuera. **Para que el Usuario vea el informe**: `python3 server.py --port <N>` (escucha en 127.0.0.1) y él abre un túnel: `ssh -N -L <N>:127.0.0.1:<N> root@<servidor>`. Nunca `0.0.0.0`."),
 "qa": dict(
  titulo="QA / verificar que algo está hecho / cerrar una wave",
  triggers=["qa","verifica","verificar","está hecho","esta hecho","test","tests","auditor",
            "comprueba","evidencia","screenshot"],
  agentes=["lidia-naive-tester","vera-art-director","ignacio-roig","marco-qa-breaker",
           "sofia-pentester","pilar-impacto-produccion"],
  skills=["verification-loops","feedback-audit","visual-regression","capturas-responsive","escribir-tests",
          "eval-estadistica","code-review-gate"],
  plugins=["playwright","chrome-devtools-mcp"],
  workflows=[], comandos=["/qa-loop"],
  rules=["verification.md","verdict-contract.md","qa-loop.md","audit-team.md"],
  orden="**Doble evidencia obligatoria**: 🔎 código (`file:line`) + 👁 en vivo (DOM/screenshot). "
        "Con una sola es `partial`, nunca `done`."),
 "impacto": dict(
  titulo="Cerrar un issue / ¿afecta a algún cliente? / impacto en producción",
  triggers=["impacto","producción","produccion","clientes","cerrar issue","cerrar el issue",
            "afecta a algún cliente","afecta a algun cliente","qué cambia para los demás","foto antes",
            "nuevo issue","nuevo-issue","cerrar-issue"],
  agentes=["pilar-impacto-produccion","roberto-clean-code"],
  skills=["migration-integrity-checks","verify-ticket","code-review-gate"],
  plugins=[], workflows=[], comandos=["/nuevo-issue","/cerrar-issue"],
  rules=["verdict-contract.md","audit-team.md","governance.md","issue-worktree-flow.md"],
  orden="**Pilar PRE** antes de tocar código → `gate_impacto.py <plan> --fase pre` · al cerrar: "
        "**Roberto** sobre el diff → **Pilar POST** → `render_impacto.py <plan> --inyectar <informe>` → "
        "`gate_impacto.py <plan> --fase post` (en `/cerrar-issue`, `issue_close.py <plan>`, que además exige "
        "el informe del issue en su ruta). Exit ≠ 0 → no se propone commit. Los dos en fase 1: "
        "el gate bloquea por ausencia, frescura o incoherencia, no por su veredicto."),
 "deploy": dict(
  titulo="Deploy / infraestructura / producción",
  triggers=["deploy","desplegar","servidor","nginx","gunicorn","terraform","infra",
            "dns","coolify","docker","systemd","certificado ssl"],
  agentes=["hugo-vigilancia-diaria","bruno-perf-cop"],
  skills=["claude-code-referencia"],
  plugins=["claude-security","aikido"],
  workflows=[], comandos=["/deploy"],
  rules=["governance.md","agent-security.md","verification.md"],
  orden="Deploy a producción **siempre requiere aprobación** (`governance.md` §2). "
        "IaC generada por IA: región y sizing explícitos o no se aplica (`agent-security.md` §7) · "
        "**G2** antes de desplegar: `gate_deps.py` (vulnerabilidades HIGH+ con arreglo, lockfile, Actions por SHA, "
        "scripts de instalación; 2 = no medido, no es verde) y el SBOM como artefacto del release."),
 "multiagente": dict(
  titulo="Esto necesita varios agentes (paralelo, orquestación, grafo de agentes)",
  triggers=["paralelo","varios agentes","multiagente","multi-agente","subagentes","workflow",
            "orquesta","worktree","agent team","fan-out","en paralelo"],
  agentes=[],
  skills=["otto","workflow-creator","claude-code-referencia"],
  plugins=[], workflows=["/plan-research","/review-branch","/bug-sweep","/codebase-map"],
  comandos=[],
  rules=["parallelization.md","goal-vs-loop.md"],
  orden="**Primero el test de independencia** (`parallelization.md` §0): si la respuesta de B "
        "cambia según A, es UNA tarea, no dos. Repartir mal cuesta N contextos para una "
        "respuesta peor. Después: ¿basta con enterarse? → pizarra. ¿Hace falta rebatir? → teams. "
        "¿Orquestación repetible? → workflow."),
 "producto": dict(
  titulo="Crear pantallas nuevas: una, un embudo o una webapp entera",
  triggers=["embudo","funnel","webapp","web app","varias pantallas","pantallas nuevas",
            "pantalla","landing","captar clientes","opt-in","optin","producto nuevo",
            "mapa de p","inventario de pantallas","recorrido del usuario","user flow",
            "nueva página","nueva pagina","diseña la","diseñar la"],
  agentes=["pol-product-advisor","conrado-cro-auditor"],
  skills=["producto","business-manager","disenar-pantalla","nueva-pantalla","disenar-conversacion","design"],
  plugins=["frontend-design","superdesign"],
  workflows=[], comandos=["/schema","/visual-map"],
  rules=["plan-docs-structure.md","html-output.md","verification.md"],
  orden="**Empieza por `/producto`, no por el código: es el paso 11 de 12.** Recorre objetivo → "
        "recorrido con bifurcaciones → mapa de páginas → ficha por pantalla → wireframe. "
        "Y **pregunta por CADA pantalla quién la diseña** (🤖 agente · 🤝 a medias · ✍️ tú en el "
        "canvas `design`). Los documentos viven en `.docs/core/producto/`."),
 "documentacion": dict(
  titulo="Escribir la documentación del proyecto (arquitectura, datos, manual…) y sacarla en PDF",
  triggers=["documentación","documentacion","documenta el proyecto","documentar","manual de usuario",
            "doc de arquitectura","modelo de datos","dafo","customer journey","pdf con la doc",
            "subir a drive","la doc del proyecto"],
  agentes=["pol-product-advisor","priya-privacy-auditor","desarrollador-backend","sofia-pentester"],
  skills=["documentar","pdf-premium","codebase-onboarding"],
  plugins=["playwright"],
  workflows=[], comandos=["/visual-map","/schema"],
  rules=["plan-docs-structure.md","verification.md","html-output.md"],
  orden="**`/documentar`: pregunta primero QUÉ documentos y para QUIÉN** → agentes en paralelo con el "
        "bloque común → capturas de la maqueta → Pol (huecos) + Priya (qué no sale) → "
        "`construir_pdf.py --separados`, que aborta si un diagrama no se lee. A Drive, el PDF; nunca los `.md`."),
 "conversacional": dict(
  titulo="Diseñar o evaluar un agente conversacional / chatbot",
  triggers=["chatbot","chat bot","agente conversacional","asistente virtual","el bot",
            "conversacional","golden set","alucina","system prompt","rag","retrieval",
            "prompt injection","inyección de prompt","jailbreak","red team del bot","owasp llm",
            "upsell","venta cruzada","el bot no vende","cuánto vende el bot"],
  agentes=["nadia-chatbot-evaluator","dario-commerce-guardrails","teo-llm-redteam",
           "rafa-retrieval-engineer","ivan-agent-runtime",
           "conrado-cro-auditor","marta-revenue-attribution"],
  skills=["disenar-conversacion","agent-evals","eval-estadistica","vector-db","langgraph-debug"],
  plugins=[], workflows=["/matrix-eval-harness"], comandos=[],
  # Sin `ai-assistant-risk.md` (sub-ola 2.03, MO-7): trata del riesgo de USAR un asistente de
  # código, no de construir un bot.
  rules=["fairness-audit.md","verdict-contract.md"],
  orden="**Diseñar va antes que medir**: `disenar-conversacion` decide persona, fronteras, "
        "fallback y qué NO puede prometer, y escribe el **golden set ANTES de construir** — si se "
        "fabrica después, el listón se ajusta al resultado. Luego: Darío ataca los guardarraíles, "
        "**Teo** hace el red team OWASP LLM (inyección, tools, fugas, gasto), "
        "`agent-evals` monta el gate, Nadia mide. **Si el bot pierde la memoria, repite el saludo o ignora "
        "una bandera**, no es diseño ni evaluación: es estado y runtime, de **Iván** y de "
        "`langgraph-debug`. **Y todo bot lleva G6**: `gate_doble_obediente.py <proyecto> --correr` "
        "exige la suite «doble obediente» (`templates/seguridad-bot/`) y la corre: aunque el modelo "
        "obedezca la inyección, no puede hacer daño. **Y G5** (`gate_agente_superficie.py`) mira las tools "
        "por AST; la ventana de 24 h, los topes de coste y los enlaces están en `templates/canal-bot/`. "
        "**Al construirlo**, precio, stock, oferta y efectos los pone el código: "
        "`patterns/stack/agente-guardarrailes.md` y `templates/bot-guardrails/`. "
        "**Si el bot vende**, qué ofrece y cuándo, el «sí» y la rúbrica los pone `templates/bot-sales/`: "
        "Nadia mide la venta (modo venta), Conrado el embudo del chat y Marta cuánto vende, con grupo de control."),
 "agente-ia": dict(
  titulo="Construir o depurar un agente IA con tools (LangGraph)",
  triggers=["langgraph","state graph","stategraph","tool call","tools","mi agente","el agente",
            "del agente","el grafo","nodo del grafo","checkpointer","agente con herramientas",
            "no se registra","no sé qué hizo","trazas","observabilidad del agente",
            "reconstruir la conversación","reconstruir la conversacion"],
  # Los SÍNTOMAS, con las palabras del Usuario (T-094: «pierden memoria, usan mal las tools, no
  # dejan rastro») y las de langgraph-debug e Iván. Solo puntúan si el prompt habla de un bot o un
  # agente (CONTEXTO_BOT): «olvida lo que te dije y cambia el botón» o «el paciente no recuerda lo
  # que tomó» no son de LangGraph. Medido en la 2.03: sin esa condición, 10 de 12 prompts que no
  # eran de bots acababan aquí (_archive/2026-10-20/medicion-2.03/).
  sintomas=["pierde memoria","pierde la memoria","pierden memoria","pierden la memoria",
            "no recuerda","olvida","se olvida","olvida el contexto","no se acuerda",
            "pierde el hilo","repite el saludo","saluda otra vez","ignora una bandera",
            "no persiste","thread_id","dice que lo hizo","dice que hizo","dice que hizo algo",
            "perdido la memoria","no se acordaba","no recordaba","ha olvidado",
            "sin memoria","no guarda el contexto","se inventa que ha hecho","dice que ha hecho",
            "usa mal las tools","usan mal las tools","la tool falla","no deja rastro",
            "no dejan rastro","se ha vuelto lento"],
  agentes=["ivan-agent-runtime","rafa-retrieval-engineer",
           "dario-commerce-guardrails","teo-llm-redteam",
           "bruno-perf-cop"],
  skills=["instrumentar-agente","langgraph-debug","disenar-conversacion","agent-evals","eval-estadistica",
          "vector-db"],
  # Sin `logfire` ni `ai-assistant-risk.md` (sub-ola 2.03, MO-7): Logfire es SaaS y la casa traza
  # los bots con Langfuse autoalojado (agente-observabilidad.md §4); la rule trata de USAR un
  # asistente de código, no de construir un bot.
  plugins=["claude-security"],
  workflows=["/matrix-eval-harness"], comandos=[],
  rules=["verdict-contract.md","agent-security.md"],
  orden="**El patrón de casa está en `patterns/stack/agente-observabilidad.md` y `agente-tools.md`** "
        "(gate: `pattern_check_agente.py`, en sombra). Lo primero, siempre: **medir qué está "
        "apagado** — LangGraph ya graba con el checkpointer y casi nadie lee `get_state_history()`. "
        "Las trazas van a **Langfuse autoalojado** (§4 del patrón), no a un SaaS. **Si no recuerda, "
        "repite el saludo o ignora una bandera**, es estado: **Iván** y `langgraph-debug` §1-2. "
        "Si la tool falla, `langgraph-debug` §4: lo que hace `ToolNode` depende de la versión de "
        "`langgraph-prebuilt` (desde la 1.0.2, la excepción tumba el turno). Y una tool es una API "
        "cuyo cliente se equivoca: contrato, validación y error devuelto, nunca lanzado. Que una "
        "inyección no pueda usarla para hacer daño lo prueba G6 (`templates/seguridad-bot/`)."),
 "config": dict(
  titulo="Configurar el harness (agentes, skills, hooks, plugins, settings)",
  triggers=["configura","configurar","settings","hook","crear agente","nueva skill","plugin",
            "mcp","permisos","harness","setup"],
  agentes=[],
  skills=["project-setup","create-agent","update-agent","check-agent","skill-authoring",
          "claude-code-referencia","auto-dream-memory","otto"],
  plugins=["skill-creator","hookify","agent-sdk-dev"],
  workflows=[], comandos=[],
  rules=["layer-decision.md","agent-security.md",
         "agent-autonomy-ladder.md","self-improvement-loop.md"],
  orden="**Elige la capa ANTES de escribir** (`layer-decision.md`): si el incumplimiento "
        "duele, es un hook, no un párrafo. >3 ficheros en `.claude/` → staging (1 permiso)."),
}

# §4: la referencia de Claude Code. Hasta el 2026-10-20 eran las 8 `boris-*`; la sub-ola 2.08 las retiró
# a `_archive/2026-10-20/skills/` y su contenido vive en las secciones de `claude-code-referencia`.
FUNDAMENTOS = {
 "Fundamentos del harness (CLAUDE.md, MCP, hooks, subagentes, diagnóstico, contexto)":
     [("claude-code-referencia", "§1-3 · §5-7")],
 "Ejecución y autonomía (worktrees, permisos y auto mode, sandbox, mods y plugins)":
     [("claude-code-referencia", "§4 · §8-10")],
 "Memoria y calidad":       [("auto-dream-memory", "")],
}

# Las 5 puertas y sus jueces (EQ-20, sub-ola 3.11; política en rules/audit-team.md §2). Un juez que
# aún no existe sale tachado: Roberto y Pilar llegan en la 3.07.
GATES = [
    ("1 · Plan", ["pilar-impacto-produccion", "pol-product-advisor"],
     "`plan-gates.md` (Gate 0b, 0)", "Pilar PRE: la foto de impacto antes de escribir código. Pol, opcional"),
    ("2 · Código", ["roberto-clean-code", "marco-qa-breaker", "nadia-chatbot-evaluator", "dario-commerce-guardrails"],
     "`/code-review` · `gate_auditor.py`", "Hasta Roberto: `code-review-gate` + verificador limpio. Nadia y Darío solo si hay bot"),
    ("3 · UI", ["lidia-naive-tester", "vera-art-director", "ignacio-roig", "aitor-a11y-auditor", "lena-i18n-auditor"],
     "`gate_diseno.py` · `/qa-loop` · `gate_auditor.py`", "Después de que pase la de código. Aitor/Lena si hay a11y o idiomas"),
    ("4 · Cierre", ["sofia-pentester", "priya-privacy-auditor", "pilar-impacto-produccion",
                    "nuria-aislamiento-tenant"],
     "`smoke/seguridad/correr.sh` · `task_progress.py --gate`",
     "Sofía al final y en staging. Pilar POST cierra el gate. Nuria si es multi-tenant"),
    ("5 · Producción", ["bruno-perf-cop", "nadia-chatbot-evaluator"],
     "`/deploy` (con OK)", "Bruno sobre lo desplegado; Nadia sobre trazas reales si hay bot"),
]

SETTINGS_SCOPE = [
 ("Proyecto normal", "`permissions.allow` amplio para editar/tests · hooks base "
  "(RAM, formato, progreso, audit) · `enableAllProjectMcpServers: false`"),
 ("Con PII / pagos / cliente (tier 2)", "Se empieza **denegando**: `deny` de `.env*`, `~/.ssh`, "
  "`~/.aws` · `ask` en push/deploy/migraciones · MCP solo con allowlist explícita · "
  "auditores `priya-privacy-auditor` y `sofia-pentester` en el ciclo"),
 ("Trabajo desatendido / nocturno", "Criterio de parada explícito · **Stop hook** determinista "
  "(ojo: el harness lo anula tras 8 bloqueos) · tope de presupuesto e iteraciones · "
  "commit sí, **push y merge NO** · ver `rules/goal-vs-loop.md` §Modo noche"),
 ("Rol no técnico", "Solo la capa de **slash commands**. No abre settings, no escribe prompts. "
  "`rules/human-role-layers.md`"),
]

NO_SE_USA = [
 ("graphify / grafo del código en ESTE repo",
  "Veredicto 2026-08-05 + piloto medido: es configuración, no un codebase (~120 ficheros de "
  "código). Sí es candidato en los derivados con código real."),
 ("10 de los 13 auditores-persona (escrito el 2026-08-20)",
  "Nunca han corrido. Cuentan como **checklist, no como cobertura** (`qa-loop.md` §2b)."),
 ("Marketplaces de terceros del catálogo de plugins",
  "`claude-code-workflows`, `dev-gom-plugins`, `ui-ux-pro-max-skill` no están añadidos ni "
  "verificados. Antes de instalar: grep anti-inyección de `agent-security.md` §5."),
]

# ─────────────────────────────────────────────────────────────────────────────
BUNDLED = {"security-review", "code-review", "simplify", "run", "init", "design",
           "dataviz", "artifact-design"}  # skills del propio Claude Code

def existe(kind, name):
    """¿La pieza existe de verdad en disco? Los plugins y las bundled se verifican aparte."""
    n = name.split(" ")[0].lstrip("/")
    if n in BUNDLED: return True
    if kind == "agentes":   return (ROOT/"agents"/f"{n}.md").exists()
    if kind == "skills":    return (ROOT/"skills"/n/"SKILL.md").exists()
    if kind == "rules":     return (ROOT/"rules"/n).exists()
    if kind == "workflows": return (ROOT/"workflows"/f"{n}.js").exists()
    if kind == "comandos":  return (ROOT/"commands"/f"{n}.md").exists() or (ROOT/"skills"/n/"SKILL.md").exists()
    return True

def marca(kind, name):
    return name if existe(kind, name) else f"~~{name}~~ ⚠️"

def ficha(key, sc):
    """La ficha de un escenario — lo que ve el usuario y lo que inyecta el hook."""
    L = [f"### {sc['titulo']}", ""]
    def fila(lbl, kind, items):
        if items:
            L.append(f"- **{lbl}:** " + " · ".join(f"`{marca(kind,i)}`" for i in items))
    fila("Agentes",   "agentes",   sc["agentes"])
    fila("Skills",    "skills",    sc["skills"])
    fila("Workflows", "workflows", sc["workflows"])
    fila("Comandos",  "comandos",  sc["comandos"])
    if sc["plugins"]:
        L.append("- **Plugins/MCP:** " + " · ".join(f"`{p}`" for p in sc["plugins"]))
    fila("Rules",     "rules",     sc["rules"])
    L += ["", f"> **Orden recomendado.** {sc['orden']}"]
    return "\n".join(L)

def _casa(trigger, texto):
    """¿El trigger aparece como PALABRA, no como trozo de otra?

    Sin esto, el trigger "el bot" casaba dentro de "cambia el color del boton" y un cambio de
    CSS se enrutaba a diseño conversacional. La subcadena es el fallo silencioso clásico de
    estos detectores: nadie lo ve hasta que enruta mal algo obvio.
    """
    return re.search(r"(?<![a-záéíóúñ])" + re.escape(trigger) + r"(?![a-záéíóúñ])", texto) is not None


# Las palabras que dicen que el prompt va de un bot o de un agente: sin una de ellas, los `sintomas`
# de un escenario no cuentan. Lumi y Xera son los bots de elvion y de musa.
CONTEXTO_BOT = ["bot","bots","chatbot","chatbots","agente","agentes","asistente","asistentes",
                "ia","llm","grafo","langgraph","lumi","xera"]
# …salvo cuando esa palabra NO habla de una IA: una persona («la asistente de dirección»), un
# asistente de instalación o un formulario por pasos, un grafo de dependencias, un bot de alertas
# que no conversa. Medido en la segunda pasada del verificador de la 2.03: sin esto, 9 de 10
# frases así acababan en agente-ia.
NO_ES_BOT = re.compile(
    r"\bla asistente\b|\basistentes? (?:dental|personal|administrativ[oa]s?|de (?:direcci[oó]n|"
    r"configuraci[oó]n|instalaci[oó]n|alta|registro|compra|pago))\b|\bgrafo de dependencias\b|"
    r"\bagentes? (?:inmobiliari[oa]s?|comercial(?:es)?|de (?:seguros|aduanas|viajes|ventas))\b|"
    r"\bbots? de (?:(?:telegram|slack|discord) (?:de )?)?(?:alertas|avisos|notificaciones)\b")


def detect(prompt):
    """Escenario del prompt, o None si no lo reconoce con confianza.

    Puntúa por ESPECIFICIDAD, no por conteo: un trigger largo ("agente conversacional")
    pesa más que uno corto ("ui"), porque acertar con él es menos casualidad. Sin esto,
    "diseña el chatbot" caía en frontend —"diseñ" y "chatbot" empataban a 1— y el desempate
    lo decidía el orden del diccionario, que es una razón pésima.
    """
    p = prompt.lower()
    de_bot = any(_casa(c, NO_ES_BOT.sub(" ", p)) for c in CONTEXTO_BOT)
    best, score = None, 0.0
    for k, sc in SCENARIOS.items():
        s = sum(len(t) for t in sc["triggers"] if _casa(t, p))
        if de_bot:
            # Un síntoma dicho de un bot es la señal más fuerte que hay: +10 para que gane a una
            # palabra de dominio suelta («el bot de la clínica no se acuerda…» es de Iván, no de
            # cumplimiento; «…y empieza de cero» no es un arranque).
            casan = [t for t in sc.get("sintomas", []) if _casa(t, p)]
            s += sum(len(t) for t in casan) + (10 if casan else 0)
        if s > score: best, score = k, s
    return best if score >= 4 else None   # <4 = coincidencia demasiado corta para fiarse

def build():
    hoy = datetime.date.today().isoformat()
    n = {k: len(list((ROOT/d).glob(g))) for k,(d,g) in {
        "agentes":("agents","*.md"), "skills":("skills","*/SKILL.md"),
        "commands":("commands","*.md"), "workflows":("workflows","*.js"),
        "hooks":("hooks","*.sh"), "rules":("rules","*.md")}.items()}
    # Un agente es un `agents/*.md` con `name:` en el frontmatter: `agents/README.md` no lo es, y
    # contarlo daba 30 con 29 (medido el 2026-10-20). Mismo criterio que gen_agent_index.py.
    n["agentes"] = sum(1 for f in (ROOT/"agents").glob("*.md")
                       if f.name != "README.md"
                       and re.search(r"\A---\n(?:.*\n)*?name:", f.read_text(encoding="utf-8", errors="replace")))
    L = [
"# AGENT-SYSTEM.md — qué tienes y qué usar",
"",
"> **GENERADO. No editar a mano** — `python3 .claude/scripts/gen_agent_system.py`.",
"> `--check` sale 1 si está desfasado. Un mapa escrito a mano se desincroniza en tres semanas.",
">",
"> **`INDEX.md` dice qué LEER. Esto dice qué USAR.** Son distintos: el índice rutea documentación,",
"> este mapa reparte capacidades. Si solo vas a mirar uno estando a punto de trabajar, mira este.",
"",
f"_Inventario real a {hoy}: {n['agentes']} agentes · {n['skills']} skills · {n['commands']} commands · "
f"{n['workflows']} workflows · {n['hooks']} hooks · {n['rules']} rules._",
"",
"---",
"",
"## 1. Qué capa uso",
"",
"> Un **loop es un nodo de un grafo**: cada capa de abajo no sustituye a la de arriba, la envuelve.",
"",
"| Necesito… | Capa | Por qué esa y no otra |",
"|---|---|---|",
]
    L += [f"| {a} | {b} | {c} |" for a,b,c in LAYERS]
    L += ["",
"**La pregunta que decide casi todo** (`rules/layer-decision.md`): *¿qué es lo PEOR que pasa si",
"Claude lo ignora?* Si la respuesta es «perdemos unos minutos» → prosa. Si es «se rompe algo caro»",
"→ **hook**. Subir el tono de un párrafo no lo convierte en obligatorio.",
"", "---", "", "## 1b. Puertas: quién juzga, en qué orden y con qué topes", "",
"El TL es **la sesión principal** (orquesta, hace de arquitecto en plan mode e integra); construyen los",
"agentes con Edit, en worktree; **juzgan los que no tienen Edit**, y un hook les impide escribir fuera de su",
"zona. Quien revisa nunca es quien hizo. Orden: plan → código → UI → cierre → producción, sin mezclar",
"puertas en una ronda. Topes por puerta: **≤5 jueces, ≤3 con navegador, ≤3 rondas** (de la 2ª, solo el",
"diff); la batería completa, solo en hito de release. Cada P0/P1 de código y UI lo valida un segundo agente.",
"Detalle: `rules/audit-team.md`.", "",
"| Puerta | Jueces | Gate determinista | Nota |", "|---|---|---|---|",
]
    L += [f"| **{g}** | " + " · ".join(f"`{marca('agentes', a)}`" for a in js) + f" | {gd} | {nota} |"
          for g, js, gd, nota in GATES]
    L += ["",
"No se crean como agentes un arquitecto, un orquestador ni un SRE: el orquestador-agente mete una capa de",
"opinión entre el Usuario y el trabajo. `~~tachado~~ ⚠️` = juez previsto que aún no existe.",
"", "---", "", "## 2. Si vas a… → esto es lo que tienes", "",
"Las cuatro capas juntas, por escenario. `~~tachado~~ ⚠️` = declarado aquí pero **ausente en disco**.",
""]
    for k, sc in SCENARIOS.items():
        L += [ficha(k, sc), ""]
    L += ["---", "", "## 3. Settings según el alcance", "",
          "| Alcance | Qué cambia |", "|---|---|"]
    L += [f"| **{a}** | {b} |" for a,b in SETTINGS_SCOPE]
    L += ["", "---", "", "## 4. Fundamentos de Claude Code (la referencia del harness)", "",
          "Son la referencia de *cómo funciona el harness*, no procedimientos de proyecto. Las 8 "
          "`boris-*` se retiraron el 2026-10-20: su contenido está en `claude-code-referencia`.", ""]
    for g, ss in FUNDAMENTOS.items():
        vivos = [(s, sec) for s, sec in ss if existe("skills", s)]
        L.append(f"- **{g}:** " + " · ".join(f"`{s}`" + (f" {sec}" if sec else "") for s, sec in vivos))
    L += ["", "---", "", "## 5. Lo que NO se usa, y por qué", "",
          "Un mapa que solo lista lo bueno hace perder el tiempo dos veces.", "",
          "| Pieza | Por qué no |", "|---|---|"]
    L += [f"| {a} | {b} |" for a,b in NO_SE_USA]
    L += ["", "---", "",
"## Anti-patterns", "",
"- ❌ Editar este fichero a mano → se regenera y pierdes el cambio. Toca `gen_agent_system.py`.",
"- ❌ Leer el mapa entero antes de cada tarea → usa `/otto <escenario>` o deja que el hook inyecte la fila.",
"- ❌ Tratar una fila como obligatoria: es **lo que tienes**, no lo que debes usar. El criterio sigue siendo tuyo.",
"- ❌ Añadir una pieza al harness y no añadirla aquí → vuelve a ser invisible, que es el fallo que esto arregla.",
""]
    return "\n".join(L) + "\n"

def main():
    a = sys.argv[1:]
    if "--detect" in a:
        prompt = a[a.index("--detect")+1]
        k, et = detect(prompt), detect_etapa(prompt)
        fr = ofrece_frontera(prompt, et)
        if not k and not et and not fr: return 1
        partes = []
        if et: partes.append(ficha_etapa(et))
        if fr: partes.append(ficha_etapa("frontera"))
        if k:  partes.append(ficha(k, SCENARIOS[k]))
        print("\n\n".join(partes)); return 0
    if "--etapa" in a:
        k = a[a.index("--etapa")+1]
        if k not in ETAPAS:
            print(f"Etapas: {', '.join(ETAPAS)}", file=sys.stderr); return 1
        print(ficha_etapa(k)); return 0
    if "--scenario" in a:
        k = a[a.index("--scenario")+1]
        if k not in SCENARIOS:
            print(f"Escenarios: {', '.join(SCENARIOS)}", file=sys.stderr); return 1
        print(ficha(k, SCENARIOS[k])); return 0
    new = build()
    if "--check" in a:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        # la fecha de la línea de inventario cambia cada día sin que cambie nada: no cuenta
        sin_fecha = lambda s: re.sub(r"_Inventario real a \d{4}-\d{2}-\d{2}:", "_Inventario real a —:", s).strip()
        if sin_fecha(cur) != sin_fecha(new):
            print("DESFASADO: AGENT-SYSTEM.md no refleja el disco. Corre gen_agent_system.py", file=sys.stderr)
            return 1
        print("OK: AGENT-SYSTEM.md al día"); return 0
    OUT.write_text(new, encoding="utf-8")
    faltan = [(k,kind,i) for k,sc in SCENARIOS.items() for kind in
              ("agentes","skills","rules","workflows","comandos") for i in sc[kind] if not existe(kind,i)]
    print(f"Escrito {OUT} — {len(SCENARIOS)} escenarios")
    if faltan:
        print(f"⚠️  {len(faltan)} piezas declaradas y AUSENTES en disco:")
        for k,kind,i in faltan: print(f"    · [{k}/{kind}] {i}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
