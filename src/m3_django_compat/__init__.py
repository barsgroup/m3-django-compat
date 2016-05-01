# coding: utf-8
from django import VERSION
from django.conf import settings


_VERSION = VERSION[:2]
_14 = _VERSION == (1, 4)


#: Минимальная подерживаемая версия Django.
MIN_SUPPORTED_VERSION = (1, 4)


#: Максимальная поддерживаемая версия Django.
MAX_SUPPORTED_VERSION = (1, 9)


assert MIN_SUPPORTED_VERSION <= _VERSION <= MAX_SUPPORTED_VERSION, (
    'Unsupported Django version: {}.{}'.format(*_VERSION)
)
# -----------------------------------------------------------------------------
# Загрузка модели


def get_model(app_label, model_name):
    u"""Возвращает класс модели.

    :param str app_label: Имя приложения модели.
    :param str model_name: Имя модели (без учета регистра символов).

    :rtype: :class:`django.db.models.base.ModelBase`
    """
    if (1, 4) <= _VERSION <= (1, 6):
        from django.db.models.loading import get_model
        result = get_model(app_label, model_name)
    elif (1, 7) <= _VERSION <= (1, 9):
        from django.apps import apps
        result = apps.get_model(app_label, model_name)
    else:
        raise

    return result
# -----------------------------------------------------------------------------
# Модель "Учетная запись"


#: Содержит имя приложения и имя класса модели учетной записи.
#:
#: Строка содержит данные в виде, пригодном для использования при описании
#: внешних ключей (``ForeignKey``, ``OneToOneField`` и т.п.), ссылающихся
#: на модель учетной записи.
#:
#: Если подключено приложение ``'django.contrib.auth'``, то для Django 1.4
#: всегда содержит значение ``'auth.User'``, а для более старших версий --
#: значение параметра ``AUTH_USER_MODEL`` из настроек системы. Если же
#: приложение ``'django.contrib.auth'`` не подключено, содержит ``None``.
#:
#: .. code::
#:
#:    from m3_django_compat import AUTH_USER_MODEL
#:
#:    class Person(models.Model):
#:        user = models.ForeignKey(AUTH_USER_MODEL)
AUTH_USER_MODEL = None
if 'django.contrib.auth' in settings.INSTALLED_APPS:
    AUTH_USER_MODEL = 'auth.User' if _14 else settings.AUTH_USER_MODEL


def get_user_model():
    u"""Возвращает класс модели учетной записи.

    Если подключено приложение ``'django.contrib.auth'``, то для Django 1.4
    возвращает :class:`django.contrib.auth.models.User`, а для
    версий 1.5 и старше - результат вызова
    :func:`django.contrib.auth.get_user_model`.

    :rtype: :class:`django.db.models.base.ModelBase` or :class:`NoneType`
    """
    if 'django.contrib.auth' not in settings.INSTALLED_APPS:
        result = None
    elif _14:
        result = get_model('auth', 'User')
    else:
        from django.contrib.auth import get_user_model
        result = get_user_model()

    return result
# -----------------------------------------------------------------------------
