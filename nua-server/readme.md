Nua Server
==========

Prototype of the Web UI for Nua.

Currently:

- Uses the orchestator as a backend, with SSH as a transport (like nua-cli)
  - This will change to use a web API (REST or RPC, TBD)
  - The Web server may be merged with the orchestator later (while keeping the layered architecture)
- The design system is currently based on:
  - Tailwind CSS
  - A17t <https://a17t.miles.land/>
  - and it will change to something else later
- The web framework currently used it Starlite (soon to be renamed to Litestar).
  - This may change to something else later.
