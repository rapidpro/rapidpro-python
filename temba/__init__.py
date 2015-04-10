from __future__ import unicode_literals

from .base import AbstractTembaClient
from .types import Broadcast, Contact, Group, Field, Flow, Label, Message, Run


class TembaClient(AbstractTembaClient):
    """
    Client for the Temba API v1

    :param str host: server hostname, e.g. 'rapidpro.io'
    :param str token: organization API token
    :param bool ssl: use SSL
    :param bool debug: print debugging statements
    """
    def __init__(self, host, token, ssl=True, debug=False):
        super(TembaClient, self).__init__(host, token, ssl, debug)

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

    def create_field(self, label, value_type):
        """
        Creates a new contact field

        :param str label: field label
        :param str value_type: one of 'T' (text), 'N' (decimal), 'D' (datetime), 'S' (state), 'I' (district)
        :return: the new field
        """
        params = self._build_params(label=label, value_type=value_type)
        return Field.deserialize(self._post('fields', params))

    def create_label(self, name, parent):
        """
        Creates a new message label

        :param str name: label name
        :param str parent: parent label UUID
        :return: the new message label
        """
        params = self._build_params(name=name, parent=parent)
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

    def delete_contact(self, contact):
        """
        Deletes an existing contact

        :param contact: contact object or UUID
        """
        self._delete('contacts', self._build_params(uuid=contact))

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
        :return: list of broadcasts
        """
        params = self._build_params(id=ids, status=statuses, before=before, after=after)
        return Broadcast.deserialize_list(self._get_multiple('broadcasts', params, pager))

    def get_contact(self, uuid):
        """
        Gets a single contact by its UUID

        :param str uuid: contact UUID
        :return: the contact
        """
        return Contact.deserialize(self._get_single('contacts', {'uuid': uuid}))

    def get_contacts(self, uuids=None, urns=None, groups=None, pager=None):
        """
        Gets all matching contacts

        :param list[str] uuids: list of UUIDs
        :param list[str] urns: list of URN strings
        :param list groups: list of group objects or UUIDs
        :return: list of contacts
        """
        params = self._build_params(uuid=uuids, urns=urns, group_uuids=groups)
        return Contact.deserialize_list(self._get_multiple('contacts', params, pager))

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
                     reverse=None, pager=None):
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
        :param list[str] labels: list of message labels
        :param datetime before: created before
        :param datetime after: created after
        :param str text: containing text
        :param bool reverse: oldest messages first
        :param object pager: pager for paged results
        :return: list of messages
        """
        params = self._build_params(id=ids, broadcast=broadcasts, urns=urns, contact=contacts, group_uuids=groups,
                                    status=statuses, direction=direction, type=_types, label=labels,
                                    before=before, after=after, text=text, reverse=reverse)
        return Message.deserialize_list(self._get_multiple('messages', params, pager))

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
        :return: list of flow runs
        """
        params = self._build_params(run=ids, flow_uuid=flows, group_uuids=groups, before=before, after=after)
        return Run.deserialize_list(self._get_multiple('runs', params, pager))

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

    def update_label(self, uuid, name, parent):
        """
        Updates an existing message label

        :param str uuid: label UUID
        :param str name: label name
        :param str parent: parent label UUID
        :return: the updated message label
        """
        params = self._build_params(uuid=uuid, name=name, parent=parent)
        return Label.deserialize(self._post('labels', params))
