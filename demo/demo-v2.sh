#!/bin/bash

echo "This demo script can compile Nua, create a 'nua' user managing
the Nua Orchestrator and run some basic demos.

It must be run locally (./demo.sh) by a user with 'sudoer' capability.

The script will install many packages (build-essential, python3.10, ...).

Important:
  - this demo takes (optionnaly)) control on postgres on the host.
  - this script will propose to erase all your docker content:
      'docker system prune -a'

- modify the REPLACE_DOMAIN file in this directory, or edit manually the
  'sample_*.toml' files in files_v2 to change the 'domain' default (example.com)
  to your domain.
- check the GIT_LOCAL variable at the beginning of the script
- NUA_CERTBOT_STRATEGY is 'none' (no https config, default is 'auto')
"

# Where to clone nua
GIT_LOCAL="${HOME}/gits2"

#######################################################################

HERE="$PWD"
NUA_CERTBOT_STRATEGY="none"
NUA_BUILD="${GIT_LOCAL}/nua/nua_build"
NUA_ORC="${GIT_LOCAL}/nua/nua_orchestrator"
DEMO="${GIT_LOCAL}/nua/demo"
NUA_REPOSITORY="https://github.com/abilian/nua.git"
BRANCH="main"

cyellow='\033[1;33m'
cgreen='\033[1;32m'
ccyan='\033[1;36m'
cclear='\033[0m'

function echo_yellow {
    echo -e "${cyellow}$1${cclear}"
}

function echo_green {
    echo -e "${cgreen}$1${cclear}"
}

function yesno {
    echo
    echo -ne "${cyellow} ----> $1 ? (y/n) ${cclear}"; read
    echo
    echo
    [[ "$REPLY" =~ ^[YyOo] ]] && return 0
    return 1
}

function exe() {
    echo -e "${ccyan}\$ $@${cclear}"
    "$@"
}


yesno "run the script" || exit 0

cat /etc/lsb-release |grep -q 'Ubuntu 22.04' || {
    echo "The script is only tested for distribution 'Ubuntu 22.04'"
    yesno "continue anyway" || exit 1
}


packages="
apt-utils
build-essential
docker.io
git
libpq-dev
libpq5
nginx-light
python3-certbot-nginx
python3-dev
python3.10
python3.10-dev
python3.10-venv
software-properties-common
sudo
"
exe sudo apt-get update --fix-missing
exe sudo apt-get upgrade -y
exe sudo apt-get install --no-install-recommends -y ${packages}

[ "${VIRTUAL_ENV}" != "p3nua" ] && [ ! -f "${HOME}/p3nua/bin/activate" ] && {
    echo
    echo_yellow "Installation of nua-build requires some venv python"
    yesno "make venv 'p3nua'" && {
        exe cd ${HOME}
        exe python3.10 -m venv p3nua
        exe source p3nua/bin/activate
        exe pip install -U pip setuptools wheel poetry
    }
}


source ${HOME}/p3nua/bin/activate || {
    echo "No virtual env '${HOME}/p3nua' ? Exiting."
    exit 1
}


yesno "git clone nua repository from '${NUA_REPOSITORY}'" && {
    exe mkdir -p "${GIT_LOCAL}"
    exe cd "${GIT_LOCAL}"
    [ -d "nua" ] && sudo rm -fr nua
    exe git clone ${NUA_REPOSITORY}
    exe cd nua
    exe git checkout ${BRANCH}
}


yesno "build nua" && {
    exe cd "${NUA_BUILD}"
    git pull
    git checkout ${BRANCH}
    ./build.sh

    exe cd "${NUA_ORC}"
    ./build.sh
}


yesno "erase all docker images (not mandatory, but it ensures a clean rebuild of nua images)" && {
    docker system prune -a
}


yesno "build some docker images for nua demo" && {
    exe cd "${HERE}/files_v2"
    exe nua-build -vv flask_pg_psyco_wheel
    exe nua-build -vv flask_upload_tmpfs
    exe nua-build -vv flask_pg_dock_psyco_wheel
}


# yesno "build all the docker images for nua test (say no)" && {
#     exe cd "${NUA_BUILD}/tests"
#     echo "This may take a few minutes..."
#     pytest -k "test_builds"
# }


yesno "Important: creation of the account for the orchestrator" && {
    # yesno "option: remove mariadb and ALL CONTENT (to fix a bug about root password)" && {
    #     sudo apt-get remove --purge  mariadb-server-10.6
    # }
    exe cd "${NUA_ORC}"
    if [ "$EUID" == "0" ]; then
        exe nua-bootstrap
    else
        exe sudo "${VIRTUAL_ENV}/bin/nua-bootstrap"
    fi
}


yesno "Demo 1: start 2 instances of an app using the local postgres server" && {
    path="${HERE}/files_v2/sample_2sites_flask_pg_psyco.toml"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/sample_2sites_flask_pg_psyco.toml
    echo -e "${cgreen}"
    cat /tmp/sample_2sites_flask_pg_psyco.toml
    echo -e "${cclear}"
    echo
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua deploy -v /tmp/sample_2sites_flask_pg_psyco.toml
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 2: start 3 instances of an app using the local postgres server" && {
    path="${HERE}/files_v2/sample_3sites_flask_pg_psyco.toml"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/sample_3sites_flask_pg_psyco.toml
    echo -e "${cgreen}"
    cat /tmp/sample_3sites_flask_pg_psyco.toml
    echo -e "${cclear}"
    echo
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua deploy -v /tmp/sample_3sites_flask_pg_psyco.toml
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 3: start 3 instances of an app using postgres and some tmpfs" && {
    path="${HERE}/files_v2/sample_3sites_flask_pg_tmpfs.toml"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/sample_3sites_flask_pg_tmpfs.toml
    echo -e "${cgreen}"
    cat /tmp/sample_3sites_flask_pg_tmpfs.toml
    echo -e "${cclear}"
    echo
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua deploy -v /tmp/sample_3sites_flask_pg_tmpfs.toml
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 4: start 2 instances of an app using postgres in a docker container" && {
    path="${HERE}/files_v2/sample_2sites_flask_pg_docker.toml"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/sample_2sites_flask_pg_docker.toml
    echo -e "${cgreen}"
    cat /tmp/sample_2sites_flask_pg_docker.toml
    echo -e "${cclear}"
    echo
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua deploy -v /tmp/sample_2sites_flask_pg_docker.toml
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}
