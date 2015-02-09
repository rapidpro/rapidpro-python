from __future__ import absolute_import, unicode_literals

import datetime
import json
import pytz
import requests
import unittest

from mock import patch
from . import TembaClient
from .base import TembaException, TembaObject, SimpleField, DatetimeField
from .types import Group
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


@patch('temba.base.request')
@patch('requests.models.Response', MockResponse)
class TembaClientTest(unittest.TestCase):

    def setUp(self):
        self.client = TembaClient('example.com', '1234567890')

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

    def test_create_field(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('fields_created'))
        field = self.client.create_field("Chat Name", 'T')

        expected_body = {'label': "Chat Name", 'value_type': 'T'}
        self.assert_request(mock_request, 'post', 'fields', data=expected_body)

        self.assertEqual(field.key, 'chat_name')
        self.assertEqual(field.label, "Chat Name")
        self.assertEqual(field.value_type, 'T')

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
        self.assertRaises(TembaException, self.client.delete_contact, 'bfff9984-38f4-4e59-998d-3663ec3c650d')

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
        self.assertEqual(contact.modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaException, self.client.get_contact, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        self.assertRaises(TembaException, self.client.get_contact, 'bfff9984-38f4-4e59-998d-3663ec3c650d')

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

        # check multiple pages
        mock_request.side_effect = (MockResponse(200, _read_json('contacts_multipage_1')),
                                    MockResponse(200, _read_json('contacts_multipage_2')),
                                    MockResponse(200, _read_json('contacts_multipage_3')))
        contacts = self.client.get_contacts()
        self.assertEqual(len(contacts), 21)

    def test_get_field(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('fields_single'))
        field = self.client.get_field('chat_name')

        self.assert_request(mock_request, 'get', 'fields', params={'key': 'chat_name'})

        self.assertEqual(field.label, "Chat Name")
        self.assertEqual(field.value_type, 'T')

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaException, self.client.get_field, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('fields_multiple'))
        self.assertRaises(TembaException, self.client.get_flow, 'chat_name')

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
        self.assertEqual(len(flow.rulesets), 1)
        self.assertEqual(flow.rulesets[0].uuid, 'e16ff762-6051-4940-964a-9b2efcb670ca')
        self.assertEqual(flow.rulesets[0].label, "Rule 1")
        self.assertEqual(flow.created_on, datetime.datetime(2014, 12, 11, 13, 47, 55, 288000, pytz.utc))

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaException, self.client.get_flow, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('flows_multiple'))
        self.assertRaises(TembaException, self.client.get_flow, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')

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
        self.assertRaises(TembaException, self.client.get_group, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('groups_multiple'))
        self.assertRaises(TembaException, self.client.get_group, '04a4752b-0f49-480e-ae60-3a3f2bea485c')

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
                                 labels=['polls', 'events'],
                                 before=datetime.datetime(2014, 12, 12, 22, 34, 36, 123000, pytz.utc),
                                 after=datetime.datetime(2014, 12, 12, 22, 34, 36, 234000, pytz.utc))
        self.assert_request(mock_request, 'get', 'messages', params={'id': [123, 234],
                                                                     'broadcast': [345, 456],
                                                                     'contact': ['abc'],
                                                                     'label': ['polls', 'events'],
                                                                     'before': '2014-12-12T22:34:36.123000',
                                                                     'after': '2014-12-12T22:34:36.234000'})

    def test_get_run(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('runs_single'))
        run = self.client.get_run(123)

        self.assert_request(mock_request, 'get', 'runs', params={'run': 123})

        self.assertEqual(run.id, 1258967)
        self.assertEqual(run.flow, 'aab50309-59a6-4502-aafb-73bcb072b695')
        self.assertEqual(run.contact, '7f16e47a-dbca-47d3-9d2f-d79dc5e1eb26')
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

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaException, self.client.get_run, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('groups_multiple'))
        self.assertRaises(TembaException, self.client.get_group, '9ec96b73-78c3-4029-ba86-5279c92996fc')

    def test_get_runs(self, mock_request):
        # check no params
        mock_request.return_value = MockResponse(200, _read_json('runs_multiple'))
        runs = self.client.get_runs()

        self.assert_request(mock_request, 'get', 'runs')

        self.assertEqual(len(runs), 2)

        # check with all params
        runs = self.client.get_runs(ids=[123, 234],
                                    flows=['a68567fa-ad95-45fc-b5f7-3ce90ebbd46d'],
                                    after=datetime.datetime(2014, 12, 12, 22, 34, 36, 978000, pytz.utc),
                                    before=datetime.datetime(2014, 12, 12, 22, 56, 58, 917000, pytz.utc))

        self.assert_request(mock_request, 'get', 'runs', params={'run': [123, 234],
                                                                 'flow_uuid': ['a68567fa-ad95-45fc-b5f7-3ce90ebbd46d'],
                                                                 'after': '2014-12-12T22:34:36.978000',
                                                                 'before': '2014-12-12T22:56:58.917000'})

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

    def assert_request(self, mock, method, endpoint, **kwargs):
        """
        Asserts that a request was made to the given endpoint with the given parameters
        """
        mock.assert_called_with(method, 'https://example.com/api/v1/%s.json' % endpoint,
                                headers={'Content-type': 'application/json',
                                         'Authorization': 'Token 1234567890',
                                         'Accept': u'application/json'}, **kwargs)


@patch('requests.models.Response', MockResponse)
class TembaExceptionTest(unittest.TestCase):
    def test_extract_errors(self):
        response = MockResponse(400, '{"field_1": ["Error #1", "Error #2"], "field_2": ["Error #3"]}')
        msg = TembaException._extract_errors(response)
        self.assertTrue(msg == "Error #1. Error #2. Error #3" or msg == "Error #3. Error #1. Error #2")


class UtilsTest(unittest.TestCase):
    class TestTZ(datetime.tzinfo):
        def utcoffset(self, dt):
            return datetime.timedelta(hours=-5)

    def test_format_iso8601(self):
        d = datetime.datetime(2014, 1, 2, 3, 4, 5, 6, UtilsTest.TestTZ())
        self.assertEqual(format_iso8601(d), '2014-01-02T08:04:05.000006')

    def test_parse_iso8601(self):
        d = datetime.datetime(2014, 1, 2, 3, 4, 5, 0, pytz.UTC)
        self.assertEqual(parse_iso8601('2014-01-02T03:04:05.000000Z'), d)
        self.assertEqual(parse_iso8601('2014-01-02T03:04:05.000000'), d)
        self.assertEqual(parse_iso8601('2014-01-02T03:04:05'), d)


class TembaObjectTest(unittest.TestCase):
    class TestType(TembaObject):
        foo = SimpleField()
        bar = DatetimeField()

    def test_create(self):
        obj = TembaObjectTest.TestType.create(foo=123, bar="abc")
        self.assertEqual(obj.foo, 123)
        self.assertEqual(obj.bar, "abc")
        obj = TembaObjectTest.TestType.create(foo=123)
        self.assertEqual(obj.foo, 123)
        self.assertIsNone(obj.bar)

        self.assertRaises(ValueError, TembaObjectTest.TestType.create, foo=123, xyz="abc")


def _read_json(filename):
    handle = open('test_files/%s.json' % filename)
    contents = unicode(handle.read())
    handle.close()
    return contents
