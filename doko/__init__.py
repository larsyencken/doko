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
import time
from collections import namedtuple
from collections import OrderedDict
import webbrowser

try:
    import CoreLocation
except ImportError:
    # CoreLocation attempts will fail.
    CoreLocation = None

import requests
import BeautifulSoup


class Location(namedtuple('Location', 'latitude longitude')):
    precision = None

    @classmethod
    def set_precision(klass, digits):
        klass.precision = digits

    def safe_value(self, value):
        if self.precision:
            return round(value, self.precision)
        else:
            return value

    def safe_longitude(self):
        return self.safe_value(self.longitude)

    def safe_latitude(self):
        return self.safe_value(self.latitude)

    def __repr__(self):
        return "%s,%s" % (self.safe_latitude(), self.safe_longitude())

DEFAULT_TIMEOUT = 3
DEFAULT_RETRIES = 10

LOCATION_STRATEGIES = OrderedDict()

CACHE_FILE = os.path.expanduser("~/.doko_cache")


# Important, define strategies in default resolution order
def location_strategy(name):
    def _(fn):
        LOCATION_STRATEGIES[name] = fn
    return _


class LocationServiceException(Exception):
    pass

def write_to_cache(location):
    with open(CACHE_FILE, 'w') as fh:
        fh.write("%f %s" % (time.time(), location))

@location_strategy("cache")
def cache_location(timeout=DEFAULT_TIMEOUT):
    """
    Fetch and return current location from a filebacked cache, stored in ~/.doko_cache

    Cache is considered value for up to 30 minutes, but refreshed each time it is queried
    """
    thirty_mins = (60 * 30)
    try:
        cache = open(CACHE_FILE).read().strip()
        timestamp, loc = cache.split(" ")
        if float(timestamp) + thirty_mins > time.time():
            lat, lon = loc.split(",")
            return Location(lat, lon)
    except IOError:
        # No cache file, but raising would fail without --force
        return None
    except ValueError:
        # Invalid content in cache file. Nuke it and start over
        os.unlink(cache_file)
        return None

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
        for i in xrange(DEFAULT_RETRIES):
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
        return Location(c.latitude, c.longitude)


@location_strategy("geoip")
def geobytes_location(timeout=DEFAULT_TIMEOUT):
    external_ip = requests.get('http://jsonip.com/').json['ip']
    try:
        resp = requests.post(
                'http://www.geobytes.com/iplocator.htm?getlocation',
                data={'ipaddress': external_ip},
                timeout=timeout,
            )
    except requests.exceptions.Timeout:
        raise LocationServiceException('timeout fetching geoip location')
    try:
        s = BeautifulSoup.BeautifulSoup(resp.content)
        latitude = float(s.find(
                'td',
                text='Latitude',
            ).parent.findNext('input')['value'])
        longitude = float(s.find(
                'td', text='Longitude'
            ).parent.findNext('input')['value'])
    except Exception:
        raise LocationServiceException('error parsing geobytes page')

    return Location(latitude, longitude)


def location(strategy=None, timeout=DEFAULT_TIMEOUT, force=False):
    """
    Detect your current location using one the available strategies. If you
    provide one by name, we use that. If force is True, back off to secondary
    strategies on failure.
    """
    if not strategy:
        strategy = LOCATION_STRATEGIES.keys()[0]

    l = None
    last_error = None

    remaining_strategies = LOCATION_STRATEGIES.copy()
    strategy_f = remaining_strategies.pop(strategy)

    try:
        l = strategy_f(timeout)
    except LocationServiceException, e:
        if not force:
            raise
        last_error = e.message

    if not l:
        for _, strategy in LOCATION_STRATEGIES:
            try:
                l = strategy()
            except LocationServiceException, e:
                last_error = e.message

    if not l:
        raise LocationServiceException(last_error)

    write_to_cache(l)

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
            help='Continue trying strategies if the first should fail')
    parser.add_option('--strategy', action='store', dest='strategy',
            help='Strategy for location lookup (corelocation|geoip)')
    parser.add_option('--precision', action='store', dest='precision',
            type=int,
            help='Store geodata with <precision> significant digits')
    parser.add_option('--cache', action='store_true', dest='cache',
            help='Consult a filebacked cache for up to 30 mins')

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
            Location.set_precision(os.getenv("DOKO_PRECISION"))
        except ValueError:
            raise "Invalid value in DOKO_PRECISION"

    if options.precision:
        Location.set_precision(options.precision)

    if not (os.getenv("DOKO_CACHE") or options.cache):
        del LOCATION_STRATEGIES['cache']

    try:
        l = location(options.strategy, timeout=options.timeout,
                force=options.force)
    except LocationServiceException, e:
        if not options.quiet:
            print >> sys.stderr, e.message
        sys.exit(1)

    print l

    if options.show:
        webbrowser.open(
                'https://maps.google.com/?q=%s' % str(l)
            )
main()
