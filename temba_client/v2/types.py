from __future__ import absolute_import, unicode_literals

from ..serialization import TembaObject, SimpleField, BooleanField, IntegerField, DatetimeField, ObjectListField


class GroupRef(TembaObject):
    """
    Used for references to contact groups in other objects
    """
    uuid = SimpleField()
    name = SimpleField()


class LabelRef(TembaObject):
    """
    Used for references to labels in other objects
    """
    uuid = SimpleField()
    name = SimpleField()


class Contact(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    language = SimpleField()
    urns = SimpleField()
    groups = ObjectListField(item_class=GroupRef)
    fields = SimpleField()
    blocked = BooleanField()
    failed = BooleanField()
    created_on = DatetimeField()
    modified_on = DatetimeField()


class Message(TembaObject):
    id = IntegerField()
    broadcast = IntegerField(optional=True)
    contact = SimpleField()
    urn = SimpleField()
    channel = SimpleField()
    direction = SimpleField()
    type = SimpleField()
    status = SimpleField()
    archived = BooleanField()
    text = SimpleField()
    labels = ObjectListField(item_class=LabelRef)
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
    flow = SimpleField()
    contact = SimpleField()
    responded = BooleanField()
    steps = ObjectListField(item_class=Step)
    created_on = DatetimeField()
    modified_on = DatetimeField()
    exited_on = DatetimeField()
    exit_type = SimpleField()
