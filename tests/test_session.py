import json
import os

from http.cookies import SimpleCookie
from typing import Optional

from pyramid import testing
from pyramid.config import Configurator
from webtest import TestApp as App, TestResponse as Response

from unsafe.session import MySessionFactory
from unsafe import db

DBNAME = 'test-sessions.db'


def setup_module():
    try:
        os.remove(DBNAME)
    except FileNotFoundError: # pragma: no cover
        pass


def make_session(request, **kwargs):
    secret = kwargs.get('secret', 'secret')
    factory = MySessionFactory(secret, database=DBNAME, **kwargs)
    return factory(request)


def serialize_cookie(value, secret=b'secret', salt=b'pyramid.session.', hashalg='sha512'):
    from webob.cookies import SignedSerializer
    serialiser = SignedSerializer(secret, salt=salt, hashalg=hashalg)
    return serialiser.dumps(value).decode('latin-1')


def deserialize_cookie(value, secret=b'secret', salt=b'pyramid.session.', hashalg='sha512'):
    from webob.cookies import SignedSerializer
    serialiser = SignedSerializer(secret, salt=salt, hashalg=hashalg)
    return serialiser.loads(value)


def save_session(session_id, userdata, expires_at=None, created_at=None, timeout=1200):
    import time
    now = int(time.time())
    if not expires_at:
        expires_at = now + timeout
    if not created_at:
        created_at = now
    with db.cursor(DBNAME) as cur:
        cur.execute('INSERT INTO session_store (session_id, expires_at, created_at, userdata) VALUES(?,?,?,?)',
                    (session_id, expires_at, created_at, json.dumps(userdata)))


def load_session(session_id):
    with db.cursor(DBNAME) as cur:
        cur.execute('SELECT userdata FROM session_store WHERE session_id = ?', (session_id,))
        row = cur.fetchone()
        return json.loads(row[0]) if row else None


def request_with_session(session_id, session_data=None, cookie=None):
    if not cookie and session_id:
        cookie = serialize_cookie(session_id)

    request = testing.DummyRequest()

    if cookie:
        request.cookies['session'] = cookie
    request.session = make_session(request)

    if session_data:
        save_session(session_id, session_data)

    return request


def make_response(request) -> Response:
    response = request.response
    getattr(request, '_process_response_callbacks')(response)
    return response


def test_new_session():
    request = request_with_session(None)
    session = request.session
    assert session.new is True
    assert dict(session) == {}

    session['foo'] = 'bar'
    response = make_response(request)

    assert 'Set-Cookie' in response.headers
    jar = SimpleCookie(response.headers['Set-Cookie'])

    assert 'session' in jar
    session_cookie = jar['session']
    session_id = deserialize_cookie(session_cookie.value)
    session_data = load_session(session_id)
    assert session_data == {'foo': 'bar'}


def test_decode_signed():
    session_id = test_decode_signed.__name__
    session_data = {'foo': 'bar'}
    session = request_with_session(session_id, session_data).session
    assert session.new is False
    assert dict(session) == session_data


def test_signature_mismatch():
    session_id = test_signature_mismatch.__name__
    cookie = serialize_cookie(session_id, secret=b'unsecret')
    session = request_with_session(session_id, cookie=cookie).session
    assert session.new is True


def foo_bar_view(request):
    request.session['foo'] = 'bar'
    return Response('OK')


def make_app(view=foo_bar_view, *, secret: Optional[str] = 'secret', **kwargs) -> App:
    config = Configurator(settings={})
    session_factory = MySessionFactory(secret, database=DBNAME, **kwargs)
    config.set_session_factory(session_factory)
    config.add_route('index', '/')
    config.add_view(route_name='index', view=view)
    app = config.make_wsgi_app()
    return App(app)


def get(view=foo_bar_view, *, secret: Optional[str] = 'secret', **kwargs) -> Response:
    return make_app(view, secret=secret, **kwargs).get('/')


def test_not_accessed():
    def view(request):
        session = request.session
        return Response('OK')

    response = get(view)
    assert 'Set-Cookie' not in response.headers


def test_signed_cookie():
    response = get()
    jar = SimpleCookie(response.headers['Set-Cookie'])
    assert 'session' in jar
    session_cookie = jar['session']
    session_id = deserialize_cookie(session_cookie.value)
    session_data = load_session(session_id)
    assert session_data == {'foo': 'bar'}


def test_unsigned_cookie():
    response = get(secret=None)
    jar = SimpleCookie(response.headers['Set-Cookie'])
    assert 'session' in jar
    session_cookie = jar['session']
    session_data = load_session(session_cookie.value)
    assert session_data == {'foo': 'bar'}
