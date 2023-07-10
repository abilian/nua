---
date: 2023-05-02
description: New release with new features and fixes
categories:
  - release
  - alpha
---

# Nua 0.5.17 released

## New features

- Nua-orchestrator: the deployment commands of the orchestrator (deploy, remove) now use a sequential mode.
- Nua-orchestrator: upgrading the application package or changing the deployed domain is permitted by the `deploy` command (experimental).

## Refactoring

- The `nua-autobuild` subproject has been merged into `nua-nuild`.
- Dependencies between subprojects have been simplified. `nua-lib` is now the only subprojects upon which the other subprojects depend.

## Fixes

- Numerous fixes.
