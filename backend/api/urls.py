from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuthViewSet,
    CommentViewSet,
    CsrfTokenView,
    EvaluationViewSet,
    NotificationViewSet,
    PresentationDayViewSet,
    PresentationViewSet,
    ProjectViewSet,
    SemesterViewSet,
    SessionViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'evaluations', EvaluationViewSet)
router.register(r'semesters', SemesterViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'sessions', SessionViewSet, basename='sessions')
router.register(r'planificacion/days', PresentationDayViewSet, basename='presentation-day')
router.register(r'planificacion/presentations', PresentationViewSet, basename='presentation')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('csrf/', CsrfTokenView.as_view(), name='csrf'),
]
