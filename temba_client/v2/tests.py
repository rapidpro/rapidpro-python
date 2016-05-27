from __future__ import absolute_import, unicode_literals

import datetime
import pytz

from mock import patch
from requests.exceptions import ConnectionError
from . import TembaClient
from ..exceptions import TembaBadRequestError, TembaTokenError, TembaRateExceededError, TembaHttpError
from ..exceptions import TembaConnectionError
from ..tests import TembaTest, MockResponse


@patch('temba_client.clients.request')
class TembaClientTest(TembaTest):
    API_VERSION = 2

    def setUp(self):
        self.client = TembaClient('example.com', '1234567890', user_agent='test/0.1')

    def test_errors(self, mock_request):
        query = self.client.get_runs()

        # bad request errors (400)
        mock_request.return_value = MockResponse(400, "XYZ")

        self.assertRaisesWithMessage(TembaBadRequestError, "XYZ", query.all)

        mock_request.return_value = MockResponse(400, '["Msg1", "Msg2"]')

        self.assertRaisesWithMessage(TembaBadRequestError, "Msg1. Msg2", query.all)

        mock_request.return_value = MockResponse(400, '{"detail": "Msg"}')

        self.assertRaisesWithMessage(TembaBadRequestError, "Msg", query.all)

        mock_request.return_value = MockResponse(400, '{"field1": ["Msg1", "Msg2"]}')

        self.assertRaisesWithMessage(TembaBadRequestError, "Msg1. Msg2", query.all)

        # forbidden errors (403)
        mock_request.return_value = MockResponse(403, '{"detail":"Invalid token"}')

        self.assertRaisesWithMessage(TembaTokenError, "Authentication with provided token failed", query.all)

        # other HTTP like 414
        mock_request.return_value = MockResponse(414, "URI too long")

        self.assertRaisesWithMessage(TembaHttpError, "414 Client Error: ...", query.all)

        # connection failure
        mock_request.side_effect = ConnectionError()

        self.assertRaisesWithMessage(TembaConnectionError, "Unable to connect to host", query.all)

    def test_retry_on_rate_exceed(self, mock_request):
        fail_then_success = [
            MockResponse(429, '', {'Retry-After': 1}),
            MockResponse(200, self.read_json('runs'))
        ]
        mock_request.side_effect = fail_then_success

        # no retries means exception right away
        iterator = self.client.get_runs().iterfetches(retry_on_rate_exceed=False)
        self.assertRaisesWithMessage(TembaRateExceededError, "You have exceeded the number of requests allowed per org "
                                                             "in a given time window. Please wait 1 seconds before "
                                                             "making further requests", iterator.__next__)

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

    def test_get_broadcasts(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('broadcasts'))

        # check with no params
        results = self.client.get_broadcasts().all()

        self.assertRequest(mock_request, 'get', 'broadcasts')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].id, 1234)
        self.assertEqual(results[0].urns, ["tel:+250783865665", "twitter:bobby"])
        self.assertEqual(len(results[0].contacts), 1)
        self.assertEqual(results[0].contacts[0].uuid, "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")
        self.assertEqual(results[0].contacts[0].name, "Joe")
        self.assertEqual(len(results[0].groups), 1)
        self.assertEqual(results[0].groups[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].groups[0].name, "The A-Team")
        self.assertEqual(results[0].text, "Hello")
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 11, 11, 8, 30, 24, 922024, pytz.utc))

        # check with all params
        self.client.get_broadcasts(
            id=12345,
            after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc)
        ).all()

        self.assertRequest(mock_request, 'get', 'broadcasts', params={
            'id': 12345,
            'after': "2014-12-12T22:34:36.978123",
            'before': "2014-12-12T22:56:58.917123"
        })

    def test_get_campaigns(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('campaigns'))

        # check with no params
        results = self.client.get_campaigns().all()

        self.assertRequest(mock_request, 'get', 'campaigns')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab")
        self.assertEqual(results[0].name, "Reminders")
        self.assertEqual(results[0].group.uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].group.name, "The A-Team")
        self.assertEqual(results[0].created_on, datetime.datetime(2014, 6, 23, 9, 34, 12, 866000, pytz.utc))

        # check with all params
        self.client.get_campaigns(
            uuid="09d23a05-47fe-11e4-bfe9-b8f6b119e9ab"
        ).all()

        self.assertRequest(mock_request, 'get', 'campaigns', params={
            'uuid': "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
        })

    def test_get_campaign_events(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('campaign_events'))

        # check with no params
        results = self.client.get_campaign_events().all()

        self.assertRequest(mock_request, 'get', 'campaign_events')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "9e6beda-0ce2-46cd-8810-91157f261cbd")
        self.assertEqual(results[0].campaign.uuid, "9ccae91f-b3f8-4c18-ad92-e795a2332c11")
        self.assertEqual(results[0].campaign.name, "Reminders")
        self.assertEqual(results[0].relative_to.key, "edd")
        self.assertEqual(results[0].relative_to.label, "EDD")
        self.assertEqual(results[0].offset, 14)
        self.assertEqual(results[0].unit, "days")
        self.assertEqual(results[0].delivery_hour, -1)
        self.assertEqual(results[0].message, None)
        self.assertEqual(results[0].flow.uuid, "70c38f94-ab42-4666-86fd-3c76139110d3")
        self.assertEqual(results[0].flow.name, "Survey Flow")
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 6, 8, 12, 18, 7, 671000, pytz.utc))

        # check with all params
        self.client.get_campaign_events(
            uuid="09d23a05-47fe-11e4-bfe9-b8f6b119e9ab"
        ).all()

        self.assertRequest(mock_request, 'get', 'campaign_events', params={
            'uuid': "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
        })

    def test_get_channels(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('channels'))

        # check with no params
        results = self.client.get_channels().all()

        self.assertRequest(mock_request, 'get', 'channels')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab")
        self.assertEqual(results[0].name, "Android Phone")
        self.assertEqual(results[0].address, "+250788123123")
        self.assertEqual(results[0].country, "RW")
        self.assertEqual(results[0].device.name, "Nexus 5X")
        self.assertEqual(results[0].device.power_level, 99)
        self.assertEqual(results[0].device.power_status, "STATUS_DISCHARGING")
        self.assertEqual(results[0].device.power_source, "BATTERY")
        self.assertEqual(results[0].device.network_type, "WIFI")
        self.assertEqual(results[0].last_seen, datetime.datetime(2016, 3, 1, 5, 31, 27, 456000, pytz.utc))
        self.assertEqual(results[0].created_on, datetime.datetime(2014, 6, 23, 9, 34, 12, 866000, pytz.utc))

        # check with all params
        self.client.get_channels(
            uuid="09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
            address="+250788123123"
        ).all()

        self.assertRequest(mock_request, 'get', 'channels', params={
            'uuid': "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
            'address': "+250788123123"
        })

    def test_get_channel_events(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('channel_events'))

        # check with no params
        results = self.client.get_channel_events().all()

        self.assertRequest(mock_request, 'get', 'channel_events')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].id, 12345)
        self.assertEqual(results[0].type, "in")
        self.assertEqual(results[0].contact.uuid, "d33e9ad5-5c35-414c-abd4-e7451c69ff1d")
        self.assertEqual(results[0].contact.name, "Frank McFlow")
        self.assertEqual(results[0].channel.uuid, "9a8b001e-a913-486c-80f4-1356e23f582e")
        self.assertEqual(results[0].channel.name, "Nexmo")
        self.assertEqual(results[0].time, datetime.datetime(2016, 1, 6, 15, 35, 3, 675716, pytz.utc))
        self.assertEqual(results[0].duration, 123)
        self.assertEqual(results[0].created_on, datetime.datetime(2016, 1, 6, 15, 33, 0, 813162, pytz.utc))

        # check with all params
        self.client.get_channel_events(
            id=12345,
            contact="5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9",
            after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc)
        ).all()

        self.assertRequest(mock_request, 'get', 'channel_events', params={
            'id': 12345,
            'contact': "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9",
            'after': "2014-12-12T22:34:36.978123",
            'before': "2014-12-12T22:56:58.917123"
        })

    def test_get_contacts(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('contacts'))

        # check with no params
        results = self.client.get_contacts().all()

        self.assertRequest(mock_request, 'get', 'contacts')
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0].uuid, "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")
        self.assertEqual(results[0].name, "Joe")
        self.assertEqual(results[0].language, "eng")
        self.assertEqual(results[0].urns, ["tel:+250973635665"])
        self.assertEqual(len(results[0].groups), 1)
        self.assertEqual(results[0].groups[0].uuid, "d29eca7c-a475-4d8d-98ca-bff968341356")
        self.assertEqual(results[0].groups[0].name, "Customers")
        self.assertEqual(results[0].fields, {'age': 34, 'nickname': "Jo"})
        self.assertEqual(results[0].blocked, False)
        self.assertEqual(results[0].stopped, False)
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 11, 11, 8, 30, 24, 922024, pytz.utc))
        self.assertEqual(results[0].modified_on, datetime.datetime(2015, 11, 11, 8, 30, 25, 525936, pytz.utc))

        # check with all params
        self.client.get_contacts(
            uuid="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
            urn="tel:+250973635665",
            group="Customers",
            deleted=False,
            after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc)
        ).all()

        self.assertRequest(mock_request, 'get', 'contacts', params={
            'uuid': "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
            'urn': "tel:+250973635665",
            'group': "Customers",
            'deleted': False,
            'after': "2014-12-12T22:34:36.978123",
            'before': "2014-12-12T22:56:58.917123"
        })

    def test_get_fields(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('fields'))

        # check with no params
        results = self.client.get_fields().all()

        self.assertRequest(mock_request, 'get', 'fields')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].key, "chat_name")
        self.assertEqual(results[0].label, "Chat Name")
        self.assertEqual(results[0].value_type, "text")

        # check with all params
        self.client.get_fields(key="chat_name").all()

        self.assertRequest(mock_request, 'get', 'fields', params={'key': "chat_name"})

    def test_get_groups(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('groups'))

        # check with no params
        results = self.client.get_groups().all()

        self.assertRequest(mock_request, 'get', 'groups')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].name, "The A-Team")
        self.assertEqual(results[0].query, None)
        self.assertEqual(results[0].count, 4)

        # check with all params
        self.client.get_groups(uuid="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a").all()

        self.assertRequest(mock_request, 'get', 'groups', params={'uuid': "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a"})

    def test_get_labels(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('labels'))

        # check with no params
        results = self.client.get_labels().all()

        self.assertRequest(mock_request, 'get', 'labels')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].name, "Important")
        self.assertEqual(results[0].count, 4)

        # check with all params
        self.client.get_labels(uuid="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a").all()

        self.assertRequest(mock_request, 'get', 'labels', params={'uuid': "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a"})

    def test_get_messages(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('messages'))

        # check with no params
        results = self.client.get_messages().all()

        self.assertRequest(mock_request, 'get', 'messages')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].id, 4105423)
        self.assertEqual(results[0].broadcast, 2690006)
        self.assertEqual(results[0].contact.uuid, "d33e9ad5-5c35-414c-abd4-e7451c69ff1d")
        self.assertEqual(results[0].contact.name, "Frank McFlow")
        self.assertEqual(results[0].urn, "twitter:franky6431")
        self.assertEqual(results[0].channel.uuid, "9a8b001e-a913-486c-80f4-1356e23f582e")
        self.assertEqual(results[0].channel.name, "Nexmo")
        self.assertEqual(results[0].direction, "out")
        self.assertEqual(results[0].type, "inbox")
        self.assertEqual(results[0].status, "wired")
        self.assertEqual(results[0].visibility, "visible")
        self.assertEqual(results[0].text, "How are you?")
        self.assertEqual(results[0].labels, [])
        self.assertEqual(results[0].created_on, datetime.datetime(2016, 1, 6, 15, 33, 0, 813162, pytz.utc))
        self.assertEqual(results[0].sent_on, datetime.datetime(2016, 1, 6, 15, 35, 3, 675716, pytz.utc))
        self.assertEqual(results[0].modified_on, None)

        # check with all params
        self.client.get_messages(
            id=123456,
            broadcast=234567,
            contact="d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
            folder="inbox",
            label="Spam",
            after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc)
        ).all()

        self.assertRequest(mock_request, 'get', 'messages', params={
            'id': 123456,
            'broadcast': 234567,
            'contact': "d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
            'folder': "inbox",
            'label': "Spam",
            'after': "2014-12-12T22:34:36.978123",
            'before': "2014-12-12T22:56:58.917123"
        })

    def test_get_org(self, mock_request):
        mock_request.return_value = MockResponse(200, self.read_json('org'))
        org = self.client.get_org()

        self.assertRequest(mock_request, 'get', 'org')

        self.assertEqual(org.name, "Nyaruka")
        self.assertEqual(org.country, "RW")
        self.assertEqual(org.languages, ["eng", "fre"])
        self.assertEqual(org.primary_language, "eng")
        self.assertEqual(org.timezone, "Africa/Kigali")
        self.assertEqual(org.date_style, "day_first")
        self.assertEqual(org.anon, False)

    def test_get_runs(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json('runs'))

        # check with no params
        query = self.client.get_runs()
        results = query.all()

        self.assertRequest(mock_request, 'get', 'runs')
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].id, 4092373)
        self.assertEqual(results[0].flow.uuid, "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a")
        self.assertEqual(results[0].flow.name, "Water Survey")
        self.assertEqual(results[0].contact.uuid, "d33e9ad5-5c35-414c-abd4-e7451c69ff1d")
        self.assertEqual(results[0].contact.name, "Frank McFlow")
        self.assertEqual(results[0].responded, True)
        self.assertEqual(len(results[0].steps), 3)
        self.assertEqual(results[0].steps[0].node, "ca6c092a-1615-474e-ab64-4e7ce75a808f")
        self.assertEqual(results[0].steps[0].category, None)
        self.assertEqual(results[0].steps[0].left_on, datetime.datetime(2015, 8, 26, 10, 4, 10, 6241, pytz.utc))
        self.assertEqual(results[0].steps[0].text, "Hi Bobby, is your water filter working? Answer with Yes or No.")
        self.assertEqual(results[0].steps[0].value, None)
        self.assertEqual(results[0].steps[0].arrived_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 824114, pytz.utc))
        self.assertEqual(results[0].steps[0].type, "actionset")
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 737686, pytz.utc))
        self.assertEqual(results[0].modified_on, datetime.datetime(2015, 8, 26, 10, 5, 47, 516562, pytz.utc))
        self.assertEqual(results[0].exited_on, datetime.datetime(2015, 8, 26, 10, 5, 47, 516562, pytz.utc))
        self.assertEqual(results[0].exit_type, "completed")

        self.assertEqual(query.first().id, results[0].id)
        self.assertRequest(mock_request, 'get', 'runs')

        # check with all params
        self.client.get_runs(
            id=123456,
            flow="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
            contact="d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
            responded=True,
            after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc)
        ).all()

        self.assertRequest(mock_request, 'get', 'runs', params={
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
