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
        runs = self.client.get_runs().iterfetches(retry_on_rate_exceed=True).__next__()
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

    def test_get_contacts(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('contacts'))

        # check with no params
        query = self.client.get_contacts()
        contacts = query.all()

        self.assert_request(mock_request, 'get', 'contacts')
        self.assertEqual(len(contacts), 2)

        self.assertEqual(contacts[0].uuid, "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")
        self.assertEqual(contacts[0].name, "Joe")
        self.assertEqual(contacts[0].language, "eng")
        self.assertEqual(contacts[0].urns, ["tel:+250973635665"])
        self.assertEqual(len(contacts[0].groups), 1)
        self.assertEqual(contacts[0].groups[0].uuid, "d29eca7c-a475-4d8d-98ca-bff968341356")
        self.assertEqual(contacts[0].groups[0].name, "Customers")
        self.assertEqual(contacts[0].fields, {'age': 34, 'nickname': "Jo"})
        self.assertEqual(contacts[0].blocked, False)
        self.assertEqual(contacts[0].failed, False)
        self.assertEqual(contacts[0].created_on, datetime.datetime(2015, 11, 11, 8, 30, 24, 922024, pytz.utc))
        self.assertEqual(contacts[0].modified_on, datetime.datetime(2015, 11, 11, 8, 30, 25, 525936, pytz.utc))

        # check with all params
        query = self.client.get_contacts(uuid="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
                                         urn="tel:+250973635665",
                                         group="Customers",
                                         after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
                                         before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc))
        query.all()

        self.assert_request(mock_request, 'get', 'contacts', params={
            'uuid': "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
            'urn': "tel:+250973635665",
            'group': "Customers",
            'after': "2014-12-12T22:34:36.978123",
            'before': "2014-12-12T22:56:58.917123"
        })

    def test_get_messages(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('messages'))

        # check with no params
        query = self.client.get_messages()
        messages = query.all()

        self.assert_request(mock_request, 'get', 'messages')
        self.assertEqual(len(messages), 2)

        self.assertEqual(messages[0].id, 4105423)
        self.assertEqual(messages[0].broadcast, 2690006)
        self.assertEqual(messages[0].contact.uuid, "d33e9ad5-5c35-414c-abd4-e7451c69ff1d")
        self.assertEqual(messages[0].contact.name, "Frank McFlow")
        self.assertEqual(messages[0].urn, "twitter:franky6431")
        self.assertEqual(messages[0].channel, "9a8b001e-a913-486c-80f4-1356e23f582e")
        self.assertEqual(messages[0].direction, "out")
        self.assertEqual(messages[0].type, "inbox")
        self.assertEqual(messages[0].status, "wired")
        self.assertEqual(messages[0].archived, False)
        self.assertEqual(messages[0].text, "How are you?")
        self.assertEqual(messages[0].labels, [])
        self.assertEqual(messages[0].created_on, datetime.datetime(2016, 1, 6, 15, 33, 0, 813162, pytz.utc))
        self.assertEqual(messages[0].sent_on, datetime.datetime(2016, 1, 6, 15, 35, 3, 675716, pytz.utc))
        self.assertEqual(messages[0].delivered_on, None)

        # check with all params
        query = self.client.get_messages(id=123456,
                                         broadcast=234567,
                                         contact="d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
                                         folder="inbox",
                                         label="Spam",
                                         after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
                                         before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc))
        query.all()

        self.assert_request(mock_request, 'get', 'messages', params={
            'id': 123456,
            'broadcast': 234567,
            'contact': "d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
            'folder': "inbox",
            'label': "Spam",
            'after': "2014-12-12T22:34:36.978123",
            'before': "2014-12-12T22:56:58.917123"
        })

    def test_get_runs(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('runs'))

        # check with no params
        query = self.client.get_runs()
        runs = query.all()

        self.assert_request(mock_request, 'get', 'runs')
        self.assertEqual(len(runs), 2)

        self.assertEqual(runs[0].id, 4092373)
        self.assertEqual(runs[0].flow.uuid, "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a")
        self.assertEqual(runs[0].flow.name, "Water Survey")
        self.assertEqual(runs[0].contact.uuid, "d33e9ad5-5c35-414c-abd4-e7451c69ff1d")
        self.assertEqual(runs[0].contact.name, "Frank McFlow")
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
        query = self.client.get_runs(id=123456,
                                     flow="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
                                     contact="d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
                                     responded=True,
                                     after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
                                     before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc))
        query.all()

        self.assert_request(mock_request, 'get', 'runs', params={
            'id': 123456,
            'flow': "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
            'contact': "d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
            'responded': True,
            'after': "2014-12-12T22:34:36.978123",
            'before': "2014-12-12T22:56:58.917123"
        })

        # check when result is empty
        mock_request.return_value = MockResponse(200, self.read_json('empty'))
        query = self.client.get_runs()

        self.assertEqual(query.all(), [])
        self.assertEqual(query.first(), None)
