# Query profiling — how to measure before you optimise

> Paths below are relative to `.claude/skills/django-orm/`.

> Companion to `references/optimization.md`. Four levels, cheapest first. Use the lowest one that answers the
> question you actually have.

| I need to know… | Use | Cost |
|---|---|---|
| How many queries does this run? | `django_assert_num_queries` / `assertNumQueries` | free, and it stays as a test |
| What exactly did it run? | `CaptureQueriesContext` | free, in a shell or a test |
| Why is *this* query slow? | `.explain()` / `EXPLAIN (ANALYZE, BUFFERS)` | needs realistic data |
| Where is the time going across a whole request? | django-debug-toolbar / silk | setup, dev/staging only |

---

## 1. Counting queries

### In pytest (the house test runner)

`pytest-django` ships the fixture; nothing else to install.

```python
def test_lead_list_query_budget(django_assert_num_queries, client, user):
    client.force_login(user)
    with django_assert_num_queries(4):
        client.get("/leads/")
```

Off-by-a-bit is fine while you explore — `django_assert_max_num_queries(5)` asserts a ceiling
instead of an exact number, which is the sane choice when pagination or auth adds a query you do
not control.

### In a Django `TestCase`

```python
class LeadListTests(TestCase):
    def test_query_budget(self):
        with self.assertNumQueries(4):
            self.client.get("/leads/")
```

### Why a budget test and not a one-off measurement

The measurement tells you today's number; the test defends it. An N+1 is almost always
*re-introduced* — someone adds a field to a serializer six months later and no one notices until
the endpoint times out. A budget test turns that into a red pipeline on the commit that caused it.

Assert the count **at two data volumes** to prove the count is constant — see
`references/n-plus-one-prevention.md`.

---

## 2. Seeing the actual SQL

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as ctx:
    list(Lead.alive.select_related("agency")[:10])

print(len(ctx.captured_queries))
for q in ctx.captured_queries:
    print(q["time"], q["sql"][:200])
```

`CaptureQueriesContext` is the mechanism `assertNumQueries` is built on. It switches the debug
cursor on by itself, so — unlike reading `connection.queries` directly — **it does not need
`DEBUG=True`** and it does not accumulate across the rest of the test.

### The `connection.queries` trap

You will see this recipe in old posts and it is worth knowing why it misleads:

```python
# ⚠️ fragile — do not build assertions on this
with override_settings(DEBUG=True):
    list(Lead.alive.all())
    print(len(connection.queries))
```

- `connection.queries` is only populated when `DEBUG=True`, so it is empty in a normal test run and
  the assertion passes vacuously.
- It **accumulates for the whole connection**; unless you reset it, you are counting every query
  since the connection opened, not the ones in the block.
- It is capped (9000 entries by default) and it keeps every SQL string in memory.

Use `CaptureQueriesContext` or `assertNumQueries`. Both scope correctly and both work with the
normal test settings.

### Just the SQL of one queryset, no execution

```python
print(Lead.alive.filter(status="new").query)     # the SQL Django would send
```

Handy, but it is not quoted for a real driver — read it, do not paste it into psql.

---

## 3. Reading the plan

```python
print(Lead.alive.filter(status="new").order_by("-created_at").explain(analyze=True, buffers=True))
```

Or straight in psql, which formats better:

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ... ;
```

What to look for, in order:

| In the plan | Means | Do |
|---|---|---|
| `Seq Scan` on a big table with a `Filter` | no usable index for that WHERE | add an index on the filtered columns |
| `rows=10` estimated vs `actual rows=90000` | the planner's statistics are stale | `ANALYZE <table>;` then re-read the plan |
| `Sort` with a large `Sort Method: external merge` | sorting on disk | index matching the `ORDER BY` |
| `Nested Loop` executed thousands of times | N+1 pushed into SQL | fix the queryset, not the index |
| `Index Scan` on a small table | fine — Postgres may still prefer a seq scan; that is correct | nothing |

**Measure on realistic data.** On 200 rows Postgres reads the whole table because that is genuinely
faster, and every plan looks like a missing index. A plan taken against a dev database with fixtures
tells you nothing about production.

---

## 4. Whole-request profiling

### django-debug-toolbar — server-rendered pages

```bash
pip install django-debug-toolbar
```

```python
# settings/dev.py only — never in production, it exposes SQL and settings
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]
```

The SQL panel gives per-query time and a duplicate-query counter — the duplicate counter is the
fastest N+1 detector there is.

### django-silk — API endpoints

The toolbar needs an HTML page to attach to; silk records requests server-side, so it works for
JSON. Same rule: staging and dev, never production — it stores request bodies.

---

## Interpreting the numbers

- **Query count matters more than query time on list views.** Forty queries at 2 ms each feel fine
  locally and are terrible over a network with real latency.
- **A single slow query beats forty fast ones** for a dashboard: one 300 ms aggregate is usually
  better than 40 round trips.
- **Time in the ORM ≠ time in the database.** If the DB says 5 ms and the request takes 400 ms, the
  cost is serialization or template rendering, and no index will help.

## Budgets

Defined in `references/optimization.md` (§Query budgets) — and they belong in a test, not in a wiki.

## Related

- `references/n-plus-one-prevention.md` — what to do once you have seen the count
- `assets/optimization-checklist.md` — the pre-merge list
- `rules/ram-pytest.md` — check RAM before running any of this
