.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

====================
Logging in database
====================

This module is used to create, save and view logs in the database, for an action or actions that can be added to our module

Features :

1. Firstly :

* The Developer adds Smile Log to his model
* The Developer specifies the DB, model, res_id, uid, and the message to display

2. Secondly :

* The administrator does the action
* The administrator can see the logs saved in DB for the action

**Table of contents**

.. contents::
   :local:

Usage
=====
To add Smile Log to an action :

1. Import SmileDBLogger to inherited action (Ex. validate button of account.invoice) :

.. figure:: static/description/inherit_and_import_smile_log.png
   :alt: Import SmileDBLogger
   :width: 100%

2. Add the module to your depends in manifest :

.. figure:: static/description/manifest.png
   :alt: Depends manifest
   :width: 100%

3. Go click to your button action (button validate in our case)

.. figure:: static/description/button_validation.png
   :alt: Button validate
   :width: 100%

4. Go to ``Settings > Technical > Logging``> Logs menu.

.. figure:: static/description/logs.png
   :alt: Logs
   :width: 100%

But before all of this, make sure that "Smile Logs / users" box is already checked.

.. figure:: static/description/smile_logs_user.png
   :alt: Smile Logs
   :width: 100%

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_audit%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================
This addons does not collect any data and does not set any browser cookies.

Credits
=======

Authors
-------

Smile SA

Maintainer
----------
This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.

