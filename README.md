# CheckRainPi -- a rainwater gauge data collection script

This is an easy script for collecting results off the serial port and
sending them out to Amazon SimpleDB.

## How it works

The script sends the memory dump command to a rainwater gauge attached
to the serial port.

It collects the results and stores them in a file.

It then posts just the latest results to a database in the Amazon
cloud.

The results can be retrieved at any time by accessing the Amazon
SimpleDB.

This script is ideal for running on a Raspberry Pi.


## Installation

First get python3 and git.

    sudo apt-get install python3 python3-virtualenv git

The following commands will create a python virtualenv and install the
script into it.

    git clone https://github.com/rvl/checkrainpi.git
    cd checkrainpi
    ./install.sh


## Configuration

Find the file `raingauge.conf` and edit it to your tastes.

In particular, you will need to go to http://aws.amazon.com/ and sign
up for a free account, so you can enter your access key into the
config file.


## Invocation

    ./venv/bin/checkrain -v --conf=raingauge.conf


## Getting results

This will print out all the samples collected so far.

    ./venv/bin/getrain --conf=raingauge.conf


## Running automatically

Put the following in a file `/etc/cron.d/checkrainpi`.

It will run the script every day at 4PM.

    SHELL=/bin/sh
    PATH=/bin:/usr/bin

    0 16 * * *  pi /home/pi/checkrainpi/venv/bin/checkrain --conf=/home/pi/checkrainpi/raingauge.conf
