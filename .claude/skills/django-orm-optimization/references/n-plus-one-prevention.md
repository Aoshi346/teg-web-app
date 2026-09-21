# The six shapes of N+1

> Companion to `../SKILL.md`. That file explains what N+1 *is*; this one is the catalogue of the
> forms it actually takes in a codebase, because only the first one looks like the textbook example.
> Models and domain: `../../django-orm-crud/references/model-patterns.md`.

**The tell is always the same:** query count grows with row count. Ten rows, eleven queries. Five
hundred rows, five hundred and one. It never shows up in development with a seeded handful of
records — it shows up the week the client imports their real data.

---

## Shape 1 — forward FK in a loop (the textbook one)

```python
for lead in Lead.alive.all():
    print(lead.agency.name)        # +1 query per lead
```

**Fix:** `Lead.alive.select_related("agency")`

Where it hides: a template doing `{{ lead.agency.name }}` inside `{% for %}`. The Python looks
clean because the loop is in HTML.

---

## Shape 2 — reverse FK or M2M in a loop

```python
for lead in Lead.alive.all():
    for appointment in lead.appointments.all():    # +1 query per lead
        ...
```

**Fix:** `Lead.alive.prefetch_related("appointments")`

`select_related` cannot do this: one lead has many appointments, so a JOIN would duplicate the lead
row. `prefetch_related` runs a second query (`WHERE lead_id IN (...)`) and matches them in Python.

---

## Shape 3 — `.count()` / `.exists()` per row

```python
for lead in Lead.alive.all():
    print(lead.appointments.count())      # +1 query per lead, even WITH prefetch_related
```

**This one survives `prefetch_related`**, which is what makes it nasty: `.count()` issues its own
`SELECT COUNT(*)` and ignores the prefetch cache entirely.

Two fixes, and the right one depends on whether you need the objects:

```python
# Need only the number → annotate. One query total, no rows transferred.
Lead.alive.annotate(appointment_count=Count("appointments"))
#   lead.appointment_count

# Need the objects anyway → prefetch and count in Python. Zero extra queries.
Lead.alive.prefetch_related("appointments")
#   len(lead.appointments.all())        ← uses the cache
#   lead.appointments.count()           ← does NOT
```

Same story for `.exists()` → `annotate(has=Exists(...))`.

---

## Shape 4 — filtering a prefetched relation per row

```python
leads = Lead.alive.prefetch_related("appointments")
for lead in leads:
    confirmed = lead.appointments.filter(status="confirmed")   # +1 query per lead
```

The prefetch cache holds `.all()`. **Any `.filter()`, `.exclude()`, `.order_by()` or `.count()` on
the related manager re-queries**, silently throwing away the prefetch you paid for.

**Fix — filter inside the prefetch:**

```python
from django.db.models import Prefetch

leads = Lead.alive.prefetch_related(
    Prefetch(
        "appointments",
        queryset=Appointment.objects.filter(status="confirmed"),
        to_attr="confirmed_appointments",     # a plain list, impossible to re-query by accident
    )
)
for lead in leads:
    lead.confirmed_appointments               # already in memory
```

`to_attr` is the defensive version: it lands as a list, so a later `.filter()` on it raises
`AttributeError` instead of quietly costing a query.

---

## Shape 5 — the deferred field that gets touched

```python
leads = Lead.alive.only("id", "name")
for lead in leads:
    print(lead.phone)          # +1 query per lead to fetch the column that was left out
```

`only()` and `defer()` optimise by *not* loading columns. Read one of the omitted columns later and
Django fetches it per object. An over-eager `only()` produces exactly the N+1 it was added to avoid.

**Fix:** include every field the code path actually reads, and remember serializers and `__str__`
count as code paths.

---

## Shape 6 — the method that queries: serializers, properties, template tags

```python
class LeadSerializer(serializers.ModelSerializer):
    appointment_count = serializers.SerializerMethodField()

    def get_appointment_count(self, obj):
        return obj.appointments.count()        # +1 query per row, per response
```

The most common N+1 in an API, and the hardest to see: the loop is inside DRF, not in your code.
Identical versions of this bug:

- a model `@property` that walks a relation, called from a template
- `__str__` returning `f"{self.lead.name}"` — this one fires in the **admin changelist**, once per row
- a custom template tag doing a lookup
- a nested serializer (`AppointmentSerializer(many=True)`) with no prefetch on the view's queryset

**Fix:** compute it in the queryset, read it in the presentation layer.

```python
# view
Lead.alive.annotate(appointment_count=Count("appointments"))

# serializer
appointment_count = serializers.IntegerField(read_only=True)
```

Rule of thumb: **a serializer, a property or a template must never be the thing that decides to hit
the database.** The queryset decides; everything downstream reads memory.

---

## Detection

```python
# In a test — the version that stays green forever, or fails when someone regresses it
def test_list_is_constant_in_queries(django_assert_num_queries, client, user, lead_factory):
    lead_factory.create_batch(3)
    client.force_login(user)
    with django_assert_num_queries(4):
        client.get("/leads/")

    lead_factory.create_batch(50)          # 17x the data...
    with django_assert_num_queries(4):     # ...same number of queries. That is the assertion.
        client.get("/leads/")
```

Asserting the count **at two different data volumes** is what actually proves the absence of N+1. A
single `assertNumQueries(4)` only proves it was 4 that once.

Automatic detection during the test run:

```bash
pip install nplusone
```

```python
# settings (test only)
INSTALLED_APPS += ["nplusone.ext.django"]
MIDDLEWARE += ["nplusone.ext.django.NPlusOneMiddleware"]
NPLUSONE_RAISE = True      # turn the warning into a failure
```

## Checklist for a list view

```
[ ] Forward FKs shown in the list → select_related
[ ] Reverse/M2M relations shown  → prefetch_related
[ ] Counts → annotate(Count(...)), not .count() per row
[ ] Filtered relations → Prefetch(queryset=..., to_attr=...)
[ ] No SerializerMethodField / property / template tag touching the DB
[ ] only()/defer() covers every field actually read (including __str__)
[ ] A query-budget test asserts the count at two data volumes
```

## Related

- `query-profiling.md` — how to see the queries in the first place
- `../SKILL.md` — patterns and budgets
- `../../django-orm-advanced-queries/references/subqueries.md` — `Exists`/`Subquery` for per-row data
