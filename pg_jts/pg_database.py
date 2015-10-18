# Copyright (C) 2015 ibu radempa <ibu@radempa.de>
#
# Permission is hereby granted, free of charge, to
# any person obtaining a copy of this software and
# associated documentation files (the "Software"),
# to deal in the Software without restriction,
# including without limitation the rights to use,
# copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is
# furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission
# notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY
# OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Query structure information from a PostgreSQL database.

Extract information on these structures from a database:
  * schemas (non-system only)
  * tables
  * columns
  * indexes
  * views

Extraction of these structures has not been implemented yet:
  * table inheritance
  * sequences
  * triggers
  * functions

.. note:: You have to call :func:`pg_query.db_init` with a PostgreSQL
          connection string in advance.
"""

from .pg_query import db_get_all


def get_database():
    """
    Return the name of the current database.

    Returns a string.
    """
    q = "SELECT current_database()"
    return db_get_all(q, None)[0][0]


def get_database_description():
    """
    Return the comment on the database.

    Returns a string.
    """
    q = """
    SELECT pg_catalog.shobj_description(d.oid, 'pg_database')
    FROM pg_catalog.pg_database d WHERE d.datname=current_database()
    """
    return db_get_all(q, None)[0][0]


def get_server_version():
    """
    Return the server version number.

    Returns a string.
    """
    q = "SELECT version()"
    return db_get_all(q, None)[0][0].split(' ')[1]


def get_now():
    """
    Return the current datetime from PostgreSQL.

    Returns a string.
    """
    q = "SELECT now()::TEXT"
    return db_get_all(q, None)[0][0]


def get_schemas():
    """
    Return a list of all non-system schemas.

    Each schema is described by a dictionary with following keys:

       * **schema_name**: name of the schema
       * **schema_comment**: the PostgreSQL comment characterizing the schema
    """
    q = "SELECT nspname, pg_catalog.obj_description(pg_namespace.oid)"\
        " FROM pg_namespace WHERE nspname NOT LIKE 'pg\_%' AND"\
        " nspname NOT LIKE 'information_schema'"
    return [{'schema_name': r[0], 'schema_comment': r[1]}
            for r in db_get_all(q, None)]


def get_tables(schema_name):
    """
    Return a list of all tables within a schema.

    Each table is described by a dictionary with following keys:

       * **table_name**: name of the table
       * **table_comment**: the PostgreSQL comment describing the table
    """
    q = """
    SELECT
        class.relname,
        pg_catalog.obj_description(class.oid) AS table_comment
    FROM
                  pg_class AS class
        LEFT JOIN pg_namespace AS nsp ON nsp.oid = class.relnamespace
    WHERE
            nsp.nspname=%s
        AND class.relkind='r'
    """
    return [{'table_name': r[0], 'table_comment': r[1]}
            for r in db_get_all(q, (schema_name,))]


def get_columns(schema_name, table_name):
    """
    Return the column properties for given *table_name* and *schema_name*.

    Return a list of dictionaries with these keys:

      * **column_name**:
      * **datatype**: 
      * **ordinal_pos**: 
      * **null**: 
      * **column_default**: 
      * **column_comment**: 
    """
    q = """
    SELECT
        att.attname AS column_name,
        SUBSTR(typ.typname, CASE WHEN attndims>0 THEN 2 ELSE 1 END)
            || COALESCE('(' ||
                information_schema._pg_char_max_length(
                information_schema._pg_truetypid(att.*, typ.*),
                information_schema._pg_truetypmod(att.*, typ.*)
                )::information_schema.cardinal_number
                || ')', '')
            || repeat('[]', attndims) AS datatype,
        att.attnum AS ordinal_position,
        NOT att.attnotnull AS null_allowed,
        pg_get_expr(ad.adbin, ad.adrelid) AS column_default,
        pg_catalog.col_description(cls.oid, att.attnum) AS column_comment
    FROM
                  pg_class AS cls
        LEFT JOIN pg_namespace AS nsp ON nsp.oid = cls.relnamespace
        LEFT JOIN pg_attribute AS att ON att.attrelid = cls.oid
        LEFT JOIN pg_type AS typ ON typ.oid = att.atttypid
        LEFT JOIN pg_attrdef AS ad ON ad.adrelid = att.attrelid
                                      AND ad.adnum = att.attnum
    WHERE
            nsp.nspname=%s
        AND cls.relkind='r'
        AND cls.relname=%s
        AND att.attnum>0
        AND NOT att.attisdropped
    ORDER BY
        ordinal_position
    """
    keys = (
        'column_name',
        'datatype',
        'ordinal_pos',
        'null',
        'column_default',
        'column_comment',
    )
    return [dict(zip(keys, r)) for r in
            db_get_all(q, (schema_name, table_name))]


def get_constraints(schema_name, table_name):
    """
    Return constraints for a table, one per constraint and per column.

    Constraint types are:

      * **c**: check constraint
      * **f**: foreign key constraint
      * **p**: primary key constraint
      * **u**: unique constraint
      * **t**: constraint trigger
      * **x**: exclusion constraint

    For each constraint the results are ordered by ordinal_position.
    """
    q = """
    SELECT
        ss.coid constraint_oid,
        ss.nc_nspname::information_schema.sql_identifier AS constraint_schema,
        ss.conname::information_schema.sql_identifier AS constraint_name,
        (ss.x).n::information_schema.cardinal_number AS column_position,
        att.attname::information_schema.sql_identifier AS column_name,
        ss.contype constraint_type,
        CASE
            WHEN ss.contype='f'::"char" THEN
                information_schema._pg_index_position(ss.conindid,
                                                      ss.confkey[(ss.x).n])
            ELSE NULL::integer
        END::information_schema.cardinal_number
                       AS position_in_unique_constraint,
        refnsp.nspname AS referenced_schema,
        refcls.relname AS referenced_table,
        refatt.attname AS referenced_column
    FROM
        pg_attribute att
        INNER JOIN
            (   SELECT r.oid AS roid,
                    r.relowner,
                    nc.nspname AS nc_nspname,
                    c.oid AS coid,
                    c.conname,
                    c.contype,
                    c.conindid,
                    c.confkey,
                    c.confrelid,
                    information_schema._pg_expandarray(c.conkey) AS x
                FROM pg_namespace nr,
                    pg_class r,
                    pg_namespace nc,
                    pg_constraint c
                WHERE
                        nr.oid=r.relnamespace
                    AND nr.nspname=%s
                    AND r.oid=c.conrelid
                    AND r.relname=%s
                    AND nc.oid=c.connamespace
                    AND (c.contype=ANY(
                               ARRAY['p'::"char", 'u'::"char", 'f'::"char"]))
                    AND r.relkind='r'::"char"
                    AND NOT pg_is_other_temp_schema(nr.oid)
            ) ss
            ON ss.roid=att.attrelid AND att.attnum=(ss.x).x
        LEFT JOIN pg_class refcls
            ON refcls.oid=ss.confrelid
        LEFT JOIN pg_namespace refnsp
            ON refcls.relnamespace=refnsp.oid
        LEFT JOIN pg_attribute refatt
            ON refatt.attrelid=refcls.oid
               AND refatt.attnum=ss.confkey[(ss.x).n]
    WHERE
            NOT att.attisdropped
        AND (pg_has_role(ss.relowner, 'USAGE'::text)
             OR
             has_column_privilege(ss.roid, att.attnum,
                                  'SELECT, INSERT, UPDATE, REFERENCES'::text))
    ORDER BY
        constraint_schema,
        constraint_name,
        column_position
    """
    keys = (
        'constraint_oid',
        'constraint_schema',
        'constraint_name',
        'column_position',
        'column_name',
        'constraint_type',
        'position_in_unique_constraint',
        'referenced_schema',
        'referenced_table',
        'referenced_column',
    )
    return [dict(zip(keys, r)) for r in
            db_get_all(q, (schema_name, table_name))]


def get_indexes(schema_name, table_name):
    """
    Return a list of indexes for a table within a schema.

    Each index is described by a dictionary as described in
    :mod:`pg_jts.pg_jts`.
    """
    q = """
    SELECT
        index_name,
        array_agg(attname) AS columns,
        indisunique,
        indisprimary,
        create_statement,
        definition
    FROM
    (
        SELECT
            inds.index_name,
            att.attname,
            (inds.x).n column_position,
            inds.indisunique,
            inds.indisprimary,
            pg_get_indexdef(inds.indexrelid) create_statement,
            regexp_replace(pg_get_indexdef(inds.indexrelid), '.* USING ', '')
                AS definition
        FROM
            (
                SELECT
                    ind.indexrelid,
                    ind.indrelid,
                    ind.indisunique,
                    ind.indisprimary,
                    cls_index.relname AS index_name,
                    information_schema._pg_expandarray(ind.indkey) AS x,
                    unnest(ind.indkey) AS index_column
                FROM
                    pg_namespace nsp,
                    pg_index ind,
                    pg_class cls_table,
                    pg_class cls_index
                WHERE
                        nsp.nspname=%s
                    AND nsp.oid=cls_table.relnamespace
                    AND cls_table.relname=%s
                    AND ind.indrelid=cls_table.oid
                    AND ind.indexrelid=cls_index.oid
            ) inds,
            pg_attribute att
        WHERE
                inds.indrelid = att.attrelid
            AND inds.index_column = att.attnum
        ORDER BY
            inds.indrelid,
            (inds.x).n
    ) t
    GROUP BY
        index_name,
        indisunique,
        indisprimary,
        create_statement,
        definition
    """
    keys = (
        'name',
        'fields',
        'unique',
        'primary',
        'creation',
        'definition',
    )
    return [dict(zip(keys, r)) for r in
            db_get_all(q, (schema_name, table_name))]


def get_views(schema_name):
    """
    Return a list of views within a schema of given name.

    Each view is described by a dictionary having these keys:

      * **view_name**: the name of the view (i.e. of the virtual table)
      * **view_definition**: the SELECT statement defining the view
    """
    q = "SELECT viewname, definition FROM pg_catalog.pg_views"\
        " WHERE schemaname=%s"
    return [{'view_name': r[0], 'view_definition': r[1]}
            for r in db_get_all(q, (schema_name,))]


def get_sequences(schema_name):
    """
    Return a list of sequences within a schema with given name.

    NOT IMPLEMENTED; TODO:

    SELECT * FROM information_schema.sequences;
    """
    pass


def get_triggers(schema_name):
    """
    Return a list of triggers within a schema with given name.

    NOT IMPLEMENTED; TODO:

    SELECT * FROM information_schema.triggers;
    """
    pass


def get_functions(schema_name):
    """
    Return a list of triggers within a schema with given name.

    NOT IMPLEMENTED; TODO:
    """
    q = """
    SELECT  proname, prosrc
    FROM    pg_catalog.pg_namespace n
    JOIN    pg_catalog.pg_proc p
    ON      pronamespace = n.oid
    WHERE   nspname = 'public';
    """


if __name__ == '__main__':
    from postgres_access import init
    init()
    from pprint import pprint as print_
    print_(get_schemas())
    for schema in get_schemas():
        print_(schema)
        schema_name = schema['schema_name']
        for table in get_tables(schema_name):
            print_(table)
            table_name = table['table_name']
            for column in get_columns(schema_name, table_name):
                print_(column)
            print(get_indexes(schema_name, table_name))
        for view in get_views(schema_name):
            print(view)
            # print(get_indexes(schema_name, table_name)))
    print()
    print(get_table_columns())
