Some tables keep growing: currency rates, messages, technical logs, imported lines.
Odoo has no generic tool to remove old records from them, so they are usually cleaned up
with ad hoc scripts.

This module lets an administrator set a retention period per model from the interface.
Deletion goes through the standard Odoo deletion, with the access rights and record rules
of the user who runs the rule. A record that cannot be deleted, because another record
still uses it or because of a business check, is skipped and the others are deleted.

The module depends only on `base`. It does not provide a scheduled action: purges run
when an administrator clicks the button, or from a scheduled action created during
configuration.
