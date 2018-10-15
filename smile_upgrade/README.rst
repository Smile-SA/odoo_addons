.. image:: https://img.shields.io/badge/licence-GPL--3-blue.svg
    :alt: License: GPL-3

================
Database Upgrade
================

This module helps you to upgrade automatically database
after code update and server restarting.

**Table of contents**

.. contents::
   :local:


Requirements
============

No requirement to use this module.


Usage
=====

Configuration
-------------

Upgrade tree view
^^^^^^^^^^^^^^^^^

Upgrades directory must be structured like this::

    project
    ├── upgrades
    |   ├── 1.1
    |   |   ├── __upgrade__.py
    |   |   ├── *.sql
    |   |   ├── *.yml  # only for post-load
    |   |   ├── *.csv  # only for post-load
    |   |   ├── *.xml  # only for post-load
    |   ├── 1.2
    |   |   ├── __upgrade__.py
    |   |   ├── *.sql
    |   ├── upgrade.conf

You can find an example of upgrade in `demo directory <smile_upgrade/demo>`_ of this module.

Configure the version
^^^^^^^^^^^^^^^^^^^^^

Fill the file *__upgrade__.py* with following options:

* `version`
* `databases`: let's empty if valid for all databases
* `translations_to_reload`: language codes list to reload in post-load
* `description`
* `modules_to_install_at_creation`: modules list to install at database creation
* `modules_to_upgrade`: modules list to update or install
* `pre-load`: list of .sql files
* `post-load`: list with .sql, .yml, .csv and .xml files
    * `.../filename` (depending on option `upgrades_path`) or
    * `module_name/.../filename`

Configure the version to load
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The upgrade version to load is set in file *upgrade.conf*, at the root of the *upgrades* directory, with this content (replace the version by your version number)::

        [options]
        version=1.2


Execute an upgrade
------------------

Odoo configuration
^^^^^^^^^^^^^^^^^^

Update your Odoo configuration file with the following options:

* `upgrades_path` (required): path to the upgrades directory
* `stop_after_upgrades` (default: False): stop server after upgrades if True

Execute upgrade
^^^^^^^^^^^^^^^

To execute an upgrade, you need to launch server with the following command::

    odoo.py -c <config_file> -d <db_name> --load=web,smile_upgrade


Additional features
-------------------

In `post-load`, you can replace filename string by tuple to specify error management.

Available options are:

* `raise` (default value): if an error is raised, stop upgrade execution by raising the error
* `rollback_and_continue`: if an error is raised, rollback to the savepoint set before the file execution and continue with the other files of the list
* `not_rollback_and_continue`: if an error is raised, no rollback is done and continue with the other files of the list

Example::

    'post-load': [
        ('post-load/fix_product_pricelist.yml', 'rollback_and_continue'),
    ],


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_upgrade%0Aversion:%211.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.


Credits
=======

Contributors
------------

* Corentin POUHET-BRUNERIE <corentin.pouhet-brunerie@smile.fr>

Maintainer
----------

This module is maintained by Smile SA.
