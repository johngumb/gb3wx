#!/bin/bash

#home=gumb.dyndns.org
#fwport=11000
#remport=11000
user=gb3wx
home=g8nxjpi
fwport=22
remport=11000
keepflag="/tmp/keeptunnel"

#
# localhost here refers to localhost on the machine this script
# is running on
#
start()
{
    /usr/bin/ssh -p ${fwport} -R ${remport}:localhost:22 ${user}@${home} -nNT -f
}

stop()
{
    if [ ! -f ${keepflag} ]; then
        pid=$(ps aux | grep ssh | grep ${remport} | awk '{print $2}')
        if [ -n "${pid}" ]; then
            kill ${pid}
        fi
    fi
}

case $1 in
    start) start
        ;;
    stop) stop
        ;;
esac