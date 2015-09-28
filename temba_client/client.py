from __future__ import absolute_import, unicode_literals

from .base import AbstractTembaClient
from .types import Boundary, Broadcast, Campaign, Contact, Group, Event, Field, Flow, Label, Message, Org, Result, Run


class TembaClient(AbstractTembaClient):
    """
    Client for the Temba API v1

    :param str host: server hostname, e.g. 'rapidpro.io'
    :param str token: organization API token
    :param str user_agent: string to be included in the User-Agent header
    """
    def __init__(self, host, token, user_agent=None):
        super(TembaClient, self).__init__(host, token, user_agent)

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
        params = self._build_params(text=text, urns=urns, contacts=contacts, groups=groups)
        return Broadcast.deserialize(self._post('broadcasts', params))

    def create_campaign(self, name, group):
        """
        Creates a new campaign

        :param str name: name
        :param str group: contact group object or UUID
        :return: the new campaign
        """
        params = self._build_params(name=name, group_uuid=group)
        return Campaign.deserialize(self._post('campaigns', params))

    def create_contact(self, name, urns, fields, groups):
        """
        Creates a new contact

        :param str name: full name
        :param list[str] urns: list of URN strings
        :param dict[str,str] fields: dictionary of contact field values
        :param list groups: list of group objects or UUIDs
        :return: the new contact
        """
        params = self._build_params(name=name, urns=urns, fields=fields, group_uuids=groups)
        return Contact.deserialize(self._post('contacts', params))

    def create_event(self, campaign, relative_to, offset, unit, delivery_hour, message=None, flow=None):
        """
        Creates a new campaign event

        :param str campaign: campaign object or UUID
        :param str relative_to: label of contact field containing a date
        :param int offset: time offset from date
        :param str unit: one of 'M' (minutes), 'H' (hours), 'D' (days), 'W' (weeks)
        :param int delivery_hour: hour of the day to fire event
        :param str message: message to send (optional)
        :param str flow: flow object or UUID to start (optional)
        :return: the new event
        """
        params = self._build_params(campaign_uuid=campaign, relative_to=relative_to, offset=offset, unit=unit,
                                    delivery_hour=delivery_hour, message=message, flow_uuid=flow)
        return Event.deserialize(self._post('events', params))

    def create_field(self, label, value_type):
        """
        Creates a new contact field

        :param str label: field label
        :param str value_type: one of 'T' (text), 'N' (decimal), 'D' (datetime), 'S' (state), 'I' (district)
        :return: the new field
        """
        params = self._build_params(label=label, value_type=value_type)
        return Field.deserialize(self._post('fields', params))

    def create_flow(self, name, _type):
        """
        Creates a new flow

        :param str name: flow name
        :param str _type: flow type: F, M or V
        :return: the new flow
        """
        params = self._build_params(name=name, flow_type=_type)
        return Flow.deserialize(self._post('flows', params))

    def create_label(self, name):
        """
        Creates a new message label

        :param str name: label name
        :return: the new message label
        """
        params = self._build_params(name=name)
        return Label.deserialize(self._post('labels', params))

    def create_runs(self, flow, contacts, restart_participants):
        """
        Creates new flow runs for the given contacts

        :param str flow: flow UUID
        :param list contacts: list of contact objects or UUIDs
        :param bool restart_participants: whether or not to restart participants already in the flow
        :return: list of new runs
        """
        params = self._build_params(flow_uuid=flow, contacts=contacts, restart_participants=restart_participants)
        return Run.deserialize_list(self._post('runs', params))

    # ==================================================================================================================
    # Delete object operations
    # ==================================================================================================================

    def delete_contact(self, contact):
        """
        Deletes an existing contact

        :param contact: contact object or UUID
        """
        self._delete('contacts', self._build_params(uuid=contact))

    def delete_event(self, event):
        """
        Deletes an existing campaign event

        :param event: event object or UUID
        """
        self._delete('events', self._build_params(uuid=event))

    # ==================================================================================================================
    # Fetch object(s) operations
    # ==================================================================================================================

    def get_boundaries(self, pager=None):
        """
        Gets all boundaries

        :param object pager: pager for paged results
        :return: list of boundaries
        """
        return Boundary.deserialize_list(self._get_multiple('boundaries', {}, pager))

    def get_broadcast(self, _id):
        """
        Gets a single broadcast by its id

        :param int _id: broadcast id
        :return: the broadcast
        """
        return Broadcast.deserialize(self._get_single('broadcasts', {'id': _id}))

    def get_broadcasts(self, ids=None, statuses=None, before=None, after=None, pager=None):
        """
        Gets all matching broadcasts

        :param list[int] ids: list of ids
        :param list[str] statuses: list of statuses
        :param datetime before: created before this datetime
        :param datetime after: created after this datetime
        :param object pager: pager for paged results
        :return: list of broadcasts
        """
        params = self._build_params(id=ids, status=statuses, before=before, after=after)
        return Broadcast.deserialize_list(self._get_multiple('broadcasts', params, pager))

    def get_campaign(self, uuid):
        """
        Gets a single campaign by its UUID

        :param str uuid: campaign UUID
        :return: the campaign
        """
        return Campaign.deserialize(self._get_single('campaigns', {'uuid': uuid}))

    def get_campaigns(self, uuids=None, before=None, after=None, pager=None):
        """
        Gets all matching campaigns

        :param list[str] uuids: list of UUIDs
        :return: list of campaigns
        """
        params = self._build_params(uuid=uuids, before=before, after=after)
        return Campaign.deserialize_list(self._get_multiple('campaigns', params, pager))

    def get_contact(self, uuid):
        """
        Gets a single contact by its UUID

        :param str uuid: contact UUID
        :return: the contact
        """
        return Contact.deserialize(self._get_single('contacts', {'uuid': uuid}))

    def get_contacts(self, uuids=None, urns=None, groups=None, before=None, after=None, pager=None):
        """
        Gets all matching contacts

        :param list[str] uuids: list of UUIDs
        :param list[str] urns: list of URN strings
        :param list groups: list of group objects or UUIDs
        :param datetime before: modified before this datetime
        :param datetime after: modified after this datetime
        :param object pager: pager for paged results
        :return: list of contacts
        """
        params = self._build_params(uuid=uuids, urns=urns, group_uuids=groups, before=before, after=after)
        return Contact.deserialize_list(self._get_multiple('contacts', params, pager))

    def get_event(self, uuid):
        """
        Gets a single campaign event by its UUID

        :param str uuid: campaign UUID
        :return: the event
        """
        return Event.deserialize(self._get_single('events', {'uuid': uuid}))

    def get_events(self, uuids=None, campaigns=None, before=None, after=None, pager=None):
        """
        Gets all matching campaign events

        :param list[str] uuids: list of UUIDs
        :return: list of events
        """
        params = self._build_params(uuid=uuids, campaign_uuid=campaigns, before=before, after=after)
        return Event.deserialize_list(self._get_multiple('events', params, pager))

    def get_field(self, key):
        """
        Gets a single contact field by its key

        :param str key: field key
        :return: the field
        """
        return Field.deserialize(self._get_single('fields', {'key': key}))

    def get_fields(self, pager=None):
        """
        Gets all contact fields

        :param object pager: pager for paged results
        :return: list of fields
        """
        return Field.deserialize_list(self._get_multiple('fields', {}, pager))

    def get_flow(self, uuid):
        """
        Gets a single flow by its UUID

        :param str uuid: flow UUID
        :return: the flow
        """
        return Flow.deserialize(self._get_single('flows', {'uuid': uuid}))

    def get_flows(self, uuids=None, archived=None, labels=None, before=None, after=None, pager=None):
        """
        Gets all flows

        :param list[str] uuids: list of flow UUIDs
        :param bool archived: flow archived state
        :param list[str] labels: list of flow labels
        :param datetime before: created before
        :param datetime after: created after
        :param object pager: pager for paged results
        :return: list of flows
        """
        params = self._build_params(uuid=uuids, archived=archived, label=labels, before=before, after=after)
        return Flow.deserialize_list(self._get_multiple('flows', params, pager))

    def get_group(self, uuid):
        """
        Gets a single group by its UUID

        :param str uuid: group UUID
        :return: the group
        """
        return Group.deserialize(self._get_single('groups', {'uuid': uuid}))

    def get_groups(self, uuids=None, name=None, pager=None):
        """
        Gets all matching groups

        :param list[str] uuids: list of group UUIDs
        :param str name: partial name match
        :param object pager: pager for paged results
        :return: list of groups
        """
        params = self._build_params(uuid=uuids, name=name)
        return Group.deserialize_list(self._get_multiple('groups', params, pager))

    def get_label(self, uuid):
        """
        Gets a single message label by its UUID

        :param str uuid: label UUID
        :return: the label
        """
        return Label.deserialize(self._get_single('labels', {'uuid': uuid}))

    def get_labels(self, uuids=None, name=None, pager=None):
        """
        Gets all matching message labels

        :param list[str] uuids: list of label UUIDs
        :param str name: partial name match
        :param object pager: pager for paged results
        :return: list of labels
        """
        params = self._build_params(uuid=uuids, name=name)
        return Label.deserialize_list(self._get_multiple('labels', params, pager))

    def get_message(self, _id):
        """
        Gets a single message by its id

        :param int _id: message id
        :return: the message
        """
        return Message.deserialize(self._get_single('messages', {'id': _id}))

    def get_messages(self, ids=None, broadcasts=None, urns=None, contacts=None, groups=None, statuses=None,
                     direction=None, _types=None, labels=None, before=None, after=None, text=None,
                     archived=None, pager=None):
        """
        Gets all matching messages

        :param list[int] ids: list of message ids
        :param list broadcasts: list of broadcast objects or ids
        :param list[str] urns: list of contact URN strings
        :param list contacts: list of contact objects or UUIDs
        :param list groups: list of group objects or UUIDs
        :param list[str] statuses: list of message statuses
        :param str direction: message direction (I or O)
        :param list[str] _types: list of message types
        :param list[str] labels: list of message labels. Prefix the label name with + to require it and with - to exclude it.
        :param datetime before: created before
        :param datetime after: created after
        :param str text: containing text
        :param bool archived: include or don't include archived messages
        :param object pager: pager for paged results
        :return: list of messages
        """
        params = self._build_params(id=ids, broadcast=broadcasts,
                                    urns=urns, contact=contacts, group_uuids=groups,
                                    status=statuses, direction=direction, type=_types, label=labels,
                                    before=before, after=after, text=text, archived=archived)
        return Message.deserialize_list(self._get_multiple('messages', params, pager))

    def get_org(self):
        """
        Gets the current organization

        :return: the org
        """
        return Org.deserialize(self._get_single('org', {}, from_results=False))

    def get_results(self, ruleset=None, contact_field=None, segment=None):
        """
        Gets all flow results for the passed in ruleset or contact field with an optional segment

        :param ruleset: a ruleset uuid
        :param contact_field: a contact field label
        :param segment:  segments are expected in these formats instead:
               { ruleset: 1515, categories: ["Red", "Blue"] }  // segmenting by another field, for those categories
               { groups: 124,151,151 }                         // segment by each each group in the passed in ids
               { location: "State", parent: null }             // segment for each admin boundary within the parent
        :return: segmented results
        """
        params = self._build_params(ruleset=ruleset, contact_field=contact_field, segment=segment)
        return Result.deserialize_list(self._get_all('results', params))

    def get_run(self, _id):
        """
        Gets a single flow run by its id

        :param int _id: run id
        :return: the flow run
        """
        return Run.deserialize(self._get_single('runs', {'run': _id}))

    def get_runs(self, ids=None, flows=None, groups=None, before=None, after=None, pager=None):
        """
        Gets all matching flow runs

        :param list[int] ids: list of run ids
        :param list[str] flows: list of flow objects or UUIDs
        :param list groups: list of group objects or UUIDs
        :param datetime before: created before
        :param datetime after: created after
        :param object pager: pager for paged results
        :return: list of flow runs
        """
        params = self._build_params(run=ids, flow_uuid=flows, group_uuids=groups, before=before, after=after)
        return Run.deserialize_list(self._get_multiple('runs', params, pager))

    # ==================================================================================================================
    # Update object operations
    # ==================================================================================================================

    def update_contact(self, uuid, name, urns, fields, groups):
        """
        Updates an existing contact

        :param str uuid: contact UUID
        :param str name: full name
        :param list[str] urns: list of URN strings
        :param dict[str,str] fields: dictionary of contact field values
        :param list groups: list of group objects or UUIDs
        :return: the updated contact
        """
        params = self._build_params(uuid=uuid, name=name, urns=urns, fields=fields, group_uuids=groups)
        return Contact.deserialize(self._post('contacts', params))

    def update_flow(self, uuid, name, _type):
        """
        Updates an existing flow

        :param str uuid: flow UUID
        :param str name: flow name
        :param str _type: flow type: F, M or V
        :return: the updated flow
        """
        params = self._build_params(uuid=uuid, name=name, flow_type=_type)
        return Flow.deserialize(self._post('flows', params))

    def update_label(self, uuid, name):
        """
        Updates an existing message label

        :param str uuid: label UUID
        :param str name: label name
        :return: the updated message label
        """
        params = self._build_params(uuid=uuid, name=name)
        return Label.deserialize(self._post('labels', params))

    # ==================================================================================================================
    # Bulk contact operations
    # ==================================================================================================================

    def add_contacts(self, contacts, group=None, group_uuid=None):
        """
        Adds the given contacts to a contact group. Group can be specified by name or by UUID.

        :param list[str] contacts: the contact UUIDs
        :param str group: the group name
        :param str group_uuid: the group UUID
        """
        params = self._build_params(contacts=contacts, action='add', group=group, group_uuid=group_uuid)
        self._post('contact_actions', params)

    def remove_contacts(self, contacts, group=None, group_uuid=None):
        """
        Removes a label from the given messages. Label can be specified by name or by UUID.

        :param list[str] contacts: the contact UUIDs
        :param str group: the group name
        :param str group_uuid: the group UUID
        """
        params = self._build_params(contacts=contacts, action='remove', group=group, group_uuid=group_uuid)
        self._post('contact_actions', params)

    def block_contacts(self, contacts):
        """
        Blocks the given contacts.

        :param list[str] contacts: the contact UUIDs
        """
        self._post('contact_actions', self._build_params(contacts=contacts, action='block'))

    def unblock_contacts(self, contacts):
        """
        Unblocks the given contacts.

        :param list[str] contacts: the contact UUIDs
        """
        self._post('contact_actions', self._build_params(contacts=contacts, action='unblock'))

    def expire_contacts(self, contacts):
        """
        Forces expiration of the given contacts' active flow runs.

        :param list[str] contacts: the contact UUIDs
        """
        self._post('contact_actions', self._build_params(contacts=contacts, action='expire'))

    def delete_contacts(self, contacts):
        """
        Permanently deletes the given contacts.

        :param list[str] contacts: the contact UUIDs
        """
        self._post('contact_actions', self._build_params(contacts=contacts, action='delete'))

    # ==================================================================================================================
    # Bulk message operations
    # ==================================================================================================================

    def label_messages(self, messages, label=None, label_uuid=None):
        """
        Applies a label to the given messages. Label can be specified by name or by UUID. If specified by name and it
        doesn't exist, it will be created.

        :param list[int] messages: the message ids
        :param str label: the label name
        :param str label_uuid: the label UUID
        """
        params = self._build_params(messages=messages, action='label', label=label, label_uuid=label_uuid)
        self._post('message_actions', params)

    def unlabel_messages(self, messages, label=None, label_uuid=None):
        """
        Removes a label from the given messages. Label can be specified by name or by UUID.

        :param list[int] messages: the message ids
        :param str label: the label name
        :param str label_uuid: the label UUID
        """
        params = self._build_params(messages=messages, action='unlabel', label=label, label_uuid=label_uuid)
        self._post('message_actions', params)

    def archive_messages(self, messages):
        """
        Archives the given messages.

        :param list[int] messages: the message ids
        """
        self._post('message_actions', self._build_params(messages=messages, action='archive'))

    def unarchive_messages(self, messages):
        """
        Un-archives (restores) the given messages.

        :param list[int] messages: the message ids
        """
        self._post('message_actions', self._build_params(messages=messages, action='unarchive'))

    def delete_messages(self, messages):
        """
        Permanently deletes the given messages.

        :param list[int] messages: the message ids
        """
        self._post('message_actions', self._build_params(messages=messages, action='delete'))
