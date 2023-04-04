#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path


if Path("env").exists():
    print("Virtual environment already exists in ./env. Please remove it first.")
    sys.exit()

print("Creating virtual environment...")
subprocess.run(["python3", "-m", "venv", "env"])

print("Installing nua-orchestrator...")
subprocess.run(["./env/bin/pip", "install", "."])

print("Checking nua-orchestrator version...")
subprocess.run(["./env/bin/nua-orchestrator", "--version"])
