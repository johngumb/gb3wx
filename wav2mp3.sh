#!/bin/bash

outtmp=/tmp/$(basename $1)

if [ ! -s $1 ]; then
    echo "$1 empty"
    exit 1
fi

sox $1 -b 16 ${outtmp} dither -s

soxrc=$?

if [ ${soxrc} -eq 0 ]; then
    lame -S -V2 ${outtmp} $(dirname $1)/$(basename $1 .wav).mp3
    retcode=$?
    rm -f ${outtmp}
else
    retcode=${soxrc}
fi

exit ${retcode}