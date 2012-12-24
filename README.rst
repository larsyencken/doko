doko (どこ)
===========

A simple command-line utility (and Python module) to determine your current location.

Doko is a clone of Victor Jalencas's `whereami <https://github.com/victor/whereami>`_ utility, but unlike whereami it supports multiple strategies for finding your location.

Kudos to `Richo Healey <https://github.com/richo/>`_ for ideas and patches.

Installing
----------

To install just GeoIP support, run::

  $ pip install doko

However, on OS X 10.6 (Mountain Lion) or later, you can also use the much more accurate Core Location framework::

  $ pip install doko[corelocation]

Using Core Location
-------------------

Once you've installed the corelocation-enabled doko package, you'll need to enable Core Location in System Preferences, in the "Security" or "Security & Privacy" section. Furthermore, you must be using Wifi for it to work.

Hacking
-------

For hacking on OSX, you will likely want to install ``requires-corelocation.txt`` as well as ``requires.txt``.

Using on the command-line
-------------------------

Just run the ``doko`` command::

  $ doko
  35.674,139.701

This will give its best guess as to your location, depending on the strategies that are available. Use the ``--show`` option to open the location in Google Maps.

More fine-grained control over strategies used and the precision returned is available. See ``doko --help``.

Using as a module
-----------------

::

  > import doko
  > doko.location('geoip')  # on any platform
  35.674,139.701
  > doko.location('corelocation')  # on OS X, using Core Location
  35.674851,139.701419
  > doko.Location.set_precision(2)
  > doko.location()
  35.67,139.70


Changelog
---------

0.2.0
~~~~~

- Make doko multiplatform, by making Core Location optional
- Honour timeouts for GeoIP lookups
- Provide control over precision to support privacy

0.1.0
~~~~~

- Fetch latitude and longitude using Core Location
- Provide backup method via GeoBytes page
