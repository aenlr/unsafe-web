import urllib.parse

from pyramid.config import Configurator
from pyramid.security import (
    Allow,
    Authenticated,
)
from pyramid.view import view_config, notfound_view_config

from .embed import embeddable

__all__ = ['main']


class RootContextFactory:
    def __init__(self, request):
        self.request = request

    @property
    def __acl__(self):
        userid = self.request.unauthenticated_userid
        if userid:
            return [
                (Allow, userid, ('view', 'edit'))
            ]
        else:
            return [
                (Allow, Authenticated, 'view')
            ]


@view_config(route_name='index', renderer='templates/index.jinja2')
def index(request):
    return {}


@notfound_view_config(decorator=embeddable, renderer='templates/404.jinja2')
def not_found_view(request):
    return {
        'path': urllib.parse.unquote(request.path)
    }


def main(global_config, **settings):
    config = Configurator(settings=settings)

    # Jinja2 template support
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('unsafe:templates/')

    # Set root context factory that provides a default ACL
    config.set_root_factory(RootContextFactory)

    # Serve static files - in production this is offloaded to nginx
    config.add_static_view(name='static',
                           path='unsafe:static', cache_max_age=0)

    # Base routes
    config.add_route('index', '/')

    # Include modules
    config.include('unsafe.auth')
    config.include('unsafe.db')
    config.include('unsafe.embed')
    config.include('unsafe.filters')
    config.include('unsafe.session')

    # Views
    # config.include('unsafe.admin')
    config.include('unsafe.notes')
    config.include('unsafe.posts')
    config.include('unsafe.topics')

    # Scan annotations
    config.scan()

    return config.make_wsgi_app()
