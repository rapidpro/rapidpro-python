from __future__ import absolute_import, unicode_literals

"""
This version of the API is still under development and so is subject to change without notice. We strongly recommend
that users continue using the existing API v1.
"""

from .types import Run
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

    def get_runs(self, flow=None, contact=None, responded=None, before=None, after=None):
        """
        Gets all matching flow runs

        :param flow: flow object or UUID
        :param contact: contact object or UUID
        :param responded: whether to limit results to runs with responses
        :param datetime before: modified before
        :param datetime after: modified after
        :return: flow run query
        """
        params = self._build_params(flow=flow, contact=contact, responded=responded, before=before, after=after)
        return self._get_query('runs', params, Run)
