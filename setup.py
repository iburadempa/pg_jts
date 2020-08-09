import re
from os import path
from setuptools import setup


repo_root_dir = path.abspath(path.dirname(__file__))


def get_version():
    with open(path.join(repo_root_dir, 'pg_jts', '__init__.py'),
              encoding='utf-8') as version_file:
        match = re.search(r'^__version__ = \((\d+), (\d+), (\d+)\)$',
                          version_file.read(), re.M)
        version = '.'.join(
            [match.group(1), match.group(2), match.group(3)]
        ) if match else None
        return version


def get_long_description():
    with open(path.join(repo_root_dir, 'README.md'),
              encoding='utf-8') as readme_file:
        return readme_file.read()


# See https://setuptools.readthedocs.io/en/latest/setuptools.html
setup(
    name='pg_jts',
    version=get_version(),
    description='Create JSON-table-schema from a live PostgreSQL database',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/iburadempa/pg_jts',
    project_urls={
        'Bug Tracker': 'https://github.com/iburadempa/pg_jts/issues',
        'Documentation': 'https://pg-jts.readthedocs.io',
    },
    author='ibu radempa',
    author_email='ibu@radempa.de',
    license='MIT',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='JSON table schema, extract schema, JTS, PostgreSQL, Postgres',
    install_requires=[],
    extras_require={
        'psycopg2-binary':  ['psycopg2-binary'],
    },
    packages=['pg_jts'],
)
