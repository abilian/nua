#!/bin/bash
for installed in $( pip list --format freeze | grep nua- )
do
    pip uninstall -y "${installed}"
done
