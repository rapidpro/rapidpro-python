from __future__ import absolute_import, unicode_literals

import datetime
import json
import pytz
import requests
import six
import unittest

from mock import patch
from . import __version__
from .client import TembaClient
from .base import TembaObject, SimpleField, IntegerField, DatetimeField, ObjectListField, TembaException
from .base import TembaNoSuchObjectError, TembaMultipleResultsError, TembaAPIError, TembaConnectionError
from .types import Group, Broadcast
from .utils import format_iso8601, parse_iso8601


class MockResponse(object):
    """
    Mock response object with a status code and some content
    """
    def __init__(self, status_code, content=''):
        self.status_code = status_code
        self.content = content

    def raise_for_status(self):
        http_error_msg = ''

        if 400 <= self.status_code < 500:
            http_error_msg = '%s Client Error: ...' % self.status_code

        elif 500 <= self.status_code < 600:
            http_error_msg = '%s Server Error: ...' % self.status_code

        if http_error_msg:
            raise requests.HTTPError(http_error_msg, response=self)

    def json(self, **kwargs):
        return json.loads(self.content)


@patch('temba_client.base.request')
@patch('requests.models.Response', MockResponse)
class TembaClientTest(unittest.TestCase):

    def setUp(self):
        self.client = TembaClient('example.com', '1234567890', user_agent='test/0.1')

    def test_init(self, mock_request):
        # by host and token
        client = TembaClient('example.com', '1234567890', user_agent='test/0.1')
        self.assertEqual(client.root_url, 'https://example.com/api/v1')
        self.assertEqual(client.headers, {'Content-type': 'application/json',
                                          'Accept': 'application/json',
                                          'Authorization': 'Token 1234567890',
                                          'User-Agent': 'test/0.1 rapidpro-python/%s' % __version__})

        # by URL
        client = TembaClient('http://example.com/api/v1', '1234567890')
        self.assertEqual(client.root_url, 'http://example.com/api/v1')
        self.assertEqual(client.headers, {'Content-type': 'application/json',
                                          'Accept': 'application/json',
                                          'Authorization': 'Token 1234567890',
                                          'User-Agent': 'rapidpro-python/%s' % __version__})

        # by URL with trailing /
        client = TembaClient('http://example.com/api/v1/', '1234567890')
        self.assertEqual(client.root_url, 'http://example.com/api/v1')

    def test_add_contacts(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.add_contacts(contacts=['bfff9984-38f4-4e59-998d-3663ec3c650d',
                                           '7a165fe9-575b-4d15-b2ac-58fec913d603'], group='Testers')

        expected_body = {'contacts': ['bfff9984-38f4-4e59-998d-3663ec3c650d', '7a165fe9-575b-4d15-b2ac-58fec913d603'],
                         'action': 'add', 'group': 'Testers'}
        self.assert_request(mock_request, 'post', 'contact_actions', data=expected_body)

    def test_archive_messages(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.archive_messages(messages=[123, 234, 345])

        expected_body = {'messages': [123, 234, 345], 'action': 'archive'}
        self.assert_request(mock_request, 'post', 'message_actions', data=expected_body)

    def test_block_contacts(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.block_contacts(contacts=['bfff9984-38f4-4e59-998d-3663ec3c650d',
                                             '7a165fe9-575b-4d15-b2ac-58fec913d603'])

        expected_body = {'contacts': ['bfff9984-38f4-4e59-998d-3663ec3c650d', '7a165fe9-575b-4d15-b2ac-58fec913d603'],
                         'action': 'block'}
        self.assert_request(mock_request, 'post', 'contact_actions', data=expected_body)

    def test_create_broadcast(self, mock_request):
        # check by group UUID
        mock_request.return_value = MockResponse(200, _read_json('broadcasts_created'))
        broadcast = self.client.create_broadcast("Howdy", groups=['04a4752b-0f49-480e-ae60-3a3f2bea485c'])

        expected_body = {'text': "Howdy", 'groups': ['04a4752b-0f49-480e-ae60-3a3f2bea485c']}
        self.assert_request(mock_request, 'post', 'broadcasts', data=expected_body)

        self.assertEqual(broadcast.id, 234252)
        self.assertEqual(broadcast.urns, [1234])
        self.assertEqual(broadcast.contacts, [])
        self.assertEqual(broadcast.groups, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])
        self.assertEqual(broadcast.text, "Howdy")
        self.assertEqual(broadcast.status, 'Q')
        self.assertEqual(broadcast.created_on, datetime.datetime(2014, 12, 12, 22, 56, 58, 917000, pytz.utc))

    def test_create_campaign(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('campaigns_created'))
        campaign = self.client.create_campaign("Reminders", group='591de2c3-66bb-471b-9c9a-761b49a5ca69')

        expected_body = {'name': "Reminders", 'group_uuid': '591de2c3-66bb-471b-9c9a-761b49a5ca69'}
        self.assert_request(mock_request, 'post', 'campaigns', data=expected_body)

        self.assertEqual(campaign.uuid, '9ccae91f-b3f8-4c18-ad92-e795a2332c11')

    def test_create_contact(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('contacts_created'))
        contact = self.client.create_contact("Amy Amanda Allen", ['tel:+250700000005'],
                                             {'nickname': "Triple A"}, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])

        expected_body = {'name': "Amy Amanda Allen",
                         'urns': ['tel:+250700000005'],
                         'fields': {'nickname': "Triple A"},
                         'group_uuids': ['04a4752b-0f49-480e-ae60-3a3f2bea485c']}
        self.assert_request(mock_request, 'post', 'contacts', data=expected_body)

        self.assertEqual(contact.uuid, 'bfff9984-38f4-4e59-998d-3663ec3c650d')
        self.assertEqual(contact.name, "Amy Amanda Allen")
        self.assertEqual(contact.urns, ['tel:+250700000005'])
        self.assertEqual(contact.groups, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])
        self.assertEqual(contact.fields, {'nickname': 'Triple A'})
        self.assertEqual(contact.language, None)
        self.assertEqual(contact.modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

    def test_create_event(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('events_created'))
        event = self.client.create_event('9ccae91f-b3f8-4c18-ad92-e795a2332c11', "EDD", 14, 'D', -1, "Howdy")

        expected_body = {'campaign_uuid': '9ccae91f-b3f8-4c18-ad92-e795a2332c11', 'relative_to': "EDD",
                         'offset': 14, 'unit': 'D', 'delivery_hour': -1, 'message': "Howdy"}
        self.assert_request(mock_request, 'post', 'events', data=expected_body)

        self.assertEqual(event.uuid, '9e6beda-0ce2-46cd-8810-91157f261cbd')

    def test_create_field(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('fields_created'))
        field = self.client.create_field("Chat Name", 'T')

        expected_body = {'label': "Chat Name", 'value_type': 'T'}
        self.assert_request(mock_request, 'post', 'fields', data=expected_body)

        self.assertEqual(field.key, 'chat_name')
        self.assertEqual(field.label, "Chat Name")
        self.assertEqual(field.value_type, 'T')

    def test_create_flow(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('flows_created'))
        flow = self.client.create_flow("Ping", 'F')

        expected_body = {'name': "Ping", 'flow_type': 'F'}
        self.assert_request(mock_request, 'post', 'flows', data=expected_body)

        self.assertEqual(flow.uuid, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')
        self.assertEqual(flow.name, "Ping")

    def test_create_label(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('labels_created'))
        label = self.client.create_label("Really High Priority")

        expected_body = {'name': "Really High Priority"}
        self.assert_request(mock_request, 'post', 'labels', data=expected_body)

        self.assertEqual(label.uuid, 'affa6685-0725-49c7-a15a-96f301d996e4')
        self.assertEqual(label.name, "Really High Priority")
        self.assertEqual(label.count, 0)

    def test_create_runs(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('runs_created'))
        runs = self.client.create_runs('04a4752b-0f49-480e-ae60-3a3f2bea485c',
                                       ['bfff9984-38f4-4e59-998d-3663ec3c650d'], True)

        expected_body = {"contacts": ['bfff9984-38f4-4e59-998d-3663ec3c650d'],
                         "restart_participants": 1,
                         "flow_uuid": "04a4752b-0f49-480e-ae60-3a3f2bea485c"}
        self.assert_request(mock_request, 'post', 'runs', data=expected_body)

        self.assertEqual(len(runs), 2)

    def test_delete_contact(self, mock_request):
        # check deleting an existing contact
        mock_request.return_value = MockResponse(204, '')
        self.client.delete_contact('bfff9984-38f4-4e59-998d-3663ec3c650d')

        self.assert_request(mock_request, 'delete', 'contacts', params={'uuid': 'bfff9984-38f4-4e59-998d-3663ec3c650d'})

        # check deleting a non-existent contact
        mock_request.return_value = MockResponse(404, 'NOT FOUND')
        self.assertRaises(TembaAPIError, self.client.delete_contact, 'bfff9984-38f4-4e59-998d-3663ec3c650d')

    def test_delete_contacts(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.delete_contacts(contacts=['bfff9984-38f4-4e59-998d-3663ec3c650d',
                                              '7a165fe9-575b-4d15-b2ac-58fec913d603'])

        expected_body = {'contacts': ['bfff9984-38f4-4e59-998d-3663ec3c650d', '7a165fe9-575b-4d15-b2ac-58fec913d603'],
                         'action': 'delete'}
        self.assert_request(mock_request, 'post', 'contact_actions', data=expected_body)

    def test_delete_event(self, mock_request):
        mock_request.return_value = MockResponse(204, '')
        self.client.delete_event('bfff9984-38f4-4e59-998d-3663ec3c650d')

        self.assert_request(mock_request, 'delete', 'events', params={'uuid': 'bfff9984-38f4-4e59-998d-3663ec3c650d'})

    def test_delete_messages(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.delete_messages(messages=[123, 234, 345])

        expected_body = {'messages': [123, 234, 345], 'action': 'delete'}
        self.assert_request(mock_request, 'post', 'message_actions', data=expected_body)

    def test_expire_contacts(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.expire_contacts(contacts=['bfff9984-38f4-4e59-998d-3663ec3c650d',
                                              '7a165fe9-575b-4d15-b2ac-58fec913d603'])

        expected_body = {'contacts': ['bfff9984-38f4-4e59-998d-3663ec3c650d', '7a165fe9-575b-4d15-b2ac-58fec913d603'],
                         'action': 'expire'}
        self.assert_request(mock_request, 'post', 'contact_actions', data=expected_body)

    def test_get_boundaries(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('boundaries_multiple'))
        boundaries = self.client.get_boundaries()

        self.assert_request(mock_request, 'get', 'boundaries')

        self.assertEqual(len(boundaries), 2)
        boundary1 = boundaries[0]
        boundary2 = boundaries[1]

        self.assertEqual(boundary1.boundary, "R195269")
        self.assertEqual(boundary1.name, "Burundi")
        self.assertEqual(boundary1.level, 0)
        self.assertFalse(boundary1.parent)
        self.assertEqual(boundary1.geometry.type, "MultiPolygon")
        self.assertIsInstance(boundary1.geometry.coordinates, list)

        self.assertEqual(boundary2.level, 1)
        self.assertEqual(boundary2.parent, "R195269")

    def test_get_broadcast(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('broadcasts_single'))
        broadcast = self.client.get_broadcast(1234)

        self.assert_request(mock_request, 'get', 'broadcasts', params={'id': 1234})

        self.assertEqual(broadcast.id, 1234)
        self.assertEqual(broadcast.urns, [55454])
        self.assertEqual(broadcast.contacts, [])
        self.assertEqual(broadcast.groups, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])
        self.assertEqual(broadcast.text, "Hello")
        self.assertEqual(broadcast.created_on, datetime.datetime(2014, 11, 12, 22, 56, 58, 917000, pytz.utc))
        self.assertEqual(broadcast.status, 'Q')

    def test_get_broadcasts(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('broadcasts_multiple'))
        broadcasts = self.client.get_broadcasts()

        self.assert_request(mock_request, 'get', 'broadcasts')

        self.assertEqual(len(broadcasts), 2)
        self.assertEqual(broadcasts[0].id, 1234)

        # check all params
        self.client.get_broadcasts(ids=[1234, 2345],
                                   statuses=['P', 'Q'],
                                   before=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc),
                                   after=datetime.datetime(2014, 12, 12, 22, 34, 36, 234000, pytz.utc))
        self.assert_request(mock_request, 'get', 'broadcasts', params={'id': [1234, 2345],
                                                                       'status': ['P', 'Q'],
                                                                       'before': '2014-12-12T22:34:36.123000',
                                                                       'after': '2014-12-12T22:34:36.234000'})

    def test_get_campaign(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('campaigns_single'))
        campaign = self.client.get_campaign('9ccae91f-b3f8-4c18-ad92-e795a2332c11')

        self.assert_request(mock_request, 'get', 'campaigns', params={'uuid': '9ccae91f-b3f8-4c18-ad92-e795a2332c11'})

        self.assertEqual(campaign.uuid, '9ccae91f-b3f8-4c18-ad92-e795a2332c11')
        self.assertEqual(campaign.name, "Mother Reminders")
        self.assertEqual(campaign.group, '591de2c3-66bb-471b-9c9a-761b49a5ca69')
        self.assertEqual(campaign.created_on, datetime.datetime(2015, 6, 8, 12, 18, 7, 671000, pytz.utc))

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_campaign, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('campaigns_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_campaign, '9ccae91f-b3f8-4c18-ad92-e795a2332c11')

    def test_get_campaigns(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('campaigns_multiple'))
        campaigns = self.client.get_campaigns()

        self.assert_request(mock_request, 'get', 'campaigns')

        self.assertEqual(len(campaigns), 2)
        self.assertEqual(campaigns[0].uuid, '9ccae91f-b3f8-4c18-ad92-e795a2332c11')

    def test_get_contact(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('contacts_single'))
        contact = self.client.get_contact('bfff9984-38f4-4e59-998d-3663ec3c650d')

        self.assert_request(mock_request, 'get', 'contacts', params={'uuid': 'bfff9984-38f4-4e59-998d-3663ec3c650d'})

        self.assertEqual(contact.uuid, 'bfff9984-38f4-4e59-998d-3663ec3c650d')
        self.assertEqual(contact.name, "John Smith")
        self.assertEqual(contact.urns, ['tel:+250700000001'])
        self.assertEqual(contact.groups, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])
        self.assertEqual(contact.fields, {'nickname': 'Hannibal'})
        self.assertEqual(contact.language, None)
        self.assertEqual(contact.blocked, False)
        self.assertEqual(contact.failed, False)
        self.assertEqual(contact.modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_contact, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_contact, 'bfff9984-38f4-4e59-998d-3663ec3c650d')

    def test_get_contacts(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        contacts = self.client.get_contacts()

        self.assert_request(mock_request, 'get', 'contacts')

        self.assertEqual(len(contacts), 4)
        self.assertEqual(contacts[0].uuid, "bfff9984-38f4-4e59-998d-3663ec3c650d")

        # check filtering by group_uuids
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        self.client.get_contacts(groups=["abc"])

        self.assert_request(mock_request, 'get', 'contacts', params={'group_uuids': ['abc']})

        # check filtering by group object
        group1 = Group.create(name="A-Team", uuid='xyz', size=4)
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        self.client.get_contacts(groups=[group1])

        self.assert_request(mock_request, 'get', 'contacts', params={'group_uuids': ['xyz']})

        # check filtering modified after a date
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        self.client.get_contacts(after=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc))

        self.assert_request(mock_request, 'get', 'contacts', params={'after': '2014-12-12T22:34:36.123000'})

        # check filtering modified before a date
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        self.client.get_contacts(before=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc))

        self.assert_request(mock_request, 'get', 'contacts', params={'before': '2014-12-12T22:34:36.123000'})

        # check filtering modified between dates
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        self.client.get_contacts(after=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc),
                                 before=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc))

        self.assert_request(mock_request, 'get', 'contacts', params={'after': '2014-12-12T22:34:36.123000',
                                                                     'before': '2014-12-12T22:34:36.123000'})

        # check multiple pages
        mock_request.side_effect = (MockResponse(200, _read_json('contacts_multipage_1')),
                                    MockResponse(200, _read_json('contacts_multipage_2')),
                                    MockResponse(200, _read_json('contacts_multipage_3')))
        contacts = self.client.get_contacts(after=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc))
        self.assertEqual(len(contacts), 21)
        self.assert_request_url(mock_request, 'get',
                                'https://example.com/api/v1/contacts.json?page=3&before=2014-12-12T22:34:36.123')

        # test with paging
        mock_request.side_effect = (MockResponse(200, _read_json('contacts_multipage_1')),
                                    MockResponse(200, _read_json('contacts_multipage_2')),
                                    MockResponse(200, _read_json('contacts_multipage_3')))
        pager = self.client.pager()
        contacts = self.client.get_contacts(pager=pager)
        self.assertEqual(len(contacts), 10)
        self.assertEqual(pager.total, 21)
        self.assertTrue(pager.has_more())
        contacts = self.client.get_contacts(pager=pager)
        self.assertEqual(len(contacts), 10)
        self.assertEqual(pager.total, 21)
        self.assertTrue(pager.has_more())
        contacts = self.client.get_contacts(pager=pager)
        self.assertEqual(len(contacts), 1)
        self.assertEqual(pager.total, 21)
        self.assertFalse(pager.has_more())

        # test asking for explicit page
        mock_request.return_value = MockResponse(200, _read_json('contacts_multipage_2'))
        mock_request.side_effect = None
        pager = self.client.pager(start_page=2)
        contacts = self.client.get_contacts(pager=pager)
        self.assertEqual(len(contacts), 10)

        self.assert_request(mock_request, 'get', 'contacts', params={'page': 2})

        # test with connection error
        mock_request.side_effect = requests.exceptions.ConnectionError
        self.assertRaises(TembaConnectionError, self.client.get_contacts)

    def test_get_event(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('events_single'))
        event = self.client.get_event('9e6beda-0ce2-46cd-8810-91157f261cbd')

        self.assert_request(mock_request, 'get', 'events', params={'uuid': '9e6beda-0ce2-46cd-8810-91157f261cbd'})

        self.assertEqual(event.uuid, '9e6beda-0ce2-46cd-8810-91157f261cbd')
        self.assertEqual(event.campaign, '9ccae91f-b3f8-4c18-ad92-e795a2332c11')
        self.assertEqual(event.relative_to, "EDD")
        self.assertEqual(event.offset, 14)
        self.assertEqual(event.unit, 'D')
        self.assertEqual(event.delivery_hour, -1)
        self.assertEqual(event.message, "")
        self.assertEqual(event.flow, '70c38f94-ab42-4666-86fd-3c76139110d3')
        self.assertEqual(event.created_on, datetime.datetime(2015, 6, 8, 12, 18, 7, 671000, pytz.utc))

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_event, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('events_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_event, '9e6beda-0ce2-46cd-8810-91157f261cbd')

    def test_get_events(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('events_multiple'))
        events = self.client.get_events()

        self.assert_request(mock_request, 'get', 'events')

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].uuid, '9e6beda-0ce2-46cd-8810-91157f261cbd')

    def test_get_field(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('fields_single'))
        field = self.client.get_field('chat_name')

        self.assert_request(mock_request, 'get', 'fields', params={'key': 'chat_name'})

        self.assertEqual(field.label, "Chat Name")
        self.assertEqual(field.value_type, 'T')

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_field, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('fields_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_flow, 'chat_name')

    def test_get_fields(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('fields_multiple'))
        fields = self.client.get_fields()

        self.assert_request(mock_request, 'get', 'fields')

        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0].key, 'chat_name')

    def test_get_flow(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('flows_single'))
        flow = self.client.get_flow('a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')

        self.assert_request(mock_request, 'get', 'flows', params={'uuid': 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d'})

        self.assertEqual(flow.uuid, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')
        self.assertEqual(flow.name, "Ping")
        self.assertEqual(flow.archived, False)
        self.assertEqual(flow.labels, ["Registration"])
        self.assertEqual(flow.participants, 5)
        self.assertEqual(flow.runs, 6)
        self.assertEqual(flow.completed_runs, 4)
        self.assertEqual(flow.expires, 720)
        self.assertEqual(len(flow.rulesets), 1)
        self.assertEqual(flow.rulesets[0].uuid, 'e16ff762-6051-4940-964a-9b2efcb670ca')
        self.assertEqual(flow.rulesets[0].label, "Rule 1")
        self.assertEqual(flow.rulesets[0].response_type, "C")
        self.assertEqual(flow.created_on, datetime.datetime(2014, 12, 11, 13, 47, 55, 288000, pytz.utc))

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_flow, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('flows_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_flow, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')

    def test_get_flows(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('flows_multiple'))
        flows = self.client.get_flows()

        self.assert_request(mock_request, 'get', 'flows')

        self.assertEqual(len(flows), 2)
        self.assertEqual(flows[0].uuid, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')

        # check all params
        self.client.get_flows(uuids=['abc', 'xyz'],
                              archived=False,
                              labels=['polls', 'events'],
                              before=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc),
                              after=datetime.datetime(2014, 12, 12, 22, 34, 36, 234000, pytz.utc))
        self.assert_request(mock_request, 'get', 'flows', params={'uuid': ['abc', 'xyz'],
                                                                  'archived': 0,
                                                                  'label': ['polls', 'events'],
                                                                  'before': '2014-12-12T22:34:36.123000',
                                                                  'after': '2014-12-12T22:34:36.234000'})

    def test_get_group(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('groups_single'))
        group = self.client.get_group('04a4752b-0f49-480e-ae60-3a3f2bea485c')

        self.assert_request(mock_request, 'get', 'groups', params={'uuid': '04a4752b-0f49-480e-ae60-3a3f2bea485c'})

        self.assertEqual(group.uuid, '04a4752b-0f49-480e-ae60-3a3f2bea485c')
        self.assertEqual(group.name, "The A-Team")
        self.assertEqual(group.size, 4)

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_group, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('groups_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_group, '04a4752b-0f49-480e-ae60-3a3f2bea485c')

    def test_get_groups(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('groups_multiple'))
        groups = self.client.get_groups()

        self.assert_request(mock_request, 'get', 'groups')

        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")

        # check filtering by name
        self.client.get_groups(name="A-Team")
        self.assert_request(mock_request, 'get', 'groups', params={'name': 'A-Team'})

    def test_get_label(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('labels_single'))
        label = self.client.get_label('946c930d-83b1-4982-a797-9f0c0cc554de')

        self.assert_request(mock_request, 'get', 'labels', params={'uuid': '946c930d-83b1-4982-a797-9f0c0cc554de'})

        self.assertEqual(label.uuid, '946c930d-83b1-4982-a797-9f0c0cc554de')
        self.assertEqual(label.name, "High Priority")
        self.assertEqual(label.count, 4567)

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_label, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('labels_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_label, '946c930d-83b1-4982-a797-9f0c0cc554de')

    def test_get_labels(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('labels_multiple'))
        labels = self.client.get_labels()

        self.assert_request(mock_request, 'get', 'labels')

        self.assertEqual(len(labels), 2)
        self.assertEqual(labels[0].uuid, "946c930d-83b1-4982-a797-9f0c0cc554de")

        # check filtering by name
        self.client.get_labels(name="Priority")
        self.assert_request(mock_request, 'get', 'labels', params={'name': 'Priority'})

    def test_get_message(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('messages_single'))
        message = self.client.get_message(13441143)

        self.assert_request(mock_request, 'get', 'messages', params={'id': 13441143})

        self.assertEqual(message.id, 13441143)
        self.assertEqual(message.broadcast, None)
        self.assertEqual(message.contact, '92fc2eee-a19a-4589-81b6-1366d2b1cb12')
        self.assertEqual(message.urn, 'tel:+250700000001')
        self.assertEqual(message.status, 'H')
        self.assertEqual(message.type, 'F')
        self.assertEqual(message.labels, ["Important"])
        self.assertEqual(message.direction, 'I')
        self.assertEqual(message.text, "Hello \u0633.")
        self.assertEqual(message.created_on, datetime.datetime(2014, 12, 12, 13, 34, 44, 0, pytz.utc))
        self.assertEqual(message.sent_on, None)
        self.assertEqual(message.delivered_on, datetime.datetime(2014, 12, 12, 13, 35, 12, 861000, pytz.utc))

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_message, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('messages_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_message, 13441143)

    def test_get_messages(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('messages_multiple'))
        messages = self.client.get_messages()

        self.assert_request(mock_request, 'get', 'messages')

        self.assertEqual(len(messages), 2)

        # check with params
        self.client.get_messages(ids=[123, 234],
                                 broadcasts=[345, 456],
                                 contacts=['abc'],
                                 labels=['polls', '+events', '-flagged'],
                                 before=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc),
                                 after=datetime.datetime(2014, 12, 12, 22, 34, 36, 234000, pytz.utc),
                                 text='heists',
                                 archived=False)

        self.assert_request(mock_request, 'get', 'messages', params={'id': [123, 234],
                                                                     'broadcast': [345, 456],
                                                                     'contact': ['abc'],
                                                                     'label': ['polls', '+events', '-flagged'],
                                                                     'before': '2014-12-12T22:34:36.123000',
                                                                     'after': '2014-12-12T22:34:36.234000',
                                                                     'text': 'heists',
                                                                     'archived': 0})

        # test getting by broadcast object (should extract id)
        broadcast = Broadcast.create(id=123)
        self.client.get_messages(broadcasts=[broadcast])

        self.assert_request(mock_request, 'get', 'messages', params={'broadcast': [123]})

    def test_get_org(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('org'))
        org = self.client.get_org()

        self.assert_request(mock_request, 'get', 'org')

        self.assertEqual(org.name, "Nyaruka")
        self.assertEqual(org.country, "RW")
        self.assertEqual(org.languages, ["eng", "fre"])
        self.assertEqual(org.primary_language, "eng")
        self.assertEqual(org.timezone, "Africa/Kigali")
        self.assertEqual(org.date_style, "day_first")
        self.assertEqual(org.anon, False)

    def test_get_results(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('results_missing_optional'))
        results = self.client.get_results(ruleset='aabe7d0f-bf27-4e76-a6b3-4d26ec18dd58')

        self.assert_request(mock_request, 'get', 'results', params={'ruleset': 'aabe7d0f-bf27-4e76-a6b3-4d26ec18dd58'})

        self.assertEqual(results[0].boundary, None)
        self.assertEqual(results[0].categories[0].label, "Male")
        self.assertEqual(results[0].categories[0].count, 2)
        self.assertEqual(results[0].categories[1].label, "Female")
        self.assertEqual(results[0].categories[1].count, 5)
        self.assertEqual(results[0].set, 7)
        self.assertEqual(results[0].unset, 3)
        self.assertEqual(results[0].label, "All")
        self.assertEqual(results[0].open_ended, None)

        mock_request.return_value = MockResponse(200, _read_json('results_missing_required'))
        self.assertRaises(TembaException, self.client.get_results)

    def test_get_run(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('runs_single'))
        run = self.client.get_run(123)

        self.assert_request(mock_request, 'get', 'runs', params={'run': 123})

        self.assertEqual(run.id, 1258967)
        self.assertEqual(run.flow, 'aab50309-59a6-4502-aafb-73bcb072b695')
        self.assertEqual(run.contact, '7f16e47a-dbca-47d3-9d2f-d79dc5e1eb26')
        self.assertEqual(run.completed, True)
        self.assertEqual(len(run.steps), 5)
        self.assertEqual(run.steps[0].node, '9a8870d7-f7a4-4f11-9379-a158d1fad6f7')
        self.assertEqual(run.steps[0].text, "This is the sheep poll. How many sheep do you have?")
        self.assertEqual(run.steps[0].value, "None")
        self.assertEqual(run.steps[0].type, "A")
        self.assertEqual(run.steps[0].arrived_on, datetime.datetime(2015, 1, 26, 13, 56, 18, 809000, pytz.utc))
        self.assertEqual(run.steps[0].left_on, datetime.datetime(2015, 1, 26, 13, 56, 18, 829000, pytz.utc))
        self.assertEqual(len(run.values), 1)
        self.assertEqual(run.values[0].category, "1 - 100")
        self.assertEqual(run.values[0].node, 'a227e4cb-351b-4284-b2bf-b91dc27ace57')
        self.assertEqual(run.values[0].text, "12")
        self.assertEqual(run.values[0].rule_value, "12")
        self.assertEqual(run.values[0].value, "12.00000000")
        self.assertEqual(run.values[0].label, "Number of Sheep")
        self.assertEqual(run.values[0].time, datetime.datetime(2015, 1, 26, 13, 57, 55, 704000, pytz.utc))
        self.assertEqual(run.created_on, datetime.datetime(2015, 1, 26, 13, 56, 18, 689000, pytz.utc))
        self.assertEqual(run.expires_on, datetime.datetime(2015, 7, 8, 1, 10, 43, 111000, pytz.utc))
        self.assertEqual(run.expired_on, None)

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaNoSuchObjectError, self.client.get_run, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('groups_multiple'))
        self.assertRaises(TembaMultipleResultsError, self.client.get_group, '9ec96b73-78c3-4029-ba86-5279c92996fc')

    def test_get_runs(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('runs_multiple'))
        runs = self.client.get_runs()

        self.assert_request(mock_request, 'get', 'runs')

        self.assertEqual(len(runs), 2)

        # check with all params
        self.client.get_runs(ids=[123, 234],
                             flows=['a68567fa-ad95-45fc-b5f7-3ce90ebbd46d'],
                             after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978000, pytz.utc),
                             before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917000, pytz.utc))

        self.assert_request(mock_request, 'get', 'runs', params={'run': [123, 234],
                                                                 'flow_uuid': ['a68567fa-ad95-45fc-b5f7-3ce90ebbd46d'],
                                                                 'after': '2014-12-12T22:34:36.978000',
                                                                 'before': '2014-12-12T22:56:58.917000'})

    def test_label_messages(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.label_messages(messages=[123, 234, 345], label="Test")

        expected_body = {'messages': [123, 234, 345], 'action': 'label', 'label': "Test"}
        self.assert_request(mock_request, 'post', 'message_actions', data=expected_body)

    def test_remove_contacts(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.remove_contacts(contacts=['bfff9984-38f4-4e59-998d-3663ec3c650d',
                                              '7a165fe9-575b-4d15-b2ac-58fec913d603'], group='Testers')

        expected_body = {'contacts': ['bfff9984-38f4-4e59-998d-3663ec3c650d', '7a165fe9-575b-4d15-b2ac-58fec913d603'],
                         'action': 'remove', 'group': 'Testers'}
        self.assert_request(mock_request, 'post', 'contact_actions', data=expected_body)

    def test_unarchive_messages(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.unarchive_messages(messages=[123, 234, 345])

        expected_body = {'messages': [123, 234, 345], 'action': 'unarchive'}
        self.assert_request(mock_request, 'post', 'message_actions', data=expected_body)

    def test_unblock_contacts(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.unblock_contacts(contacts=['bfff9984-38f4-4e59-998d-3663ec3c650d',
                                               '7a165fe9-575b-4d15-b2ac-58fec913d603'])

        expected_body = {'contacts': ['bfff9984-38f4-4e59-998d-3663ec3c650d', '7a165fe9-575b-4d15-b2ac-58fec913d603'],
                         'action': 'unblock'}
        self.assert_request(mock_request, 'post', 'contact_actions', data=expected_body)

    def test_unlabel_messages(self, mock_request):
        mock_request.return_value = MockResponse(204)
        self.client.unlabel_messages(messages=[123, 234, 345], label_uuid='affa6685-0725-49c7-a15a-96f301d996e4')

        expected_body = {'messages': [123, 234, 345], 'action': 'unlabel',
                         'label_uuid': 'affa6685-0725-49c7-a15a-96f301d996e4'}
        self.assert_request(mock_request, 'post', 'message_actions', data=expected_body)

    def test_update_contact(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('contacts_created'))
        contact = self.client.update_contact('bfff9984-38f4-4e59-998d-3663ec3c650d',
                                             "Amy Amanda Allen",
                                             ['tel:+250700000005'],
                                             {'nickname': "Triple A"},
                                             ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])

        expected_body = {'fields': {'nickname': "Triple A"},
                         'urns': ['tel:+250700000005'],
                         'uuid': 'bfff9984-38f4-4e59-998d-3663ec3c650d',
                         'name': "Amy Amanda Allen",
                         'group_uuids': ['04a4752b-0f49-480e-ae60-3a3f2bea485c']}
        self.assert_request(mock_request, 'post', 'contacts', data=expected_body)

        self.assertEqual(contact.uuid, 'bfff9984-38f4-4e59-998d-3663ec3c650d')
        self.assertEqual(contact.name, "Amy Amanda Allen")
        self.assertEqual(contact.urns, ['tel:+250700000005'])
        self.assertEqual(contact.groups, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])
        self.assertEqual(contact.fields, {'nickname': 'Triple A'})
        self.assertEqual(contact.language, None)
        self.assertEqual(contact.modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

    def test_update_flow(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('flows_created'))
        flow = self.client.update_flow('a68567fa-ad95-45fc-b5f7-3ce90ebbd46d', "Ping", 'F')

        expected_body = {'uuid': 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d',
                         'name': "Ping",
                         'flow_type': 'F'}
        self.assert_request(mock_request, 'post', 'flows', data=expected_body)

        self.assertEqual(flow.uuid, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')
        self.assertEqual(flow.name, "Ping")

    def test_update_label(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('labels_created'))
        label = self.client.update_label('affa6685-0725-49c7-a15a-96f301d996e4', "Really High Priority")

        expected_body = {'uuid': 'affa6685-0725-49c7-a15a-96f301d996e4',
                         'name': "Really High Priority"}
        self.assert_request(mock_request, 'post', 'labels', data=expected_body)

        self.assertEqual(label.uuid, 'affa6685-0725-49c7-a15a-96f301d996e4')
        self.assertEqual(label.name, "Really High Priority")

        # test when we get 400 error back
        mock_request.return_value = MockResponse(400, '{"uuid": ["No such message label with UUID: 12345678"]}')

        try:
            self.client.update_label('12345678', "Really High Priority")
        except TembaAPIError as ex:
            self.assertEqual(ex.errors, {'uuid': ["No such message label with UUID: 12345678"]})
            self.assertEqual(six.text_type(ex), "API request error. Caused by: No such message label with UUID: 12345678")
            self.assertEqual(str(ex), "API request error. Caused by: No such message label with UUID: 12345678")
        else:
            self.fail("Should have thrown exception")

        # test when (for some reason) we get a 400 but invalid JSON
        mock_request.return_value = MockResponse(400, 'xyz')

        try:
            self.client.update_label('12345678', "Really High Priority")
        except TembaAPIError as ex:
            self.assertEqual(ex.errors, {})
            self.assertEqual(six.text_type(ex), "API request error. Caused by: 400 Client Error: ...")
        else:
            self.fail("Should have thrown exception")

    def assert_request_url(self, mock, method, url, **kwargs):
        """
        Asserts that a request was made to the given url with the given parameters
        """
        mock.assert_called_with(method, url,
                                headers={'Content-type': 'application/json',
                                         'Authorization': 'Token 1234567890',
                                         'Accept': u'application/json',
                                         'User-Agent': 'test/0.1 rapidpro-python/%s' % __version__}, **kwargs)

    def assert_request(self, mock, method, endpoint, **kwargs):
        """
        Asserts that a request was made to the given endpoint with the given parameters
        """
        mock.assert_called_with(method, 'https://example.com/api/v1/%s.json' % endpoint,
                                headers={'Content-type': 'application/json',
                                         'Authorization': 'Token 1234567890',
                                         'Accept': u'application/json',
                                         'User-Agent': 'test/0.1 rapidpro-python/%s' % __version__}, **kwargs)


class UtilsTest(unittest.TestCase):
    class TestTZ(datetime.tzinfo):
        def utcoffset(self, dt):
            return datetime.timedelta(hours=-5)

    def test_format_iso8601(self):
        d = datetime.datetime(2014, 1, 2, 3, 4, 5, 6, UtilsTest.TestTZ())
        self.assertEqual(format_iso8601(d), '2014-01-02T08:04:05.000006')

    def test_parse_iso8601(self):
        dt = datetime.datetime(2014, 1, 2, 3, 4, 5, 0, pytz.UTC)
        self.assertEqual(parse_iso8601('2014-01-02T03:04:05.000000Z'), dt)
        self.assertEqual(parse_iso8601('2014-01-02T03:04:05.000000'), dt)
        self.assertEqual(parse_iso8601('2014-01-02T03:04:05'), dt)

        d = datetime.datetime(2014, 1, 2, 0, 0, 0, 0, pytz.UTC)
        self.assertEqual(parse_iso8601('2014-01-02'), d)


class TestSubType(TembaObject):
    zed = SimpleField()


class TestType(TembaObject):
    foo = SimpleField()
    bar = IntegerField()
    doh = DatetimeField()
    hum = ObjectListField(item_class=TestSubType)


class TembaObjectTest(unittest.TestCase):
    def test_create(self):
        # unspecified fields become None
        obj = TestType.create(foo='a', bar=123)
        self.assertEqual(obj.foo, 'a')
        self.assertEqual(obj.bar, 123)
        self.assertEqual(obj.doh, None)
        self.assertEqual(obj.hum, None)

        # exception if field doesn't exist
        self.assertRaises(ValueError, TestType.create, foo='a', xyz="abc")

    def test_deserialize(self):
        obj = TestType.deserialize({'foo': 'a', 'bar': 123, 'doh': '2014-01-02T03:04:05', 'hum': [{'zed': 'b'}]})
        self.assertEqual(obj.foo, 'a')
        self.assertEqual(obj.bar, 123)
        self.assertEqual(obj.doh, datetime.datetime(2014, 1, 2, 3, 4, 5, 0, pytz.UTC))
        self.assertEqual(len(obj.hum), 1)
        self.assertEqual(obj.hum[0].zed, 'b')

        # exception when integer field receives non-number
        self.assertRaises(TembaException, TestType.deserialize,
                          {'foo': 'a', 'bar': 'x', 'doh': '2014-01-02T03:04:05', 'hum': []})

        # exception when object list field receives non-list
        self.assertRaises(TembaException, TestType.deserialize,
                          {'foo': 'a', 'bar': 'x', 'doh': '2014-01-02T03:04:05', 'hum': {}})


def _read_json(filename):
    handle = open('test_files/%s.json' % filename)
    contents = six.text_type(handle.read())
    handle.close()
    return contents
