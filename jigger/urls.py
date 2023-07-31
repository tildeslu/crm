from django.conf import settings
from django.urls import path
from . import views

urlpatterns = [
    path('events/<cid>', views.eventlog),
    path('leads/<cid>', views.leadstatus),
    path('lsd2/<cid>', views.leadstatus2),
    path('lsd3/<cid>', views.leadstatus3),
]
