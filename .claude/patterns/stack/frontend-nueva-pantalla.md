# Una pantalla nueva no se empieza de cero — el molde

> El documento que atraviesa todas las capas. Los demás dicen cómo debe ser **cada** capa; este dice
> **cómo se atraviesan de una vez** para añadir una pantalla: qué ficheros son, cuáles se copian tal
> cual y cuáles se rellenan. Lo automatiza la skill `/nueva-pantalla`.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src`.

## La regla (una frase)

Una pantalla CRUD estándar **sale de un molde**: se declara el recurso y sus campos una vez, y el
resto se copia de una plantilla verificada — de modo que cambiar algo después toque **un** sitio y
no diez.

## El problema que resuelve

Hoy una pantalla nueva son ~10 ficheros escritos a mano: tipos, cliente de API, esquema, hooks,
lista, formulario, página, ruta, test y handlers de prueba. **Cada uno correcto por separado** —el
catálogo explica bien cada capa— y aun así tres pantallas del mismo proyecto acaban distintas,
porque nadie compone las capas igual dos veces. Con un agente escribiéndolas de noche, no acaban
distintas: acaban distintas **y nadie lo vio**.

El molde no es burocracia: es lo que hace que la pantalla **N+1 sea barata**. Y es el mecanismo más
eficaz para que el patrón se cumpla, porque el código **nace** conforme en vez de corregirse después.

## El molde — los 10 ficheros

Ejemplo con el recurso `pedidos` (`Order`). Lo que va entre `<>` es lo único que cambia de una
pantalla a otra.

```
src/
├── types/order.ts                                  ① alias sobre los tipos GENERADOS
├── api/orders.ts                                   ② fetchers + claves de caché
├── features/orders/
│   ├── schemas/orderForm.ts                        ③ el esquema zod del formulario
│   ├── hooks/useOrders.ts                          ④ las queries y mutaciones de la feature
│   └── components/
│       ├── OrderList.tsx                           ⑤ la lista, con los tres estados
│       ├── OrderForm.tsx                           ⑥ el formulario, con errores de campo
│       └── OrderList.test.tsx                      ⑦ el test de integración
├── pages/OrdersPage.tsx                            ⑧ compone; no implementa
├── routes.tsx                                      ⑨ UNA línea nueva (fichero compartido)
└── testing/handlers/orders.ts                      ⑩ los handlers de MSW
```

### Qué se copia y qué se rellena

**La columna de la derecha es todo el trabajo real.** Si en una pantalla nueva estás escribiendo
algo que no está en esa columna, o el molde se queda corto (dilo) o te estás saliendo de él.

| # | Fichero | De dónde sale | Qué se rellena |
|---|---|---|---|
| ① | `types/<recurso>.ts` | copiado | el nombre del esquema generado: `components['schemas']['Order']` |
| ② | `api/<recursos>.ts` | copiado — es una llamada a `recursoApi()` | nombre y ruta del recurso |
| ③ | `schemas/<recurso>Form.ts` | copiado | **los campos y sus mensajes** ← el trabajo de verdad |
| ④ | `hooks/use<Recursos>.ts` | copiado tal cual | nada |
| ⑤ | `components/<Recurso>List.tsx` | copiado | **las columnas** y el texto del estado vacío |
| ⑥ | `components/<Recurso>Form.tsx` | copiado | los campos, en el mismo orden que ③ |
| ⑦ | `components/<Recurso>List.test.tsx` | copiado | un dato de ejemplo y el texto que se busca |
| ⑧ | `pages/<Recursos>Page.tsx` | copiado tal cual | el título |
| ⑨ | `routes.tsx` | **una línea** | la ruta y el nombre de la página |
| ⑩ | `testing/handlers/<recursos>.ts` | copiado | los mismos datos de ejemplo de ⑦ |

> **Proyecto nuevo con el cliente tipado** (default desde el 2026-10-21, `frontend-contrato-con-el-backend.md`
> §Paso 3b): ② y ④ no usan `recursoApi()` sino `$api.useQuery('get', '/api/<recursos>/')` y
> `$api.useMutation(…)`, con las claves de caché que pone openapi-react-query. Este molde, y la skill
> `nueva-pantalla` que lo genera, siguen sobre `recursoApi()` hasta que se adapten: en ese proyecto,
> esos dos ficheros se escriben a mano con `$api`.

> **De dónde salen los colores y los espaciados.** De ningún sitio de este molde: de **el origen de
> tokens del proyecto**. Los componentes que se copian usan las clases del sistema de diseño, nunca
> un color escrito a mano — y eso no depende de la buena voluntad: la regla `fe-color-por-token`
> está **activa** en el comprobador y falla si aparece un `#hex` o un `rgb()` dentro de un
> componente, y `fe-origen-de-tokens` avisa si el proyecto no ha declarado su origen único.
> El procedimiento para declararlo está en `frontend-design-system.md`, y el documento fundacional
> del proyecto vive en `.docs/core/design-system.md`. Si al rellenar el molde te falta un valor,
> **se añade al origen de tokens**, no al componente.

Tres cosas se rellenan de verdad —**el recurso, los campos y las columnas**—; el resto se deriva.

### El molde, fichero a fichero

```ts
// ② src/api/orders.ts — dos líneas: la fábrica pone las claves y los fetchers
import type { Order, OrderNuevo } from '../types/order';
export const ordersApi = recursoApi<Order, OrderNuevo>('orders', '/orders/');
```

```ts
// ③ src/features/orders/schemas/orderForm.ts — AQUÍ se piensa
import { z } from 'zod';

export const orderFormSchema = z.object({
  reference: z.string().min(1, 'La referencia es obligatoria'),
  amount: z.coerce.number().positive('El importe tiene que ser mayor que cero'),
});
export type OrderFormValues = z.infer<typeof orderFormSchema>;
```

```ts
// ④ src/features/orders/hooks/useOrders.ts — copiado tal cual, cambia el nombre y nada más
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ordersApi } from '../../../api/orders';

export const useOrders = () =>
  useQuery({ queryKey: ordersApi.keys.todos, queryFn: ordersApi.listar });

export function useCrearOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ordersApi.crear,
    // la clave sale de la fábrica: inventarse otra no compila
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ordersApi.keys.todos }),
  });
}
```

```tsx
// ⑤ src/features/orders/components/OrderList.tsx — los tres estados vienen dados por <Asincrono>
export function OrderList({ onSelect }: OrderListProps) {
  return (
    <Asincrono
      query={useOrders()}
      cargando={<ListSkeleton rows={5} />}
      error={(m) => <ErrorState message={m} />}
      vacio={<EmptyState title="Aún no hay pedidos" />}
    >
      {(orders) => (
        <ul>
          {orders.map((order) => (                       {/* ← las columnas: lo que se rellena */}
            <li key={order.id}>
              <button type="button" onClick={() => onSelect(order.id)}>{order.reference}</button>
            </li>
          ))}
        </ul>
      )}
    </Asincrono>
  );
}
```

```tsx
// ⑥ src/features/orders/components/OrderForm.tsx — el 400 del backend se mapea a los campos
const form = useForm<OrderFormValues>({ resolver: zodResolver(orderFormSchema) });
const crear = useCrearOrder();

const onSubmit = form.handleSubmit(async (values) => {
  try {
    await crear.mutateAsync(values);
    onDone();
  } catch (e) {
    if (e instanceof ApiError) aplicarErroresDeCampo(e, form.setError);   // formularios.md
    else throw e;
  }
});

return (
  <form onSubmit={onSubmit} noValidate>
    {/* … los campos, en el mismo orden que el esquema … */}
    <BotonDeEnvio enviando={crear.isPending}>Guardar</BotonDeEnvio>
  </form>
);
```

`<Asincrono>` y `<BotonDeEnvio>` son las piezas de **nivel 1** de
[`frontend-a-prueba-de-errores.md`](frontend-a-prueba-de-errores.md): con ellas, olvidar el estado
de error o dejar pasar un doble clic **no compila**. Se escriben una vez por proyecto, no por
pantalla — el molde solo las usa.

### La única línea que toca un fichero compartido

```tsx
// ⑨ src/routes.tsx
{ path: 'orders', lazy: () => import('./pages/OrdersPage') },
```

`routes.tsx` lo tocan todas las pantallas, así que es el fichero donde dos frentes en paralelo se
pisan. Regla de `rules/parallelization.md` §file claims: **dueño único** — si hay dos personas o dos
agentes trabajando a la vez, uno lo edita y el otro le pide la línea.

## El otro lado: qué espera este molde del backend

Una pantalla es de punta a punta, y la mitad de atrás tiene su propio molde en el catálogo de
backend. El frontend da por hecho que existe:

| Necesita | Documento |
|---|---|
| El modelo y su migración | `backend-modelos.md` |
| El serializer (y su anotación si hay campos calculados) | `backend-serializers.md` · `frontend-contrato-con-el-backend.md` |
| El servicio con la lógica | `backend-servicios.md` |
| La vista con permisos y filtro por dueño | `backend-vistas.md` |
| El `schema.yml` regenerado | `frontend-contrato-con-el-backend.md` §paso 1 |

**El orden importa**: primero el backend, luego `npm run api:types`, y solo entonces el frontend.
Al revés se escriben los tipos a mano "provisionalmente" y ese provisional se queda.

## El límite del molde (no negociable)

**El molde cubre el caso estándar: CRUD sobre una entidad, con permisos y filtros. No cubre la
pantalla rara.** Un panel con tres orígenes de datos, un asistente de cinco pasos o un editor
gráfico se escriben a mano, y está bien: siguen el patrón capa por capa como siempre.

Ampliar el molde para cubrirlo todo es exactamente cómo se acaba en la metaprogramación de 944
líneas que `REF-8` dice **no** copiar de la referencia: un generador que lo intenta todo produce
código que nadie entiende y que solo su autor sabe modificar. Si una pantalla se sale del molde en
tres sitios, es que no era del molde.

## El antipatrón que sustituye

No es un bloque de código: es una forma de trabajar. «Copio la pantalla que más se parezca y voy
cambiando cosas.»

- **Se arrastra lo que sobra.** Un `useEffect` que existía por un motivo de la pantalla original y
  aquí no significa nada. Nadie lo quita, porque quitar algo que no entiendes da más miedo que
  dejarlo.
- **Se pierde lo que no se ve.** La pantalla copiada tenía estado vacío y la nueva no, porque el
  hueco solo aparecía con la lista sin datos y nadie la probó vacía.
- **Y a la tercera copia hay tres formas de listar una tabla.** Ninguna está mal. Y a partir de ahí
  «esto no sigue el patrón» deja de ser una frase con sentido, porque las tres tienen precedente en
  el repo.

## Cómo se comprueba

```bash
# lo generado tiene que pasar el catálogo entero, sin exenciones
python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src
```

| id | estado | ámbito | qué detecta |
|---|---|---|---|
| `fe-feature-con-test` | débil | **proyecto** | una carpeta `src/features/<x>/` con componentes y **ningún** `*.test.tsx` dentro |

Esa es la única señal mecánica que existe de que alguien escribió una pantalla a mano saltándose el
molde: el molde siempre genera el test, así que una feature entera sin uno es casi siempre eso. Es
débil porque hay proyectos que prueban desde `src/pages/`, y ahí sería un falso positivo.

**Lo que NO se comprueba, y hay que decirlo:** *no existe una regla que verifique que una pantalla
salió del molde.* No es una carencia del comprobador, es que no hay nada observable que distinguir:
código bien escrito a mano y código generado son idénticos — y deben serlo. Lo que sí se comprueba
es **el resultado**: las 44 reglas del catálogo corren sobre lo generado igual que sobre lo escrito,
y el molde está construido para pasarlas todas. Si una pantalla generada dispara una regla, el fallo
es del molde y se arregla ahí, no en la pantalla.

## La skill `/nueva-pantalla`

Lo automatiza `.claude/skills/nueva-pantalla/`, que pregunta el recurso y los campos, escribe los 10
ficheros y corre el comprobador sobre lo escrito.

**Alcance de hoy, explícito:** genera **la feature de frontend completa**. Del backend imprime la
lista de ficheros que hacen falta y verifica que el `schema.yml` esté regenerado, pero **no los
escribe**: el molde de backend (`REF-2`/`REF-3`, punto único de filtrado y mixins de modelo) aún no
existe, y generar contra un molde que no está escrito produce código que habrá que rehacer. Cuando
esté, el generador se ata a él y la pantalla sale de punta a punta con un comando.

## Related

- `frontend-a-prueba-de-errores.md` — `<Asincrono>`, `<BotonDeEnvio>`, `recursoApi()`: las piezas
- `frontend-contrato-con-el-backend.md` — de dónde salen los tipos del paso ①
- `componentes.md` (el árbol y la regla de promoción) · `api-y-errores.md` · `formularios.md` ·
  `estado.md` · `rutas.md` · `tests.md` — cada capa por separado
- `rules/parallelization.md` §file claims — por qué `routes.tsx` tiene dueño único
