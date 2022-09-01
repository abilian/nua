#!/bin/bash

for installed in $( pip freeze|grep nua-build )
do
    pip uninstall -y ${installed}
done

poetry install
