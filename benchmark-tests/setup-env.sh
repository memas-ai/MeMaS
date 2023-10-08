#!/bin/bash
pip install -r requirements.txt
# TODO: remove this after beam/datasets package upgrade 
pip install --no-deps -r requirements-no-deps.txt