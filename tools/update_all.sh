#!/bin/bash

# assuming nua diretory
cd nua-lib
poetry update
poetry install
cd ../nua-runtime
poetry update
poetry install
cd ../nua-selfbuilder
poetry update
poetry install
cd ../nua-build
poetry update
poetry install
cd ../nua-orchestrator
poetry update
poetry install
cd ..
