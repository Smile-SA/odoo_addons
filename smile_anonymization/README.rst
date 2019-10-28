======================
Database Anonymization
======================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/13.0/smile_anonymization
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module allows to anonymize automatically a database backup.
To do that, you need to define data mask on model fields in Python code or via UI.

**Table of contents**

.. contents::
   :local:

Usage
=====

| A data mask is a SQL statement, e.g.:
| ``'partner_' || id::text WHERE is_company IS NOT TRUE``

Add such a mask on the fields containing sensitive data:

* in Python code, e.g.: ``fields.Char(data_mask='NULL')``
* in UI via the menu *Settings > Technical > Database Structure > Fields*

The lock icon allows not to overload data mask at each module update if you defined it in Python code and modify via UI.

Add this module in *server_wide_modules* list in your config file or in the option *--load*.

Go to database manager and backup the desired database. You will download a anonymized backup.

Requirements
============

There are no requirements to use this module.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%smile_anonymization%0Aversion:%2013.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Smile SA

Contributors
~~~~~~~~~~~~

* Corentin Pouhet-Brunerie
* Ismail EL BAKKALI

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
