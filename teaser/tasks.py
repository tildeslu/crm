from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from background_task import background
from .models import TextMessage, TextMessageBatch
from .providers import omnicell, fakecell

from jigger.events import register_event_response

TEXT_MESSAGE_MAX_BATCH = getattr(settings, 'TEXT_MESSAGE_MAX_BATCH', 1000)
TEXT_MESSAGE_PROVIDER = getattr(settings, 'TEXT_MESSAGE_PROVIDER', 'UNKNOWN')
TEXT_MESSAGE_CHECK_SECS = getattr(settings, 'TEXT_MESSAGE_CHECK_SECS', 50)
TEXT_MESSAGE_EXPIRE_SECS = getattr(settings, 'TEXT_MESSAGE_EXPIRE_SECS', 259200)

PROVIDERS = {
    'OMNICELL': omnicell,
    'FAKECELL': fakecell,
}

@background(remove_existing_tasks=True, queue='teaser')
def send_new_batch():
    # group new additions into the batches
    while True:
        msgs = TextMessage.objects.filter(status=TextMessage.Status.NEW, batch=None)[:TEXT_MESSAGE_MAX_BATCH]
        if msgs.count() == 0:
            break

        b = TextMessageBatch()
        b.provider = TEXT_MESSAGE_PROVIDER
        b.save()

        for m in msgs:
            m.batch = b

        TextMessage.objects.bulk_update(msgs, ['batch'])

    # send in batches
    batches = TextMessageBatch.objects.filter(sent=False)
    if batches.count() > 0:
        for b in batches:
            provider = PROVIDERS.get(b.provider)
            if provider:
                provider.send_batch(b)


@background(remove_existing_tasks=True, queue='teaser')
def check_batch_status():
    # check expiration
    expire_threshold = timezone.now() - timedelta(seconds=TEXT_MESSAGE_EXPIRE_SECS)
    expired = TextMessage.objects.filter(status__in=TextMessage.nonterminal_status_list(), timestamp__lt=expire_threshold)
    if expired.count() != 0:
        for m in expired:
            m.status = TextMessage.Status.EXPIRED
        TextMessage.objects.bulk_update(expired, ['status'])

    # check active batches
    time_threshold = timezone.now() - timedelta(seconds=TEXT_MESSAGE_CHECK_SECS)
    batches = TextMessageBatch.objects.filter(finalized=False, timestamp__lt=time_threshold)
    for b in batches:
        provider = PROVIDERS.get(b.provider)
        if provider:
            provider.check_batch_status(b)

        if b.textmessage_set.filter(status__in=TextMessage.nonterminal_status_list()).count() == 0:
            b.finalized = True
            b.save()

    # send notification to delivered messages
    while True:
        msgs = TextMessage.objects.filter(notified=False, status__in=TextMessage.terminal_status_list())[:TEXT_MESSAGE_MAX_BATCH]
        if msgs.count() == 0:
            break

        for m in msgs:
            if m.producer:
                register_event_response(m.producer, __name__, "status", {"status":TextMessage.Status(m.status).name})
            m.notified = True

        TextMessage.objects.bulk_update(msgs, ['notified'])
