if __name__ == '__main__':
    import argparse
    import os
    import sys
    import waitress

    from .app import main
    from . import db
    import unsafe

    parser = argparse.ArgumentParser()
    parser.add_argument('--listen', '-l',
                        default='0.0.0.0:6543',
                        metavar='ADDRESS',
                        help='Specify alternate address and port')
    parser.add_argument('--initdb', action='store_true')
    args = parser.parse_args()

    if args.initdb:
        db.runscripts('app.db', 'db-create.sql', 'db-init.sql', script_path=os.path.join(unsafe.__path__[0], 'sql'))
        sys.exit(0)

    global_config = {}
    settings = {
        'pyramid.reload_templates': True,
        'jinja2.filters': {
            'abbrev': 'unsafe.filters:abbrev_filter',
            'model_url': 'pyramid_jinja2.filters:model_url_filter',
            'route_url': 'pyramid_jinja2.filters:route_url_filter',
            'static_url': 'pyramid_jinja2.filters:static_url_filter'
        }
    }
    app = main(global_config, **settings)

    print(f'Listening on {args.listen}')
    waitress.serve(app, listen=args.listen)
