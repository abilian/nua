#!/bin/bash

for installed in $( pip list --format freeze|grep nua-build )
do
    pip uninstall -y ${installed}
done

rm -fr dist
poetry build -f wheel
pip install dist/*.whl
nua-build --version
version=$(nua-build --version |sed 's/.*:\s*\(.*\)$/\1/')
WHEEL_DIR="/var/tmp/nua_build_wheel_${version}"
mkdir -p ${WHEEL_DIR}
mv dist/* ${WHEEL_DIR}
