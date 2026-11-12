---
name: "modelado-amenazas"
description: >-
  Usar cuando un plan o una feature cruza una frontera de confianza (Gate F de rules/plan-gates.md,
  tanda 4b.3 de /arrancar): 'modela las amenazas', 'threat model', 'STRIDE', 'qué nivel ASVS le
  toca'. NO usar para: atacar lo construido (sofia-pentester), la privacidad (priya-privacy-auditor,
  sara-salud-datos), revisar un diff (code-review-gate, /security-review) ni un bugfix de 1-3
  ficheros.
user-invocable: true
effort: high
metadata:
  version: 1.0.0
  author: tech-lead-template
  category: workflow
  updated: 2026-10-21
  source: "sub-ola 2.25 (SE-19, SE-D14) · research r3-ciberseguridad-harness.md §2.2"
---

# modelado-amenazas — qué puede ir mal en cada frontera, decidido antes de construir

## Principio

El template no tenía modelado de amenazas: `/arrancar` 4b pregunta por el login y los puertos, y
`gate_arranque.py` solo comprueba que `07-superficie.md` exista y diga «defensas». Lo que nadie miraba
es **cada sitio por donde algo de fuera entra o algo nuestro sale**. Esta skill lo mira con las cuatro
preguntas del *OWASP Threat Modeling Cheat Sheet* —qué construimos, qué puede ir mal, qué hacemos, ¿lo
hicimos bien?— y deja **una página**: una fila por amenaza, con la defensa **decidida**, el requisito de
ASVS que la pide y cómo se prueba. Una defensa sin prueba es una declaración; un requisito citado de
memoria, a menudo, un requisito que no existe.

**Lo que la hace barata:** solo se modelan las fronteras que **este** trabajo crea o cambia, no el
sistema entero. Es el mismo acotamiento que salva al Gate E de convertirse en un trámite.

## Cuándo activar

- **Gate F** (`rules/plan-gates.md`): plan grande que crea o cambia una frontera. El detector
  `python3 .claude/scripts/gate_amenazas.py <carpeta-del-plan>` dice si cruza y por qué línea.
- **`/arrancar` tanda 4b.3**, al cerrar la superficie de ataque de un proyecto nuevo.
- A petición: «modela las amenazas de esto», «¿qué nivel ASVS le toca?».
- **No:** bugfix de causa clara, copy o estilo, un refactor que no mueve fronteras (`plan-gates.md` §1).

Disparadores: 'modela las amenazas', 'modelo de amenazas', 'threat model', 'STRIDE', 'LINDDUN',
'Rule of Two', 'qué puede ir mal en esto', 'qué nivel ASVS le toca', '/modelado-amenazas'; Gate F
cuando hay endpoint público nuevo, subida de ficheros, webhook, tool de agente con efecto, tenant
nuevo, integración externa o datos personales nuevos. Produce UNA página
(templates/modelo-amenazas.md): fronteras → STRIDE → defensa decidida con su requisito ASVS 5.0.0 y
su prueba; cartas de LINDDUN GO si hay datos personales; Rule of Two por agente. La valida
scripts/gate_amenazas.py, que rechaza ids de ASVS y cartas inventadas. · NO usar para: atacar lo ya
construido (sofia-pentester), auditar la privacidad o la base legal de lo que existe
(priya-privacy-auditor; con datos de salud, sara-salud-datos), revisar un diff antes del merge
(code-review-gate, /security-review), el mínimo de login, 2FA y puertos de un proyecto nuevo (ya lo
preguntan las tandas 4b.1-4b.2 de /arrancar) ni un bugfix de 1-3 ficheros: ahí el Gate F calla.

## Contrato de entrada

| Necesito | De dónde | Si falta |
|---|---|---|
| Qué se construye | `plan.md` / `spec.md`, o la descripción de la tarea | Lo pregunto; sin esto no hay modelo |
| El código, si ya existe | Rutas que da el plan; lo leo, no lo ejecuto | Se modela el diseño, y el modelo lo dice en §6 |
| El tipo de proyecto | `07-superficie.md`, un modelo anterior o el Usuario | Pregunto: `web-marketing` · `app` · `bot` · `salud` · `pentest` (`references/asvs-por-tipo.md`) |

Si el plan no deja claro qué entra de fuera, **pregunto como mucho tres cosas, y solo esas**: qué entra
y quién lo manda · qué datos personales se tocan · qué agentes hay y qué pueden hacer. Nunca relleno una
frontera con algo plausible: el gate rechaza los huecos, y una suposición sin marcar es indistinguible
de un acuerdo.

## Procedimiento

**Paso 0 — ¿Aplica?** `gate_amenazas.py <carpeta-del-plan>` lista los candidatos (`webhook l.12`,
`datos_personales l.30`…). Si dice que no aplica y estoy de acuerdo, no escribo nada. Si cruza y el
detector se equivoca, el plan lo dice por escrito: `Gate F: no aplica — <razón de 20 caracteres o más>`.

**Paso 1 — Qué construimos: las fronteras.** `cp .claude/templates/modelo-amenazas.md` al sitio de la
tabla de abajo. Una fila por frontera, `F1`, `F2`…: de dónde a dónde, qué cruza y quién está al otro
lado. Frontera = donde cambia la confianza: navegador → API, tercero → webhook, modelo → tool, tool →
base de datos, servidor → log.

**Paso 2 — Qué puede ir mal: STRIDE por frontera.** Recorro las seis letras en cada frontera
(S suplantación · T manipulación · R repudio · I divulgación · D denegación de servicio · E elevación de
privilegios) y **escribo solo las que aplican**, en concreto: «un paciente ve las citas de otro por id»,
no «riesgo de acceso no autorizado». Toda frontera declarada tiene al menos una fila.

**Paso 3 — Qué hacemos.** Por fila, una de las cuatro respuestas de OWASP —mitigar · eliminar ·
transferir · aceptar— y:

| Respuesta | Qué escribo |
|---|---|
| mitigar / eliminar | La defensa decidida, el requisito y **cómo se prueba** (test, sabotaje, caso de Sofía) |
| transferir | A quién (el proxy, el proveedor) y por qué; el requisito si lo hay |
| aceptar | La razón y hasta cuándo, y la repito en §5 |

> ⚠️ **Recordatorio, repetido a propósito aquí, que es donde se deriva:** no cito un requisito de
> memoria. Lo saco de `gate_amenazas.py --tipo <tipo>` (o `--asvs L2 --con jwt,…`), leo su texto en el
> estándar (`https://github.com/OWASP/ASVS/tree/v5.0.0_release/5.0/en`) y solo entonces lo escribo,
> como `v5.0.0-8.2.2`. Si la amenaza es del propio modelo —inyección de prompt, agencia excesiva—, ASVS
> no la cubre: va el riesgo `LLM01`-`LLM10` (OWASP Top 10 for LLM 2025) o `ASI01`-`ASI10`.

**Paso 3b — Privacidad, solo si hay datos personales.** Recorro las 33 cartas de
`references/linddun-go.md` contra las fronteras: el *hotspot* de cada carta (entrada, salida,
almacenamiento, proceso) dice en cuál mirarla. Escribo las que **sí** aplican, con la amenaza concreta y
la defensa. D4 (registros detectables), DD4 (retención) y U5 (rectificar o borrar) aparecen casi siempre.

**Paso 3c — Agentes, solo si hay un LLM con tools.** Por agente y sesión, la Rule of Two de Meta
(31-10-2025): [A] procesa entrada no confiable · [B] accede a datos privados o sistemas sensibles ·
[C] cambia estado o comunica fuera. **Con las tres a la vez no opera en autónomo**: necesita
`interrupt()` o confirmación humana antes de lo irreversible, o partir el trabajo en una sesión nueva.
La confirmación es de una **persona**: o es el sujeto del verbo («el supervisor aprueba», «la enfermera
confirma»), o va detrás del nombre («confirmación del paciente», «revisión humana»). «El bot valida la
petición del usuario», «el agente se confirma», una «aprobación automática» o un control «por
implementar» no cuentan, y el gate los rechaza. La regla complementa al mínimo privilegio; no lo
sustituye.

**Paso 4 — ¿Lo hicimos bien?** §5 (lo aceptado, por escrito) y §6 (quién lo revisa y cuándo se vuelve
a mirar). Después:

```bash
python3 .claude/scripts/gate_amenazas.py <carpeta-del-plan>        # el Gate F completo
python3 .claude/scripts/gate_amenazas.py --modelo <modelo.md>      # solo el modelo
```

Exit 0 = cumple o no aplica · 1 = falta algo (dice qué y en qué fila) · 2 = no se pudo medir.

## Dónde va el fichero

| Trabajo | Fichero |
|---|---|
| Plan en `.docs/plans/<plan>/` | `.docs/plans/<plan>/modelo-amenazas.md` |
| Sesión SpecKit | `.specify/sessions/<ID>/modelo-amenazas.md` |
| `/arrancar` (tanda 4b.3) | `<plan>/arranque/modelo-amenazas.md`, enlazado desde `07-superficie.md` |
| En otro sitio de la carpeta del plan o de `.docs/` | El plan lo dice: `Gate F: modelo en <ruta>` (fuera de ahí, el gate lo rechaza: el ejemplo de la skill no vale de comodín) |

## Salida

Una página con este frontmatter y las seis secciones de `templates/modelo-amenazas.md`:

```yaml
reviewed: 2026-10-20          # y reviewed_by: la PERSONA que lo revisó, no el agente que lo escribió
asvs_nivel: L2                # del tipo de proyecto
asvs_extra: v5.0.0-8.3.3      # requisitos de nivel superior que se suman, o «ninguno»
datos_personales: sí          # sí → exige la tabla de LINDDUN GO
agentes_llm: sí               # sí → exige la tabla Rule of Two
```

Lo consumen: **Sofía** ataca la columna «Cómo se prueba» y cita el id en su hallazgo (campo `asvs`);
**Priya** revisa las cartas de §3; la spec de SpecKit copia nivel e ids en `Constraints`.

## Anti-patterns

- ❌ Modelar el sistema entero en cada plan → trámite; solo las fronteras que este trabajo toca.
- ❌ Las seis letras de STRIDE en cada frontera «por cumplir» → se escriben las que aplican.
- ❌ Un id de ASVS de memoria → los inventa cualquiera; el gate los rechaza.
- ❌ «Mitigar» sin cómo se prueba → una defensa que nadie prueba es una declaración.
- ❌ Un agente con [A], [B] y [C] y un «lo vigilamos en el log» como control → no es control.
- ❌ Disparar el Gate F en un bugfix → calla; y si el detector se equivoca, `Gate F: no aplica — razón`.
- ❌ Dar el verde del gate por un dictamen → comprueba forma e ids, no que la defensa sea buena.

## Ejemplos

### Usuario: «añade el webhook de Stripe para los avisos de pago»
TL: plan grande con frontera nueva → Gate F. Paso 0 lo confirma (`webhook`, `integracion_externa`).
Modelo con F1 Stripe → `/pagos/aviso/`: T aviso falsificado → mitigar, firma `Stripe-Signature`,
`v5.0.0-4.1.5`, `test_firma_mala`; T un reintento de Stripe crea dos pedidos → idempotencia por id de
evento (`rules/api-http-contract.md` §5). Sin datos personales ni agentes: `no` en los dos y sin sus
tablas. Gate en verde y el plan sigue.

### Usuario: «arregla el redondeo del total del carrito»
TL: bugfix de un fichero → sin plan formal y sin Gate F. Si hubiera plan, `gate_amenazas.py` diría «no
aplica». No escribe modelo.

### Usuario: «el asistente tiene que poder cancelar pedidos»
TL: tool con efecto → Gate F con Rule of Two: [A] texto del cliente, [B] pedidos, [C] cancela → las
tres. Control decidido: `interrupt()` con el pedido y el importe antes de cancelar, y el cliente sale del
contexto, no del modelo (`v5.0.0-8.3.3`, `patterns/stack/agente-hitl.md`).

Caso real completo, sobre una pieza del template: `references/ejemplo-mcp-comercio.md` (el servidor MCP
de comercio de la 3.42: 5 fronteras, 14 filas STRIDE, 7 cartas y 3 agentes, y siete hallazgos, H1-H7).
El gate le da todo por bueno menos la firma: lo escribió un agente, y firma quien lo revisa. Se queda en
rojo por eso hasta que lo lea el dueño del kit.

## Límites honestos

- El detector del Paso 0 es **léxico**: en un plan basta la mención de una frontera, y salta lo que no
  se construye (fuera de alcance, estado actual, negaciones, preguntas, arreglos). Da candidatos con su
  línea, no veredictos; por eso existe la salida escrita `Gate F: no aplica — razón`. Y no ve lo que el
  plan no escribe: una ficha que solo dice de qué ficheros es dueña no tiene fronteras que leer.
- El gate valida la **forma** y que ids y cartas **existan** (en cualquier parte del fichero). Que la
  defensa sea buena lo dicen la prueba y el auditor, no el verde. Tampoco distingue una defensa decidida
  de una ya hecha: por eso la que está decidida y sin hacer se escribe
  `**pendiente (H1):** <la defensa>`, con el hallazgo que la sigue. «Pendiente» a secas, «por definir»
  o «sin test» no son una defensa ni una prueba: el gate los rechaza.
- La firma de un agente se reconoce por el **nombre** (agente, Claude, GPT, Codex, un `id-en-kebab`), no
  por quién es: un agente con nombre de persona («Otto») pasa. La firma la pone la persona que lo revisó.
- Un requisito de un nivel superior al del proyecto que no esté en `asvs_extra` sale como **aviso**, no
  como error: o se suma a propósito y se declara, o el nivel se queda corto.
- Un payload en una celda (`<script>`) va entre comillas de código; suelto, cuenta como hueco.
- ASVS 5.0.0 y LINDDUN GO v241203 son las versiones de hoy: el día que cambien, se regenera
  `asvs-5.0.0.json` (su script está en `_archive/2026-10-20/medicion-2.25/`) y la tabla de cartas.

## Related

- `rules/plan-gates.md` §Gate F — cuándo se dispara · `scripts/gate_amenazas.py` — el gate y su `--autoprueba`
- `templates/modelo-amenazas.md` — la plantilla · `references/asvs-por-tipo.md` — nivel y subconjunto
- `references/linddun-go.md` — las 33 cartas · `references/ejemplo-mcp-comercio.md` — el caso real
- `skills/arrancar` §Fase 4b — la llama en la tanda 4b.3 · `sofia-pentester`, `priya-privacy-auditor`,
  `sara-salud-datos` — atacan y auditan contra este documento
- `rules/agent-security.md` (ASI01-ASI10) · `patterns/stack/agente-tools.md` · `agente-hitl.md` ·
  skill `multi-tenant-context` — las defensas de agentes que la Rule of Two pide
