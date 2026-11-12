# `.claude/patterns/stack/` — el patrón de casa sobre el stack canónico

> **Qué es:** el estilo con el que se escribe código aquí cuando **todavía no hay código del que
> deducirlo**. Es la rama "proyecto NUEVO" de US-7. La rama "proyecto EXISTENTE" la cubren
> `catalog.yaml` (dominancia medida) y el manifiesto generado del propio repo (QA-2).
>
> 📚 **¿Y dónde está hecho bien?** → **`REFERENCIAS.md`**: los 9 cuerpos de código real que
> miramos para decidir esto (Django, React y LangGraph), con qué enseña cada uno y qué patrón sale
> de dónde. Un patrón sin precedente citable es una preferencia; ese documento dice dónde buscarlo.
>
> 🧱 **¿Qué ficheros creo y en qué orden?** → **`ARRANQUE.md`**.
>
> **Stack canónico:** Django (5.2 LTS en un proyecto nuevo: `ARRANQUE.md` §Versiones de arranque) · PostgreSQL · Celery · Redis · RabbitMQ · Docker · React, **con DRF
> o con plantillas renderizadas en el servidor** (los dos arquetipos son de primera clase — ver
> "los cuatro defaults" más abajo). MongoDB queda fuera a propósito: los campos JSON de PostgreSQL
> ya cubren ese caso.
>
> ⚠️ **Fichero COMPARTIDO por las dos mitades.** Backend y frontend se escribieron en paralelo y
> esta página se sobrescribió al menos una vez en el proceso. **Edítala en destino; no la incluyas
> en un `cp -r` desde staging** o pisarás la mitad del otro. La sección de backend está descrita de
> primera mano; la de frontend se reconstruyó desde sus propios documentos y catálogo, así que su
> autor debería revisarla.

## Por qué cada regla trae su comprobación

El objetivo de este set no es que el código sea bonito: es que un agente pueda desarrollar durante
horas sin nadie delante y que por la mañana el resultado sea **auditable**. Una guía de estilo que
solo se verifica leyéndola no sobrevive a esa noche — nadie la lee a las 4 de la mañana y nadie
puede comprobar después si se siguió.

De ahí la condición dura del set: **una regla entra con su comprobación ejecutable, o no entra.**
Las que no supieron traer una están documentadas como descartadas, no disfrazadas de regla.

Corolario que se aplicó en EVO-4 y que conviene tener a mano: cuando una regla **deja de ser
universal**, no se borra — se **reclasifica** (default de proyecto nuevo · aviso · sombra) y se
dice cómo se comprueba en cada caso. Degradar sin dejar comprobación es perder la regla.

## Los cuatro defaults que NO son reglas (EVO-4)

Carpeta `apps/`, `settings/` partido, el nombre `services.py` y backend = DRF: **son el default de un
proyecto NUEVO, no un incumplimiento en uno existente**. Por qué (medido sobre un backend Django real
de 740 ficheros) y cómo se comprueba cada uno: `REGLAS.md` §Los cuatro defaults.

## Índice

El detalle de cada mitad —qué fixture prueba qué, la medición con sus denominadores, el contrato del
error 400 y por qué ninguna regla de agentes bloquea— está en **`REGLAS.md`**, con el mismo título.

### Mitad BACKEND — 55 reglas · `pattern_check_backend.py`

| Capa | Documento | Reglas | Por qué importa |
|---|---|---|---|
| 0 · Estructura | [`backend-estructura-apps.md`](backend-estructura-apps.md) | 5 | **La plantilla que no se renderiza jamás**, el enredo entre apps y el script que nadie sabe quién lanza |
| 4 · Servicios | [`backend-servicios.md`](backend-servicios.md) | 2 | Dónde vive la lógica. El error más caro del backend |
| 5 · Celery | [`backend-celery.md`](backend-celery.md) | 6 | Sus fallos son silenciosos y diferidos · **el `timeout=` que faltaba** |
| 1 · Modelos | [`backend-modelos.md`](backend-modelos.md) | 10 | Lo único que no se arregla con un deploy · **de qué hereda un modelo** |
| 2 · Serializers | [`backend-serializers.md`](backend-serializers.md) | 3 | El contrato de la API y su superficie de fuga — **solo arquetipo DRF** |
| 2b · Formularios | [`backend-formularios-django.md`](backend-formularios-django.md) | 4 | **Arquetipo server-rendered:** la única puerta con validación, y quien pone el dueño de la fila |
| 2c · Señales | [`backend-signals.md`](backend-signals.md) | 2 | Un receiver corre dentro de la transacción de otro: el efecto que sale antes del COMMIT |
| 2d · Validación | [`backend-validacion.md`](backend-validacion.md) | 3 | **Qué debe un escritor que NO es el formulario** — el hueco conceptual del estilo |
| 3 · Vistas | [`backend-vistas.md`](backend-vistas.md) | 6 | El filtrado por dueño **en un punto, no en N** · contrato del error 400 con el frontend |
| 6 · Caché | [`backend-cache-redis.md`](backend-cache-redis.md) | 4 | El bug no es "no se guardó", es "se sirvió lo viejo" |
| 7 · RabbitMQ | [`backend-mensajeria-rabbitmq.md`](backend-mensajeria-rabbitmq.md) | 1 | El único fallo que empeora solo con el tiempo |
| 8 · Docker/env | [`backend-docker-env.md`](backend-docker-env.md) | 4 | Que otro pueda levantar exactamente esto |
| 9 · Tests | [`backend-tests.md`](backend-tests.md) | 3 | **Sostiene a los demás:** sin tests, ninguna otra regla se puede verificar |
| 10 · Observabilidad | [`backend-observabilidad.md`](backend-observabilidad.md) | 2 | No hay autonomía sin señal de vuelta. Es lo primero, no lo último |
| — · CRUD heredado | [`backend-controllers.md`](backend-controllers.md) | 0 (3 en sombra) | **Descriptivo, no prescriptivo:** el framework CRUD propio de `evo-preven` (Settings + Controller). Para leer ese repo, NO para proyectos nuevos |

```bash
python3 .claude/patterns/stack/pattern_check_backend.py              # ficheros cambiados
python3 .claude/patterns/stack/pattern_check_backend.py --all        # inventario del repo
python3 .claude/patterns/stack/pattern_check_backend.py --list       # las 55 reglas y su estado
python3 .claude/patterns/stack/pattern_check_backend.py --json       # para otro agente
python3 .claude/patterns/stack/pattern_check_backend.py --self-test  # FPR + sensibilidad
```

### Mitad FRONTEND — 38 reglas · `pattern_check_frontend.py`

**Empieza por [`frontend-stack.md`](frontend-stack.md)**; los VALORES de diseño (paleta, escala,
tipografía) no están aquí y no van a estar: los declara cada proyecto en su `.docs/core/design-system.md`
(decisión del Usuario, EST-2).

| Capa | Documento | Reglas | Qué fija |
|---|---|---|---|
| **Stack** | [`frontend-stack.md`](frontend-stack.md) | 2 | **Qué se instala y por qué esa y no la alternativa** |
| **Diseño** | [`frontend-design-system.md`](frontend-design-system.md) | 1 | **El procedimiento del sistema de diseño (no sus valores)** |
| API y errores | [`api-y-errores.md`](api-y-errores.md) | 7 | El cliente único, el timeout y los tres estados |
| Tests | [`tests.md`](tests.md) | 5 | Los niveles y dónde está la frontera de cada uno |
| Componentes | [`componentes.md`](componentes.md) | 4 | Un componente por fichero, props tipadas, sin color literal |
| Estado | [`estado.md`](estado.md) | 4 | De quién es el dato antes de decidir dónde vive |
| Estilos | [`estilos.md`](estilos.md) | 4 | Tailwind sobre tokens, `cn()` e iconos que no inflan el paquete |
| Formularios | [`formularios.md`](formularios.md) | 3 | Un esquema zod, submit bloqueado, errores del backend en su campo |
| Rutas | [`rutas.md`](rutas.md) | 3 | Un módulo de rutas, `ErrorBoundary` y `<Link>` |
| Accesibilidad | [`accesibilidad.md`](accesibilidad.md) | 3 | Lo estructural, que es lo que se comprueba escribiendo |
| Saneado | [`saneado.md`](saneado.md) | 2 | Las dos puertas por las que entra un XSS en React |

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py                      # ficheros cambiados
python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src   # inventario
python3 .claude/patterns/stack/pattern_check_frontend.py --only componentes
python3 .claude/patterns/stack/pattern_check_frontend.py --list               # las 38 reglas
python3 .claude/patterns/stack/pattern_check_frontend.py --self-test          # FPR + sensibilidad
```

### Mitad AGENTES — 25 documentos, 14 reglas · `pattern_check_agente.py` (ninguna bloquea)

| Documento | Qué fija | Reglas comprobables |
|---|---|---|
| [`agente-observabilidad.md`](agente-observabilidad.md) | Qué se registra y qué se puede correlacionar después; la receta Langfuse v4, la fila por turno y el streaming v1/v2 (kit: `templates/bot-trace/`) | 7 (`ag-traza-incompleta`, en aviso desde 3.27) |
| [`agente-tools.md`](agente-tools.md) | El contrato de la tool: descripción, entrada validada, error como dato | 3 |
| [`agente-hitl.md`](agente-hitl.md) | Qué acciones no tienen vuelta y por qué paran a esperar confirmación | 1 |
| [`agente-memoria.md`](agente-memoria.md) | Qué se guarda entre turnos y qué se poda | 0 — se verifica leyendo |
| [`agente-pii.md`](agente-pii.md) | Las dos máscaras de datos personales: antes del LLM y antes de trazar (código: `templates/bot-data/`) | 0 en el checker — lo comprueban las 42 pruebas de `bot-data` |
| [`agente-evaluator-optimizer.md`](agente-evaluator-optimizer.md) | Cuándo un segundo paso revisa al primero | 0 — deliberado (§7 del propio doc) |
| [`agente-cuando-no.md`](agente-cuando-no.md) | Cuándo **no** hay que montar un agente | 0 — es juicio, y por eso no entra en `catalog.yaml` |
| [`agente-determinismo.md`](agente-determinismo.md) | Qué decide el modelo y qué decide el código | 0 — es juicio sobre el dominio (§Límites del propio doc) |
| [`agente-arquitecturas.md`](agente-arquitecturas.md) | La escalera de casa (un agente → workflow para lo que escribe → handoffs → subagentes → swarm → A2A), la taxonomía de 2026 y LangGraph siempre | 0 — es juicio |
| [`agente-rag.md`](agente-rag.md) | Cómo se recupera del catálogo, y por qué el reranking se mide | 0 — es juicio |
| [`agente-mcp-comercio.md`](agente-mcp-comercio.md) | Cómo se sirven por MCP las tools de comercio del bot sin reescribirlas (kit: `templates/mcp-comercio/`) | 0 en el checker — lo comprueban los 21 tests del kit |
| [`agente-contrato-pruebas.md`](agente-contrato-pruebas.md) | El endpoint de prueba común `/api/testing/chat/` (solo dev y staging) y su `trace_id` fijado antes del turno (kit: `templates/bot-testing/`) | 0 en el checker — lo comprueba `testing_contract.py --url` |
| [`agente-modelo-y-coste.md`](agente-modelo-y-coste.md) | Qué modelo, cuánto cuesta, la caché, el routing y qué parámetros rompen al cambiar de modelo | 3 (`ag-temperature-modelo-nuevo`, `ag-reasoning-minimal`, `ag-modelo-retirado`) — declaradas |
| [`agente-juez-llm.md`](agente-juez-llm.md) | Evaluar con un LLM: el juez interpreta, el código pone la nota | 0 — lo prueba el contrato de punta a punta (§4 del propio doc) |
| [`catalogo-modelo.md`](catalogo-modelo.md) | El modelo de catálogo: precio fuera del producto, variantes, kits, vigencia, taxonomía y relaciones con fuente y estado | 0 en el checker — lo mide `scripts/catalog_readiness.py` sobre el export (`smoke/catalog/run.sh`) |
| [`agente-catalogo-y-venta.md`](agente-catalogo-y-venta.md) | Qué mecanismo según la pregunta, sustituto ≠ complemento ≠ mejora, momentos de venta en código y el árbitro con abstención | 0 — es juicio |
| [`agente-guardarrailes.md`](agente-guardarrailes.md) | Nunca precio inventado en 4 capas, gate de oferta, la garantía en el wrapper de la tool y un solo escritor (kit: `templates/bot-guardrails/`) | 0 en el checker — lo comprueban las 45 pruebas del kit y el ataque de Darío |
| [`agente-aprendizaje.md`](agente-aprendizaje.md) | El bucle de aprendizaje del bot: señales como scores, triaje humano, dataset con reserva por hash, juez calibrado, prompt optimizado fuera de línea y canary (kit: `templates/bot-learning/`) | 0 en el checker — lo comprueban `learning_check.py` (sombra) y las 29 pruebas del kit |
| [`agente-traza-comunicaciones.md`](agente-traza-comunicaciones.md) | Qué se graba de la BBDD, el HTTP y el RAG de cada turno (sin valores), el explorador por bloques y la traza esperada por ruta (kit: `templates/bot-trace/`) | 0 en el checker — lo comprueban las 20 pruebas del kit |
| [`agente-robustez.md`](agente-robustez.md) | La ráfaga de mensajes en un hilo, desplegar con conversaciones a medias y los reintentos y timeouts de LangGraph 1.2 (kit: `templates/bot-runtime/`) | 0 en el checker — lo comprueban las 34 pruebas del kit y `deploy_compat.py check` |
| [`agente-sin-framework.md`](agente-sin-framework.md) | El mínimo de una llamada a un LLM sin framework: registro siempre, salida validada al ejecutar, memoria explícita, modelo y prompt en el repo (kit: `templates/llm-run/`) | 0 en el checker — lo comprueban las 7 pruebas del kit |
| [`agente-memoria.md`](agente-memoria.md) §3b, §6, §7 (v2, 3.29) | Recorte, borrado y retención separados; thinking e historial; memoria larga en la Store con espacio por comercio y usuario, escrituras validadas y caducidad; si cae la memoria (kit: `templates/bot-memory/`) | 2 (`ag-fallback-mudo`, `ag-content-cero`) — declaradas · y las 52 pruebas del kit |
| [`agente-conocimiento-progresivo.md`](agente-conocimiento-progresivo.md) | «No lo sé, lo pregunto»: hueco con una pregunta abierta por duda, suscriptores, fan-out al contestar el encargado y dato verificado con caducidad por predicado | 0 — sin kit; el código de referencia es el del demo de autopartes |
| [`agente-regresion-conversacional.md`](agente-regresion-conversacional.md) (3.39) | El caso multi-turno con efecto contado en la BD, trayectoria de tools, estado final y `capability`/`regression`; CI con modelo falso y nocturno con k ≥ 5; Langfuse como banco (experiments, McNemar entre runs, `environment=test`, 👍/👎 a su traza) (kit: `templates/bot-evals/`) | 0 en el checker — lo comprueban las pruebas y el `--self-test` del kit |
| [`agente-tests-grafo.md`](agente-tests-grafo.md) (3.39) | Los cuatro tipos de test del grafo sin red: enrutado, nodo, contrato de tools y un tramo (`update_state(as_node)` + `interrupt_after`), con modelo falso que llama tools (kit: `templates/bot-evals/`) | 0 en el checker — `graph_tests_check.py` en sombra y los 8 tests del ejemplo |
| [`langfuse-autoalojado.md`](langfuse-autoalojado.md) (3.28) | Un Langfuse por servidor y un proyecto por producto; techo de memoria, telemetría, organización por cliente, purga; las lecturas de v4 por API v2/v3 y cómo lee Claude las trazas (lector: `templates/bot-trace/trace_query.py`) | 0 en el checker — lo comprueban las 9 pruebas de `test_trace_query.py` |

```bash
python3 .claude/patterns/stack/pattern_check_agente.py <repo>            # legible
python3 .claude/patterns/stack/pattern_check_agente.py <repo> --json     # para otro agente
python3 .claude/patterns/stack/pattern_check_agente.py --self-test       # 0 falsos positivos
```

### Campañas — 1 documento · lo comprueban las 32 pruebas de `templates/campanas/level0.py`

| Documento | Qué fija | Reglas comprobables |
|---|---|---|
| [`campaigns.md`](campaigns.md) | Nivel 0 de campañas: consentimiento por canal y finalidad, lista de exclusión, identidad estable, exposición con control por hash para los dos brazos, la puerta de salida como queryset, conversiones reales y lo mostrado con su probabilidad; escalera N0-N5 (sub-ola 3.51) | 0 en el checker — lo comprueban el kit y `scripts/gate_campana.py` |

### Analítica de comercio — 1 documento · lo comprueban `scripts/gate_kpis.py` y `scripts/domain_lint.py`

| Documento | Qué fija | Reglas comprobables |
|---|---|---|
| [`analytics-commerce.md`](analytics-commerce.md) | El dato de un comercio desde el día uno: eventos GA4 + chat idempotentes y con `is_synthetic`, `fact_order_line` y `fact_stock_daily` de grano atómico, agregados como caché, el dato en la base de cada comercio con agregados anónimos aparte, jobs con tenant y latido, panel de 5 tarjetas con «sin datos» que solo enseña lo medido (sub-ola 3.54) | 0 en el checker — `gate_kpis.py` K1-K5 sobre `analytics/` y `campaigns/` (autoprueba 16/16) |

### El límite con lo de fuera y el registro de accesos — 5 documentos (sub-ola 3.21; el quinto, 3.68) · fuera de `pattern_check_*`

| Documento | Qué fija | Lo comprueba |
|---|---|---|
| [`backend-integrations.md`](backend-integrations.md) | Protocol + real + doble detrás de una factoría que decide, con candado de entorno y guarda de escritura | `integration_check.py` IC1-IC3 (`--self-test`) |
| [`backend-channel-adapter.md`](backend-channel-adapter.md) | El motor habla `InboundMessage`/`AgentResult`; cada canal traduce en la puerta; webhook que responde ya y paridad entre canales | `integration_check.py` CA1 con `--engine` |
| [`frontend-embeddable-widget.md`](frontend-embeddable-widget.md) | Un IIFE con su Shadow DOM, sin más credencial que el `public_token` y con DOMPurify | `skills/widget-embed-test/widget_check.py` W1-W5 (`--autoprueba`) |
| [`backend-access-audit.md`](backend-access-audit.md) | Quién leyó qué de quién: la ficha mínima, solo INSERT, cadena por día y ancla fuera (kit: `templates/access-audit/`) | `smoke/harvest/access_audit.py` contra un PostgreSQL desechable |
| [`chat-ui-comercio.md`](chat-ui-comercio.md) | La interfaz de cada momento de venta en el widget y en WhatsApp (sugerencias, carrusel 3-8, tarjeta ≤2 acciones, carrito, checkout nativo, persona), el JSON propio que la decide (UX-D7) y el chat proactivo con consentimiento (UX-D10) (sub-ola 3.68) | `skills/probar-widget/probar_widget.py` CW1-CW11 (`--autoprueba`, 11 sabotajes) |

### El dueño pregunta y la web mide — 3 documentos (sub-ola 3.55) · fuera de `pattern_check_*`

| Documento | Qué fija | Lo comprueba |
|---|---|---|
| [`agente-metricas-dueno.md`](agente-metricas-dueno.md) | El chatbot del dueño: tool de métrica cerrada sobre `fichas-kpi`, sin SQL libre, tenant de la sesión, el modelo no ve la cifra, «no se mide» fuera del catálogo (kit: `templates/owner-metrics/`) | las 32 pruebas del kit, el golden de 50 preguntas (`run_golden.py`) y `sabotage_check.py` 31/31 |
| [`conocimiento-con-evidencia.md`](conocimiento-con-evidencia.md) | Lo que el bot aprende del comercio como hecho con fuente, ámbito, vigencia y sustitución; una contradicción no sobrescribe (cosechado de evolution) | 0 — declarado, leído de un proyecto; sin kit |
| [`web-measurement.md`](web-measurement.md) | La web que lleva al chat: nombres de GA4 y del backend, consentimiento previo, sin datos personales, `chat_opened` con la visita (kit: `templates/web-events/`) | `web_events_check.py` W1-W5 (`--self-test`) y `test_track.js` |

### Lo demás, en `REGLAS.md`

- **Qué NO copiar de la referencia — la lista negra (REF-8)** y **Quitar Mongo (REF-9)**
- **Reglas que se propusieron y se cayeron al verificarlas (EVO-15)** — para no volver a proponerlas
- **Declarado, no medido** — qué significa adoptar una regla que solo se ha medido en un repo
- **Cómo se nombran los patrones de agente IA** — el vocabulario de Anthropic (PAT-5)

## Cómo encaja con el resto

```
pattern_check_{backend,frontend,agente}.py ─candidatos─▶  rita-pattern-keeper  ──▶  informe (sombra)
        (determinista, 0 tokens)                      (juzga, nunca busca — R-1)
              │
              └─▶ activo = exit 1 · debil = aviso · sombra = silencio
                  excepción: `pattern-exempt: <id> — razón` (línea, anterior o cabecera del fichero)
```

- **Cablearlo al hook** (`.claude/hooks/pattern-check.sh`) exige aprobación —`governance.md` §2—,
  así que de momento se ejecuta a mano o desde `/pattern-gate`. La línea a añadir sería
  `python3 .claude/patterns/stack/pattern_check_backend.py || FAIL=1`.
- **El de agentes no se cablea todavía, y no es por falta de aprobación**: sus 10 reglas están
  en `sombra` porque solo se han medido en dos repos nuestros (§Mitad AGENTES). Cablear un
  comprobador con n=2 sería convertir en gate lo que hoy es una hipótesis.
- **Lo cosmético no está aquí**: indentación, comillas, orden de imports y longitud de línea los
  cubren Ruff y Prettier. Repetirlos sería ruido (`rules/code-style.md`).
- **Lo semántico tampoco**: si una función que ya está en `services.py` contiene *la* regla
  correcta es criterio, y es el trabajo de Rita con los precedentes de estos documentos.

## Mantenimiento

El límite honesto que reconoce US-7: **este patrón envejece cuando el stack evoluciona**. Django
5.1 **deprecó** `CheckConstraint(check=)` —que fue correcto durante cinco versiones— y la doc lo
retira en 6.0; la próxima versión se llevará otra cosa. Se revisa al cerrar cada proyecto nuevo, y
las reglas con un `verificado:` en el YAML llevan la fecha y la fuente contra la que se comprobaron.

> **Y el patrón también envejece hacia dentro.** Este mismo párrafo decía hasta hoy que Django 5.1
> *"eliminó"* ese argumento, y era falso (EVO-10): la lista de *features removed in 5.1* no lo
> incluye. Un dato incorrecto en el patrón es peor que no tener patrón, porque se propaga con
> autoridad — un agente lo repite en una revisión y alguien pierde media mañana persiguiendo un
> problema que no existe. Cuando una regla cite una versión concreta, **se verifica contra la doc
> antes de escribirla**, no de memoria.

## Related

- `.claude/patterns/README.md` (el canon medido) · `catalog.yaml` · `ownership.yaml` (canon declarado)
- `rita-pattern-keeper` · skill `pattern-gate` · skill `practices-manifesto` (rama proyecto existente)
- `rules/code-style.md` (estilo cosmético) · `rules/security.md` · `rules/governance.md`
