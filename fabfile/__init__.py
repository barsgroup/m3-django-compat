# coding: utf-8
from os.path import join
import sys

from fabric.context_managers import cd
from fabric.decorators import task
from fabric.operations import local
from fabric.tasks import execute

from . import dist
from . import req
from . import src
from . import tests
from ._settings import PROJECT_DIR


assert sys.version_info.major == 3 and sys.version_info.minor == 6


@task
def clean():
    """Полная очистка от рабочих файлов."""
    execute(dist.clean)
    execute(src.clean)
    execute(tests.clean)

    with cd(PROJECT_DIR):
        for path in ('.eggs', 'dist'):
            path = join(PROJECT_DIR, path)
            local(f'rm -f -r -d "{path}"')

        local('git gc --quiet')
