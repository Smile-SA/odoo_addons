==============
Access Control
==============

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/12.0/smile_access_control
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

This module allows to manage users' rights using profiles.

Odoo's groups are a coherent set of rules that functionally consistent. Profiles allow you to combine several groups and effectively tailor users' access to each user.

Here an exemple :

* accounting group : create an invoice, modify an invoice, cancel an invoice
* business develloper group : create a lead, modify data of lead, close a deal

The CEO of an SME will probably belong to both groups. Profils allows to combine the both groups in one profil.

This is an alternative way to manage users rights by functional profiles.

Basically, a « profile » is a fictive user (res.users) tagged as a profile.

It means that like before (with the basic rules of Odoo),
you can add groups to your profile.

Features:

* You can associate a profile to created users.
* You can add users by profile.
* You can set fields to update for linked users.
* You have the choice to update or not in write mode for associated users,
  with field 'Update users' in profiles.

**Table of contents**

.. contents::
   :local:

Configuration
=============

To configure this module, you need to:

* Go to new menu **Settings > Users & Companies > User Profiles** and create the
  profiles you need.

Usage
=====

* Go to new menu **Settings > Users & Companies > Users** and create a new
  user, choose the profile and after saving you will have user access rights set.

Changelog
=========

**To test your profile, you need to set him as « active »,
which will be disabled afterwards at the next update.**

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_access_control%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Authors
~~~~~~~

* Smile SA

Contributors
~~~~~~~~~~~~

* Corentin Pouhet-Brunerie
* Matthieu Choplin

Maintainers
~~~~~~~~~~~

This module is maintained by the Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
