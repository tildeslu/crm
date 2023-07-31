from django.core.management.base import BaseCommand, CommandError

import argparse
from datetime import datetime, timedelta, time
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
        #parser.add_argument('campaign', nargs=1)
        parser.add_argument('file', type=argparse.FileType('wb'))

    def handle(self, *args, **options):
        xl = Workbook(write_only = True)
        ws = xl.create_sheet()

        ws.append(['Contact', 'Hold', 'Uzer', 'UserDate', 'Uzer', 'UzerDate', 'Uzer', 'UzerDate', 'aUzer', 'Clic6', 'Clic12', 'PayCampaignDate', 'PayN', 'PayDate'])
        for contact in Contact.objects.all():
            # Hold metric
            dead = contact.campaignlead_set.filter(status=CampaignLead.Status.DEAD).count()
            if dead > 0:
                holdMetric = 1
            else:
                holdMetric = ""

            # Campaign metrics
            holdM = 0
            clicM = [0, 0]
            uzerM = []
            auzerM = 0
            payM = []

            # Loop over campaigns
            for lead in contact.campaignlead_set.all():
                holdMetric = ""
                clicMetric = ""
                uzerMetric = ""
                auzerMetric = ""
                payMetric = ""

                if lead.status == CampaignLead.Status.DEAD:
                    holdMetric = "1"
                elif 'last_delivery' in lead.state:
                    if lead.state['last_delivery'] == False:
                        holdMetric = "1"

                try:
                    startOfSendEvent = lead.events.filter(action="init").latest()
                except FunnelEvent.DoesNotExist:
                    startOfSendEvent = None

                try:
                    lastClickedEvent = lead.events.filter(action="follow").latest()
                except FunnelEvent.DoesNotExist:
                    lastClickedEvent = None

                try:
                    lastDeliverEvent = lead.events.filter(action="status", data__status="Delivered").latest()
                except FunnelEvent.DoesNotExist:
                    lastDeliverEvent = None

                try:
                    lastPostbackEvent = lead.events.filter(action="postback").latest()
                except FunnelEvent.DoesNotExist:
                    lastPostbackEvent = None

                nPostbackEvents = lead.events.filter(action="postback").count()

                if startOfSendEvent and lastClickedEvent:
                    if startOfSendEvent.timestamp < lastClickedEvent.timestamp:
                        delta = (lastClickedEvent.timestamp - startOfSendEvent.timestamp).days
                        clicMetric = delta

                if lastDeliverEvent and not lastClickedEvent:
                    uzerMetric = "0"

                if startOfSendEvent and lastClickedEvent:
                    sof = datetime.combine(startOfSendEvent.timestamp.date(), time.min, startOfSendEvent.timestamp.tzinfo)
                    sof = sof + timedelta(days=3)
                    tot = 0
                    ntot = True
                    while sof < lastClickedEvent.timestamp:
                        num = lead.events.filter(action="follow", timestamp__gte=sof, timestamp__lt=sof+timedelta(days=1)).count()
                        sof = sof + timedelta(days=1)
                        if num <= 1:
                            tot  = tot + num
                        else:
                           ntot = False
                    if tot > 0 and ntot:
                        uzerMetric = tot

                if startOfSendEvent and (not lastPostbackEvent or lastPostbackEvent.timestamp < startOfSendEvent.timestamp):
                    num = lead.events.filter(action="follow", timestamp__gt=startOfSendEvent.timestamp).count()
                    if num > 3:
                        auzerMetric = num

                if nPostbackEvents > 0:
                    payMetric = nPostbackEvents #"Pay-({})-({})-({})".format(startOfSendEvent.timestamp.strftime('%Y-%m-%d'), nPostbackEvents, lastPostbackEvent.timestamp.strftime('%Y-%m-%d'))

                sosTime = ""
                if startOfSendEvent:
                    sosTime = startOfSendEvent.timestamp.strftime('%Y-%m-%d')

                lpbTime = ""
                if lastPostbackEvent:
                    lpbTime = lastPostbackEvent.timestamp.strftime('%Y-%m-%d')

                if holdMetric:
                    holdM = 1
                if uzerMetric:
                    uzerM.extend([uzerMetric, sosTime])
                if auzerMetric:
                    if auzerMetric > auzerM:
                        auzerM = auzerMetric
                if clicMetric:
                    if clicMetric < 6:
                        clicM[0] = 1
                        #if clicM[0] < clicMetric:
                        #    clicM[0] = clicMetric
                    elif clicMetric < 12:
                        clicM[1] = 1
                        #if clicM[1] < clicMetric:
                        #    clicM[1] = clicMetric
                if payMetric:
                    payM.extend([sosTime, payMetric, lpbTime])

            if len(uzerM) < 6:
                uzerM.extend([''] * (6 - len(uzerM)))
            elif len(uzerM) > 6:
                for i in range(0, len(uzerM) - 6):
                    uzerM.pop(0)

            if clicM[0] == 0:
                clicM[0] = ""
            if clicM[1] == 0:
                clicM[1] = ""

            if holdM == 0:
                holdM = ""

            if auzerM == 0:
                auzerM = ""

            row = [contact.msisdn, holdM] + uzerM + [auzerM] + clicM + payM
            #print(row)
            ws.append(row)

        options['file'].write(save_virtual_workbook(xl))
