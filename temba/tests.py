from __future__ import unicode_literals

import datetime
import json
import pytz
import unittest

from mock import patch
from . import TembaClient, TembaException


class MockResponse(object):

    def __init__(self, status_code, content=''):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("Server returned %s" % str(self.status_code))

    def json(self, **kwargs):
        return json.loads(self.content)


class TembaClientTest(unittest.TestCase):

    def setUp(self):
        self.client = TembaClient('example.com', '1234567890')

    @patch('requests.models.Response', MockResponse)
    def test_get_contact(self):
        with patch('requests.get') as mock_get:
            # check single item response
            mock_get.return_value = MockResponse(200, _read_json('contacts_1'))
            contact = self.client.get_contact('1234')

            self.assertEqual(contact.name, "John Smith")
            self.assertEqual(contact.uuid, "bfff9984-38f4-4e59-998d-3663ec3c650d")
            self.assertEqual(contact.modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

            # check multiple item response
            mock_get.return_value = MockResponse(200, _read_json('contacts_2'))
            self.assertRaises(TembaException, self.client.get_contact, '1234')

    @patch('requests.models.Response', MockResponse)
    def test_get_contacts(self):
        with patch('requests.get') as mock_get:
            # check multiple item response
            mock_get.return_value = MockResponse(200, _read_json('contacts_2'))
            contacts = self.client.get_contacts()
            self.assertEqual(len(contacts), 4)
            self.assertEqual(contacts[0].name, "John Smith")
            self.assertEqual(contacts[0].uuid, "bfff9984-38f4-4e59-998d-3663ec3c650d")
            self.assertEqual(contacts[0].modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

            # check multiple pages
            mock_get.side_effect = (MockResponse(200, _read_json('contacts_3_page_1')),
                                    MockResponse(200, _read_json('contacts_3_page_2')),
                                    MockResponse(200, _read_json('contacts_3_page_3')))
            contacts = self.client.get_contacts()
            self.assertEqual(len(contacts), 21)

            # check filtering by group_uuids
            mock_get.side_effect = [MockResponse(200, _read_json('contacts_2'))]
            self.client.get_contacts(group_uuids=["abc"])
            self.assert_request(mock_get, 'contacts', params={'group_uuids': ["abc"]})

    @patch('requests.models.Response', MockResponse)
    def test_get_group(self):
        with patch('requests.get') as mock_get:
            # check single item response
            mock_get.return_value = MockResponse(200, _read_json('groups_1'))
            group = self.client.get_group('1234')
            self.assertEqual(group.name, "The A-Team")
            self.assertEqual(group.uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
            self.assertEqual(group.size, 4)

            # check multiple item response
            mock_get.return_value = MockResponse(200, _read_json('groups_2'))
            self.assertRaises(TembaException, self.client.get_group, '1234')

    @patch('requests.models.Response', MockResponse)
    def test_get_groups(self):
        with patch('requests.get') as mock_get:
            # check no params
            mock_get.return_value = MockResponse(200, _read_json('groups_2'))
            groups = self.client.get_groups()

            self.assertEqual(len(groups), 2)
            self.assertEqual(groups[0].name, "The A-Team")
            self.assertEqual(groups[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
            self.assertEqual(groups[0].size, 4)

            # check filtering by name
            self.client.get_groups(name="A-Team")
            self.assert_request(mock_get, 'groups', params={'name': 'A-Team'})

    def assert_request(self, mock, endpoint, params):
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


if __name__ == '__main__':
    unittest.main()
