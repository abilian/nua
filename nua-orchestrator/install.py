#!/usr/bin/env python3

import subprocess
import sys
import textwrap
from pathlib import Path

print(textwrap.fill("""\
This script will install the orchestrator package in a virtual environment, \
for the only purpose of running the `nua-bootstrap` commande later."""))

if Path("env").exists():
    print("Virtual environment already exists in ./env. Please remove it first.")
    sys.exit()

print("Creating virtual environment...")
subprocess.run(["python3", "-m", "venv", "env"])
subprocess.run(["./env/bin/pip", "install", "-U", "pip", "setuptools", "wheel"])

print("Installing nua-orchestrator (in development mode)...")
subprocess.run(["./env/bin/pip", "install", "-e", "."])

# print("Checking nua-orchestrator version...")
# subprocess.run(["./env/bin/nua-orchestrator", "--version"])

print()
print("Now you can run the bootstrap command:")
print("sudo ./env/bin/nua-bootstrap")
