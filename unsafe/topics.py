from pyramid.httpexceptions import HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.request import Request
from pyramid.view import view_config

MENU = [
    {
        'title': 'Allmänt',
        'menu': [
            {
                'title': 'HTTPS',
                'topic': 'https',
                'menu': [
                    {'title': 'Certifikat', 'topic': 'certificates'},
                    {'title': 'Strict Transport Security', 'topic': 'hsts'},
                ]
            },
            {
                'title': 'Cookies',
                'topic': 'cookies',
                'menu': [
                    {'title': 'HttpOnly', 'topic': 'httponly'},
                    {'title': 'Secure', 'topic': 'secure'},
                    {'title': 'SameSite', 'topic': 'samesite'},
                ]
            },
        ]
    },
    {
        'title': 'Sårbarheter',
        'menu': [
            {
                'title': 'Sessioner',
                'topic': 'sessions',
                'menu': [
                    {'title': 'URL:er', 'topic': 'urls'},
                    {'title': 'XSS', 'topic': 'xss'},
                    {'title': 'Osäker förbindelse', 'topic': 'nohttps'},
                    {'title': 'Delad dator', 'topic': 'shared-computer'},
                ]
            },
            {
                'title': 'Cross Site Request Forgery (CSRF)',
                'topic': 'csrf'
            },
            {
                'title': 'Cross Site Scripting (XSS)',
                'topic': 'xss'
            },
            {
                'title': 'SQL Injection',
                'topic': 'sql-injection',
            },
            {
                'title': 'Lösenord',
                'topic': 'passwords',
            },
        ]
    },
]


@view_config(route_name='topics', renderer='topics/base.jinja2')
def topics(request):
    return dict(menu=MENU,
                active_page='topics',
                active_topic='',
                title='Säkerhet')


@view_config(route_name='topic')
def topic_view(request: Request):
    topic = request.matchdict['topic']
    try:
        active_menu = next(menu
                           for section in MENU
                           for menu in section['menu']
                           if menu['topic'] == topic)
    except StopIteration:
        raise HTTPNotFound()

    value = dict(menu=MENU,
                 active_page='topics',
                 active_topic=topic,
                 title=active_menu['title'])

    renderer_name = f'topics/{topic}.jinja2'
    return render_to_response(renderer_name, value, request)


def includeme(config):
    config.add_route('topics', '/topics')
    config.add_route('topic', '/topics/{topic}')
