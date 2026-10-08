## 20.0.1.0.0 (2026-10-08)

- [BREAKING] Import and export templates, runs and their logs are now restricted to the group *Role / Administrator*. Other internal users no longer have access.
- [ADD] Migration to Odoo 20.0.
- [FIX] *Test Import* and *Test Export* no longer keep the changes made by the method.
- [FIX] The *One At A Time* option now really prevents two runs of the same template at the same time.
- [FIX] The *Order by* option of export templates is now respected.
- [FIX] Exports split into several batches no longer fail when run in a new thread.
- [FIX] Runs started in a new thread by a scheduled action or a client action no longer use a closed database cursor.
