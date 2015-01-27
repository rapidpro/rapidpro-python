from __future__ import absolute_import, unicode_literals

import datetime
import pytz


ISO8601_DATE_FORMAT = '%Y-%m-%d'
ISO8601_DATETIME_FORMAT = ISO8601_DATE_FORMAT + 'T' + '%H:%M:%S'


def parse_iso8601(value):
    """
    Parses a datetime as a UTC ISO8601 date
    """
    if not value:
        return None

    if 'T' in value:  # has time
        _format = ISO8601_DATETIME_FORMAT

        if '.' in value:  # has microseconds. Some values from RapidPro don't include this.
            _format += '.%f'
        if 'Z' in value:  # has zero offset marker
            _format += 'Z'
    else:
        _format = ISO8601_DATE_FORMAT

    return datetime.datetime.strptime(value, _format).replace(tzinfo=pytz.utc)


def format_iso8601(_datetime):
    """
    Formats a datetime as a UTC ISO8601 date
    """
    _format = ISO8601_DATETIME_FORMAT + '.%f'

    return _datetime.astimezone(pytz.UTC).strftime(_format)
