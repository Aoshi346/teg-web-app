---
name: django-orm-optimization
description: "Use when a Django page or endpoint is slow, or before shipping a list view: diagnosing N+1 queries, adding select_related/prefetch_related, counting queries in a test, choosing an index, only()/defer(), bulk operations, or reading a query plan. Triggers: 'esta vista va lenta', 'N+1', 'cuántas queries hace', 'optimiza el listado', 'falta un índice', 'query lenta', 'slow endpoint', 'too many queries', 'add select_related'. NO usar para: escribir el CRUD desde cero (eso es django-orm-crud), agregaciones/analítica/subqueries (django-orm-advanced-queries), ni verificar la integridad de un backfill (migration-integrity-checks)."
user-invocable: false
metadata:
  version: 2.0.0
  author: tech-lead-template
  category: domain
  updated: 2026-08-08
---

# Django ORM Optimization

Making Django queries fast: killing N+1, indexing what you filter, and — first — **measuring**,
because the slow query is almost never the one you guessed.

## When to use this skill

- An endpoint or page takes > 200 ms
- A list is fast with 10 rows and unusable with 500
- High database CPU
- Before shipping any list view (the query count is a review item, not an afterthought)

## What this skill assumes

Models inherit `AuditableModel` and use the example domain, both defined in
`../django-orm-crud/references/model-patterns.md`:

```
Agency  1──N  Lead  1──N  Appointment  N──1  Property
```

The examples show plain functions returning querysets. Where that queryset is consumed —
a `ListView.get_queryset()` or a DRF `ViewSet.get_queryset()` — makes no difference to any
technique here: **optimization happens on the queryset, not on the delivery layer.**

## Rule zero: measure before you touch anything

Optimising without a number is guessing, and the guess is usually wrong — the expensive part is
typically a `SerializerMethodField` or a template loop nobody suspected, not the query being
stared at.

```python
# The cheapest possible measurement, in a test. Fails loudly when someone adds an N+1 later.
def test_lead_list_query_budget(django_assert_num_queries, client, user):
    client.force_login(user)
    with django_assert_num_queries(4):        # 1 count + 1 page + 2 prefetch
        client.get("/leads/")
```

Full toolkit — `CaptureQueriesContext`, `assertNumQueries`, EXPLAIN, debug-toolbar, silk —
in **`references/query-profiling.md`**.

## Core concepts

### 1. The N+1 problem

```python
# BAD: 1 + N queries
leads = Lead.alive.all()          # 1 query
for lead in leads:
    print(lead.agency.name)        # one more query per lead

# GOOD: 1 query
leads = Lead.alive.select_related("agency")
for lead in leads:
    print(lead.agency.name)        # already in memory
```

The catalogue of shapes this takes — in serializers, in templates, with `.count()`, with `only()` —
is in **`references/n-plus-one-prevention.md`**.

### 2. select_related — a SQL JOIN

For **forward** relations: `ForeignKey` and `OneToOneField`.

```python
Lead.alive.select_related("agency")
Appointment.objects.select_related("lead", "property", "assigned_to")
Appointment.objects.select_related("lead__agency", "property__owner")   # follow the chain
```

### 3. prefetch_related — a second query, joined in Python

For **reverse** FKs and `ManyToManyField`, where a JOIN would multiply rows.

```python
Property.objects.prefetch_related("appointments")
Lead.alive.prefetch_related("tags")
Agency.objects.prefetch_related("leads__appointments")
```

### 4. Prefetch objects — when the related set needs filtering

```python
from django.db.models import Prefetch

Property.objects.prefetch_related(
    Prefetch(
        "appointments",
        queryset=Appointment.objects.filter(status="confirmed").select_related("lead"),
    )
)
```

Use `Prefetch` and not `.filter()` on the related manager inside a loop: the second one re-queries
per row and quietly undoes the prefetch.

## Optimization patterns

### Pattern 1 — list views

```python
# BEFORE: N+1 on agency, N+1 on appointments
def lead_list_queryset():
    return Lead.alive.all()

# AFTER: constant number of queries, whatever the row count
def lead_list_queryset():
    return (
        Lead.alive
        .select_related("agency")
        .prefetch_related(
            Prefetch("appointments", queryset=Appointment.objects.select_related("property"))
        )
        .annotate(appointment_count=Count("appointments"))
    )
```

`annotate(Count(...))` instead of `len(lead.appointments.all())` in the template: the count happens
in the database, over all rows at once.

### Pattern 2 — detail views

```python
def lead_detail(lead_id):
    return (
        Lead.alive
        .select_related("agency", "assigned_to")
        .prefetch_related(
            Prefetch("appointments", queryset=Appointment.objects.select_related("property")),
            "documents",
        )
        .get(pk=lead_id)
    )
```

### Pattern 3 — dashboard aggregations

```python
# BEFORE: pulls every row into Python to count them
def dashboard_stats():
    leads = Lead.alive.all()
    return {
        "new": len([l for l in leads if l.status == "new"]),
        "qualified": len([l for l in leads if l.status == "qualified"]),
    }

# AFTER: one query, no rows transferred
def dashboard_stats():
    return Lead.alive.aggregate(
        total=Count("id"),
        new=Count("id", filter=Q(status=Lead.Status.NEW)),
        qualified=Count("id", filter=Q(status=Lead.Status.QUALIFIED)),
    )
```

⚠️ Combining aggregates over **different** relations in one call inflates the numbers — see
`../django-orm-advanced-queries/references/aggregations.md`.

### Pattern 4 — bulk operations, and what they cost

```python
Lead.objects.bulk_create([Lead(name=f"Lead {i}", phone=f"+{i}") for i in range(1000)])
Lead.alive.filter(status=Lead.Status.NEW).update(status=Lead.Status.CONTACTED)
```

One query instead of N. **Neither loads the model**: no `save()`, no signals, no `auto_now` bump, no
history row. Right for imports; wrong for anything a user will be asked about later — then loop and
`save()` on purpose. Full trade-off table in `../django-orm-crud/SKILL.md`.

### Pattern 5 — only() and defer()

```python
Lead.alive.only("name", "phone")
Property.objects.defer("description", "large_json_field")
Lead.alive.select_related("agency").only("id", "name", "phone", "agency__name")
```

⚠️ Touching a field you deferred triggers **one extra query per object** — `only()` applied too
eagerly turns into the N+1 it was meant to prevent.

### Pattern 6 — indexes

```python
class Lead(AuditableModel):
    phone = models.CharField(max_length=20, db_index=True)
    ...

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),   # composite: filter + sort
            models.Index(fields=["agency", "status"]),
            models.Index(fields=["-created_at"]),            # matches ordering
        ]
```

Column order in a composite index matters: it serves queries that filter on a **prefix** of the
list. `["status", "created_at"]` helps `WHERE status=... ORDER BY created_at`, and does nothing for
a query that only filters `created_at`.

An index is not free — it costs write throughput and disk. Add one because a query plan asked for
it, not preventively: `references/query-profiling.md` shows how to read the plan.

### Pattern 7 — caching the expensive one

When the query is genuinely expensive and the data tolerates being stale:

```python
from django.core.cache import cache

def dashboard_stats(agency_id):
    key = f"dashboard:stats:{agency_id}"
    stats = cache.get(key)
    if stats is None:
        stats = Lead.alive.filter(agency_id=agency_id).aggregate(...)
        cache.set(key, stats, timeout=300)
    return stats
```

Two rules that make caching safe: the key includes the **tenant** (a global key serves one agency's
numbers to another), and whatever writes the data **invalidates** it. Cache backend config lives in
the project's settings, not here.

## Performance best practices

1. **Measure first** — a query budget in a test, before and after.
2. **`select_related`** for forward FKs shown in a list.
3. **`prefetch_related`** for reverse and M2M relations.
4. **Index what you filter and sort by**, guided by the query plan.
5. **`only`/`defer`** on wide tables — carefully.
6. **Bulk operations** for volume, with the audit trade-off made consciously.
7. **Paginate everything** — no unbounded list reaches a template or a serializer.
8. **Aggregate in the database**, never in a Python loop.

## Common pitfalls

- Optimising without measuring → time spent on the query that was not the problem.
- Missing `select_related`/`prefetch_related` on a list.
- Touching a `defer()`-ed field, or filtering a prefetched relation in a loop.
- `SerializerMethodField` or template tag that hits the DB per row.
- Unbounded `all()` with no pagination.
- Indexing nothing — or indexing everything, and paying for it on every write.
- Fetching whole objects when `values()` would do.
- **Reaching for raw SQL too early.** The ORM covers subqueries, window functions, conditional
  aggregation and full-text search — that is what `django-orm-advanced-queries` is for. Drop to
  `raw()` only when a measured plan shows the ORM cannot express the query, and then parameterise
  it (`raw(sql, [param])`, never an f-string) — las reglas de seguridad del template (no copiadas aquí).

## Query budgets

| View type | Queries | Time |
|---|---|---|
| Simple list | 3-5 | < 100 ms |
| Complex list | 3-7 | < 200 ms |
| Detail | 5-10 | < 50 ms |
| Dashboard | 10-15 | < 500 ms |

Starting points, not laws — a dashboard with twelve widgets legitimately costs more. What matters is
that the number is **asserted in a test**, so a regression shows up as a failure and not as a
support ticket.

## Tools

- **django-debug-toolbar** — the query list per request, in the browser
- **django-silk** — request profiling, works on API endpoints too
- **nplusone** — flags N+1 automatically during tests
- `EXPLAIN (ANALYZE, BUFFERS)` — what the database actually did

Setup and how to read each: `references/query-profiling.md`.

## Verify before DONE

```bash
bash .claude/hooks/check-ram.sh                      # RAM gate first — rules/ram-pytest.md
pytest apps/leads/ -v -k query_budget --maxfail=3    # the budget tests still pass
python manage.py makemigrations --check --dry-run    # a new index IS a migration
```

## Resources

- **`references/n-plus-one-prevention.md`** — the six shapes of N+1 and how to spot each
- **`references/query-profiling.md`** — measuring: counting, EXPLAIN, toolbar, silk
- **`assets/optimization-checklist.md`** — pre-merge checklist

## Related

- skill `django-orm-crud` — building the CRUD in the first place
- skill `django-orm-advanced-queries` — when the query itself is the hard part
- `.claude/backend/CLAUDE.md` — index and constraint conventions
- skill `django-orm-advanced-queries` — aggregations, subqueries and window functions
