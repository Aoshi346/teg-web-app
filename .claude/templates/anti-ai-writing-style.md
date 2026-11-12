# anti-ai-writing-style.md — la lista única de lo que NO se escribe

> **Cuándo aplicar:** siempre que se **escriba** texto que va a leer una persona (copy de web, email,
> post, propuesta, microcopy, headline, CTA) y siempre que se **audite** texto buscando tells de
> generación automática. Es la **fuente única**: antes esta lógica vivía triplicada en
> `agents/especialista-contenido.md`, `agents/persuasion-specialist.md` (archivados; la evitaban al escribir) e
> `agents/ignacio-roig.md` (la detecta como categoría AI-SLOP), y las tres divergían. Los dos
> primeros pasaron el 2026-08-22 a la skill `/escribir-copy`; la fuente única sigue siendo esta.
>
> **NO aplicar:** documentación técnica interna, commits, código, informes de agente a agente. Ahí
> "optimizar" o "robusto" son la palabra correcta y no hay nada que evitar.
>
> **PERSONALIZAR por proyecto:** la sección "Vocabulario aprobado" y las excepciones de dominio son
> lo único que cambia entre proyectos. La lista de prohibidos es transversal.

---

## 0. Cómo se usa (dos direcciones, un solo criterio)

| Rol | Qué hace con este fichero |
|---|---|
| **Quien escribe** (skill `/escribir-copy`) | Lo lee **antes** de redactar y pasa el checklist §7 antes de entregar |
| **Quien audita** (`ignacio-roig`, `lena-i18n-auditor`) | Cada hit es un finding de categoría **AI-SLOP**, citando la palabra y su línea |
| **Quien mantiene** | Si una palabra sobra o falta, se cambia **aquí y solo aquí** |

**La regla de oro, antes que la lista:** el problema no son las palabras, es la **ausencia de
información**. "Revolucionamos la gestión de tu negocio" está prohibido porque no dice nada, no
porque contenga un verbo maldito. Si borras un término de la lista y la frase sigue sin decir un
hecho, un número o una consecuencia, sigue siendo AI-slop.

---

## 1. Vocabulario prohibido — español

| Familia | Prohibido | Por qué falla | Qué se escribe en su lugar |
|---|---|---|---|
| **Grandilocuencia** | revolucionar · transformar · potenciar · impulsar · empoderar · maximizar | Verbo sin objeto medible | El resultado concreto: "pasas de 6 h a 40 min" |
| **Adjetivos de folleto** | de vanguardia · innovador · disruptivo · puntero · líder del sector · de última generación · robusto · potente | Autoelogio no verificable | Un hecho que lo demuestre, o nada |
| **Corporativismo** | soluciones integrales · plataforma end-to-end · ecosistema digital · stack tecnológico · sinergias · valor añadido · optimizar la eficiencia operacional | Jerga que un cliente no usa al hablar | Lo que hace, en la frase que diría el cliente |
| **Muletillas de IA** | en un mundo donde… · en la era digital · no es solo X, es Y · desbloquea el potencial · lleva tu negocio al siguiente nivel · la IA del futuro está aquí | Frases de plantilla; aparecen en todas partes | Empezar por el dolor concreto del lector |
| **Relleno de conector** | además, es importante destacar · cabe mencionar · en resumen, podemos decir que · sin duda alguna · profundicemos en | Ocupan línea sin añadir dato | Borrar la frase entera; casi nunca se echa de menos |
| **Vaguedad cuantitativa** | numerosos · múltiples · significativo · considerable · notable mejora · hasta un X% (sin fuente) | Finge precisión | El número real con su fuente, o reconocer que no se tiene |

## 2. Vocabulario prohibido — inglés

`delve` · `leverage` · `seamless` · `robust` · `cutting-edge` · `game-changing` · `revolutionary` ·
`next-level` · `unlock the power of` · `elevate` · `harness` (como verbo de marketing) ·
`in today's fast-paced world` · `it's not just X, it's Y` · `dive deep` · `tapestry` ·
`testament to` · `navigate the complexities of` · `empower` · `streamline` ·
`we're thrilled/excited to announce` · `at the end of the day`.

## 3. Estructuras y tics (más delatores que las palabras)

- **La antítesis vacía**: "No es una herramienta, es una forma de trabajar." Suena a conclusión y no
  afirma nada. Prohibida salvo que las dos mitades sean hechos distintos.
- **El tricolon automático**: tres elementos paralelos "rápido, seguro y escalable" cuando solo hay
  evidencia de uno.
- **Párrafo de cierre que resume lo ya dicho** ("En definitiva, …"). Si el texto necesita resumen, es
  que era largo: acórtalo.
- **Simetría sospechosa**: todos los bullets con la misma longitud y la misma estructura gramatical.
  Un texto humano tiene bullets desiguales.
- **Guion largo (—) en cada párrafo** como recurso rítmico único. Uno por texto, no uno por frase.
- **Preguntas retóricas encadenadas** ("¿Y si te dijera que…?").
- **Emoji como viñeta** en UI o en texto formal (✨🚀💡 al inicio de cada punto).
- **Hedging permanente**: "podría ayudarte potencialmente a mejorar quizá". O se afirma con evidencia
  o no se dice.
- **Voz pasiva impersonal** para no comprometerse: "se ha detectado que…" → di quién.
- **El nosotros protagonista**: la empresa como héroe. El héroe es el cliente; la empresa es el guía.

## 4. CTAs y microcopy prohibidos

| Prohibido | Por qué | Que funciona |
|---|---|---|
| "Enviar" · "Contactar" · "Más información" · "Saber más" · "Descubrir" | No dicen qué pasa al pulsar | "Ver cómo funciona en mi negocio →" · "Quiero recuperar 15 h/semana" · "Empieza gratis — sin tarjeta" |
| "Solo quedan 2 plazas" sin ser verdad | Urgencia fabricada; es la señal nº1 de infoproducto | Escasez real y comprobable, o ninguna |
| "Rellena el formulario y nos pondremos en contacto" | Trabajo para el usuario, promesa vaga para él | Qué recibe, cuándo y de quién |

## 5. Tells visuales asociados (para el auditor)

No son palabras, pero pertenecen a la misma categoría **AI-SLOP** cuando aparecen sin criterio:
gradiente azul-púrpura genérico · orbs desenfocados flotando en todas las secciones · stock de
personas sonriendo ante portátiles · shine/shimmer barriendo el CTA · iconografía mezclada de tres
familias · "premium polish" repetido hasta anularse.

## 6. Excepciones — cuándo la palabra prohibida es la correcta

La lista se aplica con criterio, no con `grep -f`. **No es AI-slop** cuando:

1. Es el **término técnico exacto**: "transformar un DataFrame", "optimizar la query", "robusto ante
   fallos" en un contexto de ingeniería.
2. Es el **nombre propio** de algo: un producto, un cargo, una categoría de mercado del cliente.
3. Es **cita textual** de un cliente, una fuente o un testimonial (se cita verbatim, no se corrige).
4. Es el **vocabulario real del sector** del cliente, verificado en su web o en su forma de hablar
   (ver "Vocabulario aprobado" del proyecto).

En esos cuatro casos, quien audita marca **`review`, no `notdone`**: antes de condenar, pregunta la
intención (`rules/verdict-contract.md`).

## 7. Checklist antes de entregar cualquier texto

```
[ ] Cero hits de §1/§2 sin justificar por una excepción de §6
[ ] Ninguna estructura de §3 (antítesis vacía, tricolon, cierre-resumen, emoji-viñeta)
[ ] Cada afirmación tiene número, hecho o consecuencia detrás; si no, se borra
[ ] El cliente (TÚ) aparece más veces que la empresa (NOSOTROS)
[ ] El beneficio se entiende en la primera línea (test de 2 segundos)
[ ] CTAs con acción y resultado explícitos (§4)
[ ] Párrafos de máx 3 líneas; bullets de longitud desigual
[ ] Se lee en voz alta sin sonar a folleto
```

## 8. Detección rápida (para auditar, no para decidir solo)

```bash
grep -rniE "revolucionar|transformamos|vanguardia|disruptiv|soluciones integrales|ecosistema digital|empoderamos|potencia tu|siguiente nivel" src/ content/
grep -rniE "delve|leverage|seamless|cutting-edge|game-chang|next-level|unlock the|elevate your" src/ content/
grep -rniE ">\s*(Enviar|Contactar|Más información|Saber más|Descubrir)\s*<" src/
```

El grep **propone candidatos**; el veredicto lo pone quien lee la frase entera con §6 en la mano.

---

## Anti-patterns

- ❌ Aplicar la lista como `grep` ciego y romper un término técnico legítimo (§6).
- ❌ Sustituir la palabra prohibida por un sinónimo igual de vacío ("revolucionar" → "reinventar").
- ❌ Mantener una copia de esta lista dentro de un agente: si diverge, gana **este** fichero.
- ❌ Auditar solo el vocabulario y dejar pasar la estructura (§3), que es lo que más delata.
- ❌ Reescribir una cita textual de un cliente para que cumpla la lista.

---

_Template version: 1.0 · ND-2 (adopción AI4DEVS, 2026-08-08) — fuente única para la skill
`/escribir-copy` (que absorbió a `especialista-contenido` y `persuasion-specialist` el 2026-08-22)
e `ignacio-roig`._
