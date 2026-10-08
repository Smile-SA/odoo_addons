- CSV and XML files in `post-load` fail on Odoo 20.0, and the upgrade stops. Use Python
  files with `post_load_hook(env)` for these imports until it is fixed.
- A file path of the form `module_name/.../filename` (a file stored outside the upgrade
  folder) fails. Keep the upgrade files inside the upgrade folder.
- `not_rollback_and_continue` does not work after an SQL error: the transaction stays
  aborted, so the next file fails.
- An `__upgrade__.py` with a syntax error stops the server start instead of being
  skipped.
- `stop_after_upgrades`, `no_upgrade_lock` and `force_reload_upgrade` are read as raw
  text from the Odoo configuration file, so `False` turns them on.
- `modules_to_install_at_creation` is ignored when the database is created from the
  database manager. It works when the database is created from the command line with
  `-i`.
- The modules listed in `modules_to_upgrade` are updated twice during the same startup.
- SQL files are split on `;`. A semicolon inside a string literal or a PL/pgSQL block
  breaks the script.
- Waiting for the upgrade lock has no timeout.
- Adding fields on `res.partner` or `res.users` can make the upgrade fail. Add the column
  in a `pre-load` SQL file, with its type, constraints and a value for existing records:

  ``` sql
  ALTER TABLE res_users ADD COLUMN IF NOT EXISTS my_new_boolean BOOLEAN;
  UPDATE res_users SET my_new_boolean = TRUE;
  ```

  These queries are not needed when the database is created.
