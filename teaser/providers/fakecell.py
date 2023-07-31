from ..models import TextMessage, TextMessageBatch

def send_batch(batch):
    msgs = list(batch.textmessage_set.all())
    for msg in msgs:
        msg.internal_id = str(msg.id)
        msg.status = TextMessage.Status.SENT
    TextMessage.objects.bulk_update(msgs, ['internal_id', 'status'])

    batch.internal_id = str(batch.id)
    batch.sent = True
    batch.save()

def check_batch_status(batch):
    msgs = list(batch.textmessage_set.all())
    for m in msgs:
        if m.status == TextMessage.Status.SENT:
            m.status = TextMessage.Status.DELIVERED
    TextMessage.objects.bulk_update(msgs, ['status'])
    batch.save()
