"""
Unit tests.

See doc/devel.md for usage instructions.
"""

import json
import logging
import re
import sys
from os import environ
from traceback import format_exc
from unittest import TestCase
import psycopg2
import pg_jts


logging.basicConfig()
verbosity = sys.argv.count('-v')
if verbosity == 0:
    level = logging.WARNING
elif verbosity == 1:
    level = logging.INFO
else:
    level = logging.DEBUG
logging.getLogger().setLevel(level)


postgresql_dsn = environ.get('POSTGRESQL_DSN')


class TestPGJTS(TestCase):

    def setUp(self):
        # create database test_pg_jts
        conn = psycopg2.connect(postgresql_dsn)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE test_pg_jts")
        cur.execute("COMMENT ON DATABASE test_pg_jts IS %s", ('Testing pg_jts',))
        cur.close()
        conn.close()
        # connect to database test_pg_jts
        self.dsn = postgresql_dsn.replace('dbname=postgres', 'dbname=test_pg_jts')
        if self.dsn == postgresql_dsn:  # safety check
            print('Please use "dbname=postgres" in POSTGRESQL_DSN !')
            sys.exit(1)
        self.conn = psycopg2.connect(self.dsn)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur = self.conn.cursor()

    def sql(self, sql_, *args):
        """
        Helper method for executing sql.
        """
        try:
            self.cur.execute(sql_, *args)
        except:
            print(format_exc())
            self.conn.rollback()

    def jts(self):
        """
        Helper method for running `pg_jts.get_database`.
        """
        jts, n = pg_jts.get_database(self.dsn)
        return jts
        ### todo test n

    def test_empty_database(self):
        jts = self.jts()
        try:
            ts = json.loads(jts)
        except:
            ts = None
        self.assertIsInstance(ts, dict)
        keys1 = set(ts.keys())
        keys2 = set([
            'source', 'source_version', 'database_name',
            'database_description', 'generation_begin_time',
            'generation_end_time', 'datapackages', 'inheritance',
        ])
        self.assertEqual(keys1, keys2)
        self.assertEqual(ts['source'], 'PostgreSQL')
        self.assertEqual(ts['database_name'], 'test_pg_jts')
        self.assertEqual(ts['database_description'], 'Testing pg_jts')
        self.assertEqual(ts['datapackages'],
                         [{'datapackage': 'public', 'resources': []}])
        self.assertEqual(ts['inheritance'], [])

    def test_single_table(self):
        self.sql("""CREATE TABLE "table '*Ù" (id SERIAL)""")
        self.sql("""COMMENT ON TABLE "table '*Ù" IS 'That''s w@îrd'""")
        dp1 = json.loads(self.jts())['datapackages']
        dp2 = [{
            'datapackage': 'public',
            'resources': [
                {
                    'name': "table '*Ù",
                    'description': 'That\'s w@îrd',
                    'foreignKeys': [],
                    'fields': [
                         {'name': 'id',
                          'type': 'int',
                          'default_value': '"table \'\'*Ù_id_seq"()',
                          'constraints': {'required': True},
                         },
                     ],
                     'indexes': [],
                 },
            ],
        }]
        self.assertEqual(dp1, dp2)

    def test_data_types_and_field_names(self):
        self.sql("""CREATE TABLE table1 (
             id SERIAL,
             i1 smallint null,
             i2 int not null,
             i3 bigint,
             ia1 bigint[][] not null,
             "*-\_/'Ò" bool,
             t1 text
        )""")
        fields1 = json.loads(self.jts())['datapackages'][0]['resources'][0]['fields']
        fields2 = [
            {
                'name': 'id',
                'type': 'int',
                'default_value': 'table1_id_seq()',
                'constraints': {'required': True},
            },
            {
                'name': 'i1',
                'type': 'smallint',
                'constraints': {'required': False},
            },
            {
                'name': 'i2',
                'type': 'int',
                'constraints': {'required': True},
            },
            {
                'name': 'i3',
                'type': 'bigint',
                'constraints': {'required': False},
            },
            {
                'name': 'ia1',
                'type': 'bigint[][]',
                'constraints': {'required': True},
            },
            {
                'name': "*-\_/'Ò",
                'type': 'bool',
                'constraints': {'required': False},
            },
            {
                'name': 't1',
                'type': 'text',
                'constraints': {'required': False},
            },
        ]
        print(fields1)
        print(fields2)
        # verify both field lists are equal
        self.assertEqual([f for f in fields1 if f not in  fields2], [])
        self.assertEqual([f for f in fields2 if f not in  fields1], [])

    def test_column_comments(self):
        ...  # TODO

    def tearDown(self):
        # disconnect from database test_pg_jts
        self.cur.close()
        self.conn.close()
        # drop database test_pg_jts
        conn = psycopg2.connect(postgresql_dsn)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("DROP DATABASE test_pg_jts")
        cur.close()
        conn.close()
