from django.apps import AppConfig
from django.conf import settings

TEXT_MESSAGE_CHECK_SECS = getattr(settings, 'TEXT_MESSAGE_CHECK_SECS', 50)

class TeaserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'teaser'
    verbose_name = 'Text Messages'

    def ready(self):
        from .tasks import send_new_batch, check_batch_status
        send_new_batch(repeat=TEXT_MESSAGE_CHECK_SECS, repeat_until=None)
        check_batch_status(repeat=TEXT_MESSAGE_CHECK_SECS, repeat_until=None)
