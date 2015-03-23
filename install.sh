#!/bin/bash

set -e

if [ "$1" == "3" ]; then
    export VENV=$(pwd)/venv3
    pyvenv ${VENV}
else
    export VENV=$(pwd)/venv
    virtualenv ${VENV}
fi

source ${VENV}/bin/activate
pip install -r requirements.txt
pip install -e .

echo
echo "*** checkrainpi is now installed in ${VENV} ***"
