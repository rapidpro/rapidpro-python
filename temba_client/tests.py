from __future__ import absolute_import, unicode_literals

import datetime
import pytz
import unittest

from .exceptions import TembaException
from .serialization import TembaObject, SimpleField, IntegerField, DatetimeField, ObjectListField
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

    def test_serialize(self):
        obj = TestType.create(foo='a', bar=123, doh=datetime.datetime(2014, 1, 2, 3, 4, 5, 0, pytz.UTC),
                              hum=[TestSubType.create(zed='b')])

        json_obj = obj.serialize()
        self.assertEqual(json_obj, {'foo': 'a', 'bar': 123, 'doh': '2014-01-02T03:04:05.000000', 'hum': [{'zed': 'b'}]})
