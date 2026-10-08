The *Settings > Technical* menu is visible only in developer mode.

To let users read the logs:

- Go to *Settings > Users & Companies > Groups*.
- Open the *Smile Logs / User* group and add the users.

Users in the *Role / Administrator* group already belong to this group.

To archive and delete old logs on a regular basis:

- Go to *Settings > Technical > Automation > Scheduled Actions* and create a record.
- Set *Model* to *Smile Logs* and choose the *Execute Every* interval.
- In the *Code* tab, call the archiving method with the number of days to keep and the
  archive folder:

  ``` python
  model.archive_and_delete_old_logs(nb_days=90, archive_path="/var/backups/smile_log")
  ```

Logs older than `nb_days` days are written to a `YYYYMMDD_HHMMSS.log.csv` file in
`archive_path`, then deleted. Without `archive_path`, they are deleted without archive.

The CSV file is written by the PostgreSQL server, not by Odoo. The folder must exist on the
database server host and be writable by the PostgreSQL user, and the database user of
Odoo needs the PostgreSQL rights to write server files (superuser or
`pg_write_server_files` role).
