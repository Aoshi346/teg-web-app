# `report_kit/` — el "informe total" multi-página (sistema canónico TPL-1 W3)

Set de informe HTML autocontenido generado desde **un `report.json`** único. Las pestañas comparten
la misma topnav (fuente única `nav.json` + `render_nav.py`), decisiones persistentes (localStorage /
disco), evidencias base64, multi-ronda. **Rule: `rules/report-kit.md`** (lo que hay que cumplir) ·
**manual: `MANUAL.md`** (el porqué) · **qué informe usar: `rules/html-output.md`**.

## Archivos

| Archivo | Qué hace |
|---|---|
| `item.schema.json` | **El schema único** (meta + items: title/desc/goal/status/decision/verdict/evidence/history). `x-keep` = campos editables que persisten enteros |
| `nav.json` | Fuente única de la topnav + **perfiles** (`proyecto`/`diseño`/`incidencia`) + páginas opcionales |
| `tasks_to_items.py` | `tasks.md` (checkboxes) → `report.json`. Idempotente (merge por id): `KEEP` = del Usuario, no se pisa · `REFRESH` (desc/goal/rec/auditor/blocks/start/due/manual_test) = siempre del fichero, se vacía si deja de declararse · `CARRY` = heredado. `--round N` → snapshot a `history[]`. Además parsea `blocks:` `start:` `due:` `prereq:` `url:` `test:` `case:` (ver su docstring) |
| `embed.py` | Evidencias `img` → base64 (`report.embedded.json`). Pillow opcional (recomprime ~820px q52) |
| `graph_reduce.py` | `graph.json` (node-link) → `graph-dataset.json` con layout precalculado por comunidad. `--fixture` = dataset sintético de demo |
| `build.py` | Inyecta los JSON en las plantillas (`/*__DATA__*/null`), copia `server.py`, corre `render_nav.py --all` |
| `server.py` | Modo backend: sirve el set + `POST /api/save` → `report.json` en disco (backup rotado + escritura atómica). `127.0.0.1` |
| `*.template.html` | Las 6 páginas: `index` (resumen+mapa SVG) · `structure` (grafo del código) · `dashboard` (tareas: lista+kanban+**gantt**+**mapa mental**) · `results` (verdicts doble evidencia) · **`pruebas`** (manual de prueba manual + lo ya verificado) · `otto` (copiloto) |
| `fixture.graph-dataset.json` | Dataset sintético para `structure.html` hasta que corra `/code-graph` |
| `gen_diseno.py` | La pestaña **Diseño** (MO-76, cosechada de webs): referencias, kit de marca, direcciones, wireframes, bocetos, mockups y capturas huérfanas, por fases. La llama `build.py` si el perfil lleva `diseno` |
| `gen_modulos.py` | Página opcional **Módulos** (WA-19, cosechada de AMC): una solapa por módulo con puerto, base, rama, ficheros de los que es dueño y avance. Solo si el plan trae `modulos.json`; la llama `build.py` |
| `enlace.py` | El enlace para el Usuario, `http://localhost:<puerto>/…`, comprobado con `curl` antes de darlo (MO-26). Sale 1 si alguno no da 200 y 2 si el puerto escucha en `0.0.0.0` |
| `MANUAL.md` | El manual largo: el porqué, la medición y la historia de cada regla de `rules/report-kit.md` (era su cuerpo hasta la sub-ola 2.15) |

## Lo propio de un proyecto: `../report_kit_local/` (MO-34)

**Esta carpeta no se edita en un proyecto**: así es idéntica a la del template y `propagar.py` la
pone al día sin pisar nada. Lo propio va al lado, en `.claude/templates/report_kit_local/`:
`gen_*.py` (los corre `build.py` con `<plan>`, tras los del kit) y un `nav.json` con solo lo que añade
(`items`, `profiles`, `groups`, `como_se_llena`, `permanent`). Detalle: `rules/report-kit.md` §Lo propio.

## Flujo (el de la rule)

```bash
K=.claude/templates/report_kit ;  PLAN=.docs/plans/<fecha>-<slug>
python3 $K/tasks_to_items.py $PLAN --project <slug> --profile proyecto   # 1) tasks.md → report.json
python3 $K/embed.py $PLAN                                                # 2) evidencias → base64 (opcional)
python3 $K/build.py $PLAN --embed                                        # 3) materializar el set
cd $PLAN && python3 server.py                                            # 4) modo backend (opcional)
python3 $K/enlace.py 8800 index.html dashboard.html                      # 5) el enlace, comprobado
```

## Relación con los sistemas previos

- `speckit_dashboard/` — **archivado el 2026-10-19** (`_archive/2026-10-19/templates/`, LI-12): este kit lo absorbió; su server.py y parser viven aquí evolucionados.
- `feedback_audit/` — sigue canónico para SU caso (feedback de cliente + la skill `feedback-audit`, que lanza `feedback-verify.js`); el
  patrón base64 se generalizó aquí (`embed.py`).
- `html/` — plantillas sueltas (status-report, config-builder…) y el set de `/visual-map`.

## Gotchas

- El placeholder de datos es EXACTAMENTE `const DB = /*__DATA__*/null;` — no lo toques en las plantillas.
- La nav NUNCA a mano: `render_nav.py --all <plan>` (marcadores `NAV:BEGIN/END`).
- localStorage: `tlr::<project>::<plan_id>::v1`. En modo backend el POST manda los items COMPLETOS.
  **`dashboard.html` y `pruebas.html` comparten esa clave**: las dos serializan la lista `x-keep`
  entera, o la última en guardar borra lo que la otra no conoce.
- `pruebas.html` es nueva en `nav.json` y en los 3 perfiles: un plan generado ANTES de esto tendrá
  el enlace en la nav sin el fichero detrás hasta que se vuelva a correr `build.py`. Regenerar el
  set arregla; correr solo `render_nav.py` no.
- `file://` está bloqueado para Playwright — verifica con `python3 -m http.server --bind 127.0.0.1`.
- La topnav marca el desplegable abierto con la clase `ng-abierto`, no `open`: cinco plantillas
  tienen su propio `.open` para un botón y la barra saltaba de alto al abrir un grupo (UX-9).
