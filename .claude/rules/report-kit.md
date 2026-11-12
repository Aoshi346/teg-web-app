---
paths:
  - ".docs/plans/*/report.json"
  - ".docs/plans/*/dashboard.md"
  - ".docs/plans/*/*.html"
  - ".docs/plans/*/sources/**"
  - ".docs/core/*.html"
  - ".claude/templates/report_kit/**"
---
# Report-kit — el "informe total" multi-página con decisiones persistentes

> **Cuándo aplicar:** siempre que se entregue un **informe de proyecto, plan o incidencia** en HTML.
> Define el sistema ÚNICO de plantillas (`.claude/templates/report_kit/`), su schema de datos, sus
> perfiles y sus reglas. Sustituyó a `speckit_dashboard/` (legacy, archivado el 2026-10-19 en
> `_archive/2026-10-19/templates/` con los dashboards «lite» de `templates/html/`, LI-12) y
> generaliza el informe de `feedback_audit/`, que sigue existiendo pero NO se usa para informes nuevos.
>
> **NO aplicar:** respuestas conversacionales, una página suelta sin decisiones (usa
> `templates/html/status-report.html`), o markdown puro (default para lo trivial). **Qué informe
> usar en cada caso** y cómo se entrega (127.0.0.1 + túnel, nunca Artifact) vive en
> `rules/output-choice.md`; esta rule es el manual técnico del kit.
>
> **El manual largo** — el porqué, la medición y la historia de cada regla, las 4 vistas del
> dashboard, la sintaxis de `dashboard.md` y los tres grupos de campos — está en
> **`templates/report_kit/MANUAL.md`** (era el cuerpo de esta rule hasta la sub-ola 2.15, MO-78; los
> números de regla son los mismos). Aquí, lo que hay que cumplir. Si dicen distinto, manda esta rule.
>
> **Relacionado:** `output-choice.md` (qué salida y qué informe), `html-output.md` (el HTML suelto), `plan-docs-structure.md` (dónde vive
> el set), `verdict-contract.md` (el campo verdict), `motores-de-diseno.md` Parte F (la pestaña Diseño), skill
> `code-graph`.

---

## El principio que ordena todo lo demás

> **Un entregable que no aparece en el informe NO está entregado.**

Si el wireframe vive en una carpeta suelta, el mensaje al cliente en otra y las evidencias en una
tercera, el informe deja de ser el mapa del plan. Las pestañas **Entregables** y **Diseño** (reglas 9
y 9c) recogen por convención de carpetas todo lo que no tiene pestaña propia.

## Todo informe empieza por «Lo que pediste y dónde está» (MO-26, sub-ola 2.15)

Petición del Usuario recogida en dos proyectos (musa #52, evolution 17-10): el Usuario preguntó
*«¿está todo lo que te he dicho en el informe?»* y no estaba; y le llegaban enlaces que no abrían.

1. **La primera sección del Resumen (`index.html`) es «Lo que pediste y dónde está»**, y sale de
   **`report.json` → `meta.pedido`**: una lista en el orden de **la prioridad del Usuario** —no la de
   lo más fácil de medir—, cada petición con el sitio del informe que la responde:
   ```json
   "pedido": [{"que": "Que el informe recoja Jev y los modelos", "donde": "dashboard.html#MO-26",
               "estado": "hecho", "id": "T-052"}]
   ```
   `estado`: `hecho|en curso|falta` (sin él: `hecho` si hay `donde`, `falta` si no). **Una petición
   sin `donde` sale en rojo: es que falta.** Sin `meta.pedido` la sección no desaparece: dice que no
   está declarado y cómo se declara. Las peticiones salen de `pending-tasks.md` (lo escribe el hook
   `capture-task.sh`); `meta` escrita a mano no la pisa `tasks_to_items.py`.
2. **El enlace que se da es `http://localhost:<puerto>/<ruta>`**, servido en `127.0.0.1`, y **se
   comprueba antes de darlo**:
   ```bash
   python3 .claude/templates/report_kit/enlace.py <puerto> index.html dashboard.html
   # ✓ 200 http://localhost:8830/index.html … y el túnel SSH. Sale 1 si alguno no da 200 (ese no se
   # da) y 2 si el puerto escucha en 0.0.0.0 (eso no es localhost: es el directorio publicado).
   ```
   Usa `curl` (lo que el Usuario puede repetir). Un informe en markdown o en otra plantilla cumple
   lo mismo a mano: primera sección con ese título, y el enlace comprobado.

## Qué es

Un **set multi-página** (cada "pestaña" es un `.html` autocontenido con la misma topnav) generado
desde **un único `report.json`** (schema: `templates/report_kit/item.schema.json`). Las decisiones
se toman EN el documento y persisten: localStorage en modo estático, disco (`server.py`) en modo
backend, export JSON/MD siempre.

```
report.json  ──build.py──▶  index.html      resumen: «lo que pediste» + KPIs + tablas + mapa SVG
(+ graph-dataset.json)      structure.html  estructura del código (contrato /code-graph)
(+ sources/*.md)            dashboard.html  tareas: 4 vistas (lista · kanban · gantt · mapa mental)
                            diseno.html     referencias · marca · direcciones · wireframes · bocetos · mockups
                            entregables.html  mensajes · adjuntos · todo lo que no tiene otra pestaña
                            results.html    verdicts con doble evidencia 🔎/👁 + imágenes base64
                            pruebas.html    manual de prueba MANUAL + qué verificó ya el agente
                            fuentes.html    los informes de investigación detrás de los items (si hay sources/)
                            otto.html       sección fija del copiloto (sugerencias + permisos)
```

**Perfiles** (`nav.json#profiles`): `proyecto` (el set entero), `diseño` (sin Arquitectura, Datos,
Flujos ni Esquemas), `incidencia` (qué pasó y cómo se cerró) y **`minimo`** (2.15): Resumen,
Dashboard, Resultados, Pruebas, Entregables, Fuentes y Otto — para un plan pequeño o de un día, donde
las 35 pestañas de `proyecto` son una pared. **`issue`** (3.09, AN-6): `minimo` + «Informe del issue»
(`informe.html`, ruta fija; `gen_informe.py` lo pinta desde `informe.json` con las secciones 0-9, y
7-8 son los apartados de Pilar y Roberto que exige `gate_impacto.py`). Sustituye a los
`build_informe.py` a mano por issue.

## Cómo se escribe un item — los 4 bloques (obligatorio)

El `desc` de todo item lleva estos bloques, en este orden y con estos rótulos (el dashboard los
detecta y los separa):

```
📍 Cómo está ahora — qué hay hoy y qué duele. Con el fichero o el dato concreto.
🎯 Qué queremos conseguir — el resultado observable, no la tarea.
🔧 Cómo se haría — el mecanismo: qué se crea o se toca, con qué herramienta.
🧭 Por qué así y no de otra manera — la alternativa obvia y por qué pierde. Límites honestos.
⚠️ AVISO — (opcional) lo que cuesta, lo que puede salir mal, o lo que no cubre.
```

**Para alguien que no conoce la jerga**: cada término explicado la primera vez, un ejemplo concreto,
el coste además del beneficio, y el porqué como comparación (tabla de ejemplos: MANUAL §4 bloques).
La prueba: que alguien ajeno entienda, leyendo solo ese item, qué se gana y qué se arriesga.
**`tl_rec` es del agente y `note` es del Usuario: ningún agente escribe en `note`.**

## Reglas (no negociables)

El detalle, la medición y la historia de cada una: `templates/report_kit/MANUAL.md`, mismo número.

1. **Un solo schema** (`item.schema.json`). Prohibido inventar otro: si falta un campo, se propone ahí.
2. **Status único**: `backlog|doing|review|done|blocked` (checkbox ` `/`>`/`x`/`!`). Nada de `wip`/`pend`.
3. **Clave localStorage única**: `tlr::<project>::<plan_id>::v1`.
4. **Se persiste el item COMPLETO** (lista `x-keep`) en localStorage Y servidor.
   - **4a.** Toda página que escribe en localStorage serializa la lista `x-keep` ENTERA:
     `dashboard.html` y `pruebas.html` comparten clave. Un campo KEEP nuevo se toca en `keepOf`/
     `applyKeep` de **las dos** y en `KEEP` de `tasks_to_items.py`.
   - **4b.** El chip de modo lleva su `?` con el comando exacto del backend (`cd <plan_dir> && python3 server.py`).
   - **4c.** Las preferencias de UI van en clave aparte (`…::ui`) y se podan los valores que ya no existen.
   - **4d.** El «Modo yolo» cambia los permisos de verdad (`settings_profile.py --yolo on|off`); por eso
     `/api/save` exige `Content-Type: application/json` (415) y `Origin` local (403).
5. **Nav vía `render_nav.py`, PROHIBIDA a mano** (fuente única `nav.json`, marcadores `NAV:BEGIN/END`).
   - **5a.** Lo permanente (Core, `nav.json#permanent`) vive en `.docs/core/` y sale SOLO del plan
     activo; se genera **antes** de pintar la nav del plan.
   - **5b.** El menú lleva SIEMPRE todas las pestañas del perfil: la que no tiene datos la pone
     `gen_placeholders.py` con su receta (`nav.json#como_se_llena`). Nunca un ejemplo inventado.
   - **5d.** La barra se agrupa por la pregunta que responde: **Core ▾** (qué ES, permanente),
     **Mapas ▾** (cómo está dibujado este plan, Diseño incluido), **Calidad ▾** (¿está bien?).
     Dashboard y Resumen, nunca dentro de un desplegable.
   - **5e.** `core-sistema.html` («Las piezas») sale de `graph-dataset.full.json`, no del enfocado.
   - **5f.** La topnav se COMPRUEBA: `render_nav.py --check <plan>` (existe · lleva nav · enlaces que
     resuelven). `build.py` lo corre al final.
   - **Móvil (UX-9, 2.15):** a ≤860 px la barra es UNA fila con scroll horizontal y cada grupo abre un
     panel superpuesto bajo la barra (no empuja el contenido); su clase de estado es `ng-abierto`,
     nunca un nombre que una página pueda usar para otra cosa (`.open`).
   - **5c/5g.** `sources/` → `fuentes.html`: cada página de `sources/` es una página MÁS del informe
     (topnav con Fuentes activo, tokens del bloque SHARED, sin modo oscuro, salidas arriba y abajo).
     Una página propia (HTML sin `.md`) conserva su `<style>`; su resumen se lee del fichero ENTERO
     sin la nav (MO-40): `<p class="entradilla">` → `<meta name="description">` → `<!-- entradilla: -->`
     → primer `<p>`.
   - **5h.** `auditoria.html` no decide: lleva al dashboard filtrado. Una sola pantalla donde se decide.
   - **5i.** `sesiones.html`: el comando de cada sesión se construye en UN sitio (`gen_sesiones.py --comando`).
6. **Evidencias autocontenidas** (base64, `embed.py`): el informe abre OFFLINE.
   - **6b.** `otto.html` abre con el «Resumen del proyecto» (`meta.otto.resumen[]`), cada tarjeta con su «Por qué importa».
   - **6c.** Una `ref` fuera de la carpeta del plan no se enlaza: se copia. Nunca se amplía lo que sirve `server.py`.
7. **`otto.html` es parte del set** en todos los perfiles (con su estado vacío si Otto no ha corrido).
8. **Multi-ronda**: `--round N+1` guarda la ronda anterior en `item.history[]`.
9. **Entregables** (`gen_entregables.py`) recoge por EXCLUSIÓN todo lo que no tiene casa
   (`RESERVADAS`), y de `shots/` solo las capturas huérfanas. `render_nav.py` no pinta la nav dentro
   de `wireframes/`, `mockups/`, `prototipos/`, `resources/`, `mensajes/` ni `replays/` (se embeben).
   - **9c. Diseño (MO-76, 2.15)** (`gen_diseno.py`, cosechado de webs; perfiles `proyecto` y `diseño`):
     el material visual por las fases de `motores-de-diseno.md` Parte F — `referencias/`, `arranque/12-kit-marca/`,
     `direcciones/`, `wireframes/`, `bocetos/`, `mockups/`, `prototipos/` y las capturas huérfanas. Con
     ella, Entregables lo deja y remite a Diseño; sin material, la pone el placeholder. `build.py` la llama.
   - **9b.** A cada página se le inyecta SOLO lo que lee (`_proyectar`, decidido leyendo la plantilla,
     con `\b`). Cargar `report.json` con `fetch` rompe `file://`: descartado.
10. **Verificación pre-DONE**: servir con `--bind 127.0.0.1`, captura multi-viewport (390 y 1280),
   consola sin errores, todas las páginas autocontenidas, decisión→recarga→persiste, y el enlace
   con `enlace.py` antes de darlo.

## Lo propio de un proyecto: `templates/report_kit_local/` (MO-34, sub-ola 2.15)

**La copia del kit de un proyecto no se edita.** Había 10 copias en 5 versiones porque cada
proyecto que quería algo suyo lo metía en su `build.py` o su `nav.json`, y desde ahí `propagar.py`
ya no podía ponerlas al día sin pisarlo. Lo propio va al lado, en `.claude/templates/report_kit_local/`:

- **`gen_*.py`** — `build.py` los corre con `<plan>` como argumento, por orden alfabético, tras los
  generadores del kit y antes de placeholders y nav. Que emitan los marcadores `NAV:BEGIN/END`.
- **`nav.json`** — solo lo que AÑADE: `items`, `profiles` (ids que se suman a un perfil), `groups`
  (con el `id` de uno del kit suma hijos; uno nuevo se añade), `como_se_llena`, `permanent`. Un `id`
  que ya existe en el kit no se redefine. Lo lee `render_nav.cargar_nav`, que usan `build.py`,
  `gen_placeholders.py` y `gen_entregables.py`.

Así la carpeta `report_kit/` de cada proyecto puede ser idéntica a la del template. Igualar las copias
de los proyectos es la sub-ola 2.37 (propagación de la ola 2).

## Flujo canónico

```bash
K=.claude/templates/report_kit ;  PLAN=.docs/plans/<fecha>-<slug>
# 1) tasks.md → report.json (idempotente; conserva decisiones por id)
python3 $K/tasks_to_items.py $PLAN --project <slug> --profile proyecto
# 2) (opcional) estructura real del código → graph-dataset.json   (skill /code-graph)
#    sin él, build.py usa el fixture sintético y structure.html lo avisa
# 3) (opcional) evidencias base64
python3 $K/embed.py $PLAN
# 3b) la pestaña Entregables: recoge wireframes, mockups, mensajes, adjuntos y capturas huérfanas
python3 $K/gen_entregables.py $PLAN
# 4) materializar el set (inyección + server.py + nav única)
python3 $K/build.py $PLAN --embed
# 5) modo backend (decisiones a disco con backup atómico) — el que hace que el agente LEA lo decidido
cd $PLAN && python3 server.py --port 8830        # escucha en 127.0.0.1 (default correcto)
```

Con varios planes o proyectos abiertos, en vez de un `server.py` por plan: `webapps/report-hub/hub.py`
(un puerto para todos, mismos enlaces; `rules/output-choice.md` §3). Un plan repartido en módulos
con `modulos.json` gana la página opcional `modulos.html` (`gen_modulos.py`, lo corre `build.py`).

Y antes de dar el enlace: `python3 $K/enlace.py 8830 index.html dashboard.html` (MO-26). El Usuario
llega por túnel (`ssh -N -L 8830:127.0.0.1:8830 <usuario>@<servidor>`), **un puerto por informe** y
se cierra al terminar (`ss -tlnp | grep 88`); nunca `0.0.0.0` (`rules/security.md` §Servir HTML).

**Corregir el informe se hace editando `dashboard.md`, jamás borrando `report.json`**: el borrado se
lleva las decisiones del Usuario. Qué campo es de quién al regenerar (REFRESH · KEEP · CARRY) y la
sintaxis de `dashboard.md` (`goal:`, `blocks:`, `rec:`, `si_si:`/`si_no:`, `nocturno:`…): MANUAL.

## Dónde vive

`rules/plan-docs-structure.md` manda: el set se genera en `.docs/plans/<YYYY-MM-DD-slug>/`.
`report.json` ES la fuente de decisiones del plan. Las páginas opcionales (Alcance/Integraciones/
Paralelización/Diff/Configs) van fuera de la topnav, enlazadas desde `index.html`
(`nav.json#optional_pages`).

## Anti-patterns (los que más cuestan; la lista entera, con su porqué: MANUAL §Anti-patterns)

- ❌ Un informe que no empieza por «Lo que pediste y dónde está», o que ordena por lo fácil de medir.
- ❌ Dar un enlace sin comprobarlo con `enlace.py`, o con `127.0.0.1`/una ruta de fichero en vez de `localhost`.
- ❌ Editar la copia del kit de un proyecto en vez de usar `report_kit_local/`.
- ❌ Inventar un schema de item o una clave de localStorage ad-hoc.
- ❌ Añadir un campo KEEP y tocar `keepOf` en una sola página, u olvidarlo en `KEEP`/`CARRY`/`REFRESH`.
- ❌ Tocar el bloque `/* SHARED:BEGIN/END */` en una plantilla y no en todas (`check_shared_block.py`).
- ❌ Editar la topnav a mano, o publicar una página sin `NAV:BEGIN/END`.
- ❌ Dejar que una pestaña desaparezca del menú, o añadirla al perfil sin receta en `como_se_llena`.
- ❌ Publicar `structure.html` con el FIXTURE (build.py lo impide mirando `meta.source`).
- ❌ Generar el Core dentro del plan, o desde un plan que no es el activo.
- ❌ Ampliar la raíz que sirve `server.py` para que un enlace deje de dar 404.
- ❌ Arreglar un informe desfasado borrando `report.json`.
- ❌ Cargar `report.json` con `fetch` para adelgazar las páginas.
- ❌ Reabrir el informe de un plan con `meta.closed_at` sin limpiarlo conscientemente.
- ❌ Recuperar `speckit_dashboard/` o los dashboards «lite» archivados (LI-12).

---

_Rule version: 2.0 · 2026-10-21 — sub-ola 2.15: partida (MO-78; el cuerpo de la 1.1, literal, a
`templates/report_kit/MANUAL.md`; la tabla de decisión, a `html-output.md`), «Lo que pediste y dónde
está» + `enlace.py` (MO-26), `report_kit_local/` (MO-34), resumen de páginas propias (MO-40), pestaña
Diseño (MO-76), topnav móvil (UX-9) y perfil `minimo`. Antes: v1.1 · 2026-08-24 (+5g, +5h)._
