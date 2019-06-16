from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.response import Response


def embedded_route_url(request: Request, route_name, *elements, **kw):
    if request.embedded:
        query = kw.get('_query', None)
        if not query:
            query = 'embedded'
        elif isinstance(query, str):
            query += '&embedded'
        else:
            try:
                items = query.items()
                query = dict(items)
                query['embedded'] = ''
            except AttributeError:
                query = list(query)
                query.append(('embedded', ''))

        kw['_query'] = query
    return request.route_url(request, route_name, *elements, **kw)


def embeddable(view_callable):
    def inner(context, request):
        response: Response = view_callable(context, request)
        location = response.location
        if location and request.embedded:
            if '?' in location:
                location += '&embedded'
            else:
                location += '?embedded'
            response.location = location
        return response

    return inner


_truthy = ('True', 'true', '1', '')


def _check_view(request: Request):
    embedded: str = request.params.get('embedded')
    return embedded in _truthy


def includeme(config: Configurator):
    config.add_request_method(_check_view, name='embedded', reify=True)
    config.add_request_method(embedded_route_url, name='embedded_url')
