This module requires the Python library `psutil`. It is part of the standard Odoo requirements, so it is usually already installed.

If Odoo runs on several servers behind a load balancer, set the option `hostname` in the configuration file of each server. The default value is `localhost`.

Each run records the ID of the process that executes it. A process ID created on one host cannot be seen from the others. Without a distinct `hostname`, each time one of the servers restarts, imports and exports running on the other servers will be marked as *Killed*.
