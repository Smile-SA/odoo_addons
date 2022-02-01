.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/11.0/smile_api_rest
    :alt: Smile-SA/odoo_addons

|badge1| |badge2|

==============
Smile API Rest
==============

This module provisions you with an API which allows you to access models through HTTP requests.

Documentation generate with Swagger OpenAPI Specification - Version 2.0 (https://swagger.io/specification/v2/)

**Table of contents**

.. contents::
   :local:


Requirements
============

There are no requirements to use this module.


Usage
=====

Documentation URIs
------------------
============================================== ==============================================
URI                                            Description
============================================== ==============================================
`/<api-docs>/v<api_version>`                   API Documentation (generate with swagger)
`/<api-docs>/v<api_version>/swagger.json`      Json Swagger
============================================== ==============================================


API URIs
--------
============================================== ======= ===============================================================
URI                                            Method  Description
============================================== ======= ===============================================================
`/<api>/v<api_version>/<api_name>`             GET     Read all (with optional domain, fields, offset, limit, order)
`/api/v<api_version>/<api_name>/<id>`          GET     Read one (with optional fields)
`/api/v<api_version>/<api_name>`               POST    Create a record
`/api/v<api_version>/<api_name>/<id>`          PUT     Update a record
`/api/v<api_version>/<api_name>/<id>`          DELETE  Delete a record
`/api/v<api_version>/<api_name>/custom`        PUT     Call method (with optional parameters)
`/api/v<api_version>/<api_name>/custom/<id>`   PUT     Call method on record (with optional parameters)
============================================== ======= ===============================================================

Error response
--------------

.. code-block::

    {
        'code': <code>  # Error code,
        'error': <error>  # Error name,
        'description': <description>  # Description of the error,
    }

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_api_rest%0Aversion:%211.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.


Credits
=======

Contributors
------------

* Corentin POUHET-BRUNERIE
* Julien DRECQ

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.
