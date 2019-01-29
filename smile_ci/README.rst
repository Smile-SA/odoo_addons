======================
Continuous Integration
======================
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/10.0/smile_ci
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

Track continuous integration of a project by using different Smile's modules:
    * smile_docker: https://github.com/Smile-SA/odoo_addons/tree/10.0/smile_docker
    * smile_scm: https://github.com/Smile-SA/odoo_addons/tree/10.0/smile_scm
    * smile_test: https://github.com/Smile-SA/odoo_addons/tree/10.0/smile_ci/addons/smile_test

Features

    * Update branch
        * For SVN repositories, configure the anonymous login/password
        * For Git repositories, add read access to the server via SSH key
    * Check if changes
    * Create build
    * Test build (set max_testing to limit concurrent testing builds)
        * Create Docker containers
          (Odoo server, database engine and other linked services)
        * Run daemonized Docker containers which starts server in test mode
        * Check code quality with flake8
        * Count lines of code with cloc
        * Create new database with demo or Restore dump in XML/RPC
        * Install modules in XML/RPC
        * Let Docker containers run until new builds kill it
          (set max_running to limit concurrent running builds)
    * Attach log / config / tests result / code coverage files to build
    * Parse build logs and store results in database

**Table of contents**

.. contents::
   :local:

Usage
=====

1. Go to ``Integration > Configuration > Repositories`` to create a new repository and add branches:

    .. figure:: static/description/create_repository.png
       :alt: Create Repository
       :width: 850px

2. Go to ``Integration > Configuration > Branches`` to clone and configure the branches:

    .. figure:: static/description/config_branch.png
       :alt: Branch configuration
       :width: 790px

    .. figure:: static/description/advanced_config_branch.png
       :alt: Advanced branch configuration
       :width: 790px

3. Test or force the test branch to create a new build:

    .. figure:: static/description/create_build.png
       :alt: Create a build
       :width: 750px

    .. figure:: static/description/created_builds.png
       :alt: Created a builds
       :width: 850px

4. You can open a build, show tests result, quality errors and the code coverage of a build via this view:

    .. figure:: static/description/show_build_info.png
       :alt: Show build information
       :width: 850px

5. Log, config, tests result, code coverage files of a build are attached in this view:

    .. figure:: static/description/attachments.png
       :alt: Attachments
       :width: 700px

6. To display all builds, go to ``Integration > Dashboard``:

    .. figure:: static/description/dashboard.png
       :alt: Dashboard
       :width: 850px


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_ci%0Aversion:%2010.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Author
------

* Smile SA

Contributors
------------

* Corentin POUHET-BRUNERIE
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