# tech_school/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile
from core.models import Enrollment

@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=Enrollment)
def sync_course_enrollment(sender, instance, created, **kwargs):
    """
    Automatically adds the student to the Course.enrolled_students 
    ManyToMany field whenever an Enrollment record is created.
    """
    if created:
        instance.course.enrolled_students.add(instance.student)        