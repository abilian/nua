#!/bin/bash

for installed in $( pip list --format freeze | grep nua-image )
do
    echo "${installed}"
    pip uninstall -y "${installed}"
done

# quick fix about poetry & relative path dependencies & wheels
cp -f pyproject.toml pyproject.toml.orig
sed -i 's/^nua-lib =.*$/nua-lib = "*"/' -i pyproject.toml || sed -i "" 's/^nua-lib =.*$/nua-lib = "*"/' -i pyproject.toml
rm -fr dist
poetry build -f wheel
pip install dist/*.whl
nua-image --version
