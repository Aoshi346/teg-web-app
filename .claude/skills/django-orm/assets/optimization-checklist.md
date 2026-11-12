# Django ORM optimization checklist

Pre-merge checklist for any view that reads a list. Applies to both delivery paths — a
`ListView` and a DRF `ViewSet` optimise identically, because the work happens on the **queryset**.

## Before writing the query

- [ ] Know which relations the page/response actually shows (that decides select vs prefetch)
- [ ] Check which indexes already exist on the fields you will filter and sort by
- [ ] Have a way to measure — `django_assert_num_queries`, or debug-toolbar on dev

## Lists

- [ ] `select_related()` for every forward FK displayed
- [ ] `prefetch_related()` for every reverse FK / M2M displayed
- [ ] Counts via `annotate(Count(...))`, never `.count()` per row
- [ ] Filtered relations via `Prefetch(queryset=..., to_attr=...)`
- [ ] Pagination on — `paginate_by` (templates) or `DEFAULT_PAGINATION_CLASS` (DRF)
- [ ] No `SerializerMethodField`, model `@property` or template tag that queries
- [ ] `only()`/`defer()` only if the table is wide, and covering every field actually read

## Detail views

- [ ] `select_related()` for the objects shown
- [ ] `prefetch_related()` for nested collections
- [ ] Caching only if the query is genuinely expensive — key includes the tenant, writes invalidate

## Writes

- [ ] `bulk_create()` for importing volume
- [ ] `.update()` for a mass field change **where no audit trail is needed**
- [ ] Multi-model writes wrapped in `@transaction.atomic`
- [ ] `select_for_update()` where two requests can race the same row

## Deletes

- [ ] `soft_delete()` rather than `delete()` on auditable models
- [ ] **Deleting many: loop, do not `bulk_update()`.** One `UPDATE` per row is the correct cost
      here — a queryset `.update()` skips `save()`, so it leaves no history entry, no
      `deleted_by` per row and no `updated_at`. Use the bulk form only when the deletion will
      never have to be explained to anyone.

## Code review

- [ ] No loop touching a relation that was not prefetched
- [ ] No unbounded `.all()` reaching a template or serializer
- [ ] Aggregations in the database, not in Python
- [ ] Long-running work handed to Celery, not done in the request
- [ ] Reads go through `.alive` (soft-deleted rows stay hidden)

## Testing

- [ ] Query-budget test on the critical endpoints
- [ ] The budget asserted at **two data volumes** — that is what proves there is no N+1
- [ ] RAM checked before running pytest (`bash .claude/hooks/check-ram.sh`)

## Pre-deploy

- [ ] New index? It is a migration — `makemigrations --check --dry-run` is clean
- [ ] Plans checked with `EXPLAIN (ANALYZE, BUFFERS)` on **realistic** data volumes
- [ ] Debug-toolbar / silk disabled outside dev and staging

## Post-deploy

- [ ] Alert on query time over the budget
- [ ] Slow query log reviewed
- [ ] Database CPU watched after the first real traffic

---

## Quick reference

### select_related vs prefetch_related

| Relation | Method |
|---|---|
| `ForeignKey` (forward, many-to-one) | `select_related()` |
| `OneToOneField` | `select_related()` |
| Reverse FK (one-to-many) | `prefetch_related()` |
| `ManyToManyField` | `prefetch_related()` |

### Budgets (starting points — assert them in a test)

| View type | Queries | Time |
|---|---|---|
| Simple list | 3-5 | < 100 ms |
| Complex list | 3-7 | < 200 ms |
| Detail | 5-10 | < 50 ms |
| Dashboard | 10-15 | < 500 ms |
| Complex report | 15-20 | — |

### The audit trade-off, in one line

Bulk = one query, no history. Loop = N queries, full trail. **Choose on purpose and write down why.**
