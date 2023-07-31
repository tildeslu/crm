from django.shortcuts import redirect
from django.http import HttpResponse
from . import shortener

def expand(request, link):
    try:
        link = shortener.expand(link, request.META)
        return redirect(link)  # TODO: permanent=True
    except Exception as e:
        return HttpResponse(e.args)
