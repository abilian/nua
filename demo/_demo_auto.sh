#!/bin/bash

DELAY=0.03


function cmtn() {
    txt=$1
    for (( i=0; i<${#txt}; i++ )); do
        sleep ${DELAY}
        echo -n "${txt:$i:1}"
    done
}

function cmt() {
    echo -n "# "
    cmtn "$1"
    echo ""
}

cmt "This demo script will:"
cmt "   - build the Nua software,"
cmt "   - create a 'nua' user managing the Nua Orchestrator,"
cmt "   - build some Nua packages (nua-build tool),"
cmt "   - install groups of packages (nua-orchestrator tool),"
cmt ""; sleep 1
cmt "The demo requires a recent Ubuntu platform like Ubuntu 22.04.2 LTS."
cmt ""; sleep 0.5
cmt "The script must be run locally by a user with 'sudoer' capability."
cmt ""; sleep 0.5
cmt "You can skip parts of the demo (just answer 'n')."
cmt ""; sleep 0.5
cmt "The script will update and install many packages on the local host"
cmt "(build-essential, python3.10, ...)."
cmt ""; sleep 0.5
cmt "Important: this script will propose to erase all your docker content"
cmt "with the command:"
cmt "    'docker system prune -a'"
cmt ""; sleep 1.5
cmt "Check variables at beginning of this script:"
cmt "   - GIT_LOCAL : local git folder,"
cmt "   - NUA_CERTBOT_STRATEGY : 'none' for HTTP config, set to 'auto' for HTTPS"

# Where to clone Nua
GIT_LOCAL="${HOME}/gits2"

#######################################################################

HERE="$PWD"
NUA_CERTBOT_STRATEGY="none"
#NUA_ENV="${HOME}/env"
NUA_ENV="/home/nua/env"
NUA_ORC="${GIT_LOCAL}/nua/nua-orchestrator"
NUA_REPOSITORY="https://github.com/abilian/nua.git"
BRANCH="main"
# Unused
# NUA_BUILD="${GIT_LOCAL}/nua/nua-build"
# DEMO="${GIT_LOCAL}/nua/demo"

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
    echo -ne "${cyellow} ----> "
    cmtn "$1"
    echo -ne " ? (y/n) ${cclear}";
    sleep 0.2
    echo "y"
    echo
    return 0
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

APT_GET="sudo DEBIAN_FRONTEND=noninteractive apt-get -qq -o=Dpkg::Use-Pty=0"
exe $APT_GET update --fix-missing
exe $APT_GET upgrade -y
exe $APT_GET install --no-install-recommends -y ${packages}
exe $APT_GET autoremove -y

[ "${VIRTUAL_ENV}" != "p3nua" ] && [ ! -f "${HOME}/p3nua/bin/activate" ] && {
    echo
    echo_yellow "Installation of nua-build requires some python virtual env"
    yesno "Make venv 'p3nua'" && {
        exe cd ${HOME}
        exe python3.10 -m venv p3nua
        exe source p3nua/bin/activate
        exe pip install -qq -U pip
        exe pip install -qq -U setuptools
        exe pip install -qq -U wheel poetry python-dotenv invoke cleez
    }
}


source ${HOME}/p3nua/bin/activate || {
    echo "Error: no virtual env '${HOME}/p3nua' found. Exiting."
    exit 1
}

exe pip install -qq -U pip setuptools wheel poetry invoke

yesno "Do 'git clone' nua repository from '${NUA_REPOSITORY}' and build nua" && {
    exe mkdir -p "${GIT_LOCAL}"
    exe cd "${GIT_LOCAL}"
    [ -d "nua" ] && sudo rm -fr nua
    exe git clone -q ${NUA_REPOSITORY}
    exe cd nua
    exe git checkout -q ${BRANCH}
    inv install --quiet
}


yesno "Erase all local docker images (not mandatory, but it ensures a clean rebuild of Nua images)" && {
    yes | docker system prune -a
}


yesno "Build docker images for Nua demo" && {
    exe cd "${HERE}/apps"
    exe nua-build -vv flask-hello
    exe nua-build -vv flask-upload-tmpfs
    exe nua-build -vv flask-postgresql
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
        echo -n "Enter the fqdn replacing '${d}.example.com' ? "
        sleep 0.1
        cmtn "${d}.example.com"
        echo
        echo "${d}.example.com ${d}.example.com" >> "${HERE}/REPLACE_DOMAIN"
    done
} || {
    echo "test1.example.com test1.example.com" > "${HERE}/REPLACE_DOMAIN"
    echo "test2.example.com test2.example.com" >> "${HERE}/REPLACE_DOMAIN"
    echo "test3.example.com test3.example.com" >> "${HERE}/REPLACE_DOMAIN"
}

yesno "Demo 1: start 2 basic flask apps" && {
    file="sample1_2_flask_apps.toml"
    path="${HERE}/apps/${file}"
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
${NUA_ENV}/bin/nua-orchestrator deploy-replace -v /tmp/${file}
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 2: start 3 instances of an app using a postgres DB" && {
    file="sample2_3_flask_pg.toml"
    path="${HERE}/apps/${file}"
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
${NUA_ENV}/bin/nua-orchestrator deploy-replace -v /tmp/${file}
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 3: start 2 instances of an app using postgres and some tmpfs apps" && {
    file="sample3_3_flask_tmpfs.toml"
    path="${HERE}/apps/${file}"
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
${NUA_ENV}/bin/nua-orchestrator deploy-replace -v /tmp/${file}
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}


yesno "Demo 4: start 1 instances of 3 different apps" && {
    file="sample4_3_instances.toml"
    path="${HERE}/apps/${file}"
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
${NUA_ENV}/bin/nua-orchestrator deploy-replace -v /tmp/${file}
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}

echo_yellow "End of the demo."
