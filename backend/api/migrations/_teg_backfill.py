"""
Pure helper for migration 0035. Maps a TEG row's legacy (status, stage1_passed)
to the new `state` value. Importable by tests without running a migration.
"""


def compute_teg_state(*, status: str, stage1_passed: bool) -> str:
    if status == 'checked':
        return 'approved'
    if status == 'rejected':
        return 'failed_final'
    # status == 'pending' (or anything else conservatively treated as pending)
    return 'pending_defensa' if stage1_passed else 'pending_articulo'
