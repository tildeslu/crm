from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

import argparse
import datetime

from jigger.models import Contact, ContactTag, Campaign, CampaignLead, FunnelEvent

class Command(BaseCommand):
    help = 'Imports contacts to the system adding specified tags'

    def add_arguments(self, parser):
        parser.add_argument('--tag', action='append', nargs=1, default=[])
        parser.add_argument('--reinit', action='store_true')
        parser.add_argument('--start', type=datetime.date.fromisoformat)
        parser.add_argument('campaign', nargs=1)

    def handle(self, *args, **options):
        tags = []
        for tag_name in options['tag']:
            tag_name = tag_name[0]
            try:
                tag = ContactTag.objects.get(name__exact=tag_name)
            except ContactTag.DoesNotExist:
                raise CommandError('Tag "%s" does not exist' % tag_name)

            tags.append(tag)

        if len(tags) == 0:
            raise CommandError('No tags specified')

        if 'campaign' not in options:
            raise CommandError('Campaign not specified')


        campaign_name = options['campaign'][0]
        try:
            campaign = Campaign.objects.get(name__exact=campaign_name)
        except ContactTag.DoesNotExist:
            raise CommandError('Campaign "%s" does not exist' % campaign_name)

        for t in tags:
            self.stdout.write("Processing tag [{}]".format(t.name))
            contacts = t.contact_set.all()
            campaign.contacts.add(*contacts)

            if options['reinit']:
                self.stdout.write("Re-init...")
                cids = t.contact_set.values_list('id', flat=True)
                CampaignLead.objects.filter(campaign_id = campaign.pk, contact_id__in = cids).update(status = CampaignLead.Status.NEW)
                clds = CampaignLead.objects.filter(campaign_id = campaign.pk, contact_id__in = cids).values_list('id', flat=True)
                FunnelEvent.objects.filter(lead_id__in = clds, incoming = False, timestamp__gt = timezone.now()).delete()

        self.stdout.write(self.style.SUCCESS('Successful'))
