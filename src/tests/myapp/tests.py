# coding: utf-8
from StringIO import StringIO
from warnings import catch_warnings
import atexit
import json
import os.path
import subprocess
import sys

from django.core.management import load_command_class, call_command
from django.db import models
from django.db.models.query import QuerySet
from django.db.utils import DEFAULT_DB_ALIAS
from django.test import Client
from django.test import SimpleTestCase
from django.test import TestCase

from m3_django_compat import AUTH_USER_MODEL
from m3_django_compat import DatabaseRouterBase
from m3_django_compat import ModelOptions
from m3_django_compat import RelatedObject
from m3_django_compat import _VERSION
from m3_django_compat import atomic
from m3_django_compat import get_model
from m3_django_compat import get_related
from m3_django_compat import get_user_model
from m3_django_compat import in_atomic_block


# -----------------------------------------------------------------------------
# Проверка работы с моделью учетной записи
class CustomUserModelTestCase(TestCase):

    def test_get_user_model(self):
        u"""Проверка функции get_user_model."""
        user_model = get_model(*AUTH_USER_MODEL.split('.'))
        self.assertIs(user_model, get_user_model())
# -----------------------------------------------------------------------------
# Проверка работы с транзакциями


class AtomicTestCase(SimpleTestCase):

    allow_database_queries = True

    @classmethod
    def tearDownClass(cls):
        get_user_model().objects.all().delete()

        super(AtomicTestCase, cls).tearDownClass()

    def _create_user(self, username):
        user = get_user_model()(username=username)
        user.set_unusable_password()
        user.save()

    def _is_user_exist(self, username):
        return get_user_model().objects.filter(username=username).exists()

    @atomic
    def _simple_success(self):
        self.assertTrue(in_atomic_block())
        self._create_user('user1')

    @atomic
    def _simple_failure(self):
        self._create_user('user2')
        raise ValueError('error1')

    @atomic
    def _inner_success(self):
        self.assertTrue(in_atomic_block())
        self._create_user('user4')

    @atomic
    def _outer_success(self):
        self.assertTrue(in_atomic_block())
        self._create_user('user3')
        self.assertTrue(in_atomic_block())
        self._inner_success()
        self.assertTrue(in_atomic_block())

    @atomic
    def _inner_failure(self):
        self.assertTrue(in_atomic_block())
        self._create_user('user6')

    @atomic
    def _outer_failure(self):
        self.assertTrue(in_atomic_block())
        self._create_user('user5')
        self.assertTrue(in_atomic_block())
        self._inner_failure()
        self.assertTrue(in_atomic_block())
        raise ValueError('error2')

    def test_atomic(self):
        u"""Проверка atomic."""
        self.assertFalse(in_atomic_block())
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Подтверждение транзакции без вложенных atomic-ов
        self._simple_success()
        self.assertTrue(self._is_user_exist('user1'))
        self.assertFalse(in_atomic_block())
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Откат транзакции без вложенных atomic-ов
        try:
            self._simple_failure()
        except ValueError as error:
            self.assertRaisesMessage(error, 'error2')
        self.assertFalse(self._is_user_exist('user2'))
        self.assertFalse(in_atomic_block())
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Подтверждение транзакции с вложенными atomic-ами
        self._outer_success()
        self.assertTrue(self._is_user_exist('user3'))
        self.assertTrue(self._is_user_exist('user4'))
        self.assertFalse(in_atomic_block())
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Откат транзакции с вложенными atomic-ами
        try:
            self._outer_failure()
        except ValueError as error:
            self.assertRaisesMessage(error, 'error2')
        self.assertFalse(self._is_user_exist('user5'))
        self.assertFalse(self._is_user_exist('user6'))
        self.assertFalse(in_atomic_block())
# -----------------------------------------------------------------------------
# Проверка обеспечения совместимости менеджеров моделей


class ManagerTestCase(TestCase):

    def test_manager_compat(self):
        u"""Проверка совместимости менеджеров моделей."""
        model = get_model('myapp', 'ModelWithCustomManager')
        self.assertIsNotNone(model)

        for i in xrange(-5, 6):
            model.objects.create(number=i)

        self.assertIsInstance(model.new_manager.get_query_set(), QuerySet)
        self.assertIsInstance(model.new_manager.get_queryset(), QuerySet)
        self.assertIsInstance(model.old_manager.get_query_set(), QuerySet)
        self.assertIsInstance(model.old_manager.get_queryset(), QuerySet)

        self.assertEqual(model.objects.count(), model.old_manager.count())
        self.assertEqual(model.objects.count(), model.new_manager.count())

        with self.assertNumQueries(1), catch_warnings('ignore'):
            self.assertTrue(
                all(obj.number > 0 for obj in model.old_manager.positive())
            )
        with self.assertNumQueries(1), catch_warnings('ignore'):
            self.assertTrue(
                all(obj.number < 0 for obj in model.old_manager.negative())
            )

        with self.assertNumQueries(1):
            self.assertTrue(
                all(obj.number > 0 for obj in model.new_manager.positive())
            )
        with self.assertNumQueries(1):
            self.assertTrue(
                all(obj.number < 0 for obj in model.new_manager.negative())
            )
# -----------------------------------------------------------------------------
# Проверка корректности обеспечения совместимости для Model API


class ModelOptionsTestCase(TestCase):

    def test__get_field__method(self):
        data = (
            dict(
                model=get_model('myapp', 'Model1'),
                fields=(
                    ('simple_field', models.CharField),
                ),
            ),
            dict(
                model=get_model('myapp', 'Model2'),
                fields=(
                    ('simple_field', models.CharField),
                ),
            ),
            dict(
                model=get_model('myapp', 'Model3'),
                fields=(
                    ('simple_field', models.CharField),
                    ('m2m_field', models.ManyToManyField),
                ),
            ),
        )

        for test_data in data:
            model, fields = test_data['model'], test_data['fields']
            opts = ModelOptions(model)

            for field_name, field_type in fields:
                self.assertIsInstance(opts.get_field(field_name), field_type)

                f, _, _, _ = opts.get_field_by_name(field_name)
                self.assertIsInstance(f, field_type, field_type)
        # ---------------------------------------------------------------------

        opts = ModelOptions(get_model('myapp', 'Model2'))
        field = opts.get_field('fk_field')
        related = get_related(field)
        self.assertIsNotNone(related)
        self.assertIs(related.parent_model, get_model('myapp', 'Model1'))

    def test__get_m2m_with_model__method(self):
        data = (
            dict(
                model=get_model('myapp', 'Model3'),
                m2m_fields=('m2m_field',),
            ),
        )

        for test_data in data:
            model = test_data['model']
            m2m_fields = test_data['m2m_fields']
            opts = ModelOptions(model)

            for f, _ in opts.get_m2m_with_model():
                self.assertIsInstance(f, models.ManyToManyField)
                self.assertIn(f.name, m2m_fields)
                self.assertIs(f, model._meta.get_field(f.name))

    def test__get_all_related_objects__method(self):
        data = (
            dict(
                model=get_model('myapp', 'Model1'),
                field_names=('model2',),
            ),
            dict(
                model=get_model('myapp', 'Model2'),
                field_names=(),
            ),
            dict(
                model=get_model('myapp', 'Model3'),
                field_names=(),
            ),
        )

        for test_data in data:
            model = test_data['model']
            field_names = test_data['field_names']
            opts = ModelOptions(model)

            related_objects = opts.get_all_related_objects()
            self.assertEqual(
                len(related_objects), len(field_names),
                (model, related_objects, field_names)
            )
            self.assertEqual(
                set(field_names),
                set(related_object.model_name
                    for related_object in related_objects),
                (model, related_objects, field_names)
            )
            self.assertTrue(all(
                isinstance(ro, RelatedObject)
                for ro in related_objects
            ))
# -----------------------------------------------------------------------------
# Проверка базового класса для роутеров баз данных


class TestRouter(DatabaseRouterBase):

    def _allow(self, db, app_label, model_name):
        return (
            db == DEFAULT_DB_ALIAS and
            get_model(app_label, model_name) is get_user_model()
        )


class DatabaseRouterTestCase(TestCase):

    def test_database_router(self):
        router = TestRouter()

        if _VERSION <= (1, 6):
            self.assertTrue(
                router.allow_syncdb(DEFAULT_DB_ALIAS, get_user_model())
            )
        elif _VERSION == (1, 7):
            self.assertTrue(
                router.allow_migrate(DEFAULT_DB_ALIAS, get_user_model())
            )
        else:
            self.assertTrue(
                router.allow_migrate(DEFAULT_DB_ALIAS, 'user', 'CustomUser')
            )
# -----------------------------------------------------------------------------


class GetTemplateTestCase(TestCase):

    def test__get_template__function(self):
        u"""Проверка правильности работы функции get_template."""
        from django.http import HttpRequest
        from django.template.context import RequestContext
        from m3_django_compat import get_template

        request = HttpRequest()
        request.user = get_user_model()(username='testuser')
        context = RequestContext(request, {'var': 'value'})

        template = get_template('get_template.html')

        self.assertEquals(
            template.render(context),
            '<p>value</p><p>testuser</p>'
        )
# -----------------------------------------------------------------------------


class TestUrlPatterns(SimpleTestCase):

    u"""Проверка работоспособности описания совместимых urlpatterns."""

    def test__urlpatterns(self):
        client = Client()
        response = client.get('/test/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '<html></html>')
# -----------------------------------------------------------------------------


class _StreamReplacer(object):

    # Нужен в связи с тем, что в Django 1.4 еще не было возможности
    # использовать альтернативный поток вывода.

    def __init__(self, stdout, stderr):
        self._stdout = stdout
        self._stderr = stderr

    def __enter__(self):
        sys.stdout, self._sys_stdout = self._stdout, sys.stdout
        sys.stderr, self._sys_stderr = self._stderr, sys.stderr

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._sys_stdout
        sys.stderr = self._sys_stderr


class _ExitHandler(object):

    # Подключает и отключает обработчик выхода из системы. Нужен в связи с
    # отсутствием atexit.unregister в Python 2.

    def __init__(self, handler, *args, **kwargs):
        self.__handler = handler
        self.__args = args
        self.__kwargs = kwargs

    def __enter__(self):
        atexit.register(self.__handler, *self.__args, **self.__kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(atexit, 'unregister'):
            atexit.unregister(self.__handler)
        else:
            index = None
            for i, (handler, _, _) in enumerate(atexit._exithandlers):
                if handler is self.__handler:
                    index = i
                    break
            if index is None:
                raise ValueError(self.__handler)
            else:
                atexit._exithandlers.pop(index)


class BaseCommandTestCase(SimpleTestCase):

    u"""Проверка базового класса для management-команд."""

    def __exit_handler(self):
        if self.__stdout and self.__stderr:
            print self.__stdout.getvalue()
            print self.__stderr.getvalue()

    def setUp(self):
        self.__stdout = StringIO()
        self.__stderr = StringIO()

    def tearDown(self):
        self.__stdout.close()
        self.__stdout = None

        self.__stderr.close()
        self.__stderr = None

    def __check_result(self, output, errors):
        self.assertFalse(errors)

        args, kwargs = map(json.loads, output.split('\n')[:2])

        self.assertEqual(args, ['asd', '1'])

        for arg in ('verbosity', 'traceback', 'settings', 'pythonpath',
                    'test1', 'test2', 'test3'):
            self.assertIn(arg, kwargs)
        self.assertEqual(kwargs['verbosity'], 0)
        self.assertEqual(kwargs['traceback'], True)
        self.assertEqual(kwargs['test1'], 'qwe')
        self.assertTrue(kwargs['test2'])
        self.assertEqual(kwargs['test3'], 1)

    def test__run_from_argv(self):
        with _StreamReplacer(self.__stdout, self.__stderr):
            command = load_command_class('myapp', 'test_command')

            with _ExitHandler(self.__exit_handler):
                command.run_from_argv([
                    'python', 'test_command',
                    '-v', '0',
                    '--traceback',
                    '--test1', 'qwe',
                    '--test2',
                    '--test3', '1',
                    'asd', '1',
                ])

        self.__check_result(self.__stdout.getvalue(), self.__stderr.getvalue())

    def test__call_command(self):
        with _StreamReplacer(self.__stdout, self.__stderr):
            with _ExitHandler(self.__exit_handler):
                call_command(
                    'test_command',
                    'asd', '1',
                    verbosity=0,
                    traceback=True,
                    test1='qwe',
                    test2=True,
                    test3=1,
                )

        self.__check_result(self.__stdout.getvalue(), self.__stderr.getvalue())

    def test__command_line(self):
        process = subprocess.Popen(
            [
                sys.argv[0],
                'test_command',
                '-v', '0',
                '--traceback',
                '--test1', 'qwe',
                '--test2',
                '--test3', '1',
                'asd', '1'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.wait()

        output = process.stdout.read()
        errors = process.stderr.read()

        if process.returncode != 0:
            print output
            print errors
        else:
            self.assertEqual(process.returncode, 0)
            self.__check_result(output, errors)
# -----------------------------------------------------------------------------
