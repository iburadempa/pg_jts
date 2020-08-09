## Development

### Setup enviroment

I suggest you use [pipenv](https://pipenv.readthedocs.io/).
Clone the git repo to some directory, enter the directory and
    pipenv install -d

### Run tests

Running unit tests requires a PostgreSQL user who is allowed to create databases.
If you are afraid it could damage other databases, create a separate PostgreSQL
cluster like this:

    pg_createcluster -p 54321 --start 11 test

Whichever cluster you use, create a database user who is allowed to create databases:

    createuser -P -d test_pg_jts

For testing the PostgreSQL DSN will be given to the python interpreter
through environment variable POSTGRESQL_DSN (run this in the repo root dir):

    POSTGRESQL_DSN='host=127.0.0.1 port=54321 dbname=postgres user=test_pg_jts password=************' python -m unittest discover

You can also pass option '-v' once to get more verbose output,
or twice to get even more verbose output.

### Related stuff

If you provide patches that change optional elements in the JTS output,
then please also consider patching [jts_erd](https://github.com/iburadempa/jts_erd/) accordingly.

### Release checklist

* git (commit, pull, status)
* run tests
* update __version__ in pg_jts/__init__.py
* edit changelog
* `make -C doc html`
* git commit
* `python setup.py sdist bdist_wheel`
* twine check dist/*
* test upload to test-pypi and test install
    twine upload -r testpypi dist/*
    pip install --index-url https://test.pypi.org/simple/ pg_jts
* upload to pypi
    twine upload dist/*
* rm -r dist
* `git tag -s v0.0.1`
* `git push --tags`
