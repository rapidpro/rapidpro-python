from __future__ import unicode_literals

import datetime
import json
import pytz
import requests
import unittest

from mock import patch
from . import TembaClient, TembaException, TembaType, Group


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


@patch('requests.request')
@patch('requests.models.Response', MockResponse)
class TembaClientTest(unittest.TestCase):

    def setUp(self):
        self.client = TembaClient('example.com', '1234567890')

    def test_create_broadcast(self, mock_request):
        # check by group UUID
        mock_request.return_value = MockResponse(200, _read_json('broadcast_created'))
        broadcast = self.client.create_broadcast("Howdy", groups=['04a4752b-0f49-480e-ae60-3a3f2bea485c'])

        expected_body = json.dumps({'text': "Howdy", 'groups': ['04a4752b-0f49-480e-ae60-3a3f2bea485c']})
        self.assert_request(mock_request, 'post', 'broadcasts', data=expected_body)

        self.assertEqual(broadcast.id, 234252)
        self.assertEqual(broadcast.urns, [1234])
        self.assertEqual(broadcast.contacts, [])
        self.assertEqual(broadcast.groups, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])
        self.assertEqual(broadcast.text, "Howdy")
        self.assertEqual(len(broadcast.messages), 3)
        self.assertEqual(broadcast.status, 'Q')
        self.assertEqual(broadcast.created_on, datetime.datetime(2014, 12, 12, 22, 56, 58, 917000, pytz.utc))

    def test_create_contact(self, mock_request):
        mock_request.return_value = MockResponse(200, _read_json('contacts_created'))
        contact = self.client.create_contact("Amy Amanda Allen", ['tel:+250700000005'],
                                             {'nickname': "Triple A"}, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])

        expected_body = json.dumps({'name': "Amy Amanda Allen",
                                    'urns': ['tel:+250700000005'],
                                    'fields': {'nickname': "Triple A"},
                                    'group_uuids': ['04a4752b-0f49-480e-ae60-3a3f2bea485c']})
        self.assert_request(mock_request, 'post', 'contacts', data=expected_body)

        self.assertEqual(contact.uuid, 'bfff9984-38f4-4e59-998d-3663ec3c650d')
        self.assertEqual(contact.name, "Amy Amanda Allen")
        self.assertEqual(contact.urns, ['tel:+250700000005'])
        self.assertEqual(contact.groups, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])
        self.assertEqual(contact.fields, {'nickname': 'Triple A'})
        self.assertEqual(contact.language, None)
        self.assertEqual(contact.modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

    def test_delete_contact(self, mock_request):
        # check deleting an existing contact
        mock_request.return_value = MockResponse(204, '')
        self.client.delete_contact('bfff9984-38f4-4e59-998d-3663ec3c650d')

        self.assert_request(mock_request, 'delete', 'contacts', params={'uuid': 'bfff9984-38f4-4e59-998d-3663ec3c650d'})

        # check deleting a non-existent contact
        mock_request.return_value = MockResponse(404, 'NOT FOUND')
        self.assertRaises(TembaException, self.client.delete_contact, 'bfff9984-38f4-4e59-998d-3663ec3c650d')

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

        self.assert_request(mock_request, 'get', 'contacts', params={'group_uuids': ["abc"]})

        # check filtering by group object
        group1 = Group.create(name="A-Team", uuid='xyz', size=4)
        mock_request.return_value = MockResponse(200, _read_json('contacts_multiple'))
        self.client.get_contacts(groups=[group1])

        self.assert_request(mock_request, 'get', 'contacts', params={'group_uuids': ["xyz"]})

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
        self.assertEqual(flow.rulesets[0].node, 'e16ff762-6051-4940-964a-9b2efcb670ca')
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

        # check by contact
        self.client.get_messages(contact='123')
        self.assert_request(mock_request, 'get', 'messages', params={'contact': '123'})

    def test_get_run(self, mock_request):
        # check single item response
        mock_request.return_value = MockResponse(200, _read_json('runs_single'))
        run = self.client.get_run(123)

        self.assert_request(mock_request, 'get', 'runs', params={'run': 123})

        self.assertEqual(run.uuid, '9ec96b73-78c3-4029-ba86-5279c92996fc')
        self.assertEqual(run.flow, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')
        self.assertEqual(run.contact, '3597f744-fc7a-4709-9cb4-4db24c484f45')
        self.assertEqual(len(run.steps), 1)
        self.assertEqual(run.steps[0].node, 'e16ff762-6051-4940-964a-9b2efcb670ca')
        self.assertEqual(run.steps[0].text, "ping one")
        self.assertEqual(run.steps[0].value, "ping one")
        self.assertEqual(run.steps[0].type, "R")
        self.assertEqual(run.steps[0].arrived_on, datetime.datetime(2014, 12, 12, 22, 34, 36, 978000, pytz.utc))
        self.assertEqual(run.steps[0].left_on, None)
        self.assertEqual(len(run.values), 1)
        self.assertEqual(run.values[0].category, "All Responses")
        self.assertEqual(run.values[0].node, 'e16ff762-6051-4940-964a-9b2efcb670ca')
        self.assertEqual(run.values[0].text, "ping one")
        self.assertEqual(run.values[0].rule_value, "ping one")
        self.assertEqual(run.values[0].value, "ping one")
        self.assertEqual(run.values[0].label, "Response 1")
        self.assertEqual(run.values[0].time, datetime.datetime(2014, 12, 12, 22, 34, 36, 978000, pytz.utc))
        self.assertEqual(run.created_on, datetime.datetime(2014, 12, 12, 22, 56, 58, 917000, pytz.utc))

        # check empty response
        mock_request.return_value = MockResponse(200, _read_json('empty'))
        self.assertRaises(TembaException, self.client.get_run, 'xyz')

        # check multiple item response
        mock_request.return_value = MockResponse(200, _read_json('groups_multiple'))
        self.assertRaises(TembaException, self.client.get_group, '9ec96b73-78c3-4029-ba86-5279c92996fc')

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


class TembaTypeTest(unittest.TestCase):
    class TestType(TembaType):
        class Meta:
            fields = ('foo', 'bar')
            datetime_fields = ('bar',)

    def test_create(self):
        obj = TembaTypeTest.TestType.create(foo=123, bar="abc")
        self.assertEqual(obj.foo, 123)
        self.assertEqual(obj.bar, "abc")
        obj = TembaTypeTest.TestType.create(foo=123)
        self.assertEqual(obj.foo, 123)
        self.assertIsNone(obj.bar)

        self.assertRaises(ValueError, TembaTypeTest.TestType.create, foo=123, xyz="abc")


def _read_json(filename):
    handle = open('test_files/%s.json' % filename)
    contents = unicode(handle.read())
    handle.close()
    return contents
