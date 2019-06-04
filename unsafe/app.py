from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPNoContent
from pyramid.security import (
    remember, forget,
    Allow,
    Authenticated,
)
from pyramid.view import view_config, forbidden_view_config
from pyramid.request import Request

from . import notedb
from . import userdb


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


class NotesFactory(RootContextFactory):

    def __getitem__(self, note_id):
        note = notedb.find_note(self.request.db, note_id)
        if note:
            return NoteResource(note)

        raise KeyError(note_id)


class NoteResource:
    def __init__(self, note: notedb.Note):
        self.note = note

    @property
    def __acl__(self):
        return [
            (Allow, self.note.user_id, ('view', 'edit'))
        ]


###############################################################################
## Login
###############################################################################

@view_config(route_name='index', renderer='templates/index.jinja2')
def index(request: Request):
    return {}


@view_config(route_name='login', renderer='templates/login.jinja2')
def login_view(request):
    """Login form.

    After successful login redirects to the URL in the query or post parameter ``next``.
    By default redirects to the index page.
    """
    next_url = request.params.get('next') or request.route_url('index')

    if request.user:
        return HTTPFound(location=next_url)

    username = ''
    failed = False
    if 'submit' in request.POST:
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        user = userdb.authenticate(request.db, username, password)
        if user:
            request.user = user
            headers = remember(request, user.user_id)
            return HTTPFound(location=next_url, headers=headers)
        failed = True

    url = request.route_url('login')
    return dict(username=username,
                next=next_url,
                failed=failed,
                login_url=url)


@view_config(route_name='logout', renderer='templates/logout.jinja2')
def logout_view(request):
    """Logout view. Redirects to the login page."""
    headers = forget(request)
    request.session.invalidate()
    request.response.headers.extend(headers)
    login_url = request.route_url('login')
    return dict(login_url=login_url)
    # return HTTPFound(location=login_url, headers=headers)


@forbidden_view_config()
def forbidden_view(request):
    """Forbidden view. Redirects to login if the user is not already logged in, else returns HTTP 403."""

    if request.authenticated_userid:
        # User already logged in -> forbidden
        return HTTPForbidden()

    login_url = request.route_url('login', _query=(('next', request.path),))
    return HTTPFound(location=login_url)


###############################################################################
## Notes
###############################################################################

@view_config(route_name='note-action', request_method=('GET', 'POST'), request_param='action=delete')
def delete_note_unsafe(request):
    """Unsafe delete of note.

    - Deletes as a side effect of GET request
    - Does not validate arguments (SQL injection due to unsafe implementation of delete_note)
    - Does not check permissions
    """

    notedb.delete_note(request.db, request.params['id'])
    return HTTPNoContent()


@view_config(route_name='notes', permission='view', renderer='templates/list-notes.jinja2')
def notes_view(request):
    search = request.params.get('search', '')
    from_date = request.params.get('from', '')
    to_date = request.params.get('to', '')
    notes = notedb.find_notes(request.db,
                              user_id=request.user.user_id,
                              from_date=from_date,
                              to_date=to_date,
                              search=search)

    return {
        'user': request.user,
        'notes': notes,
        'from': from_date,
        'to': to_date,
        'search': search
    }


@view_config(route_name='edit-note', permission='edit', renderer='templates/edit-note.jinja2')
def edit_note(context: NoteResource, request: Request):
    if request.method == 'POST':
        content: str = request.params['note']
        context.note.content = content.replace('\r', '')
        notedb.save_note(request.db, context.note)
        return HTTPFound(location=request.route_url('notes'))

    return dict(title='Redigera anteckning',
                note=context.note)


@view_config(route_name='new-note', permission='edit', renderer='templates/edit-note.jinja2')
def create_note(request: Request):
    if request.method == 'POST':
        note = notedb.Note(None,
                           user_id=request.user.user_id,
                           content=request.params['note'])
        notedb.save_note(request.db, note)
        return HTTPFound(location=request.route_url('notes'))

    return dict(title='Ny anteckning',
                note=notedb.Note(None, user_id=request.user.user_id, content=''))


def _register_db(config):
    from . import db

    def get_connection(request: Request):
        conn = db.connect('app.db')

        def commit_callback(request):
            if request.exception is not None:
                conn.rollback()
            else:
                conn.commit()

        request.add_finished_callback(commit_callback)
        return conn

    config.add_request_method(get_connection, 'db', reify=True)


def main(global_config, **settings):
    from . import auth
    from .session import MySessionFactory
    from pyramid.authentication import SessionAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy
    from pyramid.config import Configurator

    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')

    ##########################################################################
    # Make database connection available on request object as 'db'
    # - Commit transaction after successful request
    # - Roll back transaction if an exception is raised
    _register_db(config)

    ##########################################################################
    # Setup session management
    session_factory = MySessionFactory(
        secret='HGHNJE9kXShQVY',
        # secret=None, # No cookie signing!
        httponly=True,
        # secure=True,
        # query_param='session',
        accept_client_session_id=False)
    config.set_session_factory(session_factory)

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
    config.add_static_view(name='static', path='unsafe:static', cache_max_age=0)

    config.add_route('index', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.add_route('notes', '/notes', factory=NotesFactory)
    config.add_route('new-note', '/notes/new')
    config.add_route('edit-note', '/notes/{note}/edit', factory=NotesFactory,
                     traverse='/{note}')

    config.add_route('note-action', '/api/notes')

    # Scan annotations
    config.scan(ignore='unsafe.__main__')

    return config.make_wsgi_app()
