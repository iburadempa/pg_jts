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

r"""
Create a generalized JSON-table-schema structure from a live postgres database.

The JSON data structure returned from :func:`get_database` is a generalization
of the `JSON-table-schema`_: The *resources* in our structure comply with the
table definition there (we extend it in allwoed ways). Our structure comprises
the whole database. It is the JSON-encoded form of a dictionary with these keys
(values being strings, if not otherwise indicated):

.. _`JSON-table-schema`:
   http://dataprotocols.org/json-table-schema/

    * **source**: the string 'PostgreSQL'
    * **source_version**: the PostgreSQL version returned by the server
    * **database_name**: the database name
    * **database_description**: the comment on the database
    * **generation_begin_time**: begin datetime as returned from PostgreSQL
    * **generation_end_time**: end datetime as returned from PostgreSQL
    * **datapackages**: a list of dictionaries, one for each PostgreSQL schema,
      with these keys:

      * **datapackage**: the name of the PostgreSQL schema
      * **resources**: a list of dictionaries, each describing a table within
        the current PostgreSQL schema and having these keys:

        * **name**: the name of the table
        * **description**: the table comment (only those components not part of
          a weak foreign key definition)
        * **primaryKey**: the primary key of the table, which is a list of
          column names
        * **fields**: a list of dictionaries describung the table columns and
          having these keys:

          * **name**: the column name
          * **description**: the column comment
          * **position**: 
          * **type**: the PostgreSQL data type, e.g., 'varchar(100)' or 'int4'
          * **defaultValue**: the default value of the column, e.g., '0', or
            'person_id_seq()' in case of a sequence
          * **constraints**: a dictionary describing constraints on the current
            column, with these keys:

            * **required**: boolean telling whether the column has a 'NOT NULL'
              constraint

        * **indexes**: a list of dictionaries, one per index and column,
          having these keys:

          * **name**: name of the index
          * **columns**: a list with the names of the columns used in the
            index and ordered by priority
          * **creation**: the SQL statement for creating the index
          * **definition**: the index definition, e.g., 'btree (id1, id2)'
          * **primary**: boolean telling whether the indexed columns form
            a primary key
          * **unique**: boolean telling whether the indexed columns are
            constrained to be unique

        * **foreignKeys**: a list of foreign keys used by the current table:

          * **columns**: the names of the columns in the current table which
            are referencing a remote relation
          * **enforced**: a boolean telling whether the foreign key constraint
            is being enforced in PostgreSQL (True), or if it is a weak
            reference and the constraint is kept only by the application
            software (False)
          * **reference**: a dict for specifying the reference target, having
            these keys:

            * **datapackage**: the name of the PostgreSQL schema in which the
              referenced table resides
            * **resource**: the name of the referenced table
            * **name**: the name of the foreign key constraint
            * **columns**: a list of the names of the referenced columns
            * **cardinalitySelf**: (optional) the cardinality of the foreign
              key relation (as obtained from a column or table comment)
              on the side of the current table
            * **cardinalityRef**: (optional) the cardinality of the foreign
              key relation (as obtained from a column or table comment)
              on the side of the remote table
            * **label**: (optional) a label describing the foreign key relation
              (as obtained from a column or table comment)

.. _foreign-key-syntax:

Foreign key syntax
~~~~~~~~~~~~~~~~~~

Foreign keys will be recognized where either a (hard) foreign key constraint
is present in PostgreSQL, or a table or column comment describes a foreign key
relation according to these syntax rules (we call this *weak reference*):

  * the comment is split at 1) ``;`` followed by a space character
    or 2) ``\n``, and results in what we call *components*
  * if a component matches one of the *relation_regexps*, we try to find
    a column name, a table name and an optional schema name in it; we match
    existing names in one of these four formats:

      * schema.table.column
      * table.column
      * schema.table(column1, column2, ..., columnN)
      * table(column1, column2, ..., columnN)

  * if a relation is valid, we also extract both cardinalities on the side of
    the table (card1) and on the foreign side (card2); the syntax is
    ``card1`` ``link`` ``card2``, where card1 and card2 are values in
    :any:`cardinalities` and link is one of ``--``, ``-`` with an optional
    space character on both sides (independently).
  * if a relation is valid, we also extract a label for the relation: when
    the component contains a string like ``label="<LABEL>"``, ``<LABEL>`` will
    be extracted. (On both sides of '=' an arbitrary number of white spaces may
    appear.

In cases where both a foreign key constraint and a weak reference are present,
the weak reference information supplements the constraint, in particular by
adding cardinalities (if present).
"""

import re
import json
from .pg_query import db_init
from . import pg_database as pd


re_components = re.compile('; |\n')
cardinalities = [
    '0..1',
    '1',
    '0..N',
    '1..N'
]
"""
Cardinalities.

These values are allowed in weak references.
"""
cards = '|'.join([re.escape(x) for x in cardinalities])
re_cardinalities = re.compile('(^| )(%s) ?--? ?(%s)( |,|$)'
                              % (cards, cards), re.I)
re_label = re.compile('(^| )label\s*=\s*"([^"]*)"( |$)')


def get_database(db_conn_str,
                 relation_regexps=None,
                 exclude_tables_regexps=None):
    """
    Return a JSON data structure representing the PostgreSQL database.

    Returns a JSON string and a list of notifications.
    The notifications inform about invalid or possibly unwanted
    syntax of the weak references (contained in the comments).

    A valid PostgreSQL connection string (*db_conn_str*) is required for
    connecting to a live PostgreSQL database with read permissions.

    The resulting data structure is missing some details. Currently
    mainly these structures are extracted from the database:

      * tables
      * foreign key relations (both constraints and weak references)
      * indexes

    The optional arguments have these meanings:

      * *exclude_tables_regexps* is a list of regular expression strings;
        if a table name matches any of them, the table and all its relations
        to other tables are omitted from the result
      * *relation_regexps* is a list of regular expression strings;
        if a table comment or a column comment matches any of them, it is
        parsed for a 'weak' foreign key relation
        (cf. :ref:`foreign-key-syntax`)
    """
    db_init(db_conn_str)
    if exclude_tables_regexps is None:
        exclude_tables_regexps = []
    begin_time = pd.get_now()
    database = pd.get_database()
    schemas = pd.get_schemas()
    res = []
    for schema in schemas:
        res_schema = {}
        schema_name = schema['schema_name']
        res_schema['datapackage'] = schema_name
        res_tables = []
        for table in pd.get_tables(schema_name):
            table_name = table['table_name']
            if not _check_exclude_table(exclude_tables_regexps, table_name):
                res_table = {}
                res_table['name'] = table_name
                table_comment = table['table_comment']
                if table_comment is not None:
                    res_table['description'] = table_comment
                constraints = _reshuffle_constraints(schema_name, table_name)
                if constraints['primary_key']:
                    res_table['primaryKey'] = constraints['primary_key']
                res_table['foreignKeys'] = constraints['foreign_keys']
                if constraints['unique']:  ## ????
                    res_table['unique'] = constraints['unique']  ## ????
                res_table['fields'] = _collect_columns(
                    schema_name,
                    table_name,
                    constraints['unique']
                )
                res_table['indexes'] = pd.get_indexes(schema_name, table_name)
                res_tables.append(res_table)
        res_schema['resources'] = res_tables
        res.append(res_schema)
    notifications = _add_annotated_foreign_keys(res, relation_regexps)
    end_time = pd.get_now()
    return json.dumps({
        'source': 'PostgreSQL',
        'source_version': pd.get_server_version(),
        'database_name': database,
        'database_description': pd.get_database_description(),
        'generation_begin_time': begin_time,
        'generation_end_time': end_time,
        'datapackages': res
    }), notifications


def _check_exclude_table(exclude_tables_regexps, table_name):
    """
    Return whether table *table_name* is to be excluded.

    Apply the patterns from *exclude_tables_regexps*.
    If at least one matches, return True.
    """
    for exclude_tables_regexp in exclude_tables_regexps:
        if re.search(exclude_tables_regexp, table_name):
            return True
    return False


def _reshuffle_constraints(schema_name, table_name):
    """
    Return primary key, foreign key and unique constraints for a table.

    See also: :func:`_collect_column_constraints`
    """
    constraint_names = []
    pk_column_names = []
    foreign_keys = {}
    unique = {}
    for constraint in pd.get_constraints(schema_name, table_name):
        # constraints are ordered by column_position
        column_name = constraint['column_name']
        constraint_type = constraint['constraint_type']
        c_oid = constraint['constraint_oid']
        if constraint_type == 'u':
            if c_oid not in unique:
                c_schema = constraint['constraint_schema']
                c_name = constraint['constraint_name']
                unique[c_oid] = {
                    'name': c_name,
                    'fields': []
                }
            unique[c_oid]['fields'].append(column_name)
        elif constraint_type == 'p':
            pk_column_names.append(column_name)  # using proper column ordering
        elif constraint_type == 'f':
            if c_oid not in foreign_keys:
                foreign_keys[c_oid] = {
                    'fields': [column_name],
                    'reference': {
                        'datapackage': constraint['referenced_schema'],
                        'resource': constraint['referenced_table'],
                        'name': constraint['constraint_name'],
                        'fields': []
                    },
                    'enforced': True
                }
            ref_col = constraint['referenced_column']
            foreign_keys[c_oid]['reference']['fields'].append(ref_col)
    return {
        'unique': list(unique.values()),
        'primary_key': pk_column_names,
        'foreign_keys': list(foreign_keys.values())
    }


def _collect_columns(schema_name, table_name, unique):
    """
    Return a column structure for a given table in a given schema.

    Return a list of dicts, each describing a table column.
    """
    res_columns = []
    columns = pd.get_columns(schema_name, table_name)
    for column in columns:  # columns are ordered by ordinal position
        res_column = {}
        res_column['name'] = column['column_name']
        res_column['type'] = column['datatype']
        description = column['column_comment']
        if description:
            res_column['description'] = description
        default_expr = column['column_default']
        if default_expr:
            res_column['default_value'] = _format_default(default_expr)
        constraints = _collect_column_constraints(column, unique)
        if constraints:
            res_column['constraints'] = constraints
        res_columns.append(res_column)
    return res_columns


def _collect_column_constraints(column, unique):
    """
    Collect constraints for a column.

    Use column information as well as unique constraint information.
    Note: for a unique constraint on a single column we set
          column / constraints / unique = True
          (and store all multicolumn uniques in the table realm)
    """
    res = {}
    if 'null' in column:
        res['required'] = column['null']
    for constr_i, constr in enumerate(unique):
        if column['column_name'] in constr['fields']:
            if len(constr['fields']) == 1:
                res['unique'] = True
    return res


def _format_default(expr):
    """
    Return text from a default value expression.

    Return a simplified form of a PostgreSQL default value.
    """
    if expr.lower().startswith('nextval('):
        r = expr.split("'", 1)[1]
        r = r.rsplit("'", 1)[0]
        return r + '()'
    elif expr.startswith("'"):
        r = expr.split("'", 1)[1]
        r = r.rsplit("'", 1)[0]
        return "'" + r + "'"
    else:
        return expr


def _add_annotated_foreign_keys(schemas, relation_regexps):
    """
    Add foreign keys defined in column comments.

    *schemas* must be a list of schemas as in :func:`get_database`.
    *relation_regexps* must be a list of regular expression strings for
    matching a 'weak' foreign key reference.
    """
    all_notifications = []
    schema_table_column = get_schema_table_column_triples(schemas)
    if relation_regexps:
        res_relation = [re.compile(x) for x in relation_regexps]
        for schema in schemas:
            schema_name = schema['datapackage']
            for table in schema['resources']:
                all_relations = []
                table_name = table['name']
                for column in table['fields']:
                    column_name = column['name']
                    if 'description' in column:
                        relations, notifications, comments = \
                            _parse_description(
                                schema_name,
                                table_name,
                                column_name,
                                column['description'],
                                schema_table_column,
                                res_relation
                            )
                        all_notifications += notifications
                        all_relations += relations
                        column['description'] = '; '.join(comments)
                if 'description' in table:
                    relations, notifications, comments = _parse_description(
                        schema_name,
                        table_name,
                        None,
                        table['description'],
                        schema_table_column,
                        res_relation
                    )
                    all_notifications += notifications
                    all_relations += relations
                    table['description'] = '; '.join(comments)
                _merge_foreign_keys(table['foreignKeys'], all_relations)
    return all_notifications


def _parse_description(schema_name, table_name, column_name,
                       description, schema_table_column, relation_regexps):
    r"""
    Extract relation information from a column or table comment.

    Split the description into components at '\n' as well as at '; '.
    Check each component for whether one of the *relations_regexps* does match.
    If so try to match (optionally a schema name,) a table name and
    the name(s) of a (tuple of) column(s) as well as two cardinalities.
    In case of a table comment also match another tuple of column names
    of the current table. For a table comment set *column_name*=None.

    Return a list of the found relations, a list of notifications from
    syntax parsing and a list remaining component (i.e., comment parts
    in which no relation was found).
    """
    current = (schema_name, table_name, column_name)
    current_text = '(schema=%s, table=%s, column=%s)' % current
    relations = []
    notifications = []
    components = re_components.split(description)
    comments = []  # remaining components
    if column_name is None:
        table_column_names = [x[2] for x in schema_table_column
                              if x[0] == schema_name and x[1] == table_name]
    for component in components:
        if not any([regex.search(component) for regex in relation_regexps]):
            comments.append(component)
            continue
        for s, t, c in schema_table_column:
            s_ = re.escape(s)
            t_ = re.escape(t)
            c_ = re.escape(c)
            found = 0
            p = re.search(' %s\.%s\.%s( |$)' % (s_, t_, c_), component)
            if p:
                found = 1
            if not found:
                p = re.search(' %s\.%s ?\( ?%s[, \)]' % (s_, t_, c_),
                              component)
                if p:
                    found = 2
            if not found:
                p = re.search(' %s\.%s( |$)' % (t_, c_), component)
                if p:
                    found = 3
            if not found:
                p = re.search(' %s ?\( ?%s[, \)]' % (t_, c_), component)
                if p:
                    found = 4
            if not found:
                continue
            matched1 = p.group(0)
            related_schema = s
            related_table = t
            related_columns = [c]
            if found in (3, 4):
                related_schema = 'public'
                if (related_schema, related_table) == current[:2]:
                    notifications.append(
                      ('INFO', current_text +
                       ' Dropping reference to same table ("%s")' % component)
                    )
                    continue
            if found in (2, 4):
                s1 = s + '.' if found == 2 else ''
                pattern = re.escape(s1 + t) + ' ?\((' +\
                          re.escape(c) + '[^\)]*)\)'
                m = re.search(pattern, component)
                if m:
                    matched1 = m.group(0)
                    cols = m.group(1).split(',')
                    related_columns = []
                    for col in cols:
                        col_name = col.strip()
                        related = (related_schema, related_table, col_name)
                        if related in schema_table_column:
                            if related[:2] == current[:2]:
                                notifications.append(
                                  ('INFO', current_text +
                                   ' Dropping reference to same table ("%s")'
                                     % component)
                                )
                            else:
                                related_columns.append(col_name)
                        else:
                            notifications.append(
                              ('WARN', current_text +
                               ' Inexistent referenced column "%s" in "%s"'
                                 % (col_name, component))
                            )
                else:
                    notifications.append(
                      ('WARN',
                       current_text + ' No closing bracket: "%s"' % component)
                    )
            m = re_cardinalities.search(component)
            cardinality_self = None
            cardinality_ref = None
            matched2 = ''
            if m:
                matched2 = m.group(0)
                cardinality_self = m.group(2)
                cardinality_ref = m.group(3)
            else:
                matched2 = ''
            m_label = re_label.search(component)
            matched3 = ''
            label = None
            if m_label:
                matched3 = m_label.group(0)
                label = m_label.group(2)
            if found:
                break
        else:
            notifications.append(
              ('WARN', current_text +
               ' No valid reference target found: "%s"' % component)
            )
        if found:
            if column_name is not None:
                # column comment
                relations.append({
                    'fields': [column_name],
                    'reference': {
                        'datapackage': related_schema,
                        'resource': related_table,
                        'fields': related_columns,
                        'cardinalitySelf': cardinality_self,
                        'cardinalityRef': cardinality_ref,
                        'label': label
                    },
                    'enforced': False
                })
            else:
                # table comment
                rest = component.replace(matched1, '')\
                                .replace(matched2, '')\
                                .replace(matched3, '')
                for col_name in table_column_names:
                    r = re.search('(^|\s+)\(\s*(%s\s*,[^\)]+)\)\s'
                                  % re.escape(col_name), rest)
                    if r:
                        col_s = r.group(2)
                        col_names = [s.strip() for s in col_s.split(',')]
                        if not set(col_names) <= set(table_column_names):
                            notifications.append(
                              ('WARN', current_text +
                               ' Invalid source column names "%s" found in:'
                               '"%s"' % (col_s, component))
                            )
                        else:
                            relations.append({
                                'fields': col_names,
                                'reference': {
                                    'datapackage': related_schema,
                                    'resource': related_table,
                                    'fields': related_columns,
                                    'cardinalitySelf': cardinality_self,
                                    'cardinalityRef': cardinality_ref,
                                    'label': label
                                },
                                'enforced': False
                            })
        else:
            comments.append(component)
    return relations, notifications, comments


def _merge_foreign_keys(fk_constraints, fk_relations):
    """
    Merge annotated foreign key relations into foreign key constraints.

    (Both constraints and relations are for the same table.)
    Add all relations, except if a matching constraint exists: then amend
    the constraint by adding cardinality information.
    """
    for rel in fk_relations:
        for constr in fk_constraints:
            if rel['fields'] == constr['fields']:
                r1 = rel['reference']
                r2 = constr['reference']
                if r1['datapackage'] == r2['datapackage'] and \
                   r1['resource'] == r2['resource'] and \
                   r1['fields'] == r2['fields']:
                        r2['cardinalitySelf'] = r1['cardinalitySelf']
                        r2['cardinalityRef'] = r1['cardinalityRef']
                        break
        else:
            fk_constraints.append(rel)


def get_schema_table_column_triples(database):
    """
    Return a list of all (schema_name, table_name, column_name)-combinations.

    *database* must have the same structure as obtained from
    :func:`get_database`.
    """
    res = []
    for schema in database:
        schema_name = schema['datapackage']
        for table in schema['resources']:
            table_name = table['name']
            for column in table['fields']:
                res.append((schema_name, table_name, column['name']))
    return res
