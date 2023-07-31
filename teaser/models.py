from django.db import models
from django.utils.translation import gettext_lazy as _

from jigger.models import FunnelEvent

# Create your models here.
class TextMessageBatch(models.Model):
    class Meta:
        verbose_name_plural = 'text message batches'
    timestamp = models.DateTimeField(auto_now=True)
    provider =  models.CharField(max_length=15)
    internal_id = models.CharField(max_length=30, null=True, blank=True)
    sent = models.BooleanField(default=False)
    finalized = models.BooleanField(default=False)

    def __str__(self):
        return '{} - {}[{}]'.format(self.id, self.provider, self.internal_id)

class TextMessage(models.Model):
    class Status(models.IntegerChoices):
        NEW = 0, _('New')
        SENT = 1, _('Sent')
        EN_ROUTE = 2, _('En Route')
        DELIVERED = 3, _('Delivered')
        EXPIRED = 4, _('Expired')
        REJECTED = 5, _('Rejected')

    timestamp = models.DateTimeField(auto_now_add=True)
    recipient = models.CharField(max_length=15, null=True)
    text = models.CharField(max_length=1000)
    internal_id = models.CharField(max_length=30, null=True, blank=True)
    batch = models.ForeignKey(TextMessageBatch, on_delete=models.CASCADE, null=True, blank=True)
    status = models.IntegerField(choices=Status.choices, default=0)
    producer = models.ForeignKey(FunnelEvent, on_delete=models.SET_NULL, null=True, blank=True)
    notified = models.BooleanField(default=False)

    @staticmethod
    def terminal_status_list():
        return [TextMessage.Status.DELIVERED, TextMessage.Status.EXPIRED, TextMessage.Status.REJECTED]

    @staticmethod
    def nonterminal_status_list():
        return [TextMessage.Status.NEW, TextMessage.Status.SENT, TextMessage.Status.EN_ROUTE]

    def has_terminal_status(self):
        if self.status in TextMessage.terminal_status_list():
            return True
        return False

    def __str__(self):
        return '[{}] {} - {}'.format(self.internal_id, self.recipient, self.text)

