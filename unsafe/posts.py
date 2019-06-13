import hmac

from pyramid.csrf import get_csrf_token
from pyramid.exceptions import BadCSRFToken
from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.security import Allow, Everyone, Authenticated
from pyramid.view import view_config

from . import db
from .app import RootContextFactory


class PostsFactory(RootContextFactory):
    __acl__ = [
        (Allow, Everyone, 'view')
    ]

    def __getitem__(self, post_id):
        post = db.post.find_post(self.request.db, post_id)
        if post:
            return PostResource(post)

        raise KeyError(post_id)


class PostResource:
    def __init__(self, post: db.post.Post):
        self.post = post

    @property
    def __acl__(self):
        return [
            (Allow, self.post.user_id, 'edit'),
            (Allow, Authenticated, ('like', 'reply')),
            (Allow, Everyone, 'view')
        ]


@view_config(route_name='posts', permission='view', renderer='posts/list-posts.jinja2')
def posts_listing(request: Request):
    """Main posts listing"""
    user_id = request.params.get('user')
    search = request.params.get('search', '')
    from_date = request.params.get('from', '')
    to_date = request.params.get('to', '')
    posts = db.post.find_posts(request.db,
                               public=True,
                               user_id=user_id,
                               from_date=from_date,
                               to_date=to_date,
                               search=search)

    unique_userids = set()
    for post in posts:
        post.replies = db.post.find_posts(request.db, reply_to=post.post_id)
        unique_userids.update(reply.user_id for reply in post.replies)
        unique_userids.add(post.user_id)

    users = {user_id: db.user.from_id(request.db, user_id) for user_id in unique_userids}

    return {
        'users': users,
        'posts': posts,
        'from': from_date,
        'to': to_date,
        'search': search
    }


@view_config(route_name='post', permission='like', renderer='json',
             request_method='POST',
             header='Content-Type:application/json',
             accept='application/json',
             # require_csrf=True
             )
def like_post_json(context: PostResource, request):
    """ JSON `like` action.

    This action is CSRF-safe thanks to:

    - Requires a POST
    - Browser form submission cannot post JSON (only ``application/x-www-form-urlencoded``)
    - CORS/SOP prevent scripts on `external pages` from posting unless a CORS policy allows it.

    Abbreviations:

    - CORS = Cross-Origin Resource Sharing
    - SOP = Same Origin Policy
    """

    request_body: dict = request.json_body

    # In case there is a CORS policy in place we also require the CSRF token
    # to be included in the JSON request.
    #
    # We can get the same effect by setting require_csrf=True which will require
    # the request to include an X-CSRF-Token header.
    #
    # Calling pyramid.csrf.check_csrf_token would also achieve the same thing by checking the X-CSRF-Token header.
    csrf_token = request_body.get('csrf_token', '')
    expected_csrf_token = get_csrf_token(request)
    if not hmac.compare_digest(csrf_token, expected_csrf_token):
        raise BadCSRFToken()

    post = db.post.like_post(request.db, context.post.post_id)
    return post


@view_config(route_name='post', permission='like',
             request_param='action=like',
             request_method='POST',
             header='Content-Type:application/x-www-form-urlencoded',
             # require_csrf=True
             )
def like_post(context: PostResource, request):
    """ Form-based `like` action.

    Make unsafe by removing constraints:

    - ``request_method='POST'`` requires that the request is a POST, avoiding destructive drive-by GET requests
    - ``require_csrf=True`` checks csrf_token in the request body or an X-CSRF-Token header (which is not possible for
    browser generated form submissions) against the expected CSRF token.
    """
    db.post.like_post(request.db, context.post.post_id)
    return HTTPFound(request.current_request_url)


def includeme(config):
    config.add_route('posts', '/posts', factory=PostsFactory)
    config.add_route('post', pattern='/posts/{post}', traverse='/{post}', factory=PostsFactory)
    config.add_route('like-post', pattern='/posts/{post}/like', traverse='/{post}', factory=PostsFactory)
