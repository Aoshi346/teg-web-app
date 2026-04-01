from django.db import models
from django.contrib.auth.models import AbstractUser


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

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    cedula = models.CharField(max_length=20, blank=True, help_text="Student/staff ID number")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Estudiante')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    semester = models.CharField(max_length=10, blank=True, default='', help_text="e.g. 9no, 10mo, N/A")
    phone = models.CharField(max_length=20, blank=True, default='', help_text="e.g. +58-414-1234567")

    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

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

    failed_attempts = models.IntegerField(default=0)

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

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='evaluations')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
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
