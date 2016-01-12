from __future__ import absolute_import, unicode_literals

from ..serialization import TembaObject, SimpleField, BooleanField, IntegerField, DatetimeField, ObjectListField


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
