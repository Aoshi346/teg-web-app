# Estado — patrón de casa

> Capa `estado` del patrón de casa (React · TypeScript). El error más común del frontend no es
> elegir mal la librería de estado: es **meter en ella cosas que no son estado**.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only estado`.

## La regla (una frase)

Antes de crear estado, decide de quién es el dato: **si vive en el servidor es caché de queries, si
se puede calcular no es estado, y solo lo que queda —estado de UI que de verdad se comparte— entra
en el store global**.

## Implementación de referencia

La decisión completa cabe en cuatro filas. Se recorren **en orden** y se para en la primera que
aplica:

| ¿De dónde sale el dato? | Dónde vive | Herramienta |
|---|---|---|
| Del servidor | caché de queries | `useQuery` / `useMutation` |
| Se deriva de props o de otro estado | de ningún sitio: se calcula al renderizar | una `const` (o `useMemo` si mide caro) |
| Es de UI y lo usa **un** subárbol | local | `useState` en el componente que lo posee |
| Es de UI y lo comparten ramas lejanas | global | store (Zustand) |

**Estado de servidor** — lo pide quien lo pinta, sin pasar por ningún store:

```tsx
const { isPending, isError, error, data } = useQuery({
  queryKey: orderKeys.all,
  queryFn: ordersApi.list,
});
```

**Estado derivado** — se calcula, no se guarda:

```tsx
// ✅ una línea, siempre coherente, cero renders extra
const pendientes = orders.filter((o) => o.status === 'pending');
const total = pendientes.reduce((sum, o) => sum + o.amount, 0);
```

**Estado de UI global** — pequeño, plano y sin nada del servidor dentro:

```ts
import { create } from 'zustand';

interface UiState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
```

El store no importa nada de React. Esa restricción no es estética: es lo que permite testear la
lógica de estado sin montar un componente, y lo que impide que el store acabe conteniendo efectos.

## El antipatrón que sustituye

**El store que se convierte en una base de datos peor.** Es la forma número uno de este error:

```ts
// ❌ src/stores/dataStore.ts
export const useDataStore = create((set) => ({
  orders: [],
  isLoading: false,
  load: async () => {
    set({ isLoading: true });
    const res = await fetch('/api/orders');
    set({ orders: await res.json(), isLoading: false });
  },
}));
```

Parece razonable y por eso se repite. Lo que se está construyendo, sin decirlo, es una caché — y
todo lo que una caché necesita hay que escribirlo a mano y nadie lo escribe: no se invalida (tras
crear un pedido, la lista miente hasta que alguien recarga), no se deduplica (tres componentes
montándose a la vez disparan tres peticiones idénticas), no hay datos obsoletos ni refetch al
volver a la pestaña, no hay reintentos, y las respuestas fuera de orden se pisan entre sí. Además
`orders` no se vacía nunca al cerrar sesión, así que el siguiente usuario ve los pedidos del
anterior. Reemplazarlo por `useQuery` borra las cinco cosas de golpe porque ya vienen resueltas.

**El estado derivado copiado con un efecto.** El segundo más común:

```tsx
// ❌
const [count, setCount] = useState(0);
useEffect(() => {
  setCount(users.length);
}, [users]);
```

Esto renderiza dos veces por cada cambio (una con el valor viejo, otra con el nuevo) y crea una
ventana real en la que `count` y `users` se contradicen — si algo lee ambos en esa ventana, pinta
una incoherencia. `const count = users.length;` no tiene ninguno de los dos problemas y es más
corto.

**La carga de datos dentro de `useEffect`.** Aunque acabe en un store o en `useState`, un efecto
que llama a la red no cancela al desmontar, no deduplica, no reintenta, se dispara dos veces en
StrictMode y provoca cascadas: el padre pide, renderiza, el hijo pide, renderiza, el nieto pide.
Tres viajes en serie donde debería haber uno.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only estado
```

| id | estado | qué detecta |
|---|---|---|
| `fe-servidor-fuera-del-store` | activo | `fetch`/`axios`/`await api.` dentro de `src/store(s)/` |
| `fe-sin-fetch-en-useeffect` | activo | cuerpo de un `useEffect` que llama a la red o encadena `.then(` |
| `fe-store-sin-react` | activo | store que importa de `react` o de un `.tsx` |
| `fe-sin-estado-derivado` | débil | `useEffect` cuyo cuerpo entero es un único `setX(...)` |

Las dos reglas de `useEffect` no son greps de línea: el checker localiza la apertura del cuerpo y
lo extrae **contando llaves balanceadas**, para poder juzgar el bloque completo y no la línea
suelta. Es lo que le permite distinguir un efecto que hace una sola cosa de uno que hace cinco.

`fe-sin-estado-derivado` es **débil** porque el mismo patrón sintáctico tiene un uso legítimo raro
(sincronizar con un sistema externo que no es React). Avisa y deja pasar.

Refuerzo en ESLint, ya presente en cualquier setup de React: `react-hooks/rules-of-hooks` y
`react-hooks/exhaustive-deps`. El segundo caza la otra mitad del problema de los efectos —
dependencias omitidas que producen valores rancios.

## Excepciones legítimas

- **Suscripciones a sistemas externos** (WebSocket, `localStorage`, `matchMedia`, un SDK de
  terceros): son exactamente para lo que existe `useEffect`, y sincronizar su valor a estado es
  correcto. Si el proyecto está en React 18+, `useSyncExternalStore` es mejor herramienta.
- **Estado de formulario en curso** dentro de un store, cuando un asistente multi-paso debe
  sobrevivir a la navegación entre rutas. Es estado de UI, no del servidor, aunque se le parezca.
- **Caché offline-first** con persistencia propia, donde el store sí es deliberadamente la fuente
  de verdad. Es una decisión de arquitectura, y como tal se escribe en el plan antes de codificarla.

```ts
// pattern-exempt: fe-servidor-fuera-del-store — modo offline: el store es la fuente de verdad (ADR-07)
```
