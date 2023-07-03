#!/bin/bash

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

pip install -r test-requirements.txt

# sysctl -w vm.max_map_count=262144

# This is needed to setup environment variables similar to docker environment
set -a
source .env
set +a

export PYTHONPATH=memas
