.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/18.0/smile_ux_feedback
    :alt: Smile-SA/odoo_addons

|badge1| |badge2|

==================
Smile UX Feedback
==================

The ``ux_feedback`` module is designed to collect user feedback on various aspects of the Odoo back office. It provides an easy-to-use interface for users to submit their performance, conformity, satisfaction ratings, and additional feedback.

.. contents:: Table of contents
   :local:

Features
========

- Icon integration: A thumbs-up icon ``<i class="fa fa-thumbs-up"></i>`` is displayed on each page of the back office.
- Feedback pop-up: Users can input their feedback through a modal that collects:

  - Performance (Many2one)
  - Conformity (Many2one)
  - Satisfaction (Many2one)
  - Feedback (free text)

- Pre-filled fields:

  - User
  - Timestamp
  - URL (with the name of the concerned view)

Installation
===========

1. Clone the repository or download the module files.
2. Place the ``ux_feedback`` directory in your Odoo addons path.
3. Update the app list in Odoo.
4. Install the ``ux_feedback`` module from the Odoo apps interface.

Usage
=====

Once installed, the thumbs-up icon will appear on every page of the back office. Clicking the icon will open a pop-up modal where users can provide their feedback. All submitted feedback will be stored and can be reviewed by administrators.

How to make a Feedback
----------------------

1. Go to the page where you want to make a feedback
2. On the top right of the Odoo back-office click on the "thums-up icon"

   .. image:: static/description/feedback_icon.png
      :alt: Thumbs-up icon in Odoo

3. A popup is displayed, here you can rate the page you're in with differents criterias:

   * **Performance**: Performant / Fairly Performant / Not Very Performant / Not Performant
   * **Completion**: Compliant / Fairly Compliant / Not Very Compliant / Not Compliant
   * **Satisfaction**: Satisfactory / Fairly Satisfactory / Not Very Satisfactory / Not Satisfactory
   * **Feedback**: Text field to write your feedback

   .. image:: static/description/feedback_popup.png
      :alt: Feedback popup in odoo

4. Click on the "Submit Button" Your feedback is now submitted

How to view all the feedbacks
-----------------------------

As an administrator

1. Go to the "UX tracker" app

   .. image:: static/description/ux_tracker_app.png
      :alt: UX tracker app in odoo

2. On this page you can see all the feedbacks that have been done

   .. image:: static/description/feedbacks.png
      :alt: Feedbacks app in odoo

Contributing
===========

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

Bug Tracker
==========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_ux_feedback%0Aversion:%218.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Contributors
-----------

* Smile
* SALIM Abdessamad
* AFMIR Mohammed

Maintainer
---------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.
