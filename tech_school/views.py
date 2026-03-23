from rest_framework import viewsets, status, permissions, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, RegisterSerializer, UserProfileSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from analytics.models import SystemLog
from django.http import HttpResponse
from rest_framework import generics, permissions
from .models import Profile, Transaction   
import requests
import uuid
from django.shortcuts import redirect
import json
import hmac
import hashlib
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from .models import Transaction 
from core.models import Enrollment
import os

User = get_user_model()



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        
        if self.action in ['register', 'create', 'login', 'forgot_password', 'validate_reset_token', 'reset_password_confirm']:
            return [permissions.AllowAny()]
        if self.action in ['list', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return RegisterSerializer
        return UserSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance == request.user:
            return Response({"error": "Cannot delete self."}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.is_active = False
        instance.save()
        
        SystemLog.objects.create(
            user=request.user,
            action=f"Archived user: {instance.username}",
            details=f"User ID {instance.id} marked as inactive."
        )
        
        return Response({"message": "Student archived successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "token": str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        email = request.data.get('email')
        # Use __iexact to avoid case-sensitivity issues
        user = User.objects.filter(email__iexact=email).first()
        
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            frontend_url = os.environ.get(
                "FRONTEND_URL",
                "http://localhost:5173"
            )
                
            # URL-safe link without the trailing slash to prevent 301 mangling
            reset_link = f"{frontend_url}/reset-password/{uid}/{token}"
            
            subject = "Reset Your Innovet Tech Password"
            message = (
                f"Hello {user.username},\n\n"
                f"We received a request to reset your password. "
                f"Click the link below to set a new one:\n\n"
                f"{reset_link}\n\n"
                f"If you didn't request this, you can safely ignore this email.\n"
                f"This link will expire in 24 hours."
            )
            import logging
            logger = logging.getLogger(__name__)

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                print(f"DEBUG: Reset link generated for {email}: {reset_link}")
            except Exception as e:
                logger.error(f"Email failed for {email}: {str(e)}")
                return Response(
                    {"error": "Email service temporarily unavailable"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            response_data = {"message": "If an account exists, a reset link has been sent."}
            if settings.DEBUG:
                response_data["debug_link"] = reset_link
                
            return Response(response_data, status=status.HTTP_200_OK)

        return Response({"message": "If an account exists, a reset link has been sent."}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['get'], url_path=r'validate-token/(?P<uidb64>[^/]+)/(?P<token>[^/]+)/?')
    def validate_reset_token(self, request, uidb64=None, token=None):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                return Response({"message": "Valid token"}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path=r'reset-password-confirm/(?P<uidb64>[^/]+)/(?P<token>[^/]+)/?')
    def reset_password_confirm(self, request, uidb64=None, token=None):
        """Step 3: Finalize password change"""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            new_password = request.data.get('password')
            if not new_password:
                return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
    
class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user 
    
    @action(detail=False, methods=['patch'], url_path='profile/update')
    def update_profile(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)  

@action(detail=True, methods=['post'], url_path='initialize-paystack')
def initialize_paystack(self, request, pk=None):
    course = self.get_object()
    url = "https://api.paystack.co/transaction/initialize"
    
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    amount_in_cents = int(course.price * 100)
    
    payload = {
        "email": request.user.email,
        "amount": amount_in_cents,
        "currency": "KES",
        "callback_url": "https://purposeless-unheeding-zula.ngrok-free.dev/api/payments/paystack-callback-bridge/",        "metadata": {
            "course_id": course.id,
            "user_id": request.user.id,
            "cart_id": f"INV-{request.user.id}-{course.id}"
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    res_data = response.json()

    if res_data['status']:
        Transaction.objects.create(
            user=request.user,
            course=course,
            tx_ref=res_data['data']['reference'],
            amount=course.price,
            status='PENDING'
        )
        return Response({"link": res_data['data']['authorization_url']})
    
    return Response({"error": "Paystack initialization failed"}, status=400)

def payment_verify_redirect(request):
    reference = request.GET.get('reference')
    return redirect(f"http://localhost:5173/payment-verify?reference={reference}")

class PaystackWebhookView(APIView):
    permission_classes = [AllowAny] 

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        paystack_signature = request.headers.get('x-paystack-signature')
        secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
        
        computed_hmac = hmac.new(
            secret, 
            request.body, 
            hashlib.sha512
        ).hexdigest()

        if computed_hmac != paystack_signature:
            return HttpResponse(status=401)

        payload = request.data
        event = payload.get('event')

        if event == "charge.success":
            data = payload.get('data')
            reference = data.get('reference')
            
            try:
                transaction = Transaction.objects.get(tx_ref=reference)
                if transaction.status == 'PENDING':
                    transaction.status = 'COMPLETED'
                    transaction.save()

                    Enrollment.objects.get_or_create(
                        user=transaction.user, 
                        course=transaction.course
                    )
            except Transaction.DoesNotExist:
                pass

        return HttpResponse(status=200)

def paystack_callback_bridge(request):
    """
    Acts as the HTTPS -> HTTP bridge for local development.
    """
    reference = request.GET.get('reference')
    return redirect(f"http://localhost:5173/payment-verify?reference={reference}")