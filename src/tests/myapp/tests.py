# coding: utf-8
from warnings import catch_warnings

from django.db import models
from django.db.models.query import QuerySet
from django.db.utils import DEFAULT_DB_ALIAS
from django.test import SimpleTestCase
from django.test import TestCase
from django.test import Client

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
