## Introduction

The schemas of tabular data (like e.g. in a CSV file) can be represented in a JSON notation
as specified in [Table schema](http://specs.frictionlessdata.io/table-schema).

The schema of a PostgreSQL database can be represented to some extent as a
JSON Table Schema (JTS). This is what pg_jts does.

It operates on a live PostgreSQL database and obtains the schema from
SQL queries on PostgreSQL's meta tables.

### FAQ

#### What can I do with a JTS-representation of my database?
> You can use tools for working with JTS (cf. https://github.com/frictionlessdata).
> On particular use case is visualizing your database as an
> entity-relationship diagram: Use [jts_erd](https://github.com/iburadempa/jts_erd/)
> for that.

#### Can I go in the reverse direction, i.e., generate a PostgreSQL database schema from a JTS?
> Have a look at [tableschema-sql-py](https://github.com/frictionlessdata/tableschema-sql-py).

#### Can I also export the data from PostgreSQL table with pg_jts?
> No, pg_jts only exports the schema. Maybe in the future it will be extended ...
