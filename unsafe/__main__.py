if __name__ == '__main__':
    import argparse
    from wsgiref.simple_server import make_server
    from .app import main

    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', '-b', default='0.0.0.0', metavar='ADDRESS',
                        help='Specify alternate bind address '
                             '[default: all interfaces]')
    parser.add_argument('port', action='store',
                        default=6543, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 6543]')
    args = parser.parse_args()

    global_config = {}
    settings = {
        'pyramid.reload_templates': True
    }
    app = main(global_config, **settings)

    with make_server(args.bind, args.port, app) as httpd:
        sa = httpd.socket.getsockname()
        print('Listening on {}:{}'.format(sa[0], sa[1]))
        httpd.serve_forever()
