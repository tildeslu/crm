from django.conf import settings
from django.urls import path
from . import views

urlpatterns = [
    path('engage', views.engage),
    path('cease', views.cease),
]

