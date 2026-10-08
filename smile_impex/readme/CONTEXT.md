Projects often exchange data with other systems on a schedule. A plain scheduled action keeps no history of its runs, and when one fails, the cause is only in the server logs.

With this module, the project code provides the actual import or export method. The module handles when it runs, which records it receives, and what happened during each run. Logs are stored with the module *smile_log*, so they can be read from the run itself.

This is a technical module. It adds no business feature on its own and is meant to be used by project modules that implement the import and export methods.

It depends on:

- *mail*
- *smile_log*, which stores the execution logs
