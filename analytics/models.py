from django.db import models
from django.conf import settings

class SystemLog(models.Model):
    """
    A low-level logging model designed for technical debugging and 
    state-change tracking across the entire platform.
    """
    action = models.CharField(
        max_length=255, 
        help_text="The internal method or process triggered (e.g., 'COURSE_UPDATE')."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="The user responsible for the action; NULL if a system task."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True 
    )

    details = models.JSONField(
        default=dict, 
        help_text="Stores structural data like {'old_price': 20, 'new_price': 15}."
    )

    class Meta:
        verbose_name = "System Log"
        verbose_name_plural = "System Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.user or 'SYSTEM'} @ {self.timestamp.isoformat()}"