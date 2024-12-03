from ..serialization import (
    BooleanField,
    DatetimeField,
    IntegerField,
    ListField,
    ObjectDictField,
    ObjectField,
    ObjectListField,
    SimpleField,
    TembaObject,
)


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
    name = SimpleField()


class Archive(TembaObject):
    archive_type = SimpleField()
    start_date = DatetimeField()
    period = SimpleField()
    record_count = IntegerField()
    size = IntegerField()
    hash = SimpleField()
    download_url = SimpleField()


class Boundary(TembaObject):
    class BoundaryRef(TembaObject):
        osm_id = SimpleField()
        name = SimpleField()

    class Geometry(TembaObject):
        type = SimpleField()
        coordinates = SimpleField()

    osm_id = SimpleField()
    name = SimpleField()
    level = IntegerField()
    parent = ObjectField(item_class=BoundaryRef)
    aliases = ListField()
    geometry = ObjectField(item_class=Geometry)


class Broadcast(TembaObject):
    id = IntegerField()
    status = SimpleField()
    urns = SimpleField()
    contacts = ObjectListField(item_class=ObjectRef)
    groups = ObjectListField(item_class=ObjectRef)
    text = SimpleField()
    created_on = DatetimeField()


class Campaign(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    archived = BooleanField()
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


class Classifier(TembaObject):
    uuid = SimpleField()
    type = SimpleField()
    name = SimpleField()
    intents = ListField()
    created_on = DatetimeField()


class Contact(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    status = SimpleField()
    language = SimpleField()
    urns = ListField()
    groups = ObjectListField(item_class=ObjectRef)
    flow = ObjectField(item_class=ObjectRef)
    fields = SimpleField()
    created_on = DatetimeField()
    modified_on = DatetimeField()
    last_seen_on = DatetimeField()


class Export(TembaObject):
    version = SimpleField()
    flows = ListField()
    campaigns = ListField()
    triggers = ListField()
    fields = ListField()
    groups = ListField()

class Field(TembaObject):
    key = SimpleField()
    name = SimpleField()
    type = SimpleField()


class Flow(TembaObject):
    class Runs(TembaObject):
        active = IntegerField()
        waiting = IntegerField()
        completed = IntegerField()
        interrupted = IntegerField()
        expired = IntegerField()
        failed = IntegerField()

    class FlowResult(TembaObject):
        key = SimpleField()
        name = SimpleField()
        categories = SimpleField()
        node_uuids = SimpleField()

    uuid = SimpleField()
    name = SimpleField()
    type = SimpleField()
    archived = BooleanField()
    labels = ObjectListField(item_class=ObjectRef)
    expires = IntegerField()
    created_on = DatetimeField()
    runs = ObjectField(item_class=Runs)
    results = ObjectListField(item_class=FlowResult)


class FlowStart(TembaObject):
    uuid = SimpleField()
    flow = ObjectField(item_class=ObjectRef)
    groups = ObjectListField(item_class=ObjectRef)
    contacts = ObjectListField(item_class=ObjectRef)
    status = SimpleField()
    restart_participants = BooleanField()
    exclude_active = BooleanField()
    params = SimpleField()
    created_on = DatetimeField()
    modified_on = DatetimeField()


class Global(TembaObject):
    key = SimpleField()
    name = SimpleField()
    value = SimpleField()
    modified_on = DatetimeField()


class Group(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    query = SimpleField()
    status = SimpleField()
    system = BooleanField()
    count = IntegerField()


class Label(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    count = IntegerField()


class Message(TembaObject):
    class AttachmentRef(TembaObject):
        content_type = SimpleField()
        url = SimpleField()

    id = IntegerField()
    broadcast = IntegerField()
    contact = ObjectField(item_class=ObjectRef)
    urn = SimpleField()
    channel = ObjectField(item_class=ObjectRef)
    direction = SimpleField()
    type = SimpleField()
    status = SimpleField()
    visibility = SimpleField()
    text = SimpleField()
    labels = ObjectListField(item_class=ObjectRef)
    attachments = ObjectListField(item_class=AttachmentRef)
    flow = ObjectField(item_class=ObjectRef)
    created_on = DatetimeField()
    sent_on = DatetimeField()
    modified_on = DatetimeField()


class Org(TembaObject):
    uuid = SimpleField()
    name = SimpleField()
    country = SimpleField()
    languages = ListField()
    primary_language = SimpleField()
    timezone = SimpleField()
    date_style = SimpleField()
    anon = SimpleField()


class Resthook(TembaObject):
    resthook = SimpleField()
    created_on = DatetimeField()
    modified_on = DatetimeField()


class ResthookEvent(TembaObject):
    resthook = SimpleField()
    data = SimpleField()
    created_on = DatetimeField()


class ResthookSubscriber(TembaObject):
    id = IntegerField()
    resthook = SimpleField()
    target_url = SimpleField()
    created_on = DatetimeField()


class Run(TembaObject):
    class StartRef(TembaObject):
        uuid = SimpleField()

    class Step(TembaObject):
        node = SimpleField()
        time = DatetimeField()

    class Value(TembaObject):
        name = SimpleField()
        value = SimpleField()
        category = SimpleField()
        node = SimpleField()
        time = DatetimeField()

    uuid = SimpleField()
    flow = ObjectField(item_class=ObjectRef)
    contact = ObjectField(item_class=ObjectRef)
    start = ObjectField(item_class=StartRef)
    responded = BooleanField()
    path = ObjectListField(item_class=Step)
    values = ObjectDictField(item_class=Value)
    created_on = DatetimeField()
    modified_on = DatetimeField()
    exited_on = DatetimeField()
    exit_type = SimpleField()
