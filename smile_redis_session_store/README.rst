.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/12.0/smile_redis_session_store
    :alt: Smile-SA/odoo_addons

|badge1| |badge2|


Redis Session Store
===================

This module allows you to use a Redis database to manage sessions,
instead of classic filesystem storage.

Redis is an open source, in-memory data structure store, used as a database, cache and message broker.

It is useful for load balancing because session's directory may not be shared.

Requirements
============

You need to install and to start a Redis server to use this module.
Documentation is available on `Redis website`_.

You need to install package `redis`::

    pip3 install redis

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


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_redis_session_store%0Aversion:%212.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Isabelle RICHARD

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.
