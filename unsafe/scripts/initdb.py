"""
Database initialization utility.

Creates database and loads initial data. Invokes `unsafe.db.init`.

Database name is given as the first argument and defaults to `app.db` in the current directory.

"""
import argparse
import sys

import unsafe.db


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('db', default='app.db', nargs='?')
    args = parser.parse_args(argv[1:])
    unsafe.db.init(args.db)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
