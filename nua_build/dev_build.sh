#!/bin/bash

for installed in $( pip freeze|grep nua-build )
do
    pip uninstall -y ${installed}
done

perl -pi -e '!$done && s/^(version = \"[.0-9]*)(.*)\"/$1."-".time()."\""/e && ($done=1)' pyproject.toml

poetry install

pytest
