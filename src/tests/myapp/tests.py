# coding: utf-8
from warnings import catch_warnings

from django.test import SimpleTestCase
from django.test import TestCase

from m3_django_compat import AUTH_USER_MODEL
from m3_django_compat import Manager
from m3_django_compat import atomic
from m3_django_compat import get_model
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
