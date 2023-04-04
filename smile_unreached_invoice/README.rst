=========================
Account Unreached Invoice
=========================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
   :target: https://github.com/Smile-SA/odoo_addons/tree/16.0/smile_anonymize_partner
   :alt: Smile-SA/odoo_addons

|badge2| |badge3|


This module provides a wizard to generate account moves for unreached purchase order lines.

SmileUnreachedInvoice
---------------------

This wizard inherits from the ``smile.account.invoice.generic.wizard.abstract`` model.

The following fields are available:

- ``accounting_date``: Date used as the accounting date for the generated account moves.
- ``account_credit_id``: Account to credit for the generated account moves.
- ``account_debit_id``: Account to debit for the generated account moves (optional).
- ``journal_id``: Journal to use for the generated account moves.
- ``reversal_date``: Date used as the reversal date for the generated account moves.
- ``purchase_ids``: Purchase orders related to the unreached invoice.

Methods
-------

The ``SmileUnreachedInvoice`` wizard defines the following methods:

- ``default_get``: Override of the method to set the default value of the ``purchase_ids`` field according to the context.
- ``_get_order_lines``: Method to retrieve the purchase order lines related to the unreached invoice.
- ``generate``: Method to generate the account moves.

Views
-----

The module defines a form view for the ``SmileUnreachedInvoice`` wizard:

- ``smile_unreached_invoice_form_view``: The form view that displays the fields of the wizard and two buttons to generate or cancel the account moves.

Actions
-------

The module defines an action to open the wizard:

- ``account_unreached_invoice_act_window``: The action to open the ``SmileUnreachedInvoice`` wizard from a purchase order form view.

Security
--------

The action to open the wizard is only available to users who belong to the "Accounting & Finance" group.


Authors
~~~~~~~

* Smile SA

Contributors
~~~~~~~~~~~~

* Elian NICAISE

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
  :alt: Smile SA
  :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
