# `referencias-diseno/` — el corpus de gusto, con su procedencia

> **Qué es:** diez diseños reales, vendorizados en el template para que las skills y los auditores
> puedan **citar `fichero:línea`** en vez de describir de memoria cómo debería verse algo.
>
> **Qué NO es:** doctrina. Es **evidencia**. La doctrina —qué técnica se usa y cuándo— vive en
> `patterns/diseno/`, y cada fila de allí apunta aquí. Si los dos dicen cosas distintas, manda la
> doctrina: esto son diez ficheros congelados de 2026, no una ley.

## De dónde salen

Del workspace **`/home/web_design`** (estaba en `/home/old/web_design`; Miller lo movió el
2026-09-18). Son diseños que produjo esta casa para sus clientes entre **febrero y abril de 2026**,
en 53 commits. **No son de terceros**: no hay problema de licencia, y por eso se pueden citar línea
a línea y leer enteros.

Se vendorizan —en vez de apuntar al original— porque el template se copia a cada proyecto y las
citas tienen que seguir resolviendo en la máquina de otro. `MANIFEST.tsv` guarda la ruta de origen,
el tamaño y el `sha256` de cada fichero.

## Qué hay

| Carpeta | Qué contiene |
|---|---|
| `bien/` | 9 diseños que el Usuario aprobó, con su dirección de arte nombrada en `INDEX.json` |
| `mal/` | 1 diseño **roto a propósito conservado**: `attomo-digital.html`. Visualmente es de lo mejor del corpus y está desplegado con `initGSAP()` definido en `:1441` y **nunca llamado**, así que todo lo que lleva `.reveal` se queda en `opacity:0` (`:1006`). Es el fixture del gate GD-01 |
| `proceso/` | Lo que produjo la calidad, que no es un fichero de diseño: las dos **galerías** de comparación, el **`RANKING.csv` humano** con sus razones de negocio, y los documentos de marca de elevaiti |

## Por qué `proceso/` importa más que `bien/`

La revisión de septiembre midió que la calidad de aquel workspace **no venía de su skill de diseño**
—cuyo motor eran enlaces simbólicos rotos y nunca pudo ejecutarse— sino del **proceso**: varias
direcciones de arte con nombre, comparadas en una galería, rankeadas por un humano con razones de
negocio, y fusionadas después.

El detalle que lo prueba está aquí dentro: `RANKING.csv` (humano) y
`elevaiti-FINAL-RECOMMENDATION.md` (de la IA) **ordenan las mismas versiones de forma distinta**, y
el humano ignoró a la IA — eligió para producción dos versiones que la IA había puesto en su último
escalón. Los dos ficheros se conservan a propósito: son el recordatorio de que **el auto-ranking de
un agente no sustituye al criterio de quien paga**.

## Los tres límites, dichos antes de que alguien se confíe

1. **Diez diseños de un solo equipo NO son dominancia.** `patterns/README.md` §1 exige ≥85 % medido
   en el repo para fijar un patrón. Esto es canon **declarado**, con el mismo trato que las reglas
   `ag-*`, que siguen en `sombra` por estar medidas en dos repos propios (precedente GAP-1). **Nada
   de aquí bloquea nada.**
2. **Las fotos no viajan** (solo las de yessmassage pesaban 2,3 MB). Estos ficheros son para **leer
   y citar**, no para renderizar: abiertos en un navegador salen sin imágenes.
3. **Los ficheros de `bien/` tienen defectos reales**, y están listados uno a uno en
   `INDEX.json → defectos_conocidos`. El más incómodo: `yessmassage-v7.html:40` define
   `--text-muted: #e8e8e8` —casi blanco— sobre fondo crema. Un corpus sin esa columna se convierte
   en doctrina y se copia entero, defectos incluidos. **Se citan por su tipografía, su composición y
   su movimiento; no por su accesibilidad** — 6 de los 9 quitan el `outline` sin reponer el foco.

## Los tres ficheros de contrato

| Fichero | Lo consume | ¿Existe ya? |
|---|---|---|
| `INDEX.json` | `skills/marca` (paso 3) (set del proyecto) · `vera-art-director` (regla R-E: citar 2 referencias con `fichero:línea` antes de puntuar alto) · `scripts/corpus_lint.py` | los consumidores **todavía no**: son las olas 4, 6 y 9 |
| `anti-patrones.yaml` | `scripts/gate_diseno.py` — las 14 semillas de regla (`GD-01`…`GD-14`), **todas en `sombra`**, cada una con el sitio exacto donde el defecto ocurrió | el gate **todavía no**: es la ola 5 |
| `MANIFEST.tsv` | La huella: ruta, bytes, `sha256`, origen y fecha. Se genera; no se edita a mano | sí |

> ⚠️ **Esos «todavía no» están escritos a propósito.** Este repo tiene medido su propio modo de
> fallo favorito —documentación que manda ejecutar algo que no existe, y nadie lo comprueba hasta
> que alguien tropieza—, y `scripts/check_mechanisms.py` existe justo para cazarlo. Un fichero de
> contrato que nombra a su consumidor futuro tiene que decir que es futuro. Lo verificado hoy:
> `scripts/verificar_precedentes.py` **sí** existe y corre en verde sobre las 60 citas del catálogo.

## Reglas de uso

- **El corpus no se edita.** Es evidencia: se añade con procedencia, nunca se corrige un fichero
  para que quede mejor. Está declarado en `patterns/ownership.yaml`.
- **Tiene techo** (12-15 entradas): meter una exige **retirar otra con su razón escrita**. Sin tope,
  esto acaba como acaban los `CLAUDE.md` — creciendo hasta que nadie lo lee.
- **Se cita con `fichero:línea`**, nunca «como hace Stripe hoy»: una afirmación sobre una web viva
  no es verificable y caduca sin avisar.
