#!/bin/bash

echo "This demo script can compile Nua, create a 'nua' user managing
the Nua Orchestrator and run some basic demos.

It must be run locally (./demo.sh) by a user with 'sudoer' capability.

The script will update and install many packages (build-essential, python3.10, ...).

Important:
  - this script will propose to erase all your docker content:
      'docker system prune -a'

- check the GIT_LOCAL variable at the beginning of the script
- NUA_CERTBOT_STRATEGY is 'none' (no https config, default is 'auto')
"

# Where to clone Nua
GIT_LOCAL="${HOME}/gits2"

#######################################################################

HERE="$PWD"
NUA_CERTBOT_STRATEGY="none"
NUA_BUILD="${GIT_LOCAL}/nua/nua-build"
NUA_ORC="${GIT_LOCAL}/nua/nua-orchestrator"
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


yesno "Run the script (many packages will be installed/updated)" || exit 0

cat /etc/lsb-release |grep -q 'Ubuntu 22.04' || {
    echo "The script is only tested for distribution 'Ubuntu 22.04'"
    yesno "Continue anyway" || exit 1
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
# libpq-dev
# libpq5

exe sudo DEBIAN_FRONTEND=noninteractive apt-get update --fix-missing
exe sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
exe sudo DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y ${packages}
exe sudo DEBIAN_FRONTEND=noninteractive apt autoremove -y

[ "${VIRTUAL_ENV}" != "p3nua" ] && [ ! -f "${HOME}/p3nua/bin/activate" ] && {
    echo
    echo_yellow "Installation of nua-build requires some python virtual env"
    yesno "Make venv 'p3nua'" && {
        exe cd ${HOME}
        exe python3.10 -m venv p3nua
        exe source p3nua/bin/activate
        exe pip install -U pip setuptools wheel poetry
    }
}


source ${HOME}/p3nua/bin/activate || {
    echo "Error: no virtual env '${HOME}/p3nua' found. Exiting."
    exit 1
}

exe pip install -U pip setuptools wheel poetry

yesno "Do 'git clone' nua repository from '${NUA_REPOSITORY}' and build nua" && {
    exe mkdir -p "${GIT_LOCAL}"
    exe cd "${GIT_LOCAL}"
    [ -d "nua" ] && sudo rm -fr nua
    exe git clone ${NUA_REPOSITORY}
    exe cd nua
    exe git checkout ${BRANCH}
    exe cd "${NUA_BUILD}"
    git pull
    git checkout ${BRANCH}
    ./build.sh
    exe cd "${NUA_ORC}"
    ./build.sh
}


yesno "Erase all local docker images (not mandatory, but it ensures a clean rebuild of Nua images)" && {
    docker system prune -a
}


yesno "Build docker images for Nua demo" && {
    exe cd "${HERE}/files_v2"
    exe nua-build -vv flask_hello
    exe nua-build -vv flask_upload_tmpfs
    exe nua-build -vv flask_pg_via_orch
}


yesno "Important: creation of the account for the orchestrator" && {
    exe cd "${NUA_ORC}"
    if [ "$EUID" == "0" ]; then
        exe nua-bootstrap
    else
        exe sudo "${VIRTUAL_ENV}/bin/nua-bootstrap"
    fi
}

yesno "Provide actual domain names for the 3 'example.com' domains" && {
    rm -f "${HERE}/REPLACE_DOMAIN"
    for d in test1 test2 test3
    do
        read -p "Enter the fqdn replacing '${d}.example.com' ? " response
        echo "${d}.example.com ${response}" >> "${HERE}/REPLACE_DOMAIN"
    done
} || {
    echo "test1.example.com test1.example.com" > "${HERE}/REPLACE_DOMAIN"
    echo "test2.example.com test2.example.com" >> "${HERE}/REPLACE_DOMAIN"
    echo "test3.example.com test3.example.com" >> "${HERE}/REPLACE_DOMAIN"
}

yesno "Demo 1: start 2 basic flask apps" && {
    file="sample1_2_flask_apps.toml"
    path="${HERE}/files_v2/${file}"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/${file}
    echo -e "${cgreen}"
    cat /tmp/${file}
    echo -e "${cclear}"
    echo
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua-orchestrator deploy -v /tmp/${file}
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 2: start 3 instances of an app using a postgres DB" && {
    file="sample2_3_flask_pg.toml"
    path="${HERE}/files_v2/${file}"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/${file}
    echo -e "${cgreen}"
    cat /tmp/${file}
    echo -e "${cclear}"
    echo
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua-orchestrator deploy -v /tmp/${file}
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 3: start 2 instances of an app using postgres and some tmpfs apps" && {
    file="sample3_3_flask_tmpfs.toml"
    path="${HERE}/files_v2/${file}"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/${file}
    echo -e "${cgreen}"
    cat /tmp/${file}
    echo -e "${cclear}"
    echo
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua-orchestrator deploy -v /tmp/${file}
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 4: start 1 instances of 3 different apps" && {
    file="sample4_3_instances.toml"
    path="${HERE}/files_v2/${file}"
    echo "The following file will be generated from user requirements (domain, db name)"
    echo "and Nua will complete with defaults values."
    echo
    nua_test_replace_domain "${HERE}/REPLACE_DOMAIN" "${path}" /tmp
    chmod a+r /tmp/${file}
    echo -e "${cgreen}"
    cat /tmp/${file}
    echo -e "${cclear}"
    echo
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua-orchestrator deploy -v /tmp/${file}
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}

echo_yellow "End of the demo."
