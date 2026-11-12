# Estructura de componentes — patrón de casa

> Capa `componentes` del patrón de casa (React · TypeScript · Tailwind).
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only componentes`.

## La regla (una frase)

Un componente por fichero, con el nombre del fichero, props tipadas con una `interface` exportada y
sin `any`, por debajo de 200 líneas y sin un solo color literal.

## Implementación de referencia

**Dónde vive cada cosa.** El árbol es plano a propósito: la profundidad se paga cada vez que
alguien busca dónde está algo.

```
src/
├── api/          cliente HTTP y un módulo por recurso   → api-y-errores.md
├── components/   compartidos entre features (Button, Card, EmptyState)
├── features/<feature>/
│   ├── components/   solo de esta feature
│   ├── hooks/        lógica de esta feature
│   └── schemas/      esquemas zod de esta feature      → formularios.md
├── hooks/        compartidos entre features
├── pages/        una por ruta; compone, no implementa
├── stores/       estado de UI global                    → estado.md
└── types/        tipos de dominio compartidos
```

La regla de promoción es una sola: **algo nace en `features/<x>/` y solo sube a la carpeta
compartida cuando lo usa una segunda feature.** No se anticipa la reutilización — se espera a que
ocurra. Al revés (crear todo en `components/` "por si acaso") se acaba con una carpeta de sesenta
ficheros donde nadie sabe cuáles siguen vivos.

**El componente.** Props en una `interface` exportada, desestructuradas en la firma:

```tsx
export interface OrderCardProps {
  order: Order;
  onSelect: (id: string) => void;
  children?: React.ReactNode;
}

export function OrderCard({ order, onSelect, children }: OrderCardProps) {
  return (
    <article className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-fg">{order.reference}</h3>
      {children}
      <button type="button" onClick={() => onSelect(order.id)}>
        Ver detalle
      </button>
    </article>
  );
}
```

`export interface` y no `type` para las props, para que el consumidor pueda extenderlas. Sin
`React.FC`: no aporta nada desde que dejó de inyectar `children` implícitos, y su tipado de
genéricos estorba. Los colores salen de tokens (`bg-card`, `text-fg`, `border-border`), nunca de un
hex.

**Cuándo se parte un componente.** Tres señales objetivas, por orden de fuerza:

1. **Pasa de 200 líneas.** Es el único umbral automático, y existe para que la conversación ocurra:
   el aviso no dice "esto está mal", dice "justifica por qué no se parte".
2. **Tiene dos motivos para cambiar.** Si el diseñador toca una mitad y el backend la otra, son dos
   componentes.
3. **Su estado no lo usa todo el árbol.** Un `useState` que solo alimenta un bloque de JSX es ese
   bloque pidiendo ser un componente.

Lo que **no** es motivo para partir: "es largo". Una lista de 40 campos de formulario en un solo
fichero se lee mejor entera que repartida en ocho ficheros de cinco líneas.

Cuando lo que crece es la lógica y no el marcado, la extracción correcta es un **hook**, no un
componente hijo: saca el `useState`/`useQuery`/handlers a `useOrderCard()` y deja el componente
como marcado casi puro. Así se testea la lógica sin renderizar.

## El antipatrón que sustituye

```tsx
// ❌ src/components/panel.tsx  — 400 líneas
export function UserPanel({ userId, users }: any) {
  const [user, setUser] = useState<any>(null);
  // …
  return (
    <div onClick={() => setUser(null)} style={{ color: '#ff0044' }}>
      <img src="/avatar.png" />
    </div>
  );
}

export function UserBadge() { … }
export function UserRow() { … }
```

Qué duele exactamente, en orden de coste:

- **`props: any`** apaga el compilador justo en la frontera donde más sirve. Renombrar un campo del
  modelo compila perfectamente y falla en tiempo de ejecución, en producción, sin que ningún test
  de tipos lo vea. Es el único error de esta lista que no se detecta leyendo el fichero.
- **Tres componentes en `panel.tsx`** rompen la búsqueda: `UserBadge` no aparece al buscar por
  nombre de fichero, y quien quiera importarlo tiene que saber ya dónde está. El nombre en
  minúsculas además choca en sistemas de ficheros que distinguen mayúsculas — verde en macOS, rojo
  en el CI de Linux.
- **`#ff0044`** sobrevive al cambio de marca y al modo oscuro. Aparece un rojo que no es *el* rojo
  y nadie sabe de dónde salió. Un token se cambia en un sitio. Da igual la notación: `rgb(255, 0, 68)`
  es el mismo problema y la regla también lo marca — pero `rgb(var(--color-brand))` no, porque eso
  ya es consumir el token. De dónde salen los tokens y qué hacer cuando falta uno:
  [`frontend-design-system.md`](frontend-design-system.md).
- **`<div onClick>`** deja el control fuera del orden de tabulación y sordo a Enter y Espacio: para
  quien navega con teclado, ese botón no existe. Ver `accesibilidad.md`.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only componentes
```

| id | estado | qué detecta |
|---|---|---|
| `fe-props-tipadas` | activo | `React.FC`, `: any`, `<any>`, `as any` (ignorando comentarios) |
| `fe-color-por-token` | activo | color literal en `.ts`/`.tsx` fuera de los ficheros de tokens/tema: `#hex` y también `rgb()`/`rgba()`/`hsl()`/`hsla()` con números |
| `fe-un-componente-por-fichero` | débil | más de un componente exportado, o un nombre de fichero que no coincide con el componente (`index.tsx` exento) |
| `fe-techo-200-lineas` | débil | componente por encima de 200 líneas |
| `fe-fecha-importe-por-helper` | débil | fecha o importe pintado sin formateador: `{x.created_at}`, `{x.fecha}`, `{x.amount}`, `.toFixed(`, `.toLocaleDateString(`, `new Intl.*Format(` fuera del helper (§Fechas e importes) |

El checker **elimina comentarios antes de aplicar las expresiones**, conservando los saltos de
línea para que el número reportado siga siendo correcto. Sin eso, `// TODO: quitar el any` se
reportaría como violación y la regla moriría por falsos positivos en una semana.

Refuerzo en ESLint, que es más preciso que el grep porque mira el AST:
`@typescript-eslint/no-explicit-any` (activar como `error`, no `warn`) y
`@typescript-eslint/no-unsafe-assignment` si el proyecto tiene `strict` y typed-linting. El techo de
líneas tiene equivalente en `max-lines` — pero se prefiere el checker, porque ESLint no distingue un
componente de un fichero de constantes.

## Fechas e importes — siempre por un helper

Una fecha del servidor o un importe **nunca** se pintan tal cual: pasan por **una** función de
formato del proyecto (`src/lib/format.ts`: `formatDate`, `formatMoney`…), y el `Intl.*Format` vive
solo ahí. En accounting_AMC se midieron 15 sitios con la fecha cruda y **cuatro formatos en la misma
tarjeta** («2026-04-02T09:00:00Z», «3 sept», «12/9/2026, 9:04:33»); el contrato las declaraba como
cadena, así que TypeScript no podía ayudar. Lo marca `fe-fecha-importe-por-helper` (débil): por el
nombre del campo (`*_at`, `fecha*`, `price`, `importe`, `amount`…) y por el formateo a mano. No ve
una fecha guardada antes en una variable con otro nombre; `key={x.fecha}` y `toLocaleString` con
opciones numéricas no cuentan. Medido el 31-10 sobre el panel de AMC (que ya tenía su gate): 4 avisos.

## Excepciones legítimas

- **Componentes acompañantes** que solo existen para su padre y nunca se importan fuera
  (`OrderCard` + `OrderCardSkeleton`): conviven en el mismo fichero. Es justo lo que
  `fe-un-componente-por-fichero` deja pasar como aviso.
- **Ficheros de tokens, tema y `tailwind.config.ts`**: son el sitio donde los hex *deben* estar. El
  checker ya los excluye por ruta.
- **`any` en el borde de una librería sin tipos**: se acota a una línea, con el motivo escrito. Si
  el tipo simplemente no se conoce, lo correcto es `unknown` y estrecharlo, no `any`.
- **Tablas, formularios largos y datos de configuración** que superan 200 líneas sin tener dos
  responsabilidades. Se documenta y se sigue.

```tsx
// pattern-exempt: fe-techo-200-lineas — tabla de 48 columnas del informe fiscal; partirla la empeora
```
