from datetime import datetime, timezone
from typing import Union, Dict, Callable, Optional

from dateutil.relativedelta import relativedelta
from pyramid.config import Configurator


def classes_filter(cls, *args, **kw):
    classes = [name for name, value in cls.items() if value]
    classes += args
    classes += [name for name, value in kw.items() if value]
    return ' '.join(classes)


def abbrev_filter(value: str, maxlen=40):
    """Return the first line of a string abbreviated to ``maxlen`` characters.

    The result will have an ellipsis appended if truncated by leaving out lines
    or truncating the first line.
    """
    if not value:
        return value
    try:
        value = value[:value.index('\n')]
    except ValueError:
        pass

    if value.endswith(':'):
        value = value[:-1]
        clipped = True
    else:
        clipped = False

    if len(value) > maxlen:
        value = value[0:maxlen]
        clipped = True

    return value + '\u2026' if clipped else value


def since_filter(value: Union[datetime, str],
                 now: Optional[Union[datetime, str]] = None):
    if not value:
        return ''

    if isinstance(value, str):
        then = datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    else:
        then = value

    if now is None:
        now = datetime.now(tz=timezone.utc)
    elif isinstance(now, str):
        now = datetime.fromisoformat(now).replace(tzinfo=timezone.utc)

    delta = relativedelta(now, then)
    if delta.years:
        return f'{abs(delta.years)} år'
    elif delta.months:
        months = abs(delta.months)
        return f'{months} månader' if months > 1 else '1 månad'
    elif delta.days:
        days = abs(delta.days)
        return f'{days} dagar' if days > 1 else '1 dag'
    elif delta.hours:
        hours = abs(delta.hours)
        return f'{hours} timmar' if hours > 1 else '1 timme'
    elif delta.minutes:
        minutes = abs(delta.minutes)
        return f'{minutes} minuter' if minutes > 1 else '1 minut'
    else:
        seconds = abs(delta.seconds)
        return f'{seconds} sekunder' if seconds != 1 else '1 sekund'


def jinja2_filters() -> Dict[str, Callable]:
    import pyramid_jinja2.filters
    return dict(abbrev=abbrev_filter,
                classes=classes_filter,
                since=since_filter,
                route_url=pyramid_jinja2.filters.route_url_filter,
                static_url=pyramid_jinja2.filters.static_url_filter,
                )


def includeme(config: Configurator):
    config.registry.settings['jinja2.filters'] = jinja2_filters()
