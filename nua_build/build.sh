#!/bin/bash

NUA_WHEEL_DIR="nua_build_wheel"

for installed in $( pip list --format freeze|grep nua-build )
do
    pip uninstall -y ${installed}
done

rm -fr dist
poetry build -f wheel
[[ -d ~/${NUA_WHEEL_DIR} ]] && rm -fr ~/${NUA_WHEEL_DIR}
mv dist nua_build_wheel
mv nua_build_wheel ~
pip install ~/${NUA_WHEEL_DIR}/*.whl
