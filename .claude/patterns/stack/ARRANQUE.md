# Arranque de un proyecto — qué se crea, en qué orden, y qué decisión trae puesta

> **Cuándo aplica:** el primer día de un proyecto nuevo del stack de casa. Responde a *"¿qué
> ficheros creo y qué va en cada uno?"*, que es la pregunta que los 40 documentos de
> `patterns/stack/` contestan por separado y ninguno junta.
>
> **NO aplica:** a un proyecto que ya existe — ahí manda `rules/refactor-progresivo.md`, que congela
> la deuda antes de exigir nada · ni sustituye a los patrones: esto es el índice y el orden; **el
> porqué de cada decisión está en el documento que se cita**, y ahí es donde hay que ir a discutirla.

> 📚 **Mientras creas cada fichero, `REFERENCIAS.md` te dice en qué código real está resuelto** —
> `evo-preven` para Django a escala, `bulletproof-react` para el frontend,
> `advanced_marketing_system` para un sistema completo con agente y panel de depuración.

---

## Backend · Django + DRF

### Versiones de arranque, y por qué esas

Lo que se escribe en el fichero de dependencias el primer día (MO-D3 y MO-D4, sub-ola 2.18; medidas en
PyPI y en la página oficial de Django el 2026-10-21). El frontend, en `frontend-stack.md`.

| Pieza | Rango | Licencia | Por qué |
|---|---|---|---|
| **Python** | 3.12 o 3.13 | PSF-2.0 | Django 5.2 pide Python ≥3.10 (PyPI) y la prueba del 21-10 corrió en la 3.14; 3.12 es lo mínimo que pide Django 6.x, así que el salto a la 6.2 LTS no obliga a cambiar también de Python |
| **Django** | `>=5.2.18,<5.3` — **5.2 LTS** | BSD-3-Clause | Decisión del Usuario del 18-10. Es la LTS vigente: soporte de seguridad hasta **abril de 2028**. Ojo con lo que eso quiere decir: su soporte principal terminó el 03-12-2025, así que ya solo recibe parches de seguridad y de pérdida de datos. La siguiente LTS es la **6.2, en abril de 2027** (soporte hasta abril de 2030); después Django pasa a una versión al año («Django 2028», en enero). El salto 5.2 → 6.2 se planifica como tarea propia, con sus tests |
| **DRF** | `>=3.18.3,<3.19` | BSD-3-Clause | La 3.18 exige Django ≥5.2 y la 3.18.2 trae tres avisos de seguridad (GHSA) que la 3.17 no tiene. **Cambio a tener en cuenta:** desde la 3.18.0 los errores de un serializer con `many=True` salen como diccionario, no como lista (la 3.18.1 añade un ajuste de compatibilidad); el sobre `{"errors": …}` de `backend-vistas.md` no cambia |
| **drf-spectacular** | `>=0.30.0,<0.31` | BSD-3-Clause | El contrato con el frontend (`frontend-contrato-con-el-backend.md`). 0.30.0 declara Django hasta la 6.0 y no pone techo a DRF: con 3.18.3 genera y valida (`spectacular --validate --fail-on-warn`) sin avisos, comprobado |
| **PostgreSQL** | 16 o 17, imagen con etiqueta exacta | `PostgreSQL` (tipo BSD) | `backend-modelos.md` · `backend-docker-env.md` |

Licencias de Django, DRF y drf-spectacular leídas en la API JSON de PyPI el 2026-10-21 (las de
Python y PostgreSQL no se midieron ese día: son las suyas de siempre, de tipo BSD): ninguna
obliga a nada al entregar o vender el backend, más allá del aviso de copyright (`rules/licenses.md`).

**API: DRF, no Django Ninja.** Ninja (1.7.1, MIT) es lo que se suele recomendar para una API JSON nueva
—tipos con Pydantic, OpenAPI sin otra pieza, `async`—, pero no hay ninguna fuente primaria de 2026 que
compare las dos, todos los proyectos de la casa usan DRF + drf-spectacular, y el patrón de contrato
entero (`frontend-contrato-con-el-backend.md`), las reglas `be-view-*` y `backend-serializers.md`
cuelgan de DRF. Cambiar a Ninja rompería esa continuidad sin una mejora demostrada; si un proyecto
tiene una razón de verdad (una API sin modelos de Django, mucho `async`), se decide con ADR
(`plan-gates.md` Gate D).

**Probado el 2026-10-21** (`_archive/2026-10-20/medicion-2.18/`): un backend con estas versiones y un
`OrderViewSet` pasa `check`, `migrate` en limpio, `makemigrations --check`, `spectacular --validate
--fail-on-warn` y las cuatro llamadas reales de `rules/verification.md` §Smoke (camino feliz 201,
inválido 400 con el sobre, sin auth 401, método incorrecto 405), y su `schema.yml` alimenta al
frontend de `frontend-stack.md`.

### El árbol de una app

Una app es **una cosa del negocio** (pedidos, clientes, catálogo), no una capa técnica. Si no sabes
ponerle un nombre del dominio, probablemente no es una app.

```
apps/<dominio>/
├── models/                  un fichero por modelo, no un models.py de 900 líneas
│   ├── __init__.py          reexporta: `from .pedido import Pedido`
│   └── pedido.py
├── choices.py               las opciones cerradas (TextChoices). Las usan modelo, serializer y front
├── serializers/             el CONTRATO con React. Cambiarlo rompe a alguien de fuera
├── views/                   ViewSets de DRF. Aquí entra lo de fuera: es la frontera donde se valida
├── services/                la lógica de negocio. Ni modelos ni HTTP: lo que hace el trabajo
├── tasks.py                 Celery. Lo que corre sin nadie mirando
├── signals.py               ⚠️ casi vacío a propósito — ver abajo
├── urls.py                  las rutas de esta app
├── admin.py
├── migrations/
└── tests/                   por capa: test_models, test_services, test_views
```

| Fichero | Qué va | Qué NO va | Patrón |
|---|---|---|---|
| `models/` | Campos, constraints, índices, `Meta`, propiedades derivadas | Lógica de negocio · efectos (enviar un correo desde `save()`) | `backend-modelos.md` · `backend-estructura-apps.md` |
| `choices.py` | `TextChoices`, una clase por conjunto | Constantes que no son opciones de un campo | `backend-modelos.md` §choices |
| `serializers/` | Validación de entrada, forma de salida | Consultas pesadas · lógica de negocio | `backend-serializers.md` |
| `views/` | Permisos, filtros, paginación, llamada al servicio | La lógica en sí — la vista **orquesta**, no calcula | `backend-vistas.md` · `backend-controllers.md` |
| `services/` | El trabajo. Funciones con argumentos explícitos | Recibir el `request` (eso lo ata a HTTP y no se puede llamar desde una task) | `backend-servicios.md` |
| `tasks.py` | Trabajo largo o que puede fallar y reintentarse | Lógica que no esté también en un servicio llamable | `backend-celery.md` |
| `signals.py` | **Casi nada** | Lógica de negocio: es control de flujo invisible | `backend-signals.md` |

> ⚠️ **`signals.py` es la trampa más cara del stack.** En el backend de referencia hay **109
> receivers**: guardar un objeto crea otros cuatro sin que nada lo indique en el sitio desde donde
> se llama. Un `signal` está bien para invalidar una caché o mandar algo a una cola; **no** para
> crear las filas relacionadas de un pedido. Eso va en un servicio, donde se ve.

### Y el detalle que cambia todo: el frontend es React

Es la decisión que decide la forma del backend entero:

| | Django clásico | **Aquí (React)** |
|---|---|---|
| La vista devuelve | HTML renderizado | **JSON** |
| Se valida en | `forms.py` | **el serializer** |
| Las opciones de un campo | El `<select>` las pinta la plantilla | Las **sirve un endpoint**; el front las pinta |
| Las URLs | `urls.py` + plantillas | `urls.py` de la API + **el router de React aparte** |
| El error | Página de error | **Código HTTP + cuerpo con la forma acordada** |

**Consecuencia práctica: `forms.py` casi no existe** y el contrato vive en los serializers. Cómo se
formatean los errores para que el front sepa qué pintar: `api-y-errores.md` y
`frontend-contrato-con-el-backend.md`.

### La infraestructura, y qué decide cada pieza

| Pieza | Para qué **aquí** | Decisión por defecto | Patrón |
|---|---|---|---|
| **PostgreSQL** | La base. Único motor | Sin Mongo. `JSONB` para lo semiestructurado | `backend-modelos.md` |
| **Redis** | Caché **y** broker de Celery | Bases distintas por uso (`/0` caché, `/1` broker): un `FLUSHDB` no se lleva las colas | `backend-cache-redis.md` |
| **Celery** | Trabajo largo, reintentable | `worker` + `beat`. Las tareas periódicas **en configuración, no en `celery.py`** | `backend-celery.md` |
| **RabbitMQ** | Solo si hay **varios consumidores** o el mensaje no se puede perder | **No por defecto**: si Redis basta, Redis | `backend-mensajeria-rabbitmq.md` |
| **Docker** | Todo, incluido desarrollo | Un servicio por pieza; secretos por entorno, nunca en el repo | `backend-docker-env.md` |

> **Redis o RabbitMQ, en una línea:** Redis es una cola simple y rapidísima que **puede perder un
> mensaje** si se cae en el momento justo. RabbitMQ garantiza la entrega y cuesta un servicio más de
> operar. Si lo que va por la cola es "regenera esta miniatura", Redis. Si es "cobra esto", la
> pregunta ya no es de infraestructura y va a `agente-hitl.md` y a `governance.md`.

### El orden del primer día

```
1. El modelo de datos y sus constraints        ← lo más caro de cambiar después
2. Los choices                                  (los necesita todo lo demás)
3. Serializers: el contrato con el front
4. Services: el trabajo de verdad
5. Views + urls: la frontera
6. Tasks, si hay algo largo
7. Tests por capa, desde el principio           ← sin esto ningún refactor es seguro
```

---

## Frontend · React + TypeScript + Vite

```
frontend/src/
├── pages/            una por ruta. Orquesta, no calcula
├── components/       reutilizables. Si dos páginas lo usan, vive aquí
├── hooks/            estado y lógica reutilizable
├── api/              el cliente. UN sitio que habla con el backend
├── stores/           estado global, y solo lo que de verdad es global
├── types/            los tipos del contrato con la API
└── styles/           tokens del design system
```

| Capa | Decisión por defecto | Patrón |
|---|---|---|
| Build | **Vite** (no Next ni CRA) | `frontend-stack.md` |
| Estilos | **Tailwind** + tokens del design system, sin CSS suelto | `estilos.md` · `frontend-design-system.md` |
| Estado del servidor | Cliente de API en un sitio, **nunca `fetch` suelto en un componente** | `frontend-contrato-con-el-backend.md` |
| Estado de UI | Local por defecto; global solo lo que lo necesita | `estado.md` |
| Formularios | Validación en el cliente **y** en el serializer. Las dos | `formularios.md` |
| Errores | Ninguna pantalla se queda en blanco: cargando, vacío y error | `frontend-a-prueba-de-errores.md` |
| Accesibilidad | Contraste y teclado desde el primer componente | `accesibilidad.md` |

**Una pantalla nueva sale de un molde de 10 ficheros**, no se escribe desde cero:
`frontend-nueva-pantalla.md`, y la skill `/nueva-pantalla` lo genera. Antes de escribirla, si la
forma no está decidida: `/disenar-pantalla`.

---

## Agente IA · LangGraph

### Antes de nada: ¿hace falta?

`agente-cuando-no.md`. Cuatro preguntas, y la que más veces sobra el agente: **si el camino es
fijo, es un script**. Dato de casa: elvion tiene 4 nodos de grafo y 505 `if` alrededor — el grafo es
el 0,3 % del código.

### El molde — y ya se puede copiar

**El molde es ejecutable desde la 3.43:** `templates/agente-conversacional/` (CB-26). Arranca con un
modelo falso, pasa sus tests y su golden mínimo, y ensambla los kits de la casa (memoria, guardas,
venta, runtime, trazas, evaluación) sin copiarlos. Para empezar un bot:
`python3 .claude/templates/agente-conversacional/scaffold.py <carpeta-del-bot> --apply`. Lo que sigue
es el árbol que deja; en el arquetipo, `apps/agents/` se llama `agent/`.

```
apps/agents/
├── graph.py          SOLO el cableado: nodos y aristas. Ni un `if` de negocio
├── nodes.py          el trabajo de cada nodo
├── routing.py        las decisiones: funciones PURAS, sin LLM y sin base de datos
├── schemas/state.py  el State: lo que se recuerda, en campos tipados; `messages` solo del turno
├── tools/            una tool por fichero, con su contrato de error
├── checkpointer.py   la persistencia, en un solo sitio
├── runtime.py        el thread_id y el config: UN solo constructor
├── traza.py          qué se registra de cada paso
└── evaluations/      el golden set y el gate
```

### Las decisiones que trae puestas

| Decisión | Por defecto | Cuándo cambia | Patrón |
|---|---|---|---|
| **Arquitectura** | **Workflow con un solo escritor** (escalón 0b) si el bot escribe en un sistema real; si solo conversa, un agente | Subir de escalón solo con una medición escrita | `agente-arquitecturas.md` §1 |
| **Dónde vive la memoria** | **Campos tipados del estado; `messages` solo del turno**, sin reducer (CB-D3, A) | Conversación abierta: además un `history` con `add_messages`, recortado antes del modelo (C). Nunca `operator.add` | `agente-memoria.md` §1b |
| **Checkpointer** | `PostgresSaver` oficial con pool propio | `MemorySaver` solo en tests, y **declarado en el log** | `agente-memoria.md` |
| **Poda** | En el `put()`, con dos topes | — | `agente-memoria.md` §3 |
| **Quién decide** | Entender→modelo · ejecutar→**código** · redactar→modelo | Nunca al revés | `agente-determinismo.md` |
| **Temperatura** | `0` donde se decide; libre donde se redacta | — | `agente-determinismo.md` §3 |
| **Tools** | Error **devuelto**, no lanzado. `args_schema` siempre | — | `agente-tools.md` |
| **Acciones sin vuelta atrás** | Puerta de aprobación en el grafo (`interrupt()`) | Nunca un "NUNCA" en el prompt | `agente-hitl.md` |
| **RAG** | Híbrido denso + BM25 con RRF, filtro por metadatos antes de ordenar | — | `agente-rag.md` |
| **Reranking** | Cross-encoder sobre el top-K, **midiendo antes y después** | **Nunca un LLM de chat**: −25 puntos medidos | `agente-rag.md` |
| **Trazas** | Langfuse en producción · LangSmith en desarrollo, y `AGENT_TRACING` dice cuál | — | `agente-observabilidad.md` §4 |
| **Evaluación** | Golden set **antes** de construir, con su gate | — | `disenar-conversacion` · `eval-estadistica` |

### El orden

```
1. ¿Hace falta un agente?                      agente-cuando-no.md
2. Cómo habla y qué NO puede prometer          /disenar-conversacion  ← antes del código
3. El golden set                               (sí: antes de construir)
4. State + checkpointer                        agente-memoria.md
5. El grafo: ReAct, y nodos con nombre         agente-arquitecturas.md
6. Tools con su contrato de error              agente-tools.md
7. Retrieval, si busca algo                    agente-rag.md
8. Puertas donde no hay vuelta atrás           agente-hitl.md
9. Trazas ANTES de la primera incidencia       agente-observabilidad.md
```

> **El 2 y el 3 van antes que el código, y es lo que más se salta.** Un golden set escrito después
> de construir se escribe para que pase lo que ya hace el bot.

---

## Lo que este documento NO es

**No es el porqué de nada.** Cada casilla apunta a su patrón, y ahí está la medición, el
contraejemplo y los límites. Si una decisión de aquí te parece mal, la discusión está en el
documento citado — no en esta tabla.

**No sustituye al arranque real.** `project-setup` monta el `.claude/`; `codebase-onboarding`
escribe el `CLAUDE.md`. Esto es lo que se construye **dentro**.

## Límites honestos

- **Las decisiones de agente están medidas sobre dos repos nuestros y cuatro ajenos**; las reglas
  `ag-*` siguen todas en `sombra` y no bloquean nada (`patterns/README.md` §GAP-1).
- **`agente-arquitecturas.md` describe supervisor y swarm leyendo el código de LangChain**, no por
  experiencia propia: ninguno de nuestros agentes los usa hoy.
- **El agente tiene molde ejecutable; el backend y el frontend, no.** `templates/agente-conversacional/`
  (3.43) corre con un modelo falso y sin Postgres: sus adaptadores a `catalog-search`, `PostgresSaver` y
  `PostgresStore` están sin medir ahí. Para Django y React, este documento sigue siendo lo más
  parecido a un molde que hay (el ejemplo de solo configuración se archivó el 2026-10-19,
  `_archive/2026-10-19/README.md`).

---

_v1.0 · 2026-08-26. Nace de una petición directa: los 40 documentos de `patterns/stack/` contestan
cada uno su parte y ninguno decía **qué se crea el primer día y en qué orden**._
_v1.1 · 2026-11-01 (sub-ola 3.43, CB-26 y CB-D3): el molde del agente apunta al arquetipo ejecutable y
la memoria pasa a campos tipados con `messages` solo del turno._
