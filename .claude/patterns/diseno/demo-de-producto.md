# Demo de producto — enseñarlo funcionando en vez de ilustrarlo (T22)

> **Cuándo aplicar:** al diseñar el hero o el bloque principal de una web **B2B, SaaS o de servicio
> técnico**, cuando lo que se vende es algo que **hace** cosas: un asistente, una automatización, un
> panel, un servicio que ahorra tiempo o dinero. Da los cuatro arquetipos, lo que cada uno exige de
> accesibilidad, y la regla de que degrade sin JS.
>
> **NO aplicar:** en negocio local o de bienestar, donde lo que se vende es una sensación y la
> respuesta es la fotografía (`imagen.md`) · para **qué dice** la demo —las frases del chat, los
> rótulos de la calculadora—, que es `skills/escribir-copy` y, si detrás hay un bot de verdad,
> `skills/disenar-conversacion` · para el **orden de los bloques** de la página
> (`estructura-de-pagina.md`) · para **construir** el producto real: esto es una demo de portada, no
> el producto.
>
> **Relacionado:** `catalogo-diseno.yaml` (T22) · `movimiento.md` §3.2 (la mejora progresiva, que
> aquí es la regla que más se incumple) · `estructura-de-pagina.md` §1 (por qué esto ganó el
> ranking) · `resources/referencias-diseno/proceso/RANKING.csv` · `aitor-a11y-auditor`.

---

## 1. Por qué gana a una ilustración

Porque lo eligió quien paga, y está escrito. En
`resources/referencias-diseno/proceso/RANKING.csv` el cliente ordenó nueve versiones de su propia
web y puso **primera** la que enseña el producto funcionando:

> **1 · V5** — *«Muy fuerte en claridad de oferta. no tiene un storytelling, pero **comunica bien el
> producto**»* · elementos destacados: *«representación de departamentos»*

Y lo dijo aún más claro al justificar la tercera:

> **3 · V7** — *«**Calculadora ROI** 🔥 / Comparativa IA vs humano (muy persuasiva) / Mensaje fuerte
> de valor ("ROI medible")»*

Dos de los tres primeros puestos se ganaron **por la demo**, no por la estética. La versión que el
mismo cliente describió como *«visualmente potente y llamativa»* quedó **sexta**, con esta razón:
*«falla en negocio: los productos se pierden»*.

El skill oficial `frontend-design` lo respalda desde el otro lado, al listar qué puede abrir un
hero: *«a headline, an image, an animation, **a live demo**, an interactive moment, or other
treatments»*. Una demo es un tratamiento de hero de primera clase, no un extra.

**La razón de fondo:** una ilustración de un robot dice *«hacemos IA»*. Un chat que contesta dice
**qué** preguntas entiende, **cómo** responde y **cuánto** tarda. Lo segundo se puede evaluar; lo
primero solo se puede creer.

> ⚠️ **Una discrepancia medida, que conviene conocer antes de citar ese ranking.** El cliente
> atribuyó la calculadora de ROI a **V7**, y en el fichero vendorizado **no está**:
>
> ```bash
> cd .claude/resources/referencias-diseno
> grep -c 'type="range"' bien/elevaiti-v7.html   # → 0
> grep -c '<table'       bien/elevaiti-v7.html   # → 0  (tampoco la «comparativa»)
> grep -n 'type="range"' bien/elevaiti-v5.html   # → la calculadora está AQUÍ (:2371-2389)
> ```
>
> Lo que sí tiene v7 es una **tarjeta** de ROI en el hero (`:1801`, `+347% ↑`): un número fijo, que
> no es una calculadora. O la versión que se rankeó no es la que se vendorizó, o el recuerdo mezcló
> dos versiones. **Lo que sigue en pie y es lo que importa: la 1.ª y la 3.ª se ganaron enseñando
> producto.** Lo que no se puede sostener es que el fichero de v7 contenga la calculadora que su
> propia reseña elogia.

---

## 2. Los cuatro arquetipos

| # | Arquetipo | Qué demuestra | Precedente |
|---|---|---|---|
| **A** | **Chat con indicador de escritura** | Cómo habla el producto y qué entiende | `bien/elevaiti-v5.html:2007` + `:756-768` |
| **B** | **Calculadora** (ROI, ahorro, presupuesto) | Que el beneficio es **suyo**, con sus números | `bien/elevaiti-v5.html:2323-2409` |
| **C** | **Terminal o registro que se escribe solo** | Que hay una máquina trabajando de verdad | **Sin precedente en el corpus** (§2.3) |
| **D** | **Tabla comparativa** (con nosotros / sin nosotros) | La decisión, puesta en dos columnas | **Sin precedente en el corpus** (§2.4) |

Se elige **uno**. Dos demos en la misma portada compiten entre sí y no se mira ninguna entera.

### 2.1 Chat con indicador de escritura (A)

El indicador de escritura es la pieza: sin él el chat parece una captura; con él parece que está
pasando algo.

```css
/* resources/referencias-diseno/bien/elevaiti-v5.html:759-768 */
.chat-typing span {
  width: 6px; height: 6px; border-radius: 50%; background: var(--cyan);
  animation: typing-bounce 1.2s ease-in-out infinite;
}
.chat-typing span:nth-child(2) { animation-delay: 0.2s; }
.chat-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
  0%,60%,100% { transform: translateY(0);     opacity: 0.4; }
  30%         { transform: translateY(-5px);  opacity: 1;   }
}
```

**Lo que hay que copiar, punto por punto:** tres puntos, no cinco · desfase de **0,2 s** entre ellos,
que es lo que lo hace parecer una onda y no un parpadeo · ciclo de **1,2 s**, lento a propósito —uno
rápido pone nervioso— · y **solo `transform` y `opacity`**, que es lo único que anima barato.

**Accesibilidad, que aquí no es opcional porque el contenido aparece solo:**

| Qué | Cómo | Dónde |
|---|---|---|
| El contenedor se anuncia | `role="log" aria-live="polite" aria-label="Mensajes del chat"` | `:2007` |
| El indicador se nombra | `aria-label="Escribiendo"` en el propio `.chat-typing` | `:3679` |
| El cromo decorativo se calla | `aria-hidden="true"` en los botones de ventana y en el campo falso | `:2001` · `:2012` |

`aria-live="polite"` y **no** `assertive`: la conversación se anuncia cuando el lector de pantalla
termina lo que estaba diciendo, sin interrumpir. Un `assertive` dentro de un bucle de demo es una
tortura para quien lo use.

### 2.2 Calculadora (B)

La única que hace que el visitante meta **sus** datos, y por eso convence distinto: el resultado
deja de ser nuestra promesa y pasa a ser su cuenta.

```html
<!-- resources/referencias-diseno/bien/elevaiti-v5.html:2371-2378 -->
<label for="roi-salary">Salario promedio mensual (€) <span id="roi-salary-val">2.500€</span></label>
<input type="range" class="roi-slider" id="roi-salary"
       min="1500" max="8000" value="2500" step="100"
       aria-label="Salario promedio mensual" oninput="updateROI()">
```

```html
<!-- :2392 — y este es el detalle que casi nadie pone -->
<div class="roi-results" role="region" aria-live="polite" aria-label="Resultados del cálculo">
```

Cinco decisiones bien tomadas en ese bloque: **pocos controles** (tres deslizadores, no un
formulario) · **valores de partida realistas**, para que el resultado ya diga algo antes de tocar
nada · **el valor actual visible junto a la etiqueta** (`2.500€`), porque un deslizador sin número es
adivinar · **`label for` + `aria-label`**, no un `<div>` haciendo de etiqueta · y **`aria-live` en los
resultados**, que es lo que hace que quien no ve la pantalla se entere de que el número ha cambiado.

Y los resultados se presentan **de menor a mayor**, terminando en la fila destacada
(`:2406`, `.roi-result-row highlight` → *«ROI potencial año 1»*). La cifra que se quiere recordar va
la última.

> **El número que sale nunca se inventa.** La fórmula se escribe y se enseña: es una **estimación**
> con sus supuestos a la vista. Una calculadora que devuelve una cifra que nadie puede reproducir es
> escasez falsa con otro traje (GD-08, `resources/referencias-diseno/anti-patrones.yaml`).

### 2.3 Terminal o registro que se escribe (C) — sin precedente

```bash
cd .claude/resources/referencias-diseno && grep -ril "typewriter\|typeWriter\|terminal" bien/ mal/ | wc -l   # → 0
```

No lo hemos hecho nunca en este corpus. Se deja escrito porque encaja donde el producto **no tiene
interfaz conversacional** —una automatización, un proceso por lotes, una integración— y enseñar su
registro es lo más honesto que se puede enseñar. Pero va marcado: **es una propuesta, no un patrón
de la casa.**

Si se usa, tres condiciones heredadas de los otros dos: el **texto completo en el HTML** y el efecto
de escritura por encima (§3), `aria-live="polite"` en el contenedor, y **líneas reales del
producto** —un registro inventado es un mock en producción, que es justo lo que prohíbe
`rules/verification.md` §Ciclo de producción—.

### 2.4 Tabla comparativa (D) — sin precedente, y con aviso

Tampoco existe en el corpus (`grep -c '<table'` → 0 en las dos referencias B2B). El cliente la
elogió y el fichero no la tiene (§1).

El aviso no es técnico: una tabla «con nosotros / sin nosotros» **la escribimos nosotros**, así que
las dos columnas están pactadas de antemano. Es persuasiva —el propio cliente la llamó *«muy
persuasiva»*— y por eso hay que sujetarla: las filas son **hechos comprobables** (tiempo de
respuesta, horas, coste), nunca adjetivos, y la otra columna describe **la situación actual**, no a
un competidor con nombre.

---

## 3. La regla que las cruza todas: tiene que degradar visiblemente

Una demo es el sitio donde más fácil es incumplir T11b (`movimiento.md` §3.2), porque su contenido
**es** dinámico. Y el corpus tiene los dos casos **en el mismo fichero**, lo que lo convierte en un
ejemplo inmejorable:

| | Sin JavaScript se ve… | Por qué |
|---|---|---|
| **Calculadora** (`:2371-2392`) | **Los deslizadores, sus etiquetas y sus valores de partida.** Solo falla el recálculo | Usa `<input type="range">` nativo: lo pinta el navegador |
| **Chat** (`:2007`) | **Una caja vacía.** El HTML dice literalmente `<!-- Messages injected by JS -->` | Los mensajes se inyectan. Sin JS no hay ninguno |

**La regla:** la demo se escribe **con su primer estado en el HTML**, y el JavaScript la anima desde
ahí. Para el chat, eso significa dejar las dos o tres primeras burbujas escritas en el marcado y que
el guion continúe la conversación; para la terminal, el texto completo ya presente. Cuesta unas
líneas de más y es la diferencia entre *«una demo que aún no ha arrancado»* y *«un hueco»*.

**Y el resto del suelo, que es el de siempre:**

- **`prefers-reduced-motion`**: la demo se queda en su **estado final** —la conversación completa, el
  resultado ya calculado—, nunca en el inicial. Apagar la animación sin reponer el estado es
  exactamente cómo se le deja una caja vacía a quien pidió menos movimiento (`movimiento.md` §8).
- **El bucle para.** Una demo que se repite indefinidamente gasta batería y distrae del texto que
  tiene al lado. Se ejecuta una vez al entrar en pantalla —con el mismo `IntersectionObserver` del
  reveal y su `unobserve`— y se queda quieta al terminar.
- **No pide datos.** Una demo de portada con un campo de correo obligatorio para ver el resultado ha
  dejado de ser una demo.

---

## 4. Límites honestos

- **Dos de los cuatro arquetipos no tienen precedente** (§2.3, §2.4). Van marcados uno por uno y no
  se presentan como patrón de la casa.
- **La atribución del ranking no cuadra con el código** (§1). Se conserva el dato **y** la
  discrepancia: el corpus se cita con lo que dice el fichero, nunca con lo que dice el recuerdo.
- **T22 es `patron` con dos precedentes** (`catalogo-diseno.yaml`) y los dos son **del mismo
  cliente**, en versiones distintas de la misma web. Eso es bastante menos independencia de la que
  sugiere la palabra «patrón».
- **Nada de esto se comprueba solo.** Que la demo degrade sin JS sí es medible —es el comando de
  `movimiento.md` §3.2 y la semilla GD-01—, pero está en `sombra`: cuenta, no avisa, no bloquea.

---

## Anti-patterns

- ❌ **Ilustrar el producto** (un robot, un cerebro, una red de nodos) pudiendo enseñarlo funcionando
  → el ranking humano puso sexta a la versión más ilustrada.
- ❌ **Dos demos en la misma portada** → compiten y no se mira ninguna entera.
- ❌ **Un contenedor vacío que rellena el JS** → sin JavaScript queda un hueco (§3). El primer estado
  va en el HTML.
- ❌ **Dejar la demo en su estado inicial con `prefers-reduced-motion`** → caja vacía para quien pidió
  menos movimiento. Se queda en el estado **final**.
- ❌ **Bucle infinito** de la conversación o del contador → batería y distracción. Una vez, al entrar.
- ❌ **`aria-live="assertive"`** en una demo → interrumpe al lector de pantalla en cada burbuja.
- ❌ **Chat sin `role="log"` ni `aria-label`, o calculadora sin `aria-live` en los resultados** → el
  contenido cambia y nadie se entera.
- ❌ **Deslizador sin su valor numérico visible** → es mover a ciegas.
- ❌ **Una cifra de ROI sin fórmula reproducible** → es una promesa disfrazada de cálculo.
- ❌ **Un registro o una conversación inventados** presentados como salida real del producto → mock en
  producción (`rules/verification.md` §Ciclo de producción).
- ❌ **Pedir el correo para ver el resultado** de la demo de portada.
- ❌ **Tabla comparativa con adjetivos** en vez de hechos comprobables, o con un competidor nombrado
  en la otra columna.
- ❌ **Una demo en una web de bienestar o de negocio local** → ahí lo que vende es la fotografía.

---

_Doc version: 1.0 · 2026-09-18 · Ola 2. Canon **declarado** (precedente GAP-1 de
`patterns/README.md` §1): no bloquea. Los arquetipos C y D van sin precedente y marcados como tales;
la discrepancia entre el ranking humano y el fichero de v7 se conserva escrita, en vez de resolverse
a favor de la versión que quedaba mejor._
