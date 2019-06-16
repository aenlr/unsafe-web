from passlib.context import CryptContext

from dataclasses import dataclass
from typing import Optional, Union, List

from . import db

pwdctx = CryptContext(
    # Supported password/hashing schemes in priority
    schemes=[
        # 'argon2',
        'bcrypt',
        'pbkdf2_sha512',
        'pbkdf2_sha256',
        'plaintext'
    ],

    # Automatically mark all but first hasher in list as deprecated.
    deprecated='auto',

    # Optionally, set the number of rounds that should be used.
    pbkdf2_sha512__rounds=100000,
    pbkdf2_sha256__rounds=200000
)


@dataclass
class User:
    """User details"""
    user_id: int
    username: str
    email: Optional[str]
    password: str
    groups: List[str]

    def __post_init__(self):
        if isinstance(self.groups, str):
            self.groups = self.groups.split()


class UserNotFoundError(Exception):
    """Error raised when a user expected to exist does not exist."""


class UserExistsError(Exception):
    """Error raised when a user already exists."""


def from_username(conn, username: str) -> Optional[User]:
    """Find user by username, returning None if there is no such user"""

    with db.cursor(conn) as cur:
        return db.fetchone(cur, User,
                           'SELECT user_id, username, password, email, groups '
                           'FROM user WHERE username = ?',
                           (username,))


def from_id(conn, user_id: int) -> User:
    """Lookup user by id.

    Returns a :class:`User` object if `user_id` is valid,
    otherwise raises :exc:`UserNotFoundError`.
    """

    with db.cursor(conn) as cur:
        user = db.fetchone(cur, User,
                           'SELECT user_id, username, password, email, groups '
                           'FROM user WHERE user_id = ?',
                           (user_id,))
        if not user:
            raise UserNotFoundError('Invalid user id')
        return user


def authenticate(conn,
                 username: str,
                 password: Union[str, bytes]) -> Optional[User]:
    """User password authentication.

    :arg username:
        Name of user to check.

    :arg password:
        Password to verify.

    :returns:
        A :class:`User` object if the username and password are correct,
        otherwise ``None``.
    """

    user = from_username(conn, username)
    if not user:
        return None

    valid, new_hash = pwdctx.verify_and_update(password, user.password)
    if not valid:
        return None

    if new_hash:
        # The stored hash is using a deprecated algorithm.
        # Replace the hash with using the preferred algorithm.
        _replace_user_hash(conn, user.user_id, new_hash)
        user.password = new_hash

    return user


def _replace_user_hash(conn, user_id, new_hash):
    with db.cursor(conn) as cur:
        cur.execute('UPDATE user SET password = ? WHERE user_id = ?',
                    (new_hash, user_id))


def create(conn,
           username: str,
           password: Union[str, bytes], email: Optional[str] = None,
           groups: List[str] = None) -> User:
    """Create a new user.

    The password is hashed by according to the default password scheme before
    being stored.

    :arg username:
        Name of user the new user. The name must be available.

    :arg password:
        User password as cleartext.

    :arg email:
        User email address.

    :arg groups:
        List of groups.

    :returns:
        Newly created :class:`User`.

    :raises UserExistsError:
        If ``username`` is already in use.
    """

    user = from_username(conn, username)
    if user:
        raise UserExistsError()

    hash = pwdctx.hash(password)
    groups_value = ' '.join(groups) if groups else ''
    with db.cursor(conn) as cur:
        cur.execute('INSERT INTO user(username, password, email, groups)'
                    'VALUES(?,?,?,?)',
                    (username, hash, email, groups_value))
        user_id = cur.lastrowid

    return User(user_id=user_id,
                username=username,
                password=hash,
                email=email,
                groups=groups or [])
