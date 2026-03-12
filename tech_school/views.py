from rest_framework import viewsets, status, permissions, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, RegisterSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from analytics.models import SystemLog
from django.http import HttpResponse

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
        user = User.objects.filter(email=email).first()
        
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            frontend_url = "https://innovet-tech-school.vercel.app"
            if settings.DEBUG:
                frontend_url = "http://localhost:5173"
                
            reset_link = f"{frontend_url}/reset-password/{uid}/{token}/"
            
            subject = "Reset Your Innovet Tech Password"
            message = (
                f"Hello {user.username},\n\n"
                f"We received a request to reset your password. "
                f"Click the link below to set a new one:\n\n"
                f"{reset_link}\n\n"
                f"If you didn't request this, you can safely ignore this email.\n"
                f"This link will expire in 24 hours."
            )

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email failed: {e}") 

            response_data = {"message": "If an account exists, a reset link has been sent."}
            if settings.DEBUG:
                response_data["debug_link"] = reset_link
                
            return Response(response_data, status=status.HTTP_200_OK)

        return Response({"message": "If an account exists, a link has been sent."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='validate-token/(?P<uidb64>[^/.]+)/(?P<token>[^/.]+)')
    def validate_reset_token(self, request, uidb64=None, token=None):
        """Step 2: Check link validity before showing forms"""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                return Response({"message": "Valid token"}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='reset-password-confirm/(?P<uidb64>[^/.]+)/(?P<token>[^/.]+)')
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