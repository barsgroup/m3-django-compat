# coding: utf-8
from inspect import isclass
from itertools import chain

from django import VERSION
from django.conf import settings
from django.db import transaction as _transaction
from django.db.models.base import Model
from django.db.models.fields import FieldDoesNotExist
from django.db.models.manager import Manager as _Manager


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


def commit_unless_managed(using=None):
    u"""Совместимый аналог функции commit_unless_managed.

    В Django 1.6+ эта функция была помечена, как устаревшая, а в Django 1.8+
    была удалена.
    """
    if (1, 4) <= _VERSION <= (1, 5):
        from django.db.transaction import commit_unless_managed as func
        return func(using)
# -----------------------------------------------------------------------------
# Обеспечение совместимости менеджеров моделей


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
# Базовый класс для загрузчика шаблонов

if (1, 4) <= _VERSION <= (1, 7):
    from django.template.loader import BaseLoader
else:
    from django.template.loaders.base import Loader as BaseLoader
# -----------------------------------------------------------------------------
# Средства обеспечения совместимости с разными версиями Model API


class RelatedObject(object):

    u"""Зависимый объект."""

    def __init__(self, relation):
        self.relation = relation

    def __repr__(self, *args, **kwargs):
        return 'RelatedObject: ' + repr(self.relation)

    @property
    def model_name(self):
        if (1, 4) <= _VERSION <= (1, 7):
            return self.relation.var_name
        else:
            return self.relation.related_model._meta.model_name


class ModelOptions(object):

    u"""Совместимые параметры модели (``Model._meta``).

    Предоставляет набор методов, которые были доступны в Django<=1.7, а в
    Django>=1.8 были помечены, как устаревшие и будут удалены в Django 2.0.

    .. seealso::

       `Migrating from the old API <https://goo.gl/mzdNSH>`_.
    """

    def __init__(self, model):
        self.model = model if isclass(model) else model.__class__
        self.opts = getattr(model, '_meta', None)
        self.is_django_model = (
            self.opts is None or
            issubclass(self.model, Model)
        )

    def get_field(self, name):
        if not self.is_django_model or (1, 4) <= _VERSION <= (1, 7):
            return self.opts.get_field(name)
        else:
            field = self.opts.get_field(name)

            if (field.auto_created or
                    field.is_relation and field.related_model is None):
                raise FieldDoesNotExist(u"{} has no field named '{}'"
                                        .format(self.model.__name__, name))

            if hasattr(field, 'related'):
                field.related.parent_model = field.related.to

            return field

    def get_field_by_name(self, name):
        if not self.is_django_model or (1, 4) <= _VERSION <= (1, 7):
            return self.opts.get_field_by_name(name)
        else:
            field = self.opts.get_field(name)

            return (
                field,
                field.model,
                not field.auto_created or field.concrete,
                field.many_to_many,
            )

    def get_all_related_objects(self):
        if not self.is_django_model or (1, 4) <= _VERSION <= (1, 7):
            return [
                RelatedObject(relation)
                for relation in self.model._meta.get_all_related_objects()
            ]
        else:
            return [
                RelatedObject(field)
                for field in self.model._meta.get_fields()
                if (
                    (field.one_to_many or field.one_to_one) and
                    field.auto_created
                )
            ]

    def get_m2m_with_model(self):
        if not self.is_django_model or (1, 4) <= _VERSION <= (1, 7):
            return self.opts.get_m2m_with_model()
        else:
            return [
                (
                    field,
                    field.model if field.model != self.model else None
                )
                for field in self.opts.get_fields()
                if field.many_to_many and not field.auto_created
            ]
# -----------------------------------------------------------------------------
# Доступ к HttpRequest.REQUEST


def get_request_params(request):
    u"""Возвращает параметры HTTP-запроса вне зависимости от его типа.

    В Django<=1.8 параметры были доступны в атрибуте ``REQUEST``, но в
    Django>=1.9 этот атрибут был удален (в 1.7 - помечен, как устаревший).
    """
    if (1, 4) <= _VERSION <= (1, 7):
        result = request.REQUEST
    else:
        if request.method == 'GET':
            result = request.GET
        elif request.method == 'POST':
            result = request.POST
        else:
            result = {}

    return result
# -----------------------------------------------------------------------------
