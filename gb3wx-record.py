import sys
from fcntl import  ioctl
from termios import (
    TIOCMIWAIT,
    TIOCM_DSR,
    TIOCM_CTS
)
import os
import subprocess
import time
import string
import datetime
import serial

#
# (modified) USB serial pinout
#
# red   +5V
# black GND
# white DTR
# green DSR
# yellow RTS
# blue   CTS
#
# originally TxD was green, RxD was white
# 
global g_wait_signals
g_wait_signals = (TIOCM_DSR | TIOCM_CTS)

def wait_for_qso_start(ser):
    print "wait for qso start"

    global g_wait_signals

    ioctl(ser.fd, TIOCMIWAIT, g_wait_signals)
    print "DSR",ser.getDSR()
    print "CTS",ser.getCTS()    
    print "QSO started"

    dsr = ser.getDSR()
    dtr = ser.getCTS()

    result = None
    
    if dsr:
        result = "10_6"

    if dtr:
        result = "6_10"

    # need to return TIOCM_DSR or TIOCM_CTS here
    # so we can wait for the appropriate one to
    # go away.
    return result

def wait_for_inactivity(ser):
    dsr = ser.getDSR()
    dtr = ser.getCTS()

    if not dsr and not dtr:
        return

    wait_for_qso_stop(ser)

def wait_for_qso_stop(ser):
    print "wait for qso stop"
    global g_wait_signals
    ioctl(ser.fd, TIOCMIWAIT, g_wait_signals)
    print "DSR",ser.getDSR()
    print "CTS",ser.getCTS()    
    print "QSO stopped"
    return

def open_result_file(filename, mode="r"):
    try:
        f = open(filename, mode)
    except IOError, err:
        yield None, err
    else:
        try:
            yield f, None
        finally:
            f.close()

def dstdir():
    # TODO set machine timezone to UTC

    DATA_DIR="/home/jag/data"
    t = datetime.datetime.utcnow()
    #t = utc_datetime_now()

    dstdirname = "%s_%s" % ( t.year, t.month)

    fname = dstdirname + "_" + "%02d_%02d_%02d_%02d" % (t.day, t.hour, t.minute, t.second)
    print dstdirname
    print fname

def test_audio():
    DATA_DIR="/home/jag/data"
    DATA_FILE="ss.wav"

    try:
        f = open(os.path.join(DATA_DIR,DATA_FILE), "wb")
    except IOError, err:
        print "IOERROR",err
        return

    with f:
        try:
            p = subprocess.Popen(['arecord','-fcd'], stdout=f, stderr=subprocess.PIPE)
        except OSError as e:
            print e.errno
            print e
            return
            
        time.sleep( 1 )
        p.terminate()
#        p.kill()

        status = p.communicate()
        print "communicate status", status


        retcode = p.wait()
        print "retcode", retcode

    return

def main():
#    dstdir()

#    return test_audio()

    serport = '/dev/ttyUSB0'

    ser = serial.Serial(serport)

     # TODO set volume using amixer on boot

    if not ser:
        print >> sys.stderr, "serial port %s not found" % serport
        sys.exit(1)

    while True:
        wait_for_inactivity(ser)

        mode = wait_for_qso_start(ser)

#        rec_handle = start_thread(start_record, mode)

        print "recording"
        wait_for_qso_stop(ser)
        print "stopping recording"
        
#        stop_record(rec_handle)


if __name__ == "__main__":
    main()



