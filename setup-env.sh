#!/bin/bash

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# download USE
if [ ! -d "encoder/universal-sentence-encoder_4" ]; then
  wget https://tfhub.dev/google/universal-sentence-encoder/4?tf-hub-format=compressed -O use4.tar
  mkdir -p encoder/universal-sentence-encoder_4
  tar -xf use4.tar -C encoder/universal-sentence-encoder_4
  rm use4.tar
fi

source .venv/bin/activate
pip install -r requirements.txt
# TODO: remove this after package split or after beam/datasets package upgrade 
pip install --no-deps -r requirements-no-deps.txt

pip install -r test-requirements.txt
python3 -c "import nltk; nltk.download('punkt')"

# sysctl -w vm.max_map_count=262144

# This is needed to setup environment variables similar to docker environment
set -a
source .env
set +a

export PYTHONPATH=memas:memas_client:memas_sdk
