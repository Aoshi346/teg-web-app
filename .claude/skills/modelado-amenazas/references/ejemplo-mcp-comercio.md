---
reviewed: 2026-10-21
reviewed_by: agente de la sub-ola 2.25 (worktree) y, con H1-H6, el de la 2.24 en proyectos; pendiente de que lo lea el dueño del kit
asvs_nivel: L2
asvs_extra: v5.0.0-8.3.3
datos_personales: sí
agentes_llm: sí
---
# Modelo de amenazas · el servidor MCP de comercio (`.claude/templates/mcp-comercio/`)

> **Caso real del template, leído en solo lectura el 2026-10-20 y puesto al día el 2026-10-21** con H1-H6
> resueltos: `.claude/templates/mcp-comercio/nucleo.py` (413 líneas), su `README.md`, `test_nucleo.py`
> (21 tests: los 13 de la 3.42 y 8 de H1-H6, que fallan con el núcleo de antes) y
> `.claude/patterns/stack/agente-mcp-comercio.md`, que trae las medidas de X-17 (sub-ola 3.42, clon de musa). Tipo de proyecto `bot` → ASVS **L2 +
> v5.0.0-8.3.3** (`asvs-por-tipo.md`). Lo valida
> `python3 .claude/scripts/gate_amenazas.py --modelo <este fichero>`. Sirve de ejemplo de la skill: así
> queda un modelo de una página sobre algo que ya existe.
> Revisado por `priya-privacy-auditor` el 20-10 (sus hallazgos 2-01 a 2-05 están incorporados).

## 1. Qué construimos: las fronteras

| Id | Frontera (de → a) | Qué cruza | Quién está al otro lado |
|---|---|---|---|
| F1 | Cliente MCP → `/mcp` del servidor (127.0.0.1; fuera, detrás del proxy TLS) | token `Bearer` del comercio, cabecera `X-Conversacion`, nombre de tool y argumentos | cualquiera que llegue al puerto; con token, el runtime del bot, Claude Code o un agente de fuera |
| F2 | Servidor → tools del bot y su base de datos (en proceso, `Proyecto.herramientas`) | argumentos ya validados, comercio y conversación comprobados | el código del proyecto, con su cuenta de servicio |
| F3 | Tools → cliente MCP (la salida) | texto de la tool escrito para el LLM del bot, con contenido del catálogo | el modelo que lo consume, que lee ese texto como contexto |
| F4 | Servidor → registro JSONL | comercio, tool, nombres de los argumentos, conversación, resultado y milisegundos | quien pueda leer el fichero |
| F5 | Runtime del bot → proveedor del LLM | el texto de las tools (pedido, nombre, email o dirección del cliente) dentro del prompt | un tercero que trata datos por cuenta del comercio |

## 2. Qué puede ir mal y qué hacemos (STRIDE por frontera)

| Frontera | STRIDE | Amenaza | Respuesta | Defensa decidida | ASVS | Cómo se prueba |
|---|---|---|---|---|---|---|
| F1 | S | token de un comercio robado o adivinado: se actúa como ese comercio | mitigar | token aleatorio por cliente y comercio en el gestor de secretos; de una tabla fija el proceso guarda solo su SHA-256, y sin token válido sale 401 antes de MCP (`nucleo.py:232-283`) | v5.0.0-13.3.1, v5.0.0-14.2.1 | `test_sin_token_o_token_falso_es_401` |
| F1 | S | el token es una credencial fija: no caduca ni rota, y ASVS pide entre componentes cuentas individuales, tokens de corta vida o certificados | mitigar | cada token es una `Credencial` de UN cliente (el bot, Claude Code…) para un comercio, con hora de caducidad: caducado, sin `Credencial`, con una caducidad que no es un número finito (NaN) o con más vida que `vida_maxima_s` (24 h por defecto) no vale; la tabla puede ser una función que se lee en cada petición, en un hilo, así que se rota sin reiniciar; si no se puede leer, no entra nadie (`nucleo.py:69,89-94,172-173,244-263,319-324`; resuelto el 21-10, hallazgo H1) | v5.0.0-13.2.1 | `test_h1_token_caducado_con_demasiada_vida_o_sin_caducidad_no_vale` · `test_h1_la_tabla_de_tokens_se_rota_sin_reiniciar` |
| F1 | E | el cliente elige el comercio con un argumento (`client_id`) | eliminar | el comercio solo sale del token (`nucleo.py:282,307-309`); un argumento de más lo rechaza el esquema con `additionalProperties: false` (`nucleo.py:130,377`) | v5.0.0-8.4.1, v5.0.0-15.3.3 | `test_el_tenant_no_se_cuela_por_un_argumento` |
| F1 | I | pedir la conversación o el pedido de otro comercio | mitigar | `es_suyo()` antes de llamar a la tool; ajeno, inexistente o basura dan la misma respuesta; la conversación tiene que ser un id de cifras ASCII antes de preguntar (`nucleo.py:163-165,384-394`) | v5.0.0-8.2.2, v5.0.0-8.4.1 | `test_conversacion_ajena_inexistente_o_basura_dan_lo_mismo` · `test_recurso_ajeno_e_inexistente_dan_acceso_denegado` |
| F1 | T | argumentos imposibles (cantidad −3) que la tool llevaba a la base de datos | mitigar | el esquema de la tool más las cotas del proyecto, validado con `jsonschema` antes de invocar (`nucleo.py:125-135,376-382`) | v5.0.0-2.2.1 | `test_argumento_invalido_nombra_el_campo` |
| F1 | D | un cliente con token llama en bucle | transferir | el núcleo no limita el ritmo: lo pone el proxy TLS si se publica fuera de la máquina (README, «Lo que el núcleo NO hace») | v5.0.0-2.4.1 | — |
| F1 | R | los intentos con un token malo no quedan en ningún sitio | mitigar | cada 401 deja una línea en el registro con su motivo (`sin_token`, `token_desconocido`, `token_caducado`, `vida_excesiva`, `credencial_mal_formada`, `tabla_no_disponible`) y nunca el token, y el cuerpo del 401 es el mismo para todos; cada llamada aceptada lleva el cliente de la credencial (`nucleo.py:265-283,358-362`; resuelto el 21-10, hallazgo H3) | v5.0.0-16.3.1 | `test_h3_un_401_queda_en_el_registro_con_su_motivo` |
| F2 | E | una tool hace con la cuenta de servicio lo que el modelo pide para otro cliente | mitigar | la conversación y el comercio se comprueban en la puerta y la tool recibe la conversación ya validada; el modelo nunca la elige (`nucleo.py:149-153,384-391`) | v5.0.0-8.3.3 | `test_sin_conversacion_la_tool_de_carrito_no_corre` · X-17: conversación de otro comercio → `acceso_denegado`, 0 filas |
| F2 | I | una excepción de la tool enseña la traza o la fila al cliente | mitigar | se captura y sale `error_interno` con el tipo de la excepción, sin traza, también si lo que falla es la puerta y no la tool (`nucleo.py:342-345,395-398`) | v5.0.0-16.5.1 | `test_una_excepcion_no_ensena_la_traza` |
| F3 | T | la salida lleva contenido del comercio (descripciones del catálogo) que el modelo que consume puede tomar por instrucciones | mitigar | para el bot y Claude Code, la Rule of Two de la §4; a un agente de fuera no se le da token hasta servir `structuredContent` y `outputSchema` (README, «Cómo lo consume cada cliente») | LLM01:2025 | G6 «doble obediente» (vector catálogo) en el bot que lo adopte |
| F4 | I | el registro guarda el email o el teléfono del checkout | mitigar | solo los NOMBRES de los argumentos, nunca sus valores (`nucleo.py:357-359`); de la cabecera `X-Conversacion`, solo un id de cifras ASCII, y lo demás se anota como `invalida`; de la tool, solo un nombre que el servidor conoce, y de los argumentos, los que nombra el esquema (y cuántos más llegaron) (`nucleo.py:72,163-165,346-356`; resuelto el 21-10, hallazgo H5: antes se anotaba tal como llegaba, y un «²» pasaba `isdigit()`, `int()` reventaba y la llamada no dejaba línea) | v5.0.0-16.2.5 | `test_el_registro_no_guarda_valores` · `test_h5_de_la_conversacion_solo_se_registra_un_id` |
| F4 | I | el JSONL lo puede leer cualquier usuario de la máquina | mitigar | el fichero se crea con permisos `0o600` y se le fuerzan también si ya existía; si no se puede escribir, la respuesta no cambia y el fallo va al logger (`nucleo.py:195-196,224-229`; resuelto el 21-10, hallazgo H6) | v5.0.0-16.4.2 | `test_h6_el_registro_se_crea_con_permisos_0600` |
| F4 | R | la hora del registro no dice su zona: no se puede alinear con el log del proxy ni con otro servidor | mitigar | UTC con desfase explícito en ISO 8601 (`+00:00`) y milisegundos (`nucleo.py:191-192`; resuelto el 21-10, hallazgo H2) | v5.0.0-16.2.2 | `test_h2_la_hora_del_registro_es_utc_con_desfase` |
| F5 | I | el texto de las tools, con datos del cliente, sale al proveedor del modelo | mitigar | las tools devuelven el mínimo que el bot necesita; el proveedor, de una lista cerrada, con contrato de encargado (RGPD art. 28) y sin entrenar con los datos; si está fuera del EEE, la garantía de los arts. 44-46. **Lo declara el proyecto que adopte el kit** (hallazgo H7) | v5.0.0-15.3.1 | Priya, eje 5, sobre el contrato del proveedor · un test de los campos que devuelve cada tool |

## 3. Privacidad (LINDDUN GO)

| Carta | Frontera | Amenaza concreta | Defensa decidida | Base legal o ASVS |
|---|---|---|---|---|
| D4 DETECTABLE RECORDS | F1 | un «no es tuyo» distinto de «no existe» confirmaría que ese pedido existe en otro comercio | misma respuesta `acceso_denegado` para ajeno, inexistente o basura (`nucleo.py:391,394`); y el mismo 401 para un token desconocido, caducado o con demasiada vida | v5.0.0-8.2.2 · RGPD art. 5.1.f |
| DD5 OVEREXPOSURE OF PERSONAL DATA | F5 | los datos del cliente del pedido llegan al proveedor del LLM con cada turno | mínimo de campos en la salida de las tools; proveedor con contrato de encargado y sin entrenamiento (H7) | RGPD arts. 5.1.c, 28 y 44-46 · v5.0.0-15.3.1 |
| DD4 UNNECESSARY DATA RETENTION | F4 | el JSONL crece sin límite ni plazo: conversación, comercio y hora de cada llamada, para siempre | un fichero por día UTC (un reinicio el mismo día junta, no pisa) y borrado de los que pasan de `dias_registro`, solo con su nombre exacto y una fecha de verdad (30 por defecto; el plazo lo declara el proyecto que adopte el kit) (`nucleo.py:176-229`; resuelto el 21-10, hallazgo H4) | RGPD art. 5.1.e |
| L1 LINKED USER REQUESTS | F4 | el id de conversación enlaza en el registro todas las llamadas de un mismo cliente | es un dato **seudonimizado**, y sigue siendo personal (RGPD art. 4.5 y considerando 26): base en el interés legítimo de seguridad y diagnóstico, el plazo de `dias_registro` (H4) y el borrado de U5 | RGPD arts. 4.5, 5.1.e y 6.1.f |
| U5 INSUFFICIENT RECTIFICATION OR ERASURE | F4 | quien pide la supresión sigue en el registro con su id de conversación | borrar las líneas de una conversación a petición, o la excepción escrita; lo declara el proyecto que adopte el kit | RGPD art. 17 |
| U1 INSUFFICIENT TRANSPARENCY | F3 | el comprador no sabe que habla con un bot, quién responde de sus datos ni que la conversación pasa por un proveedor | aviso de IA y la información del art. 13 en el canal del bot (las revisan `nora-ai-act-auditor` y Priya); lo declara el proyecto | RGPD art. 13 · Reglamento (UE) 2024/1689 art. 50 |
| Nc1 NON-COMPLIANCE OF PROCESSING WITH APPLICABLE REGULATIONS | F2 | el kit trata datos de cada comercio sin que esté escrito quién es responsable y quién encargado | el comercio, responsable; el servidor, encargado: contrato del art. 28 y entrada en el registro del art. 30; lo declara el proyecto, el kit no lo trae | RGPD arts. 28 y 30 |

## 4. Agentes (Rule of Two)

| Agente (sesión) | [A] | [B] | [C] | Control si son las tres |
|---|---|---|---|---|
| bot del comercio por MCP (una conversación) | sí: texto del cliente y catálogo | sí: carrito, pedidos y datos del checkout | sí: añade al carrito y crea el pedido | el pago lo confirma la persona en la pasarela (el checkout solo devuelve el enlace); lo demás es reversible |
| Claude Code en desarrollo | sí: salidas de las tools | no: token de un comercio de pruebas y `--allowedTools mcp__comercio` (README) | sí: carrito y pedidos de prueba | — (dos de tres) |
| agente comprador de fuera | sí | sí | sí | no opera: sin token hasta que haya confirmación del comprador antes del checkout y salida estructurada |

## 5. Lo que se acepta, por escrito

- **El ritmo de llamadas** se transfiere al proxy: sin proxy con límite, no se publica. Los 401 quedan en el
  registro con su motivo (H3), que es de donde sale la alerta.
- **H1-H6 ya no se aceptan: están resueltos en el kit** (21-10), cada uno con su test, que falla con el núcleo de
  antes, y su sabotaje (`_archive/2026-10-20/medicion-3.42/kit/probar_kit_h1_h6.sh`: antes 13 pasan y fallan
  los 8 de H1-H6; ahora 21/21; 34/34 sabotajes cazados por su test, también lo que encontró el verificador del 21-10). Lo que queda del lado del proyecto: emitir
  y rotar los tokens (su gestor de secretos) y fijar `dias_registro`.
- **H7, U1, U5 y Nc1** son del proyecto que adopte el kit: el kit no puede decidirlos por él.

## 6. ¿Lo hicimos bien?

Lo escribió el agente de la sub-ola 2.25 leyendo el kit sin ejecutarlo; el 21-10 se resolvieron H1-H6 y cada
fila cita ya la línea del núcleo nuevo y su test. Lo comprueba `gate_amenazas.py --modelo`, que hoy lo da por bueno **menos la firma**: la firma es
de la persona que lo revisa, y un agente no firma su propio modelo. Lo tiene que leer y firmar el dueño
del kit; cuando un bot lo adopte, Sofía ataca la columna «Cómo se prueba» y Priya las cartas de la §3.
Una fila «pendiente» es una defensa decidida y todavía no hecha: el gate no distingue una de otra, y por
eso se escribe `**pendiente (Hx):**` delante de la defensa, con su hallazgo.
