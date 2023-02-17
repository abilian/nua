# Nua orchestrator

## Role of the orchestrator

The orchestrator is in charge of configuring application and resources and deploying them on the host.

## Requirements

The host must be a linux server installed with the distribution:

    Ubuntu 22.04.1 LTS (jammy)

In the current version, the orchestrator manages locally a single host.

The Nua Orchestrator will need a 'nua' administrator account with root privileges (sudoer and docker groups).

The Nua Orchestrator will interfere with local resources such as Docker services and locally installed databases. The recommended configuration is therefore to use a dedicated server.

## Installation

### The bootstrap command

To install, use the boostraping script: `nua-bootstrap`.

At the moment, that implies a first temporary installation of Nua (that can be done in a temporary directory)

```console
    git clone https://github.com/abilian/nua
    cd nua-orchestrator
    ./build.sh
    nua-bootstrap
```


That command will do many things:

- create nua account
- install required packages (Docker, postgres, Nginx, ...)
- apply default configuration to the host
- ...

### Remarks

-   `nua-bootstrap` can be safely launched on an existing configuration,
-   `nua-bootstrap` must be launched as root, if not, a warning is displayed:

```console
$ nua-bootstrap
Installing Nua bootstrap on local host.
Warning: Nua was already installed.
Nua bootstrap script requires root privileges.
Please try again, this time using 'sudo'.
- When sudo, use absolute script path.
- Possible command:
    sudo /home/nua/nua310/bin/nua-bootstrap
```

### Installation phases

Installation can take several minutes, here an excerpt of main messages displayed during installation:

```console
sudo /home/nua/nua310/bin/nua-bootstrap
Installing Nua bootstrap on local host.
Warning: Nua was already installed.
Ign:1 http://downloads.mariadb.com/Tools/ubuntu jammy InRelease
Hit:2 http://nova.clouds.archive.ubuntu.com/ubuntu jammy InRelease                                                                        [...]
Installation of base packages:
apt-get install --no-install-recommends -y ca-certificates curl docker.io lsb-release git nginx-light software-properties-common python3-certbot-nginx
[...]
Modifying /etc/sudoers for user 'nua' (full access with no passwd)
-> Prior changes found: do nothing
Creation of Python virtual environment for 'nua'
-> Prior /home/nua/nua310 found: do nothing
Install pip
[...]
Installation of postgres version 14
apt-get install --no-install-recommends -y postgresql-14 libpq-dev
[...]
Setting Postgres password
Installation of Nua nginx configuration
systemctl restart nginx
Installation of local Nua orchestrator (via git)
Cloning into 'nua'...
[...]

Nua installation done for user 'nua' on this host.
Command 'nua --help':
```

At the end of the installation, the availables commands are displayed.
