.. image:: https://img.shields.io/badge/licence-GPL--3-blue.svg
    :alt: License: GPL-3

Redis Session Store
===================

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
* `sentinel_pool`: list of sentinel nodes, a pair like `(hostname, port)`
* `master_name` (default: mymaster): Redis master name


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_redis_session_store%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Isabelle RICHARD <isabelle.richard@smile.fr>

Maintainer
----------

This module is maintained by Smile SA.
