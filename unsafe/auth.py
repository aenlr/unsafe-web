import hmac
import uuid

from pyramid.config import Configurator
from pyramid.exceptions import BadCSRFToken
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.request import Request
from pyramid.security import remember, forget
from pyramid.view import view_config, forbidden_view_config

from .embed import embeddable
from . import db


def _get_user(request):
    userid = request.unauthenticated_userid
    if userid is not None:
        user = db.user.from_id(request.db, userid)
        return user


def _groupfinder(userid, request):
    user = request.user
    if user is not None:
        return ['g:' + group for group in request.user.groups]
    return None


@view_config(route_name='login', renderer='login.jinja2', decorator=embeddable)
def login_view(request: Request):
    """Login form.

    After successful login redirects to the URL in the query or post
    parameter ``next``. By default redirects to the index page.
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
        if not hmac.compare_digest(csrf_token, expected_csrf_token):
            raise BadCSRFToken()

        user = db.user.authenticate(request.db, username, password)
        if user:
            # Important - at the very least generate a new session id at
            # login/logout to prevent session fixation attacks.
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


@view_config(route_name='logout', renderer='logout.jinja2')
def logout_view(request: Request):
    """Logout view. Redirects to the login page."""
    headers = forget(request)
    request.session.invalidate()
    request.response.headers.extend(headers)
    login_url = request.route_url('login')
    return dict(login_url=login_url)


@forbidden_view_config(decorator=embeddable)
def forbidden_view(request):
    """Forbidden view.
    Redirects to login if the user is not already logged in,
    otherwise returns HTTP 403.
    """

    if request.authenticated_userid:
        # User already logged in -> forbidden
        return HTTPForbidden()

    login_url = request.route_url('login', _query=(('next', request.path),))
    return HTTPFound(location=login_url)


def includeme(config: Configurator):
    """ Setup authentication/authorization.

    - Make user object on request object as ``user``
    - Store authenticated user in session
    - Use ACL authorization (__acl__ in context)
    """
    from pyramid.authentication import SessionAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy
    config.add_request_method(_get_user, 'user', reify=True)
    authn_policy = SessionAuthenticationPolicy(callback=_groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
