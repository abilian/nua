Nua Server
==========

Prototype of the Web UI for Nua.

Currently:

- Uses the orchestator as a backend, with SSH as a transport (like nua-cli)
  - This will change to use a web API (REST or RPC, TBD)
  - The Web server may be merged with the orchestator later (while keeping the layered architecture)

- The design and UI system is currently based on:
  - Tailwind CSS
  - A17t <https://a17t.miles.land/> (we will change to something else later)
  - Alpine.js for the interactive parts (not working, and may be replaced by something else later)

- The web framework currently used it Starlite (soon to be renamed to Litestar).
  - This may change to something else later.
