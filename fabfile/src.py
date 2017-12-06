# coding: utf-8
# pylint: disable=relative-import
from os.path import dirname
from os.path import join
from shutil import get_terminal_size

from fabric.api import local
from fabric.colors import green
from fabric.context_managers import lcd
from fabric.context_managers import settings
from fabric.decorators import task
from fabric.tasks import execute

from ._settings import PROJECT_DIR
from ._settings import PROJECT_PACKAGE
from ._settings import SRC_DIR
from ._settings import TESTS_DIR
from ._utils import nested


@task
def isort():
    """Сортировка импортов в модулях проекта."""
    with lcd(PROJECT_DIR):
        _, width = get_terminal_size()
        print(green(u'-' * width, bold=True))
        print(green(u'isort', bold=True))

        local(f'isort -rc "{SRC_DIR}"')
        local(f'isort -rc "{TESTS_DIR}"')
        local(f'isort -rc "{dirname(__file__)}"')


@task
def style():
    """Проверка стилевого оформления кода проекта."""
    with nested(
        settings(ok_ret_codes=(0, 1)),
        lcd(PROJECT_DIR)
    ):
        _, width = get_terminal_size()
        print(green(u'-' * width, bold=True))
        print(green(u'PEP-8', bold=True))

        local(f'pycodestyle "{join(SRC_DIR, PROJECT_PACKAGE)}"')


@task
def pylint():
    """Проверка кода проекта с помощью PyLint."""
    with nested(
        settings(ok_ret_codes=(0, 1, 4, 30)),
        lcd(SRC_DIR),
    ):
        _, width = get_terminal_size()
        print(green(u'-' * width, bold=True))
        print(green(u'PyLint', bold=True))

        local(
            f'pylint "--rcfile={PROJECT_DIR}/pylint.rc" "{PROJECT_PACKAGE}"'
        )


@task
def clean():
    """Удаление файлов, созданных во время компиляции искодного кода."""
    for dir_path in (
        join(PROJECT_DIR, 'src'),
        join(PROJECT_DIR, 'fabfile'),
    ):
        for pattern in ('*.pyc', '__pycache__'):
            local(f'find "{dir_path}" -name {pattern} -delete')


@task(default=True)
def run_all():
    """Запуск всех проверок src.*."""
    execute(isort)
    execute(style)
    execute(pylint)
