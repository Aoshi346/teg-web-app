---
name: "nueva-pantalla"
description: >-
  Usar cuando haya que añadir una pantalla CRUD a un frontend React que ya existe: 'añade la
  pantalla de pedidos', 'monta el CRUD de X en el front', '/nueva-pantalla'; con --mockup, antes del
  backend. NO usar para: el CRUD del backend (django-orm), arrancar un proyecto (project-setup), una
  pantalla que no es CRUD (a mano) ni juzgar código ya escrito (pattern-gate).
user-invocable: true
metadata:
  version: 1.2.0
  author: tech-lead-template
  category: workflow
  updated: 2026-11-01
---

# nueva-pantalla — el molde de una feature de frontend, rellenado

## Principio

Una pantalla CRUD son diez ficheros que siempre son los mismos y siempre se conectan igual. Escritos
a mano, cada uno sale correcto por separado y las tres primeras pantallas del proyecto acaban
distintas. Esta skill rellena el molde de
`.claude/patterns/stack/frontend-nueva-pantalla.md`: **el código nace conforme al patrón en vez de
corregirse después**, que es más barato y es lo único que funciona cuando quien escribe es un agente
sin nadie mirando.

## Cuándo activar

- «añade la pantalla de <recurso>» · «crea la feature de <recurso>» · «monta el CRUD de X en el front»
- «necesito el listado y el alta de <recurso>» · `/nueva-pantalla`
- Al ejecutar una tarea de un plan que dice «pantalla de X» y el backend ya existe.

**Requisito previo, no negociable: el CONTRATO.** Esta skill no inventa contratos — esa parte no se
relaja nunca. Lo que sí cambia (2026-09-12) es **qué cuenta como contrato**, porque se pedía el
backend entero y eso obligaba a construir por dentro antes de poder enseñar nada por fuera:

| Modo | El contrato viene de | Los datos vienen de | Cuándo |
|---|---|---|---|
| **normal** | `manage.py spectacular` → `schema.yml` | el backend, que ya responde | El backend existe |
| **`--mockup`** | el `schema.yml` de **DISEÑO** (fase 2 de `/arrancar`, desde `entidades.json`) | **MSW**, el fichero ⑩ del molde | Aún no hay backend y hay que enseñar el recorrido |

En los dos casos `npm run api:types` genera `src/types/api.d.ts` y **los tipos no se escriben a
mano**. Si no hay ni backend ni `schema.yml` de diseño, **para y dilo**: sin contrato no hay mockup,
hay invención — y ese «provisional» se queda (`frontend-contrato-con-el-backend.md`).

El modo mockup es viable porque **7 de los 10 ficheros del molde no dependen del backend** y el ⑩ son
los handlers de MSW, que `patterns/stack/tests.md` ya declara que *«sirven al navegador en
desarrollo»*. La pieza estaba dentro; solo estaba clasificada como «de prueba».

Para enseñar la maqueta en una demo (no solo en `npm run dev`): `templates/frontend-demo/mockup/mockup.ts`
sirve esos mismos handlers **sin el service worker de MSW** (no se pelea con el de una PWA), con el
login real y pasando a la API real los dominios ya conectados. El E2E con base desechable, en la misma
carpeta (`e2e/run-e2e.mjs`).

**Al llegar el backend**, el `schema.yml` de diseño **se sustituye** por el real y se regeneran los
tipos: el diff entre ambos es donde aparece lo que el backend cambió sin avisar. Orden completo:
`rules/motores-de-diseno.md` Parte F.

Disparadores (de la description): 'añade la pantalla de pedidos', 'crea la feature de clientes',
'necesito el listado y el alta de X', 'monta el CRUD de X en el front', 'scaffold a new screen',
'/nueva-pantalla'. Escribe los 10 ficheros del molde de
.claude/patterns/stack/frontend-nueva-pantalla.md (tipos, api, esquema, hooks, lista, formulario,
página, ruta, test y handlers MSW) ya cableados entre sí, y corre pattern_check_frontend.py sobre lo
generado. · NO usar para: el CRUD del BACKEND Django (eso es django-orm), arrancar un proyecto desde
cero (project-setup), una pantalla que NO es CRUD sobre una entidad — panel multi-origen, asistente
de N pasos, editor (esas se escriben a mano siguiendo el catálogo capa por capa), ni para juzgar
código ya escrito (pattern-gate).

## Alcance: React + Vite, y qué hacer en Ionic o Next (31-10-2026, sub-ola 3.65, UX-10)

El molde es el de `patterns/stack/frontend-stack.md`: **React + Vite + react-router + TanStack
Query + React Hook Form/Zod + MSW**, con los tipos de `openapi-typescript`. Fuera de ese stack, la
skill no se fuerza:

| El proyecto usa | Qué hacer |
|---|---|
| **React + Vite** (el canon) | Esta skill, entera |
| **Ionic + React** (p. ej. EvoPreven) | ①-④ (tipos, api, esquema zod, hooks) y ⑩ (MSW) valen tal cual, y ⑦ (el test) con los selectores de Ionic; la lista, el formulario, la página y la ruta (⑤ ⑥ ⑧ ⑨) se escriben con los componentes de Ionic (`IonList`, `IonPage`, `IonRouterOutlet`) siguiendo **las pantallas que ya tenga el proyecto**, no el molde. Dilo en la salida |
| **Next.js** (p. ej. webs) | Mismo reparto: ①-④ y ⑩ valen, y ⑤-⑦ si la pantalla es componente de cliente; página y ruta (⑧ ⑨) van por el enrutado de Next (`app/<recurso>/page.tsx`), y la carga de datos decide si es componente de servidor o de cliente. Sin tocar el `next.config` por esta skill |
| Otro (Vue, Svelte, plantillas Django) | **No aplica.** Para y dilo: el catálogo capa por capa de `frontend-nueva-pantalla.md` sirve de lista, el código no |

`pattern_check_frontend.py` está calibrado para el canon: en Ionic o Next, lo que marque sobre las
piezas propias del framework es candidato, no fallo. **Sin medir:** cuánto del molde reutiliza de
verdad un proyecto Ionic o Next; la tabla sale de leer los dos stacks, no de haberlo corrido.

## Input contract

| Dato | Ejemplo | Si falta |
|---|---|---|
| **recurso** (singular y plural, en inglés como en la API) | `order` / `orders` | **Pregunta.** Sin esto no hay nada que generar |
| **ruta del endpoint** | `/orders/` | Dedúcela del plural y **confírmala** contra `schema.yml` |
| **campos del formulario** con tipo y obligatoriedad | `reference: texto, obligatorio` · `amount: número > 0` | **Pregunta.** Es el único trabajo real del molde |
| **columnas de la lista** | `reference`, `amount`, `created_at` | Por defecto: los campos del formulario + `id` |
| **ruta de la app** | `/orders` | Por defecto: `/` + plural |

Máximo **una** ronda de preguntas, todas juntas. Si el usuario contesta a medias, usa los defaults,
**escribe en el informe qué asumiste** y sigue: una skill que interroga tres veces no se vuelve a usar.

> ⚠️ **La única regla de diseño que esta skill hace cumplir, porque es la que llega al producto.**
> Si la pantalla lleva cualquier entrada animada, el `opacity:0` **cuelga de una clase que añade el
> propio JS** (`body.js-ready`), nunca del elemento. Motor pegable listo:
> `templates/diseno/motor-reveal.html`.
>
> El contraejemplo es real y está guardado: `resources/referencias-diseno/mal/attomo-digital.html`
> declara `.reveal{opacity:0}` sin condición (`:1006`) y define `initGSAP()` que **no llama nunca**
> (`:1441`). La página entera es invisible, y está publicada así. Esta skill escribe el código que
> va a producción: si la regla no está aquí, no llega.

## Procedimiento

1. **Leer el molde y el terreno.** `.claude/patterns/stack/frontend-nueva-pantalla.md` (los 10
   ficheros y qué se rellena en cada uno) y **una feature ya existente del proyecto** si la hay: si
   el repo tiene su propia forma, gana la del repo — el molde es el default, no una imposición.
2. **Comprobar el contrato.** ¿Existe `src/types/api.d.ts` generado y contiene el esquema del
   recurso? Si no: `npm run api:types` (o avisa de que falta el paso de
   `frontend-contrato-con-el-backend.md`). **No escribas los tipos a mano** — es exactamente lo que
   ese documento existe para evitar.
3. **Comprobar las piezas de nivel 1.** ¿Existen `<Asincrono>` y `<BotonDeEnvio>`
   (`frontend-a-prueba-de-errores.md`)? Si no existen, **créalas primero**: son dos ficheros y son
   lo que hace que la pantalla no pueda quedarse sin estado de error ni admitir doble clic.
4. **Escribir los 10 ficheros** en el orden del molde (① tipos → ⑩ handlers). En `routes.tsx`,
   **una línea**; si hay más de un frente trabajando, ese fichero tiene dueño único
   (`rules/parallelization.md` §file claims) — pide la línea en vez de editarlo.
   Si el proyecto usa el **mapa de pantallas** (`templates/frontend-screens/`, sub-ola 3.67), esa
   línea es el `load` de la pantalla en `src/app/screens.ts`, los enlaces van con `hrefTo('<id>')`
   y después se corre `python3 scripts/flow_edges.py`. En un derivado React nuevo, se monta la
   primera vez (su `README.md`, 5 minutos).
5. **Verificar.** Y esto no es opcional:
   ```bash
   python3 .claude/patterns/stack/pattern_check_frontend.py <los 10 ficheros>
   npx tsc --noEmit          # el molde solo vale si compila
   npx vitest run src/features/<recurso>/    # el test generado tiene que pasar en verde
   ```
   ⚠️ Recordatorio (repetido a propósito): **no reportes la pantalla como hecha sin pegar la salida
   de esos tres comandos.** Es el punto exacto donde se deriva — el código "se ve bien" y se da por
   terminado sin ejecutar nada.
6. **Informar** con el formato de salida de abajo.

## Formato de salida (campos, no prosa)

```
recurso:        <singular> / <plural>
ficheros:       <lista de rutas creadas> · <rutas modificadas>
rellenado:      campos=<n> columnas=<n>
supuestos:      <lo que asumiste porque no se dijo, o "ninguno">
verificación:   pattern_check=<limpio|N hallazgos> · tsc=<ok|error> · tests=<n pasan/n>
backend:        <ok | falta: lista de ficheros que hacen falta>
fuera del molde: <lo que esta pantalla necesita y el molde no cubre, o "nada">
```

## Alcance — qué NO hace (léelo antes de prometer nada)

- **No escribe el backend.** Genera la feature de **frontend completa** y, del backend, **imprime la
  lista** de lo que hace falta (modelo · serializer · servicio · vista · ruta · test) apuntando al
  documento de cada capa. Razón: el molde de backend (punto único de filtrado, mixins de modelo)
  todavía no está escrito, y generar contra un molde que no existe produce código que habrá que
  rehacer. Cuando exista, esta skill se ata a él.
- **No cubre la pantalla rara.** CRUD sobre **una** entidad, con permisos y filtros. Un panel con
  tres orígenes de datos, un asistente de cinco pasos o un editor gráfico se escriben a mano. Si la
  petición se sale del molde en tres sitios, **dilo y no lo fuerces**: un generador que intenta
  cubrirlo todo acaba en metaprogramación que nadie sabe modificar.
- **No decide el diseño.** Usa los tokens del proyecto (`frontend-design-system.md`). Si no hay
  origen de tokens, avísalo: no inventes colores.

## Anti-patterns

- ❌ Generar **sin contrato** — ni backend vivo ni `schema.yml` de diseño → inventas los tipos y hay
  que rehacerlo entero. (Con `--mockup` el contrato SÍ existe: sale de la fase 2 de `/arrancar`.)
- ❌ Escribir los tipos a mano «provisionalmente» para adelantar el mockup → ese provisional se queda.
- ❌ Escribir los tipos del recurso a mano «porque el generado aún no tiene el campo».
- ❌ Copiar la feature más parecida y renombrar: arrastra lo que sobra y pierde lo que no se ve
  (el estado vacío, casi siempre).
- ❌ Dar la pantalla por hecha sin correr el comprobador, `tsc` y el test (paso 5).
- ❌ Editar `routes.tsx` cuando otro frente lo tiene reclamado.
- ❌ Forzar el molde sobre una pantalla que no es CRUD — el molde tiene un límite escrito y es parte
  del molde.
- ❌ Preguntar campo por campo en varias rondas.

## Ejemplos

### User: «añade la pantalla de pedidos, con referencia e importe»
TL: pregunta **una vez** (ruta del endpoint `/orders/`, ¿importe obligatorio y mayor que cero?,
¿ruta `/orders`?) → comprueba `api.d.ts` y las dos piezas de nivel 1 → escribe los 10 ficheros →
corre comprobador + `tsc` + test → informa con el bloque de campos, incluyendo `backend: ok`.

### User: «monta el panel de control con las ventas del mes, las alertas y el gráfico»
TL: **no aplica el molde** y lo dice: son tres orígenes de datos y ningún CRUD. Propone escribirla a
mano siguiendo `api-y-errores.md` + `componentes.md`, reutilizando `<Asincrono>` por cada bloque
para que ninguno se quede sin estado de error.

### User: «la feature de clientes» (y `/clients/` devuelve 404)
TL: mira si hay contrato antes de parar. **Con `schema.yml` de diseño** (fase 2 de `/arrancar`):
«El backend no existe todavía, así que lo monto en modo mockup con MSW: vas a poder navegarlo y
enseñarlo hoy, y cuando esté el endpoint se sustituye el contrato y se regeneran los tipos.»
**Sin ningún contrato**: para en el paso 2. «No hay ni endpoint ni modelo de datos decidido. Si
escribo los tipos ahora me los invento y hay que rehacerlo. Dos salidas: decidimos el contrato
(`/arrancar` fase 2, unos minutos) o empiezo por el backend.»

## Related

- `.claude/patterns/stack/frontend-nueva-pantalla.md` — **el molde**: esta skill es su automatización
- `.claude/patterns/stack/frontend-a-prueba-de-errores.md` — `<Asincrono>` y `<BotonDeEnvio>` (paso 3)
- `.claude/patterns/stack/frontend-contrato-con-el-backend.md` — los tipos generados (paso 2)
- `django-orm` (`references/crud.md`) — el otro lado: el CRUD del backend
- `pattern-gate` — juzga el patrón de lo ya escrito; esta skill hace que nazca conforme
- `project-setup` — arranque del proyecto; esto es una pantalla dentro de un proyecto que ya anda
