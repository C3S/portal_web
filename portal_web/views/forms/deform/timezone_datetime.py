# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import colander

from ....services import default_tzinfo


def deferred_timezone_datetime_field(format=''):
    format = format or "%Y-%m-%dT%H:%M"

    @colander.deferred
    def timezone_datetime_field(node, kw):
        return colander.DateTime(
            default_tzinfo=default_tzinfo(kw['request']),
            format=format)

    return timezone_datetime_field
