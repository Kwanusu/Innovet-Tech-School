import json
from django.db.models import Avg, Count
from requests import Response
from rest_framework import serializers
from .models import (
    Course, Enrollment, CalendarEvent, Task, 
    TaskSubmission, Department, Topic, Lesson, LessonProgress
) 
from analytics.models import SystemLog
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.decorators import action

User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    """Provides metadata for academic department categorization."""
    class Meta:
        model = Department
        fields = ['id', 'name']

class CalendarEventSerializer(serializers.ModelSerializer):
    """Handles course scheduling, including exams and deadlines."""
    course_title = serializers.ReadOnlyField(source='course.title')

    class Meta:
        model = CalendarEvent
        fields = ['id', 'course', 'course_title', 'title', 'start_time', 'end_time', 'is_exam']

class TaskSerializer(serializers.ModelSerializer):
    """Represents graded assignments linked to specific courses."""
    class Meta:
        model = Task
        fields = ['id', 'course', 'title', 'due_date', 'weight']

class SystemLogSerializer(serializers.ModelSerializer):
    """Technical audit trail for system-wide action tracking."""
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = SystemLog
        fields = ['id', 'action', 'user', 'user_name', 'timestamp', 'details']
        read_only_fields = fields

# --- Core Logic Serializers ---

class TaskSubmissionSerializer(serializers.ModelSerializer):
    """Manages student work uploads and grading workflows."""
    task_title = serializers.ReadOnlyField(source='task.title')
    course_title = serializers.ReadOnlyField(source='task.course.title')
    student_name = serializers.ReadOnlyField(source='student.username')

    class Meta:
        model = TaskSubmission
        fields = [
            'id', 'task', 'task_title', 'course_title', 'student', 
            'student_name', 'file', 'is_completed', 'progress_percentage', 
            'grade'
        ]
        read_only_fields = ['student']

class CourseSerializer(serializers.ModelSerializer):
    """Base representation of a course with nested read-only topic data."""
    teacher = serializers.StringRelatedField(read_only=True)
    topics = serializers.SerializerMethodField() 
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'code', 'description', 'is_enrolled', 
            'price', 'is_published', 'thumbnail', 'teacher', 'topics'
        ]

    def get_topics(self, obj):
        """Serializes nested topics and their respective lessons for read operations."""
        return [
            {
                "id": topic.id,
                "title": topic.title,
                "lessons": [{"id": l.id, "title": l.title} for l in topic.lessons.all()]
            }
            for topic in obj.topics.all()
        ]

    def validate(self, data):
        """Ensures logical consistency between publishing status and pricing."""
        is_published = data.get('is_published', getattr(self.instance, 'is_published', False))
        price = data.get('price', getattr(self.instance, 'price', 0))

        if is_published and float(price) < 0:
            raise serializers.ValidationError({"price": "Published courses must have a non-negative price."})
        return data 
    def get_is_enrolled(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.enrolled_students.filter(id=user.id).exists()
        return False

class LessonSerializer(serializers.ModelSerializer):
    """ Serializes individual Lesson data including user-specific completion status."""
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'video_url', 'lesson_type', 'order', 'is_completed']

    def get_is_completed(self, obj) -> bool:
        """
        Determines if the requesting user has completed this specific lesson.
        
        Returns:
            bool: True if a 'completed' LessonProgress record exists for the user.
        """
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return LessonProgress.objects.filter(
                user=user, 
                lesson=obj, 
                is_completed=True
            ).exists()
        return False

class LessonProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for the LessonProgress model.
    
    Used primarily for updating and retrieving the completion status 
    of a specific lesson for the authenticated user.
    """
    class Meta:
        model = LessonProgress
        fields = ['id', 'user', 'lesson', 'is_completed', 'completed_at']
        read_only_fields = ['id', 'user', 'completed_at']

    def validate(self, data):
        """
        Ensure that we don't create duplicate progress records.
        The 'unique_together' constraint in the model handles this at the DB level,
        but this provides a cleaner validation error in the API.
        """
        user = self.context['request'].user
        lesson = data.get('lesson')
        
        if LessonProgress.objects.filter(user=user, lesson=lesson).exists():
            raise serializers.ValidationError("Progress for this lesson already exists.")
        return data
    
class TopicSerializer(serializers.ModelSerializer):
    """Groups lessons into modular topics."""
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'title', 'lessons', 'order']

class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for the Course Curriculum view.
    
    Provides nested topics/lessons, a flat list of completed lesson IDs 
    for the sidebar, and an overall progress percentage for the UI progress bar.
    """
    topics = TopicSerializer(many=True, read_only=True)
    completed_lesson_ids = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'thumbnail', 
            'topics', 'completed_lesson_ids', 'progress_percentage'
        ]

    def get_completed_lesson_ids(self, obj) -> list:
        """
        Retrieves a list of IDs for all lessons the user has completed in this course.
        
        Returns:
            list: IDs of completed lessons, e.g., [12, 15, 20].
        """
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return LessonProgress.objects.filter(
                user=user, 
                lesson__topic__course=obj, 
                is_completed=True
            ).values_list('lesson_id', flat=True)
        return []

    def get_progress_percentage(self, obj) -> int:
        """
        Calculates the user's completion progress as an integer percentage.
        
        Returns:
            int: The percentage of course lessons completed (0-100).
        """
        user = self.context.get('request').user
        if user and user.is_authenticated:
            total_lessons = Lesson.objects.filter(topic__course=obj).count()
            if total_lessons == 0:
                return 0
            
            completed_count = LessonProgress.objects.filter(
                user=user, 
                lesson__topic__course=obj, 
                is_completed=True
            ).count()
            
            return round((completed_count / total_lessons) * 100)
        return 0

class EnrollmentSerializer(serializers.ModelSerializer):
    """Tracks student progress and calculates cumulative performance metrics."""
    student_name = serializers.ReadOnlyField(source='student.username')
    course_title = serializers.ReadOnlyField(source='course.title')
    overall_progress = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'course', 
            'course_title', 'grade', 'overall_progress', 'enrolled_at'
        ]

    def get_overall_progress(self, obj):
        """
        Aggregates TaskSubmission data to determine completion percentage.
        Local import prevents circular dependency issues during startup.
        """
        # IMPORT HERE to avoid the circular import crash
        from .models import TaskSubmission 

        metrics = TaskSubmission.objects.filter(
            student=obj.student, 
            task__course=obj.course
        ).aggregate(average_progress=Avg('progress_percentage'))
        
        avg = metrics.get('average_progress')
        return round(avg, 2) if avg is not None else 0.0
    
    @action(detail=False, methods=['get'], url_path='enrolled-courses')
    def enrolled_courses(self, request):        
        enrolled_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
        # courses = Course.objects.filter(id__in=enrolled_ids).annotate(
        #     student_count=Count('enrolled_students')
        # )
        courses = Course.objects.all().filter(enrolled_students=request.user, id__in=enrolled_ids).annotate(
        student_count=Count('enrolled_students')
        )                   
    
        print(f"DEBUG: Found {courses.count()} courses for student {request.user.username}") # Check your console!
        
        serializer = self.get_serializer(courses, many=True, context={'request': request})
        return Response(serializer.data)
    
class CourseCreateSerializer(serializers.ModelSerializer):
    """Handles bulk creation of a course including nested Topics and Lessons."""
    class Meta:
        model = Course
        fields = ['id', 'title', 'code', 'description', 'price', 'is_published', 'thumbnail']
        read_only_fields = ['teacher']

    def create(self, validated_data):
        """
        Parses multi-part form data to create a course hierarchy.
        Extracts stringified JSON topics and assigns the requesting user as the teacher.
        """
        request = self.context.get('request')
        if not (request and request.user):
            raise serializers.ValidationError("Valid user context required for course creation.")

        topics_raw = request.data.get('topics')
        try:
            topics_data = json.loads(topics_raw) if isinstance(topics_raw, str) else (topics_raw or [])
        except (ValueError, TypeError):
            topics_data = []

        validated_data['teacher'] = request.user
        course = Course.objects.create(**validated_data)

        for topic_item in topics_data:
            lessons_data = topic_item.pop('lessons', [])
            topic = Topic.objects.create(
                course=course, 
                title=topic_item.get('title'), 
                order=topic_item.get('order', 0)
            )
            
            for lesson_item in lessons_data:
                Lesson.objects.create(topic=topic, **lesson_item)
                
        return course

class StaffOnboardingSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=['TEACHER', 'ADMIN'])
    full_name = serializers.CharField(write_only=False) 

    class Meta:
        model = User
        fields = ['email', 'full_name', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role')
        full_name = validated_data.pop('full_name')

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'].split('@')[0],
            password=get_random_string(12),
            is_staff=True 
        )

        if role == 'ADMIN':
            user.is_superuser = True 
        
        user.save()
        return user  

class AdminUserSerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(AdminUserSerializer, self).__init__(*args, **kwargs)
        if 'password' in self.fields:
            self.fields.pop('password')

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'first_name', 
            'last_name', 'date_joined', 'last_login', 
            'course_count', 'enrollment_count', 'is_active'
        ]

    def get_course_count(self, obj):
        if obj.role == 'TEACHER':
            return obj.authored_courses.count()
        return 0

    def get_enrollment_count(self, obj):
        if obj.role == 'STUDENT':
            return obj.enrolled_courses.count()
        return 0      