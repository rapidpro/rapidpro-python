from abc import ABCMeta, abstractmethod
from .exceptions import TembaSerializationException
from .utils import format_iso8601, parse_iso8601


class TembaObject(metaclass=ABCMeta):
    """
    Base class for objects returned by the Temba API
    """

    @classmethod
    def create(cls, **kwargs):
        source = kwargs.copy()
        instance = cls()

        for attr_name, field in cls._get_fields().items():
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

        for attr_name, field in cls._get_fields().items():
            field_source = field.src if field.src else attr_name

            if field_source not in item and not field.optional:
                raise TembaSerializationException(
                    "Serialized %s item is missing field '%s'" % (cls.__name__, field_source)
                )

            field_value = item.get(field_source, None)
            attr_value = field.deserialize(field_value)

            setattr(instance, attr_name, attr_value)

        return instance

    @classmethod
    def deserialize_list(cls, item_list):
        return [cls.deserialize(item) for item in item_list]

    def serialize(self):
        item = {}

        for attr_name, field in self._get_fields().items():
            attr_value = getattr(self, attr_name, None)
            field_value = field.serialize(attr_value)

            field_source = field.src if field.src else str(attr_name)
            item[field_source] = field_value

        return item

    @classmethod
    def _get_fields(cls):
        return {k: v for k, v in cls.__dict__.items() if isinstance(v, TembaField)}


# =====================================================================
# Field types
# =====================================================================


class TembaField(metaclass=ABCMeta):
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
            raise TembaSerializationException("Value '%s' field is not an boolean" % str(value))
        return value


class IntegerField(SimpleField):
    def deserialize(self, value):
        if value is not None and type(value) != int:
            raise TembaSerializationException("Value '%s' field is not an integer" % str(value))
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
            raise TembaSerializationException("Value '%s' field is not a list" % str(value))

        return self.item_class.deserialize_list(value)

    def serialize(self, value):
        if not isinstance(value, list):
            raise TembaSerializationException("Value '%s' field is not a list" % str(value))

        return [self.item_class.serialize(item) for item in value]


class ObjectDictField(ObjectField):
    def deserialize(self, value):
        if not isinstance(value, dict):
            raise TembaSerializationException("Value '%s' field is not a dict" % str(value))

        return {key: self.item_class.deserialize(item) for key, item in value.items()}

    def serialize(self, value):
        if not isinstance(value, dict):
            raise TembaSerializationException("Value '%s' field is not a dict" % str(value))

        return {key: self.item_class.serialize(item) for key, item in value.items()}
