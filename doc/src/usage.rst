Usage example
=============

1) RDBMS
--------

Install PostgreSQL 9.4

2) Database
-----------

Either choose an existing database or create a new one like this::

  createuser testuser -P
  createdb -E utf-8 -O testuser testdb

Check that you can access it like this::

  psql -W -U testuser -h 127.0.0.1 testdb
  or
  psql -d 'host=127.0.0.1 user=testuser dbname=testdb port=5432 password=***************'

Create some SQL structures::

  COMMENT ON database testdb IS 'test';
  CREATE TYPE chan AS ENUM('email', 'xmpp', 'sip');
  CREATE TABLE channel (id SERIAL PRIMARY KEY, channel_type CHAN, channel_attrs JSONB);
  COMMENT ON TABLE channel IS 'communication channel';
  COMMENT ON COLUMN channel.channel_attrs IS 'Channel attributes (specific to channel_type)';
  CREATE TABLE person (id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, channel_id INT NULL REFERENCES channel(id));
  CREATE INDEX person__name ON person (name);
  COMMENT ON COLUMN person.channel_id IS 'references channel(id) 1--1..N';
  CREATE TABLE software_release (id SERIAL PRIMARY KEY, software_name VARCHAR(100) NOT NULL, release_name VARCHAR(100), major INT NOT NULL, minor INT NOT NULL, patch INT NOT NULL, revision VARCHAR(50));
  ALTER TABLE software_release ADD CONSTRAINT software_release__version UNIQUE(software_name, major, minor, patch);
  CREATE INDEX software_release__versions2 ON software_release (major, minor);
  CREATE INDEX software_release__versions3 ON software_release (major, minor, patch);
  CREATE TABLE feature_change (id SERIAL PRIMARY KEY, description TEXT NOT NULL, major INT NOT NULL, minor INT NOT NULL);
  COMMENT ON TABLE feature_change IS 'changes of features for software releases; (major, minor) references software_release (major, minor) 1..N--1';

3) Module
---------

In the virtualenv root go to subdir pg_jts and run python3::

  >>> import pg_jts
  >>> j, notifications = pg_jts.get_database('host=127.0.0.1 user=testuser dbname=testdb port=5432 password=***************')

You will obtain a JSON representation of the database and a list of notifications. The data structure encoded as JSON looks like this::

 {'database_description': 'test',
 'database_name': 'testdb',
 'datapackages': [{'datapackage': 'public',
                   'resources': [{'description': 'communication channel',
                                  'fields': [{'constraints': {'required': False}, 'default_value': 'channel_id_seq()', 'name': 'id', 'type': 'int4'},
                                             {'constraints': {'required': True}, 'name': 'channel_type', 'type': 'chan'},
                                             {'constraints': {'required': True}, 'description': 'Channel attributes (specific to channel_type)', 'name': 'channel_attrs', 'type': 'jsonb'}],
                                  'foreignKeys': [],
                                  'indexes': [{'creation': 'CREATE UNIQUE INDEX channel_pkey ON channel USING btree (id)',
                                               'definition': 'btree (id)',
                                               'fields': ['id'],
                                               'name': 'channel_pkey',
                                               'primary': True,
                                               'unique': True}],
                                  'name': 'channel',
                                  'primaryKey': ['id']},
                                 {'fields': [{'constraints': {'required': False}, 'default_value': 'person_id_seq()', 'name': 'id', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'name', 'type': 'varchar(100)'},
                                             {'constraints': {'required': True}, 'description': 'references channel(id) 1--1..N', 'name': 'channel_id', 'type': 'int4'}],
                                  'foreignKeys': [{'enforced': True,
                                                   'fields': ['channel_id'],
                                                   'reference': {'datapackage': 'public', 'fields': ['id'], 'name': 'person_channel_id_fkey', 'resource': 'channel'}}],
                                  'indexes': [{'creation': 'CREATE UNIQUE INDEX person_pkey ON person USING btree (id)',
                                               'definition': 'btree (id)',
                                               'fields': ['id'],
                                               'name': 'person_pkey',
                                               'primary': True,
                                               'unique': True},
                                              {'creation': 'CREATE INDEX person__name ON person USING btree (name)',
                                               'definition': 'btree (name)',
                                               'fields': ['name'],
                                               'name': 'person__name',
                                               'primary': False,
                                               'unique': False}],
                                  'name': 'person',
                                  'primaryKey': ['id']},
                                 {'fields': [{'constraints': {'required': False}, 'default_value': 'software_release_id_seq()', 'name': 'id', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'software_name', 'type': 'varchar(100)'},
                                             {'constraints': {'required': True}, 'name': 'release_name', 'type': 'varchar(100)'},
                                             {'constraints': {'required': False}, 'name': 'major', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'minor', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'patch', 'type': 'int4'},
                                             {'constraints': {'required': True}, 'name': 'revision', 'type': 'varchar(50)'}],
                                  'foreignKeys': [],
                                  'indexes': [{'creation': 'CREATE UNIQUE INDEX software_release__version ON software_release USING btree (software_name, major, minor, patch)',
                                               'definition': 'btree (software_name, major, minor, patch)',
                                               'fields': ['software_name', 'major', 'minor', 'patch'],
                                               'name': 'software_release__version',
                                               'primary': False,
                                               'unique': True},
                                              {'creation': 'CREATE INDEX software_release__versions2 ON software_release USING btree (major, minor)',
                                               'definition': 'btree (major, minor)',
                                               'fields': ['major', 'minor'],
                                               'name': 'software_release__versions2',
                                               'primary': False,
                                               'unique': False},
                                              {'creation': 'CREATE INDEX software_release__versions3 ON software_release USING btree (major, minor, patch)',
                                               'definition': 'btree (major, minor, patch)',
                                               'fields': ['major', 'minor', 'patch'],
                                               'name': 'software_release__versions3',
                                               'primary': False,
                                               'unique': False},
                                              {'creation': 'CREATE UNIQUE INDEX software_release_pkey ON software_release USING btree (id)',
                                               'definition': 'btree (id)',
                                               'fields': ['id'],
                                               'name': 'software_release_pkey',
                                               'primary': True,
                                               'unique': True}],
                                  'name': 'software_release',
                                  'primaryKey': ['id'],
                                  'unique': [{'fields': ['software_name', 'major', 'minor', 'patch'], 'name': 'software_release__version'}]},
                                 {'description': 'changes of features for software releases; (major, minor) references software_release (major, minor) 1..N--1',
                                  'fields': [{'constraints': {'required': False}, 'default_value': 'feature_change_id_seq()', 'name': 'id', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'description', 'type': 'text'},
                                             {'constraints': {'required': False}, 'name': 'major', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'minor', 'type': 'int4'}],
                                  'foreignKeys': [],
                                  'indexes': [{'creation': 'CREATE UNIQUE INDEX feature_change_pkey ON feature_change USING btree (id)',
                                               'definition': 'btree (id)',
                                               'fields': ['id'],
                                               'name': 'feature_change_pkey',
                                               'primary': True,
                                               'unique': True}],
                                  'name': 'feature_change',
                                  'primaryKey': ['id']}]}],
 'generation_begin_time': '2015-10-18 13:30:20.086386+02',
 'generation_end_time': '2015-10-18 13:30:20.086386+02',
 'source': 'PostgreSQL',
 'source_version': '9.4.4'}
