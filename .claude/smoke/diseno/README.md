# `smoke/diseno/` — los fixtures del gate de diseño

> **Qué es:** por cada regla `GD-01`…`GD-15` de
> `resources/referencias-diseno/anti-patrones.yaml`, **dos** ficheros: `malo.html` con el defecto
> plantado y `bueno.html` con lo mismo hecho bien.
>
> **Se corre con:** `python3 .claude/scripts/gate_diseno.py --self-test` (exit 1 si algo falla).

## La regla: las DOS mitades, o la regla no sale de `sombra`

Un detector se mide por dos números y casi siempre se publica solo el primero:

| La mitad | La pregunta | El fixture |
|---|---|---|
| **Recall** | ¿caza el defecto que existe para cazar? | `malo.html` debe dar ≥1 hallazgo |
| **Falsos positivos** | ¿se calla cuando no hay nada? | `bueno.html` debe dar **0** |

Sin la segunda, un detector que dispara siempre «caza» el 100 % y no filtra nada — es el aviso de
`rules/qa-loop.md` §4b, y la razón de que un 14,5/15 sin su tasa de FP no diga si el instrumento
sirve. Por eso `--self-test` **exige las dos** y una regla sin sus dos ficheros se reporta como
imposible de promover.

## Lo que estos fixtures ya han cazado

No son decorativos: escribirlos encontró **tres** fallos que la corrida contra el corpus real
—mucho más grande— no encontró, porque en material abundante un fallo parcial se disimula.

| Lo que rompía | Cómo se veía | Dónde estaría hoy si no |
|---|---|---|
| GD-01 contaba una mención **en un comentario** como si fuera una llamada | `// initReveal se define y no se llama` hacía DOS apariciones → la regla se callaba | apagada justo en el fichero que lleva un `// TODO: llamar a initGSAP()` |
| GD-01 se comía la **primera clase** de cada `class="..."` | con `class="reveal"` (una sola) no casaba nada; con cientos, alguna sí | recall silenciosamente parcial, invisible sobre material real |
| `design-exempt:` sin razón dentro de `/* … */` | no casaba, así que ni se honraba ni se avisaba | alguien escribe la exención, el hallazgo sigue saliendo y nadie sabe por qué |

## Cómo se escribe un par nuevo

1. **Mínimo**: el fixture enseña UN defecto, no una página. Si hace falta leerlo dos veces, sobra algo.
2. **Gemelos de verdad**: `bueno.html` es el MISMO contenido bien resuelto, no otra página. Si se
   diferencian en más de una cosa, el «0 hallazgos» del bueno no prueba nada.
3. **El bueno lleva la trampa dentro.** El de GD-07 incluye `::placeholder` y
   `placeholder="tu@correo.com"` a propósito: son HTML y CSS correctos que R10 de
   `agents/shared/red-flags.sh` marca como si fueran deuda. Ese fichero es la guarda de regresión
   de ese falso positivo.
4. **En español y con texto real**, nunca *lorem ipsum*: el relleno miente sobre el espacio que
   ocupa lo que de verdad se escribe (`rules/motores-de-diseno.md` §F2).

⚠️ Estos ficheros llevan defectos a propósito, así que `gate_diseno.py` **excluye esta carpeta** de
cualquier barrido de directorios. Se leen solo cuando se pasan como fichero explícito, que es lo
que hace `--self-test`. Sin esa exclusión, cada corrida del gate reportaría 12 hallazgos que no son
deuda de nadie — y así es como se aprende a ignorar un informe.

**Más gemelos buenos cuando la trampa no cabe en un HTML** (sub-ola 3.67): el self-test lee también
cualquier `bueno.*` de la carpeta. `GD-08/bueno.test.ts` es el nombre de un test con «solo hoy», el
falso positivo que fitapp midió en un fichero de test.

**Los modos tienen su carpeta hermana, `smoke/diseno-modos/`** (sub-ola 3.67, UX-20), y el mismo
`--self-test` los corre: `--contra-lienzo` con un tema igual escrito de otra forma (0), con un color
cambiado de memoria (1) y con un tema sin tokens (2); `--dom` con una carpeta que trae un cascarón de
SPA sin pintar (2) y con un DOM pintado (0). El lienzo lleva los números con otro formato a
propósito, y en el `.html` porque el formateador del repo normaliza los `.css` al guardar.

## Y lo que pasar el self-test NO significa

**No promueve nada.** Las 15 reglas siguen en `sombra`: cuentan, no bloquean. Salir de ahí exige
las cinco condiciones de `rules/refactor-progresivo.md` §4.5 —incluida la quinta, que la firma un
humano con fecha— y medir la regla **fuera** del corpus con el que se escribió. Un fixture que tú
escribes para tu propia regla mide que el código hace lo que creías; no mide si la regla acierta.
