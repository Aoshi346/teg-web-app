# Django ORM CRUD

> Reference of the `django-orm` skill (was the skill `django-orm-crud`, merged on 2026-10-19 —
> LI-10). Paths below are relative to `.claude/skills/django-orm/`.

CRUD with the Django ORM, in a template project: the model layer, where the business rules go, and
the two ways of exposing it to the outside world.

## Before you start: the two things this skill assumes

**1. The base class.** Examples inherit from `AuditableModel` — timestamps, `created_by`/`updated_by`
and soft delete. It is **defined in full in `references/model-patterns.md`**; copy that block into
`apps/core/models.py`. It is ordinary Django, with no dependency beyond Django itself.

**2. The example domain.** A small CRM. Nothing outside this diagram is assumed to exist:

```
Agency  1──N  Lead  1──N  Appointment  N──1  Property
```

## Which path — server-rendered or API?

**Decide this first; it changes half the code.** Both paths share the model and the service layer;
they differ only in the outermost ring.

| | **Path A — server-rendered** | **Path B — REST API** |
|---|---|---|
| The browser gets | HTML rendered by Django | JSON |
| Validation lives in | the project's `ModelForm` base | DRF serializer |
| The view is | `ListView`, `CreateView`, `UpdateView`… | `ModelViewSet` |
| Extra dependency | none — Django ships it | `djangorestframework` |
| Use it when | Django renders the pages | a SPA or a mobile app consumes the data |
| The canon | **`.claude/patterns/stack/backend-formularios-django.md`** | `.claude/patterns/stack/backend-serializers.md` |

**Both are first-class archetypes of the house pattern — neither is the default.** Look at the repo
before choosing: adding DRF to a server-rendered project because a skill showed a ViewSet is how a
codebase grows two ways of doing everything. A backend with 385 form classes and one `ModelViewSet`
is a Path A project, whatever the skill's examples happen to show.

```bash
# Which is this project? Count before you assume.
grep -rl "forms.ModelForm\|forms.Form" --include=*.py . | wc -l
grep -rl "ModelViewSet\|APIView"        --include=*.py . | wc -l
```

## The layer map (both paths)

| Layer | Holds | Never holds |
|---|---|---|
| **Model** | fields, constraints, read-only predicates (`is_qualified()`) | business rules, side effects |
| **Service** (`services.py`) | anything beyond "save what arrived": state changes, multi-model writes, sending, charging | `request`, `Response`, DRF imports |
| **Form / Serializer** | shape validation — required, format, cross-field. In Path A the shared form base **also** sanitises text and stamps authorship | orchestration, side effects |
| **View** | HTTP ↔ domain: resolve the caller's queryset, call the service, map the exception to a status | business rules |

This is the house canon (`.claude/patterns/stack/backend-servicios.md`). The one-line test for
whether something belongs in a service: **who else could need to call it?** A rule inside a view can
only ever run from an incoming HTTP request — not from a cron, not from `manage.py`, not from a test
without faking a request.

```python
# apps/leads/services.py — no HTTP anywhere in this file
from django.db import transaction


class LeadNotQualifiable(Exception):
    """Domain error. The view decides which status code it means."""


@transaction.atomic
def qualify_lead(*, lead_id: str, qualified_by) -> Lead:
    lead = Lead.objects.select_for_update().get(pk=lead_id)   # lock: two clicks, one qualify
    if lead.status != Lead.Status.NEW:
        raise LeadNotQualifiable(f"lead {lead.pk} is already {lead.status}")

    lead.status = Lead.Status.QUALIFIED
    lead.updated_by = qualified_by
    lead.save(update_fields=["status", "updated_by", "updated_at"])   # 3 columns, not the row
    return lead
```

Keyword-only (`*`) so two same-typed ids cannot be swapped silently. Full worked example, including
`transaction.on_commit` for Celery: `.claude/patterns/stack/backend-servicios.md`.

**Plain CRUD needs no service.** If the operation is exactly "save the validated input", a service of
one line is noise — `form.save()` / `serializer.save()` is the right answer.

---

# Path A — server-rendered views and forms

## The form

**Inherit from the project's form base, never from `django.forms.ModelForm` directly.** In a
server-rendered backend the form is not a presentation layer — it is *the* integrity layer, the only
door with validation on it. The shared base is where text gets sanitised (XSS), where authorship is
stamped and where the profile's read-only fields are applied. A form that skips it silently skips
all three. Full base class and the reasoning: `.claude/patterns/stack/backend-formularios-django.md`.

```python
# apps/leads/forms.py
from django import forms

from apps.core.forms import ModelForm      # ← the project's base, not django.forms.ModelForm
from .models import Lead


class LeadForm(ModelForm):
    class Meta:
        model = Lead
        fields = ["name", "phone", "email", "status", "notes"]
        # Enumerate always. Never "__all__", never `exclude`: a whitelist protects the fields
        # that do not exist yet — a blacklist only protects the ones you already knew about.

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if not phone.startswith("+"):
            raise forms.ValidationError("Phone must start with + and the country code.")
        return phone

    def clean(self):
        cleaned = super().clean()          # super() first: that is what sanitises the strings
        if cleaned.get("status") == Lead.Status.QUALIFIED and not cleaned.get("email"):
            raise forms.ValidationError("A qualified lead needs an email address.")
        return cleaned
```

> ⚠️ **`request` is the FIRST positional argument of the house base**
> (`def __init__(self, request=None, data=None, files=None, ...)`). So `LeadForm(request.POST)`
> passes the `QueryDict` as `request`, the form stays **unbound**, `is_valid()` returns `False`
> forever and **nothing raises**: the page just re-renders blank. Instantiate by keyword —
> `LeadForm(request=request, data=request.POST)` — or let the CBV do it, as below. The checker rule
> is `be-form-request-primero`.

## The views

```python
# apps/leads/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import LeadForm
from .models import Lead


class LeadScopedMixin(LoginRequiredMixin):
    """Every view sees only this user's agency, and only live rows.

    On the mixin and not copy-pasted per view: detail, update and delete inherit the
    same filter, so there is no fourth place to forget it.
    """

    def get_queryset(self):
        return Lead.alive.filter(agency=self.request.user.agency)


class LeadListView(LeadScopedMixin, ListView):
    template_name = "leads/lead_list.html"
    context_object_name = "leads"
    paginate_by = 50                      # never render an unbounded table

    def get_queryset(self):
        return super().get_queryset().select_related("agency").order_by("-created_at")


class LeadDetailView(LeadScopedMixin, DetailView):
    template_name = "leads/lead_detail.html"


class LeadFormViewMixin(LeadScopedMixin):
    """Hands the request to the form base — which is what stamps authorship.

    Django's CBVs pass data/files/instance as KEYWORDS, so adding request here is safe with a
    base whose signature starts with `request`. Do NOT also set created_by/updated_by in
    form_valid(): the base's save() already does it, and two places that stamp the same field
    diverge the first time one of them changes.
    """

    form_class = LeadForm
    template_name = "leads/lead_form.html"
    success_url = reverse_lazy("leads:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class LeadCreateView(LeadFormViewMixin, CreateView):
    def form_valid(self, form):
        # Only what the base does NOT know about: the tenant.
        form.instance.agency = self.request.user.agency
        return super().form_valid(form)


class LeadUpdateView(LeadFormViewMixin, UpdateView):
    pass        # the base stamps updated_by; there is nothing left to add


class LeadDeleteView(LeadScopedMixin, DeleteView):
    template_name = "leads/lead_confirm_delete.html"
    success_url = reverse_lazy("leads:list")

    def form_valid(self, form):
        """Soft delete instead of removing the row.

        GOTCHA: since Django 4.0 DeleteView posts through a form, so the hook is
        form_valid(). Overriding delete() — the pre-4.0 recipe — is silently ignored
        on a POST, and the row gets hard-deleted by the parent class.
        """
        self.object = self.get_object()
        self.object.soft_delete(deleted_by=self.request.user, reason="Deleted from the UI")
        return HttpResponseRedirect(self.get_success_url())
```

Calling a service from a view is the same two lines in both paths:

```python
from django.contrib import messages
from django.shortcuts import redirect

from .services import LeadNotQualifiable, qualify_lead


def post(self, request, pk):
    try:
        qualify_lead(lead_id=pk, qualified_by=request.user)
    except LeadNotQualifiable as exc:
        messages.error(request, str(exc))
    return redirect("leads:detail", pk=pk)
```

---

# Path B — DRF API

Only if the project already exposes an API. Serializer detail: `references/serializer-patterns.md`.

## Serializer

```python
from rest_framework import serializers
from .models import Lead


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["id", "name", "phone", "email", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        # Explicit list, never __all__ — patterns/stack/backend-serializers.md (be-ser-fields-all).

    def validate_phone(self, value):
        if not value.startswith("+"):
            raise serializers.ValidationError("Phone must start with + and the country code.")
        return value

    def validate(self, attrs):
        if attrs.get("status") == Lead.Status.QUALIFIED and not attrs.get("email"):
            raise serializers.ValidationError("A qualified lead needs an email address.")
        return attrs
```

## ViewSet

The four decisions that matter. **The complete annotated version — filters, bulk actions, history,
serializer switching — is `assets/crud-template.py`;** it is not repeated here.

```python
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import LeadNotQualifiable, qualify_lead


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]      # explicit, even with a closed default in settings

    def get_queryset(self):
        """1. get_queryset(), never `queryset = ...`.

        A class attribute is evaluated once at import time and cannot see self.request, so
        the owner filter cannot live there. ModelViewSet derives list, retrieve, update AND
        destroy from this one method — one correct implementation covers all four, and one
        mistake opens all four.
        """
        return Lead.alive.filter(agency=self.request.user.agency).select_related("agency")

    # 2. Stamp authorship on the way in.
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, agency=self.request.user.agency)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    # 3. DELETE means soft delete.
    def perform_destroy(self, instance):
        instance.soft_delete(deleted_by=self.request.user, reason="Deleted via API")

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        # get_queryset() hides deleted rows, so restore looks them up explicitly —
        # still scoped to the tenant, or it becomes an IDOR.
        lead = get_object_or_404(
            Lead.objects.filter(agency=request.user.agency), pk=pk, is_deleted=True
        )
        lead.restore(restored_by=request.user)
        return Response(self.get_serializer(lead).data, status=status.HTTP_200_OK)

    # 4. Business action → call the service, translate the exception.
    @action(detail=True, methods=["post"])
    def qualify(self, request, pk=None):
        try:
            lead = qualify_lead(lead_id=pk, qualified_by=request.user)
        except LeadNotQualifiable as exc:
            raise ValidationError(str(exc)) from exc     # raise, don't return Response
        return Response(self.get_serializer(lead).data)
```

`raise ValidationError` and not `return Response({"error": ...}, status=400)`: only a **raised**
exception passes through DRF's `EXCEPTION_HANDLER`, so a returned error escapes the project's error
envelope and the frontend renders nothing. See `.claude/patterns/stack/backend-vistas.md`.

---

# Shared patterns

## Soft delete, restore, history

```python
lead.soft_delete(deleted_by=request.user, reason="Duplicate", ttl_days=30)
lead.restore(restored_by=request.user)      # clears all four deletion fields
lead.permanent_delete()                     # really gone

Lead.alive.all()                            # what users see
Lead.objects.filter(is_deleted=True)        # the recycle bin
lead.history.all()                          # only with django-simple-history installed
```

## Bulk operations — fast, and blind to the audit trail

`bulk_create()` and queryset `.update()` run in one query and **neither loads the model**: no
`save()`, no signals, no `auto_now` on `updated_at`, no history row. That is the price of the speed,
and it is the right trade for importing 10.000 rows — and the wrong one for a soft delete, which is
why the `references/optimization.md` checklist tells you to loop there.

| Need | Use | Cost |
|---|---|---|
| Import / migrate volume, no audit needed | `bulk_create()` / `.update()` | 1 query, no trail |
| Anything a user will be asked about later | loop + `save()` / `soft_delete()` | N queries, full trail |

Pick deliberately and leave the reason in a comment. Detail: `references/model-patterns.md`.

## Transactions

```python
@transaction.atomic
def create_lead_with_appointment(*, lead_data: dict, appointment_data: dict, created_by):
    lead = Lead.objects.create(**lead_data, created_by=created_by)
    appointment = Appointment.objects.create(lead=lead, **appointment_data, created_by=created_by)
    return lead, appointment
```

This function belongs in `services.py`. If it also fires a Celery task, the task goes in
`transaction.on_commit(...)` — otherwise the worker can pick it up before the COMMIT and not find the
row (`.claude/patterns/stack/backend-celery.md`).

## Best practices

1. **Filter by owner in `get_queryset()`**, once, so all four operations inherit it.
2. **`soft_delete()` on auditable models**; `delete()` only where losing the row is fine.
3. **Stamp `created_by` / `updated_by` in exactly one place** — the shared form base (A) or
   `perform_create`/`perform_update` (B). Never both.
4. **Validate shape** in the form/serializer; **business rules** in the service.
5. **Read through `.alive`**; `objects` only for the admin, the recycle bin and purge jobs.
6. **Paginate every list** — `paginate_by` (A) or `DEFAULT_PAGINATION_CLASS` (B).
7. **Wrap multi-model writes** in `@transaction.atomic`, with `select_for_update()` where two
   requests can race.
8. **Choose bulk vs loop on purpose** and leave the reason in a comment.

## Common pitfalls

- Reading with `objects` instead of `.alive` → deleted rows reappear in the UI.
- `queryset = Lead.objects.all()` with no `get_queryset()` → every tenant sees every row, and can
  edit and delete them too.
- `restore()` that only flips `is_deleted` → stale `deleted_at`/`deleted_by`, a lying audit trail.
- Overriding `delete()` on a `DeleteView` (Django ≥ 4.0) → ignored; the row is hard-deleted.
- `fields = "__all__"` **or `exclude`** on a form or serializer → the next field added becomes
  writable, and `exclude` looks controlled while doing it.
- **Path A: inheriting `django.forms.ModelForm` instead of the project's base** → no sanitising, no
  authorship, no read-only fields. The row saves, the user sees success, and it is wrong in three
  ways at once.
- **Path A: `LeadForm(request.POST)`** → `request` is the base's first argument; the form stays
  unbound, `is_valid()` is always `False`, and nothing raises.
- Expecting `.update()` / `bulk_create()` to leave history or bump `updated_at`.
- Business rules in the serializer's `validate()` → unreachable from a cron or a command.
- `return Response({"error": ...}, status=400)` → bypasses the error envelope.

## Testing

```python
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_create_lead_stamps_the_author(client, user, agency):
    client.force_login(user)
    response = client.post(reverse("leads:create"), {
        "name": "John Doe", "phone": "+34600000000", "status": "new", "notes": "",
    })
    assert response.status_code == 302
    lead = Lead.objects.get()
    assert lead.created_by == user and lead.agency == agency


def test_soft_delete_hides_but_keeps(user, lead):
    lead.soft_delete(deleted_by=user, reason="test")
    assert Lead.alive.count() == 0          # gone from the listing
    assert Lead.objects.count() == 1        # still in the table
    assert lead.deleted_by == user


def test_restore_clears_the_whole_deletion_trail(user, lead):
    lead.soft_delete(deleted_by=user, reason="oops")
    lead.restore(restored_by=user)
    assert (lead.is_deleted, lead.deleted_at, lead.deleted_by) == (False, None, None)


def test_a_user_cannot_read_another_agency(client, user, other_agency_lead):
    client.force_login(user)
    assert client.get(
        reverse("leads:detail", args=[other_agency_lead.pk])
    ).status_code == 404
```

That last test is the one worth writing first: tenant leakage is the failure that does not raise an
exception, so nothing tells you about it except a test that looks for it.

## Verify before DONE

```bash
python manage.py check                              # no system warnings
python manage.py makemigrations --check --dry-run   # nothing left unmigrated
pytest apps/leads/ -v --maxfail=3                   # by module — check RAM first
```

RAM before pytest is not optional here: `bash .claude/hooks/check-ram.sh` (`rules/ram-pytest.md`).
New endpoint? Call it once for real before reporting DONE (`rules/verification.md` §Smoke testing).

## Resources

- **`references/model-patterns.md`** — defines `AuditableModel`, the example domain, model rules
- **`references/serializer-patterns.md`** — DRF serializers (Path B only)
- **`assets/crud-template.py`** — annotated ViewSet template (Path B only)

## Related

- `.claude/patterns/stack/backend-formularios-django.md` — **Path A canon**: the form base, the
  `request`-first gotcha, why the form is the integrity layer
- `.claude/patterns/stack/backend-serializers.md` — Path B canon
- `.claude/patterns/stack/backend-servicios.md` · `.claude/patterns/stack/backend-vistas.md` ·
  `.claude/patterns/stack/backend-modelos.md` — shared canon these examples follow
- `references/optimization.md` — when the list view got slow
- skill `multi-tenant-context` — if isolation is stricter than one FK
- `.claude/patterns/stack/backend-vistas.md` — endpoint, URL and status-code conventions (measured)
- skill `code-review-gate` §Seguridad Django/DRF (permisos, IDOR)
