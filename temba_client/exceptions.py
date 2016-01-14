from __future__ import absolute_import, unicode_literals

import requests
import six


class TembaException(Exception):
    def __unicode__(self):  # pragma: no cover
        return self.message

    def __str__(self):
        return str(self.__unicode__())


class TembaNoSuchObjectError(TembaException):
    message = "No such object exists"


class TembaMultipleResultsError(TembaException):
    message = "Request for single object returned multiple objects"


class TembaBadRequestError(TembaException):
    message = "Bad request: %s"

    def __init__(self, errors):
        self.errors = errors

    def __unicode__(self):
        msgs = []
        for field, field_errors in six.iteritems(self.errors):
            for error in field_errors:
                msgs.append(error)
        cause = msgs[0] if len(msgs) == 1 else ". ".join(msgs)

        return self.message % cause


class TembaHttpError(TembaException):
    def __init__(self, caused_by):
        self.caused_by = caused_by

    def __unicode__(self):
        return unicode(self.caused_by)


class TembaConnectionError(TembaException):
    message = "Unable to connect to host"


class TembaRateExceededError(TembaException):
    message = "You have exceeded the number of requests allowed per org in a given time window. Please wait %d seconds before making further requests"

    def __init__(self, retry_after):
        self.retry_after = retry_after

    def __unicode__(self):
        return self.message % self.retry_after


class TembaSerializationException(TembaException):
    pass
