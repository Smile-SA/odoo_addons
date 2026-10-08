- Purge by domain is not available: rules can only select records by age. The fields for
  a domain exist in the model but are not shown, and running such a rule raises an error.
- No scheduled action is provided: an administrator has to create one (see Configuration).
- The ids of all the old records of the model are loaded in memory at each run, which can
  be slow on very large tables.
- The rule state never goes back to *Draft*, and the date of the last run is not stored.
- Skipped records are only reported in the server log, not in the interface.
- Records hidden from the user by record rules are not purged.
