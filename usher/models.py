from django.db import models
from django.conf import settings
from datetime import datetime, timedelta

from jigger.models import FunnelEvent

# Create your models here.
class UrlMap(models.Model):
    full_url = models.TextField()
    short_url = models.CharField(max_length=50, unique=True, db_index=True)
    usage_count = models.IntegerField(default=0)
    max_count = models.IntegerField(default=-1)
    lifespan = models.IntegerField(default=-1)
    date_created = models.DateTimeField(auto_now_add=True)
    date_expired = models.DateTimeField()
    producer = models.ForeignKey(FunnelEvent, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return '{} - {}'.format(self.short_url, self.full_url)
