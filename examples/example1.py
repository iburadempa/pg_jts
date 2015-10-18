import sys
sys.path.append('..')
dsn = sys.argv[1]

import pg_jts

j, notifications = pg_jts.get_database(dsn)

from pprint import pprint as print_
import json

print_(json.loads(j), width=200)
