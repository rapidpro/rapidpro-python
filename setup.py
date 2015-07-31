from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))


setup(
    name='rapidpro-python',
    version='1.1',
    description='Python client library for the RapidPro',
    url='https://github.com/rapidpro',

    author='Nyaruka',
    author_email='code@nyaruka.com',

    license='BSD',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='rapidpro client',
    packages=['temba'],
    install_requires=['pytz', 'requests', 'six'],

    test_suite='nose.collector',
    tests_require=['nose', 'mock', 'coverage'],
)
