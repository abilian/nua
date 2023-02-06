# Nua Lib

This subproject contains code that is shared between the various Nua subprojects.

The `nua-lib` code beeing used by `nua-agent`, It should have as little dependencies as possible

## Content

`nua-lib` provides:

- `shell`: shell shortcuts (mostly wrappers above subprocess and shutil)
- `exec`: shortcuts to execute sub commands like exec_as_root(), exec_as_root()
- `action`: higher level commands, related to the installation of packages and dependencies (wrappers above apt, pip, ...)
- and a few utilities of minor importance.
