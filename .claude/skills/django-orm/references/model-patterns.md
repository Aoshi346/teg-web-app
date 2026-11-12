# Model patterns — the auditable base class

> Paths below are relative to `.claude/skills/django-orm/`.

> This file **defines** `AuditableModel`, the base class every example in `references/crud.md` uses.
> It is plain Django: no private package, no import from anywhere outside your own project.
> Copy the block below into `apps/core/models.py` of your project and the skill works as written.
>
> Aligned with the house canon `.claude/patterns/stack/backend-modelos.md` (verified against the
> Django 5.2 docs). Where the two disagree, **the canon wins** — open an issue, don't fork the rule.

## Why a base class at all

Three fields repeat in every business table — *who made this, when, and is it still real*. Writing
them by hand on twelve models guarantees that the thirteenth forgets one, and the day you need "who
deleted the invoice?" the answer is nowhere. The base class makes the audit trail the default
instead of the thing you remember to add.

It costs one abstract model and buys: created/updated stamps, who did it, and **soft delete** —
rows leave the listing without leaving the database, which is the difference between "the client
deleted it by mistake" being a five-second fix or a restore-from-backup.

## The base class (copy into `apps/core/models.py`)

```python
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class AliveManager(models.Manager):
    """Only rows that have not been soft-deleted."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AuditableModel(models.Model):
    """Abstract base: timestamps, authorship and soft delete.

    Concrete models inherit it and add their own fields. Nothing here is magic —
    it is ordinary Django, so `makemigrations` sees these columns on every child table.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,      # deleting a user must not delete their work
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        editable=False,
    )

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
        editable=False,
    )
    deleted_reason = models.CharField(max_length=200, blank=True, default="")
    purge_after = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()   # everything, including soft-deleted
    alive = AliveManager()       # only live rows — see "Which manager" below

    class Meta:
        abstract = True

    # ---- soft delete ------------------------------------------------------

    def soft_delete(self, *, deleted_by=None, reason="", ttl_days=None):
        """Mark the row as deleted without removing it."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.deleted_reason = reason
        self.purge_after = (
            self.deleted_at + timedelta(days=ttl_days) if ttl_days else None
        )
        self.save(update_fields=[
            "is_deleted", "deleted_at", "deleted_by",
            "deleted_reason", "purge_after", "updated_at",
        ])

    def restore(self, *, restored_by=None):
        """Undo a soft delete. Clears ALL four deletion fields — see the note below."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deleted_reason = ""
        self.purge_after = None
        self.updated_by = restored_by
        self.save(update_fields=[
            "is_deleted", "deleted_at", "deleted_by", "deleted_reason",
            "purge_after", "updated_by", "updated_at",
        ])

    def permanent_delete(self):
        """Really delete the row. No undo."""
        return super().delete()
```

**`restore()` clears all four fields on purpose.** Setting only `is_deleted = False` leaves
`deleted_at` and `deleted_by` populated, so the row reads as "alive, and also deleted by Ana last
Tuesday". That stale audit trail is worse than none: the next person to read it believes it.

### `purge_after` ships without a purger — decide before you use it

`ttl_days` writes a date into `purge_after` and **nothing acts on it**. No cron, no command, no
signal. Either write the management command that deletes expired rows, or drop the field and the
`ttl_days` argument. A retention promise nobody executes is worse than an honest "we keep it
forever": it is the field someone will cite in a GDPR answer.

```python
# apps/core/management/commands/purge_expired.py  (you write this — it is not in the skill)
class Command(BaseCommand):
    def handle(self, *args, **options):
        for model in (Lead, Appointment):
            model.objects.filter(purge_after__lte=timezone.now()).delete()
```

### Which manager, and why the default shows deleted rows

| Manager | Returns | Use it in |
|---|---|---|
| `Model.objects` | **every** row, deleted included | admin, purge jobs, "restore" screens, migrations |
| `Model.alive` | only `is_deleted=False` | every view, every list the user sees |

The first manager declared becomes Django's `_default_manager`, which is what the admin, `dumpdata`
and related descriptors reach for. If that one hid rows, a soft-deleted record would silently vanish
from the admin and from `loaddata` round-trips, and you would debug it for an afternoon. So the
default is honest and **hiding is explicit**: `Lead.alive.all()`, or `filter(is_deleted=False)`.

The cost is real and worth stating: forgetting `.alive` in a view leaks deleted rows to the user.
That is a visible bug caught by one test; the alternative fails invisibly in tooling.

## History tracking — optional, and it is a real dependency

The base class above tracks *current* state (who last touched it). It does **not** keep the previous
values. If you need "what did this field say last month", add
[django-simple-history](https://django-simple-history.readthedocs.io/) — an actual PyPI package you
must install, not something this skill provides:

```bash
pip install django-simple-history          # verify it resolves before you rely on it
```

```python
# settings.py
INSTALLED_APPS = [..., "simple_history"]
```

```python
from simple_history.models import HistoricalRecords

class Lead(AuditableModel):
    ...
    history = HistoricalRecords()          # per concrete model, NOT on the abstract base
```

Then, and only then:

```python
lead.history.all()                          # every version, newest first
lead.history.filter(history_type="~")       # '+' created · '~' updated · '-' deleted
record.diff_against(record.prev_record)     # what changed between two versions
```

**`history.all()` is the accessor.** There is no `get_history()` helper — if you see that call
anywhere, it is a leftover and it will raise `AttributeError`.

Two things it does not catch, because they never load the model:

```python
Lead.objects.filter(status="new").update(status="contacted")   # no history, no auto_now
Lead.objects.bulk_create([...])                                # no history (see bulk_create docs)
```

Both are correct, fast, and invisible to the audit trail. Use them for volume, and when the change
must be auditable, loop and `save()` instead — the cost is deliberate.

## The example domain

Every example in `references/crud.md`, `references/optimization.md` and `references/advanced-queries.md` uses
this small CRM. Nothing else is assumed to exist:

```
Agency  1──N  Lead  1──N  Appointment  N──1  Property
                            (a viewing)        (the thing being sold)
```

- **Agency** — the tenant. Every row belongs to one.
- **Lead** — a potential customer, with a `status` moving `new → contacted → qualified → won/lost`.
- **Appointment** — a scheduled viewing linking a lead to a property.
- **Property** — the listing.

Swap the nouns for your domain; the patterns do not depend on them.

## A complete model

```python
from django.db import models
from apps.core.models import AuditableModel


class Lead(AuditableModel):
    """A potential customer."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")
    agency = models.ForeignKey(
        "agencies.Agency",
        on_delete=models.PROTECT,
        related_name="leads",
    )

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["phone", "agency"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def is_qualified(self):
        """Read-only predicate. Business RULES do not live here — see backend-servicios.md."""
        return self.status == self.Status.QUALIFIED
```

## Model rules (from the house canon — the checker enforces these)

1. **Inherit `AuditableModel`** for business tables. Lookup tables (countries, VAT rates) do not
   need an audit trail; plain `models.Model` is right for them.
2. **`TextChoices`, not loose string constants.** You get the DB `choices`, the label and
   `Lead.Status.NEW` in one place.
3. **`related_name` on every FK.** Without it Django invents `lead_set`, which no text search finds:
   renaming the model breaks queries silently.
4. **`blank=True, default=""` on text — never `null=True`.** Two empty states (`''` and `NULL`) means
   every query must check both, and the day one is forgotten the row vanishes from the listing.
   Exception: a field that is both optional and `unique` (a tax ID) — Postgres allows many `NULL`s
   but only one `''`.
5. **`Decimal` for money, never `FloatField`.** `0.10` has no float representation; the drift shows
   up in the monthly total, far from its cause.
6. **`on_delete` is a business decision.** `PROTECT` on anything with accounting value; `CASCADE`
   everywhere by default is how data disappears without an error.
7. **Constraints in the database**, not only in Python — a `CheckConstraint` also protects the
   import script and the shell. Django 5.1 removed `check=`; the argument is **`condition=`**.
8. **Index what you filter**, and set `ordering` in `Meta` so pagination is deterministic.

## Verify

```bash
python manage.py makemigrations --check --dry-run   # no model change left unmigrated
python manage.py check                              # no system warnings
python3 .claude/patterns/stack/pattern_check_backend.py   # house rules, AST-level
```

## Related

- `.claude/patterns/stack/backend-modelos.md` — the canon this file follows
- `.claude/patterns/stack/backend-servicios.md` — why rules do not live in `save()`
- `references/serializer-patterns.md` — the DRF layer (only if you expose an API)
- skill `migration-integrity-checks` — proving a backfill arrived intact
