#!/bin/bash

which asciinema || sudo DEBIAN_FRONTEND=noninteractive apt install -yq asciinema
clear
asciinema play -i 0.5 demo.cast
