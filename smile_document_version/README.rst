.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/18.0/smile_document_version
    :alt: Smile-SA/odoo_addons

|badge1| |badge2|

==================
Smile Document Version
==================

This module adds versioning functionality to attachments in Odoo. Each time an attachment is updated, its version number is incremented automatically.

Features
========

- Automatic versioning of attachments.
- Version number starts at 1 for new attachments.
- Version is incremented each time the attachment content is updated.

.. contents:: Table of contents
   :local:

Usage
=====

1. When you create a new attachment, the **Version number** field is automatically set to `1`.

   .. image:: static/description/version_number.png
      :alt: Version number field
      :width: 850px

2. When you update the attachment content, the **Version number** field is incremented automatically.

   .. image:: static/description/increment_version_number.png
      :alt: Increment version number
      :width: 850px
Known issues
============

No known issues at the moment.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smash it by providing detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_document_version%0Aversion:%2018.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Contributors
------------

Smile SA Development Team

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.