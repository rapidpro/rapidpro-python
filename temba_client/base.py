from __future__ import absolute_import, unicode_literals

import datetime
import json
import logging
import requests
import six

from abc import ABCMeta, abstractmethod
from . import __version__, CLIENT_NAME
from .utils import format_iso8601, parse_iso8601


logger = logging.getLogger(__name__)


# =====================================================================
# Exceptions
# =====================================================================

class TembaException(Exception):
    def __unicode__(self):  # pragma: no cover
        return self.message

    def __str__(self):
        return str(self.__unicode__())


class TembaNoSuchObjectError(TembaException):
    message = "Request for single object returned no objects"


class TembaMultipleResultsError(TembaException):
    message = "Request for single object returned multiple objects"


class TembaAPIError(TembaException):
    """
    Errors returned by the Temba API
    """
    message = "API request error"

    def __init__(self, caused_by):
        self.caused_by = caused_by
        self.errors = {}

        # if error was caused by a HTTP 400 response, we may have a useful validation error
        if isinstance(caused_by, requests.HTTPError) and caused_by.response.status_code == 400:
            try:
                self.errors = caused_by.response.json()
            except ValueError:
                pass

    def __unicode__(self):
        if self.errors:
            msgs = []
            for field, field_errors in six.iteritems(self.errors):
                for error in field_errors:
                    msgs.append(error)
            return "%s. Caused by: %s" % (self.message, ". ".join(msgs))
        else:
            return "%s. Caused by: %s" % (self.message, six.text_type(self.caused_by))


class TembaConnectionError(TembaException):
    message = "Unable to connect to host"


# =====================================================================
# Paging
# =====================================================================

class TembaPager(object):
    def __init__(self, start_page):
        self.start_page = start_page
        self.count = None
        self.next_url = None

    def update(self, response):
        self.count = response['count']
        self.next_url = response['next']

    @property
    def total(self):
        return self.count

    def has_more(self):
        return bool(self.next_url)


# =====================================================================
# Domain objects
# =====================================================================

class TembaObject(object):
    """
    Base class for objects returned by the Temba API
    """
    __metaclass__ = ABCMeta

    @classmethod
    def create(cls, **kwargs):
        source = kwargs.copy()
        instance = cls()

        for attr_name, field in six.iteritems(cls._get_fields()):
            if attr_name in source:
                field_value = source.pop(attr_name)
            else:
                field_value = None

            setattr(instance, attr_name, field_value)

        for remaining in source:
            raise ValueError("Class %s has no attribute '%s'" % (cls.__name__, remaining))

        return instance

    @classmethod
    def deserialize(cls, item):
        instance = cls()

        for attr_name, field in six.iteritems(cls._get_fields()):
            field_source = field.src if field.src else attr_name

            if field_source not in item and not field.optional:
                raise TembaException("Serialized %s item is missing field '%s'" % (cls.__name__, field_source))

            field_value = item.get(field_source, None)
            attr_value = field.deserialize(field_value)

            setattr(instance, attr_name, attr_value)

        return instance

    @classmethod
    def deserialize_list(cls, item_list):
        return [cls.deserialize(item) for item in item_list]

    @classmethod
    def _get_fields(cls):
        return {k: v for k, v in six.iteritems(cls.__dict__) if isinstance(v, TembaField)}


# =====================================================================
# Field types
# =====================================================================

class TembaField(object):
    __metaclass__ = ABCMeta

    def __init__(self, src=None, optional=False):
        self.src = src
        self.optional = optional

    @abstractmethod
    def deserialize(self, value):  # pragma: no cover
        pass


class SimpleField(TembaField):
    def deserialize(self, value):

        return value


class IntegerField(TembaField):
    def deserialize(self, value):
        if value and type(value) not in six.integer_types:
            raise TembaException("Value '%s' field is not an integer" % six.text_type(value))
        return value


class DatetimeField(TembaField):
    def deserialize(self, value):
        return parse_iso8601(value)


class ObjectField(TembaField):
    def __init__(self, item_class, src=None):
        super(ObjectField, self).__init__(src)
        self.item_class = item_class

    def deserialize(self, value):
        return self.item_class.deserialize(value)


class ObjectListField(ObjectField):
    def deserialize(self, value):
        if not isinstance(value, list):
            raise TembaException("Value '%s' field is not a list" % six.text_type(value))

        return self.item_class.deserialize_list(value)


# =====================================================================
# Client base
# =====================================================================

class AbstractTembaClient(object):
    """
    Abstract and version agnostic base client class
    """
    __metaclass__ = ABCMeta

    def __init__(self, host, token, user_agent=None):
        if host.startswith('http'):
            if host.endswith('/'):
                self.root_url = host[:-1]
            else:
                self.root_url = host
        else:
            self.root_url = 'https://%s/api/v1' % host

        self.headers = self._headers(token, user_agent)

    @staticmethod
    def _headers(token, user_agent):
        if user_agent:
            user_agent_header = '%s %s/%s' % (user_agent, CLIENT_NAME, __version__)
        else:
            user_agent_header = '%s/%s' % (CLIENT_NAME, __version__)

        return {'Content-type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Token %s' % token,
                'User-Agent': user_agent_header}

    def pager(self, start_page=1):
        """
        Returns a new pager

        :param int start_page: the starting page number
        :return: the pager
        """
        return TembaPager(start_page)

    def _get_single(self, endpoint, params, from_results=True):
        """
        GETs a single result from the given endpoint. Throws an exception if there are no or multiple results.
        """
        url = '%s/%s.json' % (self.root_url, endpoint)
        response = self._request('get', url, params=params)

        if from_results:
            num_results = len(response['results'])

            if num_results > 1:
                raise TembaMultipleResultsError()
            elif num_results == 0:
                raise TembaNoSuchObjectError()
            else:
                return response['results'][0]
        else:
            return response

    def _get_multiple(self, endpoint, params, pager):
        """
        GETs multiple results from the given endpoint
        """
        if pager:
            return self._get_page(endpoint, params, pager)
        else:
            return self._get_all(endpoint, params)

    def _get_page(self, endpoint, params, pager):
        """
        GETs a page of results from the given endpoint
        """
        if pager.next_url:
            url = pager.next_url
            params = None
        else:
            url = '%s/%s.json' % (self.root_url, endpoint)
            if pager.start_page != 1:
                params['page'] = pager.start_page

        response = self._request('get', url, params=params)

        pager.update(response)

        return response['results']

    def _get_all(self, endpoint, params):
        """
        GETs all results from the given endpoint using multiple requests to fetch all pages
        """
        results = []
        url = '%s/%s.json' % (self.root_url, endpoint)

        while url:
            response = self._request('get', url, params=params)
            results += response['results']
            url = response.get('next', None)
            params = {}

        return results

    def _post(self, endpoint, payload):
        """
        POSTs to the given endpoint which must return a single item or list of items
        """
        url = '%s/%s.json' % (self.root_url, endpoint)
        return self._request('post', url, body=payload)

    def _delete(self, endpoint, params):
        """
        DELETEs to the given endpoint which won't return anything
        """
        url = '%s/%s.json' % (self.root_url, endpoint)
        self._request('delete', url, params=params)

    def _request(self, method, url, body=None, params=None):
        """
        Makes a GET or POST request to the given URL and returns the parsed JSON
        """
        logger.debug("%s %s %s" % (method.upper(), url, json.dumps(params if params else body)))

        try:
            kwargs = {'headers': self.headers}
            if body:
                kwargs['data'] = body
            if params:
                kwargs['params'] = params

            response = request(method, url, **kwargs)

            logger.debug(" -> %s" % response.content)

            response.raise_for_status()

            return response.json() if response.content else None
        except requests.HTTPError as ex:
            raise TembaAPIError(ex)
        except requests.exceptions.ConnectionError:
            raise TembaConnectionError()

    @classmethod
    def _build_params(cls, **kwargs):
        """
        Helper method to build params for a POST body or query string. Converts Temba objects to ids and UUIDs and
        removes None values.
        """
        params = {}
        for kwarg, value in six.iteritems(kwargs):
            if value is None:
                continue
            else:
                params[kwarg] = cls._serialize_value(value)
        return params

    @classmethod
    def _serialize_value(cls, value):
        if isinstance(value, list) or isinstance(value, tuple):
            serialized = []
            for item in value:
                serialized.append(cls._serialize_value(item))
            return serialized
        elif isinstance(value, TembaObject):
            if hasattr(value, 'uuid'):
                return value.uuid
            elif hasattr(value, 'id'):
                return value.id
        elif isinstance(value, datetime.datetime):
            return format_iso8601(value)
        elif isinstance(value, bool):
            return 1 if value else 0
        else:
            return value


def request(method, url, **kwargs):  # pragma: no cover
    """
    For the purposes of testing, all calls to requests.request go through here before JSON bodies are encoded. It's
    easier to mock this and verify request data before it's encoded.
    """
    if 'data' in kwargs:
        kwargs['data'] = json.dumps(kwargs['data'])

    return requests.request(method, url, **kwargs)
