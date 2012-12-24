# -*- coding: utf-8 -*-
#
#  setup.py
#  doko
#

"""
Package information for doko package.
"""

import sys
from setuptools import setup

VERSION = '0.1.0'

requires = [
        'BeautifulSoup==3.2.1',
        'requests==0.14.0',
]
if sys.platform == 'sys':
    for package in ('pyobjc==2.4', 'pyobjc-core==2.4', 'pyobjc-framework-CoreLocation==2.4'):
        requires.append(package)

setup(
        name='doko',
        description="Detect location using CoreLocation on OS X.",
        long_description=open('README.rst').read(),
        url="http://bitbucket.org/larsyencken/doko/",
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
                ],
        },
        install_requires=requires,
    )
