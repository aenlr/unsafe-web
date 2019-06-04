import sqlite3
from contextlib import contextmanager
from typing import Iterator, Type, Union


def connect(database: str, **kwargs):
    conn = sqlite3.connect(database, **kwargs)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


@contextmanager
def cursor(db: Union[str, sqlite3.Connection], commit=None) -> Iterator[sqlite3.Cursor]:
    """
    Create a cursor and close it after use.

    :param db: An existing connection or a database name
    :param commit: if True, commit transaction after successful execution
    """

    if isinstance(db, str):
        conn = connect(db)
        if commit is None:
            commit = True
        try:
            cur = conn.cursor()
            yield cur
            if commit:
                conn.commit()
            cur.close()
        finally:
            conn.close()
    else:
        conn = db
        cur = conn.cursor()
        try:
            yield cur
            if commit:
                conn.commit()
        finally:
            cur.close()


@contextmanager
def connection(database: str, commit=True, **kwargs) -> sqlite3.Connection:
    """
    Connect to database and return connection.

    :param database: name of database file
    :param commit: if True, commit transaction after successful execution of the with body
    """
    conn = connect(database, **kwargs)
    try:
        yield conn
        if commit:
            conn.commit()
    finally:
        conn.close()


def maprow(mapping: Type, row: sqlite3.Row):
    vals = {k: row[k] for k in row.keys()}
    return mapping(**vals)


def fetchone(cur: sqlite3.Cursor, mapping: Type, select: str, params: tuple):
    cur.execute(select, params)
    row = cur.fetchone()
    if row:
        return maprow(mapping, row)


def fetchlist(cur: sqlite3.Cursor, mapping: Type, select: str, params: tuple):
    cur.execute(select, params)
    rows = cur.fetchall()
    return [maprow(mapping, row) for row in rows]
