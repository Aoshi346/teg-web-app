import pytest
from django.db.models import ProtectedError

from api.models import Project, StateOverride, User


@pytest.mark.django_db
class TestStateOverrideModel:
    def test_save_and_ordering_newest_first(self, db):
        admin = User.objects.create_user(email="a@x.com", password="x", role="Administrador")
        student = User.objects.create_user(email="s@x.com", password="x", role="Estudiante")
        project = Project.objects.create(title="P", student=student, project_type="proyecto")

        StateOverride.objects.create(
            project=project, admin=admin,
            from_state="pending_review_1", to_state="pending_defense",
            reason="first override reason text",
        )
        StateOverride.objects.create(
            project=project, admin=admin,
            from_state="pending_defense", to_state="approved",
            reason="second override reason text",
        )

        overrides = list(project.state_overrides.all())
        assert len(overrides) == 2
        assert overrides[0].to_state == "approved"
        assert overrides[1].to_state == "pending_defense"

    def test_admin_on_delete_protect(self, db):
        admin = User.objects.create_user(email="a2@x.com", password="x", role="Administrador")
        student = User.objects.create_user(email="s2@x.com", password="x", role="Estudiante")
        project = Project.objects.create(title="P2", student=student, project_type="proyecto")
        StateOverride.objects.create(
            project=project, admin=admin,
            from_state="pending_review_1", to_state="approved",
            reason="reason with enough characters",
        )
        with pytest.raises(ProtectedError):
            admin.delete()
