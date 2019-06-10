import os
import pytest

import unsafe.db as db
import unsafe.db.user as userdb

DBNAME = 'test-users.db'


def setup_module(module):
    global original_database

    try:
        os.remove(DBNAME)
    except FileNotFoundError:
        pass

    db.init(DBNAME)


@pytest.fixture
def conn():
    c = db.connect(DBNAME)
    yield c
    c.close()


def test_create(conn):
    user = userdb.create(conn, 'bob', 'secret', 'bob@example.com')
    assert user.user_id is not None
    assert user.username == 'bob'
    assert user.password is not None
    assert user.password != 'secret'
    assert user.admin is False


def test_from_username(conn):
    user = userdb.from_username(conn, 'joe')
    assert user.user_id
    assert user.username == 'joe'
    assert user.password.startswith('$2b$')
    assert user.admin is False


def test_from_id(conn):
    user = userdb.from_id(conn, 1)
    assert user.user_id == 1
    assert user.username == 'admin'
    assert user.password == 'admin'
    assert 'admin' in user.groups


def test_from_id_raises(conn):
    with pytest.raises(userdb.UserNotFoundError):
        userdb.from_id(conn, -1)


def test_authenticate(conn):
    user = userdb.authenticate(conn, 'joe', 'joe123')
    assert user is not None
    assert user.user_id
    assert user.username == 'joe'
    assert user.password.startswith('$2b$')
    assert user.groups == ['author']


def test_authenticate_failure(conn):
    user = userdb.authenticate(conn, 'joe', 'Joe123')
    assert user is None


def test_authenticate_update_hash(conn):
    user = userdb.from_username(conn, 'bosse')
    assert user.password == 'hemligt'

    user2 = userdb.authenticate(conn, 'bosse', 'hemligt')
    assert user2 is not None
    assert user2.password != 'hemligt'

    user3 = userdb.from_username(conn, 'bosse')
    assert user3 is not None
    assert user3.password == user2.password
