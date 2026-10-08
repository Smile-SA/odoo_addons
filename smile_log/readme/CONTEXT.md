Long processes such as imports, synchronisations and batch jobs need a trace that
functional users can read, without access to the server log files. That trace must also
remain when the process fails and its transaction is rolled back.

The logger writes each message at once, in its own database connection. Messages written
before an error therefore stay in the database after the rollback. Every logger gets its
own run number, so the messages of one execution can be grouped together, and each
message is linked to a model and a record id.

The messages are also passed to the standard Odoo log.

The module depends only on `base`. It is a technical building block: other modules must
call the logger to produce logs.
