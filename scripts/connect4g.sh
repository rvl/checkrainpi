#!/bin/sh

# This script causes the Telstra 4G dongle to connect if it's not
# currently connected.
# It works by sending a command to the ZTE web interface.

curl --silent -o /dev/null 'http://192.168.0.1/goform/goform_set_cmd_process?goformId=CONNECT_NETWORK'
