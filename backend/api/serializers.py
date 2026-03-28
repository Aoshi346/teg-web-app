from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import Project, AttachedFile, Evaluation, Semester, Comment

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'status', 'semester', 'phone']



class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.full_name')

    class Meta:
        model = Comment
        fields = ['id', 'project', 'author', 'author_name', 'content', 'created_at']
        read_only_fields = ['author', 'created_at']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'role', 'semester', 'phone']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            role=validated_data.get('role', 'Estudiante'),
            semester=validated_data.get('semester', ''),
            phone=validated_data.get('phone', ''),
            status='pending' # Default status
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
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    partner_name = serializers.ReadOnlyField(source='partner.full_name')
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
        # Only enforce if semesters are registered
        if Semester.objects.exists() and not Semester.objects.filter(period=value).exists():
            raise serializers.ValidationError("Periodo académico no registrado.")
        return value

    def get_advisor_names(self, obj):
        return [user.full_name for user in obj.advisors.all()]

    def get_score(self, obj):
        latest = obj.evaluations.order_by('-graded_at').first()
        return latest.score if latest else 0

    def get_diagramacion_score(self, obj):
        latest = obj.evaluations.order_by('-graded_at').first()
        if latest and isinstance(latest.section_scores, dict):
            return latest.section_scores.get('diagramacion', 0)
        return 0

    def get_contenido_score(self, obj):
        latest = obj.evaluations.order_by('-graded_at').first()
        if latest and isinstance(latest.section_scores, dict):
            return latest.section_scores.get('contenido', 0)
        return 0


class EvaluationSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)

    class Meta:
        model = Evaluation
        fields = [
            'id',
            'project',
            'reviewer',
            'reviewer_name',
            'ratings',
            'comments',
            'score',
            'pass_status',
            'section_scores',
            'graded_at',
        ]
        read_only_fields = ['reviewer', 'reviewer_name', 'graded_at']
        extra_kwargs = {
            'section_scores': {'required': False},
            'ratings': {'required': False},
            'comments': {'required': False},
        }


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ['id', 'period', 'created_at']
