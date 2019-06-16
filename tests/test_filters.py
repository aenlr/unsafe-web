from unsafe.filters import since_filter
from datetime import datetime, timedelta


def test_since_empty():
    assert since_filter('') == ''


def test_since_datetime():
    now = datetime.now()
    then = now - timedelta(seconds=1)
    assert since_filter(now, then) == '1 sekund'


def test_since_year():
    assert since_filter('2019-01-01', '2020-01-01') == '1 år'


def test_since_years():
    assert since_filter('2018-01-01', '2020-01-01') == '2 år'


def test_since_month():
    assert since_filter('2016-01-28', '2016-02-28') == '1 månad'
    assert since_filter('2016-01-28', '2016-02-29') == '1 månad'
    assert since_filter('2016-01-01', '2016-02-01') == '1 månad'


def test_since_months():
    assert since_filter('2015-11-28', '2016-02-29') == '3 månader'
    assert since_filter('2015-12-28', '2016-02-28') == '2 månader'
    assert since_filter('2015-12-28', '2016-02-29') == '2 månader'
    assert since_filter('2019-03-01', '2019-05-01') == '2 månader'


def test_since_day():
    assert since_filter('2016-02-29', '2016-03-01') == '1 dag'
    assert since_filter('2019-02-01', '2019-02-02') == '1 dag'


def test_since_days():
    assert since_filter('2019-02-01', '2019-02-28') == '27 dagar'
    assert since_filter('2016-02-01', '2016-02-29') == '28 dagar'


def test_since_hour():
    assert since_filter('2019-01-01 13:14:15', '2019-01-01 14:14:15') == '1 timme'
    assert since_filter('2019-01-01 13:14:15', '2019-01-01 14:14:16') == '1 timme'
    assert since_filter('2019-01-01 13:14:15', '2019-01-01 14:15:16') == '1 timme'


def test_since_hours():
    assert since_filter('2019-01-01 13:14:15', '2019-01-01 15:14:15') == '2 timmar'


def test_since_minute():
    assert since_filter('2019-01-01 13:14:00', '2019-01-01 13:15:00') == '1 minut'
    assert since_filter('2019-01-01 13:14:00', '2019-01-01 13:15:59') == '1 minut'


def test_since_minutes():
    assert since_filter('2019-01-01 13:14:00', '2019-01-01 13:16:00') == '2 minuter'


def test_since_second():
    assert since_filter('2019-01-01 13:14:00', '2019-01-01 13:14:01') == '1 sekund'


def test_since_seconds():
    assert since_filter('2019-01-01 13:14:00', '2019-01-01 13:14:00') == '0 sekunder'
    assert since_filter('2019-01-01 13:14:00', '2019-01-01 13:14:02') == '2 sekunder'
