import pytest
from django.db.models import ProtectedError
from rest_framework.test import APIClient

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


@pytest.mark.django_db
class TestStateOverrideSerializerVisibility:
    def _setup(self):
        admin = User.objects.create_user(email="admin@x.com", password="x", role="Administrador")
        jurado = User.objects.create_user(email="j@x.com", password="x", role="Jurado")
        student = User.objects.create_user(email="st@x.com", password="x", role="Estudiante")
        tutor = User.objects.create_user(email="t@x.com", password="x", role="Tutor")
        project = Project.objects.create(
            title="P", student=student, project_type="proyecto", reviewer=jurado
        )
        StateOverride.objects.create(
            project=project, admin=admin,
            from_state="pending_review_1", to_state="approved",
            reason="reason with enough characters",
        )
        return admin, jurado, student, tutor, project

    def test_admin_sees_overrides(self, db):
        admin, _, _, _, project = self._setup()
        client = APIClient()
        client.force_authenticate(user=admin)
        res = client.get(f"/api/projects/{project.id}/")
        assert res.status_code == 200
        assert "stateOverrides" in res.data
        assert len(res.data["stateOverrides"]) == 1
        assert res.data["stateOverrides"][0]["to_state"] == "approved"

    def test_non_admin_does_not_see_overrides(self, db):
        admin, jurado, student, tutor, project = self._setup()
        for user in (jurado, student, tutor):
            client = APIClient()
            client.force_authenticate(user=user)
            res = client.get(f"/api/projects/{project.id}/")
            # Jurado has reviewer permission; student owns project; tutor may 404 if not advisor
            if res.status_code == 200:
                assert "stateOverrides" not in res.data, f"Leaked to {user.role}"
