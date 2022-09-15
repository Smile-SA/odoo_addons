.. image:: https://img.shields.io/badge/licence-GPL--3-blue.svg
    :alt: License: GPL-3

Smile Base
=========================

* Install and make French the default language
* Activate access logs for ir.translation object
* Correct date and time format for French language
* Review the menu "Applications"
* Remove the menu "Update modules" from apps.openerp.com
* Add sequence and display window actions in IrValues
* Force to call unlink method at removal of remote object linked by a fields.many2one with ondelete='cascade'
* Add BaseModel.bulk_create, BaseModel.store_set_values and BaseModel._compute_store_set
* Improve BaseModel.load method performance
* Disable email sending/fetching by default
* Add a colored ribbon to make your environments recognisable at first glance


Usage
=====

Add this module to your addons, it will auto install.

To enable email sending, add in your configuration file :
::
  enable_email_sending = True

To enable email fetching, add in your configuration file :
::
  enable_email_fetching = True

To add a colored ribbon, definied with RGBa, add in your configuration file :
::
  server.environment = dev
  server.environment.ribbon_color = rgba(255, 0, 255, .6)


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_base%0Aversion:%209.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Maintainer
----------

This module is maintained by Smile SA.
