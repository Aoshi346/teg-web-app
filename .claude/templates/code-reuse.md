---
# Plantilla (AN-7, cosechada de EvoPreven): cópiala a `.claude/rules/code-reuse.md` del proyecto,
# ajusta `paths:` a su código de negocio y rellena «Patrones de referencia» con los SUYOS, medidos.
# Es una variante: en un proyecto pequeño o nuevo sobra (Roberto ya mide la reutilización al cerrar).
paths:
  - "**/models.py"
  - "**/views.py"
  - "**/serializers.py"
  - "**/managers.py"
  - "**/selectors.py"
  - "**/services.py"
  - "**/tasks.py"
  - "src/**/*.tsx"
  - ".claude/rules/code-reuse.md"
---

# Reutilización de código — buscar antes de escribir en <PROYECTO>

> **Cuándo aplicar:** antes de cualquier `Write`/`Edit` que añada lógica no trivial (un modelo, un
> manager, un queryset, una vista, un serializer, una tarea, un componente). **NO aplicar:** bugfix
> de una línea sin lógica nueva, formato, traducciones, migraciones autogeneradas sin lógica propia.
>
> En una rule con `paths:` y no en `CLAUDE.md`: solo importa al tocar código de negocio. La
> comprobación al cerrar la hace `roberto-clean-code` (dimensión reutilización, con la búsqueda
> pegada); esta rule es la parte de antes: que el patrón nuevo no nazca.

## Protocolo — antes de escribir

1. **Buscar lo parecido** con Grep/Glob en el área y en las apps vecinas: modelos, managers y
   querysets, vistas y serializers, tareas, plantillas de informe, formularios, filtros.
2. **Leer lo encontrado**: nombres, herencia, `related_name`, choices, manager por defecto frente al
   «todos», mixins comunes, convenciones de la app vecina.
3. **Decidir y decirlo**: usarlo tal cual · extenderlo o parametrizarlo · copiarlo y cambiar solo lo
   necesario · o, si de verdad no aplica ninguno, **justificarlo por escrito antes** de escribir.

## Cómo se presenta

Toda propuesta lleva **una línea de procedencia**, en la respuesta o en el informe (nunca en un
comentario del código: el número de línea caduca, `code-style.md` §Comentarios):

> Patrón reutilizado: `<fichero>:<línea>` (`<Clase/función>`). Cambio: <delta mínimo>.

## Patrones de referencia `[PERSONALIZAR]`

Los de este proyecto, cada uno con su `fichero:línea` comprobado al escribirlo. Ejemplos de forma
(de EvoPreven, no se copian):
- Manager con filtro por defecto: `X.objects` excluye los eliminados; `X.all_objects` solo con motivo.
- Constantes de estado: se reutiliza la constante, no se redeclaran choices.
- Modelos CRUD: heredan del modelo base o de los mixins comunes; nada de campos de auditoría a mano.

## Anti-patterns

- ❌ Un manager nuevo cuando ya hay uno con esa semántica.
- ❌ Choices o estados duplicados en vez de la constante que existe.
- ❌ Un nombre distinto al de la app vecina para el mismo concepto.
- ❌ Una librería nueva cuando ya hay una equivalente en las dependencias.

---

_Plantilla v1.0 · 2026-11-02 — sub-ola 3.09 (AN-7): de `evopreven/develop/.claude/rules/code-reuse.md`
v1.0, sin lo propio de EvoPreven._
