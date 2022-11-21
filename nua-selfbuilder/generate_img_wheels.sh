#!/bin/bash
#
#  Todo: make this part of a nua-build python script (or nua-selfimage)
#

echo "Make wheels for Nua base image if required:"

version=$(nua-build --version |sed 's/.*:\s*\(.*\)$/\1/')
WHEEL_DIR="/var/tmp/nua_build_wheel_${version}"

rm -fr "${WHEEL_DIR}"
mkdir -p "${WHEEL_DIR}"

cd ../nua-lib
rm -fr dist
poetry build -f wheel
mv dist/* "${WHEEL_DIR}"

cd ../nua-runtime
rm -fr dist
poetry build -f wheel
mv dist/* "${WHEEL_DIR}"
#
# cd ../nua-build
# rm -fr dist
# poetry build -f wheel
# mv dist/* "${WHEEL_DIR}"
