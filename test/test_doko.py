import tempfile
from unittest import TestCase
import doko

class TestLocationPrecision(TestCase):
    def test_precision(self):
        l = doko.Location(123.4567, 123.4567, 'test')
        self.assertEqual(l.latitude, 123.4567)
        self.assertEqual(l.longitude, 123.4567)
        self.assertEqual(l.safe_latitude(), 123.4567)
        self.assertEqual(l.safe_longitude(), 123.4567)

        doko.Location.set_precision(2)

        self.assertEqual(l.safe_latitude(), 123.46)
        self.assertEqual(l.safe_longitude(), 123.46)

    def tearDown(self):
        doko.Location.set_precision(None)


class TestLocationStringRepresentation(TestCase):
    def setUp(self):
        doko.Location.set_precision(3)

    def test_raw(self):
        l = doko.Location(123.4567, 123.4567, 'test')
        self.assertEqual(l.raw(), "123.4567,123.4567")

    def test_repr(self):
        l = doko.Location(123.4567, 123.4567, 'test')
        self.assertEqual(repr(l),
                "Location(latitude=123.4567, longitude=123.4567, source='test')")

    def test_render(self):
        l = doko.Location(123.4567, 123.4567, 'test')
        self.assertEqual(l.render(), '123.457,123.457')

    def test_dump_and_load(self):
        tmpfile = tempfile.mkstemp()[1]
        l = doko.Location(123.4567, 123.4567, 'test')
        l.dump(tmpfile)

        new_l = doko.Location.load(tmpfile)
        self.assertEqual(new_l.source, "cache")
        self.assertEqual(new_l.latitude, l.safe_latitude())
        self.assertEqual(new_l.longitude, l.safe_longitude())

    def tearDown(self):
        doko.Location.set_precision(None)


class GeoIPStrategyTest(TestCase):
    def setUp(self):
        doko.Location.set_precision(3)

    def test_geoip(self):
        l = doko.geobytes_location(ip='8.8.8.8')
        self.assertEqual(l.safe_latitude(), 40.749)
        self.assertEqual(l.safe_longitude(), -73.985)
        self.assertEqual(l.strategy, 'geoip')
