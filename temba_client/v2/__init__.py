from __future__ import absolute_import, unicode_literals

"""
This version of the API is still under development and so is subject to change without notice. We strongly recommend
that users continue using the existing API v1.
"""

from .types import Contact, Message, Run
from ..clients import BaseCursorClient


class TembaClient(BaseCursorClient):
    """
    Client for the Temba API v2

    :param str host: server hostname, e.g. 'rapidpro.io'
    :param str token: organization API token
    :param str user_agent: string to be included in the User-Agent header
    """
    def __init__(self, host, token, user_agent=None):
        super(TembaClient, self).__init__(host, token, user_agent, api_version=2)

    def get_contacts(self, uuid=None, urn=None, group=None, before=None, after=None):
        """
        Gets all matching contacts

        :param uuid: contact UUID
        :param urn: contact URN
        :param group: contact group name or UUID
        :param datetime before: modified before
        :param datetime after: modified after
        :return: contact query
        """
        params = self._build_params(uuid=uuid, urn=urn, group=group, before=before, after=after)
        return self._get_query('contacts', params, Contact)

    def get_messages(self, id=None, broadcast=None, contact=None, folder=None, label=None, before=None, after=None):
        """
        Gets all matching messages

        :param id: message id
        :param broadcast: broadcast id
        :param contact: contact object or UUID
        :param folder: folder name
        :param label: message label name or UUID
        :param datetime before: created before
        :param datetime after: created after
        :return: message query
        """
        params = self._build_params(id=id, broadcast=broadcast, contact=contact, folder=folder, label=label, before=before, after=after)
        return self._get_query('messages', params, Message)

    def get_runs(self, id=None, flow=None, contact=None, responded=None, before=None, after=None):
        """
        Gets all matching flow runs

        :param id: flow run id
        :param flow: flow object or UUID
        :param contact: contact object or UUID
        :param responded: whether to limit results to runs with responses
        :param datetime before: modified before
        :param datetime after: modified after
        :return: flow run query
        """
        params = self._build_params(id=id, flow=flow, contact=contact, responded=responded, before=before, after=after)
        return self._get_query('runs', params, Run)
