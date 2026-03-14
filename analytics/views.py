from django.db import models    
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from core.models import Course, Enrollment
from django.db.models.functions import TruncHour
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from .models import SystemLog
from .serializers import SystemLogSerializer

class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides raw log history and aggregated analytics for system health monitoring.
    """
    queryset = SystemLog.objects.all().order_by('-timestamp')
    serializer_class = SystemLogSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'], url_path='analytics')
    def get_analytics(self, request):
        """
        Returns aggregated data for the SystemAnalytics dashboard.
        """
        last_24_hours = timezone.now() - timedelta(hours=24)

        activity_query = (
            SystemLog.objects.filter(timestamp__gte=last_24_hours)
            .annotate(time=TruncHour('timestamp'))
            .values('time')
            .annotate(requests=Count('id'))
            .order_by('time')
        )

        activity_data = [
            {
                "time": item['time'].strftime('%H:%M'),
                "requests": item['requests']
            } for item in activity_query
        ]
        total_requests_24h = SystemLog.objects.filter(timestamp__gte=last_24_hours).count()
        security_alerts = SystemLog.objects.filter(
            timestamp__gte=last_24_hours, 
            action_type__icontains="SECURITY"
        ).count()

        return Response({
            "activityData": activity_data,
            "summary": {
                "dailyRequests": total_requests_24h,
                "securityLogs": security_alerts,
                "status": "Healthy"
            }
        })

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
