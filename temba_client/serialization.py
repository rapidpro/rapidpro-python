from __future__ import absolute_import, unicode_literals

import six

from abc import ABCMeta, abstractmethod
from .exceptions import TembaSerializationException
from .utils import format_iso8601, parse_iso8601


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
                raise TembaSerializationException("Serialized %s item is missing field '%s'"
                                                  % (cls.__name__, field_source))

            field_value = item.get(field_source, None)
            attr_value = field.deserialize(field_value)

            setattr(instance, attr_name, attr_value)

        return instance

    @classmethod
    def deserialize_list(cls, item_list):
        return [cls.deserialize(item) for item in item_list]

    def serialize(self):
        item = {}

        for attr_name, field in six.iteritems(self._get_fields()):
            attr_value = getattr(self, attr_name, None)
            field_value = field.serialize(attr_value)

            field_source = field.src if field.src else six.text_type(attr_name)
            item[field_source] = field_value

        return item

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

    @abstractmethod
    def serialize(self, value):  # pragma: no cover
        pass


class SimpleField(TembaField):
    def deserialize(self, value):
        return value

    def serialize(self, value):
        return value


class BooleanField(SimpleField):
    def deserialize(self, value):
        if value is not None and not isinstance(value, bool):
            raise TembaSerializationException("Value '%s' field is not an boolean" % six.text_type(value))
        return value


class IntegerField(SimpleField):
    def deserialize(self, value):
        if value is not None and type(value) not in six.integer_types:
            raise TembaSerializationException("Value '%s' field is not an integer" % six.text_type(value))
        return value


class DatetimeField(TembaField):
    def deserialize(self, value):
        return parse_iso8601(value)

    def serialize(self, value):
        return format_iso8601(value)


class ObjectField(TembaField):
    def __init__(self, item_class, **kwargs):
        super(ObjectField, self).__init__(**kwargs)
        self.item_class = item_class

    def deserialize(self, value):
        return self.item_class.deserialize(value) if value is not None else None

    def serialize(self, value):
        return self.item_class.serialize(value) if value is not None else None


class ObjectListField(ObjectField):
    def deserialize(self, value):
        if not isinstance(value, list):
            raise TembaSerializationException("Value '%s' field is not a list" % six.text_type(value))

        return self.item_class.deserialize_list(value)

    def serialize(self, value):
        if not isinstance(value, list):
            raise TembaSerializationException("Value '%s' field is not a list" % six.text_type(value))

        return [self.item_class.serialize(item) for item in value]


class ObjectDictField(ObjectField):
    def deserialize(self, value):
        if not isinstance(value, dict):
            raise TembaSerializationException("Value '%s' field is not a dict" % six.text_type(value))

        return {key: self.item_class.deserialize(item) for key, item in six.iteritems(value)}

    def serialize(self, value):
        if not isinstance(value, dict):
            raise TembaSerializationException("Value '%s' field is not a dict" % six.text_type(value))

        return {key: self.item_class.serialize(item) for key, item in six.iteritems(value)}
