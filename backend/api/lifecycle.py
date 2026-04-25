# backend/api/lifecycle.py — full file replacement
"""
Máquina de estados del ciclo de vida de proyectos.

Funciones puras (sin acceso a DB) que el ViewSet de Evaluación usa para
calcular el estado destino al registrar una Evaluation. PTEG y TEG tienen
tablas de transición separadas; el dispatch lo hace `next_state` según
`project.project_type`.
"""

TERMINAL_STATES = {'approved', 'failed_final'}


class InvalidTransition(Exception):
    """Raised when an evaluation would produce an illegal state transition."""


# (current_state, kind, pass_status) -> new_state
PTEG_TRANSITIONS = {
    ('pending_review_1', 'review',  'Pass'): 'pending_defense',
    ('pending_review_1', 'review',  'Fail'): 'pending_review_2',
    ('pending_review_2', 'review',  'Pass'): 'pending_defense',
    ('pending_review_2', 'review',  'Fail'): 'failed_final',
    ('pending_defense',  'defense', 'Pass'): 'approved',
    # Defense Fail keeps the project at pending_defense (existing behaviour;
    # admin uses override_state to mark failed_final if needed).
    ('pending_defense',  'defense', 'Fail'): 'pending_defense',
}

TEG_TRANSITIONS = {
    ('pending_articulo', 'review',  'Pass'): 'pending_entrega',
    ('pending_articulo', 'review',  'Fail'): 'failed_final',
    ('pending_entrega',  'review',  'Pass'): 'pending_defensa',
    ('pending_entrega',  'review',  'Fail'): 'failed_final',
    ('pending_defensa',  'defense', 'Pass'): 'approved',
    ('pending_defensa',  'defense', 'Fail'): 'failed_final',
}


def _table_for(project_type: str):
    if project_type == 'proyecto':
        return PTEG_TRANSITIONS
    if project_type == 'tesis':
        return TEG_TRANSITIONS
    raise InvalidTransition(f"Unknown project_type: {project_type!r}")


def next_state(project, evaluation_kind: str, pass_status: str) -> str:
    """
    Regla de negocio: calcula el estado destino tras registrar una Evaluation.
    Pura — no toca la DB. El caller persiste el resultado junto con la
    Evaluation de forma atómica.
    """
    current = project.state
    if current in TERMINAL_STATES:
        raise InvalidTransition(
            f"Project is {current}; no further evaluations allowed."
        )
    if pass_status not in ('Pass', 'Fail'):
        raise InvalidTransition(f"Unknown pass_status: {pass_status!r}")
    if evaluation_kind not in ('review', 'defense'):
        raise InvalidTransition(f"Unknown evaluation kind: {evaluation_kind}")

    table = _table_for(project.project_type)
    key = (current, evaluation_kind, pass_status)
    if key not in table:
        raise InvalidTransition(
            f"Cannot record {evaluation_kind} on {project.project_type} "
            f"in state {current}."
        )
    return table[key]
