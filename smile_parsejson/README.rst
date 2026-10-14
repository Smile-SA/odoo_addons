.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/18.0/smile_parsejson
    :alt: Smile-SA/odoo_addons

|badge1| |badge2|

==================
Smile Parse JSON
==================

This module provides a mixin class to simplify JSON parsing in Odoo models. It allows developers to extract nested JSON elements dynamically and handle complex JSON structures with ease.

.. contents:: Table of contents
   :local:

Usage
=====

To use this module, follow these steps:

1. Inherit the `parse_json.mixin` class in your custom model.

2. Store the JSON data in the `json_element` field.

3. Use the `json_get` method to extract values from the JSON structure by providing a list of keys or properties.

Example
-------

Given the following JSON structure:

.. code-block:: json

    {
        "id": 147,
        "idItem": 128161,
        "host": "APITUDE",
        "property": {
            "HS_AFI_H_4864843": {
                "id": 15392205,
                "name": "Regency Hotel Miami",
                "syscode": "HS_AFI_H_4864843"
            }
        }
    }

Calling `json_get(['property', '_first_child', 'name'])` will return `"Regency Hotel Miami"`.

Known issues
============

- The `json_element` field uses `eval` to parse JSON data, which can be a security risk if the input is not sanitized. Ensure that the JSON data is trusted before using this method.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smash it by providing detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_parsejson%0Aversion:%2018.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Contributors
------------

- Smile SA Development Team

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.