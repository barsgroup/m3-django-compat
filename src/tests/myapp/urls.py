# coding: utf-8
from django.conf.urls import url

from .views import test_view


urlpatterns = [
    url(r'^test/$', test_view),
]
