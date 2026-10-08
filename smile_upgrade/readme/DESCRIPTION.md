This module applies versioned data upgrades to a database when the Odoo server starts.
Each upgrade is a folder on disk that lists SQL scripts to run before the modules load,
the modules to update, and the SQL, Python, CSV and XML files to run afterwards. At
startup, the module compares the code version with the version stored in the database
and applies the missing upgrades in version order.

When a database is created, only the latest upgrade is applied, with the modules it lists
for installation at creation. A new database therefore starts at the current code version
without replaying the history.

Administrators see the version applied to the database in the top bar.
