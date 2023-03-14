RapidPro Python Client
======================

[![Build Status](https://github.com/rapidpro/rapidpro-python/workflows/CI/badge.svg)](https://github.com/rapidpro/rapidpro-python/actions?query=workflow%3ACI)
[![Coverage Status](https://codecov.io/gh/rapidpro/rapidpro-python/branch/main/graph/badge.svg)](https://codecov.io/gh/rapidpro/rapidpro-python) 
[![PyPI Release](https://img.shields.io/pypi/v/rapidpro-python.svg)](https://pypi.python.org/pypi/rapidpro-python/)

Official Python client library for the [RapidPro](http://rapidpro.github.io/rapidpro/). Supports latest Python 3.

Visit [here](http://rapidpro-python.readthedocs.org/) for complete documentation.

Installation
------------

```
pip install rapidpro-python
```

Example
-------

```python
from temba_client.v2 import TembaClient
client = TembaClient('rapidpro.io', 'your-api-token')
for contact_batch in client.get_contacts(group='Reporters').iterfetches(retry_on_rate_exceed=True):
    for contact in contact_batch:
        print(contact.name)
```

If you don't know your API token then visit the [API Explorer](http://app.rapidpro.io/api/v2/explorer)

Development
-----------

For discussions about future development, see the [RapidPro Developers Group](https://groups.google.com/forum/#!forum/rapidpro-dev).

To run the tests:

```
nose2 -C --coverage temba_client
```
