from dataclasses import dataclass
from typing import Optional, List, Union, Any, Tuple

from . import db


@dataclass
class Note:
    note_id: Optional[int]
    user_id: int
    category: str
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __json__(self, *args):
        return vars(self)


def find_notes(conn,
               *,
               user_id: Optional[int] = None,
               from_date: Optional[str] = None,
               to_date: Optional[str] = None,
               category: Optional[str] = None,
               search: Optional[str] = None) -> List[Note]:
    conditions = []
    params: Union[tuple,Tuple[Any]] = ()

    # SQL injection here
    if user_id:
        conditions.append(f'user_id = {user_id}')

    # SQL injection safe
    if from_date:
        conditions.append('updated_at >= ?')
        params += (from_date,)

    # SQL injection
    if to_date:
        conditions.append(f"updated_at <= '{to_date}'")

    # SQL injection
    if category:
        conditions.append(f"category = '{category}'")

    # SQL-injection safe - but does not handle percent in search string
    if search:
        #conditions.append(f"LOWER(content) LIKE '%{search.lower()}%'")
        conditions.append(f"LOWER(content) LIKE ?")
        params += (f'%{search.lower()}%',)

    sql = ('SELECT note_id, user_id, category, content, created_at, updated_at'
           ' FROM note' +  # noqa
           ' WHERE ' + ' AND '.join(conditions) + ' ORDER BY updated_at DESC')

    with db.cursor(conn) as cur:
        return db.fetchall(cur, Note, sql, params)


def _find_note(cur, note_id):
    # SQL injection here
    return db.fetchone(cur, Note,
                       f'SELECT note_id, user_id, category, content,'
                       f' created_at, updated_at'
                       f' FROM note WHERE note_id = {note_id}',
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
        if note.note_id:
            cur.execute(
                'UPDATE note'
                ' SET content = ?, category = ?,updated_at = CURRENT_TIMESTAMP'
                ' WHERE note_id = ?',
                (note.content, note.category, note.note_id))
        else:
            cur.execute('INSERT INTO note(user_id, content, category)'
                        'VALUES(?, ?, ?)',
                        (note.user_id, note.content, note.category))
            note.note_id = cur.lastrowid
        new_note = _find_note(cur, note.note_id)

    return new_note
