from pyramid.config import Configurator
from pyramid.request import Request

from .db import *
from . import post
from . import user


def request_connection_factory(dbname: str):
    def get_connection(request: Request):
        conn = db.connect(dbname)

        def commit_callback(request):
            if request.exception is not None:
                conn.rollback()
            else:
                conn.commit()
            conn.close()

        request.add_finished_callback(commit_callback)
        return conn

    return get_connection


def includeme(config: Configurator):
    """Register per request DB connection.

    Register a ``db`` attribute on :class:`pyramid.request.Request` returning a database connection
    for the duration of the request.

    The connection is created lazily.
    Any transaction is commited at the end of the request unless an exception was raised, in which case
    the transaction is rolled back.

    Example::

        def view(request):
            conn = request.db
            cur = conn.cursor()
            cur.execute('SELECT * FROM foo')
            ...
            cur.close()
            ...

    :param config: pyramid configurator
    """
    import os
    import logging

    dbname = os.path.normpath(config.registry.settings.get('db.app', 'app.db'))
    logging.getLogger(__name__).info('Database: %s', dbname)

    # Initialize database on first run
    if not os.path.exists(dbname): # pragma: no cover
        init(dbname)

    config.add_request_method(request_connection_factory(dbname), 'db', reify=True)
