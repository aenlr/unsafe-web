from datetime import datetime
from typing import Union

import math
from jinja2 import contextfilter
from pyramid.threadlocal import get_current_request

from . import embed


def abbrev_filter(value: str, maxlen=40):
    """Return the first line of a string abbreviated to ``maxlen`` characters.

    The result will have an ellipsis appended if truncated by leaving out lines
    or truncating the first line.
    """
    if not value:
        return value
    try:
        i = value.index('\n')
        clipped = i + 1 < len(value)
        value = value[:i]
    except ValueError:
        clipped = False

    if value.endswith(':'):
        value = value[:-1]
        clipped = True

    if len(value) > maxlen:
        value = value[0:maxlen]
        clipped = True

    return value + '\u2026' if clipped else value


def since_filter(value: Union[datetime, str]):
    if not value:
        return ''

    if isinstance(value, str):
        dt = datetime.fromisoformat(value)
    else:
        dt = value

    now = datetime.now()
    delta = now - dt
    if delta.days >= 365:
        years = int(math.ceil(delta.days / 365.0))
        return f'{years} år'
    elif delta.days >= 30:
        months = int(math.ceil(delta.days / 30.0))
        return f'{months} månader' if months > 1 else '1 månad'
    elif delta.days > 0:
        return f'{delta.days} dagar' if delta.days > 1 else '1 dag'
    elif delta.seconds >= 3600:
        hours = int(delta.seconds / 3600)
        return f'{hours} timmar' if hours > 1 else '1 timme'
    elif delta.seconds >= 60:
        minutes = int(delta.seconds / 3600)
        return f'{minutes} minuter' if minutes > 1 else '1 minut'
    else:
        return f'{delta.seconds} sekunder'


@contextfilter
def embedded_url_filter(ctx, route_name, *elements, **kw):
    request = ctx.get('request') or get_current_request()
    return embed.embedded_route_url(request, route_name, *elements, **kw)
