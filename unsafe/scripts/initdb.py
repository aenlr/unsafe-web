"""
Database initialization utility.

Creates database and loads initial data. Invokes `unsafe.db.init`.

Database name is given as the first argument and defaults to `app.db`
in the current directory.

"""
import argparse
import os
import sys

from pyramid.paster import get_appsettings

import unsafe.db as db


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', '-r', action='store_true')
    parser.add_argument('--db', '-db')
    parser.add_argument('config', default='production.ini', nargs='?')
    args = parser.parse_args(argv[1:])

    if args.db:
        dbname = args.db
    else:
        settings = get_appsettings(args.config)
        if not settings:
            settings = get_appsettings(args.config, name='unsafe')
        dbname = settings['db.app']

    if args.reset and os.path.exists(dbname):
        os.remove(dbname)

    db.init(dbname)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
