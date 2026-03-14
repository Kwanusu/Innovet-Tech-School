from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ProfileUpdateView

router = DefaultRouter()
router.register(r'auth', UserViewSet, basename='auth')

urlpatterns = [
    path('auth/profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('', include(router.urls)),
    
]

