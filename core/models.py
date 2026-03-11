from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

class CourseQuerySet(models.QuerySet):
    """Custom QuerySet for Course-related filtering logic."""
    
    def published_free(self):
        """Returns only published courses that have a price of 0."""
        return self.filter(is_published=True, price=0)
    
    def by_teacher(self, user):
        """Returns courses associated with a specific teacher user."""
        return self.filter(teacher=user)

class Department(models.Model):
    """Represents an academic department (e.g., Computer Science)."""
    name = models.CharField(max_length=100)

    def __str__(self): 
        return self.name

class Course(models.Model):
    """
    The central model representing a course of study. 
    Handles pricing, publishing status, and teacher assignment.
    """
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=False)
    thumbnail = models.ImageField(upload_to='course_thumbs/', null=True, blank=True)
    
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'TEACHER'},
        related_name='created_courses'
    )

    enrolled_students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='enrolled_courses',
        blank=True
    )
    
    objects = CourseQuerySet.as_manager()

    def clean(self):
        """Validates that a published course cannot have a negative price."""
        if self.is_published and self.price < 0:
            raise ValidationError("Price must be a non-negative value.")

    def save(self, *args, **kwargs):
        """Overrides save to ensure full_clean() is called for validation."""
        if self.teacher_id: 
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self): 
        return self.title

class Topic(models.Model):
    """A module or section within a specific Course."""
    course = models.ForeignKey(Course, related_name='topics', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.code} - {self.title}"

class Lesson(models.Model):
    """Individual learning units (videos, readings, or projects) within a Topic."""
    LESSON_TYPES = (
        ('LESSON', 'Standard Lesson'),
        ('CHALLENGE', 'Daily Challenge'),
        ('WEEKLY_PROJECT', 'Weekly Project'),
        ('CAPSTONE', 'Capstone Project'),
    )
    
    topic = models.ForeignKey(Topic, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="The actual reading/video material")
    video_url = models.URLField(blank=True, null=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='LESSON')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"[{self.lesson_type}] {self.title}"
    
class LessonProgress(models.Model):
    """
    Tracks a specific user's completion status for an individual lesson.
    
    This acts as a 'through' table between Users and Lessons, allowing 
    the system to maintain unique progress states for every student.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='lesson_progress',
        help_text="The student whose progress is being tracked."
    )
    lesson = models.ForeignKey(
        'Lesson', 
        on_delete=models.CASCADE, 
        related_name='user_progress',
        help_text="The specific lesson being completed."
    )
    is_completed = models.BooleanField(
        default=False,
        help_text="True if the student has finished the lesson content."
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The exact timestamp when the lesson was first marked complete."
    )

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name_plural = "Lesson Progresses"

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({'Done' if self.is_completed else 'Pending'})"
    
class Enrollment(models.Model):
    """Tracking model for student enrollment, specific grades, and timestamps."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'},
        related_name='enrollment_records' 
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE,
        related_name='enrollments' 
    )
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.email} in {self.course.title}"

class CalendarEvent(models.Model):
    """Scheduled events for a course, such as live lectures or exams."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_exam = models.BooleanField(default=False)

class Task(models.Model):
    """An assignment or task within a course that carries a specific weight toward the grade."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    due_date = models.DateTimeField()
    weight = models.IntegerField(default=10)

class TaskSubmission(models.Model):
    """Records the work submitted by a student for a specific Task."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='submissions/')
    is_completed = models.BooleanField(default=False)
    progress_percentage = models.IntegerField(default=0)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_graded = models.BooleanField(default=False)