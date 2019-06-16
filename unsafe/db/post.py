from dataclasses import dataclass
from typing import Optional, List, Union, Any, Tuple

from . import db


@dataclass
class Post:
    post_id: Optional[int]
    user_id: int
    content: str
    reply_to: Optional[int] = None
    likes: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __json__(self, *args):
        return vars(self)


def find_posts(conn,
               *,
               user_id: Optional[int] = None,
               reply_to: Optional[Union[int, bool]] = None,
               from_date: Optional[str] = None,
               to_date: Optional[str] = None,
               search: Optional[str] = None) -> List[Post]:
    conditions = []
    params: Union[tuple,Tuple[Any]] = ()

    if reply_to is None:
        conditions.append('reply_to IS NULL')
    elif reply_to is not False:
        conditions.append('reply_to = ?')
        params += (reply_to,)

    if user_id:
        conditions.append(f'user_id = ?')
        params += (user_id,)

    if from_date:
        conditions.append('updated_at >= ?')
        params += (from_date,)

    if to_date:
        conditions.append(f"updated_at <= ?")
        params += (to_date,)

    # SQL-injection safe - but does not handle percent in search string
    if search:
        conditions.append(f"LOWER(content) LIKE ?")
        params += (f'%{search.lower()}%',)

    sql = ('SELECT post_id, user_id, reply_to, content, likes,'
           ' created_at, updated_at'
           ' FROM post' +  # noqa
           ' WHERE ' + ' AND '.join(conditions) + ' ORDER BY updated_at DESC')

    with db.cursor(conn) as cur:
        return db.fetchall(cur, Post, sql, params)


def _find_post(cur, post_id):
    return db.fetchone(cur, Post,
                       f'SELECT post_id, user_id, reply_to, content, likes,'
                       f' created_at, updated_at'
                       f' FROM post WHERE post_id = ?',
                       (post_id,))


def find_post(conn, post_id) -> Optional[Post]:
    with db.cursor(conn) as cur:
        return _find_post(cur, post_id)


def delete_post(conn, post_id):
    with db.cursor(conn) as cur:
        cur.execute(f'DELETE from post WHERE post_id = ?', (post_id,))


def save_post(conn, post: Post) -> Post:
    with db.cursor(conn) as cur:
        if post.post_id:
            cur.execute(
                'UPDATE post SET content = ?, updated_at = CURRENT_TIMESTAMP '
                'WHERE post_id = ?',
                (post.content, post.post_id))
        else:
            cur.execute('INSERT INTO post(user_id, reply_to, content)'
                        'VALUES(?, ?, ?)',
                        (post.user_id, post.reply_to, post.content))
            post.post_id = cur.lastrowid
        new_post = _find_post(cur, post.post_id)

    return new_post


def like_post(conn, post_id) -> Post:
    with db.cursor(conn) as cur:
        cur.execute('UPDATE post SET likes = likes + 1 WHERE post_id = ?',
                    (post_id,))
        return _find_post(cur, post_id)
