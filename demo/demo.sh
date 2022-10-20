#!/bin/bash

echo "Ce script de démo peut compiler Nua, créer un utilisateur 'nua' gérant
l'orchestrateur Nua et lancer quelques démos de base.

Il doit être lancé localement (./demo.sh) par un utilisateur 'sudoer'.

- modifier le fichier REPLACE_DOMAIN dans ce répertoire
- Vérifier la variable suivante en début de script
- NUA_CERTBOT_STRATEGY est à "none" (pas de config https, par défaut: "auto")
"

GIT_LOCAL="${HOME}/gits2"

#######################################################################

HERE="$PWD"
NUA_CERTBOT_STRATEGY="none"
NUA_BUILD="${GIT_LOCAL}/nua/nua_build"
NUA_ORC="${GIT_LOCAL}/nua/nua_orchestrator_local"
DEMO="${GIT_LOCAL}/nua/demo"

function yesno {
    echo
    read -p "----> $1 ? (y/n) " -n 1
    echo
    echo
    [[ "$REPLY" =~ ^[YyOo]$ ]] && return 0
    return 1
}

function exe() {
    echo "\$ $@" ; "$@" ;
}

[ -z ${VIRTUAL_ENV} ] && {
    echo "Installatin of nua-build requires some venv python"

    yesno "make venv 'p3nua'" && {
        exe cd ${HOME}
        exe python3.10 -m venv p3nua
        exe source p3nua/bin/activate
        exe pip install -U pip
        exe pip install -U setuptools
        exe pip install -U poetry
    }
}

source ${HOME}/p3nua/bin/activate || exit 1


if [ ! -d "${NUA_BUILD}" ] ; then
    yesno "git clone nua repository" && {
        exe mkdir -p "${GIT_LOCAL}"
        exe cd "${GIT_LOCAL}"
        exe git clone -o github https://github.com/abilian/nua.git
        exe cd nua
        exe git checkout main
    }
fi

yesno "build nua" && {
    exe cd "${NUA_BUILD}"
    git pull
    git checkout main
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
    python3 ${HERE}/replace_domain.py "${path}" /tmp
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
    python3 ${HERE}/replace_domain.py "${path}" /tmp
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
    python3 ${HERE}/replace_domain.py "${path}" /tmp
    chmod a+r /tmp/sample_flask_pg_tmpfs.toml
    cat <<EOF > /tmp/test.sh
#!/bin/bash
export NUA_CERTBOT_STRATEGY="${NUA_CERTBOT_STRATEGY}"
~nua/nua310/bin/nua deploy -v /tmp/sample_flask_pg_tmpfs.toml
EOF
    chmod a+x /tmp/test.sh
    sudo -u nua bash /tmp/test.sh
}
