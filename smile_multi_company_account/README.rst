=======================
Multi-company Invoicing
=======================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/12.0/smile_multi_company_account
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module depends on ``Multi-Company Base`` module parameters. It makes invoices attached to invoicing company. Instead of attaching the invoice natively to the connected user's company, it will be registered by the invoicing company carried by the record.

Features:

* Add a filter by invoicing company in invoices.
* Automatically set ``Is Invoicing Company`` to true if company is an invoicing company (has a Chart of Accounts).
* Make possible to validate an invoice for a company different from that of the connected user, and this invoice will be registered in account by attached company and not that of connected user.

**Table of contents**

.. contents::
   :local:

Usage
=====

#. Considering two companies ``YourCompany`` and ``A1``, knowing that ``YourCompany`` is a parent company of ``A1``. Both companies are invoicing companies:

    .. figure:: static/description/companies_list.png
       :alt: YourCompany company
       :width: 850px

    .. figure:: static/description/A1_company.png
       :alt: A1 company
       :width: 850px

#. Considering a user ``user01`` connected to ``YourCompany`` company and a second user ``user02`` connected to the child company ``A1``.

    .. figure:: static/description/user01_profile.png
       :alt: user01 profile
       :width: 850px

    .. figure:: static/description/user02_profile.png
           :alt: user02 profile
           :width: 850px

#. Even if the user ``user01`` has created the invoice attached to his company ``A1``, the user ``user02`` from the parent company can validate this invoice by keeping the company A1 already attached.

    .. figure:: static/description/create_validate_invoice.png
           :alt: Create and Validate Invoice
           :width: 850px

#. The invoice will be added to ``Journal Items`` with attached company ``A1`` and not the company of the connected user who validate it.

    .. figure:: static/description/Journal_Items.png
           :alt: Journal Items
           :width: 850px

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_multi_company_account%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Contributors
------------

* Corentin POUHET-BRUNERIE
* Majda EL MARIOULI

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
