# El stack de frontend — qué se instala y por qué ese y no otro

> La decisión, tomada una vez, de qué librería resuelve cada papel en un proyecto React nuevo. No
> es una capa de código como las demás de esta carpeta: es lo que hay **antes** de escribir la
> primera línea, y lo que hace que los otros documentos (`estado.md`, `formularios.md`,
> `api-y-errores.md`…) puedan dar por sentado con qué se está trabajando.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only stack`.

## La regla (una frase)

Cada papel del frontend tiene **una** librería asignada y una **versión mayor** concreta; añadir una
segunda para el mismo papel, o trabajar en otra mayor, no está prohibido pero deja de ser el patrón
de casa y hay que escribir por qué.

## Implementación de referencia

**Qué es una "versión mayor".** Las librerías se numeran `MAYOR.menor.parche` — por ejemplo
`5.62.0`. Solo el primer número puede romper código existente: pasar de `5.62` a `5.90` es seguro,
pasar de `4` a `5` no. Por eso el canon fija la mayor y deja libre el resto: `^5.62.0` significa
"cualquier 5.x a partir de esta". Importa porque los ejemplos de estos documentos están escritos
contra una mayor concreta: copiarlos en un proyecto que va una mayor por detrás no compila.

| Papel | Librería | Mayor | Por qué esta y no la alternativa |
|---|---|---|---|
| **Estilos** | Tailwind CSS | **4** | Ver `estilos.md`. La alternativa es CSS propio o CSS-in-JS: ambas obligan a inventar nombres de clase y a mantener una hoja aparte que nadie borra |
| **Componentes de UI** | el **patrón shadcn**: Base UI + CVA, **copiados al repo** | — | No es una dependencia: es una forma de traerlos. Ver el apartado de abajo |
| **Datos del servidor** | TanStack Query | **5** | Es una **caché**, no un cliente HTTP: recuerda lo que ya pidió, deduplica peticiones simultáneas, reintenta y refresca. La alternativa —guardarlos en un store— obliga a escribir todo eso a mano y nadie lo escribe (`estado.md`) |
| **Estado de cliente** | Zustand | **5** | Un store en ~10 líneas sin ceremonia. La alternativa clásica, Redux, pide acciones, reducers y middleware antes de guardar un booleano; se justifica cuando hace falta auditar cada cambio de estado, que casi nunca es el caso |
| **Formularios** | React Hook Form | **7** | Solo re-dibuja el campo que cambia, no el formulario entero. Se elige **a propósito** sobre TanStack Form, que es más nuevo y más tipado pero tiene menos recorrido y menos respuestas escritas cuando algo falla |
| **Validación** | Zod | **4** | TypeScript solo comprueba tipos **al compilar**; en cuanto el dato llega de fuera (una API, un formulario) ya no mira nada. Si el servidor devuelve `precio` como texto donde el tipo decía número, TypeScript no se entera y Zod sí. La alternativa, Yup, no deriva el tipo TypeScript del esquema, así que acabas escribiendo la forma del dato dos veces |
| **Rutas** | react-router | **7** | Ver `rutas.md`. La alternativa es un framework completo (Next.js, Remix), que trae rutas *y* servidor: si el backend ya es Django, ese servidor sobra |
| **Iconos** | lucide-react | (sin fijar) | Cada icono es un componente que se importa por su nombre, así que al empaquetar solo viaja el que usas. Publica muy a menudo y sin romper nada, por eso su mayor no se fija |
| **Saneado de HTML** | DOMPurify | **3** | Ver `saneado.md`. No hay alternativa razonable: escribir un filtro de HTML propio es la forma clásica de dejar un agujero |
| **Cliente de la API** | openapi-fetch + openapi-react-query, sobre los tipos de openapi-typescript | **0.17** · **0.5** | Ver `frontend-contrato-con-el-backend.md` §Paso 3b. Las llamadas salen tipadas del contrato (ruta, parámetros y respuesta), y el envoltorio de TanStack Query pesa ~1 KB. Las alternativas generan más: orval escribe cliente, hooks y mocks (más código que revisar) y Hey API va por debajo de la 1.0 y cambia a menudo |
| **Tipos** | TypeScript | **5** (≥5.9) | La 7 existe y es estable, pero **no** vale aún como paquete `typescript` del proyecto: ver abajo «Por qué TypeScript 5 y no 7» |
| **Tests** | Vitest **5** · Testing Library **16** · MSW **3** · Playwright | — | Ver `tests.md`, que define qué se prueba en cada nivel. Lo que cambia al subir de mayor, abajo |

**Los dos acompañantes de Tailwind.** `clsx` y `tailwind-merge` (unos pocos kilobytes entre las
dos) hacen falta para el ayudante `cn()` de `estilos.md`. Van en el canon porque sin ellos la
alternativa es concatenar clases a mano, que tiene un fallo silencioso explicado en ese documento.

**Los componentes de UI: el patrón shadcn, que es una forma de traerlos y no una librería.** Un
botón o un diálogo bien hechos tienen dentro mucho trabajo que no se ve —foco, teclado, lector de
pantalla, cerrar con Escape— y que es justo la parte que se hace mal cuando se escribe a mano. La
respuesta habitual es instalar una suite (Material UI, Mantine, Chakra) y quedarse con sus estilos;
la de casa es otra:

1. Se parte de una **primitiva sin estilos** (*headless*: trae el comportamiento y la accesibilidad,
   ningún color). En proyectos nuevos, **Base UI** — desde julio de 2026 es el default de shadcn/ui,
   con la misma API y menos peso (su diálogo pesa 6,4 KB frente a 9,2 KB). **Radix no está
   deprecado**: donde ya esté, se queda.
2. Se le ponen las variantes con **CVA** (`class-variance-authority`): en vez de repartir cadenas de
   clases por el JSX, el componente declara sus variantes (`variant` × `size`) en un sitio.
3. Y **el fichero se copia al repositorio**, no se instala. `src/components/ui/button.tsx` es
   **nuestro**.

Por qué esa última es la decisión de verdad, con dos razones que van en la misma dirección:

- **Proyectos de cliente, rebrandeables.** Una suite con estilos propios es rapidísima el primer día
  y cara el día que hay que repintarla entera para otra marca: se acaba peleando contra sus temas.
  Con el componente en el repo, cambiarlo es editar un fichero.
- **Y para un agente es la mejor opción con diferencia**: edita un fichero tuyo en vez de pelearse
  con la API de un paquete y su documentación, y la accesibilidad y el teclado ya vienen resueltos
  desde la primitiva — que es exactamente la parte que un agente hace mal.

Lo que cuesta, dicho claro: los componentes copiados **no se actualizan solos**. Si upstream arregla
un fallo de accesibilidad, hay que traerlo a mano. Es el precio de quedarse el código, y se paga a
gusto en un proyecto de cliente; en un interno de tres pantallas, quizá no.

**El `package.json` de referencia**, que es lo que el comprobador lee:

```json
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "react-router": "^7.9.0",
    "@tanstack/react-query": "^5.62.0",
    "zustand": "^5.0.0",
    "react-hook-form": "^7.54.0",
    "@hookform/resolvers": "^5.0.0",
    "zod": "^4.0.0",
    "lucide-react": "^0.547.0",
    "dompurify": "^3.2.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^3.0.0",
    "openapi-fetch": "^0.17.0",
    "openapi-react-query": "^0.5.4"
  },
  "devDependencies": {
    "tailwindcss": "^4.1.0",
    "typescript": "^5.9.3",
    "vite": "^8.3.0",
    "@vitejs/plugin-react": "^6.1.0",
    "vitest": "^5.0.0",
    "jsdom": "^30.1.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/dom": "^10.4.0",
    "msw": "^3.0.0",
    "@playwright/test": "^1.50.0",
    "openapi-typescript": "^7.13.0",
    "@types/react": "^19.1.0",
    "@types/react-dom": "^19.1.0"
  }
}
```

`@hookform/resolvers` es la pieza que conecta React Hook Form con Zod: el formulario le pregunta al
esquema si el valor vale. Los resolvers de la versión 5 admiten Zod 4 — es lo que hace que estas dos
elecciones se puedan tomar juntas y no haya que congelar Zod en la 3.

**Este `package.json` se instala y arranca: probado el 2026-10-21** (sub-ola 2.18,
`_archive/2026-10-20/medicion-2.18/`). Un proyecto de prueba con este bloque **copiado tal cual**, Node
22, y un backend Django 5.2 + DRF 3.18 + drf-spectacular 0.30: `npm install`, `openapi-typescript`
contra el `schema.yml`, `tsc --noEmit`, `vitest run` con Testing Library + MSW 3 y `vite build`, los
cinco en verde. (Sin `@types/react` y `@types/react-dom`, `tsc` falla con TS7016: lo cazó el verificador
de la 2.18, y por eso están en la lista.) Node: **22 LTS, ≥22.22.2** (msw 3 y Vitest 5 piden 22; jsdom
30 avisa por debajo de la 22.22.2) o la **24, ≥24.15.0**.

**Licencias** (campo `license` de npm, 2026-10-21; criterio en `rules/licenses.md`): todo
`MIT`, salvo lucide-react `ISC`, TypeScript y Playwright `Apache-2.0`, y DOMPurify `MPL-2.0 OR
Apache-2.0` (se elige Apache-2.0). Ninguna obliga a nada al empaquetar o vender un frontend con ellas,
más allá de conservar su aviso de copyright.

**Lo que cambia al subir de mayor** (notas oficiales de cada versión, leídas el 2026-10-21):

- **MSW 2 → 3** (3.0.0, 28-09-2026). `server.listen({ onUnhandledRequest })` pasa a
  **`onUnhandledFrame`** — con la opción vieja `tsc` falla (TS2353, comprobado). Además: solo ESM,
  Node ≥22, TypeScript ≥5.9, en Node MSW ya no gestiona cookies y `request.headers.get('cookie')`
  devuelve `null` en todos los entornos (se usa el argumento `cookies` del resolver), y `graphql` se
  importa de `msw/graphql`.
- **Vitest 3 → 5** (5.0.0, 03-09-2026). Node 22 y Vite ≥6.4; los mocks se limpian solos antes de cada
  test; una aserción asíncrona sin `await` **hace fallar** el test (antes pasaba en verde sin comprobar
  nada); el fichero de configuración ya no se busca en las carpetas de arriba; los informes van a
  `.vitest/`.

**Por qué TypeScript 5 y no 7.** TypeScript 7.0.2 (08-07-2026) es el compilador nuevo: su `tsc`
comprueba este proyecto en verde. Pero su paquete npm ya no trae la API de JavaScript de siempre
(solo `unstable/*`), y hay herramientas del stack que la usan. Medido el 2026-10-21:

| Con… | `npm install` | `openapi-typescript` |
|---|---|---|
| `typescript@^7.0.2` | ✗ `ERESOLVE`: openapi-typescript 7.13.0 pide `typescript ^5.x` | ✗ forzando la instalación: `Cannot read properties of undefined (reading 'createKeywordTypeNode')` |
| `typescript@^6.0.3` | ✗ `ERESOLVE`, mismo motivo | ✓ forzando la instalación (y `tsc` en verde): la 6 aún trae la API |
| `typescript@^5.9.3` | ✓ | ✓ |

Con la 6 funciona, pero solo forzando: `--legacy-peer-deps` apaga la comprobación de *peers* de **todo**
el árbol, no solo la de este paquete, y eso es justo lo que caza una dependencia incompatible. Por eso se
queda la 5.9. typescript-eslint 8.72.0 pide además `typescript <6.1.0`. **Qué lo desbloquea:** que
openapi-typescript declare la 6 o la 7 en su `peerDependencies` (y typescript-eslint, la 7). Entonces se
sube aquí y en el comprobador.

**La forma de entrega decide el troceado del bundle, y se decide una vez en `vite.config.ts`.**
"Partir el paquete en trozos" no es una buena práctica que se aplique siempre: es una respuesta a
cómo se entrega ese frontend, y en el corpus hay tres entregas distintas con tres respuestas
distintas, todas coherentes:

| Entrega | Qué se hace | Dónde se ve |
|---|---|---|
| **Panel SPA con muchas pantallas** | Carga diferida **por ruta**, y la primera pantalla NO diferida (si no, se añade una espera justo donde el usuario ya está mirando) | `elvion/frontend/src/App.tsx:5-24` — 14 de 16 páginas con `lazy()`; `CockpitPage` (la de entrada) y `LoginPage`, directas |
| **Panel SPA pequeño** | Un solo paquete, sin diferir nada | `proxera_musa/frontend/admin/src/App.tsx:19-27` — 9 de 9 páginas directas |
| **Widget embebido en una web ajena** | **Prohibido** trocear: un único fichero IIFE con el CSS dentro, y un **presupuesto de tamaño** escrito | `proxera_musa/frontend/widget/vite.config.ts` — `inlineDynamicImports: true`, `cssCodeSplit: false`, *"target <250KB gzip"* · el patrón entero: `frontend-embeddable-widget.md` |

El caso del widget es el que explica la regla: si el fichero se embebe en la web de otro con una
línea de `<script>`, cada trozo extra sería otra petición desde un dominio que el navegador del
visitante no espera. Ahí el troceado no es una mejora, es un fallo.

> **Medido en el corpus (2026-08-22).** `manualChunks` —la receta habitual de "separa React y las
> librerías grandes en su propio trozo"— aparece **0 veces en los 3 `vite.config.ts`**:
>
> ```bash
> grep -c manualChunks .docs/resources/coding/{elvion/frontend,proxera_musa/frontend/admin,proxera_musa/frontend/widget}/vite.config.ts
> # → los tres a 0
> ```
>
> No se escribe como patrón de casa porque **no lo es**: repartir vendors a mano solo compensa
> cuando se ha medido antes qué pesa, y esa medición es de `bruno-perf-cop`. La carga diferida por
> ruta, en cambio, sí está en el canon y con su ejemplo: `rutas.md` §Implementación.
>
> **El presupuesto de tamaño no se escribe aquí, y es deliberado.** El único que existe en el corpus
> vive donde puede fallar: una skill del propio proyecto que lo comprueba con su número y su
> comando (`proxera_musa/.claude/skills/widget-embed-test/SKILL.md` §2 —
> `gzip -c dist/widget.js | wc -c`, falla por encima de 250 KB). Una cifra genérica en este
> documento sería inventada: 250 KB es el límite de *ese* widget embebido, no el de un panel
> interno. Lo que sí es del canon: **si hay presupuesto, se escribe con su comando y falla**; un
> número en un comentario no lo comprueba nadie.

**Por qué se fija todo esto y no se decide en cada proyecto.** No porque estas librerías sean las
mejores en abstracto —esa discusión no termina nunca— sino porque **el coste de decidir otra vez
supera la diferencia entre las opciones razonables**. Con el stack fijado, un agente empieza a
escribir en el minuto cero, los documentos de esta carpeta valen tal cual, y quien revisa reconoce
lo que lee. Cuando un proyecto tiene una razón de verdad para salirse, se sale: lo que no vale es
salirse por inercia y que nadie se entere.

## El antipatrón que sustituye

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.62.0",
    "swr": "^2.2.5",
    "react-hook-form": "^7.54.0",
    "formik": "^2.4.6",
    "zod": "^3.23.8",
    "yup": "^1.4.0"
  }
}
```

Un `package.json` así no es un accidente: es lo que pasa cuando cada persona (o cada agente) que
llega resuelve su problema con lo que ya conocía, y nadie borra lo anterior porque hay pantallas que
todavía lo usan. Lo que cuesta, en orden:

- **La revisión pierde el criterio.** Con dos librerías de formularios en el repo, "esto no sigue el
  patrón" deja de ser una frase con sentido: las dos formas tienen precedentes. La consistencia no
  se recupera sola, y el catálogo de esta carpeta queda sin autoridad.
- **Se paga dos veces el peso.** Tanto la persona que espera a que cargue la página como quien
  arregla el error de compilación cargan con las dos librerías, aunque cada pantalla use una.
- **La segunda nunca está tan bien montada.** La que se coló para salir del paso no tiene decidido
  cómo trata los errores del servidor, y ahí es donde reaparece el bug que el patrón ya había
  cerrado en la otra mitad del repo.
- **Zod 3 con React Hook Form 7 y resolvers nuevos** es la combinación que rompe sin decir nada
  claro: el mensaje de error habla de tipos incompatibles y no de versiones, y se pierde media
  mañana.

El otro antipatrón, más silencioso: **el proyecto se queda una mayor por detrás y nadie lo anota.**
Alguien copia el ejemplo de `api-y-errores.md`, escribe `isPending`, y en TanStack Query 4 ese campo
no existe — se llamaba `isLoading` y significaba otra cosa. El síntoma es una pantalla que nunca
sale del esqueleto de carga, y la causa está a tres capas de distancia.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only stack
python3 .claude/patterns/stack/pattern_check_frontend.py package.json
```

| id | estado | qué detecta |
|---|---|---|
| `fe-stack-canonico` | débil | una segunda librería en `package.json` para un papel que el canon ya asigna (Formik junto a React Hook Form, Yup junto a Zod, Jest junto a Vitest, **una suite de componentes con estilos propios** junto al patrón shadcn…) |
| `fe-version-mayor-del-canon` | débil | mayor distinta de la del canon (`react` se trata como **mínimo**; el resto, exacta) |

Las dos son **débiles a propósito**, y es la decisión más discutible de este documento. Bloquear un
`package.json` es bloquear también al proyecto que hereda código y no puede migrar hoy; y al llegar
a un repo existente estas dos reglas son justo las que más van a disparar, que es el caso que el
`README.md` de esta carpeta manda arrancar en `sombra`. Avisan, y la conversación la tiene una
persona.

El comprobador lee `dependencies`, `devDependencies` y `peerDependencies`, y compara por **nombre
exacto**: un paquete que solo esté ahí de forma indirecta (porque otro se lo trajo) no aparece en
esas listas y no se reporta.

**Lo que estas reglas NO comprueban, y conviene saberlo:**

- **Que la versión instalada sea la declarada.** `package.json` dice lo que se pidió; lo que hay
  instalado está en el fichero de bloqueo (`package-lock.json`, `pnpm-lock.yaml`). Comprobar eso
  exigiría leer un formato distinto por gestor de paquetes, y no se ha hecho. `npm ls zod` lo
  responde en un segundo.
- **Que la librería se use de verdad.** Una dependencia declarada y jamás importada no se detecta
  aquí; eso es trabajo de `depcheck` o `knip`, que ya existen y lo hacen mejor.
- **Que el paquete exista.** Un agente puede inventarse una dependencia que no está publicada
  (`rules/ai-assistant-risk.md` §slopsquatting). El comprobador da por bueno lo que lee; el gate que
  verifica existencia es `code-review-gate`.

## Excepciones legítimas

- **Un framework que ya trae su propio router** (Next.js, Remix, TanStack Start): ahí react-router
  sobra y la fila de rutas de este documento no aplica. El comprobador **no lo sabe** — no mira si
  hay `next` en las dependencias — así que en ese proyecto la exención se escribe una vez y se
  olvida.

  **Next ≥16.3 escribe en `AGENTS.md`, y en cada proyecto se decide si se le deja** (CL-D11, leído en
  la doc que trae `next@16.4.2`, `dist/docs/01-app/03-api-reference/05-config/01-next-config-js/agentRules.md`,
  y en su `generate-agent-files.js`, el 2026-10-21). Cuando `next dev` detecta un agente, crea o
  reescribe en `AGENTS.md` el bloque entre `<!-- BEGIN:nextjs-agent-rules -->` y
  `<!-- END:nextjs-agent-rules -->` (manda leer `node_modules/next/dist/docs/` antes de escribir código)
  y respeta el resto del fichero. Se apaga con `agentRules: false` en `next.config.ts`; desde la 16.4,
  el siguiente `next dev` **borra** el bloque (y el fichero, si no tenía nada más); en la 16.3 solo deja
  de escribirlo. `create-next-app --no-agents-md` no lo crea. **Si Claude Code lo lee depende del
  proyecto** (`claude-code-referencia` §1.2): con `CLAUDE.md`, `.claude/CLAUDE.md` o `CLAUDE.local.md`
  presente, `AGENTS.md` **no** se carga, salvo que el `CLAUDE.md` lo importe con `@AGENTS.md` —que es
  justo lo que escribía `create-next-app` 16.3; la 16.4.2 ya solo crea `AGENTS.md`— o que alguien haya
  puesto en `/config` las instrucciones de proyecto en `claude-md-and-agents-md`. La decisión, por
  proyecto:

  | El proyecto… | Qué se hace | Por qué |
  |---|---|---|
  | Tiene `.claude/CLAUDE.md` del template y **no** importa `@AGENTS.md` | `agentRules: false` | El bloque no llega a Claude y solo ensucia el árbol: un fichero que reescribe una herramienta en cada `next dev` |
  | Su `CLAUDE.md` importa `@AGENTS.md` | `agentRules: false` y la indicación útil, escrita **a mano** en su `CLAUDE.md`: «antes de escribir código de Next, lee la guía de `node_modules/next/dist/docs/` de la versión instalada». Y se quita el `@AGENTS.md` si el fichero no tenía nada más: desde la 16.4, Next lo **borra** y el import se queda apuntando a nada | Se conserva lo que aporta y deja de cambiar las instrucciones una herramienta sin que el TL lo vea (choca con `harness-gotchas.md` §Caché: una edición a mitad de sesión no rige hasta `/clear`) |
  | Se trabaja con Codex u otra herramienta que sí lee `AGENTS.md` | Se deja activo **y se commitea** el bloque | Es su fichero de instrucciones; el propio bloque pide commitearlo para que el árbol quede limpio |
- **Emotion o Sass que entran de la mano de otra cosa.** Material UI, por ejemplo, arrastra
  `@emotion/styled`: aparece como duplicado de Tailwind sin que nadie lo haya elegido. Es el falso
  positivo más probable de `fe-stack-canonico` y la razón principal de que sea débil.
- **Migración en curso.** Tener las dos librerías a la vez es exactamente lo que pasa mientras se
  migra de una a otra. La exención lleva la fecha y el ticket, para que se note cuando la migración
  lleva un año "en curso".
- **Una mayor por detrás con motivo.** Una dependencia de terceros que aún no soporta la nueva, por
  ejemplo. Se anota el motivo y qué la desbloquea.

```json
{
  "//": "pattern-exempt: fe-stack-canonico — @emotion/styled entra con MUI, no es una elección",
  "//2": "pattern-exempt: fe-version-mayor-del-canon — react-router 6 hasta cerrar el ticket #318"
}
```

El comprobador busca la marca `pattern-exempt: <id>` en cualquier parte del fichero, así que en
JSON —que no admite comentarios— sirve una clave falsa como estas. Como en el resto del catálogo:
una excepción sin razón escrita no es una excepción, es una desviación con permiso.

## Related

- `estilos.md` (Tailwind e iconos) · `rutas.md` (react-router 7) · `saneado.md` (DOMPurify)
- `estado.md` (TanStack Query y Zustand en uso) · `formularios.md` (React Hook Form y Zod en uso)
- `api-y-errores.md` (el cliente HTTP) · `tests.md` (los cuatro niveles de prueba)
- `frontend-design-system.md` (los tokens que consumen esos componentes) · `componentes.md`
- `frontend-contrato-con-el-backend.md` (`drf-spectacular` + `openapi-typescript`, las dos
  herramientas del contrato que no son del navegador, y §Paso 3b, el cliente tipado de la tabla)
- `ARRANQUE.md` §Versiones de arranque (el backend: Django 5.2 LTS, DRF y por qué no Ninja)
- `rules/ai-assistant-risk.md` §dependencias alucinadas · skill `code-review-gate`
