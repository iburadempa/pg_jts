Installation
============

**Beware**: This software is in alpha state.

The pg_jts package depends on `psycopg2` or `psycopg2-binary`.
You will either have to install one of them yourself, or if you
are fine with installing `psycopg2-binary`, you can add it as an
extra dependency using your favourite package manager:

    pipenv install pg_jts[psycopg2-binary]
    pip    install pg_jts[psycopg2-binary]
    pip3   install pg_jts[psycopg2-binary]

It works with python3.7 and PostgreSQL 11.7; other versions are untested,
but higher python versions and PostgreSQL 9 and above are expected to work.
