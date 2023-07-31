from django.template import Context, Template

from teaser.models import TextMessage

from usher.shortener import shorten_url

import re
url_regex = re.compile('((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)', re.DOTALL)

def apply_substitutions(text, context):
    context = Context(context)
    template = Template(text)
    return template.render(context)

def shorten_urls(text, event=None):
    links = re.findall(url_regex, text)
    for l in links:
        url = l[0]
        short_url = shorten_url(url, event)
        if short_url:
            text = text.replace(url, short_url)
    return text

def substitute_and_shorten(text, context, event=None):
    return shorten_urls(apply_substitutions(text, context), event)


def enqueue_text_message(lead, text, event=None):
    msg = TextMessage(recipient=lead.contact.msisdn, text=text, producer=event)
    msg.save()

