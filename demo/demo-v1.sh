#!/bin/bash

echo "This demo script can compile Nua, create a 'nua' user managing
the Nua Orchestrator and run some basic demos.

It must be run locally (./demo.sh) by a 'sudoer' user.

The script will install many packages (build-essential, python3.10, mariadb...).

Important: this demo takes control on mariadb and postgres on the host, thus may
requires to erase mariadb database.

- modify the REPLACE_DOMAIN file in this directory
- check the GIT_LOCAL variable at the beginning of the script
- NUA_CERTBOT_STRATEGY is 'none' (no https config, default is 'auto')
"

GIT_LOCAL="${HOME}/gits2"

#######################################################################

HERE="$PWD"
NUA_CERTBOT_STRATEGY="none"
NUA_BUILD="${GIT_LOCAL}/nua/nua_build"
NUA_ORC="${GIT_LOCAL}/nua/nua_orchestrator_local"
DEMO="${GIT_LOCAL}/nua/demo"
NUA_REPOSITORY="https://github.com/abilian/nua.git"
BRANCH="main"

cyellow='\033[1;33m'
cclear='\033[0m'
function yesno {
    echo
    echo -ne "${cyellow} ----> $1 ? (y/n) ${cclear}"; read
    echo
    echo
    [[ "$REPLY" =~ ^[YyOo] ]] && return 0
    return 1
}

function exe() {
    echo "\$ $@" ; "$@" ;
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
libmariadb-dev
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
    echo "Installation of nua-build requires some venv python"

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
    [ -d "nua" ] && rm -fr nua
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


yesno "erase all docker images" && {
    docker system prune -a
}


yesno "build some docker images for nua demo" && {
    exe cd "${NUA_BUILD}/tests"
    exe nua-build -vv flask_pg_psyco_wheel
    exe nua-build -vv flask_upload_tmpfs
    # exe nua-build -vv flask_sqla_sqlite_bind_wheel
}


yesno "build all the docker images for nua test (say no)" && {
    exe cd "${NUA_BUILD}/tests"
    echo "This may take a few minutes..."
    pytest -k "test_builds"
}


yesno "Important: creation of the account for the orchestrator" && {
    yesno "Important: removing mariadb and ALL CONTENT (to fix a bug about root password)" && {
        sudo apt-get remove --purge  mariadb-server-10.6
    }
    exe cd "${NUA_ORC}"
    echo "Just to check the warning, than do it again with sudo"

    exe nua-bootstrap
    exe sudo "${VIRTUAL_ENV}/bin/nua-bootstrap"
}


yesno "Demo1: start 2 instances of an app using the local postges server" && {
    path="${HERE}/sample_flask_pg_psyco.toml"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    exe cat "$path"
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/sample_flask_pg_psyco.toml
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua deploy -v /tmp/sample_flask_pg_psyco.toml
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo2: start 3 instances of an app using the local postges server" && {
    path="${HERE}/sample3_flask_pg_psyco.toml"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    exe cat "$path"
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/sample3_flask_pg_psyco.toml
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua deploy -v /tmp/sample3_flask_pg_psyco.toml
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo3: start 3 instances of an app using postges and some tmpfs" && {
    path="${HERE}/sample_flask_pg_tmpfs.toml"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    exe cat "$path"
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/sample_flask_pg_tmpfs.toml
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua deploy -v /tmp/sample_flask_pg_tmpfs.toml
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}
