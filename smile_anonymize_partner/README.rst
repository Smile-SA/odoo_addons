========================
Smile Anonymize Partner
========================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
   :target: https://github.com/Smile-SA/odoo_addons/tree/12.0/smile_anonymize_partner
   :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module anonymize the personal data of partners.

**Table of contents**

.. contents::
  :local:

Usage
=====

* To change fields to anonymized you should surcharge method get_anonymize_fields() that return a dictionary with 3 keys: fields, phones and emails with a list of fields for each.
    Default values: {'fields': ['name', 'street', 'street2', 'comment'], 'phones': ['phone', 'mobile'], 'emails': ['email']}
* To anonymize personal data of your partners you should call action: action_anonymization(). This method display a popup with a warning that this action is irreversible and the Yes/Cancel buttons.
* When record is anonymized the boolean is_anonymized get as value True and the partner is archived (call method toggle_active()).

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

* Laila ERAMI
* Stéphanie MARCU

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
  :alt: Smile SA
  :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
