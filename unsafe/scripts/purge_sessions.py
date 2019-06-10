import argparse
import sys

from unsafe.session import purge_sessions


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('db', default='sessions.db', nargs='?')
    args = parser.parse_args(argv[1:])
    count = purge_sessions(args.db)
    print(f'Purged {count} sessions')


if __name__ == '__main__':
    sys.exit(main() or 0)
