import codecs
import datetime
import json
import pytz
import requests
import unittest

from requests.structures import CaseInsensitiveDict
from . import __version__
from .clients import BaseClient
from .exceptions import TembaException, TembaSerializationException
from .serialization import TembaObject, SimpleField, BooleanField, IntegerField, DatetimeField, ObjectField
from .serialization import ObjectListField, ObjectDictField
from .utils import format_iso8601, parse_iso8601


class TembaTest(unittest.TestCase):
    """
    Base class for test cases
    """

    API_VERSION = None

    def read_json(self, filename, extract_result=None):
        """
        Loads JSON from the given test file
        """
        handle = codecs.open("test_files/v%d/%s.json" % (self.API_VERSION, filename), "r", "utf-8")
        contents = str(handle.read())
        handle.close()

        if extract_result is not None:
            contents = json.dumps(json.loads(contents)["results"][0])

        return contents

    def assertRaisesWithMessage(self, exc_class, message, callable_obj, *args, **kwargs):
        try:
            callable_obj(*args, **kwargs)
        except TembaException as exc:
            self.assertIsInstance(exc, exc_class)
            self.assertEqual(str(exc), message)

    def assertRequestURL(self, mock, method, url, **kwargs):
        """
        Asserts that a request was made to the given url with the given parameters
        """
        mock.assert_called_with(
            method,
            url,
            headers={
                "Content-type": "application/json",
                "Authorization": "Token 1234567890",
                "Accept": u"application/json",
                "User-Agent": "test/0.1 rapidpro-python/%s" % __version__,
            },
            verify=None,
            **kwargs
        )
        mock.reset_mock()

    def assertRequest(self, mock, method, endpoint, **kwargs):
        """
        Asserts that a request was made to the given endpoint with the given parameters
        """
        url = "https://example.com/api/v%d/%s.json" % (self.API_VERSION, endpoint)

        self.assertRequestURL(mock, method, url, **kwargs)


class UtilsTest(TembaTest):
    class TestTZ(datetime.tzinfo):
        def utcoffset(self, dt):
            return datetime.timedelta(hours=-5)

    def test_format_iso8601(self):
        d = datetime.datetime(2014, 1, 2, 3, 4, 5, 6, UtilsTest.TestTZ())
        self.assertEqual(format_iso8601(d), "2014-01-02T08:04:05.000006Z")
        # it should return None when no datetime given
        self.assertIs(format_iso8601(None), None)

    def test_parse_iso8601(self):
        dt = datetime.datetime(2014, 1, 2, 3, 4, 5, 0, pytz.UTC)
        self.assertEqual(parse_iso8601("2014-01-02T03:04:05.000000Z"), dt)
        self.assertEqual(parse_iso8601("2014-01-02T03:04:05.000000+00:00"), dt)
        self.assertEqual(parse_iso8601("2014-01-02T05:04:05.000000+02:00"), dt)
        self.assertEqual(parse_iso8601("2014-01-02T00:04:05.000000-03:00"), dt)
        self.assertEqual(parse_iso8601("2014-01-02T03:04:05.000000"), dt)
        self.assertEqual(parse_iso8601("2014-01-02T03:04:05"), dt)
        self.assertEqual(parse_iso8601(None), None)

        d = datetime.datetime(2014, 1, 2, 0, 0, 0, 0, pytz.UTC)
        self.assertEqual(parse_iso8601("2014-01-02"), d)


class TestSubType(TembaObject):
    zed = SimpleField()


class TestType(TembaObject):
    foo = SimpleField()
    bar = IntegerField()
    doh = DatetimeField()
    gem = ObjectField(item_class=TestSubType)
    hum = ObjectListField(item_class=TestSubType)
    meh = ObjectDictField(item_class=TestSubType)


class TembaSerializationExceptionTest(TembaTest):
    def test_str_works(self):
        err = TembaSerializationException("boop")
        self.assertEqual(str(err), "boop")


class FieldsTest(TembaTest):
    def test_boolean(self):
        field = BooleanField()
        self.assertEqual(field.serialize(True), True)
        self.assertEqual(field.serialize(None), None)

        self.assertEqual(field.deserialize(True), True)
        self.assertEqual(field.deserialize(False), False)
        self.assertEqual(field.deserialize(None), None)

        self.assertRaises(TembaSerializationException, field.deserialize, "")
        self.assertRaises(TembaSerializationException, field.deserialize, [])

    def test_integer(self):
        field = IntegerField()
        self.assertEqual(field.serialize(1), 1)
        self.assertEqual(field.serialize(None), None)

        self.assertEqual(field.deserialize(2), 2)
        self.assertEqual(field.deserialize(None), None)

        self.assertRaises(TembaSerializationException, field.deserialize, 1.5)
        self.assertRaises(TembaSerializationException, field.deserialize, "")
        self.assertRaises(TembaSerializationException, field.deserialize, [])

    def test_object_list(self):
        field = ObjectListField(item_class=TestSubType)
        self.assertEqual(
            field.serialize([TestSubType.create(zed="a"), TestSubType.create(zed=2)]), [{"zed": "a"}, {"zed": 2}]
        )

        self.assertRaises(TembaSerializationException, field.serialize, "Not a list")

        obj_list = field.deserialize([{"zed": "a"}, {"zed": 2}])
        self.assertEqual(len(obj_list), 2)
        self.assertEqual(obj_list[0].zed, "a")
        self.assertEqual(obj_list[1].zed, 2)

        self.assertRaises(TembaSerializationException, field.deserialize, None)
        self.assertRaises(TembaSerializationException, field.deserialize, "")

    def test_object_dict(self):
        field = ObjectDictField(item_class=TestSubType)
        self.assertEqual(
            field.serialize({"a": TestSubType.create(zed="c"), "b": TestSubType.create(zed=2)}),
            {"a": {"zed": "c"}, "b": {"zed": 2}},
        )

        self.assertRaises(TembaSerializationException, field.serialize, "Not a list")

        obj_dict = field.deserialize({"a": {"zed": "c"}, "b": {"zed": 2}})
        self.assertEqual(len(obj_dict), 2)
        self.assertEqual(obj_dict["a"].zed, "c")
        self.assertEqual(obj_dict["b"].zed, 2)

        self.assertRaises(TembaSerializationException, field.deserialize, None)
        self.assertRaises(TembaSerializationException, field.deserialize, "")


class TembaObjectTest(TembaTest):
    def test_create(self):
        # unspecified fields become None
        obj = TestType.create(foo="a", bar=123)
        self.assertEqual(obj.foo, "a")
        self.assertEqual(obj.bar, 123)
        self.assertEqual(obj.doh, None)
        self.assertEqual(obj.hum, None)

        # exception if field doesn't exist
        self.assertRaises(ValueError, TestType.create, foo="a", xyz="abc")

    def test_deserialize(self):
        obj = TestType.deserialize(
            {
                "foo": "a",
                "bar": 123,
                "doh": "2014-01-02T03:04:05",
                "gem": {"zed": "c"},
                "hum": [{"zed": "b"}],
                "meh": {"a": {"zed": "c"}, "b": {"zed": "d"}},
            }
        )
        self.assertEqual(obj.foo, "a")
        self.assertEqual(obj.bar, 123)
        self.assertEqual(obj.doh, datetime.datetime(2014, 1, 2, 3, 4, 5, 0, pytz.UTC))
        self.assertEqual(obj.gem.zed, "c")
        self.assertEqual(len(obj.hum), 1)
        self.assertEqual(obj.hum[0].zed, "b")
        self.assertEqual(len(obj.meh), 2)
        self.assertEqual(obj.meh["a"].zed, "c")
        self.assertEqual(obj.meh["b"].zed, "d")

        # exception when object list field receives non-list
        self.assertRaises(
            TembaSerializationException,
            TestType.deserialize,
            {"foo": "a", "bar": "x", "doh": "2014-01-02T03:04:05", "hum": {}},
        )

    def test_serialize(self):
        obj = TestType.create(
            foo="a",
            bar=123,
            doh=datetime.datetime(2014, 1, 2, 3, 4, 5, 0, pytz.UTC),
            gem=TestSubType.create(zed="a"),
            hum=[TestSubType.create(zed="b")],
            meh={"a": TestSubType.create(zed="c"), "b": TestSubType.create(zed="d")},
        )

        json_obj = obj.serialize()
        self.assertEqual(
            json_obj,
            {
                "foo": "a",
                "bar": 123,
                "doh": "2014-01-02T03:04:05.000000Z",
                "gem": {"zed": "a"},
                "hum": [{"zed": "b"}],
                "meh": {"a": {"zed": "c"}, "b": {"zed": "d"}},
            },
        )


class BaseClientTest(TembaTest):
    class Client(BaseClient):
        pass

    def test_init(self):
        # by host and token
        client = BaseClientTest.Client("example.com", "1234567890", user_agent="test/0.1", api_version=3)
        self.assertEqual(client.root_url, "https://example.com/api/v3")
        self.assertEqual(
            client.headers,
            {
                "Content-type": "application/json",
                "Accept": "application/json",
                "Authorization": "Token 1234567890",
                "User-Agent": "test/0.1 rapidpro-python/%s" % __version__,
            },
        )

        # by URL
        client = BaseClientTest.Client("http://example.com", "1234567890", 2)
        self.assertEqual(client.root_url, "http://example.com/api/v2")
        self.assertEqual(
            client.headers,
            {
                "Content-type": "application/json",
                "Accept": "application/json",
                "Authorization": "Token 1234567890",
                "User-Agent": "rapidpro-python/%s" % __version__,
            },
        )

        # by URL with trailing /
        client = BaseClientTest.Client("http://example.com/", "1234567890", 1)
        self.assertEqual(client.root_url, "http://example.com/api/v1")

        # verify_ssl parameter for requests
        client = BaseClientTest.Client("example.com", "1234567890", 2)
        self.assertEqual(client.verify_ssl, None)
        client = BaseClientTest.Client("example.com", "1234567890", 2, verify_ssl=False)
        self.assertFalse(client.verify_ssl)
        client = BaseClientTest.Client("example.com", "1234567890", 2, verify_ssl="/path/to/certfile")
        self.assertTrue(client.verify_ssl)
        self.assertEqual(client.verify_ssl, "/path/to/certfile")


# ====================================================================================
# Test utilities
# ====================================================================================


class MockResponse(object):
    """
    Mock response object with a status code and some content
    """

    def __init__(self, status_code, content=None, headers=None):
        self.status_code = status_code
        self.content = content or ""
        self.headers = CaseInsensitiveDict()

        if headers:
            self.headers.update(headers)

    def raise_for_status(self):
        http_error_msg = ""

        if 400 <= self.status_code < 500:
            http_error_msg = "%s Client Error: ..." % self.status_code

        elif 500 <= self.status_code < 600:
            http_error_msg = "%s Server Error: ..." % self.status_code

        if http_error_msg:
            raise requests.HTTPError(http_error_msg, response=self)

    def json(self, **kwargs):
        return json.loads(self.content)
