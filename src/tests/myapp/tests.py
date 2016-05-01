# coding: utf-8
from django.test import TestCase

from m3_django_compat import AUTH_USER_MODEL
from m3_django_compat import get_model
from m3_django_compat import get_user_model


class CustomUserModelTestCase(TestCase):

    def test_get_user_model(self):
        u"""Проверка функции get_user_model."""
        user_model = get_model(*AUTH_USER_MODEL.split('.'))
        self.assertIs(user_model, get_user_model())
