==========
Smile Base
==========

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
   :target: https://github.com/Smile-SA/odoo_addons/tree/17.0/smile_base
   :alt: Smile-SA/odoo_addons

|badge2| |badge3|

* Make French the default language if installed
* Correct date and time format for French language
* Review the menu "Applications"
* Remove the menu "App store" and "Update modules" from apps.odoo.com.
* Add sequence and display window actions in IrValues
* Force to call unlink method at removal of remote object linked by a fields.many2one with ondelete='cascade'
* Add BaseModel.store_set_values and BaseModel._compute_store_set
* Improve BaseModel.load method performance
* Disable email sending/fetching by default
* Replace email_to in emails by email_to in configuration file
* add a recompute_fields method that can be called via webservices

**Table of contents**

.. contents::
  :local:

Usage
=====

Add this module to your addons, it will auto install.

To enable email sending, add in your configuration file:
    * enable_email_sending = True

To enable email fetching, add in your configuration file:
    * enable_email_fetching = True

Changes done at migration
=========================

The feature adding a colored ribbon to make your environments recognisable at
first glance was removed during migration to Odoo 16.0.
We recommand to instead install modules `web_environment_ribbon <https://github.com/OCA/web/tree/16.0/web_environment_ribbon>`_ and `server_environment_ir_config_parameter <https://github.com/OCA/server-env/tree/16.0/server_environment_ir_config_parameter>`_.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_base%0Aversion:%2016.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

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

* Corentin Pouhet-Brunerie
* Majda EL MARIOULI

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
  :alt: Smile SA
  :target: https://www.smile.eu

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
