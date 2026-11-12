# `templates/frontend-screens/` — el mapa de pantallas de un derivado React

> Sub-ola 3.67 (UX-19). Cosechado de fitapp (`src/app/pantallas.ts`, `pages/MapaPantallas.tsx`), donde
> el Usuario pidió además ver **el flujo diseñado frente al implementado** (T-016). Reinventarlo en
> cada proyecto cuesta más que copiarlo.

## Qué trae

| Fichero | Va a | Qué hace |
|---|---|---|
| `screens.ts` | `src/app/screens.ts` | El **registro único** de pantallas: id del mapa de `/producto`, ruta, zona, nombre y `load` cuando existe la página. `hrefTo('C03', { orderId })` no compila si falta un parámetro |
| `ScreenMap.tsx` | `src/app/ScreenMap.tsx` | La página `/pantallas`: **lista** (construidas y pendientes por zona) y **flujo** (`?vista=flujo`). Y `MissingScreen`, el marcador digno de la pantalla que aún no existe |
| `flow.ts` | `src/app/flow.ts` | `DESIGNED_FLOW` (se copia del mapa de `/producto`) y la comparación con lo implementado: *implementada* · *falta en el código* · *en el código, sin diseñar* |
| `flow.implemented.json` | `src/app/` | Lo genera `flow_edges.py`; no se edita a mano |
| `flow_edges.py` | `frontend/scripts/` | Lee los `hrefTo('X')` de cada página y escribe el JSON; `--check` para CI; `--self-test` |

## Cómo se monta (5 minutos)

1. Copia los ficheros a su sitio y sustituye las pantallas de ejemplo por las del mapa de `/producto`.
2. En el router, una ruta por pantalla desde `SCREENS`: con `load`, `lazy(load)`; sin él,
   `<MissingScreen id="…" />`. Y `/pantallas` → `<ScreenMap />` solo si `SCREEN_MAP_VISIBLE`.
3. Los enlaces entre pantallas, siempre con `hrefTo(...)`: es lo que ve `flow_edges.py`.
4. `python3 scripts/flow_edges.py` tras añadir pantallas; `--check` en el CI.

## Límites, dichos

- `flow_edges.py` ve los `hrefTo` **del fichero de la página**, no los de un componente que importe.
  Por eso el mapa dice «falta en el código», no «roto».
- La vista de flujo es una **tabla**, no el diagrama de fitapp (12 ficheros con disposición y
  filtros): la tabla contesta la pregunta del Usuario; el diagrama, si un proyecto lo quiere, se
  copia de fitapp.
- Comprobado en la 3.67: `tsc --strict` en verde con React 19 y react-router 7 (los de fitapp), y un
  `hrefTo('C03')` sin parámetro no compila. **Sin medir:** montado en un derivado nuevo de punta a punta.
