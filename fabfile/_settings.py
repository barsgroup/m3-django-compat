# coding: utf-8
from os.path import abspath
from os.path import dirname
from os.path import join


#: Имя пакета с проектом.
PROJECT_PACKAGE = 'm3_django_compat'


#: Папка проекта.
PROJECT_DIR = dirname(dirname(abspath(__file__)))


#: Папка с исходными кодами.
SRC_DIR = join(PROJECT_DIR, 'src')


#: Папка с тестами.
TESTS_DIR = join(PROJECT_DIR, 'src', 'tests')


#: Название PyPI-сервера для загрузки дистрибутивов пакета в ``~/.pypirc``.
PYPI_SERVER = 'bars'


#: Папка со списками зависимостей проекта.
REQUIREMENTS_DIR = join(PROJECT_DIR, 'requirements')


#: Путь к файлу со списком зависимостей проекта для development-среды.
REQUIREMENTS_DEV = join(REQUIREMENTS_DIR, 'dev.txt')
