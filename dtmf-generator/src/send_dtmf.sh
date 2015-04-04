#!/bin/bash

send_dtmf()
{
local del=8
echo $2
./dtmfgen -drate_convert -k$1 -t100
sleep ${del}
if [ -n "$2" ]; then
    echo
fi
}
