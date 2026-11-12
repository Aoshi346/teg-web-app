# `report_kit_local/` — lo PROPIO de este proyecto en el report-kit (MO-34)

La carpeta de al lado, `report_kit/`, **no se edita en un proyecto**: es la misma en todos y
`propagar.py` la pone al día. Hasta la sub-ola 2.15 (21-10-2026) cada proyecto que quería algo suyo
editaba su copia de `build.py` o de `nav.json` —había 10 copias en 5 versiones— y a partir de ese
momento ningún arreglo del kit le llegaba sin pisar lo suyo. Lo propio va **aquí**:

| Fichero | Qué hace |
|---|---|
| `gen_*.py` | `build.py` los corre con el plan como argumento (`python3 gen_x.py <plan>`), por orden alfabético, tras los generadores del kit y antes de los placeholders y la topnav. La página que escriban lleva los marcadores `<!-- NAV:BEGIN -->` / `<!-- NAV:END -->` (la nav la pinta `render_nav.py`) |
| `nav.json` | Solo lo que AÑADE al `nav.json` del kit — mismo formato. Lo suma `render_nav.cargar_nav` |

```json
{"items": [{"id": "modulos", "label": "Módulos", "href": "modulos.html"}],
 "profiles": {"proyecto": ["modulos"]},
 "groups": [{"id": "mapas", "children": ["modulos"]}],
 "como_se_llena": {"modulos": {"que": "La torre de control de módulos.", "cmd": "python3 .claude/templates/report_kit_local/gen_modulos.py <plan>"}}}
```

- Un `id` que ya existe en el kit **no se redefine** (se avisa y se salta): sumar, no sustituir.
- Un grupo con el `id` de uno del kit (`core`, `mapas`, `calidad`) suma hijos; uno nuevo se añade.
- Una pestaña que el perfil lleva y que no tiene página sale con su placeholder (`como_se_llena`).

Este README viene del template; lo demás de esta carpeta es del proyecto y `propagar.py` no lo toca.
Regla: `rules/report-kit.md` §Lo propio de un proyecto.
