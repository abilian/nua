#!/bin/bash

for installed in $( pip list --format freeze|grep nua-build )
do
    pip uninstall -y ${installed}
done

# quick fix about poetry & relative path dependencies & wheels
cp -f pyproject.toml pyproject.toml.orig
sed -i 's/^nua-lib =.*$/nua-lib = "*"/' -i pyproject.toml || sed -i "" 's/^nua-lib =.*$/nua-lib = "*"/' -i pyproject.toml
rm -fr dist
poetry build -f wheel
pip install dist/*.whl
nua-build --version
version=$(nua-build --version |sed 's/.*:\s*\(.*\)$/\1/')
WHEEL_DIR="/var/tmp/nua_build_wheel_${version}"
mkdir -p ${WHEEL_DIR}
mv dist/* ${WHEEL_DIR}
cp -f pyproject.toml.orig pyproject.toml

# make also nua-lib wheel
cd ../nua-lib/
poetry build -f wheel
mv dist/nua_lib-* ${WHEEL_DIR}
