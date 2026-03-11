from django.contrib import admin
from .models import Course, CalendarEvent, Task, TaskSubmission, Enrollment, Lesson, Topic, Department

# Register your models here.
admin.site.register(Course)
admin.site.register(CalendarEvent)
admin.site.register(Task)
admin.site.register(TaskSubmission)
admin.site.register(Enrollment)
admin.site.register(Lesson)
admin.site.register(Topic)
admin.site.register(Department)