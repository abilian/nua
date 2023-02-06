#!/bin/bash

# assuming nua diretory
cd nua-lib
poetry update
poetry install
cd ../nua-agent
poetry update
poetry install
cd ../nua-autobuild
poetry update
poetry install
cd ../nua-build
poetry update
poetry install
cd ../nua-orchestrator
poetry update
poetry install
cd ..
