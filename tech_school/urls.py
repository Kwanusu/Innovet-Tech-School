from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ProfileUpdateView, PaystackWebhookView, paystack_callback_bridge

router = DefaultRouter()
router.register(r'auth', UserViewSet, basename='auth')

urlpatterns = [
    path('auth/profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('api/payments/paystack-webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
    path('api/payments/paystack-callback-bridge/', paystack_callback_bridge),
    path('', include(router.urls)),
    
]

