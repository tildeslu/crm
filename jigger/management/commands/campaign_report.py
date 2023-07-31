from django.core.management.base import BaseCommand, CommandError

import argparse
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from openpyxl import Workbook
from openpyxl.writer.excel import ExcelWriter
import json

from jigger.models import Contact, Campaign, CampaignLead, FunnelEvent


def save_virtual_workbook(workbook):
    """Return an in-memory workbook, suitable for a Django response."""
    temp_buffer = BytesIO()
    try:
        archive = ZipFile(temp_buffer, 'w', ZIP_DEFLATED)
        writer = ExcelWriter(workbook, archive)
        writer.write_data() #archive)
    finally:
        archive.close()
    virtual_workbook = temp_buffer.getvalue() #.getbuffer() #.getvalue()
    temp_buffer.close()
    return virtual_workbook

def do_msgstat(msgs, lead):
    total = 0
    stat = { m:0 for m in msgs }
    for ev in lead.events.filter(source='teaser.tasks', action='status'):
        if ev.data['status'] != 'DELIVERED' or not ev.parent:
            continue
        total = total + 1
        if not 'text_id' in ev.parent.data:
            continue
        m = ev.parent.data['text_id']
        stat[m] = stat.get(m, 0) + 1
    return [ stat[m] for m in msgs ] + [ total ]

def do_lastopened(lead):
    d = None
    try:
        ev = lead.events.filter(source='usher.shortener', action='follow').latest()
        d = ev.timestamp.replace(tzinfo=None)
    except Exception as e:
        pass
    return d


class Command(BaseCommand):
    help = 'Imports contacts to the system adding specified tags'

    def add_arguments(self, parser):
        parser.add_argument('campaign', nargs=1)
        parser.add_argument('file', type=argparse.FileType('wb'))

    def handle(self, *args, **options):
        if 'campaign' not in options:
            raise CommandError('Campaign not specified')

        campaign_name = options['campaign'][0]
        try:
            campaign = Campaign.objects.get(name__exact=campaign_name)
        except ContactTag.DoesNotExist:
            raise CommandError('Campaign "%s" does not exist' % campaign_name)

        cid = campaign.pk
        msgs = sorted(list(campaign.settings['texts'].keys()))

        xl = Workbook(write_only = True)
        ws = xl.create_sheet()

        ws.append(['Contact', 'Contact ID', 'Lead ID', 'Status', 'Stage', 'Tags'] + msgs + ['Total', 'Last OPENED'])
        for lead in CampaignLead.objects.prefetch_related('contact').filter(campaign_id=cid):
            ws.append([lead.contact.msisdn, lead.contact_id, lead.pk, CampaignLead.Status(lead.status).name, lead.stage, 
                ','.join(lead.contact.tags.all().values_list('name', flat=True).order_by('name'))]
                + do_msgstat(msgs, lead) + [ do_lastopened(lead) ])

        options['file'].write(save_virtual_workbook(xl))
