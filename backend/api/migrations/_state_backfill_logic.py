"""
Lógica compartida de backfill para la migración 0030 y sus tests.

Vive aquí (no en `api/lifecycle.py`) porque es lógica de migración — se usa
una sola vez y su firma trabaja con modelos histórícos/snapshots, no con la
máquina de estados operativa. Colocarla junto a la migración evita que
cambios futuros en `lifecycle.py` rompan silenciosamente la migración.
"""


def derive_state(project, evaluations) -> str:
    """
    Deriva el estado inicial de un proyecto PTEG a partir de su historial legacy:
      - Evaluations existentes (con pass_status 'Pass'/'Fail')
      - Contador legacy `failed_attempts`
      - `status` legacy ('checked'/'pending'/'rejected')

    Reglas (prioridad):
      1. status='checked'   → approved (el caso de "defensa ya ocurrió")
      2. hay al menos un Pass → pending_defense
      3. 2+ Fails o failed_attempts>=2 → failed_final
      4. 1 Fail o failed_attempts==1 → pending_review_2
      5. default → pending_review_1
    """
    fails = sum(1 for e in evaluations if e.pass_status == 'Fail')
    has_pass = any(e.pass_status == 'Pass' for e in evaluations)

    if project.status == 'checked':
        return 'approved'
    if has_pass:
        return 'pending_defense'
    if fails >= 2 or (project.failed_attempts or 0) >= 2:
        return 'failed_final'
    if fails == 1 or (project.failed_attempts or 0) == 1:
        return 'pending_review_2'
    return 'pending_review_1'
