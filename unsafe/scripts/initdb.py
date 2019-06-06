"""
Database initialization utility.

Creates database and loads initial data. Invokes `unsafe.db.init`.

Database name is given as the first argument and defaults to `app.db` in the current directory.

"""
import argparse
import os
import sys

import unsafe.db


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', '-r', action='store_true')
    parser.add_argument('db', default='app.db', nargs='?')
    args = parser.parse_args(argv[1:])

    if args.reset and os.path.exists(args.db):
        os.remove(args.db)

    unsafe.db.init(args.db)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
