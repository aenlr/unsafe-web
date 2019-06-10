import os

import pytest
from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.testing import DummyRequest
from webob.cookies import Cookie, Morsel
from webtest import TestApp

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
        except FileNotFoundError:
            pass

    db.init(DBNAME_APP)


@pytest.fixture()
def app() -> TestApp:
    global_config = {}
    settings = {
        'db.app': DBNAME_APP,
        'db.sessions': DBNAME_SESSIONS
    }

    wsgi_app = unsafe.app.main(global_config, **settings)
    return TestApp(wsgi_app)


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
    request._process_response_callbacks(response)
    return response


def parse_response_cookies(request_or_response) -> Cookie:
    try:
        response = make_response(request_or_response)
    except AttributeError:
        response = request_or_response

    headers = response.headers.getall('Set-Cookie')
    return Cookie('\r\n'.join(headers))


def get_response_cookie(rr_cookie, cookie_name) -> Morsel:
    if isinstance(rr_cookie, Cookie):
        cookies = rr_cookie
    else:
        cookies = parse_response_cookies(rr_cookie)
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
