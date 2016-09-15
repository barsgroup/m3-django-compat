# coding: utf-8
from django.http import HttpResponse


def test_view(request):
    return HttpResponse('<html></html>')
