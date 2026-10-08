This module deletes old records from any model, based on a retention period. An
administrator creates a purge rule that names a model, one of its date fields and how
long records are kept. Records whose date is older than that are deleted when the rule
runs.

Rules are managed in *Settings > Purge Data > Purge Data*. Each run deletes a limited
number of records, so that large tables can be cleaned up step by step. Each rule keeps a
count of the records it has deleted.
