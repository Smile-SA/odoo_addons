===================
Redis Session Store
===================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/10.0/smile_redis_session_store
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module allows you to use a Redis database to manage sessions,
instead of classic filesystem storage.


Requirements
============

You need to install and to start a Redis server to use this module.
Documentation is available on `Redis website`_.

You need to install package `redis`::

    pip install redis

.. _`Redis website`: http://redis.io/topics/quickstart


Usage
=====

To use Redis, install this module and please add `enable_redis = True` option
in configuration file.

Available options
-----------------

* `redis_host` (default: localhost): Redis host
* `redis_port` (default: 6379): Redis port
* `redis_dbindex` (default: 1): Redis database index
* `redis_pass` (default: None): Redis password
* `redis_socket` (default: None) :  unix socket path

If `redis_socket` is used, both `redis_host` and `redis_port` should be None.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_redis_session_store%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Contributors
------------

* Isabelle RICHARD

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
