#!/bin/bash

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

# sysctl -w vm.max_map_count=262144