doko (どこ)
=========

A simple command-line utility (and module) to determine your current location.

Doki is a Python clone of Victor Jalencas's `whereami <https://github.com/victor/whereami>`_ utility, using CoreLocation services on OS X to determine your geographical coordinates. It requires OS X 10.6 (Mountain Lion) or later to function.

Kudos to `Rich Healey <https://github.com/richo/>`_ for getting me started.

Installing
----------

::

  $ pip install doko

Enabling Core Location
----------------------

On OS X 10.6 (Mountain Lion) or later, you can enable Core Location in System Preferences, in the "Security" or "Security & Privacy" section.

Using on the command-line
-------------------------

Using Core Services alone, you can just run the ``doko`` command::

  $ doko
  35.674851 139.701419

However, it relies on using wifi, and being enabled. If you won't have a wifi connection, you may see this::

  $ doko
  location could not be found -- is wifi enabled?

In this case, you can back off to a much more approximate service based on your external IP with the ``--approx`` command::

  $ doko --approx
  35.674 139.701

This may return the location for the center of the nearest city. To debug the location returned, the ``--show`` option will open a Google Maps browser window displaying the coordinates on a map.

Using as a module
-----------------

::

  > import doko
  > doko.location()
  Location(latitude=35.674851, longitude=139.701419)
  > doko.geobytes_location()  # approximate method
  Location(latitude=35.674, longitude=139.701)


Changelog
---------

0.1.0
~~~~~

- Fetch latitude and longitude using Core Location
- Provide backup method via GeoBytes page
