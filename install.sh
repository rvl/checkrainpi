#!/bin/bash

set -e

pyvenv venv
source ./venv/bin/activate
pip install -r requirements.txt
pip install -e .

echo
echo "*** checkrainpi is now installed in $(pwd)/venv ***"
