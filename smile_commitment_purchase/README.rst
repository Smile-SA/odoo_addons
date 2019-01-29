===================
Purchase Commitment
===================

.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/12.0/smile_commitment_purchase
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module generates analytic lines at purchase confirmation / cancellation.

You can follow-up purchase commitment per budget line.

**Table of contents**

.. contents::
   :local:

Requirements
============

This module depends on
`smile_commitment_base <https://github.com/Smile-SA/odoo_addons/tree/12.0/smile_commitment_base>`_
.


Usage
=====

* Define a budgetary position listening to general accounts.

* Define a budget with budgetary position and analytic account.

* Commitment amount is 0.

* Purchase a product on the selected account, associate the analytic account on the purchase line.

* Confirming the purchase triggers the verification of:

  * Available amount, then block the processing if order amount is superior
  * Limit buget of the user confirming the order, then block the processing if order amount is superior

* Return to your budget to see the new commitment amount.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_commitment_purchase%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Authors
~~~~~~~

* Smile SA

Contributors
~~~~~~~~~~~~

* Corentin Pouhet-Brunerie
* Isabelle RICHARD
* Wafaa JAOUAHAR

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
