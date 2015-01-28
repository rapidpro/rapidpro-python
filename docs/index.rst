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


Reference:

.. toctree::
   :maxdepth: 4

   temba


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

