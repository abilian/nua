#!/bin/bash

function is_gnu_sed(){
  sed --version >/dev/null 2>&1
}

for pack in nua-lib nua-selfbuilder
do
    for installed in $( pip list --format freeze | grep "${pack}" )
    do
        echo "${installed}"
        pip uninstall -y "${installed}"
    done
done

# quick fix about poetry & relative path dependencies & wheels
# Idea here is to use the "path=" local dependency system of poetry while dev mode,
# while using the 'safe' "*" value for test deployments
cd ../nua-runtime
poetry install
cd ../nua-selfbuilder

cp -f pyproject.toml pyproject.toml.orig

is_gnu_sed && {
    sed -i 's/^nua-lib =.*$/nua-lib = { path = "..\/nua-lib\/", develop = false }/' pyproject.toml; } || {
    sed -i "" 's/^nua-lib =.*$/nua-lib = { path = "..\/nua-lib\/", develop = false }/' pyproject.toml;
}
is_gnu_sed && {
    sed -i 's/^nua-runtime =.*$/nua-runtime = { path = "..\/nua-runtime\/", develop = false }/' pyproject.toml; } || {
    sed -i "" 's/^nua-runtime =.*$/nua-runtime = { path = "..\/nua-runtime\/", develop = false }/' pyproject.toml;
}

poetry install

mv -f pyproject.toml.orig pyproject.toml
python -c "from nua.selfbuilder import __version__; print('nua.selfbuilder', __version__)"
