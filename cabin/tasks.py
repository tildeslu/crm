import os

from django.utils import timezone
from datetime import datetime

from background_task import background

from jigger.models import Contact, Campaign, CampaignLead, FunnelEvent

@background(queue='campaign')
def enqueue_enroll(contacts_tmpfile, campaign_id, start_at_iso, reinit_flag):
    try:
        with open(contacts_tmpfile, "r") as cfile:
            contacts = cfile.readlines()
    except FileNotFoundError:
        print("File gone.")
        return

    os.remove(contacts_tmpfile)

    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except:
        print("Campaign does not exist")
        return

    try:
         start_at = datetime.fromisoformat(start_at_iso)
         if not timezone.is_aware(start_at):
             start_at = timezone.make_aware(start_at)
    except:
        print("Bad date format")
        return


    cids = []
    for line in contacts:
        msisdn = line.strip().replace("+","")
        if not msisdn.isdigit():
            continue

        contact = Contact.objects.filter(msisdn__exact=msisdn).first()
        if not contact:
            contact = Contact(msisdn=msisdn, name=f"Auto-import +{msisdn}")
            contact.save()
        cids.append(contact.pk)

    if len(cids) == 0:
        print("No contacts to process.")
        return

    cids_exist = list(CampaignLead.objects.filter(campaign_id=campaign.pk, contact_id__in=cids).values_list('contact_id', flat=True).distinct())
    cids_to_clean = []
    for cid in cids:
        if cid in cids_exist:
            #print("cid={} exists in campaign={}".format(cid, campaign.pk))
            cids_to_clean.append(cid)
            continue
        cl = CampaignLead(contact_id=cid, campaign_id=campaign.pk, status=CampaignLead.Status.NEW, state={'start_at': start_at})
        cl.save()

    if reinit_flag:
        clds = CampaignLead.objects.filter(campaign_id = campaign.pk, contact_id__in = cids_to_clean).values_list('id', flat=True)
        FunnelEvent.objects.filter(lead_id__in = clds, incoming = False, timestamp__gt = timezone.now()).delete()

        CampaignLead.objects.filter(campaign_id = campaign.pk, contact_id__in = cids_to_clean).update(status = CampaignLead.Status.NEW, state = {'start_at': start_at })

    #print(cids)
    #print(campaign)
    #print(start_at)
    #print(reinit_flag)
    print("Campaign programmed.")

