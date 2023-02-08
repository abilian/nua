#!/bin/bash

echo "Deprecate. Use 'inv bump-version' instead."

#top=$(git rev-parse --show-toplevel)
#VERS=0.4.87
#
#perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-lib/pyproject.toml
#
#perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-agent/pyproject.toml
## perl -pi -e 's/(\s*nua-lib\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-agent/pyproject.toml
#
#perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-autobuild/pyproject.toml
## perl -pi -e 's/(\s*nua-lib\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-autobuild/pyproject.toml
## perl -pi -e 's/(\s*nua-agent\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-autobuild/pyproject.toml
#
#perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-build/pyproject.toml
## perl -pi -e 's/(\s*nua-lib\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-build/pyproject.toml
## perl -pi -e 's/(\s*nua-agent\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-build/pyproject.toml
## perl -pi -e 's/(\s*nua-autobuild\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-build/pyproject.toml
#
#
#perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-orchestrator/pyproject.toml
## perl -pi -e 's/(\s*nua-lib\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-orchestrator/pyproject.toml
## perl -pi -e 's/(\s*nua-agent\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-orchestrator/pyproject.toml
## perl -pi -e 's/(\s*nua-autobuild\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-orchestrator/pyproject.toml
