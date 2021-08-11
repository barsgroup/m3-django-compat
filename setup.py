# coding: utf-8
import os
from setuptools import setup, find_packages


def main():
    setup(
        name='m3-django-compat',
        author='БАРС Груп',
        author_email='dev@bars-open.ru',
        description=(
            'Библиотека для обеспечения совместимости кода с разными версиями '
            'Django.'
        ),
        url='https://stash.bars-open.ru/projects/M3/repos/m3-django-compat',
        classifiers=[
            'Intended Audience :: Developers',
            'Natural Language :: Russian',
            'Operating System :: OS Independent',
            'Framework :: Django :: 1.4',
            'Framework :: Django :: 1.5',
            'Framework :: Django :: 1.6',
            'Framework :: Django :: 1.7',
            'Framework :: Django :: 1.8',
            'Framework :: Django :: 1.9',
            'Framework :: Django :: 1.10',
            'Framework :: Django :: 1.11',
            'Framework :: Django :: 2.0',
            'Framework :: Django :: 2.1',
            'Framework :: Django :: 2.2',
            'Framework :: Django :: 3.0',
            'Framework :: Django :: 3.1',
            'Framework :: Django :: 3.2',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: Implementation :: CPython',
            'Development Status :: 5 - Production/Stable',
            'Topic :: Software Development',
        ],
        package_dir={'': 'src'},
        packages=find_packages('src', exclude=('tests', 'tests.*')),
        include_package_data=True,
        dependency_links=(
            'https://pypi.bars-open.ru/simple/m3-builder',
        ),
        setup_requires=(
            'm3-builder>=1.2,<2',
        ),
        install_requires=(
            'six>=1.11.0,<2',
            'm3-builder>=1.2,<2',
            'django>=1.4,<4',
        ),
        set_build_info=os.path.join(os.path.dirname(__file__)),
    )


if __name__ == '__main__':
    main()
