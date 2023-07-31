from django.utils import timezone
from datetime import datetime, timedelta
import random
from pprint import pprint

from ..models import Campaign, CampaignLead, FunnelEvent
from ..utils import substitute_and_shorten, enqueue_text_message

class Stage:
    NEW = 'NEW'
    COLD = 'COLD'
    OPENED = 'OPENED'
    PAID = 'PAID'

class Action:
    INITIATE = 'init'
    SEND_TEXT = 'send_sms'

class Source:
    SELF = __name__
    SMS_AGENT = 'teaser.tasks'
    SHORTENER = 'usher.shortener'
    POSTBACKS = 'hooker.views'

def enter_funnel(settings, lead):
    # make initial event
    event = lead.events.create(source=Source.SELF,action=Action.INITIATE)
    # enter funnel
    lead.stage = Stage.NEW
    lead.status = CampaignLead.Status.IN_FUNNEL
    lead.save()

def enter_stage(lead, stage, parent=None, start_at=None):
    lead.stage = stage
    sl = stage.lower()

    times = lead.state.get(f"{sl}_times", None)
    if not times:
        return

    msgs = lead.state.get(f"{sl}_texts", None)
    if not msgs:
        msgs = lead.state.texts.keys()
    if len(msgs) == 0:
        return

    if not start_at:
        start_at = timezone.now()

    for t in times:
        ts = start_at + timedelta(seconds=t)
        lead.events.create(source=Source.SELF, action=Action.SEND_TEXT, parent=parent, timestamp=ts, data={"texts":msgs})

def check_today(lead):
    today = timezone.now().date().isoformat()
    if lead.state.get('today', None) != today:
        lead.state['today'] = today
        lead.state['seen_today'] = []
        lead.state['sent_today'] = 0
        if 'last_delivery' in lead.state:
            del(lead.state['last_delivery'])

def handle_initiate(settings, lead, event, ceased):
    # parse start_at
    start_at = lead.state.get("start_at", None)
    if start_at:
        start_at = datetime.fromisoformat(start_at)

    # generate personalized messages
    ctx = {
        'lead_id': lead.id,
        'campaign_id': lead.campaign_id,
    }
    msgs = {k: substitute_and_shorten(v, ctx, event) for k,v in settings['texts'].items()}
    lead.state = {
        'texts': msgs,
        'today': timezone.now().date(),
        'seen_today': [],
        'sent_today': 0,
        'daily_limit': settings['daily_limit'],
        'cold_texts': settings['cold_texts'],
        'cold_times': settings['cold_times'],
        'opened_texts': settings['opened_texts'],
        'opened_times': settings['opened_times'],
    }

    enter_stage(lead, Stage.COLD, event, start_at)
    lead.save()
    return True

def handle_send_text(settings, lead, event, ceased):
    check_today(lead)
    # do not send if last not delivered
    if not lead.state.get('last_delivery', True):
        return True
    # do not send if ceased
    if ceased:
        return True
    # if hit daily limit
    if lead.state['sent_today'] >= lead.state['daily_limit']:
        return True
    # select what to send
    texts = [ m for m in event.data['texts'] if not m in lead.state['seen_today'] ]
    # do not send if nothing to send
    if len(texts) == 0:
        return True
    # send and register
    msg_id = random.choice(texts)
    msg = lead.state['texts'][msg_id]

    enqueue_text_message(lead, msg, event)
    print(f">>> TEXT TO: +{lead.contact.msisdn}")
    print(f"    MESSAGE: {msg}")
    event.data['text_sent'] = msg
    event.data['text_id'] = msg_id
    event.save()

    lead.state['seen_today'].append(msg_id)
    lead.state['sent_today'] = lead.state['sent_today'] + 1
    lead.state['last_delivery'] = False

    lead.save()
    return True

def handle_text_status(settings, lead, event, ceased):
    status = event.data['status']
    if status == 'DELIVERED':
        lead.state['last_delivery'] = True
    elif status == 'REJECTED':
        lead.state['last_delivery'] = False
        lead.status = CampaignLead.Status.DEAD
    elif status == 'EXPIRED':
        lead.state['last_delivery'] = False
    lead.save()
    return True

def handle_url_follow(settings, lead, event, ceased):
    if lead.stage in [Stage.COLD, Stage.OPENED]:
        # hotfix:
        #try:
        #    if event.data['meta']['REQUEST_METHOD'] == 'HEAD':
        #        return True
        #except:
        #    pass
        # if no more planned messages
        if lead.events.filter(timestamp__gt=event.timestamp, source=Source.SELF, action=Action.SEND_TEXT).count() == 0:
            enter_stage(lead, Stage.OPENED, event)
            lead.save()
        else:
            if lead.stage != Stage.OPENED:
                lead.stage = Stage.OPENED
                lead.save()
    return True

def handle_postback(settings, lead, event, ceased):
    if event.data['source'] == 'salesdoubler':
        if event.data['status'] == 'paid':
            lead.stage = Stage.PAID
            lead.status = CampaignLead.Status.CONVERTED
            lead.events.filter(timestamp__gt=event.timestamp, source=Source.SELF, action=Action.SEND_TEXT, seen=False).delete()
            lead.save()
            print(f">>> CONVERTED: +{lead.contact.msisdn}")
    return True

def handle_ignore(settings, lead, event, ceased):
    return True

DISPATCH_TABLE = {
    Source.SELF: {
        Action.INITIATE: handle_initiate,
        Action.SEND_TEXT: handle_send_text,
    },
    Source.SMS_AGENT: {
        'status': handle_text_status,
    },
    Source.SHORTENER: {
        'follow': handle_url_follow,
        '*': handle_ignore,
    },
    Source.POSTBACKS: {
        'postback': handle_postback,
    },
}

def process_event(settings, lead, event, ceased):
    print(f">>> EVENT #{event.pk} FOR: +{lead.contact.msisdn}: {event.source}/{event.action}")
    print(f" Time: {event.timestamp}")
    pprint(event.data)

    # silently consume all events
    if lead.status == CampaignLead.Status.DEAD:
        event.seen = True
        return True

    handler = None
    if event.source in DISPATCH_TABLE:
        if event.action in DISPATCH_TABLE[event.source]:
            handler = DISPATCH_TABLE[event.source][event.action]
        elif '*' in DISPATCH_TABLE[event.source]:  # default handler
            handler = DISPATCH_TABLE[event.source]['*']
    if handler:
        event.seen = handler(settings, lead, event, ceased)

# UNUSED
def leave_funnel(settings, lead):
    pass
