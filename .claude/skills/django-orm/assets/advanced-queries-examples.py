# runner: none — a template to copy into apps/<app>/ (see references/advanced-queries.md); never run on its own
"""Runnable report functions — advanced Django ORM queries.

Domain: the example CRM defined in
`references/model-patterns.md`:

    Agency  1──N  Lead  1──N  Appointment  N──1  Property

Adjust the model import paths on the next lines to your project (`apps.<app>.models`) — everything
below is stock Django. Nothing here imports a package that is not Django or your own code.

These belong in `services.py` (or `reports.py`) — plain functions that know nothing about HTTP, so
a view, a Celery task and a management command can all call them.
See `.claude/patterns/stack/backend-servicios.md`.
"""

from datetime import timedelta

from django.db.models import (
    Avg,
    BooleanField,
    Case,
    Count,
    DecimalField,
    DurationField,
    ExpressionWrapper,
    F,
    Max,
    Min,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Now, TruncMonth
from django.utils import timezone

# ── adjust these to your project ────────────────────────────────────────────
from apps.agencies.models import Agency
from apps.appointments.models import Appointment
from apps.leads.models import Lead
from apps.properties.models import Property


# ========== Dashboard ==========


def get_dashboard_stats(*, agency=None) -> dict:
    """Headline counts, in a single query.

    Returns the raw counts plus a conversion rate computed in Python. The rate is NOT an
    ORM expression on purpose: `won * 100 / total` raises ZeroDivisionError the day the
    dashboard is opened by an agency with no leads yet — which is every agency on day one.
    """
    queryset = Lead.alive.all()
    if agency is not None:
        queryset = queryset.filter(agency=agency)

    stats = queryset.aggregate(
        total=Count("id"),
        new=Count("id", filter=Q(status=Lead.Status.NEW)),
        contacted=Count("id", filter=Q(status=Lead.Status.CONTACTED)),
        qualified=Count("id", filter=Q(status=Lead.Status.QUALIFIED)),
        won=Count("id", filter=Q(status=Lead.Status.WON)),
        lost=Count("id", filter=Q(status=Lead.Status.LOST)),
    )
    total = stats["total"]
    stats["conversion_rate"] = round(stats["won"] * 100 / total, 2) if total else 0.0
    return stats


def get_leads_by_month(*, months: int = 12, agency=None):
    """Leads per calendar month, newest bucket last.

    Order matters: annotate the bucket → values() to group by it → annotate the aggregates.
    """
    cutoff = timezone.now() - timedelta(days=30 * months)

    queryset = Lead.alive.filter(created_at__gte=cutoff)
    if agency is not None:
        queryset = queryset.filter(agency=agency)

    return (
        queryset.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            total=Count("id"),
            qualified=Count("id", filter=Q(status=Lead.Status.QUALIFIED)),
            won=Count("id", filter=Q(status=Lead.Status.WON)),
        )
        .order_by("month")
    )


# ========== Property analytics ==========


def get_properties_with_analytics():
    """Per-property engagement metrics.

    Note the two chained annotate() calls: `is_hot` reads `total_appointments`, and a computed
    field that depends on another one goes in a SEPARATE annotate() — not in the same call.
    """
    latest_appointment = Appointment.objects.filter(property=OuterRef("pk")).order_by(
        "-scheduled_at"
    )

    return (
        Property.objects.annotate(
            total_appointments=Count("appointments", distinct=True),
            unique_leads=Count("appointments__lead", distinct=True),
            price_per_sqm=ExpressionWrapper(
                F("price") / F("area"), output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
            latest_appointment_date=Subquery(latest_appointment.values("scheduled_at")[:1]),
        )
        .annotate(
            is_hot=Case(
                When(total_appointments__gte=10, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )
        .select_related("agency")
        .order_by("-total_appointments")
    )


def get_properties_by_type_stats():
    """Group by property type.

    Only ONE relation is aggregated here (`appointments`). Adding a second relation to the same
    call would multiply the rows and inflate both counts — see references/aggregations.md.
    """
    return (
        Property.objects.values("property_type")
        .annotate(
            count=Count("id", distinct=True),
            avg_price=Avg("price"),
            max_price=Max("price"),
            min_price=Min("price"),
            total_value=Sum("price"),
            total_appointments=Count("appointments"),
        )
        .order_by("-count")
    )


# ========== Lead scoring ==========


def get_hot_leads(*, min_appointments: int = 3, max_age_days: int = 30):
    """Leads with recent, repeated engagement.

    `age` is a DurationField expression evaluated by the database. The tempting
    `(timezone.now() - F("created_at")).days` does NOT work: subtracting an F() produces a
    CombinedExpression, which has no `.days` — it raises AttributeError at import time.
    """
    return (
        Lead.alive.annotate(
            total_appointments=Count("appointments", distinct=True),
            confirmed_appointments=Count(
                "appointments", filter=Q(appointments__status="confirmed"), distinct=True
            ),
            age=ExpressionWrapper(Now() - F("created_at"), output_field=DurationField()),
        )
        .annotate(
            engagement_score=F("total_appointments") * 10 + F("confirmed_appointments") * 20,
        )
        .filter(
            total_appointments__gte=min_appointments,
            age__lte=timedelta(days=max_age_days),
        )
        .select_related("agency")
        .order_by("-engagement_score")
    )


def get_leads_above_agency_average():
    """Correlated subquery: leads scoring above their own agency's average."""
    agency_avg = (
        Lead.alive.filter(agency=OuterRef("agency"))
        .values("agency")
        .annotate(avg=Avg("score"))
    )

    return (
        Lead.alive.annotate(agency_avg_score=Subquery(agency_avg.values("avg")[:1]))
        .filter(score__gt=F("agency_avg_score"))
        .select_related("agency")
        .order_by("-score")
    )


# ========== Search ==========


def search_properties(*, query: str = "", filters: dict | None = None):
    """Full-text search plus optional structured filters.

    filters keys (all optional): price_min, price_max, bedrooms_min, bathrooms_min,
    area_min, area_max, property_type, features (dict of JSON lookups).
    """
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

    filters = filters or {}
    queryset = Property.objects.all()

    if query:
        # Build the vector ONCE and reuse it: repeating the expression makes Postgres
        # compute it twice per row.
        vector = SearchVector("title", weight="A") + SearchVector(
            "description", "address", weight="B"
        )
        search_query = SearchQuery(query)
        queryset = queryset.annotate(search=vector, rank=SearchRank(vector, search_query)).filter(
            search=search_query
        )

    criteria = Q()
    if (value := filters.get("price_min")) is not None:
        criteria &= Q(price__gte=value)
    if (value := filters.get("price_max")) is not None:
        criteria &= Q(price__lte=value)
    if (value := filters.get("bedrooms_min")) is not None:
        criteria &= Q(bedrooms__gte=value)
    if (value := filters.get("bathrooms_min")) is not None:
        criteria &= Q(bathrooms__gte=value)
    if (value := filters.get("area_min")) is not None:
        criteria &= Q(area__gte=value)
    if (value := filters.get("area_max")) is not None:
        criteria &= Q(area__lte=value)
    if (value := filters.get("property_type")) is not None:
        criteria &= Q(property_type=value)
    for key, value in (filters.get("features") or {}).items():
        criteria &= Q(**{f"features__{key}": value})

    queryset = queryset.filter(criteria).distinct()

    return queryset.order_by("-rank", "-created_at") if query else queryset.order_by("-created_at")


# ========== Agency performance ==========


def get_agency_performance_report():
    """Per-agency totals.

    All the counts target the SAME relation (`leads`), so one JOIN serves them all and the
    numbers stay honest. Mixing in `Count("properties")` here would multiply every lead count
    by the number of properties — run that as a second query instead.
    """
    return (
        Agency.objects.annotate(
            total_leads=Count("leads", distinct=True),
            qualified_leads=Count(
                "leads", filter=Q(leads__status=Lead.Status.QUALIFIED), distinct=True
            ),
            won_leads=Count("leads", filter=Q(leads__status=Lead.Status.WON), distinct=True),
        )
        .order_by("-total_leads")
    )


def get_agency_portfolio_value():
    """Second query, on purpose — see the docstring above."""
    return Agency.objects.annotate(
        total_properties=Count("properties", distinct=True),
        total_property_value=Sum("properties__price"),
    ).order_by("-total_property_value")


# ========== Sanity checks ==========
#
# Run these against a test database with known data. An analytics function with no
# cross-check is a number nobody can defend.
#
#   def test_dashboard_matches_hand_count(lead_factory):
#       lead_factory.create_batch(3, status="won")
#       lead_factory.create_batch(1, status="new")
#       stats = get_dashboard_stats()
#       assert stats["total"] == 4 and stats["won"] == 3
#       assert stats["conversion_rate"] == 75.0
#
#   def test_dashboard_survives_an_empty_database():
#       assert get_dashboard_stats()["conversion_rate"] == 0.0     # no ZeroDivisionError
#
#   def test_dashboard_is_one_query(django_assert_num_queries):
#       with django_assert_num_queries(1):
#           get_dashboard_stats()
