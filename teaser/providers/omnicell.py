from django.conf import settings
from ..models import TextMessage, TextMessageBatch

import random
import requests
import json

from typing import List
from requests.auth import HTTPBasicAuth

OMNICELL_SEND_ENDPOINT = 'https://api.omnicell.com.ua/ip2sms/'
OMNICELL_STATUS_ENDPOINT = 'https://api.omnicell.com.ua/ip2sms-request/'

OMNICELL_USERNAME = getattr(settings, 'OMNICELL_USERNAME', 'tryXXXXXX')
OMNICELL_PASSWORD = getattr(settings, 'OMNICELL_PASSWORD', 'XXXXXXXXX')

OMNICELL_ALPHANAMES = getattr(settings, 'OMNICELL_ALPHANAMES', ['Omni'])

class MessageBody:
    value: str
    def __init__(self, value: str) -> None:
        self.value = value

class MessageTo:
    msisdn: str
    ext_id: int
    validity: str
    tag: str
    body: MessageBody
    def __init__(self, msisdn: str, body: MessageBody) -> None:
        self.msisdn = msisdn
        self.body = body

class IndividualBulkRequest:
    uniq_key: int
    id: str
    source: str
    desc: str
    type: str
    to: List[MessageTo]

    def __init__(self, uniq_key: int, desc: str, service: str, source: str, to: List[MessageTo], type: str = 'SMS') -> None:
        self.uniq_key = uniq_key
        self.id = service
        self.source = source
        self.desc = desc
        self.type = type
        self.to = to

class StatusRequest:
    extended: bool
    groupid: int
    id: int
    value: str

    def __init__(self, id: int, groupid: int, value: str) -> None:
        self.extended = True
        if groupid is not None:
           self.groupid = groupid
        if id is not None:
           self.id = id
        self.value = value



def _send_batch(batchInternalId, alpha, texts):
    rdata = IndividualBulkRequest(batchInternalId, "Batch #" + batchInternalId, 'individual',
        alpha, [ MessageTo(tup[0], MessageBody(tup[1])) for tup in texts ])
    #print(json.dumps(rdata, default=vars, indent=4))
    req = requests.post(OMNICELL_SEND_ENDPOINT, data=json.dumps(rdata, default=vars),
        headers={'Content-Type': 'application/json;charset=UTF-8', 'Accept': 'application/json'},
        auth=HTTPBasicAuth(OMNICELL_USERNAME, OMNICELL_PASSWORD))
    if req.status_code == requests.codes.ok:
        res = req.json()
        #print(json.dumps(res, indent=4))
        if 'error' in res:
            return False
        if 'groupid' in res and 'detail' in res:
            return (res['groupid'], res['detail'])
        else:
            return (None, [res])
    return False

def _batch_status(batchId, messageId=None):
    if batchId:
        rdata = StatusRequest(None, batchId, 'details')
    else:
        rdata = StatusRequest(messageId, None, 'state')
    #print(json.dumps(rdata, default=vars, indent=4))
    req = requests.post(OMNICELL_STATUS_ENDPOINT, data=json.dumps(rdata, default=vars),
        headers={'Content-Type': 'application/json;charset=UTF-8', 'Accept': 'application/json'},
        auth=HTTPBasicAuth(OMNICELL_USERNAME, OMNICELL_PASSWORD))
    if req.status_code == requests.codes.ok:
        res = req.json()
        #print(json.dumps(res, indent=4))
        if 'error' in res:
            return False
        if 'groupid' in res and 'detail' in res:
            return (res['groupid'], res['detail'])
        else:
            return (None, [res])
    return False

StatusMap = {
    "Accepted":  TextMessage.Status.SENT,
    "Enroute":   TextMessage.Status.EN_ROUTE,
    "Delivered": TextMessage.Status.DELIVERED,
    "Expired":   TextMessage.Status.EXPIRED,
    "Deleted":   TextMessage.Status.REJECTED,
    "Rejected":  TextMessage.Status.REJECTED,
    "Undeliverable": TextMessage.Status.REJECTED,
}

def send_batch(batch):
    msgs = list(batch.textmessage_set.all())
    batch.internal_id = str(batch.pk)
    texts = [ (m.recipient, m.text) for m in msgs ]
    alpha = random.choice(OMNICELL_ALPHANAMES)
    res = _send_batch(batch.internal_id, alpha, texts)
    if res:
        mi = iter(msgs)
        for d in res[1]:
            msg = next(mi)
            msg.internal_id = str(d['id'])
            msg.status = TextMessage.Status.SENT
        TextMessage.objects.bulk_update(msgs, ['internal_id', 'status'])

        batch.internal_id = str(res[0]) if res[0] else None
        batch.sent = True
        batch.save()

def check_batch_status(batch):
    if not batch.sent:
        return
    msgs = list(batch.textmessage_set.all())
    mupd = []
    if not batch.internal_id:
        # individual status
        for m in msgs:
            if m.has_terminal_status():
                continue
            b = _batch_status(None, int(m.internal_id))
            if b:
                status = StatusMap.get(b[1][0]['state']['value'], None)
                if status:
                    m.status = status
                    mupd.append(m)
    else:
        b = _batch_status(int(batch.internal_id), None)
        if b:
            for t in b[1]:
                if not 'id' in t:
                    continue
                mid = str(t['id'])
                status = StatusMap.get(t['state']['value'], None)
                m = next((x for x in msgs if x.internal_id == mid), None)
                if m and status:
                    m.status = status
                    mupd.append(m)

    if len(mupd) > 0:
        TextMessage.objects.bulk_update(mupd, ['status'])

    batch.save()

