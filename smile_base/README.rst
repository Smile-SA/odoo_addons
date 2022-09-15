==========
Smile Base
==========

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
   :target: https://github.com/Smile-SA/odoo_addons/tree/11.0/smile_base
   :alt: Smile-SA/odoo_addons

|badge2| |badge3|

* Install and make French the default language
* Activate access logs for ir.translation object
* Correct date and time format for French language
* Review the menu "Applications"
* Remove the menu "Update modules" from apps.odoo.com
* Add sequence and display window actions in IrValues
* Force to call unlink method at removal of remote object linked by a fields.many2one with ondelete='cascade'
* Add BaseModel.bulk_create, BaseModel.store_set_values and BaseModel._compute_store_set
* Improve BaseModel.load method performance
* Disable email sending/fetching by default
* Add a colored ribbon to make your environments recognisable at first glance

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

To add a colored ribbon, definied with RGBa, add in your configuration file:
    * server.environment = dev
    * server.environment.ribbon_color = rgba(255, 0, 255, .6)

To display database name inside the colored ribbon add in your configuration file:
    * server.environment.display_dbname_in_ribbon = True


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_base%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Authors
~~~~~~~

* Smile SA

Contributors
~~~~~~~~~~~~

* Corentin Pouhet-Brunerie

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
  :alt: Smile SA
  :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
