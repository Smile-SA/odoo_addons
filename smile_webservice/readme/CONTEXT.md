When an integration with a third-party system fails, it is hard to find out
what was sent and what came back. This module keeps a record of every outgoing
call in the database, so a failed call stays visible and can be replayed later.

Project-specific modules create and send the calls. They add their own values
to the **Webservice type** field and set up authentication for the remote
service. This module handles the HTTP request, timeouts, errors and tracing.

It depends only on the `web` module.
