## Roadmap

pg_jts seems to be rarely used by anybody;
accordingly, development activity is on a low level.

### Next steps

* more tests
* proper mapping of [https://www.postgresql.org/docs/11/datatype.html](PostgreSQL data types) to
  current [http://specs.frictionlessdata.io/table-schema/#types-and-formats](table schema types+formats)

### Wish list

* add typing (plus 'Typing :: Typed' to setup.py)
* extact information on table inheritance from PostgreSQL
* command line invokation (POSTGRESQL_DSN="..." python -m pg_jts --help)
