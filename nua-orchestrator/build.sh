#!/bin/bash

function is_gnu_sed(){
  sed --version >/dev/null 2>&1
}

for installed in $( pip list --format freeze | grep nua-orchestrator )
do
    echo "${installed}"
    pip uninstall -y "${installed}"
done

# quick fix about poetry & relative path dependencies & wheels
# Idea here is to use the "path=" local dependency system of poetry while dev mode,
# while using the 'safe' "*" value for test deployments
cd ../nua-runtime
./build.sh
cd ../nua-orchestrator

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
nua --version
