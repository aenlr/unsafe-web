from pyramid.request import Request
from pyramid.view import view_config


@view_config(route_name='topics', renderer='topics/sql-injection.jinja2')
def topics(request: Request):
    return {
    }


def includeme(config):
    config.add_route('topics', '/topics')
