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


@pytest.mark.django_db
class TestOverrideEndpointAuth:
    def _make_project(self):
        student = User.objects.create_user(email="s3@x.com", password="x", role="Estudiante")
        return Project.objects.create(title="P3", student=student, project_type="proyecto")

    def test_anonymous_forbidden(self, db):
        project = self._make_project()
        client = APIClient()
        res = client.post(
            f"/api/projects/{project.id}/override_state/",
            {"state": "approved", "reason": "reason with enough characters"},
            format="json",
        )
        assert res.status_code in (401, 403)
        assert StateOverride.objects.count() == 0

    @pytest.mark.parametrize("role", ["Estudiante", "Jurado", "Tutor"])
    def test_non_admin_forbidden(self, db, role):
        project = self._make_project()
        user = User.objects.create_user(email=f"{role}@x.com", password="x", role=role)
        client = APIClient()
        client.force_authenticate(user=user)
        res = client.post(
            f"/api/projects/{project.id}/override_state/",
            {"state": "approved", "reason": "reason with enough characters"},
            format="json",
        )
        assert res.status_code == 403
        assert StateOverride.objects.count() == 0
        project.refresh_from_db()
        assert project.state == "pending_review_1"

    def test_admin_happy_path(self, db):
        project = self._make_project()
        admin = User.objects.create_user(email="adm@x.com", password="x", role="Administrador")
        client = APIClient()
        client.force_authenticate(user=admin)
        res = client.post(
            f"/api/projects/{project.id}/override_state/",
            {"state": "approved", "reason": "appealed via dean's office"},
            format="json",
        )
        assert res.status_code == 200
        assert res.data["state"] == "approved"


@pytest.mark.django_db
class TestOverrideEndpointValidation:
    def _setup(self):
        student = User.objects.create_user(email="sv@x.com", password="x", role="Estudiante")
        project = Project.objects.create(title="PV", student=student, project_type="proyecto")
        admin = User.objects.create_user(email="admv@x.com", password="x", role="Administrador")
        client = APIClient()
        client.force_authenticate(user=admin)
        return client, project

    def test_invalid_state_value(self, db):
        client, project = self._setup()
        res = client.post(
            f"/api/projects/{project.id}/override_state/",
            {"state": "gibberish", "reason": "reason with enough characters"},
            format="json",
        )
        assert res.status_code == 400
        assert "state" in res.data
        assert StateOverride.objects.count() == 0

    def test_state_equals_current(self, db):
        client, project = self._setup()
        res = client.post(
            f"/api/projects/{project.id}/override_state/",
            {"state": project.state, "reason": "reason with enough characters"},
            format="json",
        )
        assert res.status_code == 400
        assert "state" in res.data

    def test_reason_missing(self, db):
        client, project = self._setup()
        res = client.post(
            f"/api/projects/{project.id}/override_state/",
            {"state": "approved"},
            format="json",
        )
        assert res.status_code == 400
        assert "reason" in res.data

    def test_reason_too_short(self, db):
        client, project = self._setup()
        res = client.post(
            f"/api/projects/{project.id}/override_state/",
            {"state": "approved", "reason": "   short   "},
            format="json",
        )
        assert res.status_code == 400
        assert "reason" in res.data

    def test_tesis_rejected(self, db):
        student = User.objects.create_user(email="tesis@x.com", password="x", role="Estudiante")
        project = Project.objects.create(title="T", student=student, project_type="tesis")
        admin = User.objects.create_user(email="admt@x.com", password="x", role="Administrador")
        client = APIClient()
        client.force_authenticate(user=admin)
        res = client.post(
            f"/api/projects/{project.id}/override_state/",
            {"state": "approved", "reason": "reason with enough characters"},
            format="json",
        )
        assert res.status_code == 400
        assert "project_type" in res.data
        assert StateOverride.objects.count() == 0
        project.refresh_from_db()
        assert project.state == "pending_review_1"
