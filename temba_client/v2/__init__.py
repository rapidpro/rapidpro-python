from ..base import BaseCursorClient
from .types import (
    Archive,
    Boundary,
    Broadcast,
    Campaign,
    CampaignEvent,
    Channel,
    Classifier,
    Contact,
    Export,
    Field,
    Flow,
    FlowStart,
    Global,
    Group,
    Label,
    Message,
    Org,
    Resthook,
    ResthookEvent,
    ResthookSubscriber,
    Run,
)


class TembaClient(BaseCursorClient):
    """
    Client for the Temba API v2
    :param str host: server hostname, e.g. 'rapidpro.io'
    :param str token: organization API token
    :param str user_agent: string to be included in the User-Agent header
    """

    def __init__(self, host, token, user_agent=None, verify_ssl=None, transformer=None):
        super(TembaClient, self).__init__(host, token, 2, user_agent, verify_ssl, transformer=transformer)

    # ==================================================================================================================
    # Fetch object operations
    # ==================================================================================================================

    def get_archives(self, type=None, period=None, before=None, after=None):
        """
        Gets all matching archives
        :param str type: "message" or "run"
        :param str period: "daily" or "monthly"
        :param datetime before: created before
        :param datetime after: created after
        :return: archive query
        """

        params = self._build_params(type=type, period=period, before=before, after=after)
        return self._get_query("archives", params, Archive)

    def get_boundaries(self, geometry=None):
        """
        Gets all administrative boundaries
        :return: boundary query
        """
        params = self._build_params(geometry=geometry)
        return self._get_query("boundaries", params, Boundary)

    def get_broadcasts(self, id=None, before=None, after=None):
        """
        Gets all matching broadcasts
        :param id: broadcast id
        :param datetime before: created before
        :param datetime after: created after
        :return: broadcast query
        """
        params = self._build_params(id=id, before=before, after=after)
        return self._get_query("broadcasts", params, Broadcast)

    def get_campaigns(self, uuid=None):
        """
        Gets all matching campaigns
        :param uuid: campaigns UUID
        :return: campaign query
        """
        params = self._build_params(uuid=uuid)
        return self._get_query("campaigns", params, Campaign)

    def get_campaign_events(self, uuid=None, campaign=None):
        """
        Gets all matching campaign events
        :param uuid: event UUID
        :param campaign: campaign object or UUID
        :return: campaign event query
        """
        params = self._build_params(uuid=uuid, campaign=campaign)
        return self._get_query("campaign_events", params, CampaignEvent)

    def get_channels(self, uuid=None, address=None):
        """
        Gets all matching channels
        :param uuid: channel UUID
        :param urn: channel address
        :return: channel query
        """
        params = self._build_params(uuid=uuid, address=address)
        return self._get_query("channels", params, Channel)

    def get_classifiers(self, uuid=None):
        """
        Gets all matching NLU classifiers
        :param uuid: classifier UUID
        :return: classifier query
        """
        params = self._build_params(uuid=uuid)
        return self._get_query("classifiers", params, Classifier)

    def get_contacts(self, uuid=None, urn=None, group=None, deleted=None, before=None, after=None, reverse=None):
        """
        Gets all matching contacts
        :param uuid: contact UUID
        :param urn: contact URN
        :param group: contact group name or UUID
        :param deleted: return deleted contact only
        :param reverse: whether to return contacts ordered in reverse (oldest first).
        :param datetime before: modified before
        :param datetime after: modified after
        :return: contact query
        """
        params = self._build_params(
            uuid=uuid, urn=urn, group=group, deleted=deleted, reverse=reverse, before=before, after=after
        )
        return self._get_query("contacts", params, Contact)

    def get_definitions(self, flows=(), campaigns=(), dependencies=None):
        """
        Gets an export of specified definitions
        :param flows: flow objects or UUIDs to include
        :param campaigns: campaign objects or UUIDs to include
        :param dependencies: whether to include dependencies
        :return: definitions export
        """
        params = self._build_params(flow=flows, campaign=campaigns, dependencies=dependencies)
        return Export.deserialize(self._get_raw("definitions", params))

    def get_fields(self, key=None):
        """
        Gets all matching contact fields
        :param key: field key
        :return: field query
        """
        return self._get_query("fields", self._build_params(key=key), Field)

    def get_flows(self, uuid=None):
        """
        Gets all matching flows
        :param uuid: flow UUID
        :return: flow query
        """
        return self._get_query("flows", self._build_params(uuid=uuid), Flow)

    def get_flow_starts(self, uuid=None):
        """
        Gets all matching flows starts
        :param uuid: flow start UUID
        :return: flow start query
        """
        return self._get_query("flow_starts", self._build_params(uuid=uuid), FlowStart)

    def get_globals(self):
        """
        Gets all globals
        :return: global query
        """
        return self._get_query("globals", {}, Global)

    def get_groups(self, uuid=None, name=None):
        """
        Gets all matching contact groups
        :param uuid: group UUID
        :param name: group name
        :return: group query
        """
        return self._get_query("groups", self._build_params(uuid=uuid, name=name), Group)

    def get_labels(self, uuid=None, name=None):
        """
        Gets all matching message labels
        :param uuid: label UUID
        :param name: label name
        :return: label query
        """
        return self._get_query("labels", self._build_params(uuid=uuid, name=name), Label)

    def get_messages(self, id=None, folder=None, before=None, after=None):
        """
        Gets all matching messages
        :param id: message id
        :param folder: folder name
        :param datetime before: created before
        :param datetime after: created after
        :return: message query
        """
        params = self._build_params(id=id, folder=folder, before=before, after=after)
        return self._get_query("messages", params, Message)

    def get_org(self, retry_on_rate_exceed=False):
        """
        Gets the current organization
        :param retry_on_rate_exceed: whether to sleep and retry if request rate limit exceeded
        :return: the org
        """
        return Org.deserialize(self._get_raw("org", {}, retry_on_rate_exceed))

    def get_resthooks(self):
        """
        Gets all resthooks
        :return: resthook query
        """
        return self._get_query("resthooks", {}, Resthook)

    def get_resthook_events(self, resthook=None):
        """
        Gets all resthook events
        :param resthook: the resthook slug
        :return: resthook event query
        """
        params = self._build_params(resthook=resthook)
        return self._get_query("resthook_events", params, ResthookEvent)

    def get_resthook_subscribers(self, id=None, resthook=None):
        """
        Gets all resthook subscribers
        :param id: subscriber id
        :param resthook: the resthook slug
        :return: resthook subscriber query
        """
        params = self._build_params(id=id, resthook=resthook)
        return self._get_query("resthook_subscribers", params, ResthookSubscriber)

    def get_runs(
        self, uuid=None, flow=None, contact=None, responded=None, before=None, after=None, reverse=None, paths=None
    ):
        """
        Gets all matching flow runs
        :param uuid: flow run UUID
        :param flow: flow object or UUID
        :param contact: contact object or UUID
        :param responded: whether to limit results to runs with responses
        :param datetime before: modified before
        :param datetime after: modified after
        :param reverse: whether to return results ordered in reverse (oldest first).
        :param paths: whether to include path data
        :return: flow run query
        """
        params = self._build_params(
            uuid=uuid,
            flow=flow,
            contact=contact,
            responded=responded,
            reverse=reverse,
            before=before,
            after=after,
            paths=paths,
        )
        return self._get_query("runs", params, Run)

    # ==================================================================================================================
    # Create object operations
    # ==================================================================================================================

    def create_broadcast(self, text, urns=None, contacts=None, groups=None):
        """
        Creates and sends a broadcast to the given URNs, contacts or contact groups
        :param str text: message text
        :param list[str] urns: list of URN strings
        :param list contacts: list of contact objects or UUIDs
        :param list groups: list of group objects or UUIDs
        :return: the new broadcast
        """
        payload = self._build_params(text=text, urns=urns, contacts=contacts, groups=groups)
        return Broadcast.deserialize(self._post("broadcasts", None, payload))

    def create_campaign(self, name, group):
        """
        Creates a new campaign
        :param str name: campaign name
        :param * group: group object, UUID or name
        :return: the new campaign
        """
        payload = self._build_params(name=name, group=group)
        return Campaign.deserialize(self._post("campaigns", None, payload))

    def create_campaign_event(self, campaign, relative_to, offset, unit, delivery_hour, message=None, flow=None):
        """
        Creates a new campaign event
        :param * campaign: campaign object, UUID or name
        :param str relative_to: contact field key
        :param int offset:
        :param str unit:
        :param int delivery_hour:
        :param str message:
        :param * flow: flow object, UUID or name
        :return: the new campaign
        """
        payload = self._build_params(
            campaign=campaign,
            relative_to=relative_to,
            offset=offset,
            unit=unit,
            delivery_hour=delivery_hour,
            message=message,
            flow=flow,
        )
        return CampaignEvent.deserialize(self._post("campaign_events", None, payload))

    def create_contact(self, name=None, language=None, urns=None, fields=None, groups=None):
        """
        Creates a new contact
        :param str name: full name
        :param str language: the language code, e.g. "eng"
        :param list[str] urns: list of URN strings
        :param dict[str,str] fields: dictionary of contact field values
        :param list groups: list of group objects, UUIDs or names
        :return: the new contact
        """
        payload = self._build_params(name=name, language=language, urns=urns, fields=fields, groups=groups)
        return Contact.deserialize(self._post("contacts", None, payload))

    def create_field(self, name, type):
        """
        Creates a new contact field
        :param str name: field name
        :param str type: field type
        :return: the new field
        """
        return Field.deserialize(self._post("fields", None, self._build_params(name=name, type=type)))

    def create_flow_start(
        self, flow, urns=None, contacts=None, groups=None, restart_participants=None, exclude_active=None, params=None
    ):
        """
        Creates a new flow start
        :param str flow: flow UUID
        :param list[str] urns: URNs of contacts to start
        :param list[str] contacts: UUIDs of contacts to start
        :param list[str] groups: UUIDs of contact groups to start
        :param bool restart_participants: whether to restart participants already in this flow
        :param bool exclude_active: whether to exclude contacts currently in other flows
        :param * params: a dictionary of parameters to pass to the flow
        :return: the new label
        """
        payload = self._build_params(
            flow=flow,
            urns=urns,
            contacts=contacts,
            groups=groups,
            restart_participants=restart_participants,
            exclude_active=exclude_active,
            params=params,
        )
        return FlowStart.deserialize(self._post("flow_starts", None, payload))

    def create_global(self, name, value):
        """
        Creates a new global
        :param str name: global name
        :param str value: global value
        :return: the new global
        """
        payload = self._build_params(name=name, value=value)
        return Global.deserialize(self._post("globals", None, payload))

    def create_group(self, name):
        """
        Creates a new contact group
        :param str name: group name
        :return: the new group
        """
        return Group.deserialize(self._post("groups", None, self._build_params(name=name)))

    def create_label(self, name):
        """
        Creates a new message label
        :param str name: label name
        :return: the new label
        """
        return Label.deserialize(self._post("labels", None, self._build_params(name=name)))

    def create_message(self, contact, text, attachments):
        """
        Creates a new outgoing message
        :param str contact: contact UUID
        :param str text: message text
        :param list[str] attachments: message attachments
        :return: the new message
        """
        return Message.deserialize(
            self._post("messages", None, self._build_params(contact=contact, text=text, attachments=attachments))
        )

    def create_resthook_subscriber(self, resthook, target_url):
        """
        Creates a new resthook subscriber
        :param resthook: the resthook slug
        :param target_url: the target URL
        :return: the new subscriber
        """
        payload = self._build_params(resthook=resthook, target_url=target_url)
        return ResthookSubscriber.deserialize(self._post("resthook_subscribers", None, payload))

    # ==================================================================================================================
    # Update object operations
    # ==================================================================================================================

    def update_campaign(self, campaign, name, group):
        """
        Updates an existing campaign
        :param * campaign: campaign object, UUID or URN
        :param str name: campaign name
        :param * group: group object, UUID or name
        :return: the updated campaign
        """
        params = self._build_id_param(uuid=campaign)
        payload = self._build_params(name=name, group=group)
        return Campaign.deserialize(self._post("campaigns", params, payload))

    def update_campaign_event(self, event, relative_to, offset, unit, delivery_hour, message=None, flow=None):
        """
        Updates an existing campaign event
        :param * event: campaign event object, UUID or name
        :param str relative_to: contact field key
        :param int offset:
        :param str unit:
        :param int delivery_hour:
        :param str message:
        :param * flow: flow object, UUID or name
        :return: the new campaign
        """
        params = self._build_id_param(uuid=event)
        payload = self._build_params(
            relative_to=relative_to, offset=offset, unit=unit, delivery_hour=delivery_hour, message=message, flow=flow
        )
        return CampaignEvent.deserialize(self._post("campaign_events", params, payload))

    def update_contact(self, contact, name=None, language=None, urns=None, fields=None, groups=None):
        """
        Updates an existing contact
        :param * contact: contact object, UUID or URN
        :param str name: full name
        :param str language: the language code, e.g. "eng"
        :param list[str] urns: list of URN strings
        :param dict[str,str] fields: dictionary of contact field values
        :param list groups: list of group objects or UUIDs
        :return: the updated contact
        """
        is_urn = isinstance(contact, str) and ":" in contact
        params = self._build_id_param(**{"urn" if is_urn else "uuid": contact})
        payload = self._build_params(name=name, language=language, urns=urns, fields=fields, groups=groups)
        return Contact.deserialize(self._post("contacts", params, self._build_params(**payload)))

    def update_field(self, field, name, type):
        """
        Updates an existing contact field
        :param * field: contact field object or key
        :param str name: field name
        :param str type: field type
        :return: the updated field
        """
        params = self._build_id_param(key=field)
        payload = self._build_params(name=name, type=type)
        return Field.deserialize(self._post("fields", params, payload))

    def update_global(self, glbl, value):
        """
        Updates an existing global
        :param * glbl: global object or key
        :param str value: new value
        :return: the updated global
        """
        params = self._build_id_param(key=glbl)
        payload = self._build_params(value=value)
        return Global.deserialize(self._post("globals", params, payload))

    def update_group(self, group, name):
        """
        Updates an existing contact group
        :param * group: group object or UUID
        :param str name: group name
        :return: the updated group
        """
        return Group.deserialize(self._post("groups", self._build_id_param(uuid=group), self._build_params(name=name)))

    def update_label(self, label, name):
        """
        Updates an existing message label
        :param * label: label object or UUID
        :param str name: label name
        :return: the updated label
        """
        return Label.deserialize(self._post("labels", self._build_id_param(uuid=label), self._build_params(name=name)))

    # ==================================================================================================================
    # Delete object operations
    # ==================================================================================================================

    def delete_campaign_event(self, event):
        """
        Deletes an existing contact group
        :param * event: campaign event object or UUID
        """
        self._delete("campaign_events", self._build_id_param(uuid=event))

    def delete_contact(self, contact):
        """
        Deletes an existing contact
        :param * contact: contact object, UUID or URN
        """
        is_urn = isinstance(contact, str) and ":" in contact
        params = self._build_id_param(**{"urn" if is_urn else "uuid": contact})
        self._delete("contacts", params)

    def delete_group(self, group):
        """
        Deletes an existing contact group
        :param * group: group object or UUID
        """
        self._delete("groups", self._build_id_param(uuid=group))

    def delete_label(self, label):
        """
        Deletes an existing message label
        :param * label: label object or UUID
        """
        self._delete("labels", self._build_id_param(uuid=label))

    def delete_resthook_subscriber(self, subscriber):
        """
        Deletes an existing resthook subscriber
        :param * subscriber: the resthook subscriber or id
        """
        self._delete("resthook_subscribers", self._build_id_param(id=subscriber))

    # ==================================================================================================================
    # Bulk object operations
    # ==================================================================================================================

    def bulk_add_contacts(self, contacts, group):
        """
        Adds contacts to a group
        :param list[*] contacts: contact objects, UUIDs or URNs
        :param * group: contact group object or UUID
        """
        self._post("contact_actions", None, self._build_params(contacts=contacts, action="add", group=group))

    def bulk_remove_contacts(self, contacts, group):
        """
        Removes contacts from a group
        :param list[*] contacts: contact objects, UUIDs or URNs
        :param * group: contact group object or UUID
        """
        self._post("contact_actions", None, self._build_params(contacts=contacts, action="remove", group=group))

    def bulk_block_contacts(self, contacts):
        """
        Blocks contacts
        :param list[*] contacts: contact objects, UUIDs or URNs
        """
        self._post("contact_actions", None, self._build_params(contacts=contacts, action="block"))

    def bulk_unblock_contacts(self, contacts):
        """
        Un-blocks contacts
        :param list[*] contacts: contact objects, UUIDs or URNs
        """
        self._post("contact_actions", None, self._build_params(contacts=contacts, action="unblock"))

    def bulk_interrupt_contacts(self, contacts):
        """
        Interrupt active flow runs for contacts
        :param list[*] contacts: contact objects, UUIDs or URNs
        """
        self._post("contact_actions", None, self._build_params(contacts=contacts, action="interrupt"))

    def bulk_archive_contact_messages(self, contacts):
        """
        Archives all messages for contacts
        :param list[*] contacts: contact objects, UUIDs or URNs
        """
        self._post("contact_actions", None, self._build_params(contacts=contacts, action="archive_messages"))

    def bulk_delete_contacts(self, contacts):
        """
        Deletes contacts
        :param list[*] contacts: contact objects, UUIDs or URNs
        """
        self._post("contact_actions", None, self._build_params(contacts=contacts, action="delete"))

    def bulk_label_messages(self, messages, label=None, label_name=None):
        """
        Labels messages
        :param list[*] messages: message objects or ids
        :param * label: existing label object or UUID
        :param str label_name: label name which can be created if required
        """
        payload = self._build_params(messages=messages, action="label", label=label, label_name=label_name)
        self._post("message_actions", None, payload)

    def bulk_unlabel_messages(self, messages, label=None, label_name=None):
        """
        Un-labels messages
        :param list[*] messages: message objects or ids
        :param * label: existing label object or UUID
        :param str label_name: label name which is ignored if doesn't exist
        """
        payload = self._build_params(messages=messages, action="unlabel", label=label, label_name=label_name)
        self._post("message_actions", None, payload)

    def bulk_archive_messages(self, messages):
        """
        Archives messages
        :param list[*] messages: message objects or ids
        """
        self._post("message_actions", None, self._build_params(messages=messages, action="archive"))

    def bulk_restore_messages(self, messages):
        """
        Restores previously archived messages
        :param list[*] messages: message objects or ids
        """
        self._post("message_actions", None, self._build_params(messages=messages, action="restore"))

    def bulk_delete_messages(self, messages):
        """
        Deletes messages
        :param list[*] messages: message objects or ids
        """
        self._post("message_actions", None, self._build_params(messages=messages, action="delete"))
