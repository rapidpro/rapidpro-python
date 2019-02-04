import datetime
import json
import logging

import requests
import time

from urllib.parse import parse_qs, urlparse

from abc import ABCMeta
from . import __version__, CLIENT_NAME
from .exceptions import TembaMultipleResultsError, TembaNoSuchObjectError, TembaBadRequestError, TembaConnectionError
from .exceptions import TembaRateExceededError, TembaTokenError, TembaHttpError
from .serialization import TembaObject
from .utils import format_iso8601, request

logger = logging.getLogger(__name__)


MAX_RETRIES = 5


class BaseClient(object):
    """
    Abstract base client
    """

    __metaclass__ = ABCMeta

    def __init__(self, host, token, api_version, user_agent=None, verify_ssl=None):
        if host.startswith("http"):
            host_url = host
            if host_url.endswith("/"):  # trim a final slash
                host_url = host[:-1]
        else:
            host_url = "https://%s" % host

        self.root_url = "%s/api/v%d" % (host_url, api_version)

        self.headers = self._headers(token, user_agent)

        self.verify_ssl = verify_ssl

    @staticmethod
    def _headers(token, user_agent):
        if user_agent:
            user_agent_header = "%s %s/%s" % (user_agent, CLIENT_NAME, __version__)
        else:
            user_agent_header = "%s/%s" % (CLIENT_NAME, __version__)

        return {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": "Token %s" % token,
            "User-Agent": user_agent_header,
        }

    def _post(self, endpoint, params, payload):
        """
        POSTs to the given endpoint which must return a single item or list of items
        """
        url = "%s/%s.json" % (self.root_url, endpoint)
        return self._request("post", url, params=params, body=payload)

    def _delete(self, endpoint, params):
        """
        DELETEs to the given endpoint which won't return anything
        """
        url = "%s/%s.json" % (self.root_url, endpoint)
        self._request("delete", url, params=params)

    def _request(self, method, url, params=None, body=None):
        """
        Makes a GET or POST request to the given URL and returns the parsed JSON
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s %s %s" % (method.upper(), url, json.dumps(params if params else body)))

        try:
            kwargs = {"headers": self.headers}
            if body:
                kwargs["data"] = body
            if params:
                kwargs["params"] = params

            kwargs["verify"] = self.verify_ssl

            response = request(method, url, **kwargs)

            if response.status_code == 400:
                try:
                    errors = response.json()
                except ValueError:
                    errors = {"details": [response.content]}
                raise TembaBadRequestError(errors)

            elif response.status_code == 403:
                raise TembaTokenError()

            elif response.status_code == 404:
                raise TembaNoSuchObjectError()

            elif response.status_code == 429:  # have we exceeded our allowed rate?
                retry_after = response.headers.get("retry-after")
                raise TembaRateExceededError(int(retry_after) if retry_after else 0)

            response.raise_for_status()

            return response.json() if response.content else None
        except requests.HTTPError as ex:
            raise TembaHttpError(ex)
        except requests.exceptions.ConnectionError:
            raise TembaConnectionError()

    @classmethod
    def _build_params(cls, **kwargs):
        """
        Helper method to build params for a POST body or query string. Converts Temba objects to ids and UUIDs and
        removes None values.
        """
        params = {}
        for kwarg, value in kwargs.items():
            if value is None:
                continue
            else:
                params[kwarg] = cls._serialize_value(value)
        return params

    @classmethod
    def _build_id_param(cls, **kwargs):
        """
        Helper method for case where an endpoint (e.g. a v2 update) requires a single identifying param (usually UUID)
        """
        params = cls._build_params(**kwargs)

        if len(params) != 1:
            raise ValueError("Endpoint requires a single identifier parameter")

        return params

    @classmethod
    def _serialize_value(cls, value):
        if isinstance(value, list) or isinstance(value, tuple):
            serialized = []
            for item in value:
                serialized.append(cls._serialize_value(item))
            return serialized
        elif isinstance(value, TembaObject):
            if hasattr(value, "uuid"):
                return value.uuid
            elif hasattr(value, "id"):  # messages, runs, etc
                return value.id
            elif hasattr(value, "key"):  # fields
                return value.key
        elif isinstance(value, datetime.datetime):
            return format_iso8601(value)
        elif isinstance(value, bool):
            return 1 if value else 0
        else:
            return value


class Pager(object):
    """
    For iterating through page based API responses
    """

    def __init__(self, start_page):
        self.start_page = start_page
        self.count = None
        self.next_url = None

    def update(self, response):
        self.count = response["count"]
        self.next_url = response["next"]

    @property
    def total(self):
        return self.count

    def has_more(self):
        return bool(self.next_url)


class BasePagingClient(BaseClient):
    """
    Abstract base client for page-based endpoint access
    """

    __metaclass__ = ABCMeta

    def _get_single(self, endpoint, params, from_results=True):
        """
        GETs a single result from the given endpoint. Throws an exception if there are no or multiple results.
        """
        url = "%s/%s.json" % (self.root_url, endpoint)
        response = self._request("get", url, params=params)

        if from_results:
            num_results = len(response["results"])

            if num_results > 1:
                raise TembaMultipleResultsError()
            elif num_results == 0:
                raise TembaNoSuchObjectError()
            else:
                return response["results"][0]
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
            url = "%s/%s.json" % (self.root_url, endpoint)
            if pager.start_page != 1:
                params["page"] = pager.start_page

        response = self._request("get", url, params=params)

        pager.update(response)

        return response["results"]

    def _get_all(self, endpoint, params):
        """
        GETs all results from the given endpoint using multiple requests to fetch all pages
        """
        results = []
        url = "%s/%s.json" % (self.root_url, endpoint)

        while url:
            response = self._request("get", url, params=params)
            results += response["results"]
            url = response.get("next", None)
            params = {}

        return results


class CursorIterator:
    """
    For iterating through cursor based API responses
    """

    def __init__(self, client, url, params, clazz, retry_on_rate_exceed, resume_cursor):
        self.client = client
        self.url = url
        self.params = params
        self.clazz = clazz
        self.retry_on_rate_exceed = retry_on_rate_exceed
        self.resume_cursor = resume_cursor

    def __iter__(self):
        return self

    def __next__(self):
        if not self.url:
            raise StopIteration()

        if self.resume_cursor:
            self.params["cursor"] = self.resume_cursor

        response = self.client._request(
            "get", self.url, params=self.params, retry_on_rate_exceed=self.retry_on_rate_exceed
        )

        self.url = response["next"]
        self.resume_cursor = None
        self.params = {}
        results = response["results"]

        if len(results) == 0:
            raise StopIteration()
        else:
            return self.clazz.deserialize_list(results)

    def get_cursor(self):
        if not self.url:
            return None

        query_dict = parse_qs(urlparse(self.url).query)
        cursors = query_dict.get("cursor", None)
        return cursors[0] if cursors else None


class CursorQuery(object):
    """
    Result of a GET query which can then be iterated or fetched in its entirety
    """

    def __init__(self, client, url, params, clazz):
        self.client = client
        self.url = url
        self.params = params
        self.clazz = clazz

    def iterfetches(self, retry_on_rate_exceed=False, resume_cursor=None):
        """
        Returns an iterator which makes successive fetch requests for this query
        :param retry_on_rate_exceed: whether to sleep and retry if request rate limit exceeded
        :param resume_cursor: a cursor string to use to resume a previous iteration
        :return: the iterator
        """
        return CursorIterator(self.client, self.url, self.params, self.clazz, retry_on_rate_exceed, resume_cursor)

    def all(self, retry_on_rate_exceed=False):
        results = []
        for fetch in self.iterfetches(retry_on_rate_exceed):
            results += fetch
        return results

    def first(self, retry_on_rate_exceed=False):
        try:
            fetch = next(self.iterfetches(retry_on_rate_exceed))
            return fetch[0]
        except StopIteration:
            return None


class BaseCursorClient(BaseClient):
    """
    Abstract base client for cursor-based endpoint access
    """

    __metaclass__ = ABCMeta

    def _get_query(self, endpoint, params, clazz):
        """
        GETs a result query for the given endpoint
        """
        return CursorQuery(self, "%s/%s.json" % (self.root_url, endpoint), params, clazz)

    def _get_raw(self, endpoint, params, retry_on_rate_exceed=False):
        """
        GETs the raw response from the given endpoint
        """
        url = "%s/%s.json" % (self.root_url, endpoint)
        return self._request("get", url, params, retry_on_rate_exceed=retry_on_rate_exceed)

    def _request(self, method, url, params=None, body=None, retry_on_rate_exceed=False):
        if retry_on_rate_exceed:
            return self._request_wth_rate_limit_retry(method, url, params=params, body=body)
        else:
            return super(BaseCursorClient, self)._request(method, url, params=params, body=body)

    def _request_wth_rate_limit_retry(self, method, url, params=None, body=None):
        """
        Requests the given endpoint, sleeping and retrying if server responds with a rate limit error
        """
        retries = 0

        while True:
            try:
                return super(BaseCursorClient, self)._request(method, url, params=params, body=body)
            except TembaRateExceededError as ex:
                retries += 1

                if retries < MAX_RETRIES and ex.retry_after:
                    time.sleep(ex.retry_after)
                else:
                    raise ex
