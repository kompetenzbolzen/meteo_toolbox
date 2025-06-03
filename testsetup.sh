#!/bin/bash

[ ! -f venv/bin/activate ] && python -m virtualenv venv
source venv/bin/activate

pip install IPython

pip install -e .
