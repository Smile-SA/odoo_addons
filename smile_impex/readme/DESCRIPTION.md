This module provides a generic import/export engine driven by templates. Each template points to an Odoo model and a Python method to call. Every run is recorded with its state, duration, process ID, host, logs and, optionally, the value returned by the method.

Import templates call the method on the model. Export templates first select the records to export, with a domain or a filter method, split them into batches, and call the method on each batch.

A run can be started by hand from the template, by a scheduled action, or from the *Action* menu of the target model's list view. Errors raised during a run are logged, so you can read them from the interface.
