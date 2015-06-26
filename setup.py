#!/usr/bin/env python

from distutils.core import setup

setup(
    name='rapidpro-python',
    version='1.0',
    description='Python client library for the RapidPro',
    author='Nyaruka',
    url='https://github.com/rapidpro',
    packages=['temba'],
    install_requires=['pytz', 'requests'],
    test_suite='nose.collector',
    tests_require=['nose', 'mock'],
)