"""
Utility that invokes pserve with default arguments if none are given: --reload development.ini
"""
import itertools
import sys

import pyramid.scripts.pserve as pserve


def main(argv=sys.argv, quiet=False):
    prog = argv[0]
    opts = list(itertools.takewhile(lambda opt: opt.startswith('-'), argv[1:]))
    args = argv[1 + len(opts):]

    if not any(arg.endswith('.ini') for arg in args):
        args.insert(0, 'development.ini')
        if '--reload' not in opts:
            opts.append('--reload')

    if '--no-reload' in opts:
        opts.remove('--no-reload')
        try:
            opts.remove('--reload')
        except ValueError:
            pass

    pserve_args = [prog] + opts + args
    return pserve.main(pserve_args, quiet=quiet)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
