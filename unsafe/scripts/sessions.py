import argparse
import os
import sys

from pyramid.paster import get_appsettings

from unsafe.session import expire_sessions, purge_sessions, remove_sessions


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', '-db')
    parser.add_argument('--time')
    parser.add_argument('--config', default='production.ini')
    parser.add_argument('session', default='expired', nargs='*')
    args = parser.parse_args(argv[1:])

    if args.db:
        dbname = args.db
    else:
        settings = get_appsettings(args.config)
        if not settings:
            settings = get_appsettings(args.config, name='unsafe')
        dbname = settings['db.sessions']

    if not os.path.exists(dbname):
        count = 0
    elif args.session == ['all']:
        count = purge_sessions(database=dbname)
    elif args.session == 'expired':
        count = expire_sessions(expiry_time=args.time, database=dbname)
    else:
        count = remove_sessions(args.session, database=dbname)

    print(f'Purged {count} sessions from {dbname}')


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
