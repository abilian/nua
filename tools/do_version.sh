#!/bin/bash

top=$(git rev-parse --show-toplevel)
VERS=0.4.85

perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-lib/pyproject.toml

perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-runtime/pyproject.toml
# perl -pi -e 's/(\s*nua-lib\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-runtime/pyproject.toml

perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-autobuild/pyproject.toml
# perl -pi -e 's/(\s*nua-lib\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-autobuild/pyproject.toml
# perl -pi -e 's/(\s*nua-runtime\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-autobuild/pyproject.toml

perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-build/pyproject.toml
# perl -pi -e 's/(\s*nua-lib\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-build/pyproject.toml
# perl -pi -e 's/(\s*nua-runtime\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-build/pyproject.toml
# perl -pi -e 's/(\s*nua-autobuild\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-build/pyproject.toml


perl -pi -e '!$x && s/(\s*version\s*=\s*)\"(.+)\"/\1\"'${VERS}'\"/ && ($x=1)' ${top}/nua-orchestrator/pyproject.toml
# perl -pi -e 's/(\s*nua-lib\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-orchestrator/pyproject.toml
# perl -pi -e 's/(\s*nua-runtime\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-orchestrator/pyproject.toml
# perl -pi -e 's/(\s*nua-autobuild\s*=\s*)\"(.+)\"/\1\"=='${VERS}'\"/' ${top}/nua-orchestrator/pyproject.toml
