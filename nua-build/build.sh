#!/bin/bash

# function is_gnu_sed(){
#   sed --version >/dev/null 2>&1
# }

for installed in $( pip list --format freeze | grep nua- )
do
    echo "${installed}"
    pip uninstall -y "${installed}"
done
#
# # quick fix about poetry & relative path dependencies & wheels
# # Idea here is to use the "path=" local dependency system of poetry while dev mode,
# # while using the 'safe' "*" value for test deployments
# cd ../nua-autobuild
# ./build.sh
# cd ../nua-build
#
# cp -f pyproject.toml pyproject.toml.orig
#
# is_gnu_sed && {
#     sed -i 's/^nua-lib =.*$/nua-lib = { path = "..\/nua-lib\/", develop = false }/' pyproject.toml; } || {
#     sed -i "" 's/^nua-lib =.*$/nua-lib = { path = "..\/nua-lib\/", develop = false }/' pyproject.toml;
# }
# is_gnu_sed && {
#     sed -i 's/^nua-agent =.*$/nua-agent = { path = "..\/nua-agent\/", develop = false }/' pyproject.toml; } || {
#     sed -i "" 's/^nua-agent =.*$/nua-agent = { path = "..\/nua-agent\/", develop = false }/' pyproject.toml;
# }
# is_gnu_sed && {
#     sed -i 's/^nua-autobuild =.*$/nua-autobuild = { path = "..\/nua-autobuild\/", develop = false }/' pyproject.toml; } || {
#     sed -i "" 's/^nua-autobuild =.*$/nua-autobuild = { path = "..\/nua-autobuild\/", develop = false }/' pyproject.toml;
# }
# poetry install
#
# mv -f pyproject.toml.orig pyproject.toml

poetry install

nua-build --version
