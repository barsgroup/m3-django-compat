# coding: utf-8
import os
import sys

from setuptools import setup, find_packages


def main():
    setup(
        name='m3-django-compat',
        author=u'БАРС Груп',
        author_email='dev@bars-open.ru',
        description=u'Библиотека для обеспечения совместимости кода с '
                    u'разными версия Django',
        url='https://stash.bars-open.ru/projects/M3/repos/m3-django-compat',
        package_dir={'': 'src'},
        packages=find_packages('src', exclude=('tests', 'tests.*')),
        include_package_data=True,
        dependency_links=(
            'http://pypi.bars-open.ru/simple/m3-builder',
        ),
        setup_requires=(
            'm3-builder>=1.0.1',
        ),
        install_requires=(
            'm3-builder>=1.0.1',
        ),
        set_build_info=os.path.join(os.path.dirname(__file__)),
    )


if __name__ == '__main__':
    main()
