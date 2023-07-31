from django.conf import settings
from django.utils import timezone
from importlib import import_module

from background_task import background

from .models import Campaign, CampaignLead, FunnelEvent

EVENT_CHECK_SIZE = getattr(settings, 'EVENT_CHECK_SIZE', 1000)
EVENT_CHECK_CYCLES = getattr(settings, 'EVENT_CHECK_CYCLES', 100)

def load_driver(campaign):
    root = __name__.rsplit('.', 1)[0]
    return import_module(f"{root}.drivers.{campaign.driver}")

@background(remove_existing_tasks=True, queue='campaign')
def start_funnels():
    # get all new leads
    leads = list(CampaignLead.objects.filter(status=CampaignLead.Status.NEW).order_by('campaign_id')[:EVENT_CHECK_SIZE])
    cid = -1
    for l in leads:
        if cid != l.campaign_id:
            campaign = l.campaign
            cid = l.campaign_id
            campmod = None
            try:
                campmod = load_driver(campaign)
            except:
                pass
        if campmod:
            campmod.enter_funnel(campaign.settings, l)

@background(remove_existing_tasks=True, queue='campaign')
def process_events():
    # get all past events
    now = timezone.now()
    cycles = EVENT_CHECK_CYCLES

    while cycles > 0:
        cycles = cycles - 1
        events = list(FunnelEvent.objects.filter(timestamp__lte=now, seen=False).select_related('lead')[:EVENT_CHECK_SIZE])
        # shortcut
        if len(events) == 0:
            break
        # filter a single event per lead and group by campaign
        per_lead=dict()
        per_camp=dict()
        for e in events:
            if not e.lead_id in per_lead:
                per_lead[e.lead_id] = e
                if e.lead.campaign_id in per_camp:
                    per_camp[e.lead.campaign_id].append(e)
                else:
                    per_camp[e.lead.campaign_id] = [e]
        events = per_lead.values()
        # run handlers per-campaign
        for cid, evts in per_camp.items():
            campmod = None
            try:
                campaign = Campaign.objects.get(pk=cid)
                campmod = load_driver(campaign)
            except:
                raise
            if campmod:
                for e in evts:
                    campmod.process_event(campaign.settings, e.lead, e, campaign.ceased)
        # mass save seen flag
        FunnelEvent.objects.bulk_update(events, ['seen'])
