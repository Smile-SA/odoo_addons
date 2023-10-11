.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/16.0/smile_module_auto_update
    :alt: Smile-SA/odoo_addons

.. |badge3| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta

|badge1| |badge2| |badge3|

==================
Module Auto Update
==================

This module helps you automatically upgrade modules changed since last
server restarting.

As the module is based on module
`smile_upgrade <https://apps.odoo.com/apps/modules/16.0/smile_upgrade>`_,
you can continue to use upgrades to execute `pre-load` and `post-load` scripts,
but filling the `modules_to_upgrade` list is not useful anymore.

**Table of contents**

.. contents::
   :local:


Requirements
============

Please add modules
`module_auto_update <https://apps.odoo.com/apps/modules/16.0/module_auto_update/>`_
and `smile_upgrade <https://apps.odoo.com/apps/modules/16.0/smile_upgrade>`_
inside your addons path.

Usage
=====

Install the module, change source code of some modules, restart your Odoo instance and
your modules will automatically will be updated.

Please consult dependency modules documentation for more information about them.



Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_module_auto_update%0Aversion:%216.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.


Credits
=======

Contributors
------------

* Isabelle RICHARD

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.
