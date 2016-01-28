from __future__ import absolute_import, unicode_literals

from ..serialization import TembaObject, SimpleField, BooleanField, IntegerField, DatetimeField, ObjectField
from ..serialization import ObjectListField


class ObjectRef(TembaObject):
    """
    Used for references to objects in other objects
    """
    uuid = SimpleField()
    name = SimpleField()


class Contact(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    language = SimpleField()
    urns = SimpleField()
    groups = ObjectListField(item_class=ObjectRef)
    fields = SimpleField()
    blocked = BooleanField()
    failed = BooleanField()
    created_on = DatetimeField()
    modified_on = DatetimeField()


class Message(TembaObject):
    id = IntegerField()
    broadcast = IntegerField()
    contact = ObjectField(item_class=ObjectRef)
    urn = SimpleField()
    channel = ObjectField(item_class=ObjectRef)
    direction = SimpleField()
    type = SimpleField()
    status = SimpleField()
    archived = BooleanField()
    text = SimpleField()
    labels = ObjectListField(item_class=ObjectRef)
    created_on = DatetimeField()
    sent_on = DatetimeField()
    delivered_on = DatetimeField()


class Step(TembaObject):
    node = SimpleField()
    text = SimpleField()
    value = SimpleField()
    category = SimpleField()
    type = SimpleField()
    arrived_on = DatetimeField()
    left_on = DatetimeField()


class Run(TembaObject):
    id = IntegerField()
    flow = ObjectField(item_class=ObjectRef)
    contact = ObjectField(item_class=ObjectRef)
    responded = BooleanField()
    steps = ObjectListField(item_class=Step)
    created_on = DatetimeField()
    modified_on = DatetimeField()
    exited_on = DatetimeField()
    exit_type = SimpleField()
