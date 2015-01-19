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

class TestRadio:
    s_serial_device_name = "/dev/ttyUSB1"
    s_serial = serial.Serial(s_serial_device_name)

    def __init__(self, signal_detect, tx_on ):
        self.m_signal_detect = signal_detect
        self.m_tx_on = tx_on
        self.s_serial.setDTR(False)
        self.s_serial.setRTS(False)
        return

    def spoof_signal_received(self,period=4):
        if self.m_signal_detect=="DTR":
            self.s_serial.setDTR(True)
        elif self.m_signal_detect=="RTS":
            self.s_serial.setRTS(True)
        else:
            assert(False)
        
        time.sleep(period)

        if self.m_signal_detect=="DTR":
            self.s_serial.setDTR(False)
        elif self.m_signal_detect=="RTS":
            self.s_serial.setRTS(False)
        else:
            assert(False)

    def get_serial_device(self):
        return self.s_serial
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
global g_wait_signals
g_wait_signals = (TIOCM_DSR | TIOCM_CTS | TIOCM_CD)
def main():
    t_6_metre = TestRadio("DTR","DSR")

    t_10_metre = TestRadio("RTS","CTS")

    ser = t_6_metre.get_serial_device()

    print "stabilising..."

    time.sleep(1)

    while ser.getDSR() or ser.getCTS():
        time.sleep(1)
        print "stabilising..."

    testrig = t_6_metre
    testrig2 = t_10_metre

    if testrig == t_6_metre:
        print "open 6 to 10"
    else:
        print "open 10 to 6"

    testrig.spoof_signal_received()

#    t_10_metre = TestRadio("RTS","CTS")
#    t_10_metre.spoof_signal_received()

    for i in range(14):
        print ser.getDSR(), ser.getCTS()
        time.sleep(1)

    print "first over"
    testrig.spoof_signal_received(20)

    time.sleep(1)

#    while True:
#        print ser.getDSR(), ser.getCTS()
#        time.sleep(1)

    print "second over"
    testrig2.spoof_signal_received(20)

    while True:
        print ser.getDSR(), ser.getCTS()
        time.sleep(1)

if __name__ == "__main__":
    main()



