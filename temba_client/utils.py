from __future__ import absolute_import, unicode_literals

import datetime
import json
import pytz
import requests
import six


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


def format_iso8601(value):
    """
    Formats a datetime as a UTC ISO8601 date or returns None if value is None
    """
    if value is None:
        return None

    _format = ISO8601_DATETIME_FORMAT + '.%fZ'

    return six.text_type(value.astimezone(pytz.UTC).strftime(_format))


def request(method, url, **kwargs):  # pragma: no cover
    """
    For the purposes of testing, all calls to requests.request go through here before JSON bodies are encoded. It's
    easier to mock this and verify request data before it's encoded.
    """
    if 'data' in kwargs:
        kwargs['data'] = json.dumps(kwargs['data'])

    return requests.request(method, url, **kwargs)
