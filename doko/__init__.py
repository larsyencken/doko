# -*- coding: utf-8 -*-
#
#  whereami.py
#  whereami
#

"""
Use the Core Location framework.
"""

import os
import sys
import time
import optparse
from optparse import OptionValueError
from collections import namedtuple
from collections import OrderedDict
import webbrowser

import requests
from geoip2.database import Reader

try:
    import CoreLocation
except ImportError:
    # CoreLocation attempts will fail.
    CoreLocation = None

import doko.landmark

DEFAULT_TIMEOUT = 3
DEFAULT_RETRIES = 10

LOCATION_STRATEGIES = OrderedDict()

CACHE_FILE = os.path.expanduser("~/.doko_cache")


class Location(namedtuple('Location', 'latitude longitude source')):
    precision = None

    @classmethod
    def set_precision(cls, digits):
        cls.precision = digits

    def safe_value(self, value):
        if self.precision:
            return round(value, self.precision)
        else:
            return value

    def safe_longitude(self):
        return self.safe_value(self.longitude)

    def safe_latitude(self):
        return self.safe_value(self.latitude)

    def raw(self):
        return "%s,%s" % (self.latitude, self.longitude)

    def render(self):
        return "%s,%s" % (self.safe_latitude(), self.safe_longitude())

    def __repr__(self):
        return 'Location(latitude=%s, longitude=%s, source=%s)' % (
            self.latitude,
            self.longitude,
            repr(self.source),
        )

    def dump(self, filename):
        with open(filename, 'w') as ostream:
            ostream.write('%s,%s' % (self.render(), self.source))

    @classmethod
    def load(cls, filename):
        with open(filename, 'r') as istream:
            cache = istream.read().strip()
            lat, lon, source = cache.split(",")
            return cls(float(lat), float(lon), 'cache')


# Important, define strategies in default resolution order
def location_strategy(name):
    def _(fn):
        LOCATION_STRATEGIES[name] = fn
        return fn
    return _


class LocationServiceException(Exception):
    def __init__(self, message):
        self.message = message


if 'DOKO_LANDMARK' in os.environ:
    @location_strategy("landmark")
    def landmark_location(**kwargs):
        name = os.environ['DOKO_LANDMARK']
        with doko.landmark.LandmarkStore() as s:
            if name in s:
                lat, lon = s[name]
                return Location(lat, lon, 'landmark')

        raise LocationServiceException('unknown landmark %s' % name)


@location_strategy("cache")
def cache_location(timeout=DEFAULT_TIMEOUT):
    """
    Fetch and return current location from a filebacked cache, stored in
    ~/.doko_cache

    Cache is considered value for up to 30 minutes, but refreshed each time
    it is queried
    """
    thirty_mins = (60 * 30)
    if not os.path.exists(CACHE_FILE):
        return

    last_updated = os.stat(CACHE_FILE).st_mtime
    if last_updated + thirty_mins < time.time():
        return

    try:
        l = Location.load(CACHE_FILE)
    except ValueError:
        # Invalid content in cache file. Nuke it and start over
        os.unlink(CACHE_FILE)
        return

    return l

if CoreLocation:
    @location_strategy("corelocation")
    def corelocation_location(timeout=DEFAULT_TIMEOUT):
        """
        Fetch and return a Location from OS X Core Location, or throw
        a LocationServiceException trying.
        """

        m = CoreLocation.CLLocationManager.new()

        if not m.locationServicesEnabled():
            raise LocationServiceException(
                'location services not enabled -- check privacy settings in System Preferences'  # nopep8
            )

        if not m.locationServicesAvailable():
            raise LocationServiceException('location services not available')

        m.startUpdatingLocation()
        CoreLocation.CFRunLoopStop(CoreLocation.CFRunLoopGetCurrent())
        l = m.location()

        # retry up to ten times, possibly sleeping between tries
        for i in range(DEFAULT_RETRIES):
            if l:
                break

            time.sleep(float(timeout) / DEFAULT_RETRIES)
            CoreLocation.CFRunLoopStop(CoreLocation.CFRunLoopGetCurrent())
            l = m.location()

        if not l:
            raise LocationServiceException(
                'location could not be found -- is wifi enabled?'
            )

        c = l.coordinate()
        return Location(c.latitude, c.longitude, 'corelocation')


@location_strategy("geoip")
def geoip_location(ip=None, timeout=DEFAULT_TIMEOUT):
    geoip_file = os.environ.get('GEOIP2_FILE')

    if not geoip_file or not os.path.exists(geoip_file):
        raise LocationServiceException(
            'no valid GEOIP2_FILE set -- please download and decompress: '
            'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz'  # noqa
        )

    if not ip:
        try:
            xff = requests.get('http://jsonip.com/').json()['ip']
            ip = xff.split(', ')[-1]
        except Exception:
            raise LocationServiceException(
                'error getting an ip -- are you online?'
            )

    reader = Reader(geoip_file)

    rec = reader.omni(ip)
    if not rec.location:
        raise LocationServiceException(
            'unable to geocode ip address ({0})'.format(ip)
        )

    loc = rec.location

    return Location(loc.latitude, loc.longitude, 'geoip')


def location(strategy=None, timeout=DEFAULT_TIMEOUT, force=False):
    """
    Detect your current location using one the available strategies. If you
    provide one by name, we use that. If force is True, back off to secondary
    strategies on failure.
    """
    if not strategy:
        strategy = next(iter(LOCATION_STRATEGIES.keys()))

    l = None
    last_error = None

    remaining_strategies = LOCATION_STRATEGIES.copy()
    strategy_f = remaining_strategies.pop(strategy)

    try:
        l = strategy_f(timeout=timeout)
    except LocationServiceException as e:
        if not force:
            raise
        last_error = e.message

    if not l:
        for strategy_f in remaining_strategies.values():
            try:
                l = strategy_f()
            except LocationServiceException as e:
                last_error = e.message

    if not l:
        raise LocationServiceException(last_error)

    # success!
    l.dump(CACHE_FILE)

    return l


def _create_option_parser():
    usage = \
"""%prog [options]

Use CoreServices to find your current geolocation as latitude and longitude
coordinates. Exits with status code 1 on failure."""  # nopep8

    parser = optparse.OptionParser(usage)
    parser.add_option('--timeout', action='store', type='float',
                      default=DEFAULT_TIMEOUT,
                      help='Time to keep trying for if no location is found.')
    parser.add_option('--quiet', action='store_true',
                      help='Suppress any error messages.')
    parser.add_option('--show', action='store_true',
                      help='Show result on Google Maps in a browser.')
    parser.add_option('-f', '--force', action='store_true', dest='force',
                      help='Continue trying strategies if the first should'
                      ' fail')
    parser.add_option('--strategy', action='store', dest='strategy',
                      help='Strategy for location lookup '
                      '(corelocation|geoip)')
    parser.add_option('--precision', action='store', dest='precision',
                      type=int, help='Store geodata with <precision> '
                      'significant digits')
    parser.add_option('--cache', action='store_true', dest='cache',
                      help='Consult a filebacked cache for up to 30 mins')
    parser.add_option('--show-strategy', action='store_true',
                      help='Include the strategy which succeeded in the '
                      'output')
    parser.add_option('--remember', action='store', dest='remember',
                      help='Remember this location as <landmark>')

    return parser


def main():
    argv = sys.argv[1:]
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if args:
        parser.print_help()
        sys.exit(1)

    if options.strategy and options.strategy not in LOCATION_STRATEGIES:
        raise OptionValueError("%s is not a valid strategy" % options.strategy)

    if os.getenv("DOKO_PRECISION"):
        try:
            Location.set_precision(int(os.getenv("DOKO_PRECISION")))
        except ValueError:
            raise "Invalid value in DOKO_PRECISION"

    if options.precision:
        Location.set_precision(options.precision)

    if not (os.getenv("DOKO_CACHE") or options.cache):
        del LOCATION_STRATEGIES['cache']
    else:
        print('Using cache')

    try:
        l = location(options.strategy, timeout=options.timeout,
                     force=options.force)
    except LocationServiceException as e:
        if not options.quiet:
            print(e.message, file=sys.stderr)
        sys.exit(1)

    if options.show_strategy:
        print(l.render(), '(%s)' % l.source)
    else:
        print(l.render())

    if options.remember:
        doko.landmark.add_landmark(options.remember, l.latitude, l.longitude)

    if options.show:
        webbrowser.open(
            'https://maps.google.com/?q=%s,%s' % (
                l.safe_latitude(),
                l.safe_longitude(),
            )
        )
