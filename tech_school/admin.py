from django.contrib import admin
from .models import User, AuditLog

# Register your models here.
admin.site.register(User)
admin.site.register(AuditLog)