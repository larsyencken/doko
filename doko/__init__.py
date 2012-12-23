# -*- coding: utf-8 -*-
#
#  whereami.py
#  whereami
#

"""
Use the Core Location framework.
"""

import sys
import optparse
import time
from collections import namedtuple
import webbrowser

import CoreLocation
import requests
import BeautifulSoup

Location = namedtuple('Location', 'latitude longitude')

DEFAULT_TIMEOUT = 3
DEFAULT_RETRIES = 10


class LocationServiceException(Exception):
    pass


def location(timeout=DEFAULT_TIMEOUT):
    """
    Fetch and return a Location from OS X Core Location, or throw
    a LocationServiceException trying.
    """
    m = CoreLocation.CLLocationManager.new()

    if not m.locationServicesEnabled():
        raise LocationServiceException(
                'location services not enabled -- check privacy settings in System Preferences'  # noqa
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


def geobytes_location():
    external_ip = requests.get('http://jsonip.com/').json['ip']
    resp = requests.post(
            'http://www.geobytes.com/iplocator.htm?getlocation',
            data={'ipaddress': external_ip},
        )
    try:
        s = BeautifulSoup.BeautifulSoup(resp.content)
        latitude = float(s.find('td',
            text='Latitude').parent.findNext('input')['value'])
        longitude = float(s.find('td',
            text='Longitude').parent.findNext('input')['value'])
    except Exception:
        raise LocationServiceException('error parsing geobytes page')

    return Location(latitude, longitude)


def _create_option_parser():
    usage = \
"""%prog [options]

Use CoreServices to find your current geolocation as latitude and longitude
coordinates. Exits with status code 1 on failure."""

    parser = optparse.OptionParser(usage)
    parser.add_option('--timeout', action='store', dest='timeout',
            type='float', default=DEFAULT_TIMEOUT,
            help='Time to keep trying for if no location is found.')
    parser.add_option('--quiet', action='store_true', dest='quiet',
            help='Suppress any error messages.')
    parser.add_option('--show', action='store_true',
            help='Show result on Google Maps in a browser.')
    parser.add_option('--approx', action='store_true',
            help='Use a GeoIP service if Core Location fails.')

    return parser


def main():
    argv = sys.argv[1:]
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if args:
        parser.print_help()
        sys.exit(1)

    l = None
    error = None
    try:
        l = location(options.timeout)
    except LocationServiceException, e:
        error = e.message

    if not l and options.approx:
        try:
            l = geobytes_location()
        except LocationServiceException, e:
            error = e.message

    if not l:
        if not options.quiet:
            print >> sys.stderr, error
        sys.exit(1)

    print ' '.join(map(str, l))

    if options.show:
        webbrowser.open(
                'https://maps.google.com/?q=%s+%s' % l
            )
