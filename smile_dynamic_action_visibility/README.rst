.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

.. |badge2| image:: https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github
    :target: https://github.com/Smile-SA/odoo_addons/tree/18.0/smile_conditional_fields
    :alt: Smile-SA/odoo_addons

|badge1| |badge2|

========================
Smile Dynamic Action Visibility
========================

This module allows administrators to dynamically control the visibility of
**Actions** and **Reports** in Odoo based on record conditions. It replaces static,
hardcoded visibility rules with a flexible, database-driven rule engine.

Field rules can control:

* **Visibility:** Show or hide actions and reports dynamically.
* **Requirement:** Optionally, integrate with other dynamic rules (if extended).
* **Readonly Status:** N/A (this module focuses on action/report visibility).

**Table of contents**

.. contents::
   :local:

Features
========

* **Dynamic Action Control:** Show or hide server actions dynamically.
* **Report Visibility:** Control availability of print reports in the UI.
* **Expression-Based Rules:** Use Python expressions evaluated on the active record.
* **Multi-Record Support:** In list views, if any selected record satisfies the condition, the action or report is hidden.
* **Model-Specific Rules:** Bind actions to specific models.
* **OWL-Compatible:** Fully integrated with Odoo 18 ActionMenus.
* **Safe Evaluation:** Conditions are evaluated in a sandboxed environment.
* **Graceful Fallback:** UI remains functional even if rule evaluation fails.

Usage
=====

1. Go to **Settings > Technical > Actions > Action Rules**.
2. Create a new rule and define a **Name**.
3. Select the **Target Model**.
4. Select the **Action or Report** to control.
5. Define the **Condition** using a Python expression:

   * When the condition evaluates to ``True``, the action or report will be hidden.
   * Examples:
     - ``record.state == 'draft'`` → hide when the record is in draft
     - ``record.amount_total > 10000`` → hide for high-value records

6. Save the rule. The visibility is updated automatically in the UI.

.. note::
   * If no active record exists (e.g., list view without selection), all actions having rules defined for the model are hidden.
   * In multi-record selection, if any record satisfies the condition, the related action/report is hidden.

Examples
========

* **Draft Protection:** Hide the ``Confirm`` action on ``sale.order`` when
  ``record.state == 'done'``.
* **Conditional Reports:** Hide invoice print reports when ``record.state != 'posted'``.
* **Workflow Enforcement:** Hide cancellation actions once a document is validated.
* **Financial Control:** Hide high-impact actions when ``record.amount_total > 50000``.

Technical Details
=================

* **Backend Engine:** Rules are stored in the ``dynamic.action.rule`` model.
* **Evaluation:** Conditions are evaluated using Python ``eval`` in a sandboxed context exposing only the ``record`` variable.
* **RPC Integration:** The method ``get_invisible_action_ids()`` is exposed to the web client to filter actions.
* **OWL Patch:** The ``ActionMenus`` OWL component is patched to dynamically remove invisible actions and reports from dropdowns.
* **Performance:** Invisible action IDs are computed once per interaction and filtered client-side for efficiency.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/Smile-SA/odoo_addons/issues>`_.
In case of trouble, please check there if your issue has already been reported. If you spotted it first, help us smash it by providing detailed feedback `here <https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_conditional_fields%0Aversion:%2018.0>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Contributors
------------

* Younes EL AHRACH
* Smile SA Development Team

Maintainer
----------

This module is maintained by Smile SA.

Since 1991, Smile has been a pioneer of technology and the European expert in open source solutions.
