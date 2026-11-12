# A prueba de errores — qué IMPIDE equivocarse, no qué lo documenta

> No es una capa más del catálogo: es el eje que atraviesa a todas. Dice **dónde se para** cada
> error del patrón de frontend —si es imposible cometerlo, si lo marca el editor mientras escribes,
> o si solo lo caza el comprobador cuando ya está escrito— y qué piezas de código suben una regla
> de nivel.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --niveles`.

## La regla (una frase)

Un error que sale caro no se documenta: **se hace imposible**; cada regla del catálogo declara en
qué nivel se para hoy, y solo se sube de nivel la que duele —porque subir cuesta escribir una pieza
y conseguir que se use.

## Los tres niveles

| Nivel | Dónde se para el error | Cuándo te enteras | Qué cuesta |
|---|---|---|---|
| **1 · imposible** | La estructura no deja cometerlo: si usas la pieza del patrón, el error no existe | Nunca ocurre | Escribir la pieza una vez y que la gente la adopte |
| **2 · al escribir** | El compilador o el linter lo marcan en el editor | En el segundo siguiente, con el fichero abierto | Configurar el linter una vez |
| **3 · en el gate** | El comprobador lo caza al pasar el gate | Cuando ya está escrito, a veces al día siguiente | Nada — es el default |

**Por qué la diferencia importa tanto con agentes trabajando de noche.** Una regla de nivel 3
significa que el agente escribió mal, el gate lo cazó, y por la mañana hay trabajo pendiente que
alguien tiene que entender y rehacer. Una de nivel 1 significa que no pasó. El mismo error, la misma
regla escrita en el mismo sitio, y la mañana siguiente es distinta.

Los tres niveles **no se sustituyen, se acumulan**: la regla del comprobador sigue existiendo aunque
haya una pieza de nivel 1, porque nada obliga a usar la pieza. Es defensa en profundidad, no un
reemplazo — y por eso `--niveles` dice "5 reglas **en** nivel 1", no "5 reglas retiradas".

## Las piezas de nivel 1 — el código que hace el error imposible

Cinco piezas, todas pequeñas, todas en el proyecto derivado. Cada una cierra un error concreto que
hoy solo se caza en el gate. **Ninguna es obligatoria**: son la versión del patrón que además
impide equivocarse, y el catálogo acepta las dos formas (el comprobador reconoce las piezas y no
las marca — ver §Cómo se comprueba).

### 1. `request()` — el timeout va dentro, no en la llamada

Ya existe (`api-y-errores.md`), y es el ejemplo más claro de qué significa nivel 1: **quien usa
`request()` no puede olvidar el timeout porque no lo escribe**. El día que alguien llama a `fetch`
directamente, vuelve al nivel 3 y lo caza `fe-timeout-obligatorio`. La pieza no elimina la regla:
elimina la ocasión.

### 2. `<Asincrono>` — no compila sin el estado de carga y el de error

El error que cierra: la pantalla que se queda en blanco cuando el backend falla. Hoy lo caza
`fe-tres-estados` **después** de escribir el componente. La pieza lo cierra antes, y el mecanismo es
solo TypeScript: los dos renderers son **props obligatorias**, así que olvidarlos no compila.

```tsx
// src/components/Asincrono.tsx
import type { UseQueryResult } from '@tanstack/react-query';
import type { ReactNode } from 'react';

export interface AsincronoProps<T> {
  query: UseQueryResult<T>;
  cargando: ReactNode;                    // obligatoria: no hay default
  error: (mensaje: string) => ReactNode;  // obligatoria: no hay default
  vacio?: ReactNode;                      // opcional: no toda lista necesita mensaje
  children: (datos: T) => ReactNode;
}

export function Asincrono<T>({ query, cargando, error, vacio, children }: AsincronoProps<T>) {
  if (query.isPending) return <>{cargando}</>;
  if (query.isError) return <>{error(toUserMessage(query.error))}</>;
  if (vacio && Array.isArray(query.data) && query.data.length === 0) return <>{vacio}</>;
  return <>{children(query.data)}</>;
}
```

```tsx
// ✅ el consumidor: no puede olvidarse de nada, y `datos` llega ya estrechado (sin `?.` ni `!`)
<Asincrono
  query={useOrders()}
  cargando={<ListSkeleton rows={5} />}
  error={(m) => <ErrorState message={m} />}
  vacio={<EmptyState title="Aún no hay pedidos" />}
>
  {(orders) => <ul>{orders.map((o) => <li key={o.id}>{o.reference}</li>)}</ul>}
</Asincrono>
```

Lo que gana además del compilador: el mensaje de error pasa **siempre** por `toUserMessage()`, así
que `fe-error-traducido` también deja de tener ocasión de dispararse.

**Lo que cuesta, dicho claro:** un render-prop se lee peor que tres `if` seguidos, y quien no lo
haya visto antes tarda un minuto en entenderlo. Las tres guardas en línea que enseña
`api-y-errores.md` **siguen siendo patrón de casa y correctas**; esta pieza es para el proyecto que
prefiere pagar ese minuto una vez a cambio de que el hueco en blanco no pueda existir.

### 3. `<BotonDeEnvio>` — el doble clic no llega a ser posible

El error que cierra: dos POST por un doble clic —dos pedidos, dos cargos—. Lo caza hoy
`fe-submit-bloqueado`. La pieza deriva el `disabled` del estado de la mutación **por dentro** y no
acepta que se lo pasen: el tipo excluye la prop.

```tsx
// src/components/BotonDeEnvio.tsx
type PropsDeBoton = Omit<React.ComponentProps<'button'>, 'disabled' | 'type'>;

export interface BotonDeEnvioProps extends PropsDeBoton {
  enviando: boolean;   // `mutation.isPending` — es lo único que hay que pasarle
  children: ReactNode;
}

export function BotonDeEnvio({ enviando, children, ...resto }: BotonDeEnvioProps) {
  return (
    <button {...resto} type="submit" disabled={enviando} aria-busy={enviando}>
      {enviando ? 'Enviando…' : children}
    </button>
  );
}
```

`Omit<…, 'disabled'>` es lo que hace el trabajo: pasarle `disabled` **es un error de tipos**, así
que nadie puede "arreglar" el botón desactivando su propia protección. El `aria-busy` va de regalo y
cierra media queja de accesibilidad.

### 4. `recursoApi()` — la clave de caché no se puede inventar

El error que cierra: el usuario crea algo, la petición va bien, y la lista sigue mostrando lo de
antes porque alguien invalidó `['orders']` donde la query usaba `['orders', 'list']`. Hoy
`fe-mutacion-invalida-cache` comprueba **que** se invalida, no **con qué clave** — y la clave
inventada es justo el bug que queda vivo.

```ts
// src/api/recurso.ts — la fábrica: se escribe una vez en el proyecto
export function recursoApi<T, Nuevo>(nombre: string, ruta: string) {
  const keys = { todos: [nombre] as const, uno: (id: string) => [nombre, id] as const };
  return {
    keys,
    listar: () => request<T[]>(ruta),
    crear: (input: Nuevo) => request<T>(ruta, { method: 'POST', body: JSON.stringify(input) }),
  };
}

// src/api/orders.ts — un recurso: tres líneas
import type { components } from '../types/api';           // tipos generados: frontend-contrato-con-el-backend.md
type Order = components['schemas']['Order'];
export const ordersApi = recursoApi<Order, Omit<Order, 'id'>>('orders', '/orders/');
```

```ts
// ✅ la clave sale de la fábrica; una inventada no existe en el tipo y no compila
queryClient.invalidateQueries({ queryKey: ordersApi.keys.todos });
```

El `as const` es lo que hace que la clave sea un tipo concreto y no `string[]`. Sin él, cualquier
array de textos encaja y volvemos al principio.

### 5. La cookie `HttpOnly` — quitar el dato de en medio

La más limpia de las cinco, porque no añade nada: **quita**. El token en cookie `HttpOnly`
(`frontend-auth.md`) **no llega nunca a JavaScript**, así que no puede acabar en `localStorage` ni
salir en un XSS. Cierra `fe-token-no-en-localstorage` sin que haya nada que recordar.

> **El siguiente candidato, y hoy NO está en el catálogo:** un **registro de rutas tipado**
> (`config/paths.ts` con `path` + `getHref(params)`), donde navegar a una ruta que no existe sea un
> error de tipos en vez de una cadena mal escrita que falla en ejecución. La arquitectura de
> referencia lo tiene y es de lo más barato que se puede copiar. `rutas.md` hoy exige un **módulo
> único** de rutas —que es otra cosa— y `fe-rutas-en-un-sitio` solo detecta `<Route>` sueltos fuera
> de él. Se anota aquí como deuda declarada para no dar por hecha una pieza que nadie ha escrito.

## El antipatrón que sustituye

```tsx
// ❌ el aviso en prosa, que es lo que había antes de esta página
// IMPORTANTE: acuérdate SIEMPRE de poner disabled mientras la mutación está en curso.
// (y tres pantallas más abajo, alguien con prisa)
<button type="submit">Guardar</button>
```

Un comentario en mayúsculas no es un mecanismo: es una petición. Lo que duele exactamente:

- **Escala al revés.** Cada regla nueva escrita como aviso compite por la atención de quien lee, y
  la número quince hace que las catorce anteriores se lean peor. Una pieza de nivel 1 no consume
  atención: se usa y ya.
- **El agente no la incumple por rebeldía**, sino porque a las 3 de la mañana está resolviendo otra
  cosa y esa frase quedó tres ficheros atrás. La prop obligatoria, en cambio, está en su cara.
- **Y el que más cuesta**: subir el tono no cambia nada. `rules/layer-decision.md` lo dice para el
  harness y aquí vale igual — si una norma escrita se incumple, no se reescribe más fuerte, se baja
  de capa.

## Cuándo se sube una regla de nivel (y cuándo no)

Subir de 3 a 1 cuesta escribir la pieza, documentarla y conseguir que se adopte. Se hace **solo**
cuando el incumplimiento sale caro. En frontend, "caro" es esto:

| Se sube | Por qué duele | Pieza |
|---|---|---|
| Doble envío en algo que cobra o crea | Dos cargos al mismo cliente; se descubre por reclamación | `<BotonDeEnvio>` |
| Pantalla en blanco cuando el backend falla | El usuario no distingue "no tienes nada" de "está roto", y abandona | `<Asincrono>` |
| Sesión que sobrevive al logout | En un ordenador compartido, el siguiente ve datos del anterior | cookie `HttpOnly` + `queryClient.clear()` |
| Petición sin timeout | Esqueleto de carga eterno, sin error y sin nada que reintentar | `request()` |

**No se sube** lo que es cuestión de gusto o de orden (nombres, longitud de fichero, orden de
imports): ahí el nivel 3 sobra y de hecho la mayoría de esas reglas son débiles a propósito.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --niveles   # las reglas por nivel
python3 .claude/patterns/stack/pattern_check_frontend.py --list      # nivel en la columna nN
```

La tabla de niveles **vive en el comprobador** (`NIVEL_DE_ERROR`), no en este documento: aquí se
explica el criterio y allí está el dato. Así no hay dos listas que sincronizar, y el `--self-test`
avisa si alguien renombra una regla y deja la tabla apuntando a un id que ya no existe.

**El comprobador reconoce las piezas de nivel 1** y no las marca — importa, porque lo contrario
sería castigar la forma más segura de escribir:

| Regla | Además de lo suyo, acepta |
|---|---|
| `fe-tres-estados` | un componente que usa `<Asincrono>` (los dos renderers son obligatorios en el tipo) |
| `fe-submit-bloqueado` | un formulario que usa `<BotonDeEnvio>` (el `disabled` lo pone la pieza) |

**Lo que NO se comprueba, y es la mitad honesta de esta página:**

- **Que las piezas se usen.** Nada obliga a llamar a `<Asincrono>` en vez de escribir tres `if`;
  lo único que sabe el comprobador es que, si están, los estados están cubiertos. El nivel 1 reduce
  la ocasión de error, no la posibilidad.
- **Que la pieza esté bien escrita en el proyecto.** El comprobador reconoce el nombre, no audita la
  implementación: un `<Asincrono>` que ignore su prop `error` pasaría. Eso lo ve una revisión, o un
  test de la pieza —que es exactamente el tipo de test que sí merece la pena escribir una vez.
- **El nivel 2 no lo verifica nadie desde aquí.** Que ESLint tenga puesta la regla que dice la tabla
  es responsabilidad del proyecto; este comprobador no lee `.eslintrc`. La columna de nivel 2 dice
  *qué configurar*, no *que esté configurado*.

## Excepciones legítimas

- **Proyecto que hereda código** y no puede adoptar las piezas hoy: se queda en nivel 3, que es el
  default y funciona. Esta página no obliga a nada; describe a dónde llegar.
- **Pantalla de diagnóstico o interna** donde el estado de error crudo es el objetivo: se usa la
  forma en línea con su exención escrita, como en el resto del catálogo.
- **Un componente que de verdad no puede fallar** (datos ya en caché por un loader de ruta, sin red
  de por medio): no necesita `<Asincrono>`; necesita no llamar a `useQuery`.

## Related

- `api-y-errores.md` (los tres estados en línea, el cliente único y el timeout) ·
  `formularios.md` (`fe-submit-bloqueado`) · `rutas.md` (el registro de rutas) ·
  `frontend-auth.md` (la cookie y el vaciado de caché)
- `frontend-nueva-pantalla.md` — el molde que usa estas piezas ya montadas
- `rules/layer-decision.md` — el mismo criterio aplicado al harness: si se ignora, baja de capa
- `README.md` de esta carpeta — estados `activo/débil/sombra`, que son otra cosa: el estado dice
  **si bloquea**, el nivel dice **cuándo se entera**
