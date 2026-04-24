from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import (
    AttachedFile,
    Comment,
    Evaluation,
    Presentation,
    PresentationDay,
    PresentationJuror,
    Project,
    Semester,
    SessionLog,
    StateOverride,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    cedula_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'nationality', 'cedula', 'cedula_display',
            'role', 'status', 'semester', 'phone', 'date_joined',
        ]

    def get_cedula_display(self, obj):
        if obj.cedula is None:
            return ''
        return f'{obj.nationality or "V"}-{obj.cedula}'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Compute full_name from the property
        data['full_name'] = instance.full_name
        return data

    def to_internal_value(self, data):
        # Accept full_name writes and split into first_name/last_name
        internal = dict(data)
        if 'full_name' in internal:
            full = internal.pop('full_name')
            if full:
                parts = str(full).strip().split(" ", 1)
                internal.setdefault('first_name', parts[0])
                internal.setdefault('last_name', parts[1] if len(parts) > 1 else "")
        return super().to_internal_value(internal)


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'project', 'author', 'author_name', 'content', 'created_at']
        read_only_fields = ['author', 'created_at']

    def get_author_name(self, obj):
        return obj.author.full_name


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(write_only=True, required=False, default="")

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'first_name', 'last_name', 'nationality', 'cedula', 'role', 'semester', 'phone']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'nationality': {'required': False},
            'cedula': {'required': False, 'allow_null': True, 'default': None},
            'semester': {'required': False},
            'phone': {'required': False},
        }

    def create(self, validated_data):
        full_name = validated_data.pop('full_name', '')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')

        # If full_name provided but not first/last, split it
        if full_name and not first_name:
            parts = full_name.strip().split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data.pop('password'),
            first_name=first_name,
            last_name=last_name,
            nationality=validated_data.get('nationality', 'V'),
            cedula=validated_data.get('cedula', None),
            role=validated_data.get('role', 'Estudiante'),
            semester=validated_data.get('semester', ''),
            phone=validated_data.get('phone', ''),
            status='pending',
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


class AttachedFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = AttachedFile
        fields = ['id', 'project', 'name', 'file', 'file_type', 'date', 'url']
        extra_kwargs = {
            'file': {'write_only': True},
            'project': {'read_only': True},
        }

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return ""


class StateOverrideSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.full_name', read_only=True)

    class Meta:
        model = StateOverride
        fields = ['id', 'from_state', 'to_state', 'reason', 'admin_name', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    files = AttachedFileSerializer(many=True, read_only=True, required=False)
    student_name = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()
    advisors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.filter(role='Tutor'), required=False)
    advisor_names = serializers.SerializerMethodField()
    reviewer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='Jurado'),
        required=False,
        allow_null=True,
    )
    reviewer_name = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    diagramacion_score = serializers.SerializerMethodField()
    contenido_score = serializers.SerializerMethodField()
    failed_attempts = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        extra_kwargs = {
            'student': {'read_only': True},
            'submitted_date': {'read_only': True},
            'review_date': {'required': False},
        }

    def validate_period(self, value):
        if value and Semester.objects.exists() and not Semester.objects.filter(period=value).exists():
            raise serializers.ValidationError("Periodo académico no registrado.")
        return value

    def get_student_name(self, obj):
        return obj.student.full_name

    def get_partner_name(self, obj):
        return obj.partner.full_name if obj.partner else None

    def get_advisor_names(self, obj):
        return [user.full_name for user in obj.advisors.all()]

    def get_reviewer_name(self, obj):
        return obj.reviewer.full_name if obj.reviewer else None

    def _latest_eval(self, obj):
        evals = list(obj.evaluations.all())
        if not evals:
            return None
        valid_evals = [e for e in evals if e.graded_at is not None]
        if not valid_evals:
            return None
        return max(valid_evals, key=lambda e: e.graded_at)

    def get_score(self, obj):
        latest = self._latest_eval(obj)
        return latest.score if latest else 0

    def get_diagramacion_score(self, obj):
        latest = self._latest_eval(obj)
        if latest and isinstance(latest.section_scores, dict):
            return latest.section_scores.get('diagramacion', 0)
        return 0

    def get_contenido_score(self, obj):
        latest = self._latest_eval(obj)
        if latest and isinstance(latest.section_scores, dict):
            return latest.section_scores.get('contenido', 0)
        return 0

    def get_failed_attempts(self, obj):
        if obj.project_type != 'proyecto':
            return 0
        return obj.evaluations.filter(kind='review', pass_status='Fail').count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        if user and getattr(user, 'role', None) == 'Administrador':
            data['stateOverrides'] = StateOverrideSerializer(
                instance.state_overrides.all(), many=True
            ).data
        return data


class EvaluationSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Evaluation
        fields = [
            'id', 'project', 'reviewer', 'reviewer_name',
            'kind',
            'ratings', 'comments', 'score', 'pass_status',
            'section_scores', 'graded_at',
        ]
        read_only_fields = ['reviewer', 'reviewer_name', 'graded_at']
        extra_kwargs = {
            'section_scores': {'required': False},
            'ratings': {'required': False},
            'comments': {'required': False},
            'kind': {'required': False, 'default': 'review'},
        }

    def get_reviewer_name(self, obj):
        return obj.reviewer.full_name if obj.reviewer else None


class SemesterSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)

    class Meta:
        model = Semester
        fields = ['id', 'period', 'is_active', 'start_month', 'end_month', 'label', 'created_at']


class SessionLogSerializer(serializers.ModelSerializer):
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = SessionLog
        fields = [
            'id', 'device', 'browser', 'ip_address',
            'created_at', 'last_active_at', 'is_active', 'is_current',
        ]
        read_only_fields = ['id', 'device', 'browser', 'ip_address', 'created_at', 'last_active_at', 'is_active']

    def get_is_current(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.session_key == request.session.session_key if hasattr(request, 'session') else False


class SessionTrackSerializer(serializers.Serializer):
    session_key = serializers.CharField(max_length=40)
    user_agent = serializers.CharField(required=False, allow_blank=True, default='')


class PresentationJurorSerializer(serializers.ModelSerializer):
    juror_name = serializers.CharField(source='juror.full_name', read_only=True)

    class Meta:
        model = PresentationJuror
        fields = (
            'juror', 'juror_name', 'individual_score',
            'notified', 'notified_at', 'confirmed_attendance', 'attended',
        )
        read_only_fields = fields


class PresentationSerializer(serializers.ModelSerializer):
    start_time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])

    # DRF marks M2M fields with through= as read-only; declare it explicitly
    # as writable so that validate_jurado() runs and create/update can manage
    # PresentationJuror rows directly.
    jurado = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role='Jurado'),
        required=False,
    )

    # Read-only flattened fields for the frontend
    student_name = serializers.CharField(
        source='project.student.full_name', read_only=True
    )
    student_email = serializers.CharField(
        source='project.student.email', read_only=True
    )
    project_title = serializers.CharField(
        source='project.title', read_only=True
    )
    project_type = serializers.CharField(
        source='project.project_type', read_only=True
    )
    tutor_name = serializers.SerializerMethodField()
    jurado_names = serializers.SerializerMethodField()
    juror_entries = PresentationJurorSerializer(many=True, read_only=True)

    class Meta:
        model = Presentation
        fields = [
            'id', 'day', 'project', 'tutor', 'jurado',
            'start_time', 'duration_minutes', 'order',
            'student_name', 'student_email', 'project_title', 'project_type',
            'tutor_name', 'jurado_names', 'juror_entries',
        ]
        read_only_fields = ['day']

    def get_tutor_name(self, obj):
        return obj.tutor.full_name if obj.tutor else None

    def get_jurado_names(self, obj):
        return [u.full_name for u in obj.jurado.all()]

    def validate_jurado(self, users):
        """
        Verifica que todos los usuarios en la lista de jurado tengan el rol 'Jurado'.
        El campo limit_choices_to en el modelo no produce un error 400 automáticamente,
        por lo que esta validación explícita es necesaria para rechazar usuarios con
        otros roles y retornar una respuesta de error adecuada.
        """
        for user in users:
            if getattr(user, 'role', None) != 'Jurado':
                raise serializers.ValidationError(
                    f"El usuario '{user.email}' no tiene el rol Jurado."
                )
        return users

    def create(self, validated_data):
        """
        Crea la presentación y luego crea las filas PresentationJuror para cada
        jurado. Con through= activo Django prohíbe .jurado.set() / .add(), por lo
        que se deben insertar las filas del modelo puente explícitamente.
        """
        jurors = validated_data.pop('jurado', [])
        presentation = Presentation.objects.create(**validated_data)
        for user in jurors:
            PresentationJuror.objects.create(presentation=presentation, juror=user)
        return presentation

    def update(self, instance, validated_data):
        """
        Actualiza los campos escalares de la presentación. Si se envía 'jurado',
        sincroniza las filas PresentationJuror: elimina las que ya no están en la
        lista y agrega las nuevas, preservando los campos extra (individual_score,
        notified, etc.) de las filas que persisten.
        """
        jurors = validated_data.pop('jurado', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if jurors is not None:
            current = {pj.juror_id: pj for pj in instance.juror_entries.all()}
            wanted_ids = {u.id for u in jurors}
            for pj in list(current.values()):
                if pj.juror_id not in wanted_ids:
                    pj.delete()
            for u in jurors:
                if u.id not in current:
                    PresentationJuror.objects.create(presentation=instance, juror=u)
        return instance


class PresentationDaySerializer(serializers.ModelSerializer):
    presentations = PresentationSerializer(many=True, read_only=True)

    class Meta:
        model = PresentationDay
        fields = [
            'id', 'date', 'semester', 'notes', 'created_at', 'created_by',
            'presentations',
        ]
        read_only_fields = ['created_at', 'created_by']
