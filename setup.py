from os import path
from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import setup

here = path.abspath(path.dirname(__file__))
session = PipSession()
install_requires = [str(r.req) for r in parse_requirements('%s/requirements/base.txt' % here, session=session)]
tests_requires = [str(r.req) for r in parse_requirements('%s/requirements/tests.txt' % here, session=session)]

setup(
    name='rapidpro-python',
    version='1.3',
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
        'Programming Language :: Python :: 3',
    ],

    keywords='rapidpro client',
    packages=['temba'],
    install_requires=install_requires,

    test_suite='nose.collector',
    tests_require=tests_requires,
)
