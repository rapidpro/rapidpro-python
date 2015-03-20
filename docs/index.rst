.. temba documentation master file, created by
   sphinx-quickstart on Wed Jan 28 13:37:50 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to rapidpro-python's documentation!
===========================================

This is the official Python client library for `RapidPro <http://rapidpro.github.io/rapidpro/>`_.

To create a :class:`temba.TembaClient` instance, you need to know the name of the host server, and your API token.
If you don't know your API token then visit the `API Explorer <http://rapidpro.io/api/v1/explorer>`_. For example:

.. code-block:: python

    from temba import TembaClient
    client = TembaClient('rapidpro.io', <YOUR-API-TOKEN>)


Fetching Single Objects
-----------------------

For each type, the client provides a method for fetching a single instance by it's unique identifier. For most types
this will be a UUID. However for broadcasts, messages and flow runs, this will be an integer, and for fields this will
be the key name.

If the requested object is not found, then an exception is raised.

.. code-block:: python

    contact = client.get_contact('cc276708-7752-4b52-a4ea-d3264847220e')
    message = client.get_message(12345)
    field = client.get_field('age')

Fetching Multiple Objects
-------------------------

For each type, the client provides a method for fetching multiple instances, which can be used to fetch results
with or without paging. For example the following method calls don't use paging and so return all results available from
the API, making as many requests as required:

.. code-block:: python

    contacts = client.get_contacts()             # all contacts
    contacts = client.get_contacts(name="Bob")   # all contacts whose name contains "Bob"
    contacts = client.get_contacts(uuids=[...])  # contacts whose UUID is listed

Obviously such calls have the potential to return very large numbers of results and so should be used with caution.
Alternatively the same results can be fetched with paging. For example the following code downloads all matching
contacts one page at a time:

.. code-block:: python

    pager = client.pager()
    while True:
        contacts = client.get_contacts(name="Bob", pager=pager)

        # do something with this page of contacts...

        if not pager.has_more()
            break

.. warning::
    Fetching multiple objects may require multiple requests to the API. Care should be take to formulate queries which
    will match the same sequence of results, even if new objects are created between those API requests. For example,
    when querying for messages one could use the `before` argument with the current timestamp to ensure new messages
    aren't included.

Reference:

.. toctree::
   :maxdepth: 4

   temba


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

