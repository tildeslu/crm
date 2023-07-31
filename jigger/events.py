from .models import Contact, ContactTag, Campaign, CampaignLead, FunnelEvent

def register_event_response(parent, source, action, data=None, incoming=True):
    f = FunnelEvent(parent=parent, lead=parent.lead, incoming=incoming, source=source, action=action, data=data)
    f.save()

def register_event(lead, source, action, data=None, incoming=True):
    f = FunnelEvent(lead=lead, incoming=incoming, source=source, action=action, data=data)
    f.save()
