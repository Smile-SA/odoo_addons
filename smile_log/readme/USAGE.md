To log messages from a module:

- Add `smile_log` to the `depends` of the module manifest.
- Create a logger with the database name, the model name, the record id and the user id,
  then send messages:

  ``` python
  from odoo.addons.smile_log.tools import SmileDBLogger

  logger = SmileDBLogger(self.env.cr.dbname, self._name, self.id, self.env.uid)
  logger.info("Import started")
  ```

- The logger offers `debug`, `info`, `warning`, `error`, `critical` and `exception`.
  `error`, `critical` and `exception` add the current traceback to the message.
  `time_info` and `time_debug` add the time elapsed since the logger was created.
- `logger.pid` gives the run number shared by all the messages of this logger.

To read the logs:

- Go to *Settings > Technical > Logging > Logs*.
- The list shows the *Date*, *Pid*, *Model name*, *Ressource id*, *Level* and *Message*
  of each log, newest first.
- Use the search to filter on these fields, and the *Model* and *PID* groupings to
  gather the logs of a model or of one run.

When the Odoo server stops, an *Odoo server stopped* message is logged in each database
that received logs.
