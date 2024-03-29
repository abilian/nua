# Nua demo

This demo script will:

- build the Nua software,
- create a 'nua' user managing the Nua Orchestrator,
- build some Nua packages (nua-build tool),
- install groups of packages (nua-orchestrator tool).

The demo requires a recent Ubuntu platform like Ubuntu 22.04.2 LTS.

The script must be run locally by a user with 'sudoer' capability.

You can skip parts of the demo (just answer 'n').

The script will update and install many packages on the local host
(build-essential, python3.10, ...).

Important: this script will propose to erase all your docker content
with the command:

    'docker system prune -a'

Check variables at beginning of this script:

   - GIT_LOCAL : local git folder,
   - NUA_CERTBOT_STRATEGY : 'none' for HTTP config, set to 'auto' for HTTPS

Last update: Nua version 0.5.21

## Run it

To run the demo, on a dispendable Ubuntu 22.04 server or VM, simply run (after reading the information above):

```shell
./demo.sh
```

## View a recording

```shell
./play_demo_screencast.sh
```

Or view it online:

[![asciicast](https://asciinema.org/a/572550.svg)](https://asciinema.org/a/572550)

More to come....
