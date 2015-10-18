#!/bin/bash
#
execfile=/home/gb3wx/gb3wx/gb3wx-record.py

while true; do
    /usr/bin/python ${execfile} > /tmp/gb3wx-record.py 2>&1
    record_rc=$?
    echo "$(date) $(basename ${execfile}) exited rc ${record_rc}"
    sleep 10
done
