"""
Módulo de despacho de notificaciones para TesisFar.

Cada función pública construye el conjunto de destinatarios, filtra por preferencias
del usuario, crea las filas de Notification y envía correos electrónicos de forma
sincrónica (con aislamiento de fallos).

Regla clave: el actor (usuario que disparó el evento) nunca recibe su propia notificación.
Un usuario sin fila UserPreference se trata como opted-IN a todo (sin crear fila en DB).
"""

import logging
from types import SimpleNamespace

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification, User

logger = logging.getLogger(__name__)

# Mapping from Project.STATE_CHOICES codes to human-readable labels
_STATE_LABELS = {
    'pending_review_1': 'Pendiente 1ra revisión',
    'pending_review_2': 'Pendiente 2da revisión',
    'pending_defense': 'Pendiente defensa oral',
    'approved': 'Aprobado',
    'failed_final': 'Reprobado (sin más intentos)',
}

_DEFAULT_PREFS = SimpleNamespace(
    notify_evaluation_received=True,
    notify_state_change=True,
    notify_assignment=True,
    notify_comment_added=True,
    notify_semester_changes=True,
    email_enabled=True,
)


def _resolve_prefs(user):
    """
    Retorna las preferencias del usuario o un objeto con todos los valores
    en True si no existe fila UserPreference. No crea nada en la base de datos.
    """
    prefs = getattr(user, 'preferences', None)
    if prefs is None:
        return _DEFAULT_PREFS
    return prefs


def _project_link(project):
    path = 'tesis' if project.project_type == 'tesis' else 'proyectos'
    return f'/dashboard/{path}/{project.pk}'


def _send_notification_email(user, title, body):
    """
    Envía un correo electrónico de notificación al usuario. Atrapa cualquier
    excepción para que un fallo de correo no interrumpa el despacho de notificaciones.
    """
    try:
        send_mail(
            subject=title,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send notification email to %s", user.email)


def dispatch_evaluation_received(evaluation, actor):
    """
    Notifica al estudiante y al compañero de un proyecto cuando se registra
    una evaluación. El actor (jurado) queda excluido de los destinatarios.
    """
    project = evaluation.project
    candidate_ids = {
        u.pk for u in [project.student, project.partner]
        if u is not None and u.pk != actor.pk
    }
    if not candidate_ids:
        return None

    users = User.objects.filter(id__in=candidate_ids).select_related('preferences')
    link = _project_link(project)
    title = "Nueva evaluación recibida"
    payload = {"evaluation_id": evaluation.pk, "project_id": project.pk}

    for user in users:
        prefs = _resolve_prefs(user)
        if not prefs.notify_evaluation_received:
            continue
        body = f"Tu proyecto «{project.title}» fue evaluado."
        Notification.objects.create(
            recipient=user,
            kind='evaluation_received',
            title=title,
            body=body,
            payload=payload,
            link_url=link,
        )
        if prefs.email_enabled:
            _send_notification_email(user, title, body)

    return None


def dispatch_state_change(project, from_state, to_state, actor, kind_source):
    """
    Notifica a los participantes del proyecto cuando cambia el estado.

    kind_source='evaluation': notifica estudiante, compañero y tutores.
    kind_source='override': también incluye al jurado asignado.
    El actor queda excluido en todos los casos.
    """
    candidates = set()
    for u in [project.student, project.partner]:
        if u is not None:
            candidates.add(u.pk)
    for advisor in project.advisors.all():
        candidates.add(advisor.pk)
    if kind_source == 'override' and project.reviewer is not None:
        candidates.add(project.reviewer.pk)

    candidates.discard(actor.pk)

    if not candidates:
        return None

    users = User.objects.filter(id__in=candidates).select_related('preferences')
    link = _project_link(project)
    title = "Estado del proyecto actualizado"
    to_state_label = _STATE_LABELS.get(to_state, to_state)
    payload = {
        "from_state": from_state,
        "to_state": to_state,
        "kind_source": kind_source,
        "project_id": project.pk,
    }

    for user in users:
        prefs = _resolve_prefs(user)
        if not prefs.notify_state_change:
            continue
        body = f"«{project.title}» pasó a {to_state_label}."
        Notification.objects.create(
            recipient=user,
            kind='state_change',
            title=title,
            body=body,
            payload=payload,
            link_url=link,
        )
        if prefs.email_enabled:
            _send_notification_email(user, title, body)

    return None


def dispatch_assignment(project, new_reviewer, previous_reviewer, actor):
    """
    Notifica al jurado entrante (asignación) y al jurado saliente (remoción)
    cuando se cambia el revisor de un proyecto.

    Cualquiera de los dos puede ser None (operaciones parciales son válidas).
    El actor no recibe notificación aunque sea uno de los revisores.
    """
    link = _project_link(project)
    payload = {
        "project_id": project.pk,
        "new_reviewer_id": new_reviewer.pk if new_reviewer else None,
        "previous_reviewer_id": previous_reviewer.pk if previous_reviewer else None,
    }

    if new_reviewer is not None and new_reviewer.pk != actor.pk:
        user = User.objects.filter(pk=new_reviewer.pk).select_related('preferences').first()
        if user:
            prefs = _resolve_prefs(user)
            if prefs.notify_assignment:
                title = "Te asignaron un proyecto"
                body = f"Eres jurado de «{project.title}»."
                Notification.objects.create(
                    recipient=user,
                    kind='assignment',
                    title=title,
                    body=body,
                    payload=payload,
                    link_url=link,
                )
                if prefs.email_enabled:
                    _send_notification_email(user, title, body)

    if previous_reviewer is not None and previous_reviewer.pk != actor.pk:
        user = User.objects.filter(pk=previous_reviewer.pk).select_related('preferences').first()
        if user:
            prefs = _resolve_prefs(user)
            if prefs.notify_assignment:
                title = "Ya no eres jurado de un proyecto"
                body = f"Te quitaron como jurado de «{project.title}»."
                Notification.objects.create(
                    recipient=user,
                    kind='assignment',
                    title=title,
                    body=body,
                    payload=payload,
                    link_url=link,
                )
                if prefs.email_enabled:
                    _send_notification_email(user, title, body)

    return None


def dispatch_comment_added(comment):
    """
    Notifica a todos los participantes del proyecto (estudiante, compañero,
    tutores, jurado) cuando se agrega un comentario. El autor queda excluido.
    """
    project = comment.project
    actor = comment.author

    candidates = set()
    for u in [project.student, project.partner, project.reviewer]:
        if u is not None:
            candidates.add(u.pk)
    for advisor in project.advisors.all():
        candidates.add(advisor.pk)
    candidates.discard(actor.pk)

    if not candidates:
        return None

    users = User.objects.filter(id__in=candidates).select_related('preferences')
    link = _project_link(project)
    title = f"Nuevo comentario en {project.title}"
    body = comment.content[:120]
    payload = {
        "comment_id": comment.pk,
        "project_id": comment.project_id,
        "author_id": comment.author_id,
    }

    for user in users:
        prefs = _resolve_prefs(user)
        if not prefs.notify_comment_added:
            continue
        Notification.objects.create(
            recipient=user,
            kind='comment_added',
            title=title,
            body=body,
            payload=payload,
            link_url=link,
        )
        if prefs.email_enabled:
            _send_notification_email(user, title, body)

    return None


def dispatch_semester_activated(semester, actor):
    """
    Difunde una notificación a todos los usuarios con rol Estudiante cuando
    un semestre es activado. El actor queda excluido (caso degenerado si el
    actor es estudiante).

    Usa bulk_create para eficiencia con grandes cantidades de estudiantes.
    """
    students = (
        User.objects.filter(role='Estudiante')
        .exclude(pk=actor.pk)
        .select_related('preferences')
    )

    title = "Nuevo semestre activo"
    body = f"El semestre {semester.period} es ahora el activo."
    payload = {"semester_id": semester.pk, "period": semester.period}
    link = "/dashboard/settings"

    rows = []
    email_users = []

    for user in students:
        prefs = _resolve_prefs(user)
        if not prefs.notify_semester_changes:
            continue
        rows.append(
            Notification(
                recipient=user,
                kind='semester_activated',
                title=title,
                body=body,
                payload=payload,
                link_url=link,
            )
        )
        if prefs.email_enabled:
            email_users.append(user)

    if rows:
        Notification.objects.bulk_create(rows)

    for user in email_users:
        _send_notification_email(user, title, body)

    return None
