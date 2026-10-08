- Before and after each request, the call commits the database transaction. This
  saves the call's state even when the request fails, but it also commits any
  pending changes made earlier in the same transaction.
- The **Model** and **Files** fields exist but are not used by the module. Files
  sent as multipart form data come from the context and are never stored on the
  call.
- If **Expected response** or **XML namespaces** contains text that cannot be
  evaluated, saving shows a raw evaluation error instead of a validation
  message.
- If no authentication data is provided by an inheriting module, requests are
  sent with an empty Basic Auth login and password.
- Search filters exist only for Draft, Done and Error. There is none for
  In progress.
