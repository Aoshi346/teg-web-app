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
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Estudiante')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    full_name = models.CharField(max_length=255, blank=True)
    semester = models.IntegerField(blank=True, null=True)
    phone = models.IntegerField(blank=True, null=True)

    first_name = None
    last_name = None
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

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
    period = models.CharField(max_length=20, blank=True)  # Academic period e.g. "2026-01"
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
    period = models.CharField(max_length=7, unique=True)  # Format: YYYY-SS
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period"]

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

