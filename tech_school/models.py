from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser to include
    role-based access control (RBAC) and profile metadata.
    """
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"
        
    role = models.CharField(
        max_length=25,
        choices=Role.choices, 
        default=Role.ADMIN,
        help_text="Determines user permissions and dashboard access."
    )
    bio = models.TextField(blank=True, help_text="Short biography of the user.")
    email = models.EmailField(unique=True)
    
    @property
    def is_teacher(self):
        """Quick check to verify if the user has teacher-level permissions."""
        return self.role == self.Role.TEACHER 

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class AuditLog(models.Model):
    """
    System-wide logging for tracking user actions and security events.
    Stored with a link to the user, but preserved even if the user is deleted.
    """
    action_type = models.CharField(max_length=50, help_text="Category of action (e.g., LOGIN, DELETE_COURSE).")
    message = models.TextField(help_text="Detailed description of the event.")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='logs', 
        on_delete=models.SET_NULL, 
        null=True
    )

    class Meta:
        ordering = ['-timestamp']    
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        user_str = self.user.username if self.user else "System/Deleted User"
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} - {user_str}: {self.action_type}"