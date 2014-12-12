from __future__ import unicode_literals

import datetime
import pytz


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def parse_datetime(value):
    return datetime.datetime.strptime(value, DATETIME_FORMAT).replace(tzinfo=pytz.utc)


class DictStruct(object):
    """
    Wraps a dictionary turning it into a structure looking object
    """
    def __init__(self, classname, entries, datetime_fields=()):
        self._classname = classname
        self._values = entries

        # for each of our datetime fields, convert back to datetimes
        for field in datetime_fields:
            value = self._values.get(field, None)
            if value:
                self._values[field] = parse_datetime(value)

        self._initialized = True

    def __getattr__(self, item):
        if not item in self._values:
            raise AttributeError("'%s' object has no attribute '%s'" % (self._classname, item))

        return self._values[item]

    def __setattr__(self, item, value):
        # needed to prevent infinite loop
        if not self.__dict__.has_key('_initialized'):
            return object.__setattr__(self, item, value)

        if not item in self._values:
            raise TypeError("'%s' object has no attribute '%s'" % (self._classname, item))

        self._values[item] = value

    def __unicode__(self):
        return "%s [%s]" % (self._classname, self._values)