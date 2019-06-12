from pyramid.request import Request
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.view import view_config

MENU = [
    {
        'title': 'Allmänt',
        'menu': [
            {'title': 'Cookies', 'topic': 'cookies'},
            {'title': 'Sessioner', 'topic': 'sessions'},
        ]
    },
    {
        'title': 'Sårbarheter',
        'menu': [
            {
                'title': 'Sessionskapning',
                'topic': 'session-hijacking',
                'menu': [
                    {'title': 'Delad dator', 'topic': 'shared-computer'},
                    {'title': 'Delad dator', 'topic': 'shared-computer'},
                ]
            },
            {
                'title': 'SQL-injection',
                'topic': 'sql-injection',
            },

        ]
    },
]


@view_config(route_name='topics', renderer='topics/base.jinja2')
def topics(request: Request):
    return dict(menu=MENU,
                active_page='topics',
                active_topic='',
                title='Sårbarheter')


@view_config(route_name='topic')
def topic(request: Request):
    topic = request.matchdict['topic']
    menu = next(menu
                for section in MENU
                for menu in section['menu']
                if menu['topic'] == topic)

    value = dict(menu=MENU,
                 active_page='topics',
                 active_topic=topic,
                 title=menu['title'])

    renderer_name = f'topics/{topic}.jinja2'
    return render_to_response(renderer_name, value, request)


def includeme(config):
    config.add_route('topics', '/topics')
    config.add_route('topic', '/topics/{topic}')
