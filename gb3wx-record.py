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
import threading

global g_debounce_time
g_debounce_time=0.5 # seconds

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
    for i in range(5):
        time.sleep(1)
        ser.setDTR(True)
        ser.setRTS(False)
        time.sleep(1)
        ser.setDTR(False)
        ser.setRTS(True)
    #
    # Leave with both LEDs extinguished
    #
    ser.setDTR(False)
    ser.setRTS(False)


class LED:
    def __init__(self, ser, colour):
        self.m_colour = colour
        self.m_serial = ser
        self.m_state = "init"

        self.m_funcmap={}
        self.m_funcmap["red"]=self.m_serial.setDTR
        self.m_funcmap["green"]=self.m_serial.setRTS
        assert (colour in self.m_funcmap.keys())

        self.set_state(self.m_state)

        return

    def set_state(self, state):
        if state == self.m_state:
            return

        self.m_state = state
        if state == "on":
            self.m_funcmap[self.m_colour](True)
        elif state == "off":
            self.m_funcmap[self.m_colour](False)
        else:
            assert(False and "bad led state")

        print self.m_colour, "LED", self.m_state

        return

    def get_state(self):
        return self.m_state
    

global g_wait_signals
g_wait_signals = (TIOCM_DSR | TIOCM_CTS | TIOCM_CD)

def get_qso_signals(ser):
    dsr = ser.getDSR()
    cts = ser.getCTS()
    dcd = ser.getCD()
    return (dsr, cts, dcd)

def wait_for_qso_start(ser):
    print "wait for qso start"

    global g_wait_signals
    global g_debounce_time

    #
    # wait for status change
    #
    while True:

        (dsr, cts, dcd) = get_qso_signals(ser)

        #
        # qso happening already? (dsr XOR cts)
        # if not then wait for change
        #
        if dsr == cts and (not dcd):
		ioctl(ser.fd, TIOCMIWAIT, g_wait_signals)

        (dsr, cts, dcd) = get_qso_signals(ser)
        print "DSR",dsr
        print "CTS",cts
        print "DCD",dcd
        print "wait_for_qso_start: change detected"

        #
        # debounce
        #
        signals = get_qso_signals(ser)

        time.sleep(g_debounce_time)

        newsignals = get_qso_signals(ser)

        test = False

        if newsignals == signals:
            (dsr, cts, dcd) = signals

            print "DSR",dsr
            print "CTS",cts
            print "DCD",dcd

            if dcd:
                #
                # test result takes precedence over rig signalling
                #
                test = True
                break

            elif dsr and cts:
                #
                # HACK - bogus response
                # wait until we get just dsr or cts; dcd for debug
                #
                print "dsr and cts set, bogus response, re-arm"
            elif (not dsr) and (not cts):
                #
                # HACK - bogus response
                # wait until we get just dsr or cts; dcd for debug
                #
                print "dsr and cts clear, bogus response, re-arm"
            else:
                #
                # either dsr or cts is active - a qso is
                # happening one way or the other
                #
                break
        else:
            print "debounce: %s did not match %s" % (newsignals,signals)
        
    result = None
    
    if dsr:
        result = "6_10"

    if cts:
        result = "10_6"

    if test:
        result = "test"

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

def ensure_record_stopped():
    os.system("/usr/bin/pgrep arecord > /dev/null && /usr/bin/killall arecord")

def dstdir_fname():
    # TODO set machine timezone to UTC

    t = datetime.datetime.utcnow()

    dstdirname = "%04d_%02d" % ( t.year, t.month)

    fname = dstdirname + "_" + "%02d_%02d_%02d_%02d" % (t.day, t.hour, t.minute, t.second)
    return (dstdirname, fname)

def data_dir():
    DATA_DIR_FILE=os.path.expanduser("~/gb3wx/datadir")
    DATA_DIR=os.path.expanduser(open(DATA_DIR_FILE).read()).strip()

    return DATA_DIR

def start_record( direction ):

    ensure_record_stopped()

    data_file="%s.wav" % direction

    (dstdir, fname) = dstdir_fname()

    fullpath = os.path.join(data_dir(),dstdir,fname+"_"+data_file)

    if not os.path.exists(os.path.dirname(fullpath)):
        os.makedirs(os.path.dirname(fullpath))

    try:
        f = open(os.path.join(fullpath), "wb")
    except IOError, err:
        print "IOERROR",err
        return

    with f:
        try:
            p = subprocess.Popen(['arecord','-fcd','-Dhw:0'], stdout=f, stderr=subprocess.PIPE)
            print "/usr/bin/chrt -r -p 99 %s" % p.pid
            os.system("/usr/bin/chrt -r -p 99 %s" % p.pid)
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

    ensure_record_stopped()

    return

def main():
    serport = '/dev/ttyUSB0'

    ser = serial.Serial(serport)

    green_led = LED(ser, "green")

    red_led = LED(ser, "red")

    green_led.set_state( "off" )
    red_led.set_state( "off" )

     # TODO set volume using amixer on boot

    if not ser:
        print >> sys.stderr, "serial port %s not found" % serport
        sys.exit(1)

    wait_for_inactivity(ser)

    #
    # TODO write a file per day which provides a summary of activity
    # eg. total minutes active 10/6 and 6/10
    #
    while True:

        mode = wait_for_qso_start(ser)

        if mode == "test":
            ledtest(ser)
        else:
            qso_stop_thread = threading.Thread(target=wait_for_qso_stop,args=(ser,))
            qso_stop_thread.start()

            rec_handle = start_record(mode)

            if mode == "10_6":
                led = red_led
            elif mode == "6_10":
                led = green_led
            else:
                assert ( False )

            led.set_state( "on" )
            print "recording"
            #wait_for_qso_stop(ser)
            qso_stop_thread.join()

            print "stopping recording"

            stop_record(rec_handle)
            led.set_state( "off" )

if __name__ == "__main__":
    main()



