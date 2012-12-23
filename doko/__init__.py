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

import CoreLocation

Location = namedtuple('Location', 'latitude longitude')

DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 10


class LocationServiceException(Exception):
    pass


def whereami(timeout=DEFAULT_TIMEOUT):
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


def _create_option_parser():
    usage = \
"""%prog [options]

Use CoreServices to find your current geolocation as latitude and longitude
coordinates. Exits with status code 1 on failure."""

    parser = optparse.OptionParser(usage)
    parser.add_option('--timeout', action='store', dest='timeout',
            type='float', default=10,
            help='Time to keep trying for if no location is found.')
    parser.add_option('--quiet', action='store_true', dest='quiet',
            help='Suppress any error messages.')

    return parser


def main():
    argv = sys.argv[1:]
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if args:
        parser.print_help()
        sys.exit(1)

    try:
        l = whereami(options.timeout)
        print ' '.join(map(str, l))
    except LocationServiceException, e:
        if not options.quiet:
            print >> sys.stderr, e.message
        sys.exit(1)
