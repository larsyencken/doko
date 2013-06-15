# -*- coding: utf-8 -*-
#
#  setup.py
#  doko
#

"""
Package information for doko package.
"""

from setuptools import setup

VERSION = '0.3.1'

requires = [
        'BeautifulSoup>=3.2.1',
        'requests>=0.14.0',
        'PyYAML>=3.10',
    ]

corelocation_requires = [
        'pyobjc>=2.4',
        'pyobjc-core>=2.4',
        'pyobjc-framework-CoreLocation>=2.4',
    ]

setup(
        name='doko',
        description="Detect your current location.",
        long_description=open('README.rst').read(),
        url="http://github.com/larsyencken/doko/",
        version=VERSION,
        author="Lars Yencken",
        author_email="lars@yencken.org",
        license="ISC",
        packages=[
            'doko',
        ],
        entry_points={
            'console_scripts': [
                    'doko = doko:main',
                    'doko-landmark = doko.landmark:main',
                ],
        },
        install_requires=requires,
        extras_require={
            'corelocation': corelocation_requires,
        }
    )
