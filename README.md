RapidPro Python Client
======================

Beginnings of a simple Python client library for the RapidPro API

Usage
-----

If you don't know your API token then visit the [API Explorer](http://rapidpro.io/api/v1/explorer)

```python
from temba import TembaClient
client = TembaClient('rapidpro.io', <YOUR-API-TOKEN>)
print client.get_contacts()
```
