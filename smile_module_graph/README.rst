==================
Modules Graph
==================

.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-Smile_SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/12.0/smile_module_graph
    :alt: Smile-SA/odoo_addons

|badge2| |badge3|

Generate Modules Graph from Odoo's user interface with upward, downward tree view or both.

You need to install Graphviz to print graph. More infos on http://www.graphviz.org.

You can install it with pip:

    * sudo apt install python3-pip
    * pip3 install pydot

Features:

* Print all modules graph.
* Print graph of selected modules only from tree view.
* Print graph of specific module.
* Select upward, downward or both in tree view to print selected module's graph.

**Table of contents**

.. contents::
   :local:

Usage
=====

To print all modules graph:

#. Go to ``Applications > Print Modules Graph``.
#. A popup view of Modules Graph will be displayed.
#. Filter displayed modules in function of their state.

    .. figure:: static/description/modules_graph_form.png
       :alt: Modules Graph Popup
       :width: 850px

#. Click on the button ``Print Graph`` to print the image of module's generated graph.

    .. figure:: static/description/print_graph.png
       :alt: Print Graph
       :width: 850px

#. Download the png file.

    .. figure:: static/description/installed_modules_graph.png
       :alt: Installed Modules Graph
       :width: 850px

To print graph of selected modules:

#. Go to ``Applications`` tree view.
#. Select modules then go to ``Print > Modules Graph`` to print the graph.

    .. figure:: static/description/selected_modules.png
       :alt: Select modules
       :width: 850px

#. Select type of tree view (Up or Down or Up & Down), then Print the graph.

    .. figure:: static/description/print_modules_graph.png
       :alt: print Modules Graph
       :width: 850px

#. resultant graph:

    .. figure:: static/description/resultant_graph.png
       :alt: Resultant Graph
       :width: 600px

You can also print a graph of specific module:

#. Go to a specific module, for example CRM.
#. From the button ``Print Graph`` in module's form, print the graph.

    .. figure:: static/description/graph_of_module.png
       :alt: Graph of specific module
       :width: 850px

    .. figure:: static/description/crm_graph.png
       :alt: CRM Graph
       :width: 400px

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_module_graph%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

GDPR / EU Privacy
=================

This addons does not collect any data and does not set any browser cookies.

Credits
=======

Contributors
------------

* Corentin POUHET-BRUNERIE
* Majda EL MARIOULI

Maintainer
----------

This module is maintained by Smile SA.

Since 1991 Smile has been a pioneer of technology and also the European expert in open source solutions.

.. image:: https://avatars0.githubusercontent.com/u/572339?s=200&v=4
   :alt: Smile SA
   :target: http://smile.fr

This module is part of the `odoo-addons <https://github.com/Smile-SA/odoo_addons>`_ project on GitHub.

You are welcome to contribute.
