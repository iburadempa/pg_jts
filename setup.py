from setuptools import setup, find_packages
from codecs import open
from os import path
from pg_jts import __version__ as version_triple

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pg_jts',
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='.'.join([str(n) for n in version_triple]),
    description='Create JSON-table-schema from a live PostgreSQL database',
    long_description=long_description,
    url='https://github.com/iburadempa/pg_jts',
    author='ibu radempa',
    author_email='ibu@radempa.de',
    license='MIT',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.4',
    ],
    keywords='set integer integers range ranges multiple span interval operations',
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['pg_jts'],
    #test_suite = 'tests',
)
