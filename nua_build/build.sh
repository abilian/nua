#!/bin/bash

NUA_WHEEL_DIR="/var/tmp/nua_build_wheel"

for installed in $( pip list --format freeze|grep nua-build )
do
    pip uninstall -y ${installed}
done

rm -fr dist
poetry build -f wheel
[[ -d ${NUA_WHEEL_DIR} ]] && rm -fr ${NUA_WHEEL_DIR}
mkdir -p ${NUA_WHEEL_DIR}
mv dist/* ${NUA_WHEEL_DIR}
pip install ${NUA_WHEEL_DIR}/*.whl
