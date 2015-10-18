Installation
============

**Beware**: This software is in alpha state.

Currently there is no python package; you have to install from source.

It works with python3.4 and PostgreSQL 9.4; other versions are untested,
but other minor versions of python3 and PostgreSQL 9 are expected to work.

You need psycopg2 on your PYTHONPATH.


Detailed instructions
---------------------

Prepare a virtualenv with python3::

  mkdir pg_jts
  cd pg_jts
  virtualenv -p python3
  source bin/activate

Install package libpq-dev and then::

  pip3 install psycopg2

In the virtualenv root dir::

  git clone https://github.com/iburadempa/pg_jts.git
