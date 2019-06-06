from pyramid.request import Request
from pyramid.security import Allow, Everyone
from pyramid.view import view_config

from .app import RootContextFactory
from . import postdb
from . import userdb


class PostsFactory(RootContextFactory):
    __acl__ = [
        (Allow, Everyone, 'view')
    ]

    def __getitem__(self, post_id):
        post = postdb.find_post(self.request.db, post_id)
        if post:
            return PostResource(post)

        raise KeyError(post_id)


class PostResource:
    def __init__(self, post: postdb.Post):
        self.post = post

    @property
    def __acl__(self):
        return [
            (Allow, self.post.user_id, 'edit'),
            (Allow, Everyone, 'view')
        ]


@view_config(route_name='posts', permission='view', renderer='templates/list-posts.jinja2')
def posts_view(request: Request):
    user_id = request.params.get('user')
    search = request.params.get('search', '')
    from_date = request.params.get('from', '')
    to_date = request.params.get('to', '')
    posts = postdb.find_posts(request.db,
                              public=True,
                              user_id=user_id,
                              from_date=from_date,
                              to_date=to_date,
                              search=search)

    unique_userids = set()
    for post in posts:
        post.replies = postdb.find_posts(request.db, reply_to=post.post_id)
        unique_userids.update(reply.user_id for reply in post.replies)
        unique_userids.add(post.user_id)

    users = {user_id: userdb.from_id(request.db, user_id) for user_id in unique_userids}

    return {
        'users': users,
        'posts': posts,
        'from': from_date,
        'to': to_date,
        'search': search
    }


def includeme(config):
    config.add_route('posts', '/posts', factory=PostsFactory)
