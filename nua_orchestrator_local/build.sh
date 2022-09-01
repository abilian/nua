#!/bin/bash

for installed in $( pip freeze|grep nua-orchestrator-local )
do
    pip uninstall -y ${installed}
done

poetry install
