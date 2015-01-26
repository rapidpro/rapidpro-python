from __future__ import unicode_literals

import datetime
import pytz
import requests


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


class TembaException(Exception):
    """
    Exception class for all errors from client methods
    """
    def __init__(self, msg, caused_by=None):
        self.msg = msg
        self.caused_by = caused_by

        # if error was caused by a HTTP 400 response, we may have a useful validation error
        if isinstance(caused_by, requests.HTTPError) and caused_by.response.status_code == 400:
            msg = self._extract_errors(caused_by.response)
            if msg:
                self.caused_by = msg

    @staticmethod
    def _extract_errors(response):
        try:
            errors = response.json()
            msgs = []
            for field, field_errors in errors.iteritems():
                for error in field_errors:
                    msgs.append(error)
            return ". ".join(msgs)
        except Exception:
            return None

    def __unicode__(self):
        if self.caused_by:
            return "%s. Caused by: %s" % (self.msg, self.caused_by)
        else:
            return self.msg

    def __str__(self):
        return str(self.__unicode__())


class TembaType(object):
    """
    Base class for types returned by the Temba API
    """
    @classmethod
    def create(cls, **kwargs):
        fields = set(cls.Meta.fields)
        source = kwargs.copy()
        instance = cls()

        for field in fields:
            field_attr = field[1] if isinstance(field, tuple) else field

            if field_attr in source:
                field_value = source[field_attr]
                del source[field_attr]
            else:
                field_value = None

            setattr(instance, field_attr, field_value)

        for remaining in source:
                raise ValueError("Class %s has no attribute '%s'" % (cls.__name__, remaining))

        return instance

    @classmethod
    def deserialize(cls, item):
        fields = set(cls.Meta.fields)
        datetime_fields = getattr(cls.Meta, 'datetime_fields', ())
        nested_list_fields = getattr(cls.Meta, 'nested_list_fields', {})
        instance = cls()

        for field in fields:
            # if attr name is different to json obj property, field is a tuple
            if isinstance(field, tuple):
                field_source = field[0]
                field_attr = field[1]
            else:
                field_source = field_attr = field

            if not field_source in item:
                raise TembaException("Serialized %s item is missing field '%s'" % (cls.__name__, field))

            field_value = item[field_source]

            # parse datetime fields
            if field_attr in datetime_fields:
                field_value = parse_iso8601(field_value)

            # parse nested list type fields
            if field_attr in nested_list_fields:
                nested_list_type = nested_list_fields[field_attr]

                if not isinstance(field_value, list):
                    raise TembaException("Value for nested list field '%s' is not a list" % field)

                field_value = nested_list_type.deserialize_list(field_value)

            setattr(instance, field_attr, field_value)

        return instance

    @classmethod
    def deserialize_list(cls, item_list):
        return [cls.deserialize(item) for item in item_list]

    class Meta:
        fields = ()
        datetime_fields = ()


class Broadcast(TembaType):
    class Meta:
        fields = ('id', 'urns', 'contacts', 'groups', 'text', 'messages', 'status', 'created_on')
        datetime_fields = ('created_on',)


class Contact(TembaType):
    class Meta:
        fields = ('uuid', 'name', 'urns', ('group_uuids', 'groups'), 'fields', 'language', 'modified_on')
        datetime_fields = ('modified_on',)


class Group(TembaType):
    class Meta:
        fields = ('uuid', 'name', 'size')


class Field(TembaType):
    class Meta:
        fields = ('key', 'label', 'value_type')


class FlowRuleSet(TembaType):
    class Meta:
        fields = (('node', 'uuid'), 'label')


class Flow(TembaType):
    class Meta:
        fields = ('uuid', 'name', 'archived', 'labels', 'participants', 'runs', 'completed_runs', 'rulesets', 'created_on')
        datetime_fields = ('created_on',)
        nested_list_fields = {'rulesets': FlowRuleSet}


class Message(TembaType):
    class Meta:
        fields = ('contact', 'urn', 'status', 'type', 'labels', 'direction', 'text', 'created_on', 'delivered_on', 'sent_on')
        datetime_fields = ('created_on', 'delivered_on', 'sent_on')


class RunValueSet(TembaType):
    class Meta:
        fields = ('node', 'category', 'text', 'rule_value', 'value', 'label', 'time')
        datetime_fields = ('time',)


class RunStep(TembaType):
    class Meta:
        fields = ('node', 'text', 'value', 'type', 'arrived_on', 'left_on')
        datetime_fields = ('arrived_on', 'left_on')


class Run(TembaType):
    @classmethod
    def deserialize(cls, item):
        run = super(Run, cls).deserialize(item)

        # Temba API should only be returning values for the last visit to each step but returns all instead
        last_only = []
        nodes_seen = set()
        for valueset in reversed(run.values):
            if valueset.node not in nodes_seen:
                last_only.append(valueset)
                nodes_seen.add(valueset.node)
        last_only.reverse()
        run.values = last_only

        return run

    class Meta:
        fields = (('run', 'id'), ('flow_uuid', 'flow'), 'contact', 'steps', 'values', 'created_on')
        datetime_fields = ('created_on',)
        nested_list_fields = {'steps': RunStep, 'values': RunValueSet}
