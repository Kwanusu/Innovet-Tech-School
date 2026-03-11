from rest_framework import serializers
from .models import SystemLog

class SystemLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for system events and change-tracking data.
    Provides human-readable user mapping and formatted timestamps for UI consistency.
    """
    user_name = serializers.ReadOnlyField(source='user.username')
    formatted_time = serializers.DateTimeField(
        source='timestamp', 
        format="%Y-%m-%d %H:%M:%S", 
        read_only=True
    )
    severity = serializers.SerializerMethodField()
    class Meta:
        model = SystemLog
        fields = [
            'id', 'action', 'user', 'user_name', 
            'timestamp', 'formatted_time', 'details'
        ]
        
        read_only_fields = fields
        

    def get_severity(self, obj):
        """Maps actions to UI color schemes."""
        if 'delete' in obj.action.lower():
            return 'error'  # Red in UI
        if 'update' in obj.action.lower():
            return 'warning' # Amber in UI
        return 'info' # Blue in UI