# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from pytz import timezone as pytz_timezone
from zoneinfo import ZoneInfo


def default_timezone(request):
    return 'Europe/Berlin'


def default_tzinfo(request):
    return ZoneInfo(default_timezone(request))


def utc_to_timezone(request, datetime, timezone=''):
    timezone = timezone or default_timezone(request)
    return datetime.astimezone(pytz_timezone(timezone))


def timezone_to_utc(request, datetime, timezone=''):
    return datetime.astimezone(pytz_timezone('UTC'))
