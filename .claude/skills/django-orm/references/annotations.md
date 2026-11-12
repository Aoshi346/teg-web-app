# Django ORM Annotations

> Paths below are relative to `.claude/skills/django-orm/`.

## Basic Annotations

```python
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

# Add computed field
leads_with_full_contact = Lead.objects.annotate(
    full_contact=Concat('name', Value(' - '), 'phone', output_field=CharField())
)
# Access: lead.full_contact -> "John Doe - +34123456789"

# Count related objects
properties_with_counts = Property.objects.annotate(
    appointment_count=Count('appointments'),
    lead_count=Count('appointments__lead', distinct=True)
)
# Access: property.appointment_count, property.lead_count
```

## Calculated Fields

```python
from django.db.models import F, ExpressionWrapper, DecimalField

# Price per square meter
properties_with_price_per_sqm = Property.objects.annotate(
    price_per_sqm=ExpressionWrapper(
        F('price') / F('area'),
        output_field=DecimalField()
    )
).filter(price_per_sqm__lte=3000)

# Commission amount
properties_with_commission = Property.objects.annotate(
    commission_amount=ExpressionWrapper(
        F('price') * F('commission_rate'),
        output_field=DecimalField()
    )
)

# Age of the record, evaluated by the database
from datetime import timedelta
from django.db.models import DurationField
from django.db.models.functions import Now

leads_with_age = Lead.alive.annotate(
    age=ExpressionWrapper(Now() - F('created_at'), output_field=DurationField())
).filter(age__lte=timedelta(days=30))

# ❌ NOT this — `timezone.now() - F('created_at')` builds a CombinedExpression, which has
#    no `.days` attribute. It raises AttributeError the moment the module is imported:
#        age_days=(timezone.now() - F('created_at')).days
#    Use Now() (the database clock) and compare against a timedelta.
```

## Conditional Annotations

```python
from django.db.models import Case, When, Value, BooleanField

# Is qualified flag
leads_with_flags = Lead.objects.annotate(
    is_qualified=Case(
        When(status='qualified', then=Value(True)),
        default=Value(False),
        output_field=BooleanField()
    ),
    is_hot=Case(
        When(score__gte=80, then=Value(True)),
        default=Value(False),
        output_field=BooleanField()
    )
)

# Priority level
leads_with_priority = Lead.objects.annotate(
    priority=Case(
        When(score__gte=80, then=Value('high')),
        When(score__gte=50, then=Value('medium')),
        default=Value('low'),
        output_field=CharField()
    )
)
```

## Aggregations in Annotations

```python
# Count related objects
leads_with_counts = Lead.objects.annotate(
    appointment_count=Count('appointments'),
    document_count=Count('documents'),
    note_count=Count('notes')
)

# Sum related values
properties_with_totals = Property.objects.annotate(
    total_appointments=Count('appointments'),
    total_commission=Sum(
        ExpressionWrapper(
            F('price') * F('commission_rate'),
            output_field=DecimalField()
        )
    )
)
```

## String Functions

```python
from django.db.models.functions import Lower, Upper, Length, Substr

# Lowercase/Uppercase
leads_normalized = Lead.objects.annotate(
    name_lower=Lower('name'),
    name_upper=Upper('name')
)

# String length
leads_with_lengths = Lead.objects.annotate(
    name_length=Length('name'),
    phone_length=Length('phone')
).filter(name_length__lt=5)

# Substring
leads_with_prefix = Lead.objects.annotate(
    phone_country=Substr('phone', 1, 3)  # First 3 chars
)
```

## Date/Time Functions

```python
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay, TruncDate

# Extract parts
leads_with_dates = Lead.objects.annotate(
    year=ExtractYear('created_at'),
    month=ExtractMonth('created_at'),
    day=ExtractDay('created_at')
)

# Truncate to date
appointments_by_date = Appointment.objects.annotate(
    date=TruncDate('scheduled_at')
).values('date').annotate(count=Count('id'))
```

## Subqueries in Annotations

```python
from django.db.models import Subquery, OuterRef

# Latest appointment date
latest_appointments = Appointment.objects.filter(
    lead=OuterRef('pk')
).order_by('-scheduled_at')

leads_with_latest = Lead.objects.annotate(
    latest_appointment_date=Subquery(
        latest_appointments.values('scheduled_at')[:1]
    )
)

# Count from subquery
qualified_count = Lead.objects.filter(
    agency=OuterRef('pk'),
    status='qualified'
).values('agency').annotate(count=Count('id'))

agencies_with_stats = Agency.objects.annotate(
    qualified_leads=Subquery(
        qualified_count.values('count')[:1]
    )
)
```

## Window Functions

```python
from django.db.models import Window, F
from django.db.models.functions import RowNumber, Rank, DenseRank

# Row number
properties_with_rank = Property.objects.annotate(
    row_number=Window(
        expression=RowNumber(),
        order_by=F('price').desc()
    )
)

# Rank within partition
properties_ranked_by_type = Property.objects.annotate(
    rank=Window(
        expression=Rank(),
        partition_by=[F('property_type')],
        order_by=F('price').desc()
    )
).filter(rank__lte=10)

# Dense rank (no gaps)
leads_ranked = Lead.objects.annotate(
    dense_rank=Window(
        expression=DenseRank(),
        order_by=F('score').desc()
    )
)
```

## Multiple Annotations

```python
# Combine multiple annotations
leads_enriched = Lead.alive.annotate(
    # Computed fields
    full_contact=Concat('name', Value(' - '), 'phone', output_field=CharField()),
    age=ExpressionWrapper(Now() - F('created_at'), output_field=DurationField()),

    # Aggregations over TWO different relations — see the warning below
    appointment_count=Count('appointments', distinct=True),
    document_count=Count('documents', distinct=True),

    # Conditional fields
    is_qualified=Case(
        When(status='qualified', then=Value(True)),
        default=Value(False),
        output_field=BooleanField()
    ),

    # Subqueries
    latest_appointment=Subquery(
        Appointment.objects.filter(
            lead=OuterRef('pk')
        ).order_by('-scheduled_at').values('scheduled_at')[:1]
    )
)
```

> ⚠️ **Two `Count`s over two DIFFERENT relations in one call inflate each other.** Django joins
> both tables, so a lead with 3 appointments and 2 documents yields 6 rows and reports
> `appointment_count=6, document_count=6`. `distinct=True` (above) fixes the count; if you are
> summing values rather than counting, `distinct` cannot save you — run a second query or use
> `Subquery`. Full explanation in `references/aggregations.md`.

> **A field computed from another annotation goes in a SEPARATE `annotate()`:**
>
> ```python
> Lead.alive.annotate(
>     appointment_count=Count("appointments"),
> ).annotate(                                     # ← second call
>     is_busy=Case(When(appointment_count__gte=5, then=Value(True)),
>                  default=Value(False), output_field=BooleanField()),
> )
> ```

## Performance Considerations

```python
# Efficient annotations (evaluated in DB)
leads = Lead.objects.annotate(
    appointment_count=Count('appointments')
).filter(appointment_count__gt=5)

# Use select_related/prefetch_related with annotations
leads = Lead.objects.select_related('agency').annotate(
    appointment_count=Count('appointments')
)

# Avoid N+1 with annotations
properties = Property.objects.annotate(
    latest_appointment=Subquery(...)
).prefetch_related('appointments')
```

## Best Practices

1. **Use F() objects** for database-level calculations
2. **Use ExpressionWrapper** for complex expressions
3. **Add output_field** when required by Django
4. **Profile queries** to ensure annotations are efficient
5. **Use distinct()** when necessary (joins can duplicate rows)
6. **Combine with select_related/prefetch_related** for optimization
7. **Use subqueries** for complex related data
