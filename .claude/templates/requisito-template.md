# Molde de un requisito — los 11 apartados

> **Qué es esto.** El molde de UN requisito. Lo rellena la skill `arrancar` en su fase 1b, a partir
> de lo que contesta el Usuario, y de aquí salen tres cosas: `<plan>/arranque/02-requisitos.md` (lo
> legible), `requisitos.json` (los datos) y `requisitos.html` (la página).
>
> **De dónde sale.** Los apartados 1, 2, 6, 8, 9, 10 y 11 son el formato que ya funcionaba en
> `accounting_AMC` (`scripts/gen_requisitos.py` de su repo, 7 requisitos renderizados; en el template es
> `templates/report_kit/gen_requisitos.py`). Los apartados 3, 4, 5 y
> 7 los pidió el Usuario el 2026-09-12: *«lo único que faltaría es saber qué es lo del usuario, qué
> hace el usuario, cuál es la entrada, cuál es la salida, y si falta algún ejemplo»*.
>
> **La regla que lo ordena todo:** un requisito describe **lo que el usuario consigue**, no lo que
> el sistema hace por dentro. Si un apartado solo se puede rellenar hablando de tablas, funciones o
> endpoints, está mal contestado — eso va en el modelo de datos o en las trazas.

---

## R-<n> · <Título en la lengua del negocio, no en la del código>

<!-- El título lo entiende quien paga. "Cerrar el trimestre con el Excel", no "endpoint de cierre". -->

### 1. Qué deja en las manos del usuario

<!-- El PRODUCTO del requisito: qué tiene esta persona cuando termina que no tenía antes.
     Un objeto, no una sensación. Un fichero, una lista, un aviso, una decisión tomada. -->

### 2. Quién y cuándo

<!-- Quién lo hace (rol real, no "el usuario") y en qué momento de su día o de su mes.
     Si lo hacen dos roles distintos de forma distinta, son DOS requisitos. -->

### 3. Qué hace el usuario

<!-- Los pasos que da la PERSONA, en su lenguaje. "Arrastra el Excel y pulsa Revisar".
     No lo que hace el sistema: eso es el apartado 6 y las trazas. -->

### 4. Cuál es su entrada

<!-- Qué aporta: un fichero (¿de dónde sale, qué formato, quién se lo da?), unos datos que
     escribe, una decisión que toma, o nada. Si la entrada viene de un tercero que no
     controlamos, dilo aquí: es lo que dispara el Gate E de `rules/plan-gates.md`. -->

### 5. Cuál es la salida

<!-- Qué recibe de vuelta y DÓNDE: una pantalla, un fichero que se descarga, un correo, un
     aviso, una fila nueva en una lista. Si la salida es "nada visible", el requisito no se
     puede verificar y hay que replantearlo. -->

### 6. Cómo se usa

<!-- El recorrido de principio a fin, en prosa corta. Aquí sí entra el sistema, pero contado
     como lo contarías a quien lo va a usar, no a quien lo va a programar. -->

### 7. Ejemplos

<!-- AL MENOS UNO, con datos REALES del negocio — nunca `foo`, `test` ni `ejemplo 1`.
     Un caso del camino feliz y, si existe, uno del caso raro que de verdad pasa.
     Este apartado es el que más veces salva una discusión seis meses después. -->

| Situación | Entra | Sale |
|---|---|---|
| <el caso normal> | <datos reales> | <lo que ve> |
| <el caso raro que sí pasa> | <datos reales> | <lo que ve> |

### 8. Qué beneficio tiene

<!-- Qué se ahorra o qué se gana, en horas, en errores o en dinero. Con una cifra si la hay,
     y si no la hay, dilo: "no medido" es honesto; inventarla no. -->

### 9. El recorrido, como máquina de estados

<!-- En qué SITUACIONES puede quedarse el trabajo, qué lo mueve de una a otra y dónde se
     atasca. La diferencia con el apartado 6: un recorrido dice "pulsa aquí y luego allí";
     una máquina de estados dice en qué situación queda el expediente y quién lo desatasca.
     OBLIGATORIO: al menos un estado FINAL. Una máquina sin salida es un bug de diseño. -->

| Estado | Tipo | Qué lo saca de aquí | Quién |
|---|---|---|---|
| <sin empezar> | inicio | <qué ocurre> | persona · sistema |
| <en curso> | trabajo | | |
| <cerrado> | **fin** | — | — |
| <atascado> | problema | <qué lo desbloquea> | |

### 10. Por qué se usa así y no de otra manera

<!-- La alternativa obvia y por qué pierde. Si no hay alternativa que valga la pena nombrar,
     este apartado sobra... y probablemente el requisito no estaba pensado del todo. -->

### 11. Qué falta

<!-- Lo que NO cubre, lo que se decidió dejar fuera y lo que está a medias, con su porqué.
     Vacío no vale: "nada" es casi siempre mentira, y el día que lo sea, se escribe "nada,
     y esto es lo que se comprobó". -->

### Criterios de aceptación (Gherkin)

<!-- Uno por cada cosa verificable. El "entonces" tiene que ser OBSERVABLE: si no se puede
     mirar, el criterio está mal escrito y `rules/verdict-contract.md` lo devuelve a la spec.
     De aquí salen los tests, y por eso el verbo normativo (DEBE) no es opcional. -->

```gherkin
Dado que <contexto inicial concreto>
cuando <la acción del apartado 3>
entonces <el resultado observable del apartado 5>
```

---

## Cómo se rellena — el reparto

| Apartado | Quién lo aporta |
|---|---|
| 1 · 2 · 3 · 4 · 5 · 7 (un ejemplo) | **Se PREGUNTA al Usuario** (fase 1b de `arrancar`, 3 tandas) |
| 6 · 8 · 9 (transiciones) · 10 · 11 · Gherkin | **Los redacta el agente** y se confirman de una vez |
| 9 (los nombres de los estados) | Se PREGUNTA: nadie de fuera sabe cómo se llaman aquí |

> **Por qué no se preguntan los 11.** Siete requisitos × once apartados son setenta y siete turnos,
> y la sesión se abandona antes de la mitad. Se preguntan los cinco que **solo el Usuario sabe** y
> se redactan los seis que se derivan de ellos.

## Anti-patterns

- ❌ Un título en lenguaje de código ("endpoint de conciliación") → el requisito lo lee quien paga.
- ❌ El apartado 5 vacío o "se guarda en base de datos" → si no se ve, no se verifica.
- ❌ Ejemplos con `foo`, `test@test.com` o "Cliente 1" → no prueban nada y esconden el caso real.
- ❌ Una máquina de estados **sin estado final** → el trabajo no puede terminar nunca.
- ❌ "Qué falta: nada" sin haberlo comprobado.
- ❌ Un "entonces" que no se puede observar → devuélvelo antes de escribir el test.
- ❌ Mezclar en el apartado 3 lo que hace la persona con lo que hace el sistema.
