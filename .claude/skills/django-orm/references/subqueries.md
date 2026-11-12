# Django ORM Subqueries

> Paths below are relative to `.claude/skills/django-orm/`.

> Domain and base model (`AuditableModel`, `Lead.alive`): defined in
> `references/model-patterns.md`.
>
> **`Subquery` is not needed for an `__in` lookup.** `filter(x__in=some_queryset)` already
> compiles to a subquery. Wrapping it (`__in=Subquery(qs.values_list("id", flat=True))`)
> produces the same SQL with more noise — several examples below have been simplified
> accordingly. Reach for `Subquery` when you need a **value** from a related row
> (`annotate(latest=Subquery(...))`), and for `Exists` when you need a boolean.

## Basic Subquery

```python
from django.db.models import Subquery, OuterRef

# Get latest appointment date for each lead
latest_appointments = Appointment.objects.filter(
    lead=OuterRef('pk')
).order_by('-scheduled_at')

leads_with_latest = Lead.objects.annotate(
    latest_appointment_date=Subquery(
        latest_appointments.values('scheduled_at')[:1]
    )
)
# Access: lead.latest_appointment_date
```

## Subquery with Filter

```python
# Properties with at least one qualified lead.
# Pass the queryset straight to __in — no Subquery() wrapper needed.
qualified_leads = Lead.alive.filter(status='qualified')

properties_with_qualified = Property.objects.filter(
    appointments__lead__in=qualified_leads
).distinct()          # distinct(): the join repeats the property once per matching appointment

# Agencies with high-performing leads
agencies = Agency.objects.filter(
    leads__in=Lead.alive.filter(score__gte=80)
).distinct()

# Better still when you only need "does one exist" — Exists stops at the first match,
# while the __in form materialises the whole id set:
from django.db.models import Exists, OuterRef

agencies = Agency.objects.filter(
    Exists(Lead.alive.filter(agency=OuterRef('pk'), score__gte=80))
)                     # no distinct() needed: no join, no duplicated rows
```

## Subquery with Annotations

```python
# Average score per agency
avg_scores = Lead.objects.filter(
    agency=OuterRef('pk')
).values('agency').annotate(
    avg_score=Avg('score')
)

agencies_with_avg_score = Agency.objects.annotate(
    avg_lead_score=Subquery(
        avg_scores.values('avg_score')[:1]
    )
)

# Total appointments per property
appointment_counts = Appointment.objects.filter(
    property=OuterRef('pk')
).values('property').annotate(
    count=Count('id')
)

properties_with_counts = Property.objects.annotate(
    total_appointments=Subquery(
        appointment_counts.values('count')[:1]
    )
)
```

## Exists Subquery

```python
from django.db.models import Exists

# Properties with confirmed appointments
confirmed_appointments = Appointment.objects.filter(
    property=OuterRef('pk'),
    status='confirmed'
)

properties_with_confirmed = Property.objects.annotate(
    has_confirmed_appointments=Exists(confirmed_appointments)
).filter(has_confirmed_appointments=True)

# Leads without any appointments
has_appointments = Appointment.objects.filter(
    lead=OuterRef('pk')
)

leads_without_appointments = Lead.objects.annotate(
    has_appointments=Exists(has_appointments)
).filter(has_appointments=False)
```

## Multiple Subqueries

```python
# Leads with multiple subqueries
latest_appointment = Appointment.objects.filter(
    lead=OuterRef('pk')
).order_by('-scheduled_at')

total_appointments = Appointment.objects.filter(
    lead=OuterRef('pk')
).values('lead').annotate(count=Count('id'))

leads_enriched = Lead.objects.annotate(
    latest_appointment_date=Subquery(
        latest_appointment.values('scheduled_at')[:1]
    ),
    appointment_count=Subquery(
        total_appointments.values('count')[:1]
    )
)
```

## Subquery with Case/When

```python
# Property status based on appointments
recent_appointments = Appointment.objects.filter(
    property=OuterRef('pk'),
    scheduled_at__gte=timezone.now() - timedelta(days=30)
).values('property').annotate(count=Count('id'))

# The Case reads recent_appointment_count, so it goes in a SECOND annotate() —
# a field computed from another annotation cannot be defined in the same call.
properties_with_status = Property.objects.annotate(
    recent_appointment_count=Subquery(
        recent_appointments.values('count')[:1]
    ),
).annotate(
    temperature=Case(
        When(recent_appointment_count__gt=5, then=Value('hot')),
        When(recent_appointment_count__gt=0, then=Value('warm')),
        default=Value('cold'),
        output_field=CharField()
    )
)
# Named `temperature`, not `status`: annotating with the name of an existing model field
# raises ValueError ("The annotation 'status' conflicts with a field on the model").
```

## Correlated Subqueries

```python
# Leads with score above agency average
agency_avg_score = Lead.objects.filter(
    agency=OuterRef('agency')
).values('agency').annotate(
    avg=Avg('score')
)

leads_above_average = Lead.objects.annotate(
    agency_avg_score=Subquery(
        agency_avg_score.values('avg')[:1]
    )
).filter(score__gt=F('agency_avg_score'))

# Properties priced below type average
type_avg_price = Property.objects.filter(
    property_type=OuterRef('property_type')
).values('property_type').annotate(
    avg=Avg('price')
)

properties_below_average = Property.objects.annotate(
    type_avg_price=Subquery(
        type_avg_price.values('avg')[:1]
    )
).filter(price__lt=F('type_avg_price'))
```

## Subquery with Aggregations

```python
# Total value of properties per agency
property_values = Property.objects.filter(
    agency=OuterRef('pk')
).values('agency').annotate(
    total=Sum('price')
)

agencies_with_portfolio_value = Agency.objects.annotate(
    total_property_value=Subquery(
        property_values.values('total')[:1]
    )
)

# Average appointment duration per lead
appointment_durations = Appointment.objects.filter(
    lead=OuterRef('pk')
).values('lead').annotate(
    avg_duration=Avg('duration')
)

leads_with_avg_duration = Lead.objects.annotate(
    avg_appointment_duration=Subquery(
        appointment_durations.values('avg_duration')[:1]
    )
)
```

## JSON Fields — usually no subquery at all

```python
# Filter the JSON field directly. The subquery-on-itself version some codebases carry
# (`Property.objects.filter(id__in=Property.objects.filter(...))`) is a no-op wrapper
# around exactly this query.
properties_with_parking = Property.objects.filter(features__parking=True)

properties = Property.objects.filter(features__amenities__has_key='gym')

# A subquery IS warranted when the JSON lives on a DIFFERENT model:
from django.db.models import Exists, OuterRef

leads_who_saw_a_pool = Lead.alive.filter(
    Exists(
        Appointment.objects.filter(
            lead=OuterRef('pk'),
            property__features__pool=True,
        )
    )
)
```

JSON lookups do not use ordinary B-tree indexes — add a GIN index on the field if you filter on it
regularly.

## Nested Subqueries

```python
# Properties viewed by a high-scoring lead.
# Each step passes a queryset to __in; no Subquery() wrapper anywhere.
high_score_leads = Lead.alive.filter(score__gte=80)

properties_with_high_score_leads = Property.objects.filter(
    appointments__lead__in=high_score_leads
).distinct()

# Two hops, expressed as a relation traversal instead of nested subqueries —
# shorter, and the planner handles it better.
agencies_with_qualified = Agency.objects.filter(
    leads__status='qualified',
    leads__appointments__status='confirmed',
).distinct()

# Same thing with Exists, when the outer query already has other filters:
agencies_with_qualified = Agency.objects.filter(
    Exists(
        Lead.alive.filter(
            agency=OuterRef('pk'),
            status='qualified',
            appointments__status='confirmed',
        )
    )
)
```

## Performance Optimization

```python
# Pass the queryset directly — Django builds the subquery itself
appointments = Appointment.objects.filter(
    lead__in=Lead.alive.filter(status='qualified')
)

# Use select_related/prefetch_related with subqueries
properties = Property.objects.annotate(
    latest_appointment=Subquery(...)
).select_related('agency').prefetch_related('appointments')

# Limit subquery results
latest_appointment = Appointment.objects.filter(
    lead=OuterRef('pk')
).order_by('-scheduled_at')[:1]  # Limit to 1 result
```

## Best Practices

1. **Use Subquery to pull a VALUE** from a related row (`annotate(latest=Subquery(...))`).
   For an `__in` filter, pass the queryset directly — `Subquery()` around it changes nothing.
2. **Use Exists** for boolean checks — it stops at the first match, `Count(...) > 0` does not
3. **Limit subquery results** with [:1] when appropriate
4. **Use values()** in subqueries for better performance
5. **Avoid deep nesting** (2-3 levels max)
6. **Profile queries** to ensure subqueries are efficient
7. **Consider prefetch_related** as alternative when appropriate
8. **Use distinct()** when subqueries can return duplicates
