===================
Continuous Delivery
===================
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/10.0/smile_cd
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module allows to deploy Odoo applications thanks to Ansible.
It depends on smile_ci, the module of continuous integration: https://github.com/Smile-SA/odoo_addons/tree/10.0/smile_ci.

Features:

* Deploy Odoo on your hosts from tag or commit
* Configure your hosts as you want thanks to configurable Ansible inventory
* Plan deployments with automatic deployment rules
* Configure as many Ansible roles as you want (e.g. redis)


**Table of contents**

.. contents::
   :local:


Configuration
=============

* Configuration of the role to install and configure Odoo on your server  (`see configuration here <static/description/AnsibleOdoo.pdf>`_).
* Configuration of the role to upgrade Odoo on your server by using smile_upgrade and postgresql_db (`see here <static/description/AnsibleOdooDeploy.pdf>`_).


Usage
=====

#. Go to your branch, in the deployment tab add your environment configuration

#. Click on `Deploy` button to lunch deployment

#. Track your deployment from smart button or from the menu `Integration > Deployments`

    .. figure:: static/description/env_config.png
       :alt: Environment configuration
       :width: 850px


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_cd%0Aversion:%2010.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Author
------

* Smile SA

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