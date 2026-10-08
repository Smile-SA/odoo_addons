Deploying a new version of a project usually comes with data fixes: SQL patches, module
updates, one-off scripts. Run by hand, these steps get forgotten or run twice, and they
have to be repeated on every environment.

With this module, the upgrade steps live in the project repository next to the code.
Restarting the server on the new code brings the database to the matching version. The
applied version is stored in the database, so an upgrade already applied is not run again.

When several servers start on the same database at once, a PostgreSQL lock makes them
wait for each other, and only one of them runs the upgrade.

The module depends only on `web` and is installed automatically.
