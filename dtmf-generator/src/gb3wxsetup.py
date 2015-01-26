import sys
import os
import subprocess
import time
import string
import datetime
import serial

if __name__=="__main__":
    
    serport = '/dev/ttyUSB0'

    ser = serial.Serial(serport)

    if len(sys.argv) > 1:
        val = True
    else:
        val = False

    start=2730
    for i in range(start, 100000):
        ser.setRTS(True)
        hstr=repr(i)
        #hstr="0421"

        #p = subprocess.Popen(['./dtmfgen','-dplughw:1','-k%s' % hstr, '-t50'])
        #p.wait()
        time.sleep(0.7)
        ser.setRTS(False)
        time.sleep(0.4)

        
                             
