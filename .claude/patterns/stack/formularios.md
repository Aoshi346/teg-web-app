# Formularios y validación — patrón de casa

> Capa `formularios` del patrón de casa (React Hook Form · zod ↔ DRF).
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only formularios`.

## La regla (una frase)

Un único esquema zod por formulario es la fuente de la validación de cliente, el submit se bloquea
mientras vuela, y **los errores de campo que devuelve el backend se pintan en su campo** — porque
la validación de cliente es comodidad, la del servidor es la de verdad.

## Implementación de referencia

**El esquema, en su fichero** — `src/features/orders/schemas/order.ts`. Un sitio, reutilizable en
tests, y el tipo sale de él en vez de escribirse dos veces:

```ts
import { z } from 'zod';

export const orderSchema = z.object({
  reference: z.string().min(1, 'La referencia es obligatoria'),
  email: z.email('Introduce un email válido'),
  phone: z
    .string()
    .regex(/^(\+34|0034|34)?[6789]\d{8}$/, 'Introduce un teléfono español válido'),
});

export type OrderInput = z.infer<typeof orderSchema>;
```

**Nota de versión (zod 4, el canon de `frontend-stack.md`).** Los formatos de cadena son funciones
de primer nivel: `z.email()`, `z.url()`, `z.uuid()`. La forma antigua encadenada —
`z.string().email()` — sigue funcionando pero está **deprecada** en la 4, así que copiar un ejemplo
de un blog escrito para la 3 mete deuda desde el primer día. El resto del esquema no cambia:
`z.string().min()` y `.regex()` son iguales en las dos.

**El formulario** — `src/features/orders/components/OrderForm.tsx`:

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { orderSchema, type OrderInput } from '../schemas/order';
import { ApiError } from '../api/client';

export function OrderForm({ onCreated }: { onCreated: () => void }) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<OrderInput>({ resolver: zodResolver(orderSchema) });

  async function onSubmit(values: OrderInput) {
    try {
      await ordersApi.create(values);
      onCreated();
    } catch (err) {
      if (err instanceof ApiError) {
        for (const [field, msgs] of Object.entries(err.fields)) {
          setError(field as keyof OrderInput, { message: msgs[0] });
        }
        return;
      }
      setError('root', { message: 'No pudimos guardar el pedido.' });
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <label htmlFor="reference">Referencia</label>
      <input id="reference" {...register('reference')} aria-invalid={!!errors.reference} />
      {errors.reference && <p role="alert">{errors.reference.message}</p>}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Guardando…' : 'Guardar'}
      </button>
    </form>
  );
}
```

**El contrato con el backend.** Es la mitad que casi nunca se escribe y la que hace que los dos
lados encajen. El backend envía **una sola forma para todos los errores** y el cliente
(`api-y-errores.md`) la normaliza a `ApiError.fields`, que el formulario vuelca campo por campo con
`setError`:

```
400  { "errors": { "reference": ["Ya existe un pedido con esa referencia."] } }
        → setError('reference', …)     el mensaje aparece BAJO el campo
400  { "errors": { "non_field_errors": ["Las fechas se solapan."] } }
        → setError('root', …)          el mensaje aparece sobre el botón
403 / 500                              → toUserMessage(error), nunca en un campo
```

Ese sobre `{"errors": …}` **no es el de fábrica de DRF** —que devuelve el campo a nivel raíz en
validación y `{"detail": …}` en auth/404/throttling—: lo garantiza un `EXCEPTION_HANDLER` del
backend (regla `be-api-exception-handler`, activa en su comprobador). Si lo lees como "DRF ya lo
hace" y aterrizas en un proyecto donde falta esa línea de `settings`, el formulario no pintará
ningún error de campo. El cliente de casa normaliza también las formas por defecto justamente para
que ese olvido no sea invisible (`api-y-errores.md`).

Dos detalles que hacen el trabajo: `noValidate` apaga los globos nativos del navegador, que no se
pueden estilar, salen en el idioma del navegador y no del sitio, y desaparecen solos; y
`aria-invalid` + `role="alert"` hacen que el lector de pantalla anuncie el error en vez de dejarlo
como texto rojo decorativo.

Sobre el momento de validar: el defecto de React Hook Form (`mode: 'onSubmit'` con
`reValidateMode: 'onChange'`) es el que se quiere. Validar en cada tecla marca en rojo un email
que el usuario todavía está escribiendo; validar solo al enviar y **corregir en vivo a partir de
ahí** es lo que se siente justo.

Si el proyecto usa React 19 sin React Hook Form, el equivalente de casa es `useActionState`, que
devuelve `[state, action, isPending]` — el `isPending` cumple el mismo papel que `isSubmitting`, y
el checker lo acepta. Nota de versión: en las canary se llamó `useFormState` en `react-dom`; el
nombre bueno es `useActionState` de `react`.

## Los formatos españoles, en un solo sitio

El esquema por formulario evita que la regex viva en el JSX; **no** evita que la misma regex esté
copiada en seis esquemas con seis variantes. Los tres formatos que todo proyecto español vuelve a
escribir —teléfono, NIF/CIF y código postal— viven en `src/lib/validadores.ts` y los esquemas los
componen:

```ts
// src/lib/validadores.ts
import { z } from 'zod';

export const telefonoEs = z
  .string()
  .regex(/^(\+34|0034|34)?[6789]\d{8}$/, 'Introduce un teléfono español válido');

// Las TRES formas: NIF, NIE (X/Y/Z) y CIF. Formato, no validez: la letra de control
// la comprueba el servidor (ver abajo).
export const nif = z
  .string()
  .regex(
    /^\d{8}[TRWAGMYFPDXBNJZSQVHLCKE]$|^[XYZ]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]$|^[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]$/i,
    'Introduce un NIF, NIE o CIF válido',
  );

// Provincias 01-52. El `[0-5]\d{4}` que se copia por ahí acepta 00000 y 53999.
export const codigoPostal = z
  .string()
  .regex(/^(0[1-9]|[1-4]\d|5[0-2])\d{3}$/, 'Introduce un código postal válido (5 dígitos)');
```

El esquema del formulario los compone, y sigue siendo un esquema por formulario:

```ts
// src/features/leads/schemas/lead.ts
import { z } from 'zod';
import { telefonoEs, nif } from '@/lib/validadores';

export const leadSchema = z.object({
  nombre: z.string().min(1, 'El nombre es obligatorio'),
  email: z.email('Introduce un email válido'),
  telefono: telefonoEs,
  nif,
});
```

**El formato no es la validación, y esto es lo que hay que decir en voz alta.** Una regex dice que
la cadena *parece* un NIF; no dice que exista. La letra de control se calcula (`nº mod 23` sobre
`TRWAGMYFPDXBNJZSQVHLCKE`) y ese cálculo es del servidor, igual que cualquier otra comprobación de
verdad — la del cliente es comodidad (§La regla). Medido sobre las dos regex heredadas:

```
12345678Z → regex ✓   letra correcta ✓
12345678A → regex ✓   letra INCORRECTA          ← el cliente lo deja pasar, y debe
X1234567L → la regex heredada lo RECHAZA        ← era un NIE: un residente extranjero
                                                   no podía rellenar el formulario
CP 28001  → regex ✓   provincia válida ✓
CP 00000  → [0-5]\d{4} ✓   provincia INVÁLIDA   ← por eso el rango va explícito arriba
CP 53999  → [0-5]\d{4} ✓   provincia INVÁLIDA
```

Que el cliente deje pasar `12345678A` **no es un fallo**: es el reparto correcto. Lo que sí sería un
fallo es que el 400 del servidor no llegue al campo, y de eso se ocupa el `setError` de arriba.

**El teclado del móvil.** Un campo de teléfono sin `inputMode="tel"` abre el teclado alfabético y el
usuario teclea nueve dígitos buscándolos entre letras; lo mismo con `inputMode="email"` y
`inputMode="numeric"` para el código postal. Es un atributo, no cambia nada en escritorio, y no hay
comprobador para él: se mira en la revisión de la pantalla.

## El asistente de varios pasos

Dónde vive el estado en curso ya lo decide `estado.md` (§Excepciones legítimas: es estado de UI, no
del servidor, aunque se le parezca). Lo que añade aquí es **qué pasa si el usuario recarga a mitad**:
se guarda el borrador en `localStorage` bajo una clave del asistente, y al montar se restaura.

Con dos condiciones que no son opcionales:

- **El borrador se valida al restaurarlo, con el mismo esquema.** Un `JSON.parse` a pelo devuelve lo
  que se guardó *con la versión anterior del formulario* —campos que ya no existen, tipos que
  cambiaron— y lo mete en el estado sin que nadie lo mire. La forma segura es
  `esquema.partial().safeParse(guardado)` y descartar el borrador si no pasa: vale más volver a
  empezar que arrastrar un paso corrupto hasta el envío.
- **Se borra al enviar, y también al abandonar el flujo.** El borrador de un alta lleva nombre,
  teléfono y NIF de una persona; quedarse en el navegador de un ordenador compartido es justo el
  tipo de dato que nadie esperaba dejar ahí.

Sin comprobador. La regla que sí se comprueba en un asistente es la de siempre: un esquema por paso
y el botón bloqueado mientras vuela.

## El antipatrón que sustituye

```tsx
// ❌ src/features/signup/components/SignupForm.tsx
export function SignupForm() {
  const { register, handleSubmit } = useForm();

  async function onSubmit(values) {
    try {
      await fetch('/api/signup', { method: 'POST', body: JSON.stringify(values) });
    } catch (err) {
      console.log(err);
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('phone', {
        pattern: { value: /^[6789]\d{8}$/, message: 'Teléfono inválido' },
      })} />
      <button type="submit">Enviar</button>
    </form>
  );
}
```

- **La regex vive en el JSX.** Cuando el backend empiece a aceptar teléfonos portugueses, el
  servidor los aceptará y el formulario los seguirá rechazando. Nadie relaciona el bug con esta
  línea porque está enterrada en el marcado, y la misma regex está copiada en otros tres
  formularios con tres variantes distintas.
- **El botón nunca se deshabilita.** El usuario impaciente pulsa dos veces y se crean dos registros
  — o dos cargos. Es el bug más caro de la lista y el más fácil de evitar: un atributo.
- **El error del servidor va a la consola.** El 400 que decía exactamente qué campo estaba mal se
  descarta; el usuario ve el formulario quieto, sin saber si se envió. Reintenta, y ahora son tres
  registros.
- **Sin `noValidate`**, el navegador valida primero con sus propias reglas y sus propios mensajes,
  así que conviven dos sistemas de validación con textos distintos.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only formularios
```

| id | estado | qué detecta |
|---|---|---|
| `fe-esquema-unico` | activo | regla `pattern:` con regex inline en un fichero que usa `useForm` |
| `fe-submit-bloqueado` | activo | fichero con `handleSubmit(` que no menciona `isSubmitting` ni `isPending` |
| `fe-errores-de-campo-del-backend` | débil | `useForm` con un `catch` pero sin ninguna llamada a `setError` |

`fe-errores-de-campo-del-backend` es **débil** porque no puede distinguir un formulario que ignora
los errores de campo de uno cuyo endpoint no devuelve errores por campo (un `POST /logout`, por
ejemplo). Señala el sitio donde hay que mirar; decide la persona.

**Lo que NO tiene comprobador, y se dice aquí para que nadie lo dé por cubierto:** que los formatos
españoles se importen de `validadores.ts` en vez de repetirse (`fe-esquema-unico` solo caza la regex
en el JSX, no la copiada en un segundo esquema), el `inputMode` de los campos, y las dos condiciones
del borrador del asistente. Un gate para cualquiera de las tres marcaría demasiados sitios legítimos
(regla de inversión, `patterns/README.md` §2): se miran en la revisión de la pantalla.

Complemento en ESLint: `jsx-a11y/label-has-associated-control` obliga a que todo `<input>` tenga su
`<label>` asociada — es a la vez la regla de accesibilidad y la que hace que
`screen.getByLabelText('Referencia')` funcione en los tests (`tests.md`).

## Excepciones legítimas

- **Búsqueda instantánea o filtros**, donde no hay "envío" y por tanto no hay `isSubmitting`. Si no
  hay `handleSubmit`, la regla ni siquiera aplica.
- **Un único campo con una regla trivial** (un buscador con `required`) donde montar un esquema es
  más código que valor. El límite práctico: en cuanto hay dos campos, o uno con formato, va al
  esquema.
- **Formularios de solo lectura o de confirmación** (un "¿seguro?" con un botón) sin validación.

```tsx
// pattern-exempt: fe-submit-bloqueado — filtro sin envío: se aplica al escribir, no hay submit
```
