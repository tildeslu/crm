from django.apps import AppConfig
from django.conf import settings

EVENT_CHECK_SECS = getattr(settings, 'EVENT_CHECK_SECS', 10)

class JiggerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jigger'
    verbose_name = 'Campaign processing'

    def ready(self):
        from .tasks import start_funnels, process_events
        start_funnels(repeat=EVENT_CHECK_SECS, repeat_until=None)
        process_events(repeat=EVENT_CHECK_SECS, repeat_until=None)

