import datetime
import json
import pytz

from unittest.mock import patch
from requests.exceptions import ConnectionError
from . import TembaClient
from .types import Campaign, CampaignEvent, Contact, Field, Flow, Group, Label, Message, ResthookSubscriber
from ..exceptions import TembaBadRequestError, TembaTokenError, TembaRateExceededError, TembaHttpError
from ..exceptions import TembaConnectionError
from ..tests import TembaTest, MockResponse


@patch("temba_client.clients.request")
class TembaClientTest(TembaTest):
    API_VERSION = 2

    def setUp(self):
        self.client = TembaClient("example.com", "1234567890", user_agent="test/0.1")

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

    def test_get_and_resume_cursor(self, mock_request):
        response_json = json.loads(self.read_json("runs"))
        response_json["next"] = "https://app.rapidpro.io/api/v2/runs.json?cursor=qwerty%3D&flow=flow_uuid"
        mock_request.return_value = MockResponse(200, json.dumps(response_json))

        iterator = self.client.get_runs().iterfetches(retry_on_rate_exceed=True)
        self.assertEqual(iterator.get_cursor(), None)

        iterator.__next__()
        self.assertEqual(iterator.get_cursor(), "qwerty=")

        iterator.url = None
        self.assertEqual(iterator.get_cursor(), None)

        iterator = self.client.get_runs().iterfetches(retry_on_rate_exceed=True, resume_cursor="qwERty=")

        # we have resume cursor attribute set
        self.assertTrue(iterator.resume_cursor)

        iterator.__next__()

        # resume cursor attribute should be cleared
        self.assertFalse(iterator.resume_cursor)
        self.assertEqual(iterator.url, "https://app.rapidpro.io/api/v2/runs.json?cursor=qwerty%3D&flow=flow_uuid")

        self.assertRequest(mock_request, "get", "runs", params={"cursor": "qwERty="})

    def test_retry_on_rate_exceed(self, mock_request):
        fail_then_success = [MockResponse(429, "", {"Retry-After": 1}), MockResponse(200, self.read_json("runs"))]
        mock_request.side_effect = fail_then_success

        # no retries means exception right away
        iterator = self.client.get_runs().iterfetches(retry_on_rate_exceed=False)
        self.assertRaisesWithMessage(
            TembaRateExceededError,
            "You have exceeded the number of requests allowed per org "
            "in a given time window. Please wait 1 seconds before "
            "making further requests",
            iterator.__next__,
        )

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
        mock_request.return_value = MockResponse(429, "", {"Retry-After": 1})

        self.assertRaises(TembaRateExceededError, self.client.get_runs().all, retry_on_rate_exceed=False)
        self.assertRaises(TembaRateExceededError, self.client.get_runs().all, retry_on_rate_exceed=True)

    # ==================================================================================================================
    # Fetch object operations
    # ==================================================================================================================

    def test_get_archives(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("archives"))

        # check with no params
        results = self.client.get_archives().all()

        self.assertRequest(mock_request, "get", "archives")
        self.assertEqual(len(results), 4)

        self.assertEqual(results[1].archive_type, "message")
        self.assertEqual(results[1].start_date, datetime.datetime(2018, 4, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(results[1].period, "monthly")
        self.assertEqual(results[1].record_count, 10)
        self.assertEqual(results[1].size, 23)
        self.assertEqual(results[1].hash, "f0d79988b7772c003d04a28bd7417a62")
        self.assertEqual(results[1].download_url, "http://s3-bucket.aws.com/my/archive.jsonl.gz")

        self.client.get_archives(
            archive_type="message",
            period="daily",
            after=datetime.datetime(2018, 1, 1, tzinfo=pytz.utc),
            before=datetime.datetime(2018, 5, 1, tzinfo=pytz.utc),
        ).all()

        self.assertRequest(
            mock_request,
            "get",
            "archives",
            params={
                "archive_type": "message",
                "period": "daily",
                "after": "2018-01-01T00:00:00.000000Z",
                "before": "2018-05-01T00:00:00.000000Z",
            },
        )

    def test_get_boundaries(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("boundaries"))

        # check with no params
        results = self.client.get_boundaries().all()

        self.assertRequest(mock_request, "get", "boundaries")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[1].osm_id, "R195270")
        self.assertEqual(results[1].name, "Bujumbura")
        self.assertEqual(results[1].level, 1)
        self.assertEqual(results[1].parent.osm_id, "R195269")
        self.assertEqual(results[1].parent.name, "Burundi")
        self.assertEqual(results[1].aliases, ["Buja"])
        self.assertEqual(results[1].geometry.type, "MultiPolygon")
        self.assertEqual(
            results[1].geometry.coordinates,
            [[[[29.5025959, -3.2634468], [29.4886074, -3.2496493], [29.4170303, -3.2721906]]]],
        )

        results = self.client.get_boundaries(geometry=False).all()

        self.assertRequest(mock_request, "get", "boundaries", params={"geometry": False})

        results = self.client.get_boundaries(geometry=True).all()

        self.assertRequest(mock_request, "get", "boundaries", params={"geometry": True})

    def test_get_broadcasts(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("broadcasts"))

        # check with no params
        results = self.client.get_broadcasts().all()

        self.assertRequest(mock_request, "get", "broadcasts")
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
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc),
        ).all()

        self.assertRequest(
            mock_request,
            "get",
            "broadcasts",
            params={"id": 12345, "after": "2014-12-12T22:34:36.978123Z", "before": "2014-12-12T22:56:58.917123Z"},
        )

    def test_get_campaigns(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("campaigns"))

        # check with no params
        results = self.client.get_campaigns().all()

        self.assertRequest(mock_request, "get", "campaigns")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab")
        self.assertEqual(results[0].name, "Reminders")
        self.assertEqual(results[0].archived, False)
        self.assertEqual(results[0].group.uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].group.name, "The A-Team")
        self.assertEqual(results[0].created_on, datetime.datetime(2014, 6, 23, 9, 34, 12, 866000, pytz.utc))

        # check with all params
        self.client.get_campaigns(uuid="09d23a05-47fe-11e4-bfe9-b8f6b119e9ab").all()

        self.assertRequest(mock_request, "get", "campaigns", params={"uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab"})

    def test_get_campaign_events(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("campaign_events"))

        # check with no params
        results = self.client.get_campaign_events().all()

        self.assertRequest(mock_request, "get", "campaign_events")
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
        self.client.get_campaign_events(uuid="09d23a05-47fe-11e4-bfe9-b8f6b119e9ab").all()

        self.assertRequest(
            mock_request, "get", "campaign_events", params={"uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab"}
        )

    def test_get_channels(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("channels"))

        # check with no params
        results = self.client.get_channels().all()

        self.assertRequest(mock_request, "get", "channels")
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
        self.client.get_channels(uuid="09d23a05-47fe-11e4-bfe9-b8f6b119e9ab", address="+250788123123").all()

        self.assertRequest(
            mock_request,
            "get",
            "channels",
            params={"uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab", "address": "+250788123123"},
        )

    def test_get_channel_events(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("channel_events"))

        # check with no params
        results = self.client.get_channel_events().all()

        self.assertRequest(mock_request, "get", "channel_events")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].id, 12345)
        self.assertEqual(results[0].type, "in")
        self.assertEqual(results[0].contact.uuid, "d33e9ad5-5c35-414c-abd4-e7451c69ff1d")
        self.assertEqual(results[0].contact.name, "Frank McFlow")
        self.assertEqual(results[0].channel.uuid, "9a8b001e-a913-486c-80f4-1356e23f582e")
        self.assertEqual(results[0].channel.name, "Nexmo")
        self.assertEqual(results[0].extra, {"foo": "bar"})
        self.assertEqual(results[0].occurred_on, datetime.datetime(2016, 1, 6, 15, 35, 3, 675716, pytz.utc))
        self.assertEqual(results[0].created_on, datetime.datetime(2016, 1, 6, 15, 33, 0, 813162, pytz.utc))

        # check with all params
        self.client.get_channel_events(
            id=12345,
            contact="5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9",
            after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc),
        ).all()

        self.assertRequest(
            mock_request,
            "get",
            "channel_events",
            params={
                "id": 12345,
                "contact": "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9",
                "after": "2014-12-12T22:34:36.978123Z",
                "before": "2014-12-12T22:56:58.917123Z",
            },
        )

    def test_get_contacts(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("contacts"))

        # check with no params
        results = self.client.get_contacts().all()

        self.assertRequest(mock_request, "get", "contacts")
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0].uuid, "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")
        self.assertEqual(results[0].name, "Joe")
        self.assertEqual(results[0].language, "eng")
        self.assertEqual(results[0].urns, ["tel:+250973635665"])
        self.assertEqual(len(results[0].groups), 1)
        self.assertEqual(results[0].groups[0].uuid, "d29eca7c-a475-4d8d-98ca-bff968341356")
        self.assertEqual(results[0].groups[0].name, "Customers")
        self.assertEqual(results[0].fields, {"age": 34, "nickname": "Jo"})
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
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc),
        ).all()

        self.assertRequest(
            mock_request,
            "get",
            "contacts",
            params={
                "uuid": "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
                "urn": "tel:+250973635665",
                "group": "Customers",
                "deleted": False,
                "after": "2014-12-12T22:34:36.978123Z",
                "before": "2014-12-12T22:56:58.917123Z",
            },
        )

    def test_get_definitions(self, mock_request):
        mock_request.return_value = MockResponse(200, self.read_json("definitions"))

        # check with all params
        definitions = self.client.get_definitions(
            flows=["04a4752b-0f49-480e-ae60-3a3f2bea485c", "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a"],
            campaigns=[],
            dependencies=False,
        )

        self.assertRequest(
            mock_request,
            "get",
            "definitions",
            params={
                "flow": ["04a4752b-0f49-480e-ae60-3a3f2bea485c", "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a"],
                "campaign": [],
                "dependencies": 0,
            },
        )

        self.assertEqual(definitions.version, "10.1")

    def test_get_fields(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("fields"))

        # check with no params
        results = self.client.get_fields().all()

        self.assertRequest(mock_request, "get", "fields")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].key, "chat_name")
        self.assertEqual(results[0].label, "Chat Name")
        self.assertEqual(results[0].value_type, "text")

        # check with all params
        self.client.get_fields(key="chat_name").all()

        self.assertRequest(mock_request, "get", "fields", params={"key": "chat_name"})

    def test_get_flows(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("flows"))

        # check with no params
        results = self.client.get_flows().all()

        self.assertRequest(mock_request, "get", "flows")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].name, "Registration")
        self.assertEqual(results[0].archived, False)
        self.assertEqual(len(results[0].labels), 1)
        self.assertEqual(results[0].labels[0].uuid, "5a4eb79e-1b1f-4ae3-8700-09384cca385f")
        self.assertEqual(results[0].labels[0].name, "Important")
        self.assertEqual(results[0].expires, 600)
        self.assertEqual(results[0].created_on, datetime.datetime(2014, 6, 23, 9, 34, 12, 866000, pytz.utc))
        self.assertEqual(results[0].runs.active, 56)
        self.assertEqual(results[0].runs.completed, 123)
        self.assertEqual(results[0].runs.interrupted, 2)
        self.assertEqual(results[0].runs.expired, 34)
        self.assertEqual(results[0].results[0].key, "color")
        self.assertEqual(results[0].results[0].name, "Color")
        self.assertEqual(results[0].results[0].categories, ["Orange", "Blue", "Other", "Nothing"])
        self.assertEqual(
            results[0].results[0].node_uuids,
            ["2bfbd76a-245a-473c-a296-28e4815f3a98", "d8b0ed18-a5c2-48be-98af-9b7f017fdc6c"])

        # check with all params
        self.client.get_flows(uuid="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a").all()

        self.assertRequest(mock_request, "get", "flows", params={"uuid": "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a"})

    def test_get_flow_starts(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("flow_starts"))

        # check with no params
        results = self.client.get_flow_starts().all()

        self.assertRequest(mock_request, "get", "flow_starts")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "93a624ad-5440-415e-b49f-17bf42754acb")
        self.assertEqual(results[0].flow.uuid, "f5901b62-ba76-4003-9c62-72fdacc1b7b7")
        self.assertEqual(results[0].flow.name, "Registration")
        self.assertEqual(len(results[0].groups), 1)
        self.assertEqual(results[0].groups[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].groups[0].name, "The A-Team")
        self.assertEqual(len(results[0].contacts), 2)
        self.assertEqual(results[0].contacts[0].uuid, "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")
        self.assertEqual(results[0].contacts[0].name, "Joe")
        self.assertEqual(results[0].restart_participants, True)
        self.assertEqual(results[0].status, "pending")
        self.assertEqual(results[0].extra, {"day": "Monday"})
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 737686, pytz.utc))
        self.assertEqual(results[0].modified_on, datetime.datetime(2015, 9, 26, 10, 4, 9, 737686, pytz.utc))

        # check with all params
        self.client.get_flow_starts(uuid="93a624ad-5440-415e-b49f-17bf42754acb").all()

        self.assertRequest(mock_request, "get", "flow_starts", params={"uuid": "93a624ad-5440-415e-b49f-17bf42754acb"})

    def test_get_groups(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("groups"))

        # check with no params
        results = self.client.get_groups().all()

        self.assertRequest(mock_request, "get", "groups")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].name, "The A-Team")
        self.assertEqual(results[0].query, None)
        self.assertEqual(results[0].count, 4)

        # check with all params
        self.client.get_groups(uuid="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a", name="Testers").all()

        self.assertRequest(
            mock_request, "get", "groups", params={"uuid": "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a", "name": "Testers"}
        )

    def test_get_labels(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("labels"))

        # check with no params
        results = self.client.get_labels().all()

        self.assertRequest(mock_request, "get", "labels")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
        self.assertEqual(results[0].name, "Important")
        self.assertEqual(results[0].count, 4)

        # check with all params
        self.client.get_labels(uuid="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a", name="Testing").all()

        self.assertRequest(
            mock_request, "get", "labels", params={"uuid": "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a", "name": "Testing"}
        )

    def test_get_messages(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("messages"))

        # check with no params
        results = self.client.get_messages().all()

        self.assertRequest(mock_request, "get", "messages")
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
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc),
        ).all()

        self.assertRequest(
            mock_request,
            "get",
            "messages",
            params={
                "id": 123456,
                "broadcast": 234567,
                "contact": "d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
                "folder": "inbox",
                "label": "Spam",
                "after": "2014-12-12T22:34:36.978123Z",
                "before": "2014-12-12T22:56:58.917123Z",
            },
        )

    def test_get_org(self, mock_request):
        mock_request.return_value = MockResponse(200, self.read_json("org"))
        org = self.client.get_org()

        self.assertRequest(mock_request, "get", "org")

        self.assertEqual(org.name, "Nyaruka")
        self.assertEqual(org.country, "RW")
        self.assertEqual(org.languages, ["eng", "fre"])
        self.assertEqual(org.primary_language, "eng")
        self.assertEqual(org.timezone, "Africa/Kigali")
        self.assertEqual(org.date_style, "day_first")
        self.assertEqual(org.anon, False)

    def test_get_resthooks(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("resthooks"))

        # check with no params
        results = self.client.get_resthooks().all()

        self.assertRequest(mock_request, "get", "resthooks")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].resthook, "new-mother")
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 737686, pytz.utc))
        self.assertEqual(results[0].modified_on, datetime.datetime(2015, 9, 26, 10, 4, 9, 737686, pytz.utc))

    def test_get_resthook_events(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("resthook_events"))

        # check with no params
        results = self.client.get_resthook_events().all()

        self.assertRequest(mock_request, "get", "resthook_events")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].resthook, "new-mother")
        self.assertEqual(results[0].data, {"foo": "bar"})
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 737686, pytz.utc))

        # check with all params
        self.client.get_resthook_events(resthook="new-mother").all()

        self.assertRequest(mock_request, "get", "resthook_events", params={"resthook": "new-mother"})

    def test_get_resthook_subscribers(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("resthook_subscribers"))

        # check with no params
        results = self.client.get_resthook_subscribers().all()

        self.assertRequest(mock_request, "get", "resthook_subscribers")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].id, 1001)
        self.assertEqual(results[0].resthook, "new-mother")
        self.assertEqual(results[0].target_url, "http://foo.bar/mothers")
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 737686, pytz.utc))

        # check with all params
        self.client.get_resthook_subscribers(id=1001, resthook="new-mother").all()

        self.assertRequest(mock_request, "get", "resthook_subscribers", params={"id": 1001, "resthook": "new-mother"})

    def test_get_runs(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, self.read_json("runs"))

        # check with no params
        query = self.client.get_runs()
        results = query.all()

        self.assertRequest(mock_request, "get", "runs")
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0].id, 4092373)
        self.assertEqual(results[0].flow.uuid, "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a")
        self.assertEqual(results[0].flow.name, "Water Survey")
        self.assertEqual(results[0].contact.uuid, "d33e9ad5-5c35-414c-abd4-e7451c69ff1d")
        self.assertEqual(results[0].contact.name, "Frank McFlow")
        self.assertEqual(results[0].start.uuid, "93a624ad-5440-415e-b49f-17bf42754acb")
        self.assertEqual(results[0].responded, True)
        self.assertEqual(len(results[0].path), 4)
        self.assertEqual(results[0].path[0].node, "27a86a1b-6cc4-4ae3-b73d-89650966a82f")
        self.assertEqual(results[0].path[0].time, datetime.datetime(2015, 11, 11, 13, 5, 50, 457742, pytz.utc))
        self.assertEqual(len(results[0].values), 2)
        self.assertEqual(results[0].values["color"].value, "blue")
        self.assertEqual(results[0].values["color"].category, "Blue")
        self.assertEqual(results[0].values["color"].input, "it is blue")
        self.assertEqual(results[0].values["color"].name, "color")
        self.assertEqual(results[0].values["color"].node, "fc32aeb0-ac3e-42a8-9ea7-10248fdf52a1")
        self.assertEqual(results[0].values["color"].time, datetime.datetime(2015, 11, 11, 13, 3, 51, 635662, pytz.utc))
        self.assertEqual(results[0].values["reason"].value, "Because it's the color of sky")
        self.assertEqual(results[0].values["reason"].category, "All Responses")
        self.assertEqual(results[0].values["reason"].node, "4c9cb68d-474f-4b9a-b65e-c2aa593a3466")
        self.assertEqual(
            results[0].values["reason"].time, datetime.datetime(2015, 11, 11, 13, 5, 57, 576056, pytz.utc)
        )
        self.assertEqual(results[0].created_on, datetime.datetime(2015, 8, 26, 10, 4, 9, 737686, pytz.utc))
        self.assertEqual(results[0].modified_on, datetime.datetime(2015, 8, 26, 10, 5, 47, 516562, pytz.utc))
        self.assertEqual(results[0].exited_on, datetime.datetime(2015, 8, 26, 10, 5, 47, 516562, pytz.utc))
        self.assertEqual(results[0].exit_type, "completed")

        self.assertEqual(query.first().id, results[0].id)
        self.assertRequest(mock_request, "get", "runs")

        # check with all params
        self.client.get_runs(
            id=123456,
            flow="ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
            contact="d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
            responded=True,
            after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978123, pytz.utc),
            before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917123, pytz.utc),
        ).all()

        self.assertRequest(
            mock_request,
            "get",
            "runs",
            params={
                "id": 123456,
                "flow": "ffce0fbb-4fe1-4052-b26a-91beb2ebae9a",
                "contact": "d33e9ad5-5c35-414c-abd4-e7451c69ff1d",
                "responded": True,
                "after": "2014-12-12T22:34:36.978123Z",
                "before": "2014-12-12T22:56:58.917123Z",
            },
        )

        # check when result is empty
        mock_request.return_value = MockResponse(200, self.read_json("empty"))
        query = self.client.get_runs()

        self.assertEqual(query.all(), [])
        self.assertEqual(query.first(), None)

    # ==================================================================================================================
    # Create object operations
    # ==================================================================================================================

    def test_create_broadcast(self, mock_request):
        mock_request.return_value = MockResponse(200, self.read_json("broadcasts", extract_result=0))
        broadcast = self.client.create_broadcast(
            text="Hello",
            urns=["tel:+250783865665", "twitter:bobby"],
            contacts=["5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"],
            groups=["04a4752b-0f49-480e-ae60-3a3f2bea485c"],
        )

        self.assertRequest(
            mock_request,
            "post",
            "broadcasts",
            data={
                "text": "Hello",
                "urns": ["tel:+250783865665", "twitter:bobby"],
                "contacts": ["5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"],
                "groups": ["04a4752b-0f49-480e-ae60-3a3f2bea485c"],
            },
        )
        self.assertEqual(broadcast.id, 1234)

    def test_create_campaign(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("campaigns", extract_result=0))
        campaign = self.client.create_campaign(name="Reminders", group="Reporters")

        self.assertRequest(mock_request, "post", "campaigns", data={"name": "Reminders", "group": "Reporters"})
        self.assertEqual(campaign.uuid, "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab")

    def test_create_campaign_event(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("campaign_events", extract_result=0))
        event = self.client.create_campaign_event(
            campaign=Campaign.create(uuid="9ccae91f-b3f8-4c18-ad92-e795a2332c11"),
            relative_to="edd",
            offset=14,
            unit="days",
            delivery_hour=-1,
            flow=Flow.create(uuid="70c38f94-ab42-4666-86fd-3c76139110d3"),
        )

        self.assertRequest(
            mock_request,
            "post",
            "campaign_events",
            data={
                "campaign": "9ccae91f-b3f8-4c18-ad92-e795a2332c11",
                "relative_to": "edd",
                "offset": 14,
                "unit": "days",
                "delivery_hour": -1,
                "flow": "70c38f94-ab42-4666-86fd-3c76139110d3",
            },
        )
        self.assertEqual(event.uuid, "9e6beda-0ce2-46cd-8810-91157f261cbd")

    def test_create_contact(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("contacts", extract_result=0))
        contact = self.client.create_contact(
            name="Joe",
            language="eng",
            urns=["tel:+250973635665"],
            fields={"nickname": "Jo", "age": 34},
            groups=["d29eca7c-a475-4d8d-98ca-bff968341356"],
        )

        self.assertRequest(
            mock_request,
            "post",
            "contacts",
            data={
                "name": "Joe",
                "language": "eng",
                "urns": ["tel:+250973635665"],
                "fields": {"nickname": "Jo", "age": 34},
                "groups": ["d29eca7c-a475-4d8d-98ca-bff968341356"],
            },
        )
        self.assertEqual(contact.uuid, "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")

    def test_create_field(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("fields", extract_result=0))
        field = self.client.create_field(label="Chat Name", value_type="text")

        self.assertRequest(mock_request, "post", "fields", data={"label": "Chat Name", "value_type": "text"})
        self.assertEqual(field.key, "chat_name")

    def test_create_flow_start(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("flow_starts", extract_result=0))
        start = self.client.create_flow_start(
            flow="f5901b62-ba76-4003-9c62-72fdacc1b7b7",
            contacts=["5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"],
            groups=["04a4752b-0f49-480e-ae60-3a3f2bea485c"],
            urns=[],
            restart_participants=False,
            extra={"day": "Monday"},
        )

        self.assertRequest(
            mock_request,
            "post",
            "flow_starts",
            data={
                "flow": "f5901b62-ba76-4003-9c62-72fdacc1b7b7",
                "contacts": ["5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"],
                "groups": ["04a4752b-0f49-480e-ae60-3a3f2bea485c"],
                "urns": [],
                "restart_participants": False,
                "extra": {"day": "Monday"},
            },
        )
        self.assertEqual(start.uuid, "93a624ad-5440-415e-b49f-17bf42754acb")

    def test_create_group(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("groups", extract_result=0))
        group = self.client.create_group(name="Reporters")

        self.assertRequest(mock_request, "post", "groups", data={"name": "Reporters"})
        self.assertEqual(group.uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")

    def test_create_label(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("labels", extract_result=0))
        label = self.client.create_label(name="Important")

        self.assertRequest(mock_request, "post", "labels", data={"name": "Important"})
        self.assertEqual(label.uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")

    def test_create_resthook_subscriber(self, mock_request):
        subscriber_json = self.read_json("resthook_subscribers", extract_result=0)

        mock_request.return_value = MockResponse(201, subscriber_json)
        subscriber = self.client.create_resthook_subscriber(resthook="new-mother", target_url="http://foo.bar/mothers")

        self.assertRequest(
            mock_request,
            "post",
            "resthook_subscribers",
            data={"resthook": "new-mother", "target_url": "http://foo.bar/mothers"},
        )
        self.assertEqual(subscriber.id, 1001)

    # ==================================================================================================================
    # Update object operations
    # ==================================================================================================================

    def test_update_campaign(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("campaigns", extract_result=0))

        # check update by UUID
        campaign = self.client.update_campaign(
            campaign="09d23a05-47fe-11e4-bfe9-b8f6b119e9ab", name="Reminders", group="Reporters"
        )

        self.assertRequest(
            mock_request,
            "post",
            "campaigns",
            params={"uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab"},
            data={"name": "Reminders", "group": "Reporters"},
        )
        self.assertEqual(campaign.uuid, "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab")

    def test_update_campaign_event(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("campaign_events", extract_result=0))
        event = self.client.update_campaign_event(
            event=CampaignEvent.create(uuid="9e6beda-0ce2-46cd-8810-91157f261cbd"),
            relative_to="edd",
            offset=14,
            unit="days",
            delivery_hour=-1,
            flow=Flow.create(uuid="70c38f94-ab42-4666-86fd-3c76139110d3"),
        )

        self.assertRequest(
            mock_request,
            "post",
            "campaign_events",
            params={"uuid": "9e6beda-0ce2-46cd-8810-91157f261cbd"},
            data={
                "relative_to": "edd",
                "offset": 14,
                "unit": "days",
                "delivery_hour": -1,
                "flow": "70c38f94-ab42-4666-86fd-3c76139110d3",
            },
        )
        self.assertEqual(event.uuid, "9e6beda-0ce2-46cd-8810-91157f261cbd")

    def test_update_contact(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("contacts", extract_result=0))

        # check update by UUID
        contact = self.client.update_contact(
            contact="5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9",
            name="Joe",
            language="eng",
            urns=["tel:+250973635665"],
            fields={"nickname": "Jo", "age": 34},
            groups=["d29eca7c-a475-4d8d-98ca-bff968341356"],
        )

        self.assertRequest(
            mock_request,
            "post",
            "contacts",
            params={"uuid": "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"},
            data={
                "name": "Joe",
                "language": "eng",
                "urns": ["tel:+250973635665"],
                "fields": {"nickname": "Jo", "age": 34},
                "groups": ["d29eca7c-a475-4d8d-98ca-bff968341356"],
            },
        )
        self.assertEqual(contact.uuid, "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")

        # check partial update by URN
        self.client.update_contact(contact="tel:+250973635665", language="fre")

        self.assertRequest(
            mock_request, "post", "contacts", params={"urn": "tel:+250973635665"}, data={"language": "fre"}
        )

    def test_update_field(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("fields", extract_result=0))

        # check update by object
        field = self.client.update_field(Field.create(key="chat_name"), label="Chat Name", value_type="text")

        self.assertRequest(
            mock_request,
            "post",
            "fields",
            params={"key": "chat_name"},
            data={"label": "Chat Name", "value_type": "text"},
        )
        self.assertEqual(field.key, "chat_name")

    def test_update_group(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("groups", extract_result=0))

        # check update by UUID
        group = self.client.update_group(group="04a4752b-0f49-480e-ae60-3a3f2bea485c", name="Reporters")

        self.assertRequest(
            mock_request,
            "post",
            "groups",
            params={"uuid": "04a4752b-0f49-480e-ae60-3a3f2bea485c"},
            data={"name": "Reporters"},
        )
        self.assertEqual(group.uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")

    def test_update_label(self, mock_request):
        mock_request.return_value = MockResponse(201, self.read_json("labels", extract_result=0))

        # check update by UUID
        label = self.client.update_label(label="04a4752b-0f49-480e-ae60-3a3f2bea485c", name="Important")

        self.assertRequest(
            mock_request,
            "post",
            "labels",
            params={"uuid": "04a4752b-0f49-480e-ae60-3a3f2bea485c"},
            data={"name": "Important"},
        )
        self.assertEqual(label.uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")

    # ==================================================================================================================
    # Delete object operations
    # ==================================================================================================================

    def test_delete_campaign_event(self, mock_request):
        mock_request.return_value = MockResponse(204, "")

        # check delete by object
        self.client.delete_campaign_event(CampaignEvent.create(uuid="9e6beda-0ce2-46cd-8810-91157f261cbd"))

        self.assertRequest(
            mock_request, "delete", "campaign_events", params={"uuid": "9e6beda-0ce2-46cd-8810-91157f261cbd"}
        )

    def test_delete_contact(self, mock_request):
        mock_request.return_value = MockResponse(204, "")

        # check delete by object
        self.client.delete_contact(Contact.create(uuid="5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"))

        self.assertRequest(mock_request, "delete", "contacts", params={"uuid": "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"})

        # check delete by UUID
        self.client.delete_contact("5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")

        self.assertRequest(mock_request, "delete", "contacts", params={"uuid": "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"})

        # check delete by URN
        self.client.delete_contact("tel:+250973635665")

        self.assertRequest(mock_request, "delete", "contacts", params={"urn": "tel:+250973635665"})

        # error if neither is provided
        self.assertRaises(ValueError, self.client.delete_contact, None)

    def test_delete_group(self, mock_request):
        mock_request.return_value = MockResponse(204, "")

        # check delete by object
        self.client.delete_group(Group.create(uuid="04a4752b-0f49-480e-ae60-3a3f2bea485c"))

        self.assertRequest(mock_request, "delete", "groups", params={"uuid": "04a4752b-0f49-480e-ae60-3a3f2bea485c"})

        # check delete by UUID
        self.client.delete_group("04a4752b-0f49-480e-ae60-3a3f2bea485c")

        self.assertRequest(mock_request, "delete", "groups", params={"uuid": "04a4752b-0f49-480e-ae60-3a3f2bea485c"})

    def test_delete_label(self, mock_request):
        mock_request.return_value = MockResponse(204, "")

        # check delete by object
        self.client.delete_label(Label.create(uuid="5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"))

        self.assertRequest(mock_request, "delete", "labels", params={"uuid": "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"})

        # check delete by UUID
        self.client.delete_label("5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9")

        self.assertRequest(mock_request, "delete", "labels", params={"uuid": "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9"})

    def test_delete_resthook_subscriber(self, mock_request):
        mock_request.return_value = MockResponse(204, "")

        # check delete by object
        self.client.delete_resthook_subscriber(ResthookSubscriber.create(id=1001))

        self.assertRequest(mock_request, "delete", "resthook_subscribers", params={"id": 1001})

        # check delete by id
        self.client.delete_resthook_subscriber(1001)

        self.assertRequest(mock_request, "delete", "resthook_subscribers", params={"id": 1001})

    # ==================================================================================================================
    # Bulk object operations
    # ==================================================================================================================

    def test_contact_actions(self, mock_request):
        mock_request.return_value = MockResponse(204, "")

        contacts = [
            Contact.create(uuid="bfff9984-38f4-4e59-998d-3663ec3c650d"),
            "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9",
            "tel:+250783835665",
        ]
        resolved_contacts = [
            "bfff9984-38f4-4e59-998d-3663ec3c650d",
            "5079cb96-a1d8-4f47-8c87-d8c7bb6ddab9",
            "tel:+250783835665",
        ]

        self.client.bulk_add_contacts(contacts=contacts, group="Testers")
        self.assertRequest(
            mock_request,
            "post",
            "contact_actions",
            data={"contacts": resolved_contacts, "action": "add", "group": "Testers"},
        )

        self.client.bulk_remove_contacts(contacts=contacts, group="Testers")
        self.assertRequest(
            mock_request,
            "post",
            "contact_actions",
            data={"contacts": resolved_contacts, "action": "remove", "group": "Testers"},
        )

        self.client.bulk_block_contacts(contacts=contacts)
        self.assertRequest(
            mock_request, "post", "contact_actions", data={"contacts": resolved_contacts, "action": "block"}
        )

        self.client.bulk_unblock_contacts(contacts=contacts)
        self.assertRequest(
            mock_request, "post", "contact_actions", data={"contacts": resolved_contacts, "action": "unblock"}
        )

        self.client.bulk_interrupt_contacts(contacts=contacts)
        self.assertRequest(
            mock_request, "post", "contact_actions", data={"contacts": resolved_contacts, "action": "interrupt"}
        )

        self.client.bulk_archive_contacts(contacts=contacts)
        self.assertRequest(
            mock_request, "post", "contact_actions", data={"contacts": resolved_contacts, "action": "archive"}
        )

        self.client.bulk_delete_contacts(contacts=contacts)
        self.assertRequest(
            mock_request, "post", "contact_actions", data={"contacts": resolved_contacts, "action": "delete"}
        )

    def test_message_actions(self, mock_request):
        mock_request.return_value = MockResponse(204, "")

        messages = [Message.create(id=1001), 1002]
        resolved_messages = [1001, 1002]

        self.client.bulk_label_messages(messages=messages, label="Testing", label_name="Spam")
        self.assertRequest(
            mock_request,
            "post",
            "message_actions",
            data={"messages": resolved_messages, "action": "label", "label": "Testing", "label_name": "Spam"},
        )

        self.client.bulk_unlabel_messages(messages=messages, label="Testing", label_name="Spam")
        self.assertRequest(
            mock_request,
            "post",
            "message_actions",
            data={"messages": resolved_messages, "action": "unlabel", "label": "Testing", "label_name": "Spam"},
        )

        self.client.bulk_archive_messages(messages=messages)
        self.assertRequest(
            mock_request, "post", "message_actions", data={"messages": resolved_messages, "action": "archive"}
        )

        self.client.bulk_restore_messages(messages=messages)
        self.assertRequest(
            mock_request, "post", "message_actions", data={"messages": resolved_messages, "action": "restore"}
        )

        self.client.bulk_delete_messages(messages=messages)
        self.assertRequest(
            mock_request, "post", "message_actions", data={"messages": resolved_messages, "action": "delete"}
        )


@patch("temba_client.clients.request")
class TembaClientVerifyTest(TembaTest):
    def test_verify_false(self, mock_request):
        client = TembaClient("example.com", "12345", verify_ssl=False)
        self.assertFalse(client.verify_ssl)

    def test_verify_true(self, mock_request):
        client = TembaClient("example.com", "12345", verify_ssl=True)
        self.assertTrue(client.verify_ssl)

    def test_verify_path(self, mock_request):
        client = TembaClient("example.com", "12345", verify_ssl="/path/to/cert")
        self.assertEqual(client.verify_ssl, "/path/to/cert")

    def test_verify_notset(self, mock_request):
        client = TembaClient("example.com", "12345")
        self.assertEqual(client.verify_ssl, None)
