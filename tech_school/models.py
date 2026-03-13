from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"
        
    role = models.CharField(max_length=25, choices=Role.choices, default=Role.ADMIN)
    email = models.EmailField(unique=True)

# The new Profile model
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, help_text="Short biography of the user.")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"
    
    @property
    def is_teacher(self):
        """Quick check to verify if the user has teacher-level permissions."""
        return self.role == self.Role.TEACHER 

# --- SIGNALS ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

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