from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User que usa email como identificador
    en lugar de username. La implementación por defecto de BaseUserManager pasa
    username=... al constructor del modelo, lo cual falla en Django 6 contra un
    User que elimina ese campo. Esta clase evita ese problema aceptando email
    como primer argumento y delegando el resto a set_password + save.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users require an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ('Administrador', 'Administrador'),
        ('Estudiante', 'Estudiante'),
        ('Jurado', 'Jurado'),
        ('Tutor', 'Tutor'),
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('pending', 'Pending'),
    )
    NATIONALITY_CHOICES = (
        ('V', 'Venezolano'),
        ('E', 'Extranjero'),
        ('P', 'Pasaporte'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    nationality = models.CharField(
        max_length=1, choices=NATIONALITY_CHOICES, default='V', blank=True
    )
    cedula = models.PositiveIntegerField(
        null=True, blank=True, help_text="Numeric-only cédula/ID number"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Estudiante')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    semester = models.CharField(max_length=10, blank=True, default='', help_text="e.g. 9no, 10mo, N/A")
    phone = models.CharField(max_length=20, blank=True, default='', help_text="e.g. +58-414-1234567")

    username = None
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['nationality', 'cedula'],
                condition=models.Q(cedula__isnull=False),
                name='unique_nationality_cedula',
            ),
        ]

    @property
    def full_name(self):
        """Computed from first_name + last_name for backwards compatibility."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p).strip() or self.email.split("@")[0]

    @full_name.setter
    def full_name(self, value):
        """Accept a full_name string and split into first/last for backwards compatibility."""
        if not value:
            return
        parts = value.strip().split(" ", 1)
        self.first_name = parts[0]
        self.last_name = parts[1] if len(parts) > 1 else ""

    def __str__(self):
        return self.email


class Project(models.Model):
    TYPE_CHOICES = (
        ('proyecto', 'Proyecto (PTEG)'),
        ('tesis', 'Tesis (TEG)'),
    )
    STATUS_CHOICES = (
        ('checked', 'Aprobado'),
        ('pending', 'Pendiente'),
        ('rejected', 'Rechazado'),
    )
    STATE_CHOICES = (
        ('pending_review_1', 'Pendiente 1ra revisión'),
        ('pending_review_2', 'Pendiente 2da revisión'),
        ('pending_defense', 'Pendiente defensa oral'),
        ('approved', 'Aprobado'),
        ('failed_final', 'Reprobado (sin más intentos)'),
    )

    title = models.CharField(max_length=255)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    partner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='partner_projects', null=True, blank=True)
    advisors = models.ManyToManyField(User, related_name='advised_projects', limit_choices_to={'role': 'Tutor'}, blank=True)

    submitted_date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    review_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stage1_passed = models.BooleanField(default=False, help_text="For Tesis only")
    period = models.CharField(max_length=20, blank=True)
    project_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='proyecto')

    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='pending_review_1',
        db_index=True,
        help_text="Estado del ciclo de vida del proyecto. Autogestionado por Evaluation.",
    )

    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_projects',
        null=True,
        blank=True,
        limit_choices_to={'role': 'Jurado'},
        help_text="Jurado asignado para evaluar este proyecto",
    )

    def __str__(self):
        return f"{self.title} ({self.student.email})"


class AttachedFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='project_files/', blank=True, null=True)
    file_type = models.CharField(max_length=10, choices=(('pdf', 'PDF'), ('word', 'Word')))
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


class Evaluation(models.Model):
    PASS_STATUS = (
        ('Pass', 'Pass'),
        ('Fail', 'Fail'),
    )
    KIND_CHOICES = (
        ('review', 'Revisión'),
        ('defense', 'Defensa oral'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='evaluations')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    kind = models.CharField(
        max_length=10,
        choices=KIND_CHOICES,
        default='review',
        db_index=True,
    )
    ratings = models.JSONField(default=dict, blank=True)
    comments = models.JSONField(default=dict, blank=True)
    score = models.FloatField(default=0)
    pass_status = models.CharField(max_length=10, choices=PASS_STATUS)
    section_scores = models.JSONField(default=dict, blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Evaluation for {self.project.title} ({self.pass_status})"


class Semester(models.Model):
    MONTH_CHOICES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
        (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
        (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
        (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    period = models.CharField(max_length=7, unique=True, help_text="Format: YYYY-01 or YYYY-02")
    is_active = models.BooleanField(default=False)
    start_month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES, default=1)
    end_month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES, default=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period"]

    @property
    def label(self):
        month_map = dict(self.MONTH_CHOICES)
        year = int(self.period[:4])
        start = f"{month_map.get(self.start_month, '?')} {year}"
        end_year = year + 1 if self.end_month < self.start_month else year
        end = f"{month_map.get(self.end_month, '?')} {end_year}"
        return f"{start} – {end}"

    def __str__(self):
        return self.period


class Comment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.project.title}"


class PresentationDay(models.Model):
    """A planned day of presentations (admin-managed)."""

    date = models.DateField(unique=True)
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name='presentation_days'
    )
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True,
        related_name='created_presentation_days'
    )

    class Meta:
        ordering = ['date']

    def __str__(self):
        return str(self.date)


class Presentation(models.Model):
    """A single thesis/project presentation slot inside a day."""

    day = models.ForeignKey(
        PresentationDay, on_delete=models.CASCADE, related_name='presentations'
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='presentations'
    )
    tutor = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tutored_presentations',
        limit_choices_to={'role': 'Tutor'}
    )
    jurado = models.ManyToManyField(
        'User',
        through='PresentationJuror',
        related_name='juried_presentations',
        limit_choices_to={'role': 'Jurado'},
        blank=True,
    )
    start_time = models.TimeField(help_text="Hora de inicio HH:MM")
    duration_minutes = models.PositiveSmallIntegerField(
        default=30, help_text="Duración estimada en minutos"
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['day__date', 'start_time', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=['day', 'project'], name='unique_project_per_day'
            ),
        ]

    def __str__(self):
        return f"{self.project.title} @ {self.day.date} {self.start_time}"


class PresentationJuror(models.Model):
    """
    Modelo puente explícito para la relación M2M entre Presentation y User
    (rol Jurado). Reemplaza la tabla implícita auto-generada por Django para
    permitir registrar datos por jurado: puntaje individual, notificación de
    asistencia y confirmación/presencia el día de la presentación.
    """

    presentation = models.ForeignKey(
        Presentation, on_delete=models.CASCADE, related_name='juror_entries'
    )
    juror = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Jurado'},
        related_name='juror_entries',
        db_column='user_id',
    )
    individual_score = models.FloatField(null=True, blank=True)
    notified = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)
    confirmed_attendance = models.BooleanField(default=False)
    attended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_presentation_jurado'
        unique_together = ('presentation', 'juror')
        ordering = ['presentation', 'id']

    def __str__(self):
        return f"{self.juror.email} → {self.presentation_id}"


def _get_device_from_user_agent(user_agent: str) -> str:
    """Extract device from user agent string."""
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua and 'mobile' in ua:
        return 'Mobile Device'
    if 'iphone' in ua or 'ipad' in ua:
        return 'iOS Device'
    if 'android' in ua:
        return 'Android Device'
    if 'windows' in ua:
        return 'Windows'
    if 'macintosh' in ua or 'mac os' in ua:
        return 'macOS'
    if 'linux' in ua:
        return 'Linux'
    return 'Unknown Device'


def _get_browser_from_user_agent(user_agent: str) -> str:
    """Extract browser from user agent string."""
    ua = user_agent.lower()
    if 'chrome' in ua and 'edg' not in ua:
        return 'Chrome'
    if 'firefox' in ua:
        return 'Firefox'
    if 'safari' in ua and 'chrome' not in ua:
        return 'Safari'
    if 'edg' in ua:
        return 'Edge'
    if 'opera' in ua or 'opr' in ua:
        return 'Opera'
    return 'Unknown Browser'


class SessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_logs')
    session_key = models.CharField(max_length=40, unique=True)
    device = models.CharField(max_length=100, blank=True, default='')
    browser = models.CharField(max_length=100, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-last_active_at']
        verbose_name = 'Session Log'
        verbose_name_plural = 'Session Logs'

    def save(self, *args, **kwargs):
        if self.user_agent:
            if not self.device:
                self.device = _get_device_from_user_agent(self.user_agent)
            if not self.browser:
                self.browser = _get_browser_from_user_agent(self.user_agent)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session for {self.user.email} ({self.device}/{self.browser})"


class StateOverride(models.Model):
    """Admin-only manual override of Project.state. Bypasses lifecycle.next_state().

    Append-only audit log. No edit/delete endpoint. admin is PROTECTed so
    audit rows never become orphans; project is CASCADE since overrides are
    scoped to project lifetime.
    """

    STATE_CHOICES = Project.STATE_CHOICES

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='state_overrides',
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='performed_state_overrides',
    )
    from_state = models.CharField(max_length=20, choices=STATE_CHOICES)
    to_state = models.CharField(max_length=20, choices=STATE_CHOICES)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project_id}: {self.from_state} → {self.to_state} by {self.admin_id}"

    def clean(self):
        if self.from_state == self.to_state:
            raise ValidationError("from_state y to_state no pueden ser iguales.")
