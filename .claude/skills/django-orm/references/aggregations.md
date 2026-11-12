# Django ORM Aggregations

> Paths below are relative to `.claude/skills/django-orm/`.

> Domain and base model (`AuditableModel`, `Lead.alive`): defined in
> `references/model-patterns.md`. Everything here is stock Django.

## ⚠️ The trap to read first: aggregating over two relations at once

```python
# WRONG — both numbers are inflated
Lead.alive.annotate(
    appointment_count=Count("appointments"),
    document_count=Count("documents"),
)
```

Django resolves this as a single query joining **both** tables. A lead with 3 appointments and 2
documents produces 3 × 2 = 6 rows, so it reports `appointment_count=6` and `document_count=6`.
Nothing errors; the dashboard is just wrong, and it is wrong in a way that looks plausible.

```python
# RIGHT — for counts
Lead.alive.annotate(
    appointment_count=Count("appointments", distinct=True),
    document_count=Count("documents", distinct=True),
)

# RIGHT — for sums, where distinct cannot help (it would drop legitimate equal values)
from django.db.models import Subquery, OuterRef

appointment_totals = (
    Appointment.objects.filter(lead=OuterRef("pk"))
    .values("lead")
    .annotate(total=Sum("price"))
)
Lead.alive.annotate(appointment_total=Subquery(appointment_totals.values("total")[:1]))
```

Rule: **one relation per aggregate query.** Two relations → `distinct=True` if counting,
`Subquery` or a second query if summing or averaging.

## Basic Aggregations

```python
from django.db.models import Count, Sum, Avg, Max, Min, StdDev, Variance

# Single aggregation
total_leads = Lead.objects.count()
avg_price = Property.objects.aggregate(Avg('price'))

# Multiple aggregations
stats = Property.objects.aggregate(
    total=Count('id'),
    avg_price=Avg('price'),
    max_price=Max('price'),
    min_price=Min('price'),
    total_value=Sum('price'),
    price_stddev=StdDev('price')
)
# Returns: {'total': 150, 'avg_price': 250000, 'max_price': 1000000, ...}
```

## Conditional Aggregations

```python
from django.db.models import Q

# Count with filter
stats = Lead.objects.aggregate(
    total=Count('id'),
    new=Count('id', filter=Q(status='new')),
    qualified=Count('id', filter=Q(status='qualified')),
    won=Count('id', filter=Q(status='won'))
)
# Returns: {'total': 100, 'new': 30, 'qualified': 20, 'won': 15}

# Sum with condition
property_stats = Property.objects.aggregate(
    total_value=Sum('price'),
    available_value=Sum('price', filter=Q(is_available=True)),
    sold_value=Sum('price', filter=Q(status='sold'))
)
```

## Group By with Annotations

```python
# Group by single field
leads_by_status = Lead.objects.values('status').annotate(
    count=Count('id')
).order_by('status')
# Returns: [{'status': 'new', 'count': 30}, {'status': 'qualified', 'count': 20}, ...]

# Group by multiple fields
properties_by_type_location = Property.objects.values(
    'property_type', 'location'
).annotate(
    count=Count('id'),
    avg_price=Avg('price')
).order_by('property_type', 'location')

# Group by related field
leads_by_agency = Lead.objects.values('agency__name').annotate(
    total_leads=Count('id'),
    qualified_leads=Count('id', filter=Q(status='qualified'))
).order_by('-total_leads')
```

## Date-Based Aggregations

```python
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncYear

# By date
leads_by_date = Lead.objects.annotate(
    date=TruncDate('created_at')
).values('date').annotate(
    count=Count('id')
).order_by('date')

# By month
leads_by_month = Lead.objects.annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    count=Count('id'),
    qualified=Count('id', filter=Q(status='qualified'))
).order_by('month')

# By week
appointments_by_week = Appointment.objects.annotate(
    week=TruncWeek('scheduled_at')
).values('week').annotate(
    count=Count('id'),
    confirmed=Count('id', filter=Q(status='confirmed'))
).order_by('week')

# By year
properties_by_year = Property.objects.annotate(
    year=TruncYear('created_at')
).values('year').annotate(
    count=Count('id'),
    total_value=Sum('price')
).order_by('year')
```

## Conditional Aggregations with Case/When

```python
from django.db.models import Case, When, IntegerField, DecimalField

# Count by category
stats = Lead.objects.aggregate(
    active=Count(Case(
        When(status__in=['new', 'contacted'], then=1),
        output_field=IntegerField()
    )),
    qualified=Count(Case(
        When(status='qualified', then=1),
        output_field=IntegerField()
    )),
    closed=Count(Case(
        When(status__in=['won', 'lost'], then=1),
        output_field=IntegerField()
    ))
)

# Sum with conditions
property_value = Property.objects.aggregate(
    available_value=Sum(Case(
        When(is_available=True, then='price'),
        output_field=DecimalField()
    )),
    sold_value=Sum(Case(
        When(status='sold', then='price'),
        output_field=DecimalField()
    ))
)
```

## Aggregations with Expressions

```python
from django.db.models import F, ExpressionWrapper, DecimalField

# Average commission (price * commission_rate)
avg_commission = Property.objects.aggregate(
    avg_commission=Avg(
        ExpressionWrapper(
            F('price') * F('commission_rate'),
            output_field=DecimalField()
        )
    )
)

# Total area of available properties
total_area = Property.objects.filter(
    is_available=True
).aggregate(
    total_sqm=Sum('area')
)
```

## Nested Aggregations

```python
# Properties with most appointments
properties_with_most_appointments = Property.objects.annotate(
    appointment_count=Count('appointments')
).order_by('-appointment_count')[:10]

# Agencies with most qualified leads.
# All three aggregates target the SAME relation ('leads'), so one join serves them and the
# numbers stay correct — this is the safe shape, unlike the two-relation case at the top.
agencies_with_qualified = Agency.objects.annotate(
    total_leads=Count('leads', distinct=True),
    qualified_leads=Count('leads', filter=Q(leads__status='qualified'), distinct=True),
).order_by('-qualified_leads')

# The rate is computed in Python, NOT in the ORM:
#   Count(...) * 100.0 / Count('leads')  divides by zero for any agency with no leads —
#   i.e. every agency on its first day. Postgres raises, the whole dashboard 500s.
for agency in agencies_with_qualified:
    agency.conversion_rate = (
        round(agency.qualified_leads * 100 / agency.total_leads, 2)
        if agency.total_leads else 0.0
    )

# If it must happen in SQL (to sort or filter by it), guard the denominator with NullIf:
from django.db.models import F, FloatField
from django.db.models.functions import Cast, NullIf

agencies = Agency.objects.annotate(
    total_leads=Count('leads', distinct=True),
    qualified_leads=Count('leads', filter=Q(leads__status='qualified'), distinct=True),
).annotate(
    conversion_rate=Cast('qualified_leads', FloatField()) * 100.0
                    / NullIf(Cast('total_leads', FloatField()), 0.0)   # → NULL, not an error
).order_by(F('conversion_rate').desc(nulls_last=True))
```

## Best Practices

1. **Use aggregate()** for single-row results (total count, avg, etc.)
2. **Use annotate()** for per-object calculations (group by)
3. **Add filters** with filter parameter in aggregations
4. **Use values()** before annotate() for GROUP BY behavior
5. **Use distinct()** when counting across joins
6. **Profile queries** to ensure performance
7. **Index frequently aggregated fields**
