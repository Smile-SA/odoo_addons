To deliver an upgrade:

1. Add a folder for the new version in the upgrades directory, with its
   `__upgrade__.py` and its files.
2. Set the new version in `upgrade.conf`.
3. Deploy the code and restart the server (see Installation).

At startup, the module applies every upgrade whose version is higher than the database
version and lower than or equal to the code version, and whose `databases` list is empty
or contains the database. For each startup with something to apply, it:

- waits for the upgrade lock if another server holds it;
- disables scheduled actions until the upgrade is done;
- runs the `pre-load` SQL files;
- updates the modules listed in `modules_to_upgrade`;
- runs the `post-load` files and reloads the listed translations;
- stores the new version in the database.

The log shows `no upgrade to load` when the database is already up to date.

Upgrades run only when the server starts on a database and when a database is created.
Installing a module from the Apps menu or restoring a database does not trigger them.

Administrators (users with the Settings access rights) see the code version in the top
bar, next to a fork icon. `?!` means that no upgrade has been recorded in the database.
