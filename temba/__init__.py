from __future__ import unicode_literals

from .base import AbstractTembaClient
from .types import TembaException, TembaType, Broadcast, Contact, Group, Field, Flow, Message, Run


class TembaClient(AbstractTembaClient):
    """
    Client for the Temba API v1
    """
    def create_broadcast(self, text, urns=None, contacts=None, groups=None):
        """
        Creates and sends a broadcast to the given URNs, contact UUIDs or group UUIDs
        """
        params = self._build_params(text=text, urns=urns, contacts=contacts, groups=groups)
        return Broadcast.deserialize(self._post_single('broadcasts', params))

    def create_contact(self, name, urns, fields, groups):
        """
        Creates a new contact
        """
        params = self._build_params(name=name, urns=urns, fields=fields, group_uuids=groups)
        return Contact.deserialize(self._post_single('contacts', params))

    def delete_contact(self, uuid):
        """
        Deletes an existing contact
        """
        self._delete('contacts', {'uuid': uuid})

    def get_broadcast(self, _id):
        """
        Gets a single contact by its id
        """
        return Broadcast.deserialize(self._get_single('broadcasts', {'id': _id}))

    def get_contact(self, uuid):
        """
        Gets a single contact by its UUID
        """
        return Contact.deserialize(self._get_single('contacts', {'uuid': uuid}))

    def get_contacts(self, name=None, groups=None):
        """
        Gets all matching contacts
        """
        params = self._build_params(name=name, group_uuids=groups)
        return Contact.deserialize_list(self._get_all('contacts', params))

    def get_field(self, key):
        """
        Gets a single contact field by its key
        """
        return Field.deserialize(self._get_single('fields', {'key': key}))

    def get_fields(self):
        """
        Gets all fields
        """
        return Field.deserialize_list(self._get_all('fields', {}))

    def get_flow(self, uuid):
        """
        Gets a single flow by its UUID
        """
        return Flow.deserialize(self._get_single('flows', {'uuid': uuid}))

    def get_flows(self, before=None, after=None):
        """
        Gets all flows
        """
        params = self._build_params(before=before, after=after)
        return Flow.deserialize_list(self._get_all('flows', params))

    def get_group(self, uuid):
        """
        Gets a single flow by its UUID
        """
        return Group.deserialize(self._get_single('groups', {'uuid': uuid}))

    def get_groups(self, name=None):
        """
        Gets all matching groups
        """
        params = self._build_params(name=name)
        return Group.deserialize_list(self._get_all('groups', params))

    def get_messages(self, contacts=None, groups=None, status=None, direction=None, _type=None,
                     before=None, after=None):
        """
        Gets all matching messages
        """
        params = self._build_params(contact=contacts, group_uuids=groups,
                                    status=status, direction=direction, type=_type,
                                    before=before, after=after)
        return Message.deserialize_list(self._get_all('messages', params))

    def get_run(self, _id):
        """
        Gets a single flow run by its id
        """
        return Run.deserialize(self._get_single('runs', {'run': _id}))

    def get_runs(self, flow=None, groups=None, before=None, after=None):
        """
        Gets all matching flow runs
        """
        params = self._build_params(flow_uuid=flow, group_uuids=groups, before=before, after=after)
        return Run.deserialize_list(self._get_all('runs', params))

    def update_contact(self, uuid, name, urns, fields, groups):
        """
        Updates an existing contact
        """
        params = self._build_params(uuid=uuid, name=name, urns=urns, fields=fields, group_uuids=groups)
        return Contact.deserialize(self._post_single('contacts', params))
