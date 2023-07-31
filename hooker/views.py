from django.http import HttpResponse
from jigger.models import CampaignLead
from jigger.events import register_event

def postback(request, source):
    data = {"source": source}
    for p,v in request.GET.items():
        data[p] = v
    print(data)
    try:
        lead_id = int(request.GET['lid'])
        lead = CampaignLead.objects.get(pk=lead_id)
        register_event(lead, __name__, 'postback', data)
    except:
        pass
    return HttpResponse('')
