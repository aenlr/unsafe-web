from dataclasses import dataclass
from typing import Optional, List

from . import db


@dataclass
class Note:
    note_id: Optional[int]
    user_id: int
    content: str
    created_at: str = None
    updated_at: str = None


def find_notes(conn, user_id, from_date=None, to_date=None, search: Optional[str] = None) -> List[Note]:
    sql = 'SELECT note_id, user_id, content, created_at, updated_at FROM note WHERE user_id = ?'
    params = (user_id,)

    if search:
        # SQL-injection safe - but does not handle percent in search string
        sql += f" AND lower(content) LIKE ?"
        params += (f'%{search.lower()}%',)

    # SQL injection here
    if from_date:
        sql += f" AND updated_at >= '{from_date}'"

    if to_date:
        sql += f" AND updated_at <= '{to_date}'"

    sql += ' ORDER BY updated_at DESC'

    with db.cursor(conn) as cur:
        return db.fetchlist(cur, Note, sql, params)


def _find_note(cur, note_id):
    # SQL injection here
    return db.fetchone(cur, Note,
                       f'SELECT note_id, user_id, content, created_at, updated_at FROM note WHERE note_id = {note_id}',
                       ())


def find_note(conn, note_id) -> Optional[Note]:
    with db.cursor(conn) as cur:
        return _find_note(cur, note_id)


def delete_note(conn, note_id):
    with db.cursor(conn) as cur:
        # SQL injection here
        cur.execute(f'DELETE from note WHERE note_id = {note_id}')


def save_note(conn, note: Note) -> Note:
    with db.cursor(conn) as cur:
        # Safe from SQL injection
        if note.note_id:
            cur.execute('UPDATE note SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE note_id = ?',
                        (note.content, note.note_id))
        else:
            cur.execute('INSERT INTO note (content, user_id) VALUES(?, ?)',
                        (note.content, note.user_id))
            note.note_id = cur.lastrowid
        new_note = _find_note(cur, note.note_id)

    return new_note
