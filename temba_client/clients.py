from __future__ import absolute_import, unicode_literals

import datetime
import json
import logging
import requests
import six

from abc import ABCMeta
from . import __version__, CLIENT_NAME
from .exceptions import TembaMultipleResultsError, TembaNoSuchObjectError, TembaAPIError, TembaConnectionError
from .serialization import TembaObject
from .utils import format_iso8601, request

logger = logging.getLogger(__name__)


class BaseClient(object):
    """
    Abstract base client
    """
    __metaclass__ = ABCMeta

    def __init__(self, host, token, user_agent=None, api_version=None):
        if host.startswith('http'):
            if host.endswith('/'):
                self.root_url = host[:-1]
            else:
                self.root_url = host
        else:
            self.root_url = 'https://%s/api/v%d' % (host, api_version)

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
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s %s %s" % (method.upper(), url, json.dumps(params if params else body)))

        try:
            kwargs = {'headers': self.headers}
            if body:
                kwargs['data'] = body
            if params:
                kwargs['params'] = params

            response = request(method, url, **kwargs)

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


class BasePagingClient(BaseClient):
    """
    Abstract base client for page-based endpoint access
    """
    __metaclass__ = ABCMeta

    class Pager(object):
        """
        For iterating through page based API responses
        """
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


class BaseCursorClient(BaseClient):
    """
    Abstract base client for cursor-based endpoint access
    """
    __metaclass__ = ABCMeta

    class Query(object):
        """
        Result of a GET query which can then be iterated or fetched in its entirety
        """
        def __init__(self, client, url, params, clazz):
            self.client = client
            self.url = url
            self.params = params
            self.clazz = clazz

        def iterfetches(self):
            return BaseCursorClient.Iterator(self.client, self.url, self.params, self.clazz)

        def all(self):
            results = []
            for fetch in self.iterfetches():
                results += fetch
            return results

        def first(self):
            try:
                fetch = next(self.iterfetches())
                return fetch[0]
            except StopIteration:
                return None

        def get(self):
            result = self.first()
            if result is None:
                raise TembaNoSuchObjectError()
            else:
                return result

    class Iterator(object):
        """
        For iterating through cursor based API responses
        """
        def __init__(self, client, url, params, clazz):
            self.client = client
            self.url = url
            self.params = params
            self.clazz = clazz

        def __iter__(self):
            return self

        def next(self):
            if not self.url:
                raise StopIteration()

            response = self.client._request('get', self.url, params=self.params)
            self.url = response['next']
            self.params = {}
            results = response['results']

            if len(results) == 0:
                raise StopIteration()
            else:
                return self.clazz.deserialize_list(results)

    def _get_query(self, endpoint, params, clazz):
        """
        GETs a result query for the given endpoint
        """
        return BaseCursorClient.Query(self, '%s/%s.json' % (self.root_url, endpoint), params, clazz)
