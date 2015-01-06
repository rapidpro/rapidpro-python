from __future__ import unicode_literals

import json
import requests

from abc import ABCMeta
from .types import TembaException, TembaType, Contact, Group, Field, Flow, Message, Run


class AbstractTembaClient(object):
    """
    Abstract and version agnostic base client class
    """
    __metaclass__ = ABCMeta

    def __init__(self, host, token, ssl=True, debug=False):
        if host.startswith('http'):
            self.root_url = host
        else:
            self.root_url = '%s://%s/api/v1' % ('https' if ssl else 'http', host)

        self.token = token
        self.debug = debug

    def _get_single(self, endpoint, **params):
        """
        GETs a single result from the given endpoint. Throws an exception if there are no or multiple results.
        """
        url = '%s/%s.json' % (self.root_url, endpoint)
        response = self._request('get', url, params=params)

        num_results = len(response['results'])

        if num_results > 1:
            raise TembaException("Request for single object returned %d objects" % num_results)
        elif num_results == 0:
            raise TembaException("Request for single object returned no objects")
        else:
            return response['results'][0]

    def _get_all(self, endpoint, **params):
        """
        GETs all results from the given endpoint
        """
        num_requests = 0
        results = []

        url = '%s/%s.json' % (self.root_url, endpoint)
        while url:
            response = self._request('get', url, params=params)
            num_requests += 1
            results += response['results']
            url = response['next']

        return results

    def _post_single(self, endpoint, payload):
        """
        POSTs to the given endpoint which must return a single item
        """
        url = '%s/%s.json' % (self.root_url, endpoint)
        return self._request('post', url, body=payload)

    def _delete(self, endpoint, **params):
        """
        DELETEs to the given endpoint which won't return anything
        """
        url = '%s/%s.json' % (self.root_url, endpoint)
        return self._request('delete', url, params=params)

    def _request(self, method, url, body=None, params=None):
        """
        Makes a GET or POST request to the given URL and returns the parsed JSON
        """
        headers = {'Content-type': 'application/json',
                   'Accept': 'application/json',
                   'Authorization': 'Token %s' % self.token}

        if self.debug:
            print "%s %s %s" % (method.upper(), url, json.dumps(params if params else body))

        try:
            args = {'headers': headers}
            if body:
                args['data'] = json.dumps(body)
            if params:
                args['params'] = params

            response = requests.request(method, url, params=params, headers=headers)

            if self.debug:
                print " -> %s" % response.content

            response.raise_for_status()

            return response.json() if response.content else None
        except requests.HTTPError, ex:
            raise TembaException("Request error", ex)


class TembaClient(AbstractTembaClient):
    """
    Client for the Temba API v1
    """
    def create_contact(self, name, urns, fields, group_uuids):
        """
        Creates a new contact
        """
        payload = {'name': name, 'urns': urns, 'fields': fields, 'group_uuids': group_uuids}
        return Contact.deserialize(self._post_single('contacts', payload))

    def update_contact(self, uuid, name, urns, fields, group_uuids):
        """
        Updates an existing contact
        """
        payload = {'uuid': uuid, 'name': name, 'urns': urns, 'fields': fields, 'group_uuids': group_uuids}
        return Contact.deserialize(self._post_single('contacts', payload))

    def delete_contact(self, uuid):
        """
        Updates an existing contact
        """
        self._delete('contacts', uuid=uuid)

    def get_contact(self, uuid):
        """
        Gets a single contact by its UUID
        """
        return Contact.deserialize(self._get_single('contacts', uuid=uuid))

    def get_contacts(self, name=None, group_uuids=None):
        """
        Gets all matching contacts
        """
        params = {}
        if name is not None:
            params['name'] = name
        if group_uuids is not None:
            params['group_uuids'] = group_uuids

        return Contact.deserialize_list(self._get_all('contacts', **params))

    def get_field(self, key):
        """
        Gets a single contact field by its key
        """
        return Field.deserialize(self._get_single('fields', key=key))

    def get_fields(self):
        """
        Gets all fields
        """
        return Field.deserialize_list(self._get_all('fields'))

    def get_flow(self, uuid):
        """
        Gets a single flow by its UUID
        """
        return Flow.deserialize(self._get_single('flows', uuid=uuid))

    def get_flows(self):
        """
        Gets all flows
        """
        return Flow.deserialize_list(self._get_all('flows'))

    def get_group(self, uuid):
        """
        Gets a single flow by its UUID
        """
        return Group.deserialize(self._get_single('groups', uuid=uuid))

    def get_groups(self, name=None):
        """
        Gets all matching groups
        """
        params = {}
        if name is not None:
            params['name'] = name

        return Group.deserialize_list(self._get_all('groups', **params))

    def get_message(self, _id):
        """
        Gets a single message by its id
        """
        return Message.deserialize(self._get_single('messages', id=_id))

    def get_messages(self, contact=None):
        """
        Gets all matching messages
        """
        params = {}
        if contact:
            params['contact'] = contact

        return Message.deserialize_list(self._get_all('messages', **params))

    def get_run(self, uuid):
        """
        Gets a single flow run by its UUID
        """
        return Run.deserialize(self._get_single('runs', uuid=uuid))

    def get_runs(self, flow_uuid=None, group_uuids=None):
        """
        Gets all matching flow runs
        """
        params = {}
        if flow_uuid:
            params['flow_uuid'] = flow_uuid
        if group_uuids is not None:
            params['group_uuids'] = group_uuids

        return Run.deserialize_list(self._get_all('runs', **params))
