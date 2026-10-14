[![License: AGPL-3](https://img.shields.io/badge/licence-AGPL--3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![GitHub](https://img.shields.io/badge/github-Smile--SA%2Fodoo_addons-lightgray.png?logo=github)](https://github.com/Smile-SA/odoo_addons/tree/18.0/smile_dynamic_action_visibility)

# Smile Dynamic Action Visibility

This module enables administrators to dynamically control **action and report visibility** in Odoo.  
It allows for the definition of rules that hide actions or reports based on specific conditions, replacing static XML definitions with flexible, database-driven logic.

Field rules can control:

* **Visibility:** Hide actions or reports dynamically based on record values.
* **Condition-Based Logic:** Define Python expressions evaluated on records.
* **Multi-Record Support:** Rules are evaluated across all selected records; if any record satisfies the condition, the action is hidden.

## Table of contents

- [Features](#features)
- [Usage](#usage)
- [Examples](#examples)
- [Technical Details](#technical-details)
- [Bug Tracker](#bug-tracker)
- [Credits](#credits)

## Features

* **Dynamic Action Control:** Show or hide actions and reports without modifying XML views.
* **Expression-Based Logic:** Use Python expressions (e.g., `record.state == 'draft'`) for real-time evaluation.
* **Multi-Record Handling:** Supports list views and multi-selection. An action is hidden if **any** selected record satisfies the condition.
* **Role-Based Rules:** Restrict actions to specific user groups or roles.
* **Cross-Model Conditions:** Evaluate conditions on related fields or records.
* **Database-Driven:** Rules are stored in `dynamic.action.rule` for easy management.

## Usage

1. Go to **Settings > Technical > Actions > Action Rules**.
2. Create a new rule and select the **Target Model**.
3. Select the **Action** or **Report** to which the rule will apply.
4. Define the **Condition** using a Python expression:

    * When the condition evaluates to `True`, the action or report will be **hidden**.
    * Example expressions:
        * `<code>record.state == 'draft'</code>` → hides when record is in draft.
        * `<code>record.amount_total &gt; 10000</code>` → hides for high-value records.

5. Save the rule. Visibility is updated automatically in the UI for both **form views** and **list views**.

> [!IMPORTANT]
> These rules **override** native XML definitions and modifiers dynamically at runtime.

## Examples

* **Workflow Control:** Hide the `Validate Invoice` action on `account.move` when the record is in draft.
* **High-Value Orders:** Hide the `Confirm Sale` action on `sale.order` when `amount_total > 10000`.
* **Manager-Only Reports:** Hide the `Print Ledger` report on `account.move` for users who are not in the Accounting Manager group.
* **Multi-Selection Handling:** If multiple records are selected, the action is hidden if **any record** satisfies the condition.

## Technical Details

* **Server-Side Evaluation:** Conditions are evaluated on the backend using a sandboxed `eval()` with `{"__builtins__": {}}` for safety.
* **Multi-Record Support:** The backend handles multiple active IDs to ensure consistent behavior in list views.
* **Frontend Integration:** The module patches Odoo's `ActionMenus` OWL component to dynamically remove hidden actions from dropdowns.
* **Persistence:** Rules are stored in the `dynamic.action.rule` model.
* **Performance:** Evaluations are efficient and stop early when the condition is satisfied for a record.

## Bug Tracker

Bugs are tracked on [GitHub Issues](https://github.com/Smile-SA/odoo_addons/issues).  
Please check existing issues before reporting. If you found a new issue, provide detailed feedback [here](https://github.com/Smile-SA/odoo_addons/issues/new?body=module:%20smile_dynamic_action_visibility%0Aversion:%2018.0).

Do not contact contributors directly about support or technical issues.

## Credits

### Contributors

* Younes EL AHRACH  
* Smile SA Development Team

### Maintainer

This module is maintained by Smile SA.  

Since 1991, Smile has been a pioneer in technology and the European expert in open-source solutions.
