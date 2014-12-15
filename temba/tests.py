from __future__ import unicode_literals

import datetime
import json
import pytz
import unittest

from mock import patch
from . import TembaClient, TembaException


class MockResponse(object):
    """
    Mock HTTP response with a status code and some content
    """
    def __init__(self, status_code, content=''):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("Server returned %d" % self.status_code)

    def json(self, **kwargs):
        return json.loads(self.content)


class TembaClientTest(unittest.TestCase):

    @patch('requests.models.Response', MockResponse)
    def setUp(self):
        self.client = TembaClient('example.com', '1234567890')

    def test_get_contact(self):
        with patch('requests.get') as mock_get:
            # check single item response
            mock_get.return_value = MockResponse(200, _read_json('contacts_single'))
            contact = self.client.get_contact('bfff9984-38f4-4e59-998d-3663ec3c650d')

            self.assertEqual(contact.uuid, 'bfff9984-38f4-4e59-998d-3663ec3c650d')
            self.assertEqual(contact.name, "John Smith")
            self.assertEqual(contact.urns, ['tel:+250700000001'])
            self.assertEqual(contact.group_uuids, ['04a4752b-0f49-480e-ae60-3a3f2bea485c'])
            self.assertEqual(contact.fields, {'nickname': 'Hannibal'})
            self.assertEqual(contact.language, None)
            self.assertEqual(contact.modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

            # check multiple item response
            mock_get.return_value = MockResponse(200, _read_json('contacts_multiple'))
            self.assertRaises(TembaException, self.client.get_contact, 'bfff9984-38f4-4e59-998d-3663ec3c650d')

    def test_get_contacts(self):
        with patch('requests.get') as mock_get:
            # check no params
            mock_get.return_value = MockResponse(200, _read_json('contacts_multiple'))
            contacts = self.client.get_contacts()
            self.assertEqual(len(contacts), 4)
            self.assertEqual(contacts[0].uuid, "bfff9984-38f4-4e59-998d-3663ec3c650d")

            # check filtering by group_uuids
            mock_get.return_value = MockResponse(200, _read_json('contacts_multiple'))
            self.client.get_contacts(group_uuids=["abc"])
            self.assert_request(mock_get, 'contacts', params={'group_uuids': ["abc"]})

            # check multiple pages
            mock_get.side_effect = (MockResponse(200, _read_json('contacts_multipage_1')),
                                    MockResponse(200, _read_json('contacts_multipage_2')),
                                    MockResponse(200, _read_json('contacts_multipage_3')))
            contacts = self.client.get_contacts()
            self.assertEqual(len(contacts), 21)

    def test_get_flow(self):
        with patch('requests.get') as mock_get:
            # check single item response
            mock_get.return_value = MockResponse(200, _read_json('flows_single'))
            flow = self.client.get_flow('a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')
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

            # check multiple item response
            mock_get.return_value = MockResponse(200, _read_json('flows_multiple'))
            self.assertRaises(TembaException, self.client.get_flow, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')

    def test_get_flows(self):
        with patch('requests.get') as mock_get:
            # check no params
            mock_get.return_value = MockResponse(200, _read_json('flows_multiple'))
            flows = self.client.get_flows()
            self.assertEqual(len(flows), 2)
            self.assertEqual(flows[0].uuid, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')

    def test_get_group(self):
        with patch('requests.get') as mock_get:
            # check single item response
            mock_get.return_value = MockResponse(200, _read_json('groups_single'))
            group = self.client.get_group('04a4752b-0f49-480e-ae60-3a3f2bea485c')
            self.assertEqual(group.uuid, '04a4752b-0f49-480e-ae60-3a3f2bea485c')
            self.assertEqual(group.name, "The A-Team")
            self.assertEqual(group.size, 4)

            # check multiple item response
            mock_get.return_value = MockResponse(200, _read_json('groups_multiple'))
            self.assertRaises(TembaException, self.client.get_group, '04a4752b-0f49-480e-ae60-3a3f2bea485c')

    def test_get_groups(self):
        with patch('requests.get') as mock_get:
            # check no params
            mock_get.return_value = MockResponse(200, _read_json('groups_multiple'))
            groups = self.client.get_groups()
            self.assertEqual(len(groups), 2)
            self.assertEqual(groups[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")

            # check filtering by name
            self.client.get_groups(name="A-Team")
            self.assert_request(mock_get, 'groups', params={'name': 'A-Team'})

    def test_get_run(self):
        with patch('requests.get') as mock_get:
            # check single item response
            mock_get.return_value = MockResponse(200, _read_json('runs_single'))
            run = self.client.get_run('9ec96b73-78c3-4029-ba86-5279c92996fc')
            self.assertEqual(run.uuid, '9ec96b73-78c3-4029-ba86-5279c92996fc')
            self.assertEqual(run.flow_uuid, 'a68567fa-ad95-45fc-b5f7-3ce90ebbd46d')
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

            # check multiple item response
            mock_get.return_value = MockResponse(200, _read_json('groups_multiple'))
            self.assertRaises(TembaException, self.client.get_group, '9ec96b73-78c3-4029-ba86-5279c92996fc')

    def test_get_messages(self):
        with patch('requests.get') as mock_get:
            # check no params
            mock_get.return_value = MockResponse(200, _read_json('messages_multiple'))
            messages = self.client.get_messages()
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0].text, "Hello \u0633.")

    def assert_request(self, mock, endpoint, params):
        """
        Asserts that a request was made to the given endpoint with the given parameters
        """
        mock.assert_called_with('https://example.com/api/v1/%s.json' % endpoint,
                                headers={'Content-type': 'application/json',
                                         'Authorization': 'Token 1234567890',
                                         'Accept': u'application/json'},
                                params=params)


def _read_json(filename):
    handle = open('test_files/%s.json' % filename)
    contents = unicode(handle.read())
    handle.close()
    return contents
