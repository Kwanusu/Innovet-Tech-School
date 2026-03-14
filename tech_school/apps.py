from django.apps import AppConfig


class TechSchoolConfig(AppConfig):
    name = 'tech_school'
    
def ready(self):
        # This import is internal to the function to avoid circular imports
        import tech_school.signals    
