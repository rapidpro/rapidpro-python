from __future__ import absolute_import, unicode_literals

import requests
import six


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
                self.errors = {'non_field_errors': [caused_by.response.content]}
                pass

    def __unicode__(self):
        if self.errors:
            msgs = []
            for field, field_errors in six.iteritems(self.errors):
                for error in field_errors:
                    msgs.append(error)
            cause = msgs[0] if len(msgs) == 1 else ". ".join(msgs)

            return "%s. Caused by: %s" % (self.message, cause)
        else:
            return "%s. Caused by: %s" % (self.message, six.text_type(self.caused_by))


class TembaConnectionError(TembaException):
    message = "Unable to connect to host"


class TembaRateLimitError(TembaException):
    message = "You have exceeded the number of requests allowed per org in a given time window. Please wait %d seconds before making further requests"

    def __init__(self, retry_after):
        self.retry_after = retry_after

    def __unicode__(self):
        return self.message % self.retry_after


class TembaSerializationException(TembaException):
    pass
