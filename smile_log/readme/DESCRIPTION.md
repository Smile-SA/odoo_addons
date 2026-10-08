This module stores technical logs in the database, so that they can be read from the
Odoo interface. Developers send messages from their own code through a dedicated
logger. Each message is saved with its date, level, user, the record it relates to and
a run number shared by all messages of the same logger.

Users in the *Smile Logs / User* group read these logs in *Settings > Technical >
Logging > Logs*. A server method archives old logs to a CSV file and removes them from
the database, and can be called from a scheduled action.
