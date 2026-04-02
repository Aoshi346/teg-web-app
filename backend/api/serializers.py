from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import Project, AttachedFile, Evaluation, Semester, Comment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='*', read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'cedula', 'role', 'status', 'semester', 'phone', 'date_joined',
        ]

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
        fields = ['email', 'password', 'full_name', 'first_name', 'last_name', 'cedula', 'role', 'semester', 'phone']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'cedula': {'required': False},
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
            cedula=validated_data.get('cedula', ''),
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


class ProjectSerializer(serializers.ModelSerializer):
    files = AttachedFileSerializer(many=True, read_only=True, required=False)
    student_name = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()
    advisors = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.filter(role='Tutor'), required=False)
    advisor_names = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    diagramacion_score = serializers.SerializerMethodField()
    contenido_score = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        extra_kwargs = {
            'student': {'read_only': True},
            'submitted_date': {'read_only': True},
            'review_date': {'required': False},
        }

    def validate_period(self, value):
        if Semester.objects.exists() and not Semester.objects.filter(period=value).exists():
            raise serializers.ValidationError("Periodo académico no registrado.")
        return value

    def get_student_name(self, obj):
        return obj.student.full_name

    def get_partner_name(self, obj):
        return obj.partner.full_name if obj.partner else None

    def get_advisor_names(self, obj):
        return [user.full_name for user in obj.advisors.all()]

    def _latest_eval(self, obj):
        evals = list(obj.evaluations.all())
        return max(evals, key=lambda e: e.graded_at) if evals else None

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


class EvaluationSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Evaluation
        fields = [
            'id', 'project', 'reviewer', 'reviewer_name',
            'ratings', 'comments', 'score', 'pass_status',
            'section_scores', 'graded_at',
        ]
        read_only_fields = ['reviewer', 'reviewer_name', 'graded_at']
        extra_kwargs = {
            'section_scores': {'required': False},
            'ratings': {'required': False},
            'comments': {'required': False},
        }

    def get_reviewer_name(self, obj):
        return obj.reviewer.full_name if obj.reviewer else None


class SemesterSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)

    class Meta:
        model = Semester
        fields = ['id', 'period', 'is_active', 'start_month', 'end_month', 'label', 'created_at']
