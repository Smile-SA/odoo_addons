- Only users in the **Access Rights** group, or **Administrator** (Settings), can
  see the **Webservices** menu and read the calls. Users outside these groups
  cannot reach webservice calls. Modules that create calls for them must run
  with elevated rights.
- By default, an outgoing call times out after 60 seconds. To change this, set
  the `webservice_call_timeout` option (in seconds) in the Odoo server
  configuration file, then restart the server:

  ``` ini
  [options]
  webservice_call_timeout = 120
  ```
