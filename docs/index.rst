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

Alternatively you can create a client from the complete URL of the API root. You can use this if you need to connect to
a local RapidPro instance that doesn't use SSL. For example:

.. code-block:: python

    client = TembaClient('http://localhost:8000/api/v1', <YOUR-API-TOKEN>)

Fetching Single Objects
-----------------------

For each type, the client provides a method for fetching a single instance by it's unique identifier. For most types
this will be a UUID. However for broadcasts, messages and flow runs, this will be an integer, and for fields this will
be the key name.

If the requested object is not found, then a `TembaNoSuchObjectError` is raised.

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
    contacts = client.get_contacts(name="Bob")   # all contacts whose name contains Bob
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

The pager also allows you to specify a particular page to start at. For example:

.. code-block:: python

    pager = client.pager(start_page=2)
    contacts = client.get_contacts(name="Bob", pager=pager)  # the second page of contacts called Bob

.. note::
    Page numbers are one-based rather than zero-based for consistency with the RapidPro API.

.. warning::
    Fetching multiple objects may require multiple requests to the API. Care should be take to formulate queries which
    will match the same sequence of results, even if new objects are created between those API requests. For example,
    when querying for messages one could use the `before` argument with the current timestamp to ensure new messages
    aren't included.



Error Handling
--------------

If an API request causes a validation error in RapidPro, the client call will raise a `TembaAPIError` which will contain
the error messages for each field.

.. code-block:: python

    try:
        client.update_label('invalid-uuid', name="Test", parent_uuid=None)
    except TembaAPIError, ex:
        for field, field_errors = ex.errors.iteritems():
            for field_error in field_errors:
                # TODO do something with each error message

.. note::
    Field names for errors won't always match the names of the arguments passed to the client call.

If there was a connection problem then the client call will raise a `TembaConnectionError`.

See Also
==================

.. toctree::
   :maxdepth: 4

   temba

* :ref:`genindex`
* :ref:`search`

