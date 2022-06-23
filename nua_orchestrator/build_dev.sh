#!/bin/bash
pip freeze|grep nua-orchestrator|xargs pip uninstall -y

perl -pi -e '!$done && s/^(version = \"[.0-9]*)(.*)\"/$1."-".time()."\""/e && ($done=1)' pyproject.toml

poetry install

pytest
