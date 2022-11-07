#!/bin/bash

for installed in $( pip list --format freeze | grep nua-orchestrator )
do
    echo "${installed}"
    pip uninstall -y "${installed}"
done

poetry install
