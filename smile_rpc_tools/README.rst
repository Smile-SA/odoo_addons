===========================
Smile RPC Tools
===========================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
   :target: https://github.com/Smile-SA/odoo_addons/tree/13.0/smile_base
   :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module aims to gather various methods that would improve RPC calls performance or functionalities.

**Table of contents**

.. contents::
  :local:

Usage
=====

**Nested_read**

This method allows you to improve performances during json_rpc reading process, when you need to read information
on related sub fields.

We extended base.model with a new method : *nested_read*. With this method, you are allowed to add not only
the standard fields of the current object, but also fields of the nested records, with a single call.

There are two main advantages with using this method:

- Code visibility and simplycity: Instead of multiplying your rpc calls in you code, or having to handle parrallel calls, you simply need to do a call with a json definition of the fields you wish to read.
- Perfomance: When doing complex read calls, fetching data on many related models, you probably need to do several calls one after the other (this is reinforced if you were not parrallelysing your calls). That means that your time complexity before obtaining all your data is `nbrOfCalls * RoundTimeTripToServer`. With this method, you only do one call, substancially reducing the impact of the network.

Since we only use in this method the orm read method, security and rights properties are conserved

Example : Get sale.order fields (name, customer[name], total_amount) and sale.order.line fields (product_id[name], product_uom_qty)

*With old method (read)* :

* First call on sale.order ID, to get : [name, partner_id, total_amount, order_line]
* Second call (with partner_id of the previous call), on res.partner, to get : [name]
* Third call (with a loop on the first call's order_line result), on sale.order.line : [product_id, product_uom_qty]
* Last call (with product_id of the previous call), on product.product : [name]

*With new method (nested_read)* :

Simply use a dictonary structure in the json_call on the sale.order model :

    {
        'fields': [
            'name',
            'amount_total'
        ],
        'partner_id': {
            'fields': [
                'name'
            ]
        },
        'order_line': {
            'fields': [
                'product_uom_qty'
            ],
            'product_id': {
                'fields' : [
                    'name'
                ]
            }
        }
    }

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_base%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Authors
~~~~~~~

* Smile SA

Contributors
~~~~~~~~~~~~

* Robin Delaye

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
  :alt: Smile SA
  :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
