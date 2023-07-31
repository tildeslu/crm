from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
class ContactTag(models.Model):
    name = models.CharField(max_length=60)
    def __str__(self):
        return self.name

class Contact(models.Model):
    name = models.CharField(max_length=200)
    msisdn = models.CharField(max_length=15)
    tags = models.ManyToManyField(ContactTag, blank=True)
    def __str__(self):
        return self.msisdn

class Campaign(models.Model):
    name = models.CharField(max_length=200)
    contacts = models.ManyToManyField(Contact, through='CampaignLead', blank=True)
    driver = models.CharField(max_length=15)
    settings = models.JSONField(null=True, blank=True)
    ceased = models.BooleanField(default=False)
    def __str__(self):
        return self.name

class CampaignLead(models.Model):
    class Status(models.IntegerChoices):
        NEW = 0, _('New')
        DEAD = 1, _('Dead')
        IN_FUNNEL = 2, _('In Funnel')
        CONVERTED = 3, _('Converted')
        CANCELLED = 4, _('Cancelled')

    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, related_name='leads', on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=0)
    stage = models.CharField(max_length=15, null=True, blank=True)
    state = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)

class FunnelEvent(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=50)
    action = models.CharField(max_length=50)
    data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    seen = models.BooleanField(default=False)
    incoming = models.BooleanField(default=False)
    lead = models.ForeignKey(CampaignLead, related_name='events', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return '[{}] - {}/{}'.format(self.pk, self.source, self.action)

    class Meta:
        get_latest_by = 'timestamp'
        ordering = ['timestamp']
