#!/bin/bash

DATADIR=$(eval echo $(cat ~/gb3wx/datadir))

iswav()
{
    file=$1

     [ "${file##*.}" = "wav" ]
}

recdir=${DATADIR}

if [ -d ${recdir} ]; then
    find ${recdir}  | while read fname; do
        if iswav ${fname}; then
            if $(dirname $0)/wav2mp3.sh ${fname}; then
                rm -f ${fname}
            fi
        fi
    done
fi

