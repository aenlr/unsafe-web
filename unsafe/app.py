import hmac
import uuid

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.request import Request
from pyramid.security import (
    remember, forget,
    Allow,
    Authenticated,
)
from pyramid.view import view_config, forbidden_view_config

from . import userdb
from .embed import embeddable


class RootContextFactory:
    def __init__(self, request):
        self.request = request

    @property
    def __acl__(self):
        userid = self.request.unauthenticated_userid
        if userid:
            return [
                (Allow, userid, ('view', 'edit'))
            ]
        else:
            return [
                (Allow, Authenticated, 'view')
            ]


###############################################################################
## Login
###############################################################################

@view_config(route_name='index', renderer='templates/index.jinja2')
def index(request):
    return {}


@view_config(route_name='login', renderer='templates/login.jinja2', decorator=embeddable)
def login_view(request: Request):
    """Login form.

    After successful login redirects to the URL in the query or post parameter ``next``.
    By default redirects to the index page.
    """

    def bind_set_csrf_token(value, max_age=None):
        def set_cookie(request, response):
            response.set_cookie(
                'csrf_token',
                value=value,
                path=request.path,
                secure=request.scheme == 'https',
                httponly=True,
                samesite='Strict',
                max_age=max_age)

        return set_cookie

    next_url = request.params.get('next') or request.route_url('index')
    if request.user:
        return HTTPFound(location=next_url)

    username = ''
    failed = False
    if 'submit' in request.POST:
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        csrf_token = request.POST.get('csrf_token', '')
        expected_csrf_token = request.cookies.get('csrf_token', '')
        if hmac.compare_digest(csrf_token, expected_csrf_token):
            user = userdb.authenticate(request.db, username, password)
            if user:
                # Important - at the very least generate a new session id at login/logout
                # to prevent session fixation attacks.
                request.session.invalidate()
                request.user = user
                headers = remember(request, user.user_id)
                request.add_response_callback(bind_set_csrf_token('', 0))
                return HTTPFound(location=next_url, headers=headers)

        failed = True

    csrf_token = uuid.uuid4().hex
    url = request.route_url('login')
    request.add_response_callback(bind_set_csrf_token(csrf_token))
    return dict(username=username,
                next=next_url,
                failed=failed,
                login_url=url,
                csrf_token=csrf_token)


@view_config(route_name='logout', renderer='templates/logout.jinja2')
def logout_view(request):
    """Logout view. Redirects to the login page."""
    headers = forget(request)
    request.session.invalidate()
    request.response.headers.extend(headers)
    login_url = request.route_url('login')
    return dict(login_url=login_url)


@forbidden_view_config(decorator=embeddable)
def forbidden_view(request):
    """Forbidden view. Redirects to login if the user is not already logged in, else returns HTTP 403."""

    if request.authenticated_userid:
        # User already logged in -> forbidden
        return HTTPForbidden()

    login_url = request.route_url('login', _query=(('next', request.path),))
    return HTTPFound(location=login_url)


def _register_request_db_attribute(config: Configurator) -> None:
    """Regiser per request DB connection.

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
    import logging
    import os
    from . import db
    import unsafe

    dbname = os.path.normpath(config.registry.settings.get('database', 'app.db'))
    logging.getLogger(__name__).info('Database: %s', dbname)

    # Initialize database on first run
    if not os.path.exists(dbname):
        scripts = ('db-create.sql', 'db-init.sql')
        sql_path = os.path.join(unsafe.__path__[0], 'sql')
        logging.getLogger(__name__).info('Running database scripts %s: %s', sql_path, ' '.join(scripts))
        try:
            db.runscripts(dbname, *scripts, script_path=sql_path)
        except Exception:
            os.remove(dbname)
            raise

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

    config.add_request_method(get_connection, 'db', reify=True)


def main(global_config, **settings):
    from . import auth
    from . import embed
    from .session import MySessionFactory
    from pyramid.authentication import SessionAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy
    from pyramid.csrf import SessionCSRFStoragePolicy
    import os

    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')

    # Make embedded property available on request object
    embed.register_request_property(config)

    ##########################################################################
    # Make database connection available on request object as 'db'
    # - Commit transaction after successful request
    # - Roll back transaction if an exception is raised
    _register_request_db_attribute(config)

    ##########################################################################
    # Setup session management
    session_secret = os.environ.get('UNSAFE_SESSION_SECRET', 'secret')
    session_factory = MySessionFactory(
        secret=session_secret,
        # secret=None, # No cookie signing!
        httponly=True,
        # secure=True,
        # query_param='session',
        accept_client_session_id=False)
    config.set_session_factory(session_factory)
    config.set_csrf_storage_policy(SessionCSRFStoragePolicy())

    ##########################################################################
    # Setup authentication/authorization
    # - Make user object on request object as 'user'
    # - Store authenticated user in session
    # - Use ACL authorization (__acl__ in context)
    config.add_request_method(auth.get_user, 'user', reify=True)
    authn_policy = SessionAuthenticationPolicy(callback=auth.groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    ##########################################################################
    # Setup views and routes
    # - Root context factory provides a default ACL
    # - /static/* serves static files
    config.set_root_factory(RootContextFactory)
    # Serve static files - in production this is offloaded to nginx
    config.add_static_view(name='static', path='unsafe:static', cache_max_age=0)

    # Base routes
    config.add_route('index', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    # Include modules
    # config.include('unsafe.admin')
    config.include('unsafe.notes')
    config.include('unsafe.posts')
    config.include('unsafe.topics')

    # Scan annotations
    config.scan()

    return config.make_wsgi_app()
