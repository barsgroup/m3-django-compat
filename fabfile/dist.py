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
from ._settings import PYPI_SERVER


@task
def build():
    """Сборка дистрибутива."""
    local(f'find "{PROJECT_DIR}" -name "*.pyc" -type f -delete')
    with lcd(PROJECT_DIR):
        local('python setup.py sdist')


@task
def upload():
    """Сборка дистрибутива и загрузка на PyPI-сервер."""
    local(f'find "{PROJECT_DIR}" -name "*.pyc" -type f -delete')
    with lcd(PROJECT_DIR):
        local(f'python setup.py sdist upload -r {PYPI_SERVER}')


@task
def clean():
    """Удаление файлов, созданных во время сборки дистрибутивов."""
    for path in (
        join(PROJECT_DIR, 'dist'),
        join(PROJECT_DIR, 'src', 'm3_django_compat.egg-info'),
    ):
        if exists(path):
            print('REMOVE:', path)
            if isdir(path):
                rmtree(path)
            else:
                remove(path)
