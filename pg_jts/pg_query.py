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
PostgreSQL access.

To use this module, :func:`db_init` has to be called in advance.
"""


import psycopg2

conn = None
"""
Database connection.
"""

cur = None
"""
Database cursor within connection :any:`conn`.
"""


def db_init(db_conn_str=None):
    """
    Initialize a database connection using a connection string.
    """
    global conn
    global cur
    if db_conn_str is not None:
        conn = psycopg2.connect(db_conn_str)
        cur = conn.cursor()


def db_get_all(query, attrs):
    """
    Execute an SQL query and return all rows (as list of tuples).
    """
    global cur
    if cur is None:
        raise Exception('Database not initialized, call db_init() !')
    cur.execute(query, attrs)
    return cur.fetchall()
