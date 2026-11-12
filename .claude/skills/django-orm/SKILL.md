---
name: "django-orm"
description: >-
  Usar con el ORM de Django: CRUD ('crea el CRUD de X', 'nuevo endpoint para X', 'soft delete'),
  consultas ('cuántos X por Y', 'agrupa por', 'ranking') u optimización ('esta vista va lenta',
  'N+1', 'falta un índice'). NO usar para: la integridad de datos tras una migración
  (migration-integrity-checks), qué migraciones piden aprobación (rules/governance.md) ni la suite
  de tests (escribir-tests).
paths:
  - "**/models.py"
  - "**/models/*.py"
  - "**/views.py"
  - "**/viewsets.py"
  - "**/serializers.py"
  - "**/managers.py"
  - "**/querysets.py"
  - "**/admin.py"
  - "**/manage.py"
  - "**/urls.py"
  - "**/forms.py"
  - ".claude/skills/django-orm/**"
user-invocable: false
metadata:
  version: 3.0.0
  author: tech-lead-template
  category: domain
  updated: 2026-10-19
  absorbe: "django-orm-crud, django-orm-advanced-queries y django-orm-optimization (v2.0.0) — fusionadas el 2026-10-19 (LI-10)"
---

# django-orm — CRUD, consultas avanzadas y optimización

## Principio

Tres frentes del mismo ORM, con el mismo dominio de ejemplo y la misma clase base, pagaban tres
descripciones en el listado de cada sesión de los proyectos Django. Ahora es **una skill con tres
referencias**: este fichero decide cuál toca y la referencia trae el detalle. Las rutas son
relativas a la carpeta de la skill (`.claude/skills/django-orm/`).

**Regla de entrada:** se lee la referencia **antes** de escribir código. Aquí solo está el routing,
lo que comparten las tres y lo que no se negocia.

## Cuándo activar

- Hay que crear, editar o borrar un modelo de punta a punta (CRUD), por vistas de Django o por DRF.
- Hay que sacar números: agregados, informes, rankings, búsquedas, filtros sobre algo calculado.
- Algo va lento o se va a publicar un listado: el número de queries es un punto de revisión.

Disparadores por frente: (1) CRUD: modelo nuevo + formulario y vistas o ViewSet y serializer,
borrado lógico y restauración, auditoría created_by/updated_by, bulk, transacciones — 'crea el CRUD
de X', 'alta/edición/borrado de X', 'nuevo endpoint para X', 'soft delete', 'histórico de cambios',
'CRUD for X', 'add a ViewSet'. (2) Consultas avanzadas: agregaciones y group-by, annotate, Q,
Subquery/Exists, Case/When, ventanas y ranking, por día/mes, JSONField, full-text — 'estadísticas
de', 'agrupa por', 'cuántos X por Y', 'ranking', 'top N por categoría', 'buscador', 'group by',
'aggregate', 'full-text search'. (3) Optimización: N+1, select_related/prefetch_related, contar
queries, índices, only/defer, EXPLAIN — 'esta vista va lenta', 'query lenta', 'optimiza el
listado', 'N+1', 'cuántas queries hace', 'too many queries', 'falta un índice', 'slow endpoint'.
Enruta a references/crud.md, advanced-queries.md u optimization.md.

## Procedimiento

### 1. Elige la referencia por el síntoma

| Lo que tienes delante | Referencia | Detalle que carga después si hace falta |
|---|---|---|
| Modelo + alta/edición/borrado, formulario o ViewSet, borrado lógico, histórico, bulk, transacciones | **`references/crud.md`** | `references/model-patterns.md` (define `AuditableModel` y el dominio) · `references/serializer-patterns.md` (solo DRF) · `assets/crud-template.py` (solo DRF) |
| "Cuántos X por Y", dashboards, informes, ranking, top N por grupo, full-text, `JSONField` | **`references/advanced-queries.md`** | `references/aggregations.md` · `references/annotations.md` · `references/subqueries.md` · `assets/advanced-queries-examples.py` |
| Va lento, N+1, demasiadas queries, falta un índice, leer un plan | **`references/optimization.md`** | `references/n-plus-one-prevention.md` · `references/query-profiling.md` · `assets/optimization-checklist.md` |

Si son dos frentes a la vez (un informe nuevo **y** lento), primero el que construye
(`advanced-queries.md`) y después el que mide (`optimization.md`): no se optimiza lo que aún no da
el número correcto.

### 2. Lo que comparten las tres (no lo repitas en el código)

- **Clase base `AuditableModel`**: timestamps, `created_by`/`updated_by` y borrado lógico. Está
  definida entera en `references/model-patterns.md`; se copia a `apps/core/models.py`.
- **Dominio de ejemplo**: un CRM pequeño — `Agency 1──N Lead 1──N Appointment N──1 Property`. Nada
  fuera de ese diagrama se da por existente.
- **Path A o Path B**: vistas y formularios de Django **o** API con DRF. Se decide **contando** en
  el repo antes de elegir (`references/crud.md` §Which path); el patrón de casa de cada camino está
  en `.claude/patterns/stack/backend-formularios-django.md` y `backend-serializers.md`.

### 3. Verifica antes de DONE (lo común; cada referencia añade lo suyo)

```bash
bash .claude/hooks/check-ram.sh                      # RAM antes de pytest — rules/ram-pytest.md
python manage.py check                               # sin avisos del sistema
python manage.py makemigrations --check --dry-run    # nada sin migrar (un índice nuevo ES una migración)
pytest apps/<modulo>/ -v --maxfail=3                 # por módulo, nunca la suite entera ni --cov
```

- **CRUD**: si hay endpoint nuevo, se llama una vez de verdad antes de DONE (`rules/verification.md` §Smoke testing).
- **Consultas**: el total cuadra con una cuenta a mano, excluye las filas borradas y es **una**
  query, no N.
- **Optimización**: los tests de presupuesto de queries (`-k query_budget`) siguen pasando.

## Anti-patterns

- ❌ Escribir código sin haber leído la referencia del frente: los ejemplos asumen `AuditableModel`
  y el dominio del CRM, y copiar un trozo suelto rompe en silencio.
- ❌ Meter DRF en un proyecto que renderiza con Django porque un ejemplo enseñaba un ViewSet (Path A
  vs Path B: se cuenta antes).
- ❌ Bajar a `raw()` sin un plan medido que demuestre que el ORM no puede expresar la consulta.
- ❌ Optimizar a ojo: la query lenta casi nunca es la que se sospechaba (`references/optimization.md`
  §Rule zero).
- ❌ Usar `bulk_create`/`update()` donde hacen falta la auditoría o las señales: son rápidos **y
  ciegos** al rastro (`references/crud.md` §Bulk operations).
- ❌ Un informe sin test que lo cruce con una cuenta a mano: es un número que nadie puede defender.

## Ejemplos

### User: "crea el CRUD de propiedades, con borrado lógico"
TL: lee `references/crud.md`; cuenta formularios frente a ViewSets en el repo para elegir el camino;
hereda de `AuditableModel` (`references/model-patterns.md`); servicio sin HTTP, vistas o ViewSet;
verifica con el bloque de §3 y llama al endpoint una vez de verdad.

### User: "el listado de leads tarda 3 segundos con 500 filas"
TL: lee `references/optimization.md`; mide primero (cuenta de queries en un test); encuentra el N+1
con `references/n-plus-one-prevention.md`; añade `select_related`/`prefetch_related`; deja el test de
presupuesto de queries para que no vuelva.

### User: "quiero un dashboard con leads por mes y el top 3 de agencias"
TL: lee `references/advanced-queries.md` (date bucketing + ventanas); escribe las funciones en
`services.py`; test que cruza el agregado con una cuenta a mano y comprueba que es una sola query.

## Related

- `migration-integrity-checks` (skill) — integridad de los datos antes y después de una migración
- `escribir-tests` (skill) — la suite del módulo; `code-review-gate` la juzga
- `nueva-pantalla` (skill) — el otro lado del CRUD, en React
- `.claude/patterns/stack/backend-modelos.md`, `backend-vistas.md`, `backend-serializers.md` — el
  patrón de casa medido contra los proyectos
- `desarrollador-backend` (agente) — implementa usando esta skill
- `_archive/2026-10-19/skills/django-orm-*` — las tres skills tal como eran (README §Sub-ola 1.04)
