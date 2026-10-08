- No scheduled action is provided: old logs are kept until an administrator creates one
  (see Configuration).
- The CSV archive is written on the database server, which is often a different host from
  the Odoo server, and needs PostgreSQL rights that hosted databases rarely grant.
- Messages also go to the standard Odoo log, where they are formatted with Python `%`
  formatting. A message with a literal `%` can raise a logging error in the server log.
  The traceback added by `error`, `critical` and `exception` is escaped for this reason.
- The log handler keeps one open database connection per database for the lifetime of
  the server process.
- Logs are read-only in the interface: they cannot be deleted by hand, only by the
  archiving method.
