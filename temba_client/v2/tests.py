from __future__ import absolute_import, unicode_literals

import unittest

from mock import patch
from . import TembaClient
from ..tests import MockResponse


@patch('temba_client.clients.request')
class TembaClientTest(unittest.TestCase):

    def setUp(self):
        self.client = TembaClient('example.com', '1234567890', user_agent='test/0.1')

    def test_get_runs(self, mock_request):
        pass
