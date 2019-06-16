import os

from bs4 import BeautifulSoup

import pytest
from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.testing import DummyRequest
from webob.cookies import Cookie, Morsel
from webtest import TestApp as App

import unsafe.app
from unsafe.auth import login_view, logout_view
from unsafe import db
from unsafe.db import request_connection_factory

DBNAME_SESSIONS = 'test-sessions.db'
DBNAME_APP = 'test-app.db'

db_factory = request_connection_factory(DBNAME_APP)

csrf_cookie_name = 'csrf_token'


def setup_module():
    for fn in (DBNAME_APP, DBNAME_SESSIONS):
        try:
            os.remove(fn)
        except FileNotFoundError: # pragma: no cover
            pass

    db.init(DBNAME_APP)


@pytest.fixture()
def app() -> App:
    global_config = {}
    settings = {
        'db.app': DBNAME_APP,
        'db.sessions': DBNAME_SESSIONS
    }

    wsgi_app = unsafe.app.main(global_config, **settings)
    return App(wsgi_app)


def parse_html_response(response: Response):
    return BeautifulSoup(response.unicode_body, "html.parser")


def login(username, password, csrf_token='00112233445566778899aabbccddeeff', **kwargs):
    body = {
        'csrf_token': csrf_token,
        'submit': '',
        'username': username,
        'password': password
    }
    cookies = {csrf_cookie_name: csrf_token}

    request = make_request(path='/login',
                           post=body,
                           cookies=cookies,
                           **kwargs)

    value = login_view(request)
    response = make_response(request)

    return request, response, value


def make_request(scheme='https', **kwargs) -> DummyRequest:
    def route_url(route_name, *segments, **kwargs):
        return '/' + route_name

    request = testing.DummyRequest(**kwargs)
    request.scheme = scheme
    request.route_url = route_url
    request.user = None

    request.db = db_factory(request)
    return request


def make_response(request) -> Response:
    response = request.response
    getattr(request, '_process_response_callbacks')(response)
    return response


def parse_response_cookies(request_or_response) -> Cookie:
    try:
        response = make_response(request_or_response)
    except AttributeError:
        response = request_or_response

    headers = response.headers.getall('Set-Cookie')
    return Cookie('\r\n'.join(headers))


def get_response_cookie(request_or_response, cookie_name) -> Morsel:
    cookies = parse_response_cookies(request_or_response)
    key = cookie_name if isinstance(cookie_name, bytes) else cookie_name.encode('ascii')
    return cookies[key]


def get_cookie_value(cookie: Morsel) -> str:
    return cookie.value.decode('ascii')


def get_response_cookie_value(rr_cookie, cookie_name) -> str:
    cookie = get_response_cookie(rr_cookie, cookie_name)
    return get_cookie_value(cookie)


def test_csrf_token_set():
    request = make_request()
    result = login_view(request)
    csrf_cookie = get_response_cookie_value(request, csrf_cookie_name)
    assert result['csrf_token'] == csrf_cookie


def test_csrf_token_not_reused():
    original_csrf_token = '00112233445566778899aabbccddeeff'
    request = make_request(cookies={csrf_cookie_name: original_csrf_token})
    result = login_view(request)
    assert result['csrf_token'] != original_csrf_token


@pytest.mark.slow
def test_login_clears_csrf_cookie():
    _, response, value = login('admin', 'admin')
    assert isinstance(value, HTTPFound)
    cookie = get_response_cookie(response, csrf_cookie_name)
    assert cookie.value == b''
    assert cookie.max_age == b'0'


def test_login_view_does_not_create_session():
    request = make_request()
    login_view(request)
    cookies = parse_response_cookies(request)
    assert b'session' not in cookies
    assert 'session' not in cookies


@pytest.mark.functional
class TestLoginApp:

    def test_form(self, app):
        response: Response = app.get('/login')
        assert response.status_code == 200

        body = parse_html_response(response)
        form = body.form
        assert form['autocomplete'] == 'on'
        assert form['method'] == 'post'

        assert form.find(attrs={'name': 'csrf_token'}) is not None

        username = form.find(attrs={'name': 'username'})
        assert username['value'] == ''
        assert username['required'] == ''
        assert username['autocomplete'] == 'username'
        assert username['autofocus'] == ''

        password = form.find(attrs={'name': 'password'})
        assert password['type'] == 'password'
        assert password['required'] == ''
        assert password['autocomplete'] == 'current-password'
        assert not password.get('value')

        assert form.find('button', attrs={'name': 'submit'}) is not None

    @pytest.mark.slow
    def test_submit(self, app: App):
        response: Response = app.get('https://test.com/login')
        assert response.status_code == 200
        assert 'session' not in app.cookies
        assert 'csrf_token' in app.cookies

        params = dict(csrf_token=app.cookies['csrf_token'],
                      username='bosse',
                      password='hemligt',
                      submit='')

        response = app.post('https://test.com/login', params)
        assert response.status_code == 302
        assert response.headers['Location'] == 'https://test.com/'
        assert 'session' in app.cookies
        assert 'csrf_token' not in app.cookies

        response = app.get(response.headers['Location'])
        assert response.status_code == 200
        assert b'<title>Startsida' in response.body

    def test_bad_csrf_token(self, app: App):
        response: Response = app.get('/login')
        assert response.status_code == 200
        assert 'csrf_token' in app.cookies

        params = dict(csrf_token='x', username='y', password='z', submit='')
        response = app.post('/login', params, expect_errors=True)
        assert response.status_code == 400
        assert response.status == '400 Bad CSRF Token'
