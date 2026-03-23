from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError 
from rest_framework.permissions import IsAuthenticated, IsAdminUser      
import json
from django.db import transaction
from .models import Task, Course, TaskSubmission, CalendarEvent, Enrollment, Topic, Lesson
from .serializers import (
    CourseDetailSerializer, TaskSerializer, EnrollmentSerializer, 
    CourseSerializer, CourseCreateSerializer, CalendarEventSerializer, 
    TaskSubmissionSerializer, LessonProgress, LessonSerializer, StaffOnboardingSerializer
)
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
import secrets
from tech_school.models import Transaction

User = get_user_model()

class AdminDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for the High-Level Admin Command Center.
    Provides system-wide metrics and user management.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def get_stats(self, request):
        """GET /api/admin/stats/"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        stats = {
            "metrics": {
                "total_students": User.objects.filter(role='STUDENT').count(),
                "total_teachers": User.objects.filter(role='TEACHER').count(),
                "active_courses": Course.objects.filter(is_published=True).count(),
                "total_revenue": Enrollment.objects.aggregate(total=Count('id'))['total'] or 0, # Adjust for your pricing logic
            },
            "growth": {
                "new_enrollments": Enrollment.objects.filter(enrolled_at__gte=last_30_days).count(),
                "completion_rate": 85, 
            }
        }
        return Response(stats)
    
    @action(detail=False, methods=['post'], url_path='invite-staff')
    def invite_staff(self, request):
        email = request.data.get('email')
        role = request.data.get('role', 'staff') 

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            temp_password = secrets.token_urlsafe(12)
            user = User.objects.create_user(
                email=email,
                username=email,
                password=temp_password,
                is_staff=True,
                role=role 
            )

            return Response({
                "message": f"Invitation sent to {email}",
                "temp_password": temp_password 
                
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='users')
    def list_users(self, request):
        """GET /api/admin/users/?role=TEACHER"""
        role = request.query_params.get('role', 'ALL')
        
        users = User.objects.all()
        if role != 'ALL':
            users = users.filter(role=role)

        user_data = users.values('id', 'username', 'email', 'role', 'date_joined')
        return Response(user_data)

    @action(detail=False, methods=['get'], url_path='logs')
    def system_logs(self, request):
        """GET /api/admin/logs/"""
        logs = [
            {"id": 1, "action": "Course Created", "user": "Admin", "time": "2 mins ago"},
            {"id": 2, "action": "New Enrollment", "user": "Student_01", "time": "15 mins ago"},
        ]
        return Response(logs)

class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing course instances.
    Provides logic for public listings, teacher-owned courses, and student enrollments.
    """
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user
        base_queryset = Course.objects.annotate(student_count=Count('enrolled_students'))

        # If we are inside the 'enrolled_courses' action, we want a wider net
        if self.action == 'enrolled_courses':
            return base_queryset.filter(enrolled_students=user)

        if user.is_anonymous:
            return base_queryset.filter(is_published=True, price=0)
        
        if user.role == 'TEACHER':
            return base_queryset.filter(teacher=user)
            
        if user.role == 'STUDENT':
            # This logic is good, but ensure your test course is actually IS_PUBLISHED=True
            return base_queryset.filter(Q(enrolled_students=user) | Q(is_published=True, price=0)).distinct()
            
        return base_queryset.all()

    def get_permissions(self):
        # Add your custom GET actions to the AllowAny if you want them public,
        # OR ensure they are explicitly handled.
        if self.action in ['list', 'retrieve', 'enrolled_courses', 'my_courses']:
            return [permissions.IsAuthenticated()] # These MUST be authenticated
        
        if self.action in ['list', 'retrieve']:
             return [permissions.AllowAny()]
             
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='enrolled-courses')
    def enrolled_courses(self, request):
        # We call self.get_queryset() here to respect the logic above
        courses = self.get_queryset().distinct()
        
        # DEBUG: Check your terminal!
        print(f"User: {request.user} | Role: {request.user.role} | Count: {courses.count()}")
        
        serializer = self.get_serializer(courses, many=True, context={'request': request})
        return Response(serializer.data)

    # def get_permissions(self):
    #     """
    #     Allows anyone to view course lists/details, but requires authentication for modifications.
    #     """
    #     if self.action in ['list', 'retrieve']:
    #         return [permissions.AllowAny()]
    #     return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """
        Returns specialized serializers for different actions:
        - create: CourseCreateSerializer (handles teacher assignment).
        - retrieve: CourseDetailSerializer (includes full related data).
        - default: CourseSerializer.
        """
        if self.action == 'create':
            return CourseCreateSerializer
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer

    def perform_create(self, serializer):
        """
        Assigns the current user as the teacher of the course.
        Only users with the 'TEACHER' role or Admin status can create courses.
        """
        if self.request.user.role != 'TEACHER' and not self.request.user.is_staff:
            raise PermissionDenied("Only teachers can create courses.")
        serializer.save(teacher=self.request.user)


    @action(detail=True, methods=['patch', 'put'], url_path='update')
    def update_course(self, request, pk=None):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        with transaction.atomic():

            course.title = request.data.get('title', course.title)
            course.code = request.data.get('code', course.code)
            course.description = request.data.get('description', course.description)
            course.price = request.data.get('price', course.price)
            course.is_published = request.data.get('is_published') == 'true'
            
            if 'thumbnail' in request.FILES:
                course.thumbnail = request.FILES['thumbnail']
            
            course.save()

            topics_json = request.data.get('topics')
            if topics_json:
                topics_data = json.loads(topics_json)
       
                keep_topic_ids = []
                
                for t_data in topics_data:
                    topic_id = t_data.get('id')
               
                    topic, created = Topic.objects.update_or_create(
                        id=topic_id if isinstance(topic_id, int) else None,
                        course=course,
                        defaults={
                            'title': t_data['title'],
                            'order': t_data['order']
                        }
                    )
                    keep_topic_ids.append(topic.id)
               
                    keep_lesson_ids = []
                    for l_data in t_data.get('lessons', []):
                        lesson_id = l_data.get('id')
                        
                        lesson, l_created = Lesson.objects.update_or_create(
                            id=lesson_id if isinstance(lesson_id, int) else None,
                            topic=topic,
                            defaults={
                                'title': l_data['title'],
                                'content': l_data['content'],
                                'lesson_type': l_data.get('lesson_type', 'LESSON'),
                                'order': l_data['order']
                            }
                        )
                        keep_lesson_ids.append(lesson.id)
                   
                    topic.lessons.exclude(id__in=keep_lesson_ids).delete()

                course.topics.exclude(id__in=keep_topic_ids).delete()

        serializer = CourseSerializer(course, context={'request': request})
        return Response(serializer.data)    

    @action(detail=False, methods=['get'], url_path='my-courses')
    def my_courses(self, request):
        """
        GET /api/courses/my-courses/
        Dashboard endpoint for teachers to view courses they have created.
        """
        if request.user.role != 'TEACHER':
            return Response({"detail": "Access restricted to teachers."}, status=403)
        
        courses = Course.objects.filter(teacher=request.user).annotate(
            student_count=Count('enrolled_students')
        )
        serializer = self.get_serializer(courses, many=True, context={'request': request})
        return Response(serializer.data)

    # @action(detail=False, methods=['get'], url_path='enrolled-courses')
    # def enrolled_courses(self, request):
    #     """
    #     GET /api/courses/enrolled-courses/
    #     Dashboard endpoint for students to view courses they are currently enrolled in.
    #     """
    #     if request.user.role != 'STUDENT':
    #         return Response({"detail": "Access restricted to students."}, status=403)

    #     courses = Course.objects.filter(enrolled_students=request.user).annotate(
    #         student_count=Count('enrolled_students')
    #     ).distinct()
    #     serializer = self.get_serializer(courses, many=True, context={'request': request})
    #     return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='initialize-paystack')
    def initialize_paystack(self, request, pk=None):
        """
        POST /api/courses/{id}/initialize-paystack/
        Initializes a Paystack transaction for a specific course.
        """
        course = self.get_object()
        user = request.user

        if course.enrolled_students.filter(id=user.id).exists():
            return Response({"error": "You are already enrolled in this course."}, status=400)

        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        amount_in_cents = int(course.price * 100)
        
        payload = {
            "email": user.email,
            "amount": amount_in_cents,
            "currency": "KES",
            "callback_url": "https://purposeless-unheeding-zula.ngrok-free.dev/api/payments/paystack-callback-bridge/",
            "metadata": {
                "course_id": course.id,
                "user_id": user.id,
                "course_title": course.title
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            res_data = response.json()

            if res_data.get('status'):
                # 3. Create a local record of the pending transaction
                Transaction.objects.create(
                    user=user,
                    course=course,
                    tx_ref=res_data['data']['reference'],
                    amount=course.price,
                    status='PENDING'
                )
                # Return the checkout link to the React frontend
                return Response({"link": res_data['data']['authorization_url']})
            
            return Response({"error": "Paystack was unable to initialize."}, status=400)

        except requests.exceptions.RequestException as e:
            return Response({"error": f"Connection to Paystack failed: {str(e)}"}, status=503)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course Tasks.
    Visibility is restricted to courses the user is involved in.
    """
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        Restricts task visibility:
        - Students: Tasks from courses they are enrolled in.
        - Teachers: Tasks from courses they teach.
        """
        user = self.request.user
        if user.role == 'STUDENT':
            return Task.objects.filter(course__enrolled_students=user)
        if user.role == 'TEACHER':
            return Task.objects.filter(course__teacher=user)
        return Task.objects.all()

class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet to manage student enrollments.
    Handles manual teacher enrollment and student history.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Students only see their own progress
        if user.role == 'STUDENT':
            return Enrollment.objects.filter(student=user).select_related('course')
        # Staff/Teachers see everything
        return Enrollment.objects.all().select_related('student', 'course')

    def create(self, request, *args, **kwargs):
        """
        Custom create to handle enrollment via email from the Quick Enroll modal.
        """
        if request.user.role not in ['ADMIN', 'TEACHER']:
            raise PermissionDenied("Only instructors or admins can manually enroll students.")

        email = request.data.get('email')
        course_id = request.data.get('courseId') 

        if not email or not course_id:
            raise ValidationError({"error": "Both email and courseId are required."})

        try:
            student = User.objects.get(email=email)
            course = Course.objects.get(id=course_id)

            # Check if already enrolled to prevent duplicates
            if Enrollment.objects.filter(student=student, course=course).exists():
                return Response(
                    {"error": "This student is already enrolled in this course."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create the enrollment
            enrollment = Enrollment.objects.create(
                student=student, 
                course=course,
                enrollment_type='MANUAL' # Good for tracking paid vs manual
            )

            # Ensure the ManyToMany field on Course is also updated
            course.enrolled_students.add(student)

            serializer = self.get_serializer(enrollment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response({"error": "No account found with this email."}, status=404)
        except Course.DoesNotExist:
            return Response({"error": "Course not found."}, status=404)

    def perform_create(self, serializer):
        # Fallback for standard POST requests
        if self.request.user.role not in ['ADMIN', 'TEACHER']:
            raise PermissionDenied("Only staff can enroll students.")
        serializer.save()

class CalendarEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for course-related calendar events.
    """
    serializer_class = CalendarEventSerializer

    def get_queryset(self):
        """
        Filters events based on the user's participation in the associated course.
        """
        user = self.request.user
        if user.role == 'STUDENT':
            return CalendarEvent.objects.filter(course__enrolled_students=user)
        if user.role == 'TEACHER':
            return CalendarEvent.objects.filter(course__teacher=user)
        return CalendarEvent.objects.all()


class TaskSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling student task submissions and teacher grading.
    """
    serializer_class = TaskSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Ensures students see only their work, and teachers see work for their courses.
        """
        user = self.request.user
        if user.role == 'STUDENT':
            return TaskSubmission.objects.filter(student=user)
        return TaskSubmission.objects.filter(task__course__teacher=user)

    def perform_create(self, serializer):
        """
        Automatically assigns the submitting user as the 'student' on the submission.
        """
        serializer.save(student=self.request.user)

    @action(detail=True, methods=['post'], url_path='grade')
    def grade(self, request, pk=None):
        """
        POST /api/submissions/{id}/grade/
        Allows a teacher to apply a grade and feedback to a specific submission.
        Validates that the requester is the instructor for the course.
        """
        submission = self.get_object()
        if request.user != submission.task.course.teacher:
            raise PermissionDenied("You are not authorized to grade this course.")

        grade = request.data.get('grade')
        feedback = request.data.get('feedback', '')

        if grade is None:
            return Response({"error": "Grade is required"}, status=400)

        submission.grade = grade
        submission.feedback = feedback
        submission.is_graded = True 
        submission.save()

        serializer = self.get_serializer(submission)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enroll_student(request, course_id):
    """
    Functional view to manually enroll a student into a course via email.
    
    Expects:
    - course_id: URL parameter
    - email: JSON body key
    
    Actions:
    1. Validates user exists and has 'STUDENT' role.
    2. Adds user to Course.enrolled_students (M2M).
    3. Creates/Updates Enrollment tracking model record.
    """
    email = request.data.get('email')
    try:
        student = User.objects.get(email__iexact=email)
        course = Course.objects.get(id=course_id)
        
        if student.role != 'STUDENT':
            return Response({"message": "User is not a student."}, status=400)
            
        if course.enrolled_students.filter(id=student.id).exists():
            return Response({"message": "Student already enrolled"}, status=400)
            
        course.enrolled_students.add(student)
        Enrollment.objects.get_or_create(student=student, course=course)
        
        return Response({"message": f"Successfully enrolled {email}"}, status=200)

    except User.DoesNotExist:
        return Response({"message": "No student found with this email"}, status=404)
    except Course.DoesNotExist:
        return Response({"message": "Course not found"}, status=404)

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='complete')
    def mark_complete(self, request, pk=None):
        """
        Custom action to mark a lesson as completed for the current user.
        URL: /api/lessons/{id}/complete/
        """
        lesson = self.get_object()
        user = request.user

        progress, created = LessonProgress.objects.update_or_create(
            user=user,
            lesson=lesson,
            defaults={'is_completed': True}
        )

        course = lesson.topic.course
        total_lessons = Lesson.objects.filter(topic__course=course).count()
        completed_lessons = LessonProgress.objects.filter(
            user=user, 
            lesson__topic__course=course, 
            is_completed=True
        ).count()
        
        overall_percent = round((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

        return Response({
            'status': 'success',
            'lessonId': lesson.id,
            'progress': {
                'completed_count': completed_lessons,
                'total_count': total_lessons,
                'overall_percent': overall_percent
            }
        }, status=status.HTTP_200_OK)    
        
        
class StaffManagementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return User.objects.filter(role__in=['TEACHER', 'ADMIN']).annotate(
            courses_led=Count('authored_courses'), # Assuming a related_name in Course model
            active_students=Count('authored_courses__enrollments', distinct=True)
        ) 

class InviteStaffView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        requested_role = request.data.get('role')
        if requested_role == 'ADMIN' and not request.user.is_superuser:
            return Response(
                {"detail": "Unauthorized. Only Superusers can promote others to Admin."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = StaffOnboardingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": f"Successfully onboarded {requested_role}"}, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)               