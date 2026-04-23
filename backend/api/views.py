from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import login, logout
from django.db.models import Q
from django.db import IntegrityError
from .models import User, Project, Evaluation, Semester, AttachedFile, Comment, SessionLog, PresentationDay, Presentation
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    ProjectSerializer, AttachedFileSerializer, EvaluationSerializer, SemesterSerializer, CommentSerializer,
    SessionLogSerializer, SessionTrackSerializer,
    PresentationDaySerializer, PresentationSerializer,
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
        # Track the session
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        SessionLog.objects.update_or_create(
            session_key=request.session.session_key,
            user=user,
            defaults={
                'is_active': True,
                'user_agent': user_agent,
                'ip_address': self._get_client_ip(request),
            }
        )
        return Response(UserSerializer(user).data)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

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

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', None)
        return ip

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
    """Only Administrador and Jurado can create evaluations."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, "role", None) in ["Administrador", "Jurado"]
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

        role = getattr(user, 'role', None)
        if role in ['Administrador', 'Jurado']:
            return qs
        if role == 'Tutor':
            return qs.filter(project__advisors=user).distinct()
        return qs.filter(Q(project__student=user) | Q(project__partner=user)).distinct()

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


class IsCommentAuthorOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update', 'destroy']:
            return obj.author == request.user or getattr(request.user, 'role', None) == 'Administrador'
        return True

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author').all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthorOrAdmin]

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        if project_id:
            return Comment.objects.select_related('author').filter(project_id=project_id)
        # Require project param — don't expose all comments
        return Comment.objects.none()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SessionViewSet(viewsets.GenericViewSet):
    serializer_class = SessionLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SessionLog.objects.filter(user=self.request.user, is_active=True)

    def list(self, request):
        sessions = self.get_queryset()
        serializer = SessionLogSerializer(sessions, many=True, context={'request': request})
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        try:
            session = SessionLog.objects.get(pk=pk, user=request.user)
        except SessionLog.DoesNotExist:
            return Response({'detail': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        session.is_active = False
        session.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def track(self, request):
        serializer = SessionTrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_key = serializer.validated_data['session_key']
        user_agent = serializer.validated_data.get('user_agent', '')

        session, created = SessionLog.objects.update_or_create(
            session_key=session_key,
            user=request.user,
            defaults={
                'is_active': True,
                'user_agent': user_agent,
                'ip_address': self._get_client_ip(request),
            }
        )
        return Response(SessionLogSerializer(session, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', None)
        return ip


class PresentationDayViewSet(viewsets.ModelViewSet):
    serializer_class = PresentationDaySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "bulk", "add_presentation"]:
            return [permissions.IsAuthenticated(), IsAdminUserRole()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = PresentationDay.objects.all().prefetch_related(
            'presentations__jurado',
            'presentations__project__student',
        )
        params = self.request.query_params
        from_date = params.get('from')
        to_date = params.get('to')
        semester_id = params.get('semester')
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(
        detail=False, methods=['post'], url_path='bulk',
        permission_classes=[permissions.IsAuthenticated, IsAdminUserRole]
    )
    def bulk(self, request):
        """
        Crea o recupera días de presentación a partir de una lista de fechas.
        La operación es idempotente: si un día ya existe para esa fecha,
        simplemente se retorna sin duplicarlo. Esto permite que el admin
        reenvíe el mismo rango sin errores.
        """
        dates = request.data.get('dates', [])
        semester_id = request.data.get('semester')
        notes = request.data.get('notes', '')

        if not dates or not semester_id:
            return Response(
                {'detail': 'dates and semester are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            semester = Semester.objects.get(pk=semester_id)
        except Semester.DoesNotExist:
            return Response({'detail': 'Semester not found.'}, status=status.HTTP_400_BAD_REQUEST)

        days = []
        for date_str in dates:
            day, _ = PresentationDay.objects.get_or_create(
                date=date_str,
                defaults={
                    'semester': semester,
                    'notes': notes,
                    'created_by': request.user,
                },
            )
            days.append(day)

        serializer = PresentationDaySerializer(days, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True, methods=['post'], url_path='presentations',
        permission_classes=[permissions.IsAuthenticated, IsAdminUserRole]
    )
    def add_presentation(self, request, pk=None):
        """
        Agrega una presentación a un día de presentaciones específico.
        El día se obtiene del URL (pk), no del payload.
        Captura la violación de unicidad (mismo proyecto en el mismo día)
        y la convierte en un error 400 legible.
        """
        day = self.get_object()
        serializer = PresentationSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        project = serializer.validated_data.get('project')
        if Presentation.objects.filter(day=day, project=project).exists():
            return Response(
                {'detail': 'Este proyecto ya está programado para este día.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            presentation = serializer.save(day=day)
        except IntegrityError:
            return Response(
                {'detail': 'Este proyecto ya está programado para este día.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PresentationSerializer(presentation).data,
            status=status.HTTP_201_CREATED,
        )


class PresentationViewSet(viewsets.ModelViewSet):
    queryset = Presentation.objects.all()
    serializer_class = PresentationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminUserRole()]
        return [permissions.IsAuthenticated()]
