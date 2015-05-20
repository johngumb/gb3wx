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
    s_serial_device_name = "/dev/ttyUSB0"
    s_serial = serial.Serial(s_serial_device_name)

    def __init__(self, signal_detect, tx_on, rx_audiofile ):
        self.m_signal_detect = signal_detect
        self.m_tx_on = tx_on
        self.m_rx_audiofile = rx_audiofile
        self.s_serial.setDTR(False)
        self.s_serial.setRTS(False)
        return

    def start_playback(self):

        f = open(os.path.join(self.m_rx_audiofile), "rb")

        with f:

            handle = subprocess.Popen(['aplay','-Dplughw:2'], stdin=f, stderr=subprocess.PIPE)

        return handle

    def stop_playback(self, handle):
        handle.terminate()
        status = handle.communicate()
        retcode = handle.wait()
        return retcode

    def spoof_signal_received(self,period=4):
        if self.m_signal_detect=="DTR":
            self.s_serial.setDTR(True)
        elif self.m_signal_detect=="RTS":
            self.s_serial.setRTS(True)
        else:
            assert(False)
        
        h = self.start_playback()

        for i in range(int(period*10)):
            print self.s_serial.getDSR(), self.s_serial.getCTS()
            time.sleep(0.1)

        self.stop_playback(h)

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
    l="../lefttest16.wav"
    r="../righttest16.wav"
    t_6_metre = TestRadio("DTR","DSR",l)

    t_10_metre = TestRadio("RTS","CTS",r)

    ser = t_6_metre.get_serial_device()

    print "stabilising..."


    while ser.getDSR() or ser.getCTS():
        time.sleep(1)
        print "stabilising..."

    n = 1
    print "sleep %d" % n
    time.sleep(n)

    testrig = t_6_metre
    testrig2 = t_10_metre

    if testrig == t_6_metre:
        print "open 6 to 10"
    else:
        print "open 10 to 6"

    testrig.spoof_signal_received(5)

    time.sleep(2)

    print "first over"
    testrig.spoof_signal_received(20)

    print "second over"
    testrig2.spoof_signal_received(20)

    time.sleep(2)

    print "third over"
    testrig.spoof_signal_received(20)

    time.sleep(2)

    print "fourth over"
    testrig2.spoof_signal_received(20)

    while True:
        print ser.getDSR(), ser.getCTS()
        time.sleep(1)

if __name__ == "__main__":
    main()



