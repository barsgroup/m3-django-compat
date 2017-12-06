# coding: utf-8
# pylint: disable=relative-import
from fabric.api import local
from fabric.decorators import task

from ._settings import REQUIREMENTS_DEV


@task
def clean():
    """Удаление всех пакетов из окружения."""
    local(
        "pip freeze | "
        "egrep -v '\''pkg-resources'\'' | "
        "xargs pip uninstall -y"
    )
    local('pip install -U --force-reinstall setuptools fabric3')


@task
def dev():
    """Обновление списка зависимостей для development-среды."""
    local(f'pip install -U -r "{REQUIREMENTS_DEV}"')
