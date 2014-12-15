from __future__ import unicode_literals

import requests

from .types import Contact, ContactGroup, Flow, FlowRun


class TembaException(Exception):
    def __init__(self, msg, caused_by=None):
        self.msg = msg
        self.caused_by = caused_by

    def __unicode__(self):
        text = self.msg
        if self.caused_by:
            text += "\ncaused by:\n%s" % self.caused_by
        return text


class TembaClient(object):
    """
    Client for the Temba API
    """
    def __init__(self, host, token, ssl=True):
        if host.startswith('http'):
            self.root_url = host
        else:
            self.root_url = '%s://%s/api/v1' % ('https' if ssl else 'http', host)

        self.token = token

    def create_contact(self, name, urns, fields, group_uuids):
        payload = {'name': name, 'urns': urns, 'fields': fields, 'group_uuids': group_uuids}
        return Contact.deserialize(self._create_single('contacts', payload))

    def get_contact(self, uuid):
        return Contact.deserialize(self._get_single('contacts', uuid=uuid))

    def get_contacts(self, name=None, group_uuids=None):
        params = {}
        if name is not None:
            params['name'] = name
        if group_uuids is not None:
            params['group_uuids'] = group_uuids

        return Contact.deserialize_list(self._get_all('contacts', **params))

    def get_flow(self, uuid):
        return Flow.deserialize(self._get_single('flows', uuid=uuid))

    def get_flows(self):
        return Flow.deserialize_list(self._get_all('flows'))

    def get_group(self, uuid):
        return ContactGroup.deserialize(self._get_single('groups', uuid=uuid))

    def get_groups(self, name=None):
        params = {}
        if name is not None:
            params['name'] = name

        return ContactGroup.deserialize_list(self._get_all('groups', **params))

    def get_run(self, uuid):
        return FlowRun.deserialize(self._get_single('runs', uuid=uuid))

    def get_runs(self, flow_uuid=None, group_uuids=None):
        params = {}
        if flow_uuid is not None:
            params['flow_uuid'] = flow_uuid
        if group_uuids is not None:
            params['group_uuids'] = group_uuids

        return FlowRun.deserialize_list(self._get_all('runs', **params))

    def _create_single(self, endpoint, **params):
        """
        Creates a single item at the given endpoint, which returns the new item
        """
        url = '%s/%s.json' % (self.root_url, endpoint)
        return self._post(url, **params)

    def _get_single(self, endpoint, **params):
        """
        Gets a single result from the given endpoint. Return none if there are no results and throws an exception if
        there are multiple results.
        """
        url = '%s/%s.json' % (self.root_url, endpoint)

        response = self._get(url, **params)
        num_results = len(response['results'])

        if num_results > 1:
            raise TembaException("Request for single object returned %d objects" % num_results)
        elif num_results == 0:
            return None
        else:
            return response['results'][0]

    def _get_all(self, endpoint, **params):
        """
        Gets all results from the given endpoint
        """
        # start = time.time()
        num_requests = 0
        results = []

        url = '%s/%s.json' % (self.root_url, endpoint)
        while url:
            response = self._get(url, **params)
            num_requests += 1
            results += response['results']
            url = response['next']

        # print "Fetched all from endpoint '%s' in %f (%d requests)" % (endpoint, time.time() - start, num_requests)

        return results

    def _get(self, url, **kwargs):
        """
        Makes a GET request to the given URL and returns the parsed JSON
        """
        try:
            response = requests.get(url, params=kwargs, headers=self._headers())
            response.raise_for_status()
            return response.json()
        except requests.HTTPError, ex:
            raise TembaException("Request error", ex)

    def _post(self, url, **kwargs):
        """
        Makes a POST request to the given URL and returns the parsed JSON
        """
        try:
            response = requests.post(url, data=kwargs, headers=self._headers())
            response.raise_for_status()
            return response.json()
        except requests.HTTPError, ex:
            raise TembaException("Request error", ex)

    def _headers(self):
        """
        Gets HTTP headers
        """
        return {'Content-type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Token %s' % self.token}