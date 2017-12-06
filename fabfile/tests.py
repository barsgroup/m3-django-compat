# coding: utf-8
# pylint: disable=not-context-manager, relative-import
from os import remove
from os.path import exists
from os.path import isdir
from os.path import join
from shutil import rmtree

from fabric.api import local
from fabric.context_managers import lcd
from fabric.decorators import task

from ._settings import PROJECT_DIR


@task
def run():
    """Запуск тестов."""
    with lcd(PROJECT_DIR):
        local('coverage erase')
        local('tox')
        local('coverage report --show-missing')


@task
def clean():
    """Удаление файлов, созданных во время сборки дистрибутивов."""
    for path in (
        join(PROJECT_DIR, '.tox'),
        join(PROJECT_DIR, '.eggs'),
        join(PROJECT_DIR, '.coverage'),
    ):
        if exists(path):
            print('REMOVE:', path)
            if isdir(path):
                rmtree(path)
            else:
                remove(path)
