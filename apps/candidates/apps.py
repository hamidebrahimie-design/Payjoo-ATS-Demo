from django.apps import AppConfig

class CandidatesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.candidates'
    verbose_name = 'مدیریت کاندیداها'

    def ready(self):
        import apps.candidates.signals
