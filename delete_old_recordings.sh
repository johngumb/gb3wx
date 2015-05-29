#!/bin/bash

DATADIR=$(eval echo $(cat ~/gb3wx/datadir))
LIMIT="6 months"
TESTFILE=/tmp/testfile
delete_oldstuff()
{
    touch -d -"${LIMIT}" ${TESTFILE}
    find ${DATADIR} -type f  | while read fname; do
        if [ ${fname} -ot ${TESTFILE} ]; then
            echo "${fname} too old"
            rm -f ${fname}
        fi
    done
    rm -f ${TESTFILE}

    find ${DATADIR} -type d | while read directory; do
        if [ -z "$(ls ${directory})" ]; then
            echo "${directory} is empty"
            rmdir ${directory}
        fi
    done
}

delete_oldstuff
