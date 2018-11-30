==================
Models Graph
==================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/12.0/smile_model_graph
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

Generate Models Graph from Odoo's user interface with depth and relation names between models.
    You need to install Graphviz to print graph. More infos on http://www.graphviz.org.
    You can install it with pip:

    * sudo apt install python3-pip
    * pip3 install pydot

**Table of contents**

.. contents::
   :local:

Usage
=====

#. After activating the Developer Mode, go to ``Settings > Technical > Database Structure > Models``.
    .. figure:: static/description/menu_models.png
       :alt: Models menu
       :width: 850px

#. Select your model for which you want to download the graph. For example, ``ir.model``. Then click on Print button and choose ``Models Graph``.
    .. figure:: static/description/ir_model.png
       :alt: ir.model model
       :width: 850px

#. Select the number of depth you want to display and finally click on ``Print Graph``.
    .. figure:: static/description/models_graph.png
       :alt: Models Graph
       :width: 850px

#. The result for the ``ir.model`` will be:
    .. figure:: static/description/model_graph.png
       :alt: Model Graph representation
       :width: 850px

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_model_graph%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Contributors
------------

* Corentin POUHET-BRUNERIE
* Ibrahim BOUDMIR

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
