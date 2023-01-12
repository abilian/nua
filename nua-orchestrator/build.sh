#!/bin/bash

for installed in $( pip list --format freeze | grep nua- )
do
    echo "${installed}"
    pip uninstall -y "${installed}"
done

poetry install

nua-orchestrator --version
