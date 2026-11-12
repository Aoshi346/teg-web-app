---
paths:
  - ".docs/html/**"
  - ".docs/plans/*/*.html"
  - ".docs/plans/*/report.json"
  - ".docs/plans/*/sources/**"
  - ".docs/feedback/**"
  - ".claude/skills/html-suelto/**"
  - ".claude/skills/pdf-premium/**"
  - ".claude/skills/feedback-audit/**"
  - ".claude/templates/html/**"
  - ".claude/templates/report_kit/**"
  - ".claude/rules/output-choice.md"
  - ".claude/output-styles/**"
---
# Qué informe para qué — y cómo se entrega

> **Cuándo aplicar:** antes de entregar cualquier salida que no sea una respuesta en el chat: elegir
> la pieza, dónde se guarda y cómo llega al Usuario. Es el catálogo único (AN-2): `report-kit.md` es el
> manual técnico del kit y `html-output.md` la convención de un HTML suelto; ninguna de las dos repite
> esta tabla. **NO aplicar:** al contenido de cada pieza (eso es su skill o su rule).

## 1. Qué salida toca — la primera pregunta con «sí» decide

| # | Pregunta | Sí → |
|---|---|---|
| 1 | ¿Lo necesitas ya, en esta conversación, y cabe en una pantalla? | **Markdown en el chat** (el default: el HTML cuesta 2-4× más) |
| 2 | ¿Lo edita una persona a mano o lo lee otro agente? (config, research literal, `REPORT.md`) | **Fichero `.md`**; si acompaña a un plan, en `sources/` (lo pinta `md_to_html.py`) |
| 3 | ¿Sale hacia un cliente para leer, firmar o imprimir? | **`pdf-premium`** |
| 4 | ¿Es el trabajo de UN issue que irá a producción? | report-kit perfil **`issue`**: `informe.html` en ruta fija (`gen_informe.py`), con los apartados de Pilar y Roberto; lo cierra `/cerrar-issue` |
| 5 | ¿Hay decisiones que tienen que sobrevivir a la pestaña? (aprobar, priorizar, Gantt, pruebas) | **report-kit** (§2 para el perfil) |
| 6 | ¿Hay que comprobar el feedback de un cliente contra la web en vivo? | **`feedback-audit`** (un HTML con capturas en base64, abre sin servidor) |
| 7 | ¿Son resultados de auditores? (qa-loop, pentest, a11y) | **`REPORT.md` + `findings.json`** → pestaña Resultados del kit, no un HTML aparte; entre proyectos y rondas, `findings.html` de `report-hub` |
| 8 | ¿Quieres ver la forma del código? | **`/visual-map`** (+ `/code-graph`), en el Gate B del plan grande |
| 9 | ¿Es un esquema decidido, no derivado del código? (C4, lean canvas) | **`/schema`** → `.docs/schemas/` |
| 10 | ¿Describe lo que el proyecto ES hoy? | **`.docs/core/`** (`gen_core.py`) |
| 11 | ¿Hay que decidir cómo se ve algo? | **`disenar-pantalla`** (una) · **`direcciones-de-arte`** (N estilos) · **`marca`** |
| 12 | ¿Hay que comparar N configuraciones con métricas? | **`matrix-eval-harness`** |
| 13 | ¿Hay que ver el harness entero, de lo general a lo concreto? | **`.docs/core/core-levels.html`** (`gen_core_levels.py`): sesión → capas → familia → pieza, y un proyecto de ejemplo |
| — | Ninguna | **Página suelta**, skill **`html-suelto`** (antes `html-artifact`): explica UNA cosa sin decisiones que guardar |

## 2. El perfil del report-kit

| Necesito… | Perfil o pieza |
|---|---|
| Plan vivo con tareas **y** resultados (el caso común) | `proyecto` |
| Diseño o propuesta **sin código** | `diseño` (sin arquitectura, datos ni flujos) |
| Incidencia: qué pasó, qué se hizo, cierre | `incidencia` |
| Plan pequeño o de un día, sin código propio | `minimo` |
| El eje tiempo · la forma del plan | vistas Gantt y Mapa mental del dashboard |
| Que una persona pruebe a mano lo entregado | `pruebas.html` |
| Enseñar referencias, marca, wireframes o mockups | pestaña Diseño (`gen_diseno.py`) |

## 3. Cómo se entrega — siempre igual, en todos los proyectos

- **Nunca como Artifact de claude.ai** (decisión del Usuario; vivía solo en una memoria local, AN-D2).
  Tampoco un informe de cliente subido a un host público «para compartirlo».
- **Servido en `127.0.0.1` y por túnel SSH**, un puerto por informe: `server.py` del kit
  (`cd <plan> && python3 server.py`) o `python3 -m http.server <puerto> --bind 127.0.0.1`. Nunca
  `0.0.0.0`, tampoco en Docker (`rules/security.md`). Al terminar, se cierra (`servidores-vivos.sh`
  lista los que siguen vivos al cerrar la sesión).
- **Varios informes, o varios proyectos, a la vez: un solo puerto con `report-hub`**
  (`python3 webapps/report-hub/hub.py --port 8790`, en el template, 4.18): índice de todos los
  planes, panel de hallazgos de auditores (fila 7, sin abrir carpetas) y registro de peticiones.
  Monta cada proyecto con la misma forma que `server.py`, así que los informes viejos abren sin
  regenerar; el modo yolo sigue siendo cosa del `server.py` del plan. Detalle: su `README.md`.
- **El enlace es `http://localhost:<puerto>/<ruta>`, comprobado antes de darlo**:
  `python3 .claude/templates/report_kit/enlace.py <puerto> <ruta>…` (sale 1 si alguno no da 200). Con
  el túnel: `ssh -L <puerto>:127.0.0.1:<puerto> <servidor>`.
- **Empieza por «Lo que pediste y dónde está»** (MO-26): cada cosa pedida, en el orden de prioridad
  del Usuario, con el sitio donde está; lo que no tiene sitio, se dice. En el kit es `meta.pedido`.
- **Dónde vive**: el informe de un plan, en `.docs/plans/<fecha>-<slug>/`; una página suelta, en
  `.docs/html/<slug>-<fecha>.html` (no en `.claude/docs/html/`, ni en la raíz). Un research o un plan
  largo, en el repo: lo que vive solo en `~/.claude/plans/` se sobrescribe, y el hook
  `warn-plans-outside-repo.sh` avisa al escribir ahí (AN-14).
- **Si sale hacia un cliente** (web, PDF, propuesta): sin notas internas visibles,
  `python3 .claude/scripts/check_internal_notes.py <fichero-o-carpeta>` en 0 (AN-13).

## 4. Nunca

Un Artifact de claude.ai para un informe · `speckit_dashboard/` y los dashboards lite (retirados el
19-10) · un generador de informe nuevo dentro de un plan (`build_informe.py`): si al kit le falta algo,
se propone en el kit · un `.html` en la raíz del repo · servir en `0.0.0.0`.

## 5. En el chat: el output-style «Visual y explicativo»

Para la fila 1 hay un estilo de respuesta en `.claude/output-styles/visual-explanatory.md` (AN-D5,
cosechado de EvoPreven): resumen sencillo, detalles y **el diagrama al final**, que es lo que queda a
la vista en la terminal. **Viene apagado**: se enciende por sesión con `/output-style` (o `/config`) o
por proyecto con `"outputStyle": "Visual y explicativo"` en `settings.json`. Activo, suma ~2,4k al
contexto fijo de cada mensaje (`check_instrucciones.py` lo cuenta) y no llega a los subagentes.

_Rule version: 1.1 · 2026-10-31 — sub-ola 4.18 (WA-17, WA-19): `report-hub` en §3 y fila 7. 1.0 · 2026-10-31 — sub-ola 3.18 (AN-2, AN-D2): absorbe la tabla de decisión de
`html-output.md` §Qué informe usar (2.15, MO-78) y el árbol de 12 preguntas de la página «Qué informe
usar» de la revisión integral; destino único de la página suelta, `.docs/html/` (ORD-4)._
