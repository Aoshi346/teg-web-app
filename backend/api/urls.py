from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet, ProjectViewSet, CsrfTokenView, EvaluationViewSet, SemesterViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'evaluations', EvaluationViewSet)
router.register(r'semesters', SemesterViewSet)
router.register(r'comments', CommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('csrf/', CsrfTokenView.as_view(), name='csrf'),
]
