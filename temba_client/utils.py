from __future__ import absolute_import, unicode_literals

import json
import requests
import six
import iso8601


def parse_iso8601(value):
    """
    Parses a datetime as a UTC ISO8601 date
    """
    if not value:
        return None

    return iso8601.parse_date(value)


def format_iso8601(value):
    """
    Formats a datetime as a UTC ISO8601 date or returns None if value is None
    """
    if value is None:
        return None

    return six.text_type(value.isoformat())


def request(method, url, **kwargs):  # pragma: no cover
    """
    For the purposes of testing, all calls to requests.request go through here before JSON bodies are encoded. It's
    easier to mock this and verify request data before it's encoded.
    """
    if 'data' in kwargs:
        kwargs['data'] = json.dumps(kwargs['data'])

    return requests.request(method, url, **kwargs)
