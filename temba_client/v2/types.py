from __future__ import absolute_import, unicode_literals

from ..serialization import TembaObject, SimpleField, BooleanField, IntegerField, DatetimeField, ObjectField
from ..serialization import ObjectListField


class ObjectRef(TembaObject):
    """
    Used for references to objects in other objects
    """
    uuid = SimpleField()
    name = SimpleField()


class FieldRef(TembaObject):
    """
    Used for references to fields in other objects
    """
    key = SimpleField()
    label = SimpleField()


class Broadcast(TembaObject):
    id = IntegerField()
    urns = SimpleField()
    contacts = ObjectListField(item_class=ObjectRef)
    groups = ObjectListField(item_class=ObjectRef)
    text = SimpleField()
    created_on = DatetimeField()


class Campaign(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    group = ObjectField(item_class=ObjectRef)
    created_on = DatetimeField()


class CampaignEvent(TembaObject):
    uuid = SimpleField()
    campaign = ObjectField(item_class=ObjectRef)
    relative_to = ObjectField(item_class=FieldRef)
    offset = IntegerField()
    unit = SimpleField()
    delivery_hour = IntegerField()
    flow = ObjectField(item_class=ObjectRef)
    message = SimpleField()
    created_on = DatetimeField()


class Channel(TembaObject):
    class Device(TembaObject):
        name = SimpleField()
        power_level = IntegerField()
        power_status = SimpleField()
        power_source = SimpleField()
        network_type = SimpleField()

    uuid = SimpleField()
    name = SimpleField()
    address = SimpleField()
    country = SimpleField()
    device = ObjectField(item_class=Device)
    last_seen = DatetimeField()
    created_on = DatetimeField()


class ChannelEvent(TembaObject):
    id = IntegerField()
    type = SimpleField()
    contact = ObjectField(item_class=ObjectRef)
    channel = ObjectField(item_class=ObjectRef)
    time = DatetimeField()
    duration = IntegerField()
    created_on = DatetimeField()


class Contact(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    language = SimpleField()
    urns = SimpleField()
    groups = ObjectListField(item_class=ObjectRef)
    fields = SimpleField()
    blocked = BooleanField()
    stopped = BooleanField()
    created_on = DatetimeField()
    modified_on = DatetimeField()


class Field(TembaObject):
    key = SimpleField()
    label = SimpleField()
    value_type = SimpleField()


class Group(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    query = SimpleField()
    count = IntegerField()


class Label(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    count = IntegerField()


class Message(TembaObject):
    id = IntegerField()
    broadcast = IntegerField()
    contact = ObjectField(item_class=ObjectRef)
    urn = SimpleField()
    channel = ObjectField(item_class=ObjectRef)
    direction = SimpleField()
    type = SimpleField()
    status = SimpleField()
    visibility = SimpleField(optional=True)
    text = SimpleField()
    labels = ObjectListField(item_class=ObjectRef)
    created_on = DatetimeField()
    sent_on = DatetimeField()
    modified_on = DatetimeField(optional=True)


class Org(TembaObject):
    name = SimpleField()
    country = SimpleField()
    languages = SimpleField()
    primary_language = SimpleField()
    timezone = SimpleField()
    date_style = SimpleField()
    anon = SimpleField()


class Run(TembaObject):
    class Step(TembaObject):
        node = SimpleField()
        text = SimpleField()
        value = SimpleField()
        category = SimpleField()
        type = SimpleField()
        arrived_on = DatetimeField()
        left_on = DatetimeField()

    id = IntegerField()
    flow = ObjectField(item_class=ObjectRef)
    contact = ObjectField(item_class=ObjectRef)
    responded = BooleanField()
    steps = ObjectListField(item_class=Step)
    created_on = DatetimeField()
    modified_on = DatetimeField()
    exited_on = DatetimeField()
    exit_type = SimpleField()
