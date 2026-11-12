# Estructura de tests — patrón de casa

> Capa `tests` del patrón de casa (Vitest · Testing Library · MSW · Playwright).
> **El E2E no se define aquí**: su estabilidad, sus selectores y su estado inicial son
> `rules/verification.md` §Estabilidad E2E. Este documento define los **niveles** —qué se prueba en cada uno y
> dónde está la frontera— y las reglas del nivel unitario/integración.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only tests`.

## La regla (una frase)

Cada test vive en el nivel más barato que puede demostrar lo que afirma, se escribe contra lo que
el usuario percibe (rol y etiqueta, no `data-testid` ni clases) y sustituye la red en el
**boundary**, nunca el módulo que la envuelve.

## Implementación de referencia

**Los tres niveles y su frontera.** Lo que decide el nivel no es el tamaño del código probado, es
*qué se está afirmando*:

| Nivel | Afirma | Herramienta | Frontera dura |
|---|---|---|---|
| **Unitario** | una función pura, un esquema zod, un reducer | Vitest, sin DOM | no monta componentes |
| **Integración** | un componente hace lo que promete, con su red simulada | Testing Library + MSW | **sin navegador** |
| **E2E** | un flujo crítico completo funciona de verdad | Playwright | **el único que abre navegador** |

La frontera que importa es la de en medio: **un test de integración no abre navegador y un E2E no
usa `render()`**. En cuanto se cruzan, se acaba con E2E lentos que prueban lógica de un `if`, y
con tests de integración que arrastran un navegador (y, en este servidor, cuentan doble en RAM —
`rules/ram-pytest.md`).

La proporción que se busca es la clásica: muchos unitarios, bastantes de integración y **solo los
flujos críticos en E2E** (login, el camino feliz del núcleo, el que cobra). No es una cuota que
nadie mida; es la consecuencia de aplicar la tabla de arriba honestamente.

**Un test de integración de casa:**

```tsx
import { render, screen } from '@testing-library/react';
import { server } from '../../tests/msw/server';
import { OrderList } from './OrderList';

test('muestra el estado vacío cuando no hay pedidos', async () => {
  server.use(mockOrders([]));
  render(<OrderList />, { wrapper: QueryWrapper });
  expect(await screen.findByText('Aún no hay pedidos')).toBeVisible();
});
```

**Cómo se busca en el DOM.** La prioridad es la de Testing Library, y no es arbitraria: cuanto más
arriba, más se parece la consulta a cómo encuentra el elemento una persona real.

```
getByRole(…, { name }) ▸ getByLabelText ▸ getByPlaceholderText ▸ getByText ▸ getByDisplayValue
                                                                        ▸ getByTestId (último recurso)
```

`getByRole('button', { name: 'Guardar' })` falla si el botón pierde su nombre accesible — que es
exactamente el bug que quieres que falle. `getByTestId` pasaría igual con el botón roto para un
lector de pantalla.

**El `data-testid` es del E2E, no del unitario.** No es una contradicción con
`rules/verification.md` §E2E-2, que lo exige como selector estable: son dos contratos distintos. El
E2E corre contra la app compilada, no conoce el árbol de componentes y necesita un ancla que
sobreviva a los rediseños. El test de integración renderiza el componente él mismo, tiene acceso al
árbol accesible y no necesita el ancla — si la usa, se está saltando la única comprobación gratis
de accesibilidad que tiene.

**La red se simula en el boundary** con MSW, en `tests/msw/handlers.ts`, y los mismos handlers
sirven al navegador en desarrollo.

## El antipatrón que sustituye

```tsx
// ❌ src/components/Widget.test.tsx
vi.mock('../api/orders');

test('renders', async () => {
  const { container } = render(<Widget />);
  expect(container.querySelector('.title')).toBeTruthy();
  expect(screen.getByTestId('widget-root')).toBeVisible();
  await new Promise((r) => setTimeout(r, 500));
  expect(container).toMatchSnapshot();
});
```

- **`vi.mock('../api/orders')`** sustituye justo el código que más falla. Todo lo que ocurre entre
  el componente y el servidor —serializar el cuerpo, el status, la forma del error, el 400 con sus
  campos— queda sin probar, y el test sigue verde cuando el backend cambia el contrato. Con MSW se
  intercepta la petición HTTP: el cliente real corre y el fallo aparece.
- **`container.querySelector('.title')`** ata el test a una clase de presentación. Renombrar una
  clase de Tailwind rompe un test que no tenía nada que ver con el estilo, y el equipo aprende a
  arreglar tests en vez de a confiar en ellos.
- **`setTimeout(500)`** hace el test lento *y* frágil a la vez: medio segundo perdido en cada
  ejecución y rojo intermitente el día que el CI va cargado. `findBy*` espera por la condición y
  vuelve en cuanto se cumple.
- **`toMatchSnapshot()`** no afirma nada: falla con cualquier cambio, incluido el correcto, y el
  reflejo aprendido es `-u` sin leer el diff. Un test que siempre se acepta es un test que no
  existe.
- **`test('renders')`** no dice qué debería pasar, así que cuando falle nadie sabrá si el fallo
  importa.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only tests
```

| id | estado | qué detecta |
|---|---|---|
| `fe-nivel-del-test` | activo | `page.goto`/`@playwright` en un test unitario, o `@testing-library/react` dentro de `e2e/` |
| `fe-consulta-por-rol` | activo | `*ByTestId` o `container.querySelector` en un test que no es E2E |
| `fe-red-en-el-boundary` | activo | `vi.mock`/`jest.mock` de una ruta que contiene `api` o `services` |
| `fe-sin-snapshot-de-componente` | activo | `toMatchSnapshot(` |
| `fe-sin-espera-por-tiempo` | activo | `setTimeout(`, `sleep(`, `waitForTimeout(` en un test |

`fe-nivel-del-test` es la regla que hace ejecutable la tabla de niveles: sin ella, "cada test en su
nivel" sería una buena intención. Clasifica por ruta y nombre (`*.test.*`/`*.spec.*`, y `e2e/` o
`playwright` en la ruta), así que la convención de nombres es parte del contrato.

Refuerzo en ESLint con `eslint-plugin-testing-library`, que ve el AST y por tanto es más fino:
`testing-library/no-container`, `testing-library/no-node-access`,
`testing-library/prefer-screen-queries` y `testing-library/await-async-queries` (esta última caza
el `findBy*` sin `await`, que produce un test verde que no comprueba nada — no lo cubre el checker).

## Excepciones legítimas

- **Canvas, mapas, editores enriquecidos y librerías de terceros sin roles accesibles**: no hay rol
  ni etiqueta a la que agarrarse, y `getByTestId` es la respuesta correcta.
- **Snapshots de datos**, no de componentes: el resultado de un serializador o de un formateador en
  un `.toMatchInlineSnapshot()` corto y legible en el propio test es útil. Lo prohibido es
  fotografiar árboles de DOM enteros.
- **Test de rendimiento o de temporizadores** que necesita tiempo real. Antes de exceptuar,
  comprueba si `vi.useFakeTimers()` resuelve el caso — casi siempre lo hace, y sin coste.
- **Mockear el módulo de API** cuando lo que se prueba es precisamente el manejo de un fallo que
  MSW no puede producir (un `AbortError` de timeout, por ejemplo).

```tsx
// pattern-exempt: fe-consulta-por-rol — el canvas de Mapbox no expone roles; testid es el único ancla
```
