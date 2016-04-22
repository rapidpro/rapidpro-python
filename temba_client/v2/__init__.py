from __future__ import absolute_import, unicode_literals

"""
This version of the API is still under development and so is subject to change without notice. We strongly recommend
that users continue using the existing API v1.
"""

from .types import Broadcast, Campaign, CampaignEvent, Channel, ChannelEvent, Contact, Field, Group, Label, Message
from .types import Org, Run
from ..clients import BaseCursorClient


class TembaClient(BaseCursorClient):
    """
    Client for the Temba API v2

    :param str host: server hostname, e.g. 'rapidpro.io'
    :param str token: organization API token
    :param str user_agent: string to be included in the User-Agent header
    """
    def __init__(self, host, token, user_agent=None):
        super(TembaClient, self).__init__(host, token, 2, user_agent)

    def get_broadcasts(self, id=None, before=None, after=None):
        """
        Gets all matching broadcasts

        :param id: broadcast id
        :param datetime before: created before
        :param datetime after: created after
        :return: broadcast query
        """
        params = self._build_params(id=id, before=before, after=after)
        return self._get_query('broadcasts', params, Broadcast)

    def get_campaigns(self, uuid=None):
        """
        Gets all matching campaigns

        :param uuid: campaigns UUID
        :return: campaign query
        """
        params = self._build_params(uuid=uuid)
        return self._get_query('campaigns', params, Campaign)

    def get_campaign_events(self, uuid=None, campaign=None):
        """
        Gets all matching campaign events

        :param uuid: event UUID
        :param campaign: campaign object or UUID
        :return: campaign event query
        """
        params = self._build_params(uuid=uuid, campaign=campaign)
        return self._get_query('campaign_events', params, CampaignEvent)

    def get_channels(self, uuid=None, address=None):
        """
        Gets all matching channels

        :param uuid: channel UUID
        :param urn: channel address
        :return: channel query
        """
        params = self._build_params(uuid=uuid, address=address)
        return self._get_query('channels', params, Channel)

    def get_channel_events(self, id=None, contact=None, before=None, after=None):
        """
        Gets all matching channel events

        :param id: event id
        :param contact: contact object or UUID
        :param datetime before: created before
        :param datetime after: created after
        :return: channel event query
        """
        params = self._build_params(id=id, contact=contact, before=before, after=after)
        return self._get_query('channel_events', params, ChannelEvent)

    def get_contacts(self, uuid=None, urn=None, group=None, deleted=None, before=None, after=None):
        """
        Gets all matching contacts

        :param uuid: contact UUID
        :param urn: contact URN
        :param group: contact group name or UUID
        :param deleted: return deleted contact only
        :param datetime before: modified before
        :param datetime after: modified after
        :return: contact query
        """
        params = self._build_params(uuid=uuid, urn=urn, group=group, deleted=deleted, before=before, after=after)
        return self._get_query('contacts', params, Contact)

    def get_fields(self, key=None):
        """
        Gets all matching contact fields

        :param key: field key
        :return: field query
        """
        return self._get_query('fields', self._build_params(key=key), Field)

    def get_groups(self, uuid=None):
        """
        Gets all matching contact groups

        :param uuid: group UUID
        :return: group query
        """
        return self._get_query('groups', self._build_params(uuid=uuid), Group)

    def get_labels(self, uuid=None):
        """
        Gets all matching message labels

        :param uuid: label UUID
        :return: label query
        """
        return self._get_query('labels', self._build_params(uuid=uuid), Label)

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
        params = self._build_params(id=id, broadcast=broadcast, contact=contact, folder=folder, label=label,
                                    before=before, after=after)
        return self._get_query('messages', params, Message)

    def get_org(self, retry_on_rate_exceed=False):
        """
        Gets the current organization

        :param retry_on_rate_exceed: whether to sleep and retry if request rate limit exceeded
        :return: the org
        """
        return Org.deserialize(self._get_raw('org', {}, retry_on_rate_exceed))

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
