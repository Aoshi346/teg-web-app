#!/usr/bin/env python3
"""manual.html — el proceso entero explicado PASO A PASO, para quien llega nuevo.

QUÉ ES Y QUÉ NO ES. Esto es un MANUAL: explica cómo se trabaja aquí, y no cambia según el
proyecto. No confundir con `gen_proceso.py` → `proceso.html`, que es un TABLERO DE ESTADO: dice en
qué punto está UN proyecto concreto y se pinta de colores según lo medido en el disco.

    manual.html    cómo se hace            permanente, en .docs/core/     ← esto
    proceso.html   por dónde vamos         de un plan, en .docs/plans/

POR QUÉ ES UN GENERADOR Y NO UN HTML ESCRITO A MANO. Un manual del proceso escrito a mano envejece
en cuanto cambia un comando, y entonces enseña a hacer las cosas como ya no se hacen — que es peor
que no tener manual. Los pasos, sus comandos y sus enlaces viven aquí como datos.

PARA QUIÉN ESTÁ ESCRITO: alguien que se incorpora y no conoce ni el proceso ni la jerga. Por eso
cada paso responde siempre a lo mismo —qué es · por qué existe · qué haces TÚ · el comando · qué
deja escrito · cómo sabes que está bien · qué NO se decide aquí— y por eso hay glosario.

    python3 .claude/templates/report_kit/gen_manual.py [salida.html]
"""
from __future__ import annotations

import datetime as dt
import html as H
import os
import pathlib
import re
import sys

# Dónde está el material del curso, RELATIVO a la carpeta del manual: `.docs/core/ai4dev/`, igual
# en el template que en un derivado (allí lo copia `project-setup`). Hasta el 2026-10-19 el template
# lo leía de `sources/` del plan ai4dev; ese plan se archivó (LI-30) y el material vino aquí, que es
# donde ya lo buscaban los derivados. Se enlaza el gemelo `.html` de cada fuente y no el `.md`:
# servido, el `.md` se descarga en vez de abrirse (text/markdown).
AI4DEV = os.environ.get("AI4DEV_DIR", "ai4dev")

BLOQUES = [
    ("definir",  "1 · DEFINIR",  "Qué vamos a hacer y para quién. Sin esto, todo lo demás son suposiciones.", "#1e40af"),
    ("disenar",  "2 · DISEÑAR",  "Cómo se va a ver y cómo se usa. Antes de escribir una línea de código.",   "#7c3aed"),
    ("construir","3 · CONSTRUIR","Escribirlo. Es la parte que más se parece a «programar», y es la más corta.", "#0f766e"),
    ("verificar","4 · VERIFICAR","Comprobar que hace lo que dijimos. No es opcional y no es el final.",       "#b45309"),
]

PASOS = [
 dict(id="encuadre", bloque="definir", n="1", titulo="Encuadre", sub="¿qué es y para quién?",
  que="Escribir en una página qué se va a construir, para quién, y —sobre todo— qué NO entra.",
  porque="Es el paso que más se salta y el que más caro sale. Sin un «qué queda fuera» escrito, "
         "el proyecto crece sin que nadie decida que crezca, y la primera vez que alguien dice "
         "«ya que estamos» ya es tarde para discutirlo.",
  pasos=["Ejecuta el comando. **No escribas tú el documento**: la skill te va a preguntar.",
         "Contesta a las tandas de 3-4 preguntas. Si no sabes algo, **dilo**: hay una respuesta "
         "`desconocido` y es una respuesta válida.",
         "Nunca rellenes un hueco con algo que suene bien. Si no lo sabes, se marca y se pregunta "
         "a quien lo sepa.",
         "Revisa el «qué queda fuera» antes de cerrar. Si está vacío, el paso no está hecho."],
  comando="/arrancar",
  produce=".docs/plans/<plan>/arranque/00-encuadre.md",
  gate="python3 .claude/scripts/gate_arranque.py . --explica",
  no_aqui="Cómo se va a construir, qué tecnología, ni qué pantallas hace falta. Eso viene después.",
  leer=[("skills/arrancar/SKILL.md","la skill que te hace las preguntas")],
  mods=[("A-modulos-1-6","Módulos 4-5 — Planificación y documentación efectivas con AI")]),

 dict(id="prd", bloque="definir", n="2", titulo="PRD", sub="el problema y el éxito",
  que="El documento de producto: qué problema resuelve, a quién, y cómo sabremos que ha funcionado.",
  porque="«El éxito» tiene que ser algo que se pueda mirar. Si el criterio es «que quede bien», "
         "nadie puede decir nunca si se terminó.",
  pasos=["Sigue en `/arrancar` — es su fase 1, no hace falta otro comando.",
         "Escribe el criterio de éxito como algo **observable**: un número, una pantalla que "
         "existe, un correo que llega. No «que sea rápido».",
         "Si te sale un PRD de diez páginas, algo va mal: cabe en una."],
  comando="/arrancar  (fase 1)",
  produce=".docs/plans/<plan>/arranque/01-prd.md",
  gate="El mismo `gate_arranque.py`: comprueba que existe, que tiene contenido propio y que **no "
       "es la plantilla con el título cambiado**.",
  no_aqui="Los requisitos detallados. El PRD dice el problema; los requisitos dicen qué hace el sistema.",
  leer=[("templates/prd-template.md","el molde")],
  mods=[("A-modulos-1-6","Módulos 4-5 — Planificación y documentación efectivas con AI")]),

 dict(id="requisitos", bloque="definir", n="3", titulo="Requisitos", sub="los 11 apartados + Gherkin",
  que="Cada cosa que el sistema tiene que hacer, con sus 11 apartados y sus criterios de aceptación.",
  porque="Los 11 apartados existen porque un requisito de una línea se interpreta de cinco formas. "
         "Los cuatro que más se olvidan son: **qué hace el usuario · cuál es su entrada · cuál es "
         "la salida · un ejemplo con datos reales**.",
  pasos=["Sigue en `/arrancar` (fase 1b). Te pregunta 5 apartados; los otros 6 los redacta y tú los confirmas.",
         "Escribe los criterios en **Gherkin**: `Dado que… cuando… entonces…`. El «entonces» tiene "
         "que ser **una sola cosa que se pueda mirar**.",
         "Si no puedes escribir el «entonces» como algo observable, el requisito está mal escrito: "
         "devuélvelo, no lo apruebes.",
         "Pon un ejemplo con datos de verdad. Es el apartado que más discusiones evita seis meses después."],
  comando="/arrancar  (fase 1b)",
  produce=".docs/plans/<plan>/arranque/02-requisitos.md  →  requisitos.html",
  gate="python3 .claude/scripts/spec_lint.py <sesión>",
  no_aqui="Cómo se implementa. Un requisito dice QUÉ, nunca CÓMO.",
  leer=[("templates/requisito-template.md","los 11 apartados"),
        ("rules/verdict-contract.md","qué es Gherkin y cómo se verifica")],
  mods=[("D-openspec-specdd","Desarrollo guiado por especificación"),
        ("A-modulos-1-6","Módulos 4-5 — documentación efectiva")]),

 dict(id="datos", bloque="definir", n="4", titulo="Datos y flujos", sub="el ERD de diseño",
  que="Qué cosas guarda el sistema, cómo se relacionan, y por dónde pasa cada dato.",
  porque="Esto se decide **antes** de programar, no lo descubre el backend al escribirse. Y cada "
         "campo lleva marcado si es **dato personal**: de ahí sale sola la parte de RGPD del paso 6.",
  pasos=["Sigue en `/arrancar` (fase 2).",
         "Por cada campo, marca `personal: true|false`. **No es opcional**: si no lo marcas, el "
         "paso de ética hay que escribirlo a mano y se escribe peor.",
         "Genera el diagrama y míralo. Un modelo de datos que no se entiende mirándolo está mal.",
         "Más tarde, cuando exista código, `--diff` te dice qué se construyó distinto de lo previsto."],
  comando="python3 .claude/scripts/gen_modelo_datos.py <plan>",
  produce="arranque/03-modelo-datos.md · data-model.html · user-flows.html · trazas.html",
  gate="El gate comprueba que existe y está firmado. Que sea **correcto** lo dice quien conoce el negocio.",
  no_aqui="Qué base de datos se usa. Eso es el paso 5.",
  leer=[("rules/plan-docs-structure.md","dónde vive cada diagrama")],
  mods=[("B-modulos-7-12","Módulo 8 — Bases de datos"),
        ("E-graph-engineering","el recorrido del dato, no solo la estructura")]),

 dict(id="stack", bloque="definir", n="5", titulo="Stack y ADR", sub="con qué y por qué",
  que="Con qué tecnología se construye, y **por qué esa y no otra**, escrito para dentro de un año.",
  porque="Un ADR es una página que dice: qué problema había, qué se eligió, **qué se descartó y por "
         "qué**, y qué aceptamos perder. Sin las alternativas descartadas no es una decisión: es un anuncio.",
  pasos=["Sigue en `/arrancar` (fase 3).",
         "Antes de decidir construir algo, pregúntate si el mercado ya lo resuelve. Auth, pagos, "
         "envío de correo y búsqueda casi siempre se compran.",
         "Escribe el ADR **con la decisión fresca**, no después. A las dos semanas ya nadie recuerda "
         "las alternativas.",
         "Mínimo **dos alternativas descartadas** con su razón, y **las consecuencias negativas**. "
         "Si no encuentras ninguna, no has terminado de pensarla."],
  comando="cp .claude/templates/adr-template.md .docs/adr/000N-<slug>.md",
  produce="arranque/05-stack.md · .docs/adr/*.md",
  gate="Revisión humana. Un ADR sin alternativas descartadas se devuelve.",
  no_aqui="El diseño visual. Y tampoco la estructura de carpetas: eso sale del stack.",
  leer=[("rules/adr.md","cómo se escribe un ADR"),
        ("rules/plan-gates.md","el gate de comprar-o-construir")],
  mods=[("B-modulos-7-12","Módulos 9-10 — backend y frontend asistidos por AI"),
        ("A-backend-capas","el patrón de capas de casa")]),

 dict(id="etica", bloque="definir", n="6", titulo="Ética y RGPD", sub="qué datos y con qué base legal",
  que="Qué datos personales se tratan, con qué base legal, cuánto se guardan y quién más los ve.",
  porque="**Va antes de construir, no después.** Auditar al final encuentra los problemas cuando "
         "ya cuestan diez veces más. Y sale casi solo: el modelo de datos del paso 4 ya marcó qué "
         "campos son personales.",
  pasos=["Sigue en `/arrancar` (fase 4).",
         "Por cada dato personal del paso 4: **por qué se puede tratar** (base legal), **cuánto tiempo** "
         "se guarda, y **quién más lo ve** (proveedores, terceros).",
         "Si el producto trata datos de **salud**, para aquí y usa `/cumplimiento-salud`: son otras "
         "reglas y son más duras.",
         "Si el sistema **decide algo sobre una persona** (aprueba, puntúa, filtra), esa persona "
         "tiene derecho a que lo revise un humano. Eso hay que construirlo, no solo declararlo."],
  comando="/arrancar  (fase 4)   ·   /cumplimiento-salud  si hay datos de salud",
  produce="arranque/06-etica-privacidad.md",
  gate="El gate caza un documento que declara datos personales **sin base legal**.",
  no_aqui="La seguridad técnica (contraseñas, ataques). Eso es el paso 7 y es distinto.",
  leer=[("rules/ai-assistant-risk.md","el riesgo de usar IA con código de cliente"),
        ("rules/fairness-audit.md","si el sistema decide sobre personas")],
  mods=[("A-modulos-1-6","**Módulo 6 — Ética, Regulación y Privacidad en el uso de AI**")]),

 dict(id="seguridad", bloque="definir", n="7", titulo="Superficie de ataque", sub="por dónde entran, y las defensas",
  que="Por dónde puede entrar alguien que no debería, y qué se monta para impedirlo — **decidido antes**.",
  porque="Medido en esta casa: un minero de criptomonedas estuvo **17 días** dentro de un WordPress. "
         "No entraron por un fallo del código: entraron **con una contraseña válida**, por la puerta "
         "buena. Ninguna auditoría de código detecta eso.",
  pasos=["Sigue en `/arrancar` (fase 4b).",
         "Decide y escribe: **2FA** en las cuentas de administrador · **límite de intentos** de login · "
         "qué puertos se exponen (la respuesta correcta suele ser **ninguno**) · qué se registra en los logs.",
         "Nunca metas contraseñas, tokens ni datos personales en una URL: acaban en el log, en el "
         "historial del navegador y en las capturas de pantalla.",
         "Al final del proyecto, los auditores **atacan de verdad** para comprobar que se cumple."],
  comando="/arrancar  (fase 4b)   ·   python3 .claude/scripts/check_puertos_docker.py <proyecto>",
  produce="arranque/07-superficie.md",
  gate="python3 .claude/scripts/check_puertos_docker.py — sale 1 si algo se publica fuera",
  no_aqui="La base legal de los datos: eso era el paso 6.",
  leer=[("rules/security.md","la seguridad de la aplicación"),
        ("rules/agent-security.md","la seguridad del propio harness")],
  mods=[("C-modulos-13-18-extra","**Módulo 15 — DevSecOps: seguridad por diseño**"),
        ("C-modulos-13-18-extra","Módulo 13 — DevSecOps: infraestructura")]),

 dict(id="marca", bloque="disenar", n="8", titulo="Marca", sub="identidad · guía · kit · logo",
  que="Cómo se ve y qué transmite: identidad → guía → kit (paleta, tipografía, iconos, **logo**) → tokens.",
  porque="Sin esto, los diseños salen genéricos, y no por gusto: la herramienta de bocetos **detecta "
         "que no hay colores decididos y se pinta en grises a propósito**. La salida no es inventar "
         "colores: es hacer este paso.",
  pasos=["Comprueba primero si ya hay marca: `check_design_login.py`, y mira si el cliente ya tiene "
         "un sistema propio (Figma, un PDF, la web de Claude Design hasta el 14-12-2026). **Crear una marca paralela a la que ya usan es el fallo "
         "más caro de este paso.**",
         "Ejecuta `/marca`. Te preguntará en dos tandas qué tiene que transmitir. **No propongas "
         "colores todavía** — el color es el paso 3 de la skill.",
         "Del kit salen los **tokens**, y los tokens son lo que lee el código. Si te saltas eso, los "
         "tres pasos anteriores no sirven de nada.",
         "El **logo se elige**: tres direcciones distintas y decide una persona. Un logo que nadie "
         "eligió es el que se queda para siempre.",
         "Sirve `brand.html` y que lo mire alguien antes de seguir."],
  comando="python3 .claude/scripts/check_design_login.py   →   /marca",
  produce="arranque/10-identidad.md · 11-guia-marca.md · 12-kit-marca/ · brand.html · design-system.md",
  gate="Después de este paso, los bocetos **dejan de salir en grises**. Si siguen grises, el kit no "
       "llegó a los tokens.",
  no_aqui="Nada de pantallas concretas. Esto decide el idioma visual, no las frases.",
  leer=[("skills/marca/SKILL.md","los 6 pasos"),
        ("rules/motores-de-diseno.md","Parte F — el orden y qué herramienta va en cada casilla"),
        ("examples/marca-lumi/","**un ejemplo trabajado entero** — mira `brand.html`")],
  mods=[("K-estilo-evopreven-mejorado","el estilo como patrón de casa")]),

 dict(id="lowfi", bloque="disenar", n="9", titulo="Baja fidelidad", sub="¿está bien organizado?",
  que="Cajas grises: qué va arriba, qué se agrupa con qué, cuántos pasos tiene. **Sin color de marca.**",
  porque="Si enseñas un boceto con colores, la conversación se va al color y **nadie mira la "
         "estructura** — que es lo que costará caro cambiar después. En gris, se habla de la estructura.",
  pasos=["`/disenar-pantalla --lowfi`.",
         "**Texto real, nunca «lorem ipsum».** El relleno miente sobre el espacio que ocupa lo que "
         "vas a escribir de verdad.",
         "Enséñalo y que se decida en tres minutos. Esto se tira siempre: no le dediques una tarde.",
         "Si ya hay otra pantalla igual resuelta en el proyecto, **puedes saltarte este paso** — pero "
         "di que te lo saltas por eso y no por prisa."],
  comando="/disenar-pantalla --lowfi",
  produce="<plan>/bocetos/*lowfi*.html",
  gate="Lo mira el Usuario, en tres minutos. No hay script.",
  no_aqui="El color, la tipografía final y el tono del texto.",
  leer=[("rules/motores-de-diseno.md","§F2 — low-fi no es «high-fi en gris»")],
  mods=[("C-frontend-bulletproof","estructura de frontend")]),

 dict(id="highfi", bloque="disenar", n="10", titulo="Alta fidelidad", sub="¿está bien resuelto?",
  que="La pantalla como se va a ver de verdad, con los tokens reales y **los cuatro estados**.",
  porque="Los cuatro estados son: con datos · **vacía** · cargando · **error**. Los dos del medio son "
         "los que nadie diseña y los que el usuario ve el primer día.",
  pasos=["`/disenar-pantalla` (sin `--lowfi`).",
         "Usa **solo** colores que estén en `design-system.md`. Si falta uno, el que falta es el "
         "paso de marca — no te lo inventes aquí.",
         "Dibuja los cuatro estados. Si no sabes qué poner en el vacío, esa pantalla no está pensada.",
         "Que lo miren los auditores visuales antes de escribir código."],
  comando="/disenar-pantalla",
  produce="<plan>/bocetos/*.html",
  gate="`vera-art-director` y `aitor-a11y-auditor` sobre el boceto servido.",
  no_aqui="Cómo se implementa. Y ya no se rediscute la estructura: eso se cerró en el paso 9.",
  leer=[("skills/disenar-pantalla/SKILL.md","cómo generar variantes comparables")],
  mods=[("B-modulos-7-12","Módulo 10 — frontend asistido por AI")]),

 dict(id="mockup", bloque="construir", n="11", titulo="Mockup vivo", sub="funciona con datos simulados",
  que="La pantalla **funcionando y navegable**, con datos falsos. Todavía sin backend.",
  porque="Enseñar algo que funciona a la semana cambia por completo la conversación con el cliente. "
         "Y no hace falta el backend: **hace falta el contrato**, que se decidió en el paso 4.",
  pasos=["`/nueva-pantalla --mockup`.",
         "Los datos los sirve **MSW** (un simulador que responde como responderá el backend). Ya "
         "venía en el molde de ficheros y no lo usaba nadie.",
         "**Nunca escribas los tipos a mano «provisionalmente».** Ese provisional se queda. Si no hay "
         "contrato, no hay mockup: hay invención.",
         "Aquí ya entran todos los auditores y el ciclo de QA completo — antes de que exista una "
         "línea de backend."],
  comando="/nueva-pantalla --mockup",
  produce="El frontend corriendo, navegable, con datos simulados",
  gate="/qa-loop con la aplicación corriendo",
  no_aqui="Nada de guardar datos de verdad.",
  leer=[("skills/nueva-pantalla/SKILL.md","el molde de 10 ficheros"),
        ("rules/motores-de-diseno.md","§F3 — el contrato, no el backend")],
  mods=[("C-frontend-bulletproof","el patrón de frontend"),
        ("B-modulos-7-12","Módulo 10 — frontend")]),

 dict(id="desarrollo", bloque="construir", n="12", titulo="Desarrollo", sub="backend · datos · frontend real",
  que="Todo el desarrollo de verdad: la base de datos, la lógica, los permisos, y el frontend hablando "
      "con el backend real en vez de con el simulador.",
  porque="Aquí el diseño **ya no se rediscute**. Si aparece una discusión de diseño en este paso, es "
         "que un paso anterior se cerró mal.",
  pasos=["Sustituye el contrato de diseño por el real que genera el backend, y **mira el diff**: ahí "
         "aparece lo que cambió sin avisar.",
         "Los simuladores de MSW vuelven a ser solo de test: dejan de servir al navegador.",
         "**Antes de correr tests, comprueba la memoria**: `bash .claude/hooks/check-ram.sh`. Y nunca "
         "lances `pytest` entero — siempre por módulo.",
         "Commit por cada paso terminado, con mensaje que explique **por qué**, no solo qué."],
  comando="bash .claude/hooks/check-ram.sh   →   pytest apps/<modulo> -v --maxfail=3",
  produce="El producto funcionando de verdad",
  gate="`python manage.py migrate` contra la base real — `check` no habla con la base de datos",
  no_aqui="Rediscutir el diseño. Y decidir cosas de producto: eso se cerró en el bloque 1.",
  leer=[("rules/verification.md","por qué `check` en verde no basta"),
        ("rules/ram-pytest.md","por qué pytest entero mata el servidor")],
  mods=[("B-modulos-7-12","Módulos 8-9 — bases de datos y backend"),
        ("A-backend-capas","las capas"), ("B-backend-infra","infraestructura")]),

 dict(id="qa", bloque="verificar", n="13", titulo="QA", sub="auditores y doble evidencia",
  que="Comprobar que hace lo que dijimos, con **evidencia**: en el código **y** en la pantalla.",
  porque="La regla que más se incumple: **«hecho» exige ver las dos cosas.** El código puede tener "
         "algo que no se renderiza, y la pantalla puede mostrar algo que no está en el repo. Con una "
         "sola de las dos, el veredicto es «a medias», no «hecho».",
  pasos=["Congela la versión que vas a auditar y **no la toques mientras corren los auditores**. "
         "Ya pasó: se parcheó en caliente y la nota resultante no describía nada real.",
         "Lanza `/qa-loop`. Tres auditores en paralelo, cada uno con su ángulo.",
         "Lee los hallazgos buscando **la intención** antes de condenar: el código raro suele ser "
         "deliberado y llevar su comentario. Mira el `git log` de esas líneas.",
         "Arregla, y **vuelve a pasar la ronda entera**. Un arreglo declarado y no verificado ya se "
         "ha colado tres veces."],
  comando="/qa-loop",
  produce=".docs/feedback/qa-loop/<wave>/",
  gate="Media ≥ 9.0 **y** los gates categóricos: cero P0 abiertos, y los tres auditores sobre la misma versión",
  no_aqui="Añadir funcionalidad. Si aparece algo nuevo, es un requisito y vuelve al paso 3.",
  leer=[("rules/qa-loop.md","el protocolo entero"),
        ("rules/verdict-contract.md","la doble evidencia 🔎/👁")],
  mods=[("B-modulos-7-12","Módulos 7 y 11 — testing y QA con AI"),
        ("M-mejorar-lidia-medible","cómo se mide a un auditor")]),
]

GLOSARIO = [
 ("PRD","El documento de producto. Dice qué problema se resuelve, para quién, y cómo sabremos que ha funcionado. Cabe en una página."),
 ("Requisito","Una cosa que el sistema tiene que hacer. Aquí cada uno lleva 11 apartados, para que no se pueda interpretar de cinco formas."),
 ("Gherkin","Una forma de escribir criterios: «Dado que… cuando… entonces…». Sirve porque el «entonces» ya te dice cómo comprobarlo."),
 ("Gate","Un script que dice sí o no, y no opina. Si sale con error, no se pasa de fase. Un gate que nadie ha visto fallar no es un gate."),
 ("ADR","Una página con una decisión de arquitectura: el contexto, qué se eligió, qué se descartó y por qué, y qué aceptamos perder."),
 ("ERD","El diagrama de qué cosas guarda el sistema y cómo se relacionan entre sí."),
 ("Token (de diseño)","Un color, un tamaño o un espacio con nombre, declarado en un solo sitio. El código los lee de ahí; nadie escribe un color a mano."),
 ("Low-fi / High-fi","Baja y alta fidelidad. El primero son cajas grises y contesta «¿está bien organizado?»; el segundo se ve de verdad y contesta «¿está bien resuelto?»."),
 ("MSW","Un simulador que responde como responderá el backend. Permite que el frontend funcione antes de que exista el backend."),
 ("Mockup","La pantalla funcionando y navegable, pero con datos falsos. Se puede enseñar."),
 ("Skill","Un procedimiento empaquetado que se invoca escribiendo `/nombre`. No es un chat: son pasos con un orden."),
 ("SpecKit","El sistema que ordena la ejecución por fases (waves) cuando el trabajo es grande. Entra DESPUÉS de que esté todo definido."),
 ("Wave","Un bloque de trabajo dentro de una sesión de SpecKit. Se cierra con su gate antes de abrir el siguiente."),
 ("Doble evidencia","Para decir que algo está hecho hay que verlo en el código 🔎 y en la pantalla 👁. Con una sola, es «a medias»."),
 ("RGPD","El reglamento europeo de protección de datos. Aquí se decide ANTES de construir, no se audita después."),
 ("Modo noche","Dejar trabajo corriendo sin nadie mirando. Solo se puede si la documentación está completa: lo que hace preguntar a las 3 de la mañana es un hueco en los documentos."),
]

ATASCOS = [
 ("No sé qué contestar a una pregunta de `/arrancar`",
  "Contesta `desconocido`. Es una respuesta válida y queda marcada. Lo que **no** vale es inventar algo que suene razonable: eso se convierte en un requisito que nadie decidió."),
 ("El gate me bloquea y no entiendo por qué",
  "`python3 .claude/scripts/gate_arranque.py . --explica` te dice qué falta y cómo se arregla. Si dice que un documento «es la plantilla», es que se copió el molde y se cambió el título."),
 ("Los bocetos me salen en gris",
  "No es un fallo: es a propósito. Significa que no hay tokens de marca decididos. La salida es hacer el paso 8, no inventar colores."),
 ("Me piden empezar a programar ya",
  "Se puede: alguien con autoridad dice explícitamente «sáltate esto y ponte a programar». Pero se escribe una exención con motivo, responsable y fecha de caducidad. Lo que no vale es saltárselo en silencio."),
 ("Un auditor dice que algo está mal y yo creo que está bien",
  "Busca la intención antes de discutir: mira si esa línea tiene un comentario que la explique (`// defensive:`, `// workaround:`) y mira su `git log`. El código raro suele ser deliberado."),
 ("He terminado, ¿ya está?",
  "No hay «hecho» sin verificar: el código corre, los tests del módulo pasan, hay captura si hay pantalla, y la consola del navegador está limpia. Sin las cuatro, está a medias."),
]


def md(s):
    """Negrita, código y saltos — lo mínimo para que el texto se lea."""
    s = H.escape(str(s))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s

W, HT, GX, GY, COLS = 206, 74, 34, 30, 4

def maquina(BLOQUES, PASOS):
    """La máquina entera: una banda por bloque, nodos en filas de 4, flechas entre consecutivos."""
    pos, filas, y = {}, [], 8
    bandas = []
    for bid, btit, bsub, bcol in BLOQUES:
        ns = [p for p in PASOS if p["bloque"] == bid]
        chunks = [ns[i:i+COLS] for i in range(0, len(ns), COLS)]
        y0 = y
        y += 30                                  # cabecera de la banda
        for ch in chunks:
            for i, p in enumerate(ch):
                pos[p["id"]] = (10 + i*(W+GX), y)
            filas.append([p["id"] for p in ch]); y += HT + GY
        bandas.append((bid, btit, bsub, bcol, y0, y - GY + 10))
    ancho = 10 + COLS*(W+GX) - GX + 10
    alto = y + 4
    g = []
    for bid, btit, bsub, bcol, y0, y1 in bandas:
        g.append(f'<rect x="2" y="{y0}" width="{ancho-4}" height="{y1-y0}" rx="12" '
                 f'fill="{bcol}0d" stroke="{bcol}33"/>'
                 f'<text x="14" y="{y0+20}" font-size="12" font-weight="700" fill="{bcol}" '
                 f'letter-spacing=".08em">{H.escape(btit)}</text>')
        # El subtítulo del bloque SALE del SVG a propósito. Estaba dentro y las flechas entre
        # bloques lo cruzaban; moverlo de sitio solo cambiaba a quién cruzaban. Fuera del dibujo,
        # la clase de fallo desaparece en vez de desplazarse — y encima se lee mejor.

    orden = [p["id"] for p in PASOS]
    for a, b in zip(orden, orden[1:]):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        if y1 == y2:
            g.append(f'<line x1="{x1+W}" y1="{y1+HT/2}" x2="{x2-4}" y2="{y2+HT/2}" '
                     f'stroke="#94a3b8" stroke-width="1.8" marker-end="url(#fl)"/>')
        else:
            # La bajada NO entra por el centro del nodo destino: la etiqueta del bloque ocupa
            # los primeros ~150 px y la línea la cruzaba (visto en la captura). Entra por el
            # cuarto derecho, que siempre queda despejado.
            my = y1 + HT + 14
            xd = x2 + W * 0.75
            g.append(f'<path d="M{x1+W/2} {y1+HT} V{my} H{xd} V{y2-4}" fill="none" '
                     f'stroke="#94a3b8" stroke-width="1.8" marker-end="url(#fl)"/>')
    col = {b[0]: b[3] for b in BLOQUES}
    for p in PASOS:
        x, y = pos[p["id"]]; c = col[p["bloque"]]
        g.append(
          f'<a href="#p-{p["id"]}"><g class="nodo">'
          f'<rect x="{x}" y="{y}" width="{W}" height="{HT}" rx="10" fill="#fff" stroke="{c}" stroke-width="2"/>'
          f'<circle cx="{x+22}" cy="{y+24}" r="12" fill="{c}"/>'
          f'<text x="{x+22}" y="{y+28}" font-size="12" font-weight="700" fill="#fff" '
          f'text-anchor="middle">{p["n"]}</text>'
          f'<text x="{x+42}" y="{y+28}" font-size="14" font-weight="700" fill="{c}">'
          f'{H.escape(p["titulo"])[:22]}</text>'
          f'<text x="{x+13}" y="{y+50}" font-size="11" fill="#475569">{H.escape(p["sub"])[:34]}</text>'
          f'<text x="{x+13}" y="{y+65}" font-size="10" fill="#94a3b8">pulsa para abrirlo</text>'
          f'</g></a>')
    return (f'<svg viewBox="0 0 {ancho} {alto}" width="100%" style="max-width:{ancho}px">'
            f'<defs><marker id="fl" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">'
            f'<path d="M0,0 L0,6 L8,3 z" fill="#94a3b8"/></marker></defs>' + "".join(g) + "</svg>")

def tarjeta(p, col, AI4DEV):
    pasos = "".join(f"<li>{md(x)}</li>" for x in p["pasos"])
    leer = "".join(f'<li><a href="../../.claude/{r}">{H.escape(r)}</a> — {md(d)}</li>'
                   for r, d in p["leer"])
    mods = "".join(f'<li><a href="{AI4DEV}/{f}.html">{H.escape(f)}</a> — {md(d)}</li>'
                   for f, d in p["mods"])
    return f"""<section class="paso" id="p-{p['id']}">
<div class="ph" style="border-color:{col}">
  <span class="pn" style="background:{col}">{p['n']}</span>
  <div><h3>{H.escape(p['titulo'])}</h3><p class="psub">{H.escape(p['sub'])}</p></div>
</div>
<p class="pq">{md(p['que'])}</p>
<div class="pw"><b>Por qué existe este paso.</b> {md(p['porque'])}</div>
<p class="rot">Qué haces tú</p>
<ol class="pasos">{pasos}</ol>
<div class="grid2">
  <div><p class="rot">El comando</p><pre>{H.escape(p['comando'])}</pre>
       <p class="rot">Qué deja escrito</p><p class="mini"><code>{H.escape(p['produce'])}</code></p></div>
  <div><p class="rot">Cómo sabes que está bien</p><p class="mini">{md(p['gate'])}</p>
       <p class="rot">Qué NO se decide aquí</p><p class="mini">{md(p['no_aqui'])}</p></div>
</div>
<div class="grid2">
  <div><p class="rot">Para leer más</p><ul class="mini">{leer}</ul></div>
  <div><p class="rot">Del curso AI4DEV</p><ul class="mini">{mods}</ul></div>
</div>
<p class="volver"><a href="#maquina">↑ volver a la máquina</a></p>
</section>"""


def leyenda(BLOQUES):
    """Los cuatro bloques explicados, debajo del dibujo."""
    f = "".join(
      f'<div style="border-left:3px solid {c};padding-left:12px">'
      f'<p style="margin:0;font-size:12px;font-weight:700;letter-spacing:.08em;color:{c}">'
      f'{H.escape(tit)}</p><p style="margin:2px 0 0;font-size:14px;color:#475569">'
      f'{H.escape(sub)}</p></div>' for _, tit, sub, c in BLOQUES)
    return ('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));'
            f'gap:16px;margin-top:16px">{f}</div>')

COL = {b[0]: b[3] for b in BLOQUES}

def build(destino: pathlib.Path) -> str:
    glos = "".join(f"<tr><td><b>{H.escape(t)}</b></td><td>{md(d)}</td></tr>" for t, d in GLOSARIO)
    atasc = "".join(f'<details><summary>{H.escape(q)}</summary><p>{md(a)}</p></details>'
                    for q, a in ATASCOS)
    tarjetas = "".join(tarjeta(p, COL[p["bloque"]], AI4DEV) for p in PASOS)
    idx = " · ".join(f'<a href="#p-{p["id"]}">{p["n"]}. {H.escape(p["titulo"])}</a>' for p in PASOS)

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Manual del proceso — paso a paso</title><style>
*{{box-sizing:border-box}}
body{{margin:0;padding:0;background:#f6f7f9;color:#0f172a;
 font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:16px;line-height:1.65;
 -webkit-font-smoothing:antialiased}}
.w{{max-width:1080px;margin:0 auto;padding:26px 20px 60px}}
h1{{font-size:32px;line-height:1.15;margin:0 0 8px;font-weight:700;letter-spacing:-.01em}}
h2{{font-size:22px;margin:44px 0 10px;font-weight:700;scroll-margin-top:60px}}
h3{{font-size:19px;margin:0;font-weight:700}}
.lead{{font-size:18px;color:#475569;margin:0 0 6px}}
.rot{{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#64748b;
 font-weight:700;margin:16px 0 5px}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px;margin:14px 0;
 box-shadow:0 1px 2px rgba(15,23,42,.05)}}
.nav{{position:sticky;top:46px;z-index:9;background:rgba(246,247,249,.95);backdrop-filter:blur(6px);
 border-bottom:1px solid #e2e8f0;padding:9px 20px;font-size:12.5px;line-height:2}}
.nav a{{color:#334155;text-decoration:none;white-space:nowrap}}
.nav a:hover{{text-decoration:underline}}
.nodo rect{{transition:filter .12s}} .nodo:hover rect{{filter:brightness(.97)}}
.paso{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:22px;margin:18px 0;
 scroll-margin-top:58px}}
.ph{{display:flex;gap:13px;align-items:center;border-left:4px solid;padding-left:13px;margin-bottom:14px}}
.pn{{width:30px;height:30px;border-radius:999px;color:#fff;font-weight:700;display:flex;
 align-items:center;justify-content:center;flex:0 0 30px;font-size:15px}}
.psub{{margin:1px 0 0;color:#64748b;font-size:14px}}
.pq{{font-size:17.5px;margin:0 0 12px}}
.pw{{background:#fffbeb;border-left:3px solid #d97706;padding:11px 15px;border-radius:0 9px 9px 0;
 font-size:15px;margin:0 0 4px}}
ol.pasos{{margin:4px 0 8px;padding-left:22px}} ol.pasos li{{margin:6px 0}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:6px}}
@media(max-width:760px){{.grid2{{grid-template-columns:1fr}}}}
pre{{background:#0f172a;color:#e2e8f0;padding:11px 13px;border-radius:9px;font-size:13.5px;
 overflow-x:auto;margin:0}}
code{{font-family:ui-monospace,Menlo,monospace;font-size:13.5px;background:#f1f5f9;
 padding:1px 5px;border-radius:4px}}
pre code{{background:none;padding:0}}
.mini{{font-size:14.5px;margin:0}} ul.mini{{padding-left:20px;margin:0}} ul.mini li{{margin:4px 0}}
a{{color:#1d4ed8}}
table{{width:100%;border-collapse:collapse;font-size:15px}}
td{{padding:8px 10px;border-bottom:1px solid #eef2f7;vertical-align:top}}
td:first-child{{width:180px;white-space:nowrap}}
details{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px;margin:8px 0}}
summary{{cursor:pointer;font-weight:600}}
details p{{margin:9px 0 0;font-size:15px}}
.volver{{margin:16px 0 0;font-size:13px}}
.avisoI{{background:#eff6ff;border-left:3px solid #1d4ed8;padding:12px 16px;border-radius:0 9px 9px 0;margin:14px 0}}
.avisoR{{background:#fef2f2;border-left:3px solid #b91c1c;padding:12px 16px;border-radius:0 9px 9px 0;margin:14px 0}}
.pie{{margin-top:40px;padding-top:14px;border-top:1px solid #e2e8f0;font-size:13px;color:#64748b}}
@media print{{.nav{{display:none}} .paso,.card{{break-inside:avoid;box-shadow:none}} body{{background:#fff}}}}
</style></head><body>
<!-- NAV:BEGIN --><!-- NAV:END -->
<div class="nav"><b>Ir a:</b> <a href="#maquina">La máquina</a> · {idx} ·
<a href="#glosario">Glosario</a> · <a href="#atascos">Si te atascas</a> · <a href="#curso">El curso</a></div>
<div class="w">

<h1>Cómo se hace un proyecto aquí</h1>
<p class="lead">Trece pasos, en este orden. Cada uno decide <b>una</b> cosa y deja <b>un</b> documento.</p>

<div class="avisoI"><b>Léete esto antes de tocar nada.</b> Este manual no es una recomendación: es el
orden en que se trabaja. Los pasos no están en este orden por gusto — cada uno usa lo que decidió el
anterior, y saltarse uno no ahorra tiempo: lo gasta más tarde y más caro. Si un paso te parece
innecesario, <b>pregunta antes de saltártelo</b>: casi siempre está ahí porque algo salió mal una vez.</div>

<div class="card">
<p class="rot">Las cinco cosas que hay que saber antes de empezar</p>
<ol class="pasos">
<li><b>Tú no escribes los documentos: los contesta una entrevista.</b> Escribes <code>/arrancar</code>
y te va preguntando por tandas. Tu trabajo es contestar bien, no redactar.</li>
<li><b>«No lo sé» es una respuesta válida y correcta.</b> Se marca como <code>desconocido</code> y se
pregunta a quien lo sepa. Inventar algo que suene razonable es el peor error posible: se convierte
en un requisito que nadie decidió.</li>
<li><b>Un «gate» es un script que dice sí o no.</b> No opina y no se le discute. Si sale en rojo, no
se pasa de fase. Si no entiendes por qué te bloquea, añádele <code>--explica</code>.</li>
<li><b>Nada está «hecho» hasta que se ve.</b> Hace falta verlo en el código <b>y</b> en la pantalla.
Con una sola de las dos cosas, está a medias.</li>
<li><b>Commit a menudo, con el porqué en el mensaje.</b> El «qué» ya lo dice el diff; lo que se
pierde es el porqué.</li>
</ol>
</div>

<div class="avisoR"><b>Lo único que nunca se hace sin preguntar:</b> desplegar a producción · borrar
datos de verdad · fusionar a la rama principal · instalar cosas en el sistema · gastar dinero. Si
dudas de si algo entra en esta lista, es que entra: pregunta.</div>

<h2 id="maquina">La máquina entera</h2>
<p class="lead">Pulsa cualquier paso para abrir sus instrucciones.</p>
<div class="card"><div style="overflow-x:auto">{maquina(BLOQUES, PASOS)}</div>
{leyenda(BLOQUES)}</div>

<h2>Los pasos, uno a uno</h2>
{tarjetas}

<h2 id="glosario">Glosario — la jerga, en cristiano</h2>
<div class="card"><table>{glos}</table></div>

<h2 id="atascos">Si te atascas</h2>
{atasc}

<h2 id="curso">La documentación del curso AI4DEV</h2>
<p class="lead">Está entera en el repo. Cada paso de arriba enlaza el módulo que le toca; esta es la
lista completa.</p>
<div class="card"><table>
<tr><td><b>Módulos 1-6</b></td><td>Introducción a la IA en desarrollo (1-2) · Lab de IDEs (3) ·
<b>Planificación y documentación efectivas (4-5)</b> · <b>Ética, regulación y privacidad (6)</b>
<br><a href="{AI4DEV}/A-modulos-1-6.html">A-modulos-1-6.md</a></td></tr>
<tr><td><b>Módulos 7-12</b></td><td>Testing y calidad (7) · Bases de datos (8) · Backend (9) ·
Frontend (10) · Tests automáticos y QA (11) · Lab de chatbot (12)
<br><a href="{AI4DEV}/B-modulos-7-12.html">B-modulos-7-12.md</a></td></tr>
<tr><td><b>Módulos 13-18</b></td><td>DevSecOps e infraestructura (13) · <b>Seguridad por diseño y
observabilidad (15)</b> · Multi-agentes (16) · El futuro del rol (17-18)
<br><a href="{AI4DEV}/C-modulos-13-18-extra.html">C-modulos-13-18-extra.md</a></td></tr>
<tr><td><b>Patrón de backend</b></td><td>Las capas de aplicación y la infraestructura, con el patrón
de casa<br><a href="{AI4DEV}/A-backend-capas.html">A-backend-capas.md</a> ·
<a href="{AI4DEV}/B-backend-infra.html">B-backend-infra.md</a></td></tr>
<tr><td><b>Patrón de frontend</b></td><td>bulletproof-react analizado a fondo
<br><a href="{AI4DEV}/C-frontend-bulletproof.html">C-frontend-bulletproof.md</a></td></tr>
<tr><td><b>Especificación</b></td><td>OpenSpec, SpecDD y spec-kit comparados
<br><a href="{AI4DEV}/D-openspec-specdd.html">D-openspec-specdd.md</a></td></tr>
<tr><td><b>El recorrido del dato</b></td><td>Grafos para entender cómo funciona algo sin leer el código
<br><a href="{AI4DEV}/E-graph-engineering.html">E-graph-engineering.md</a></td></tr>
<tr><td><b>El harness</b></td><td>Manual de Claude Code, orquestación y seguridad
<br><a href="{AI4DEV}/F-drive-claudecode-harness.html">F-…-harness.md</a> ·
<a href="{AI4DEV}/H-drive-claudecode-orquestacion-seguridad.html">H-…-orquestacion-seguridad.md</a></td></tr>
<tr><td><b>Estilo y auditores</b></td><td>El estilo como patrón de casa · cómo se mide a un auditor
<br><a href="{AI4DEV}/K-estilo-evopreven-mejorado.html">K-estilo-…md</a> ·
<a href="{AI4DEV}/M-mejorar-lidia-medible.html">M-mejorar-lidia-medible.md</a></td></tr>
</table></div>

<div class="avisoI"><b>Y un último apunte, que es el que más tiempo ahorra.</b> La parte lenta de este
proceso son los pasos 1 a 7: pensar y escribir. La parte rápida es programar. Eso sorprende al
principio y es deliberado — cuando la documentación está completa, el trabajo de construir se puede
dejar corriendo sin nadie mirando, porque no queda ninguna decisión que preguntar. Lo que hace que
un agente te despierte a las tres de la mañana no es su autonomía: es un hueco en los documentos.</div>

<p class="pie"><b>Generado</b> por <code>.claude/templates/report_kit/gen_manual.py</code> el {dt.date.today()}.
No se edita a mano: se regenera. · Este manual explica <b>el proceso</b>; para ver en qué punto está
un proyecto concreto, eso es <code>proceso.html</code> de su plan, que es otra cosa.</p>
</div></body></html>"""

if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".docs/core/manual.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(out), encoding="utf-8")
    print(f"OK {out}  ({len(PASOS)} pasos · {len(GLOSARIO)} términos · {out.stat().st_size//1024} KB)")
