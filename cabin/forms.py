from django.core.exceptions import ValidationError
from django.utils import timezone
from django import forms

from datetime import datetime, timedelta

from jigger.models import Campaign


def get_campaign_choices():
    return [ (x.pk, x.name) for x in Campaign.objects.all() ]

def get_last_campaign():
    return Campaign.objects.latest('pk').pk


def tomorrow():
    td = datetime.now()
    td = td + timedelta(days=1)
    td = td.replace(hour=9, minute=0)
    return td

class EngageForm(forms.Form):

    contacts = forms.FileField()
    campaign = forms.ChoiceField(choices=get_campaign_choices, initial=get_last_campaign)
    start_at = forms.DateTimeField(initial=tomorrow())
    re_init = forms.BooleanField(required=False)

    def clean_start_at(self):
        data = self.cleaned_data['start_at']

        # Check date is not in past.
        if data < timezone.now():
            raise ValidationError('Invalid date - renewal in past')

        # Remember to always return the cleaned data.
        return data

class CeaseForm(forms.Form):

    campaign = forms.ChoiceField(choices=get_campaign_choices, initial=get_last_campaign)

