import sys
from serial import Serial
from fcntl import  ioctl
from termios import (
    TIOCMIWAIT,
    TIOCM_RNG,
    TIOCM_DSR,
    TIOCM_CD,
    TIOCM_CTS
)

g_wait_signals = (TIOCM_DSR |
                TIOCM_CTS)

def wait_for_qso_start():
    global g_wait_signals

    ioctl(ser.fd, TIOCMIWAIT, wait_signals)
    dsr = ser.getDSR()
    dtr = ser.getCTS()

    result = None
    
    if dsr:
        result = "10_6"

    if dtr:
        result = "6_10"

    return result

def wait_for_inactivity():
    wait_for_qso_stop()

def wait_for_qso_stop():
    global g_wait_signals
    ioctl(ser.fd, TIOCMIWAIT, wait_signals)
    ser.getDSR()
    ser.getCTS()

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

        rec_handle = start_thread(start_record, mode)

        wait_for_qso_stop(ser)

        stop_record(rec_handle)


if __name__ == "__main__":
    main()



