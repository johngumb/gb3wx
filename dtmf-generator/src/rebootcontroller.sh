#!/bin/bash

. ./send_dtmf.sh

echo $0
echo $(dirname $0)
ACFILE=$(dirname $0)/access
if [ -s ${ACFILE} ]; then
   ACCESS=$(cat ${ACFILE})
else
   echo "no access file"
   exit 1
fi

send_dtmf ${ACCESS}
send_dtmf \*\*
send_dtmf \#
send_dtmf \#
