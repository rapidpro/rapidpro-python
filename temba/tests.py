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
            # check single contact response
            mock_get.return_value = MockResponse(200, self._read_json('contacts_1'))
            contact = self.client.get_contact('1234')

            self.assertEqual(contact.name, "John Smith")
            self.assertEqual(contact.uuid, "bfff9984-38f4-4e59-998d-3663ec3c650d")
            self.assertEqual(contact.modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

            # check multiple contact response
            mock_get.return_value = MockResponse(200, self._read_json('contacts_2'))

            self.assertRaises(TembaException, self.client.get_contact, '1234')

    @patch('requests.models.Response', MockResponse)
    def test_get_contacts(self):
        with patch('requests.get') as mock_get:
            # check multiple contact response
            mock_get.return_value = MockResponse(200, self._read_json('contacts_2'))
            contacts = self.client.get_contacts()

            self.assertEqual(len(contacts), 4)
            self.assertEqual(contacts[0].name, "John Smith")
            self.assertEqual(contacts[0].uuid, "bfff9984-38f4-4e59-998d-3663ec3c650d")
            self.assertEqual(contacts[0].modified_on, datetime.datetime(2014, 10, 1, 6, 54, 9, 817000, pytz.utc))

    @patch('requests.models.Response', MockResponse)
    def test_get_group(self):
        with patch('requests.get') as mock_get:
            # check single contact response
            mock_get.return_value = MockResponse(200, self._read_json('groups_1'))
            group = self.client.get_group('1234')

            self.assertEqual(group.name, "The A-Team")
            self.assertEqual(group.uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
            self.assertEqual(group.size, 4)

    @patch('requests.models.Response', MockResponse)
    def test_get_groups(self):
        with patch('requests.get') as mock_get:
            # check single contact response
            mock_get.return_value = MockResponse(200, self._read_json('groups_2'))
            groups = self.client.get_groups()

            self.assertEqual(len(groups), 2)
            self.assertEqual(groups[0].name, "The A-Team")
            self.assertEqual(groups[0].uuid, "04a4752b-0f49-480e-ae60-3a3f2bea485c")
            self.assertEqual(groups[0].size, 4)

    def _read_json(self, filename):
        handle = open('test_files/%s.json' % filename)
        contents = unicode(handle.read())
        handle.close()
        return contents


if __name__ == '__main__':
    unittest.main()
