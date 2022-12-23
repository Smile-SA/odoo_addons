====================
Performance Analyzer
====================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/14.0/smile_perf_analyzer
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

Features :

This module log in function of logging rules:

* each JSON-RPC / XML-RPC call linked to a model:
  db, datetime, model, method, user, total time, db time, args, result
* Python method profiling
* SQL queries stats

A logging rule is defined directly via the user interface
(menu: Settings > Technical > Performance > Rules)
and it's applied without restarting Odoo server.

To hide the database _perf created during the installation :

* add "dbfilter = (?!.*_perf$)" in your config file.

The postgresql role used should be SUPERUSER, or the module installation will fail.

If the postgresql role cannot be SUPERUSER for security reasons :

- comment the last lines of the init method perf_log.py :
   cr.execute('DROP USER MAPPING IF EXISTS FOR %s SERVER perf_server' % db_user)

   cr.execute('CREATE USER MAPPING FOR %s SERVER perf_server OPTIONS (user %%s, password %%s)' % db_user, (db_user, db_password))

   cr.execute('DROP FOREIGN TABLE IF EXISTS %s' % (self._table,))

   cr.execute('CREATE FOREIGN TABLE %s (%s) SERVER perf_server' % (self._table, ', '.join('%s %s' % c for c in columns)))

- install the module :
- With a SUPERUSER role (if your postgres role name is not "odoo", modify it on the next SQL requests):
   GRANT USAGE ON FOREIGN SERVER perf_server TO odoo;
- With your odoo role (change password if needed):
   DROP USER MAPPING IF EXISTS FOR odoo SERVER perf_server;

   CREATE USER MAPPING FOR odoo SERVER perf_server OPTIONS (user 'odoo', password 'odoo');

   DROP FOREIGN TABLE IF EXISTS ir_logging_perf_log;

   CREATE FOREIGN TABLE ir_logging_perf_log (path VARCHAR, date timestamp, uid int4, model VARCHAR, method VARCHAR, total_time numeric, db_time numeric, db_count int4, args text, result text, error text, stats text, db_stats text, slow_queries text, slow_recomputation text, id int4) SERVER perf_server;


**Table of contents**

.. contents::
   :local:

Usage
=====
To create a rule :

1. Go to ``Settings > Technical > Performance> Rules`` menu :

* In this example we will create a rule for Administrator account in sale.order module :

 We specify :

  a. Methods,

  b. Slow RPC calls - Min. duration,

  c. Slow SQL requests - Min. duration,

  d. Slow field's recomputation - Min. duration

  e. Profile Python methods,

  f. Log SQL requests

.. figure:: static/description/rule_form.png
   :alt: rule form
   :width: 900 px

   We can make rules to monitor crons (all crons will be monitored ; there is actually no way to specify a specific one) :

   - path : ""

   - model : ir.cron

   - method : _callback

   Or button clicks (chose the right model and method) :

   - path : '/web/dataset/call_button'

   - model : ir.cron

   - method : method_direct_trigger


2. The rule will be added to the rules :

.. figure:: static/description/rules.png
   :alt: rules
   :width: 900 px

3. Then, when the Administrator executes one of the methods declared in the created rule, Performance Analyzer will record automatically :

* Date
* Method
* SQL requests time
* SQL requests count
* Total Time, etc

To show the Logs :

4. Go to ``Settings > Technical > Performance``> Logs menu :

.. figure:: static/description/logs.png
   :alt: logs
   :width: 900 px

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_perf_analyzer%0Aversion:%2014.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================
This addons does not collect any data and does not set any browser cookies.

Credits
=======

Authors
-------

Smile SA

Contributors
------------

* Corentin POUHET-BRUNERIE
* Wafaa JAOUAHAR

Maintainer
----------
This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: https://www.smile.eu

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.

