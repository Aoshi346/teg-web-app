# DRF Serializer Best Practices

> **Path B only.** Serializers exist to build a JSON API. If Django renders your pages, the
> equivalent layer is the project's shared `ModelForm` base — see "Path A" in `SKILL.md` and its
> canon, `.claude/patterns/stack/backend-formularios-django.md`. Both archetypes are first-class;
> do not add `djangorestframework` to a server-rendered project just to reuse these patterns.
>
> Models here inherit `AuditableModel` and use the example domain (Agency ─ Lead ─ Appointment ─
> Property), both defined in `model-patterns.md`.

## Basic Serializer Structure

```python
from rest_framework import serializers
from .models import Lead

class LeadSerializer(serializers.ModelSerializer):
    """Lead serializer with validation."""

    class Meta:
        model = Lead
        fields = ['id', 'name', 'phone', 'email', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
```

## Field Validation

### Single Field Validation

```python
class LeadSerializer(serializers.ModelSerializer):
    def validate_phone(self, value):
        """Validate phone format."""
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone must start with +")

        # Uniqueness check that survives an UPDATE. Without exclude(pk=...), editing a
        # lead without changing its phone reports "already exists" against itself, and
        # every PATCH fails — the classic version of this validator is broken on update.
        duplicates = Lead.objects.filter(phone=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("Phone already exists")

        return value

    def validate_email(self, value):
        """Validate email format."""
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value
```

### Cross-Field Validation

```python
class LeadSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        """Cross-field validation."""
        # Qualified leads must have email
        if attrs.get('status') == 'qualified' and not attrs.get('email'):
            raise serializers.ValidationError(
                "Email required for qualified leads"
            )

        # Won leads must have notes
        if attrs.get('status') == 'won' and not attrs.get('notes'):
            raise serializers.ValidationError(
                "Notes required for won leads"
            )

        return attrs
```

## Nested Serializers

```python
class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ['id', 'name']

class LeadDetailSerializer(serializers.ModelSerializer):
    """Lead serializer with nested agency."""
    agency = AgencySerializer(read_only=True)
    agency_id = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(),
        write_only=True,
        source='agency'
    )

    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'phone', 'email', 'status',
            'agency', 'agency_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
```

## Read-Only and Write-Only Fields

```python
class LeadSerializer(serializers.ModelSerializer):
    # Computed field (read-only)
    display_name = serializers.SerializerMethodField()

    # Write-only: accepted on input, never echoed back
    import_token = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Lead
        fields = ['id', 'name', 'phone', 'display_name', 'import_token', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_display_name(self, obj):
        """Only fields that exist on the model — see model-patterns.md."""
        return f"{obj.name} ({obj.phone})"
```

## Custom Fields

```python
class LeadSerializer(serializers.ModelSerializer):
    # Override field with custom behavior
    phone = serializers.CharField(
        max_length=20,
        required=True,
        help_text="International format required (+34...)"
    )

    # Choice field with custom options (TextChoices — see model-patterns.md)
    status = serializers.ChoiceField(
        choices=Lead.Status.choices,
        default=Lead.Status.NEW
    )

    class Meta:
        model = Lead
        fields = ['id', 'phone', 'status']
```

## Method Fields

```python
class LeadSerializer(serializers.ModelSerializer):
    # Computed fields
    is_qualified = serializers.SerializerMethodField()
    appointments_count = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = ['id', 'name', 'is_qualified', 'appointments_count']

    def get_is_qualified(self, obj):
        """Check if lead is qualified."""
        return obj.status == Lead.Status.QUALIFIED

    def get_appointments_count(self, obj):
        """Count appointments for this lead.

        ⚠️ This is an N+1 generator: one COUNT query per row in the list. Annotate it in
        the view's queryset instead and read the annotation here:

            # views.py
            Lead.alive.annotate(appointments_count=Count("appointments"))

            # serializer
            appointments_count = serializers.IntegerField(read_only=True)

        A SerializerMethodField that touches the database is the single most common cause
        of a list endpoint that is fast with 10 rows and unusable with 500.
        """
        return obj.appointments.count()
```

## Multiple Serializers for Same Model

```python
# List serializer (minimal fields)
class LeadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['id', 'name', 'phone', 'status']

# Detail serializer (all fields)
class LeadDetailSerializer(serializers.ModelSerializer):
    agency = AgencySerializer(read_only=True)
    appointments = AppointmentSerializer(many=True, read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'phone', 'email', 'status', 'notes',
            'agency', 'appointments',
            'created_at', 'updated_at'
        ]

# Create/Update serializer (write fields)
class LeadWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['name', 'phone', 'email', 'status', 'notes', 'agency_id']

# Use in ViewSet
class LeadViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Never `queryset = Lead.objects.all()`: that returns every tenant's rows and
        # every soft-deleted one, for read AND write. See SKILL.md, Path B.
        return Lead.alive.filter(agency=self.request.user.agency)

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        elif self.action == 'retrieve':
            return LeadDetailSerializer
        else:  # create, update, partial_update
            return LeadWriteSerializer
```

## Validation with Context

```python
class LeadSerializer(serializers.ModelSerializer):
    def validate_phone(self, value):
        """Validate phone with context."""
        request = self.context.get('request')

        # Check if updating existing lead
        if self.instance:
            # Skip validation if phone unchanged
            if self.instance.phone == value:
                return value

        # Check for duplicates in same agency
        agency = self.context.get('agency')
        if Lead.objects.filter(phone=value, agency=agency).exists():
            raise serializers.ValidationError(
                "Phone already exists in this agency"
            )

        return value

# In ViewSet
class LeadViewSet(viewsets.ModelViewSet):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['agency'] = self.request.user.agency
        return context
```

## Best Practices

1. **Use ModelSerializer** when possible (DRY principle)
2. **Separate read/write serializers** for complex models
3. **Add field-level validation** with `validate_<field_name>`
4. **Add cross-field validation** with `validate()`
5. **Use read_only_fields** for computed/auto-generated fields
6. **Use write_only** for sensitive fields (passwords)
7. **Add help_text** for API documentation
8. **Use SerializerMethodField** for computed fields
9. **Optimize nested serializers** (avoid N+1 queries)
10. **Pass context** when needed (request, user, etc.)
