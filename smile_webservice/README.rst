.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/18.0/smile_webservice
    :alt: Smile-SA/odoo_addons

|badge1| |badge2|

==================
Smile Webservice
==================

The ``smile_webservice`` module is designed to manage webservice calls within the Odoo environment. It provides an interface for creating, tracking, and managing webservice calls.

.. contents:: Table of contents
   :local:

Features
========

- List and form views for webservice calls.
- Status tracking with decorations for different states (error, in progress, done).
- Buttons for actions like force call, re-try, reset to draft, and force done.
- Detailed information on webservice calls including headers, parameters, and responses.

Installation
===========

1. Clone the repository or download the module files.
2. Place the ``smile_webservice`` directory in your Odoo addons path.
3. Update the app list in Odoo.
4. Install the ``smile_webservice`` module from the Odoo apps interface.

Usage
=====

Once installed, you can access the webservice calls through the "Webservices" menu in the Odoo settings back office. You can track their status, and manage their execution.

1. Go to the new menu **Settings > Webservices** to see webservice calls.

   .. image:: static/description/webservice.png
      :alt: webservice in odoo

2. Use the list view to see all webservice calls and their statuses.

   .. image:: static/description/webservice_list.png
      :alt: webservice in odoo

3. Use the form view to see detailed information and perform actions like re-try or force done.

   .. image:: static/description/webservice_form.png
      :alt: webservice in odoo

Contributing
===========

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

Bug Tracker
==========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_webservice%0Aversion:%218.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Contributors
-----------

Smile SA Development Team

Maintainer
---------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.