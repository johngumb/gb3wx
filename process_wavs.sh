#!/bin/bash

DATADIR=$(eval echo $(cat ~/gb3wx/datadir))

iswav()
{
    file=$1

     [ "${file##*.}" = "wav" ]
}

recdir=$(python gb3wx-record.py --querydir)

if [ -d ${recdir} ]; then
    find ${recdir}  | while read fname; do
        if iswav ${fname}; then
            if ./wav2mp3.sh ${fname}; then
                rm -f ${fname}
            fi
        fi
    done
fi

