# -*- coding: utf-8 -*-
#
#  landmark.py
#  doko
#

"""
A set of known places you're interested in storing.
"""

import os
import sys
import optparse
import yaml
from contextlib import contextmanager


LANDMARK_FILE = os.path.expanduser('~/.doko_landmarks')


@contextmanager
def LandmarkStore(landmark_file=LANDMARK_FILE):
    s = _LandmarkStore(landmark_file)
    yield s
    s.close()


class _LandmarkStore(object):
    def __init__(self, landmark_file):
        self._filename = landmark_file
        self._places = {}
        if os.path.exists(self._filename):
            with open(self._filename) as istream:
                self._places.update(yaml.load(istream))

        self._dirty = False

    def __getitem__(self, k):
        return self._places[k]

    def __contains__(self, k):
        return k in self._places

    def __iter__(self):
        return iter(self._places)

    def __delitem__(self, k):
        if k in self._places:
            del self._places[k]
            self._dirty = True

    def add_landmark(self, name, lat, lon):
        self._places[name] = [lat, lon]
        self._dirty = True

    def close(self):
        if self._dirty:
            with open(self._filename, 'w') as ostream:
                yaml.safe_dump(self._places, ostream)
        self._dirty = False

    def __del__(self):
        self.close()


def add_landmark(name, lat, lon):
    with LandmarkStore() as s:
        s.add_landmark(name, lat, lon)


def list_landmarks():
    with LandmarkStore() as s:
        for name in sorted(s):
            print name, s[name]


def del_landmark(name):
    with LandmarkStore() as s:
        del s[name]


def _create_option_parser():
    usage = \
"""%prog --add name lat lon
       %prog --del name
       %prog --list

Manage a database of known places."""

    parser = optparse.OptionParser(usage)
    parser.add_option('--add', action='store_true', dest='add_landmark',
            help='Add a new landmark')
    parser.add_option('--del', action='store_true', dest='del_landmark',
            help='Delete an existing landmark')
    parser.add_option('--list', action='store_true', dest='list_landmarks',
            help='List all existing landmarks')

    return parser


def main():
    argv = sys.argv[1:2]
    parser = _create_option_parser()
    options = parser.parse_args(argv)[0]
    args = sys.argv[2:]

    if options.list_landmarks and len(args) == 0:
        return list_landmarks()

    if options.add_landmark and len(args) == 3:
        name, lat, lon = args
        try:
            lat, lon = map(float, (lat, lon))
            return add_landmark(name, lat, lon)

        except ValueError:
            pass

    if options.del_landmark and len(args) == 1:
        name, = args
        return del_landmark(name)

    parser.print_help()
    sys.exit(1)
