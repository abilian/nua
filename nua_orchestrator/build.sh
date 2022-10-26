#!/bin/bash

for installed in $( pip freeze|grep nua-orchestrator )
do
    pip uninstall -y "${installed}"
done

poetry install
