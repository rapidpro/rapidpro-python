from __future__ import absolute_import, unicode_literals

import codecs
import datetime
import json
import pytz
import requests
import six
import unittest

from . import __version__
from .clients import BaseClient
from .exceptions import TembaSerializationException
from .serialization import TembaObject, SimpleField, BooleanField, IntegerField, DatetimeField, ObjectListField
from .utils import format_iso8601, parse_iso8601


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


class FieldsTest(unittest.TestCase):
    def test_boolean(self):
        field = BooleanField()
        self.assertEqual(field.serialize(True), True)
        self.assertEqual(field.deserialize(True), True)
        self.assertEqual(field.deserialize(False), False)
        self.assertRaises(TembaSerializationException, field.deserialize, "")
        self.assertRaises(TembaSerializationException, field.deserialize, [])


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
        self.assertRaises(TembaSerializationException, TestType.deserialize,
                          {'foo': 'a', 'bar': 'x', 'doh': '2014-01-02T03:04:05', 'hum': []})

        # exception when object list field receives non-list
        self.assertRaises(TembaSerializationException, TestType.deserialize,
                          {'foo': 'a', 'bar': 'x', 'doh': '2014-01-02T03:04:05', 'hum': {}})

    def test_serialize(self):
        obj = TestType.create(foo='a', bar=123, doh=datetime.datetime(2014, 1, 2, 3, 4, 5, 0, pytz.UTC),
                              hum=[TestSubType.create(zed='b')])

        json_obj = obj.serialize()
        self.assertEqual(json_obj, {'foo': 'a', 'bar': 123, 'doh': '2014-01-02T03:04:05.000000', 'hum': [{'zed': 'b'}]})


class BaseClientTest(unittest.TestCase):
    class Client(BaseClient):
        pass

    def test_init(self):
        # by host and token
        client = BaseClientTest.Client('example.com', '1234567890', user_agent='test/0.1', api_version=3)
        self.assertEqual(client.root_url, 'https://example.com/api/v3')
        self.assertEqual(client.headers, {'Content-type': 'application/json',
                                          'Accept': 'application/json',
                                          'Authorization': 'Token 1234567890',
                                          'User-Agent': 'test/0.1 rapidpro-python/%s' % __version__})

        # by URL
        client = BaseClientTest.Client('http://example.com/api/v1', '1234567890')
        self.assertEqual(client.root_url, 'http://example.com/api/v1')
        self.assertEqual(client.headers, {'Content-type': 'application/json',
                                          'Accept': 'application/json',
                                          'Authorization': 'Token 1234567890',
                                          'User-Agent': 'rapidpro-python/%s' % __version__})

        # by URL with trailing /
        client = BaseClientTest.Client('http://example.com/api/v1/', '1234567890')
        self.assertEqual(client.root_url, 'http://example.com/api/v1')


# ====================================================================================
# Test utilities
# ====================================================================================

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


def read_json(filename):
    """
    Test utility method to load JSON from the given test file
    """
    handle = codecs.open('test_files/%s.json' % filename, 'r', 'utf-8')
    contents = six.text_type(handle.read())
    handle.close()
    return contents
