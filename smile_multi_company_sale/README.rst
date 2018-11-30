==================
Multi-company Sale
==================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/11.0/smile_multi_company_sale
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module makes sales management attached to invoicing company..

Features:

* Attach sales order to invoicing companies.
* Force the income and taxes corresponding to selected invoicing company when creating the invoice order.

**Table of contents**

.. contents::
   :local:

Usage
=====

Connect to your invoicing company to create a sale order:

.. figure:: static/description/create_sale_order.png
   :alt: Sale Order Creation
   :width: 850px

Create an invoice, the system will pass the company id in the context of the invoice:

.. figure:: static/description/create_invoice_for_SO.png
   :alt: Create invoice for sale order
   :width: 850px

.. figure:: static/description/income_account_filtered.png
   :alt: Income Account Filtered
   :width: 850px

.. figure:: static/description/customer_taxes_filtered.png
   :alt: Customer Taxes Filtered
   :width: 850px


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_multi_company_sale%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Contributors
------------

* Corentin POUHET-BRUNERIE

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
