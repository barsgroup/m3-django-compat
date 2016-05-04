# coding: utf-8
from django.db import models

from m3_django_compat import Manager


class OldManager(Manager):

    def get_query_set(self):
        return super(OldManager, self).get_query_set()

    def positive(self):
        return self.get_query_set().filter(number__gt=0)

    def negative(self):
        return self.get_query_set().filter(number__lt=0)


class NewManager(Manager):

    def get_queryset(self):
        return super(NewManager, self).get_queryset()

    def positive(self):
        return self.get_queryset().filter(number__gt=0)

    def negative(self):
        return self.get_queryset().filter(number__lt=0)


class ModelWithCustomManager(models.Model):

    u"""Модель с переопределенным менеджером, поддерживающим совместимость."""

    number = models.IntegerField()

    objects = models.Manager()
    old_manager = OldManager()
    new_manager = NewManager()
