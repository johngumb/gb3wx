import sys
from fcntl import  ioctl
from termios import (
    TIOCMIWAIT,
    TIOCM_DSR,
    TIOCM_CTS,
    TIOCM_CD
)
import os
import subprocess
import time
import string
import datetime
import serial

#
# 1 second for debounce
#
global g_debounce_time
g_debounce_time=0.2

#
# (modified) USB serial pinout
#
# red   DCD
# black GND
# white DTR
# green DSR
# yellow RTS
# blue   CTS
#
# originally TxD was green, RxD was white
# 
def ledtest(ser):
    while True:
        time.sleep(1)
        ser.setDTR(True)
        ser.setRTS(False)
        time.sleep(1)
        ser.setDTR(False)
        ser.setRTS(True)


global g_wait_signals
g_wait_signals = (TIOCM_DSR | TIOCM_CTS | TIOCM_CD)

def get_qso_signals(ser):
    dsr = ser.getDSR()
    cts = ser.getCTS()

    return (dsr, cts)

def wait_for_qso_start(ser):
    print "wait for qso start"

    global g_wait_signals
    global g_debounce_time

    #
    # wait for status change
    #
    while True:
        ioctl(ser.fd, TIOCMIWAIT, g_wait_signals)
        print "DSR",ser.getDSR()
        print "CTS",ser.getCTS()    
        print "DCD",ser.getCD()
        print "wait_for_qso_start: change detected"

        #
        # debounce
        #
        signals = get_qso_signals(ser)

        time.sleep(g_debounce_time)

        newsignals = get_qso_signals(ser)

        if newsignals == oldsignals:
            dsr = ser.getDSR()
            cts = ser.getCTS()
            dcd = ser.getCD()
            print "DSR",dsr
            print "CTS",cts
            print "DCD",dcd
            if dsr and cts:
                #
                # HACK - bogus response
                # wait until we get just dsr or cts; dcd for debug
                #
                print "dsr and cts set, bogus response, re-arm"
            else:
                break
        
        
    result = None
    
    if dsr:
        result = "10_6"

    if cts:
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
    print "DCD",ser.getCD()
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

def dstdir_fname():
    # TODO set machine timezone to UTC


    t = datetime.datetime.utcnow()
    #t = utc_datetime_now()

    dstdirname = "%s_%s" % ( t.year, t.month)

    fname = dstdirname + "_" + "%02d_%02d_%02d_%02d" % (t.day, t.hour, t.minute, t.second)
    return (dstdirname, fname)

def start_record( direction ):
    DATA_DIR="/home/gb3wx/data"
    data_file="%s.wav" % direction

    (dstdir, fname) = dstdir_fname()

    fullpath = os.path.join(DATA_DIR,dstdir,fname+"_"+data_file)

    if not os.path.exists(os.path.dirname(fullpath)):
        os.makedirs(os.path.dirname(fullpath))

    try:
        f = open(os.path.join(fullpath), "wb")
    except IOError, err:
        print "IOERROR",err
        return

    with f:
        try:
            p = subprocess.Popen(['arecord','-fcd','-Dhw:1'], stdout=f, stderr=subprocess.PIPE)
        except OSError as e:
            print e.errno
            print e
            return
            

    return p

def stop_record(p):

    p.terminate()
    #p.kill()

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

        rec_handle = start_record(mode)

        print "recording"
        wait_for_qso_stop(ser)
        print "stopping recording"
        
        stop_record(rec_handle)


if __name__ == "__main__":
    main()



