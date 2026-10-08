## 20.0.1.0.0 (2026-10-08)

- [BREAKING] Access to webservice calls is restricted to the Access Rights group
  (internal, portal and public users no longer have access).
- [ADD] Migration to Odoo 20.0.
- [FIX] A call that fails before getting a response (network error, timeout,
  empty header) now goes to Error instead of staying In progress.
- [FIX] Retrying failed calls in bulk now replays them instead of marking them
  as done.
- [FIX] Duration is measured from the start of the request, not from the
  creation of the call.
