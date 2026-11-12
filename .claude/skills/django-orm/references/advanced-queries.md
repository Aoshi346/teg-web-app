# Django ORM Advanced Queries

> Reference of the `django-orm` skill (was the skill `django-orm-advanced-queries`, merged on 2026-10-19 —
> LI-10). Paths below are relative to `.claude/skills/django-orm/`.

Aggregations, annotations, subqueries and window functions — the read side, for dashboards,
reports and search.

## When to use this skill

- Analytics dashboards and reports
- "How many X per Y", grouped and bucketed by date
- Filtering on something computed, or ranking within a group
- Full-text search on PostgreSQL, or querying a `JSONField`

**Reach for the ORM before raw SQL.** Everything on this page compiles to one SQL statement.
Drop to `raw()` only when a measured plan shows the ORM cannot express the query — and then
parameterise it (`raw(sql, [param])`, never an f-string): `rules/security.md`.

## What this skill assumes

Models inherit `AuditableModel` and use the example domain, both defined in
`references/model-patterns.md`:

```
Agency  1──N  Lead  1──N  Appointment  N──1  Property
```

`Lead.alive` is the manager that excludes soft-deleted rows. Reports should use it — otherwise the
numbers include records the user believes they deleted.

## Core concepts

### 1. Q objects — OR, NOT, and grouping

```python
from django.db.models import Q

Lead.alive.filter(Q(status="new") | Q(status="contacted"))

Property.objects.filter(
    Q(price__gte=100000, price__lte=500000) &
    (Q(bedrooms__gte=2) | Q(property_type="studio"))
)

Lead.alive.filter(~Q(status="qualified"))                 # NOT

Property.objects.filter(
    Q(location__icontains=query) | Q(description__icontains=query)
).filter(is_available=True)
```

Positional `Q` arguments must come **before** keyword arguments, or Python raises a `SyntaxError`.

### 2. Aggregations — one row of numbers

```python
from django.db.models import Count, Sum, Avg, Max, Min

Lead.alive.aggregate(
    total=Count("id"),
    new=Count("id", filter=Q(status=Lead.Status.NEW)),
    qualified=Count("id", filter=Q(status=Lead.Status.QUALIFIED)),
)
# {'total': 100, 'new': 30, 'qualified': 20}
```

> ⚠️ **Aggregating across two different relations in one call inflates both numbers.** Django
> JOINs them, so rows multiply: a lead with 3 appointments and 2 documents reports 6 of each.
> Fixes: `distinct=True` on the `Count`, separate queries, or `Subquery`. Detail:
> `references/aggregations.md`.

### 3. Annotations — a computed column per row

```python
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

Lead.alive.annotate(
    full_contact=Concat("name", Value(" - "), "phone", output_field=CharField())
)

Property.objects.annotate(
    appointment_count=Count("appointments"),
).filter(appointment_count__gt=5)
```

**Chain a second `annotate()` when one computed field depends on another**, rather than defining
both in the same call — order of evaluation within a single `annotate()` is not something to rely on:

```python
from django.db.models import BooleanField, Case, Value, When

Property.objects.annotate(
    appointment_count=Count("appointments"),
).annotate(
    is_hot=Case(
        When(appointment_count__gte=10, then=Value(True)),
        default=Value(False),
        output_field=BooleanField(),
    )
)
```

### 4. Subqueries and Exists

```python
from django.db.models import Subquery, OuterRef, Exists

# Latest appointment date per lead
latest = Appointment.objects.filter(lead=OuterRef("pk")).order_by("-scheduled_at")
Lead.alive.annotate(latest_appointment_date=Subquery(latest.values("scheduled_at")[:1]))

# "Has at least one X" → Exists, not Count
confirmed = Appointment.objects.filter(property=OuterRef("pk"), status="confirmed")
Property.objects.annotate(has_confirmed=Exists(confirmed)).filter(has_confirmed=True)
```

`Exists` stops at the first match; `Count(...) > 0` counts every row before comparing. On a big
related table that is the whole difference.

**A queryset already works with `__in` — do not wrap it in `Subquery`:**

```python
qualified = Lead.alive.filter(status=Lead.Status.QUALIFIED)

Property.objects.filter(appointments__lead__in=qualified).distinct()          # ✅
Property.objects.filter(
    appointments__lead_id__in=Subquery(qualified.values_list("id", flat=True))
).distinct()                                                                  # ❌ same SQL, more noise
```

`.distinct()` matters here: a JOIN to a multi-row relation repeats the parent row per match.

### 5. Full-text search (PostgreSQL)

```python
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

vector = SearchVector("title", weight="A") + SearchVector("description", weight="B")
query = SearchQuery("apartamento barcelona")

Property.objects.annotate(search=vector, rank=SearchRank(vector, query)) \
                .filter(search=query).order_by("-rank")
```

Build the vector **once** into a variable and reuse it for `filter` and `rank` — repeating the
expression makes Postgres compute it twice.

Beyond a few thousand rows this recomputes the vector on every search: add a stored
`SearchVectorField` with a GIN index and keep it updated with a trigger or `SearchVectorField` +
`bulk_update`. That is a schema change, so it needs a migration.

### 6. JSON fields

```python
from django.db import models
from apps.core.models import AuditableModel


class Property(AuditableModel):
    features = models.JSONField(default=dict)     # {"parking": true, "elevator": true}

Property.objects.filter(features__parking=True)
Property.objects.filter(features__has_key="air_conditioning")
Property.objects.filter(features__amenities__contains={"gym": True})
```

`default=dict` (the callable), never `default={}` — a mutable default is shared between instances.
JSON lookups do not use ordinary column indexes; add a GIN index on the field if you filter on it
often.

### 7. Date bucketing

```python
from django.db.models.functions import TruncMonth, TruncWeek, TruncDate

Lead.alive.annotate(month=TruncMonth("created_at")) \
          .values("month") \
          .annotate(count=Count("id"), qualified=Count("id", filter=Q(status="qualified"))) \
          .order_by("month")
```

The order is load-bearing: `annotate` (compute the bucket) → `values` (group by it) → `annotate`
(aggregate within the group) → `order_by`. Swap `values` and the first `annotate` and you get one
row per record instead of one per month.

`Trunc*` respects `TIME_ZONE`: with `USE_TZ = True` the buckets are local days, not UTC days. That
is usually what you want and always what you must state when someone questions the numbers.

## Advanced patterns

### Dynamic filters

```python
def build_property_query(filters: dict):
    """Compose a filter from optional criteria. Lives in services.py, not in the view."""
    query = Q()
    if price_min := filters.get("price_min"):
        query &= Q(price__gte=price_min)
    if price_max := filters.get("price_max"):
        query &= Q(price__lte=price_max)
    if bedrooms := filters.get("bedrooms"):
        query &= Q(bedrooms__gte=bedrooms)
    if location := filters.get("location"):
        query &= Q(location__icontains=location)
    return Property.objects.filter(query)
```

`:=` treats `0` and `""` as absent. If zero is a legitimate filter value, test with
`filters.get(k) is not None` instead.

### Conditional aggregation

```python
from django.db.models import Case, When, IntegerField

Lead.alive.aggregate(
    active=Count("id", filter=Q(status__in=["new", "contacted"])),      # preferred
    closed=Count(Case(When(status__in=["won", "lost"], then=1),
                      output_field=IntegerField())),                    # older equivalent
)
```

`Count(..., filter=Q(...))` is the modern form — shorter, and it compiles to `FILTER (WHERE ...)`.

### Window functions — ranking within a group

```python
from django.db.models import Window, F
from django.db.models.functions import RowNumber

Property.objects.annotate(
    rank=Window(expression=RowNumber(),
                partition_by=[F("property_type")],
                order_by=F("price").desc())
).filter(rank__lte=10)          # top 10 per type
```

Filtering on a window annotation is supported, **but not with `OR`/`XOR`**: a disjunctive predicate
against a window function raises `NotImplementedError` ("Heterogeneous disjunctive predicates
against window functions"). Split it into two queries, or filter in a subquery.

## Best practices

1. **Aggregate in the database.** A Python loop over rows to count them transfers the whole table.
2. **`Exists` for "is there any"**, `Count` only when you need the number.
3. **`values()` / `values_list()`** when you need numbers, not model instances.
4. **`distinct()`** whenever a JOIN can duplicate the parent row.
5. **Chain `annotate()`** when one computed field feeds another.
6. **Index what you group and filter by**; JSON and full-text need GIN, not a normal index.
7. **Read the plan before believing it is fast** — `references/optimization.md`.

## Common pitfalls

- Two aggregations over different relations in one `annotate()` → both inflated (use `distinct=True`).
- Missing `distinct()` after joining a multi-row relation.
- `values()` and `annotate()` in the wrong order → grouping that is not what you meant.
- Reporting over `objects` instead of `.alive` → soft-deleted rows in the totals.
- `default={}` on a `JSONField` (mutable default shared across instances).
- Wrapping a queryset in `Subquery` for an `__in` lookup — unnecessary.
- Assuming a `Trunc*` bucket is UTC when `USE_TZ = True`.
- Dividing by a `Count` that can be zero → division by zero on an empty group.
- Reaching for raw SQL before trying `Subquery`/`Window`/`Case`.

## Verify before DONE

An analytics query with no verification is a number nobody can defend. Minimum, for any report:

```python
import pytest
from django.db.models import Count

pytestmark = pytest.mark.django_db


def test_monthly_counts_match_a_hand_count(lead_factory):
    """Cross-check the aggregate against a naive count over known data."""
    lead_factory.create_batch(3, created_at="2026-01-15T10:00:00Z")
    lead_factory.create_batch(2, created_at="2026-02-15T10:00:00Z")

    rows = list(leads_by_month())
    assert [(r["count"]) for r in rows] == [3, 2]


def test_report_excludes_soft_deleted(lead_factory, user):
    lead = lead_factory()
    lead.soft_delete(deleted_by=user)
    assert dashboard_stats()["total"] == 0


def test_report_query_budget(django_assert_num_queries):
    with django_assert_num_queries(1):        # a dashboard aggregate is ONE query
        dashboard_stats()
```

```bash
bash .claude/hooks/check-ram.sh        # RAM gate — rules/ram-pytest.md
pytest apps/reports/ -v --maxfail=3
python manage.py check
```

The three checks that catch nearly every reporting bug: **the total matches a hand count**, **it
excludes soft-deleted rows**, and **it is one query, not N**.

## Resources

- **`references/aggregations.md`** — group-by, conditional aggregation, the multi-relation trap
- **`references/annotations.md`** — computed fields, string/date functions, window functions
- **`references/subqueries.md`** — `Subquery`, `OuterRef`, `Exists`, correlated subqueries
- **`assets/advanced-queries-examples.py`** — runnable report functions

## Related

- `references/optimization.md` — measuring and fixing what these queries cost
- `references/crud.md` — the model and service layers these read from
- `.claude/patterns/stack/backend-servicios.md` — report functions belong in `services.py`
