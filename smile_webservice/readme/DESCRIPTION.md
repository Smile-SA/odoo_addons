This module records the HTTP calls Odoo makes to external systems. Each call is
stored with its URL, headers, parameters, response, duration and, when it fails,
the error code and message.

Administrators can look through these calls in the back office. They can replay
a call that failed, force a draft call to run, or change a call's state by hand.

The module also gives developers a small API. Any Odoo model can use it to
create a traced call and send it as JSON, XML or multipart form data. Other
modules are expected to build on it: on its own, the module sends nothing.
