"""
Simple session store example.

There are settings to introduce security vulnerabilties for demonstration
purposes.

Setting ``secret`` to *None* disables cookie signing.

Setting ``query_param`` allows setting the session id with a query parameter.

Setting ``accept_client_session_id`` to *True* accepts session ids that were
not generated by the server (or session that have been deleted).
"""
import json
import os
import time
from typing import Optional
import datetime

from pyramid.config import Configurator
from pyramid.interfaces import ISession
from webob.cookies import SignedSerializer
from zope.interface import implementer

from . import db


def MySessionFactory(secret: str,
                     *,
                     hashalg='sha512',
                     salt='pyramid.session.',
                     cookie_name='session',
                     path='/',
                     domain: Optional[str] = None,
                     database='sessions.db',
                     timeout=1200,
                     samesite='Lax',
                     httponly=False,
                     secure=False,
                     query_param: Optional[str] = None,
                     accept_client_session_id=False
                     ):
    """
    Configure a :term:`session factory` which will provide a sqlite-backed
    session store.

    The return value of this function is a :term:`session factory`, which may
    be provided as the ``session_factory`` argument of a :class:`pyramid.config.Configurator`
    constructor, or used as the ``session_factory`` argument of the
    :meth:`pyramid.config.Configurator.set_session_factory` method.

    Parameters:

    ``secret``
      A string which is used to sign the cookie. The secret should be at
      least as long as the block size of the selected hash algorithm. For
      ``sha512`` this would mean a 512 bit (64 character) secret.  It should
      be unique within the set of secret values provided to Pyramid for
      its various subsystems (see :ref:`admonishment_against_secret_sharing`).

    ``hashalg``
      The HMAC digest algorithm to use for signing. The algorithm must be
      supported by the :mod:`hashlib` library. Default: ``'sha512'``.

    ``salt``
      A namespace to avoid collisions between different uses of a shared
      secret. Reusing a secret for different parts of an application is
      strongly discouraged (see :ref:`admonishment_against_secret_sharing`).
      Default: ``'pyramid.session.'``.

    ``cookie_name``
      The name of the cookie used for sessioning. Default: ``'session'``.

    ``path``
      The path used for the session cookie. Default: ``'/'``.

    ``domain``
      The domain used for the session cookie.  Default: ``None`` (no domain).

    ``secure``
      The 'secure' flag of the session cookie.

    ``httponly``
      Hide the cookie from Javascript by setting the 'HttpOnly' flag of the
      session cookie..

    ``samesite``
      The 'samesite' option of the session cookie. Set the value to ``None``
      to turn off the samesite option.  Default: ``'Lax'``.

    ``timeout``
      A number of seconds of inactivity before a session times out.
      Default: ``1200``.

    """

    # Create database and session_store table if needed
    with db.cursor(database) as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS session_store (
                session_id TEXT PRIMARY KEY,
                expires_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                userdata TEXT NOT NULL
                );
            ''')

    if secret:
        cookie_serializer = SignedSerializer(secret, salt=salt,
                                             hashalg=hashalg)
    else:
        cookie_serializer = IdentityCookieSerializer()

    return _session_factory(cookie_serializer=cookie_serializer,
                            cookie_name=cookie_name,
                            path=path,
                            domain=domain,
                            database=database,
                            timeout=timeout,
                            samesite=samesite,
                            httponly=httponly,
                            secure=secure,
                            query_param=query_param,
                            accept_client_session_id=accept_client_session_id)


def purge_sessions(database='sessions.db'):
    with db.cursor(database) as cur:
        now = int(time.time())
        cur.execute('DELETE FROM session_store WHERE expires_at >= ?', (now,))
        return cur.rowcount


def remove_sessions(session_ids, database='sessions.db'):
    with db.cursor(database) as cur:
        cur.executemany('DELETE FROM session_store WHERE session_id = ?',
                        (session_ids,))
        return cur.rowcount


def expire_sessions(expiry_time=None, database='sessions.db'):
    with db.cursor(database) as cur:
        if expiry_time is None:
            expiry_time = time.time()
        elif isinstance(expiry_time, datetime.date):
            expiry_time = time.mktime(expiry_time.timetuple())
        elif isinstance(expiry_time, str):
            dt = datetime.datetime.fromisoformat(expiry_time)
            expiry_time = time.mktime(dt.timetuple())
        elif not isinstance(expiry_time, (int, float)):
            raise ValueError()
        expiry_time = int(expiry_time)
        cur.execute('DELETE FROM session_store WHERE expires_at >= ?',
                    (expiry_time,))
        return cur.rowcount


class IdentityCookieSerializer:
    def dumps(self, x):
        return x

    def loads(self, x):
        return x


def _session_factory(*,
                     cookie_serializer: SignedSerializer,
                     cookie_name: str,
                     path: str,
                     domain: Optional[str],
                     database: str,
                     timeout: int,
                     samesite: str,
                     httponly: bool,
                     secure: bool,
                     query_param: Optional[str],
                     accept_client_session_id: bool
                     ):
    def new_expiry_time():
        return int(time.time()) + timeout

    def new_session_id():
        return os.urandom(16).hex()

    def set_session_cookie(request, response, val, max_age=None):
        cookie_secure = request.scheme == 'https' if secure is None else secure
        response.set_cookie(
            cookie_name,
            value=val,
            path=path,
            domain=domain,
            secure=cookie_secure,
            httponly=httponly,
            samesite=samesite,
            max_age=max_age)

    @implementer(ISession)
    class MySession(dict):

        def __init__(self, request):
            super().__init__()

            self._session_id = None

            # DO NOT put session ids in the URL or body.
            #
            if query_param in request.params:
                self._session_id = request.params.get(cookie_name)
            else:
                cookie_val: str = request.cookies.get(cookie_name)
                if cookie_val:
                    try:
                        self._session_id = cookie_serializer.loads(cookie_val)
                    except ValueError:
                        # Signature check failed
                        pass

            self._dirty = False
            self._created = None
            self._expires = None
            self._accessed = False
            self._loaded = self._session_id is None
            self._new = self._session_id is None
            self._reset_cookie = False

            request.add_response_callback(self._save)

        @property
        def created(self) -> int:
            """Integer representing Epoch time when the session was created."""

            self._load()
            if not self._created:
                self._created = int(time.time())
            return self._created

        @property
        def new(self):
            """If ``True``, the session is new."""
            self._load()
            return self._new

        def invalidate(self):
            """ Invalidate the session.
            Delete persistent session data, invalidate session id and reset
            the session object to new state.

            An invalidated session may be used after the call to ``invalidate``
            with the effect that a new session is created to store the data.
            This enables workflows requiring an entirely new session, such as
            in the case of changing privilege levels or preventing fixation
            attacks.
            """
            if self._session_id:
                with db.cursor(database) as cur:
                    self._delete_session(cur)

            super().clear()
            self._accessed = False
            self._dirty = False
            self._created = None
            self._expires = None
            self._loaded = True
            self._new = True

        def changed(self):
            """ Mark the session as changed. A user of a session should
            call this method after he or she mutates a mutable object that
            is *a value of the session* (it should not be required after
            mutating the session itself).  For example, if the user has
            stored a dictionary in the session under the key ``foo``, and
            he or she does ``session['foo'] = {}``, ``changed()`` needn't
            be called.  However, if subsequently he or she does
            ``session['foo']['a'] = 1``, ``changed()`` must be called for
            the sessioning machinery to notice the mutation of the
            internal dictionary."""
            self._load()
            if not self._dirty:
                self._accessed = True
                self._dirty = True
                if not self._created:
                    self._created = int(time.time())

        def _save(self, request, response):
            """Response callback to persist session data and manages cookies"""
            if self._dirty:
                if self._new:
                    self._store_new_session(request, response)
                else:
                    self._store_modified_session()
            elif self._reset_cookie:
                set_session_cookie(request, response, '', 0)
            elif self._accessed:
                self._update_expiry_time()

        def _store_new_session(self, request, response):
            """Persist session data and set session cookie"""
            if not self._session_id:
                self._session_id = new_session_id()
            expires_at = new_expiry_time()
            userdata = json.dumps(self)
            with db.cursor(database) as cur:
                cur.execute('INSERT INTO session_store'
                            '(session_id, expires_at, created_at, userdata)'
                            'VALUES (?, ?, ?, ?)',
                            (self._session_id, expires_at, self._created,
                             userdata))

            cookie_val = cookie_serializer.dumps(self._session_id)
            set_session_cookie(request, response, cookie_val)

        def _store_modified_session(self):
            """Persist modified session data and update expiry time"""
            expires_at = new_expiry_time()
            userdata = json.dumps(self)
            with db.cursor(database) as cur:
                cur.execute(
                    'UPDATE session_store SET expires_at = ?, userdata = ?'
                    'WHERE session_id = ?',
                    (expires_at, userdata, self._session_id))

        def _update_expiry_time(self):
            """Update expiry time for session"""
            expires_at = new_expiry_time()
            with db.cursor(database) as cur:
                cur.execute(
                    'UPDATE session_store SET expires_at = ? '
                    'WHERE session_id = ?',
                    (expires_at, self._session_id))

        def _load(self):
            """Load session state from sqlite database if not yet loaded"""
            if not self._loaded:
                self._loaded = True
                with db.cursor(database) as cur:
                    cur.execute(
                        'SELECT expires_at, created_at, userdata'
                        ' FROM session_store WHERE session_id = ?',
                        (self._session_id,))
                    row = cur.fetchone()
                    if row and time.time() < row[0]:
                        # Existing non-expired session
                        self._created = int(row[1])
                        self._reset_cookie = False
                        userdata = json.loads(row[2])
                        self._update(userdata)
                    else:
                        # Non-existing or expired session
                        if accept_client_session_id:
                            # Using client session id --> session fixation
                            self._created = int(time.time())
                            self._new = row is None
                            self._reset_cookie = False
                        else:
                            self._delete_session(cur)
                            self.invalidate()

        def _update(self, values):
            # Avoid triggering changed() which is called as a side-effect
            # of self.update() or self[key] = val.
            _dict_setitem = dict.__setitem__
            for k, v in values.items():
                _dict_setitem(self, k, v)

        def _delete_session(self, cur):
            """Delete session state using the given database cursor"""
            if self._session_id:
                cur.execute('DELETE FROM session_store WHERE session_id = ?',
                            (self._session_id,))
                self._session_id = None
                self._reset_cookie = True

        get = manage_accessed(dict.get)
        __getitem__ = manage_accessed(dict.__getitem__)
        items = manage_accessed(dict.items)
        values = manage_accessed(dict.values)
        keys = manage_accessed(dict.keys)
        __contains__ = manage_accessed(dict.__contains__)
        __iter__ = manage_accessed(dict.__iter__)
        # __eq__ = manage_accessed(dict.__eq__)

        clear = manage_changed(dict.clear)
        update = manage_changed(dict.update)
        setdefault = manage_changed(dict.setdefault)
        pop = manage_changed(dict.pop)
        popitem = manage_changed(dict.popitem)
        __setitem__ = manage_changed(dict.__setitem__)
        __delitem__ = manage_changed(dict.__delitem__)

    return MySession


def manage_accessed(wrapped):
    """Wrap a dict accessor to update the session access flag"""

    def accessed(session, *arg, **kw):
        if not session._accessed:
            session._load()
            session._accessed = True
        return wrapped(session, *arg, **kw)

    accessed.__doc__ = wrapped.__doc__
    return accessed


def manage_changed(wrapped):
    """Wrap a dict mutator to update session dirty flags and creation time"""

    def changed(session, *arg, **kw):
        session.changed()
        return wrapped(session, *arg, **kw)

    changed.__doc__ = wrapped.__doc__
    return changed


def includeme(config: Configurator):
    from pyramid.csrf import SessionCSRFStoragePolicy

    session_dbname = os.path.normpath(
        config.registry.settings.get('db.sessions', 'sessions.db'))
    session_secret = os.environ.get('UNSAFE_SESSION_SECRET', 'secret')
    session_factory = MySessionFactory(
        database=session_dbname,
        secret=session_secret,
        # secret=None, # No cookie signing!
        httponly=True,
        # samesite='Strict',
        # secure=True,
        # query_param='session',
        accept_client_session_id=False)
    config.set_session_factory(session_factory)
    config.set_csrf_storage_policy(SessionCSRFStoragePolicy())
