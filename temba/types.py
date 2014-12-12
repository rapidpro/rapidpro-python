from __future__ import unicode_literals

import datetime
import pytz


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def parse_datetime(value):
    return datetime.datetime.strptime(value, DATETIME_FORMAT).replace(tzinfo=pytz.utc)


class TembaType(object):
    @classmethod
    def deserialize(cls, item):
        fields = cls.Meta.fields
        datetime_fields = getattr(cls.Meta, 'datetime_fields', ())
        instance = cls()

        for field in fields:
            if field in datetime_fields:
                setattr(instance, field, parse_datetime(item[field]))
            else:
                setattr(instance, field, item[field])

        return instance

    @classmethod
    def deserialize_list(cls, item_list):
        return [cls.deserialize(item) for item in item_list]

    class Meta:
        fields = ()
        datetime_fields = ()


class Contact(TembaType):
    class Meta:
        fields = ('uuid', 'name', 'urns', 'group_uuids', 'fields', 'modified_on')
        datetime_fields = ('modified_on',)


class ContactGroup(TembaType):
    class Meta:
        fields = ('uuid', 'name', 'size')


class Flow(TembaType):
    class Meta:
        fields = ('uuid',)  # TODO add all fields


class FlowRun(TembaType):
    class Meta:
        fields = ('uuid',)  # TODO add all fields