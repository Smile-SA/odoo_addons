=================
Discount Contract
=================
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/10.0/smile_discount_contract
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module offers the possibility to create and manage discount contracts .

Features:

* Creation of discount contract templates which can be used in different discount contracts.
* Possibility to add a parent template ( the parent template's rules will be added to the template rules ).
* Customization of discount rules ,products applied to ,type of contract ( sale ,purchase )...
* Auto-calculation of contract's end date depending on the start date and the number of months specified in the contract's template.
* auto-renew if the self-renewal checkbox is checked otherwise its manually updated by clicking on ``Update``.
* Computation of the due amount based on the customer invoices.
* Generation of refunds.


**Table of contents**

.. contents::
   :local:

Usage
=====

To create a new discount contract template:

#. Go to ``Accounting > Discounts > Discount contract templates`` menu .
#. Insert the template's  informations and rules to apply .

    .. figure:: static/description/discount_template_creation.png
       :alt: Discount contract template creation
       :width: 900px


   Rule creation :


    .. figure:: static/description/discount_rule_creation.png
       :alt: Discount rule creation
       :width: 900px


To create a new discount contract :

#. Go to ``Accounting > Discounts > Discount contracts`` menu .
#. Select the template to use and the partner .
#. Save and validate the contract .

    .. figure:: static/description/discount_contract_creation.png
       :alt: Discount contract creation
       :width: 900px


#. after the creation of a customer invoice ( the invoice date should be included in the discount contract period ) click on update .


    .. figure:: static/description/contract_updating.png
       :alt: Updating the contract
       :width: 900px


The due will be apdated .


    .. figure:: static/description/due_updating.png
       :alt: Due apdated
       :width: 900px


A Discount contract line will be generated.


    Click on the smart button ``Due`` .

    .. figure:: static/description/discount_contract_line_generation.png
       :alt: Discount contract line generation
       :width: 900px


Click on ``Generate refund`` button .


    .. figure:: static/description/refund_generated.png
       :alt: refund updated
       :width: 900px


A customer invoice will be generated

Click on the smart button ``Invoiced``.


    .. figure:: static/description/invoices_refund_generated.png
       :alt: Invoice generated
       :width: 900px



Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_discount_contract%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

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