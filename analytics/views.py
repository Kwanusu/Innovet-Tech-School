from django.db import models
from rest_framework import viewsets, permissions
from .models import SystemLog
from .serializers import SystemLogSerializer
    
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from core.models import Course, Enrollment

class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Automated logging view: Provides a history of grade changes and course updates.
    """
    queryset = SystemLog.objects.all().order_by('-timestamp')
    serializer_class = SystemLogSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminDashboardStatsView(APIView):
    """
    Gather aggregated data for the Admin Dashboard.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = {
            "metrics": {
                "total_students": Enrollment.objects.values('user').distinct().count(),
                "active_enrollments": Enrollment.objects.count(),
                "completion_rate": self._get_global_completion_rate(),
                "system_alerts": SystemLog.objects.filter(action__icontains='delete').count()
            },
            "recent_activity": self._get_recent_logs(),
            "course_distribution": self._get_course_popularity()
        }
        return Response(data)

    def _get_global_completion_rate(self):
        avg = Enrollment.objects.aggregate(avg_progress=models.Avg('progress_percent'))
        return round(avg['avg_progress'] or 0, 1)

    def _get_recent_logs(self):
        logs = SystemLog.objects.all().select_related('user').order_by('-timestamp')[:10]
        return SystemLogSerializer(logs, many=True).data

    def _get_course_popularity(self):
        return Course.objects.annotate(
            student_count=Count('enrollments')
        ).values('title', 'student_count').order_by('-student_count')[:5]    
