import os
import pytest

import unsafe
from unsafe import db
from unsafe import userdb

test_databasename = 'users-test.db'


def setup_module(module):
    global original_database

    try:
        os.remove(test_databasename)
    except FileNotFoundError:
        pass

    sql_path = os.path.join(unsafe.__path__[0], 'sql')
    with db.connection(test_databasename) as conn:
        for script in ['db-create.sql', 'db-init.sql']:
            script_path = os.path.join(sql_path, script)
            with open(script_path) as f:
                script = f.read()
                conn.executescript(script)



@pytest.fixture
def conn():
    c = db.connect(test_databasename)
    yield c
    c.close()


def test_create(conn):
    user = userdb.create(conn, 'bob', 'secret', 'bob@example.com', False)
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
