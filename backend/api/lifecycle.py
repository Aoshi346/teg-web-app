"""
Máquina de estados del ciclo de vida de proyectos PTEG.

Proporciona funciones puras (sin acceso a DB) que el ViewSet de Evaluación
usa para calcular el estado destino al registrar una evaluación. Mantenerlo
puro permite testearlo exhaustivamente y reutilizarlo en migraciones de datos
si fuera necesario sin arrastrar dependencias del ORM.
"""

TERMINAL_STATES = {'approved', 'failed_final'}


class InvalidTransition(Exception):
    """Raised when an evaluation would produce an illegal state transition."""


def next_state(project, evaluation_kind: str, pass_status: str) -> str:
    """
    Regla de negocio: calcula el estado destino de un proyecto PTEG tras
    registrar una Evaluation. Pura — no toca la DB. El caller persiste el
    resultado junto con la Evaluation de forma atómica.
    """
    current = project.state

    if current in TERMINAL_STATES:
        raise InvalidTransition(
            f"Project is {current}; no further evaluations allowed."
        )

    if pass_status not in ('Pass', 'Fail'):
        raise InvalidTransition(f"Unknown pass_status: {pass_status!r}")

    if evaluation_kind == 'review':
        if current == 'pending_review_1':
            return 'pending_defense' if pass_status == 'Pass' else 'pending_review_2'
        if current == 'pending_review_2':
            return 'pending_defense' if pass_status == 'Pass' else 'failed_final'
        raise InvalidTransition(
            f"Cannot record review on project in state {current}."
        )

    if evaluation_kind == 'defense':
        if current == 'pending_defense':
            return 'approved' if pass_status == 'Pass' else 'pending_defense'
        raise InvalidTransition(
            f"Cannot record defense on project in state {current}."
        )

    raise InvalidTransition(f"Unknown evaluation kind: {evaluation_kind}")


def status_projection(state: str) -> str:
    """Maps a lifecycle state to the legacy Project.status value for backwards compatibility."""
    if state == 'approved':
        return 'checked'
    if state == 'failed_final':
        return 'rejected'
    return 'pending'
