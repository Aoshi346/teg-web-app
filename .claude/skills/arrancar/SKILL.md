---
name: "arrancar"
description: >-
  Usar cuando hay que EMPEZAR algo sin definir: 'empieza', 'arranca el proyecto', 'proyecto
  nuevo', 'de cero'. Pregunta por tandas y deja PRD, requisitos,
  datos, stack, ética y superficie de ataque antes de construir. NO usar para: el harness
  (project-setup), qué pantallas (/producto), la jugada de una tarea (/otto), la spec de una
  feature (/speckit.specify) ni retomar (auto-dream-memory).
user-invocable: true
metadata:
  version: 1.4.0
  author: tech-lead-template
  category: workflow
  updated: 2026-10-31
---

# arrancar — definir antes de construir, preguntando

## Principio

Un proyecto que empieza sin documentos base no empieza: **se empieza a adivinar**. Esta skill es la
entrevista que convierte una idea en los documentos de los que cuelga todo lo demás, y lo hace
**preguntando en tandas cortas**, no generando de memoria. Existe porque lo que había hacía lo
contrario: `/speckit.specify` trae orden explícita de *"make informed guesses"* y una lista de temas
sobre los que *"don't ask"*, y el único comando que sí pregunta bien (`/speckit.clarify`) nunca se
encadenaba. El resultado medido: proyectos con código escrito y sin un solo requisito acordado.

**La regla que ordena toda la skill:** cada dato que no se pregunta se convierte en una suposición,
y una suposición no marcada como tal es indistinguible de un acuerdo. Aquí se puede suponer — pero
la suposición queda **etiquetada**, y el gate la cuenta.

## Cuándo activar

- El Usuario dice **«empieza»**, «empecemos», «arranca el proyecto», «proyecto nuevo», «quiero hacer
  una app de X», «vamos a construir», «de cero», «no sé por dónde empezar».
- Hay un repo con código pero **sin `.docs/core/`**: el proyecto existe y su documentación base no.
- **Obligatorio antes de** escribir código de producto cuando `TL_ARRANQUE=1` — el hook
  `gate-arranque.sh` bloquea el primer `Write` a un fichero de código y remite aquí.
- Más disparadores: 'arrancamos', 'quiero construir', 'vamos a hacer', 'monta el proyecto',
  '/arrancar'.
- Lo que produce, preguntando por tandas de 3-4: PRD, requisitos con sus 11 apartados y criterios en
  Gherkin, modelo de datos de DISEÑO, flujos, stack con ADR, ética/privacidad y la SUPERFICIE DE
  ATAQUE con sus defensas decididas (2FA, límite de intentos, exposición, logs).
- NO usar para: configurar el harness del proyecto —agentes, permisos, hooks— (eso es
  `project-setup`, que no toca el producto); decidir qué PANTALLAS hacen falta cuando el producto ya
  está definido (`/producto`); elegir maquinaria del harness para UNA tarea concreta (`/otto`);
  escribir la spec de una feature dentro de un proyecto que ya tiene sus documentos base
  (`/speckit.specify`, que además trae orden explícita de no preguntar); ni para retomar un trabajo a
  medias (`auto-dream-memory`).

## Contrato de entrada

| Necesito | Si no lo tengo |
|---|---|
| Una frase de qué es esto | **Es la primera pregunta.** No se infiere del nombre del repo |
| Si hay código ya escrito | Lo miro (`git log`, la estructura). No lo pregunto si lo puedo ver |
| El plan donde escribir | Lo creo: `.docs/plans/<fecha>-<slug>/arranque/` |
| Respuestas a una tanda | **Se marca `desconocido` y se sigue.** Nunca se inventa, y nunca se bloquea la entrevista entera por una pregunta |

**El sobre de evidencia.** Cada dato que se guarda lleva su procedencia, heredada de
`entrevistador-negocio`:

`documentado` (hay un fichero que lo dice) · `recordado` (lo dijo el Usuario de memoria) ·
`supuesto` (lo propuso el agente y el Usuario no lo corrigió) · `desconocido` (nadie lo sabe aún).

Un documento donde más de la mitad de los datos son `supuesto` **no es un acuerdo**: es un borrador,
y así se marca en su cabecera.

## Procedimiento

**Cómo se pregunta, y no es negociable:** `AskUserQuestion`, **3-4 preguntas por tanda**, una tanda
cada vez. Nunca las once de golpe. Entre tanda y tanda se escribe lo acordado, para que una sesión
que se corte no pierda lo anterior. El procedimiento se sigue **entero, fase por fase**.

> ⚠️ **Si te descubres rellenando una plantilla sin haber hecho su tanda, para:** eso es justo lo que
> hace `/speckit.specify` y la razón por la que esta skill existe. (Era la única instrucción del
> comando `/arrancar`, retirado el 2026-10-19 porque tenía el mismo nombre que esta skill y solo
> decía «invócala»: `/arrancar` lleva ahora aquí, sin depender de qué gana por precedencia.)

---

### Fase 0 — Encuadre

> ⚠️ **No escribas nada todavía.** Esta fase existe para saber qué NO hay que preguntar después.

**Tanda 0.1** — ¿Qué es esto, en una frase, como se lo contarías a alguien que paga? · ¿Es producto
nuevo, un módulo dentro de algo que ya existe, o rehacer algo? · ¿Hay código ya escrito?

**Tanda 0.2** — ¿Quién lo va a usar a diario y en qué momento de su día? · ¿Hay fecha o compromiso
con alguien? · ¿Qué NO entra, aunque alguien lo vaya a suponer?

**Tanda 0.3 · el sector** — ¿De qué sector es el negocio? (las opciones de `vertical` en
`templates/configuracion-de-proyecto.yaml`, o «ninguno»). Se guarda en `respuestas.vertical` del
`.claude/CONFIGURACION.yaml` y `propagar.py` instala su paquete, si está medido. Si ya está instalado
(`.claude/skills/domain-<sector>/`), sus `questions.yaml` entran en las tandas 1.3 y 2.1 (1-2
preguntas cada una, sin pasar de 4) y su `seed.yaml` se siembra en la 2.1. Sin paquete, se sigue igual.

**Produce:** `<plan>/arranque/00-encuadre.md` + el plan creado con `apuntar.py`.
**Reutiliza:** si hay código, `gen_inventario_stack.py` propone el stack **medido** en vez de
preguntarlo a ciegas. Al cerrar la fase, corre `/otto` (Gate 0 de `rules/plan-gates.md`).

---

### Fase 1 — El PRD

> ⚠️ **Recordatorio, repetido a propósito:** aquí es donde más se deriva. Tienes `prd-template.md`
> delante y la tentación es rellenarlo entero de una sentada porque "se deduce del encuadre". No se
> deduce: el dolor, quién decide y qué métrica lo mide **solo los sabe el Usuario**.

**Tanda 1.1 · el problema** — ¿Qué duele hoy, a quién y con qué frecuencia? (pide un caso concreto,
no una generalidad) · ¿Cómo se resuelve hoy? · ¿Qué pasa si no hacemos nada? · ¿Cuánto cuesta ese
dolor, en horas, euros o clientes?

**Tanda 1.2 · quién manda** — ¿Quién decide el alcance cuando haya discusión? · ¿Quién lo mantiene
después de lanzarlo? · ¿Quién paga? · ¿Quién tiene veto técnico?

**Tanda 1.3 · éxito y recorte** — ¿Qué será verdad cuando esto exista? (resultado observable, no
tarea) · ¿Qué métrica lo mide, cuánto vale hoy y cuál es el objetivo? · Si hubiera que lanzar solo
un tercio, ¿cuál? · *(con paquete de sector: + sus preguntas `"1.3"`)*

**Produce:** `<plan>/arranque/01-prd.md` desde `.claude/templates/prd-template.md`.
**Gate:** `gate_arranque.py <plan> --fase prd`.

---

### Fase 1b — Los requisitos (el corazón)

> ⚠️ **Recordatorio, repetido a propósito:** de los 11 apartados **se preguntan cinco** (1, 2, 3, 4,
> 5 y un ejemplo del 7). Los otros seis los redactas tú y se confirman de una vez. Preguntar los
> once por requisito son setenta y siete turnos y la sesión se abandona.

Por **cada** requisito, tres tandas:

**Tanda R.1** — ¿Qué le queda al usuario en la mano cuando termina? · ¿Quién lo hace y cada cuánto? ·
¿Qué hace él exactamente, paso a paso? · ¿Esto **DEBE** pasar siempre o es deseable? *(esta última
fuerza el verbo normativo que `spec_lint.py` exige — no la quites)*

**Tanda R.2** — ¿Qué entra? (fichero, formulario, mensaje, nada) · ¿Qué sale y dónde se ve? · Dame
**un caso real con datos reales**.

**Tanda R.3** — ¿En qué situaciones puede quedarse el trabajo? (pide 4-7 nombres: «sin subir»,
«esperando decisión», «cerrado») · ¿En cuál se atasca más veces? · ¿Qué lo saca de ahí: una persona
o el sistema?

**Produce:** `02-requisitos.md` (legible) + `requisitos.json` (datos) + `requisitos.html`.
**Molde:** `.claude/templates/requisito-template.md`.
**Gate:** `gate_arranque.py <plan> --fase requisitos` — falla si falta un apartado, si no hay ningún
verbo normativo, si no hay Gherkin, o si **alguna máquina de estados no tiene estado final**.

---

### Fase 2 — Datos y flujos

**Tanda 2.1 · las cosas** — Nómbrame las 5-8 «cosas» de las que habla el negocio (cliente,
expediente, factura…) · ¿Cuál es la unidad que se cuenta a fin de mes? · ¿Cómo reconoce **una
persona** cada una? (no el id técnico) · ¿Cuáles ya existen en algún sitio y cuáles nacen aquí?
*(con paquete de sector: + sus preguntas `"2.1"`, y su `seed.yaml` se copia a
`.docs/domain/domain.yaml` con todo en `supuesto`: se enseña y el Usuario confirma, corrige o tacha;
lo que confirma pasa a `recordado`. Con eso, `gen_agent_domain.py` da a los auditores su dominio.)*
*(si el negocio **vende** —tienda, venta por chat, catálogo con stock—: + «¿qué cifras querrá ver el
dueño?», y se ofrece el patrón `patterns/stack/analytics-commerce.md` (eventos, ventas por línea, stock
diario) y el pack `negocio` con la skill `metricas-dominio`: lo que no se registra desde el día uno no
se reconstruye.)*

**Tanda 2.1b · de dónde viene cada cosa, y quién manda** *(la tanda que más problemas evita)* —
¿Este dato **nace aquí** o viene de fuera? Si viene de fuera, **de qué sistema exactamente** · ¿El
mismo dato aparece en **más de un sitio**? Nómbralos todos, y dime **cuál manda** · Lo que no manda:
¿se **regenera** desde la fuente, o alguien lo edita a mano?

Y si el producto **responde con información** (un asistente, un buscador, cualquier cosa con
recuperación): el inventario de **fuentes de conocimiento** —catálogo, preguntas frecuentes,
documentos, banco de conocimiento, notas del comercio— con **un dueño cada una** y qué manda sobre
qué cuando dos se contradicen.

> **Por qué esta tanda existe, con el caso medido.** En Elvion el precio vivía en tres sitios y
> nadie había declarado cuál era la fuente: el cociente entre producto padre y variación era una
> constante de **0,7196 repetida en 476 productos** —un valor derivado que alguien calculó una vez y
> que el sistema seguía sirviendo como si fuera real— y de ahí salieron **31 de 50 fallos de
> conversación**. El mismo producto estaba además en la API del comercio, en el índice de vectores,
> en el grafo y en las preguntas frecuentes.
>
> **Un dato sin fuente declarada no es un dato: es una discusión pendiente.** Y el fallo no aparece
> al escribirlo, aparece meses después cuando dos sitios discrepan y arreglar el síntoma lo devuelve
> en la siguiente sincronización.
>
> Las tres reglas que salen de ahí: **un dato, una fuente** · **lo derivado se regenera, no se
> edita** (un valor derivado editado a mano es indistinguible de uno real) · **si no se sabe cuál es
> la fuente, eso es el problema**, no la inconsistencia que se acaba de ver.

**Tanda 2.2 · relaciones** — ¿Qué pertenece a qué? · Si se borra la de arriba, ¿qué pasa con las de
abajo? · ¿Qué hay que conservar aunque se borre todo lo demás? · ¿Puede la misma cosa estar en dos
sitios a la vez?

**Tanda 2.3 · sensibilidad** *(alimenta la fase 4: se pregunta aquí porque es aquí donde se sabe)* —
¿Cuáles de estos campos son de una persona identificable? · ¿Alguno es de **salud**, de menores,
biométrico o de ideología? · ¿Cuánto hay que conservarlos, y lo decidimos nosotros o una ley?

**Tanda 2.4 · flujos** — El recorrido principal de punta a punta · ¿Dónde se sale del camino? · ¿Hay
algo que hace el sistema solo, sin que nadie mire?

**Tanda 2.5 · mensajes por iniciativa propia** *(pregunta fija; una sola, y no se salta)* — ¿El
producto **mandará mensajes a clientes sin que ellos empiecen la conversación**? (campañas, carrito
abandonado, recordatorios de recompra, avisos de oferta; por WhatsApp, email o SMS). Se apunta en
`entidades.json` como `"mensajes_propios": true|false`. **Si es sí**, nacen ya en el modelo de datos,
con `"patron"`, las tablas de `patterns/stack/campaigns.md`: **D-1** consentimiento (libro por canal y
finalidad, no un booleano), **D-2** exclusión (bajas, Robinson, 131049), **D-3** identidad estable y
**D-6** exposición con grupo de control; con ofertas, también **D-7** (margen y coste del descuento).
Y la fase 4 hereda la base legal del comercio (`rules/campanas-salida.md`).

> **Por qué es fija, con el caso medido.** Elvion lo descubrió tarde: campañas sin consentimiento, sin
> bajas y sin identidad de suscriptor, y por eso su envío real sigue en simulación forzada. Preguntarlo
> aquí cuesta un minuto; añadir esas tablas cuando ya hay envíos obliga a tirar el historial (lo que no
> se registró no se reconstruye) y expone al comercio a seguir escribiendo a quien pidió la baja.

**Produce:** `03-modelo-datos.md` + `entidades.json` + `data-model.html` · `04-flujos.md` +
`user-flows.html` · `trazas.json` (el viaje del dato, para la pestaña Recorridos) ·
`.docs/domain/domain.yaml` (desde la semilla del paquete o desde `templates/domain.yaml`: estados,
acciones únicas, límites y sensibilidad salen de estas tandas) y `gen_agent_domain.py` para los auditores.
**Gate:** falla si hay **algún campo sin la clave `personal: true|false`** —ese campo es el que hace
que la fase 4 se derive en vez de volver a preguntarse— **y si alguna entidad no declara `fuente`**
(`propia` · `externa` · `derivada`), con su `fuente_detalle` cuando no nace aquí. Lo mismo para
cualquier campo que declare una fuente distinta de la de su entidad: el precio derivado del padre es
justo el caso que hay que poder escribir. **Y falla si `entidades.json` no dice `mensajes_propios`**
(tanda 2.5), o si dice `true` y le falta alguna entidad con `"patron": "D-1"`, `"D-2"` o `"D-6"`.

```json
{ "nombre": "Producto", "fuente": "externa",
  "fuente_detalle": "WooCommerce del comercio, por sincronización cada N horas",
  "campos": [
    {"nombre": "precio", "personal": false, "fuente": "derivada",
     "fuente_detalle": "de Variacion.precio — NUNCA del producto padre"}
  ]}
```

---

### Fase 3 — Stack, arquitectura y decisiones

**Tanda 3.1 · stack** — Propón el **medido** (`gen_inventario_stack.py`) o el de casa
(`patterns/stack/ARRANQUE.md`) y que el Usuario confirme o corrija · ¿Dónde vive cuando esté vivo? ·
¿Quién lo mantiene dentro de un año?

**Tanda 3.2 · comprar o construir** *(el Gate C de `plan-gates.md`, que hasta hoy era prosa)* — ¿Qué
parte de esto ya la vende alguien hecha? · ¿Cuál es la parte que **solo podemos hacer nosotros**? ·
¿Cuánto al mes es aceptable pagar por lo que no construyamos?
Y por cada pieza de fuera que se elija, su **licencia** (SPDX, leída en el registro) frente al uso:
¿se modifica?, ¿se ofrece a clientes por red?, ¿se entrega o se vende con ella dentro? Va en
`05-stack.md` con el formato del Gate C (MO-29) y el criterio de `rules/licenses.md`.

**Tanda 3.3 · bordes** — ¿Qué sistemas de fuera toca? · ¿Qué pasa si uno cae una mañana entera? ·
¿Qué decisión de estas es **cara de revertir** dentro de seis meses?

**Produce:** `05-stack.md` · `schemas/c4-{context,container}.html` · **un ADR por cada respuesta a la
última pregunta** (`rules/adr.md`) · `constitution.md` rellenada.

---

### Fase 4 — Ética, privacidad y regulación, ANTES de construir

> Aquí está la inversión: `priya-privacy-auditor`, `nora-ai-act-auditor` y `sara-salud-datos`
> auditan a posteriori y en modo sombra. Se les da como entrada **los documentos de diseño**, no el
> código: funcionan igual (los tres ya preguntan antes de auditar) y su veredicto llega cuando aún
> es barato cambiar.

**Tanda 4.1** *(se rellena sola con la tanda 2.3 — aquí solo se confirma)* — ¿Trata datos
personales? · ¿De salud, de menores o biométricos? · ¿El sistema **decide** algo sobre una persona
sin que un humano lo mire? · ¿Habla una IA con alguien de fuera?

**Tanda 4.2** *(solo si algo de 4.1 fue que sí)* — ¿Con qué base legal? · ¿Cuánto se conserva cada
dato y quién lo borra? · ¿Qué proveedores de fuera van a verlos?

**Tanda 4.3** *(una vez por proyecto: decide si es «delicado»)* — ¿La marca o el material son de
un **cliente**, y sin permiso escrito para mandarlos a terceros? · ¿Hay datos de salud o personales
**de terceros**? · ¿El contrato deja fuera a los **subencargados** (proveedores de IA, generadores)? ·
¿La base de datos de desarrollo tendrá datos **reales**?

**Produce:** `06-etica-privacidad.md` · y si hay datos de salud, el pack de `cumplimiento-salud` con
su `gate_datos_salud.py` — que hoy solo se invoca desde `/deploy`, o sea el día del lanzamiento. Si
alguna de 4.3 es que sí: **`.claude/proyecto-delicado.md`** desde `templates/proyecto-delicado.md`,
con el motivo en su primera línea y quién lo decidió (con eso `aviso-envio-externo.sh` pregunta antes
de mandar nada fuera y `screenshot.py` pasa la guarda de datos personales: `rules/motores-de-diseno.md`
§7). Si es la última, además `datos_reales_desarrollo` en `CONFIGURACION.yaml` y, si son de terceros
con contrato pendiente, el candado (`patterns/stack/backend-candado-datos-reales.md`).

> **Límite honesto, y va escrito en el propio documento:** el gate comprueba que cada pieza exista,
> esté fechada y firmada. **No comprueba que sea correcta.** Un verde aquí no es un dictamen legal.

---

### Fase 4b — Superficie de ataque y defensas, ANTES de construir

> **Petición del Usuario (2026-09-12):** *«en todo el proceso también tiene que haber toda la parte
> de RGPD, ciberseguridad y OWASP. Hay auditores que ya lo revisan, pero tiene que estar ANTES de
> crear. La app tiene que estar súper robusta […] y luego, con el auditor, hacer ataques para ver
> que de verdad se cumple.»*
>
> La fase 4 cubre RGPD (qué datos, con qué base legal). Esta cubre lo otro: **por dónde entran**.
> Y la diferencia no es teórica — el incidente del 2026-09-11 que documenta `rules/security.md`
> entró **por la puerta buena, con una contraseña válida**: 258 IPs distintas contra `wp-login.php`
> en 14 días. Ninguna auditoría de código habría visto eso, porque no había nada que auditar.

**Tanda 4b.1 · quién entra** — ¿Quién se autentica, y con qué? (usuario y contraseña · SSO · enlace
mágico · clave de API) · ¿Hay administradores, y qué pueden hacer? · ¿Qué pasa **hoy** si alguien
consigue la contraseña de un administrador? · ¿Hay algo alcanzable **sin** autenticarse?

**Tanda 4b.2 · por dónde se entra** — ¿Qué entra de fuera sin que lo escriba un usuario nuestro?
(webhooks, ficheros subidos, correos, importaciones) · ¿Se publica algo en un puerto, o todo va
detrás de un proxy con dominio y HTTPS? · ¿Qué se registra en los logs, y hay algo que no debería
estar ahí?

**Las defensas se DECIDEN aquí, no se descubren después.** El mínimo, que sale directo de lo ya
medido en `rules/security.md` §autenticación web y §puertos:

| Defensa | Contra qué | Por qué está en el mínimo |
|---|---|---|
| **2FA en todas las cuentas de administración** | La contraseña robada o reutilizada | Es la **única** medida que habría cortado el incidente real en seco |
| **Límite de intentos + bloqueo de cuenta** | Fuerza bruta | Convierte 406 intentos en 5, y **avisa** de que alguien lo intenta |
| **Límite por IP** (`limit_req`, fail2ban) | Un atacante desde una IP | Mitiga; **no resuelve**: con 258 IPs el atacante rota |
| **Nada escucha en `0.0.0.0`** | El barrido de bots | Solo el proxy en 80/443. Y ojo: un puerto publicado por Docker **se salta el firewall del host** — medido |
| **Idempotencia** en lo que cobra, envía o publica | El reintento y el doble clic | `rules/api-http-contract.md` §5 |
| **Ningún secreto en la URL** | Logs, historial, `Referer`, capturas | `rules/api-http-contract.md` §4 |
| **Subida de ficheros acotada** | Ejecución remota | Tipo real (no la extensión), tamaño, y **fuera de la raíz servida** |

> ⚠️ **El límite por IP mitiga y no resuelve, y hay que decirlo:** el ataque medido venía de 258 IPs
> para 406 intentos, diseñado para quedar por debajo de cualquier umbral por IP. Lo que lo para es
> que **la contraseña no sea suficiente**. Prometer robustez con solo un `limit_req` es prometer lo
> que el dato no sostiene.

**Tanda 4b.3 · el tipo y las fronteras** *(sub-ola 2.25)* — ¿Qué tipo de proyecto es? (`web-marketing`
· `app` · `bot` · `salud` · `pentest`: fija el nivel ASVS, `skills/modelado-amenazas/references/asvs-por-tipo.md`)
· De todo lo que entra de fuera (4b.2), ¿qué sería lo más caro si saliera mal? · Si hay un agente con
tools, ¿qué puede hacer **sin preguntar** a nadie?

Con esas respuestas, la skill **`modelado-amenazas`** escribe `<plan>/arranque/modelo-amenazas.md`: las
fronteras de 4b.1-4b.2 con su STRIDE, la defensa decidida, su requisito ASVS y cómo se prueba; las cartas
de LINDDUN GO si la tanda 2.3 marcó campos personales; la Rule of Two si hay agentes. Se cierra con
`python3 .claude/scripts/gate_amenazas.py --modelo <plan>/arranque/modelo-amenazas.md` en verde.

**Produce:** `<plan>/arranque/07-superficie.md` — quién entra y cómo · qué es alcanzable sin
autenticar · la tabla de defensas **decididas** con su porqué · qué se registra y qué no · el **nivel
ASVS** del proyecto y el enlace a `modelo-amenazas.md` · y lo que se acepta como riesgo, escrito.

**Y el cierre, que es la otra mitad de la petición:** cuando el producto exista, **`sofia-pentester`
ataca de verdad** contra este documento y contra la columna «Cómo se prueba» del modelo de amenazas —
no contra su intuición. Cada defensa decidida aquí es un
caso de prueba suyo: intentar entrar sin 2FA, forzar el login, buscar el puerto abierto, subir un
fichero que no toca. Una defensa declarada y no probada es una declaración, no una defensa.

---

### Fase 5 — Cierre

Sin preguntas. Tres cosas: **promover** los documentos a `.docs/core/` (`gen_core.py --promote`),
**crear la sesión SpecKit** (`new-session.sh`) con `spec.md` **derivado** de los requisitos — así
`spec_lint.py` pasa por construcción, no por suerte — y a partir de ahí mandan `/speckit.plan` →
`/speckit.tasks` → `/speckit.implement` → `/speckit.converge`, **solo para ejecutar**.

El `spec.md` lo escribe `scripts/requisitos_to_spec.py`, no la memoria de nadie: primero
`python3 .claude/scripts/requisitos_to_spec.py <plan> <sesión> --check` (dice cuántos requisitos,
cuántas líneas y cuántos salen sin verbo o sin criterio; sobre fitapp, el 2026-10-21: 21 · 514 · 0 ·
0) y después sin `--check`. Lo que falte en la spec se arregla volviendo a la fase 1b, no a mano.

## Salida

| Documento | Ruta | Permanente en |
|---|---|---|
| Encuadre | `<plan>/arranque/00-encuadre.md` | — muere con el plan |
| PRD | `01-prd.md` | `.docs/core/producto/01-product-brief.md` |
| Requisitos | `02-requisitos.md` + `requisitos.json` | `.docs/core/producto/00-requisitos.md` |
| Modelo de datos | `03-modelo-datos.md` + `entidades.json` | `.docs/core/producto/06-data-model.md` |
| Flujos y trazas | `04-flujos.md` + `trazas.json` | `.docs/core/producto/02-user-flow.md` |
| Stack | `05-stack.md` | `.docs/core/arquitectura.md` |
| Ética | `06-etica-privacidad.md` | `.docs/core/privacidad.md` |
| Superficie de ataque | `07-superficie.md` | `.docs/core/seguridad.md` |
| Modelo de amenazas | `modelo-amenazas.md` | el mismo nombre, en `.docs/core/` |
| ADR | `.docs/adr/000N-*.md` | ya es permanente |

## Anti-patterns

- ❌ **Escribir un documento sin haber preguntado su tanda** → es exactamente lo que hace
  `/speckit.specify` y por lo que existe esta skill.
- ❌ Preguntar los 11 apartados de un requisito uno a uno → 77 turnos y sesión abandonada.
- ❌ Rellenar un hueco con algo plausible en vez de marcarlo `desconocido`.
- ❌ Guardar un dato sin su sobre de evidencia → al mes no se distingue lo acordado de lo supuesto.
- ❌ Saltarse la tanda 2.3 (qué campo es personal) → la fase 4 deja de derivarse y hay que reabrir
  la entrevista entera.
- ❌ Dar por buena una máquina de estados sin estado final.
- ❌ Ejemplos con `foo` o `test@test.com` en el apartado 7.
- ❌ Usar esta skill para configurar el harness (es `project-setup`) o para decidir pantallas
  (`/producto`).
- ❌ Correr `/speckit.specify` después de esto → su trabajo ya está hecho, y mejor, porque se preguntó.

## Ejemplos

### Usuario: «empieza»
TL: Fase 0, tanda 0.1 con `AskUserQuestion`: qué es esto en una frase · nuevo o módulo · ¿hay código?
No escribe ningún documento hasta tener las respuestas.

### Usuario: «quiero hacer una app para que las clínicas gestionen sus citas»
TL: detecta «clínica» → el escenario de cumplimiento se activa. Arranca la fase 0 **y avisa** de que
la fase 4 va a ser larga: datos de salud implican `sara-salud-datos` y `gate_datos_salud.py`.

### Usuario: «esto ya lo tengo a medias, sáltate el papeleo y ponte a programar»
TL: lo dice claro — el gate va a bloquear el primer `Write` a código. Dos salidas: correr las fases
que faltan (`gate_arranque.py . --explica` dice cuáles), o escribir la exención
`.docs/arranque/EXENCION.md` con su motivo y caducidad. **La exención la escribe el Usuario.**

## Related

- `rules/plan-gates.md` — Gate 0b (clarificación inversa) y Gate C, que esta skill hace ejecutables
- `templates/{prd,requisito,ticket,adr}-template.md` · `templates/screen-spec.md`
- `scripts/gate_arranque.py` · `hooks/gate-arranque.sh` — el gate y su hook. La firma de cada
  documento va en el frontmatter: `reviewed:` con una fecha real y `reviewed_by:` con la persona que lo
  revisó; el `autor:` que trae la plantilla solo cuenta si no hay `reviewed_by:`, y un agente no firma
  (2.17, MO-61). El hook solo mira lo que está DENTRO del proyecto: el scratchpad no es producto, un
  worktree sí
- `scripts/requisitos_to_spec.py` — los requisitos de la fase 1b → el `spec.md` de la sesión (fase 5)
- skill `modelado-amenazas` + `scripts/gate_amenazas.py` — la tanda 4b.3 y el Gate F de `plan-gates.md`
- `project-setup` — el harness, **no** el producto · `/producto` — las pantallas · `/otto` — la jugada
- `rules/verdict-contract.md` — el Gherkin de los criterios · `rules/adr.md` — la fase 3
