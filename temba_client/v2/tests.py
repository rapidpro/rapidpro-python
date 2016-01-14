from __future__ import absolute_import, unicode_literals

import datetime
import pytz

from mock import patch
from . import TembaClient
from ..exceptions import TembaRateExceededError
from ..tests import TembaTest, MockResponse


@patch('temba_client.clients.request')
class TembaClientTest(TembaTest):
    API_VERSION = 2

    def setUp(self):
        self.client = TembaClient('example.com', '1234567890', user_agent='test/0.1')

    def test_retry_on_rate_exceed(self, mock_request):
        fail_then_success = [
            MockResponse(429, '', {'Retry-After': 1}),
            MockResponse(200, self.read_json('runs'))
        ]
        mock_request.side_effect = fail_then_success

        # no retries means exception right away
        iterator = self.client.get_runs().iterfetches(retry_on_rate_exceed=False)
        self.assertRaises(TembaRateExceededError, iterator.__next__)

        mock_request.side_effect = fail_then_success

        # retries means it will try again after the first 429
        runs = self.client.get_runs().iterfetches(retry_on_rate_exceed=True).next()
        self.assertEqual(len(runs), 2)

        mock_request.side_effect = fail_then_success

        query = self.client.get_runs()
        self.assertRaises(TembaRateExceededError, query.all, retry_on_rate_exceed=False)

        mock_request.side_effect = fail_then_success

        runs = self.client.get_runs().all(retry_on_rate_exceed=True)
        self.assertEqual(len(runs), 2)

        # if requests always return 429, we will hit max retries regardless
        mock_request.side_effect = None
        mock_request.return_value = MockResponse(429, '', {'Retry-After': 1})

        self.assertRaises(TembaRateExceededError, self.client.get_runs().all, retry_on_rate_exceed=False)
        self.assertRaises(TembaRateExceededError, self.client.get_runs().all, retry_on_rate_exceed=True)

    def test_get_runs(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('runs'))

        # check with no params
        query = self.client.get_runs()
        runs = query.all()

        self.assert_request(mock_request, 'get', 'runs')
        self.assertEqual(len(runs), 2)

        self.assertEqual(runs[0].id, 4092373)
        self.assertEqual(runs[0].flow, "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a")
        self.assertEqual(runs[0].contact, "d33e9ad5-5c35-414c-abd4-e7451c69ff1d")
        self.assertEqual(runs[0].responded, True)
        self.assertEqual(len(runs[0].steps), 3)
        self.assertEqual(runs[0].steps[0].node, "ca6c092a-1615-474e-ab64-4e7ce75a808f")
        self.assertEqual(runs[0].steps[0].category, None)
        self.assertEqual(runs[0].steps[0].left_on, datetime.datetime(2015, 8, 26, 10, 4, 10, 6241, pytz.utc))
        self.assertEqual(runs[0].steps[0].text, "Hi Bobby, is your water filter working? Answer with Yes or No.")
        self.assertEqual(runs[0].steps[0].value, None)
        self.assertEqual(runs[0].steps[0].arrived_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 824114, pytz.utc))
        self.assertEqual(runs[0].steps[0].type, "actionset")
        self.assertEqual(runs[0].created_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 737686, pytz.utc))
        self.assertEqual(runs[0].modified_on, datetime.datetime(2015, 8, 26, 10, 5, 47, 516562, pytz.utc))
        self.assertEqual(runs[0].exited_on, datetime.datetime(2015, 8, 26, 10, 5, 47, 516562, pytz.utc))
        self.assertEqual(runs[0].exit_type, "completed")

        self.assertEqual(query.first().id, runs[0].id)
        self.assert_request(mock_request, 'get', 'runs')

        # check with all params
        query = self.client.get_runs(flow="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
                                     contact="d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
                                     responded=True,
                                     after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
                                     before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc))
        query.all()

        self.assert_request(mock_request, 'get', 'runs', params={'flow': "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
                                                                 'contact': "d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
                                                                 'responded': True,
                                                                 'after': "2014-12-12T22:34:36.978123",
                                                                 'before': "2014-12-12T22:56:58.917123"})

        # check when result is empty
        mock_request.return_value = MockResponse(200, self.read_json('empty'))
        query = self.client.get_runs()

        self.assertEqual(query.all(), [])
        self.assertEqual(query.first(), None)
