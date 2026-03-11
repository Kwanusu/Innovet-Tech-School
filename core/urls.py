from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, TaskViewSet, EnrollmentViewSet, LessonViewSet, AdminDashboardViewSet,
    CalendarEventViewSet, TaskSubmissionViewSet, enroll_student
)
from . import views

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'calendar', CalendarEventViewSet, basename='calendar')
router.register(r'submissions', TaskSubmissionViewSet, basename='submission')
router.register(r'admin', AdminDashboardViewSet, basename='admin-dashboard')

urlpatterns = [
    path('', include(router.urls)),
    path('courses/<int:course_id>/enroll/', enroll_student, name='manual-enroll'),
]

