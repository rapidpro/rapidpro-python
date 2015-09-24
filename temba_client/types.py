from __future__ import absolute_import, unicode_literals

from .base import TembaObject, SimpleField, IntegerField, DatetimeField, ObjectListField, ObjectField


class Broadcast(TembaObject):
    id = IntegerField()
    urns = SimpleField()
    contacts = SimpleField()
    groups = SimpleField()
    text = SimpleField()
    status = SimpleField()
    created_on = DatetimeField()


class Campaign(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    group = SimpleField(src='group_uuid')
    created_on = DatetimeField()


class Contact(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    urns = SimpleField()
    groups = SimpleField(src='group_uuids')
    fields = SimpleField()
    language = SimpleField()
    blocked = SimpleField()
    failed = SimpleField()
    modified_on = DatetimeField()


class Group(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    size = IntegerField()


class Event(TembaObject):
    uuid = SimpleField()
    campaign = SimpleField(src='campaign_uuid')
    relative_to = SimpleField()
    offset = IntegerField()
    unit = SimpleField()
    delivery_hour = IntegerField()
    message = SimpleField()
    flow = SimpleField(src='flow_uuid')
    created_on = DatetimeField()


class Field(TembaObject):
    key = SimpleField()
    label = SimpleField()
    value_type = SimpleField()


class RuleSet(TembaObject):
    uuid = SimpleField(src='node')
    label = SimpleField()
    response_type = SimpleField()


class Flow(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    archived = SimpleField()
    labels = SimpleField()
    participants = IntegerField()
    runs = IntegerField()
    completed_runs = IntegerField()
    expires = IntegerField()
    rulesets = ObjectListField(item_class=RuleSet)
    created_on = DatetimeField()


class Label(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    count = IntegerField()


class Message(TembaObject):
    id = IntegerField()
    broadcast = IntegerField()
    contact = SimpleField()
    urn = SimpleField()
    status = SimpleField()
    type = SimpleField()
    labels = SimpleField()
    direction = SimpleField()
    archived = SimpleField()
    text = SimpleField()
    created_on = DatetimeField()
    delivered_on = DatetimeField()
    sent_on = DatetimeField()


class Org(TembaObject):
    name = SimpleField()
    country = SimpleField()
    languages = SimpleField()
    primary_language = SimpleField()
    timezone = SimpleField()
    date_style = SimpleField()
    anon = SimpleField()


class RunValueSet(TembaObject):
    node = SimpleField()
    category = SimpleField()
    text = SimpleField()
    rule_value = SimpleField()
    value = SimpleField()
    label = SimpleField()
    time = DatetimeField()


class FlowStep(TembaObject):
    node = SimpleField()
    text = SimpleField()
    value = SimpleField()
    type = SimpleField()
    arrived_on = DatetimeField()
    left_on = DatetimeField()


class Run(TembaObject):
    id = IntegerField(src='run')
    flow = SimpleField(src='flow_uuid')
    contact = SimpleField()
    steps = ObjectListField(item_class=FlowStep)
    values = ObjectListField(item_class=RunValueSet)
    created_on = DatetimeField()
    expires_on = DatetimeField()
    expired_on = DatetimeField()
    completed = SimpleField()

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


class Geometry(TembaObject):
    type = SimpleField()
    coordinates = SimpleField()


class Boundary(TembaObject):
    boundary = SimpleField()
    name = SimpleField()
    level = IntegerField()
    parent = SimpleField()
    geometry = ObjectField(item_class=Geometry)


class CategoryStats(TembaObject):
    count = IntegerField()
    label = SimpleField()


class Result(TembaObject):
    boundary = SimpleField(optional=True)
    set = IntegerField()
    unset = IntegerField()
    open_ended = SimpleField()
    label = SimpleField()
    categories = ObjectListField(item_class=CategoryStats)
