from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from .models import UrlMap

from crawlerdetect import CrawlerDetect
from datetime import timedelta
import random

from jigger.events import register_event_response

def get_random(tries=0):
    length = getattr(settings, 'SHORTENER_LENGTH', 5)
    length += tries

    # Removed l, I, 1
    dictionary = "ABCDEFGHJKLMNOPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz234567890"
    return ''.join(random.choice(dictionary) for _ in range(length))


def create(link, producer=None):
    # Use defaults from settings
    lifespan = getattr(settings, 'SHORTENER_LIFESPAN', -1)
    max_uses = getattr(settings, 'SHORTENER_MAX_USES', -1)

    # Expiry date, -1 to disable
    if lifespan != -1:
        expiry_date = timezone.now() + timedelta(seconds=lifespan)
    else:
        expiry_date = timezone.make_aware(timezone.datetime.max, timezone.get_default_timezone())

    # Check if the same url already exists
    for f in UrlMap.objects.filter(full_url=link):
        if f.max_count == max_uses and f.date_expired == expiry_date and f.producer == producer:
            return f.short_url

    # Try up to three times to generate a random number without duplicates.
    # Each time increase the number of allowed characters
    for tries in range(3):
        try:
            short = get_random(tries)
            m = UrlMap(full_url=link, short_url=short, max_count=max_uses, date_expired=expiry_date, producer=producer)
            m.save()
            return m.short_url
        except IntegrityError:
            continue

    raise KeyError("Could not generate unique shortlink")


def shorten_url(link, producer):
    try:
        l = create(link, producer)
    except:
        return None
    #abs_url = getattr(settings, 'SHORTENER_ABSOLUTE_URL', '')
    abs_urls = getattr(settings, 'SHORTENER_ABSOLUTE_URLS', [])
    abs_url = random.choice(abs_urls)
    return f"{abs_url}{l}"



def report_follow(url, full_url, meta):
    data = {}
    data['link'] = url.short_url
    data['template_url'] = url.full_url
    data['full_url'] = full_url

    bot = False
    if meta:
        metadict = { k: str(meta[k]) for k in meta.keys() }
        cd = CrawlerDetect(headers=meta)
        bot = cd.isCrawler()

        if meta.get('REQUEST_METHOD', '') == 'HEAD':
            bot = true

        data['bot'] = bot
        data['meta'] = metadict

    if url.producer:
        register_event_response(url.producer, __name__, "bot_crawl" if bot else "follow", data=data)

def permute_url(url, meta=None):
    url_map = getattr(settings, 'SHORTENER_SITE_MAP', {})
    f = url.full_url
    for k,v in url_map.items():
        if f.startswith(k):
            f = random.choice(v) + f[len(k):]
            break
    return f

def expand(link, meta=None):
    try:
        url = UrlMap.objects.get(short_url__exact=link)
    except UrlMap.DoesNotExist:
        raise KeyError("invalid shortlink")

    # ensure we are within usage counts
    if url.max_count != -1:
        if url.max_count <= url.usage_count:
            raise PermissionError("max usages for link reached")

    # ensure we are within allowed datetime
    # print(timezone.now())
    # print(url.date_expired)
    if timezone.now() > url.date_expired:
        raise PermissionError("shortlink expired")

    url.usage_count += 1
    url.save()

    full_url = permute_url(url, meta)
    report_follow(url, full_url, meta)
    return full_url

