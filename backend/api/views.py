from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import login, logout
from django.db.models import Q
from .models import User, Project, Evaluation, Semester, AttachedFile, Comment
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    ProjectSerializer, AttachedFileSerializer, EvaluationSerializer, SemesterSerializer, CommentSerializer
)
from django.middleware.csrf import get_token
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "role", None) == "Administrador")

class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        login(request, user)
        return Response(UserSerializer(user).data)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user

        if request.method.lower() == 'patch':
            if user.role == 'Estudiante':
                allowed_fields = {'full_name', 'first_name', 'last_name', 'phone', 'cedula'}
            else:
                allowed_fields = {'full_name', 'first_name', 'last_name', 'phone', 'cedula', 'semester'}
            clean_data = {
                key: value
                for key, value in request.data.items()
                if key in allowed_fields
            }

            serializer = UserSerializer(
                user,
                data=clean_data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response(UserSerializer(user).data)

class CsrfTokenView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({"csrfToken": token})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminUserRole()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user

        if getattr(user, "role", None) == "Administrador":
            return User.objects.all()

        if getattr(user, "role", None) == "Estudiante":
            if self.request.query_params.get('role') == 'Estudiante':
                 return User.objects.filter(role="Estudiante")
            return User.objects.filter(role="Tutor")

        return User.objects.filter(id=user.id)


_project_qs_opts = {
    'select': ('student', 'partner'),
    'prefetch': ('advisors', 'evaluations', 'files'),
}

def _optimized_projects(qs):
    return qs.select_related(*_project_qs_opts['select']).prefetch_related(*_project_qs_opts['prefetch'])


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'Administrador':
            return _optimized_projects(Project.objects.all())

        if user.role == 'Tutor':
            return _optimized_projects(Project.objects.filter(advisors=user).distinct())

        if user.role == 'Jurado':
            # Jurados see all projects for evaluation purposes
            return _optimized_projects(Project.objects.all())

        # Student sees own projects + projects where they are a partner
        return _optimized_projects(
            Project.objects.filter(Q(student=user) | Q(partner=user)).distinct()
        )

    def perform_create(self, serializer):
        user = self.request.user
        target_student = user
        if getattr(user, 'role', None) == 'Administrador':
            data = self.request.data
            student_id = data.get('student')
            student_email = data.get('student_email')
            if student_id:
                try:
                    target_student = User.objects.get(id=student_id)
                except User.DoesNotExist:
                    raise ValidationError({'student': 'User not found'})
            elif student_email:
                try:
                    target_student = User.objects.get(email=student_email)
                except User.DoesNotExist:
                    raise ValidationError({'student_email': 'User not found'})

        period = self.request.data.get('period')
        if not period:
            active_semester = Semester.objects.filter(is_active=True).first()
            if active_semester:
                period = active_semester.period

        serializer.save(student=target_student, period=period)

    @action(detail=True, methods=['post'], url_path='reassign_student')
    def reassign_student(self, request, pk=None):
        user = request.user
        if getattr(user, 'role', None) != 'Administrador':
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        project = self.get_object()
        student_id = request.data.get('student')
        student_email = request.data.get('student_email')

        target_student = None
        if student_id:
            try:
                target_student = User.objects.get(id=student_id)
            except User.DoesNotExist:
                raise ValidationError({'student': 'User not found'})
        elif student_email:
            try:
                target_student = User.objects.get(email=student_email)
            except User.DoesNotExist:
                raise ValidationError({'student_email': 'User not found'})

        if not target_student:
            raise ValidationError({'detail': 'Provide student id or student_email'})

        project.student = target_student
        project.save()
        return Response(ProjectSerializer(project).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='files', parser_classes=[MultiPartParser, FormParser])
    def upload_file(self, request, pk=None):
        project = self.get_object()
        user = request.user

        if getattr(user, 'role', None) == 'Estudiante' and project.student != user:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        uploaded = request.FILES.get('file')
        if not uploaded:
            raise ValidationError({'file': 'This field is required.'})

        filename = uploaded.name
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if ext not in ['pdf', 'doc', 'docx']:
            raise ValidationError({'file': 'Only PDF or Word files are allowed.'})

        file_type = 'pdf' if ext == 'pdf' else 'word'
        attached = AttachedFile.objects.create(
            project=project,
            name=filename,
            file=uploaded,
            file_type=file_type,
        )

        serializer = AttachedFileSerializer(attached, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IsReviewerRole(BasePermission):
    """Only Administrador, Tutor, and Jurado can create evaluations."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, "role", None) in ["Administrador", "Tutor", "Jurado"]
        )


class EvaluationViewSet(viewsets.ModelViewSet):
    queryset = Evaluation.objects.select_related('project', 'reviewer').all()
    serializer_class = EvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsReviewerRole()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Evaluation.objects.select_related('project', 'reviewer').all()
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        if getattr(user, 'role', None) in ['Administrador', 'Tutor', 'Jurado']:
            return qs
        return qs.filter(project__student=user)

    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        if not project_id:
            raise ValidationError({'project': 'This field is required.'})
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise ValidationError({'project': 'Project not found'})

        if project.project_type == 'proyecto' and project.failed_attempts >= 2:
            raise ValidationError({'detail': 'El proyecto ya agotó los 2 intentos permitidos.'})

        serializer.save(reviewer=self.request.user, project=project)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)


class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminUserRole()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def current(self, request):
        current_semester = Semester.objects.filter(is_active=True).first()
        if not current_semester:
            return Response({"detail": "No active semester set."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(current_semester)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAdminUserRole])
    def set_active(self, request, pk=None):
        semester = self.get_object()
        Semester.objects.exclude(pk=semester.pk).update(is_active=False)
        semester.is_active = True
        semester.save()
        return Response(self.get_serializer(semester).data)

    def perform_create(self, serializer):
        is_active = self.request.data.get('is_active', False)
        if is_active:
            Semester.objects.all().update(is_active=False)
        serializer.save()


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author').all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        if project_id:
            return Comment.objects.select_related('author').filter(project_id=project_id)
        # Require project param — don't expose all comments
        return Comment.objects.none()

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if self.action in ['update', 'partial_update', 'destroy']:
            if obj.author != request.user and getattr(request.user, 'role', None) != 'Administrador':
                self.permission_denied(
                    request,
                    message='Solo el autor o un administrador puede modificar este comentario.',
                )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
