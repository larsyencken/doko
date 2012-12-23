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

Using as a module
-----------------

::

  > import doko
  > doko.whereami()
  Location(latitude=35.674851, longitude=139.701419)


Using on the command-line
-------------------------

::

  $ doko
  35.674851 139.701419
