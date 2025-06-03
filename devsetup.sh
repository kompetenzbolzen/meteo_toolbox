#!/bin/bash

VENV="python -m virtualenv"

rm -rf venv/
$VENV venv
source venv/bin/activate

pip install ipython
pip install --editable .
