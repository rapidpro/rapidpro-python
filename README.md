RapidPro Python Client
======================

Official Python client library for the [RapidPro](http://rapidpro.github.io/rapidpro/). 
Visit [here](http://rapidpro-python.readthedocs.org/) for complete documentation.

Example
-------

```python
from temba import TembaClient
client = TembaClient('rapidpro.io', 'your-api-token')
for contact in client.get_contacts():
    print contact.name
    
client.create_broadcast(text="Howdy", contacts=contacts[0:5])
```

If you don't know your API token then visit the [API Explorer](http://rapidpro.io/api/v1/explorer)
