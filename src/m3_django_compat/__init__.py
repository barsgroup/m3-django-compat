# coding: utf-8
from django import VERSION
from django.conf import settings
from django.db.models.loading import get_model


_VERSION = VERSION[:2]


assert (1, 4) <= _VERSION <= (1, 5)


_14 = _VERSION == (1, 4)
_15 = _VERSION == (1, 5)
# -----------------------------------------------------------------------------
# Модель "Учетная запись"


#: Содержит имя приложения и имя класса модели учетной записи.
#:
#: Строка содержит данные в виде, пригодном для использования при описании
#: внешних ключей (`ForeignKey``, ``OneToOneField`` и т.п.), ссылающихся
#: на модель учетной записи.
#:
#: Для Django 1.4 всегда содержит значение `'auth.User'`, а для более старших
#: версий - значение параметра `AUTH_USER_MODEL` из настроек системы.
#:
#: .. code::
#:
#:    from m3_django_compat import AUTH_USER_MODEL
#:    class Person(models.Model):
#:        user = models.ForeignKey(AUTH_USER_MODEL)
AUTH_USER_MODEL = 'auth.User' if _14 else settings.AUTH_USER_MODEL


def get_user_model():
    u"""Возвращает класс модели учетной записи.

    Для Django 1.4 возвращает :class:`django.contrib.auth.models.User`, а для
    версий 1.5 и старше - результат вызова
    :func:`django.contrib.auth.get_user_model`.
    """
    if _14:
        result = get_model('auth', 'User')
    else:
        from django.contrib.auth import get_user_model
        result = get_user_model()

    return result
# -----------------------------------------------------------------------------
