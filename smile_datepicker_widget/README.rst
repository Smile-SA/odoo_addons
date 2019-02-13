=================
Datepicker Widget
=================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/11.0/smile_widget_datepicker
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|


This module allows configuring a datepicker popup's default date to depends
on another date's value.
For example , if you have a start date and an end date (fields types can be
date or datetime), you can force end date's datepicker popup default date
to be equals to start date + 1 day.

**Table of contents**

.. contents::
   :local:


Usage
=====

In the end date field's options (the field that you want to depend on
an another datefield) add:

.. code-block:: xml

    <field name="end_date" options="{'datepicker_start_date':'name of start date's field','datepicker_step': 3}"/>


Where ``name of start date's field`` is the name of the field you want to be
followed and ``3`` (optional, by default datepicker_step = 1 ) represents
the difference (number of days) between start date and the end date's
datepicker popup default date.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and
welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_widget_datepicker%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical
issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Contributors
------------

* Timothée BANCKAERT
* Wafaa JAOUAHAR

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert
in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
