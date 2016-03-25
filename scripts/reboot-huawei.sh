#!/bin/bash

SCRIPTS=$(cd `dirname $0`; pwd)
VENV="$SCRIPTS/../venv"

$VENV/bin/python $SCRIPTS/reboot.py
