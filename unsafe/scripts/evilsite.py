"""
Serve the evil site.
"""
import argparse
import http.server
import sys
from functools import partial


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', default='localhost:6543')
    parser.add_argument('--bind', '-b', default='127.0.0.1')
    parser.add_argument('port', default='8000', type=int, nargs='?')
    parser.add_argument('--directory', '-d', default='evil-site')
    args = parser.parse_args(argv[1:])
    handler_class = partial(http.server.SimpleHTTPRequestHandler,
                            directory=args.directory)
    http.server.test(HandlerClass=handler_class, port=args.port, bind=args.bind)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
