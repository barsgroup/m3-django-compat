# coding: utf-8
from django import VERSION
from django.conf import settings
from django.db import transaction as _transaction


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
# Транзакции


def in_atomic_block(using=None):
    u"""Возвращает ``True``, если в момент вызова открыта транзакция.

    Если включен режим автоподтверждения (autocommit), то возвращает ``False``.

    :param str using: Алиас базы данных.

    :rtype: bool
    """
    if (1, 4) <= _VERSION <= (1, 5):
        result = _transaction.is_managed(using)
    else:
        result = _transaction.get_connection(using).in_atomic_block

    return result


if (1, 4) <= _VERSION <= (1, 5):
    class _Atomic(object):

        def __init__(self, savepoint):
            self._savepoint = savepoint
            self._sid = None

        def entering(self, using):
            if in_atomic_block(using):
                if self._savepoint:
                    self._sid = _transaction.savepoint(using)
            else:
                self._commit_on_exit = True

                _transaction.enter_transaction_management(using=using)
                _transaction.managed(True, using=using)

        def exiting(self, exc_value, using):
            if self._sid:
                if self._savepoint:
                    if exc_value is None:
                        _transaction.savepoint_commit(self._sid, using)
                    else:
                        _transaction.savepoint_rollback(self._sid, using)
            else:
                try:
                    if exc_value is not None:
                        if _transaction.is_dirty(using=using):
                            _transaction.rollback(using=using)
                    else:
                        if _transaction.is_dirty(using=using):
                            try:
                                _transaction.commit(using=using)
                            except:
                                _transaction.rollback(using=using)
                                raise
                finally:
                    _transaction.leave_transaction_management(using=using)


def atomic(using=None, savepoint=True):
    u"""Совместимый аналог декоратора/менеджера контекста ``atomic``.

    В Django>=1.6 задействует функционал ``atomic``, а в версиях ниже 1.6
    имитирует его поведение средствами модуля ``django.db.transaction``, при
    этом, в отличие от ``commit_on_success`` из Django<1.6, поддерживает
    вложенность.

    :param str using: Алиас базы данных. Если указано значение ``None``, будет
        использован алиас базы данных по умолчанию.
    :param bool savepoint: Определяет, будут ли использоваться точки сохранения
        (savepoints) при использовании вложенных ``atomic``.
    """
    if (1, 4) <= _VERSION <= (1, 5):
        if callable(using):
            # atomic вызван как декоратор без параметров
            from django.db.utils import DEFAULT_DB_ALIAS
            func = using
            using = DEFAULT_DB_ALIAS
        else:
            func = None

        atomic = _Atomic(savepoint)
        result = _transaction._transaction_func(
            atomic.entering, atomic.exiting, using
        )

        if func:
            result = result(func)
    else:
        result = _transaction.atomic(using, savepoint)

    return result
# -----------------------------------------------------------------------------
# Обеспечение совместимости менеджеров моделей


from django.db.models.manager import Manager as _Manager


class Manager(_Manager):

    u"""Базовый класс для менеджеров моделей.

    Создан в связи с переименованием в Django 1.6 метода ``get_query_set`` в
    ``get_queryset`` и ``get_prefetch_query_set`` в ``get_prefetch_queryset``.

    "Пробрасывает" вызовы этих методов к методам
    :class:`django.db.models.manager.Manager`, соответствующим используемой
    версии Django.

    Предназначен для использования в качестве базового класса вместо
    :class:`django.db.models.manager.Manager`.
    """

    def __get_queryset_method(self):
        if (1, 4) <= _VERSION <= (1, 5):
            result = super(Manager, self).get_query_set
        else:
            result = super(Manager, self).get_queryset

        return result

    @property
    def get_queryset(self):
        return self.__get_queryset_method()

    @property
    def get_query_set(self):
        return self.__get_queryset_method()

    def __get_prefetch_queryset_method(self):
        if (1, 4) <= _VERSION <= (1, 5):
            result = super(Manager, self).get_prefetch_query_set
        else:
            result = super(Manager, self).get_prefetch_queryset

        return result

    @property
    def get_prefetch_queryset(self):
        return self.__get_prefetch_queryset_method()

    @property
    def get_prefetch_query_set(self):
        return self.__get_prefetch_queryset_method()
# -----------------------------------------------------------------------------
