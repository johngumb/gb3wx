import sys
from serial import Serial
from fcntl import  ioctl
from termios import (
    TIOCMIWAIT,
    TIOCM_DSR,
    TIOCM_CTS
)

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

def main():
    serport = '/dev/ttyUSB0'

    ser = Serial(serport)

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



