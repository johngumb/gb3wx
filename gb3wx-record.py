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
import logging
import logging.handlers

global g_logger

global g_debounce_time
g_debounce_time=0.05 # seconds

def log(logger, msg):
    do_print = False

    if do_print:
        print msg

    logger(msg)
    return
    
def get_logger():
    log = logging.getLogger(__name__)

    log.setLevel(logging.DEBUG)

    #handler = logging.handlers.SysLogHandler(address = '/dev/log')
    mb = 1000000

    fn = os.path.join(os.path.expanduser("~"),"log/gb3wx-record.log")
    handler = logging.handlers.RotatingFileHandler(fn, maxBytes=mb, backupCount=10)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)

    log.addHandler(handler)

    return log

def get_ofcom_logger():
    log = logging.getLogger("gb3wx")

    log.setLevel(logging.INFO)

    fn = os.path.join(os.path.expanduser("~"),"log/gb3wx-activity.log")

    handler = logging.handlers.TimedRotatingFileHandler(fn, when = 'w6', interval = 1, backupCount=100)

    formatter = logging.Formatter('%(asctime)s %(message)s')

    handler.setFormatter(formatter)

    log.addHandler(handler)

    return log
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
def ledpattern(ser, cycles, msg=""):
    if msg:
        log(g_logger.info, "%s led pattern" % msg)

    for i in range(cycles):
        time.sleep(0.5)
        ser.setDTR(True)
        ser.setRTS(False)
        time.sleep(0.5)
        ser.setDTR(False)
        ser.setRTS(True)
    #
    # Leave with both LEDs extinguished
    #
    ser.setDTR(False)
    ser.setRTS(False)

class Watchdog(threading.Thread):
    def __init__(self):
        threading.Thread.__init__ (self)
        self.m_last_activity = datetime.datetime.now()
        self.m_qso_active = False
        return

    # TODO synchronise properly
    def activity(self):
        global g_logger

        self.m_last_activity = datetime.datetime.now()

        return

    # TODO synchronise properly
    def qso_active(self):
        global g_logger

        self.m_qso_active = True

        return

    # TODO synchronise properly
    def qso_stopped(self):
        global g_logger

        self.m_qso_active = False

        return

    def rebootcontroller(self):
        global g_logger

        log(g_logger.info, "rebooting controller...")

        p = subprocess.Popen(["./rebootcontroller.sh"], cwd="/home/gb3wx/gb3wx/dtmf-generator/src", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        status = p.communicate()
        log(g_logger.info, "reboot controller communicate status %s" % repr(status))

        retcode = p.wait()
        log(g_logger.info,"reboot controller retcode %d" % retcode)

        return

    def run(self):
        global g_logger
        log(g_logger.info, "watchdog started")

        while True:
            timediff = datetime.datetime.now() - self.m_last_activity

            if timediff.seconds > 600 and not self.m_qso_active:
                self.rebootcontroller()

            # TODO don't reboot too frequently
            time.sleep(60)

        return

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

        log(g_logger.info, "%s LED %s" % (self.m_colour, self.m_state))

        return

    def get_state(self):
        return self.m_state
    

global g_wait_signals
g_wait_signals = (TIOCM_DSR | TIOCM_CTS | TIOCM_CD)

global g_qso_signals
g_qso_signals={}

def get_qso_signals(ser, reason=""):
    global g_qso_signals
    s = g_qso_signals
    keys = ["DSR", "CTS", "DCD"]

    result = [ s[sig]() for sig in keys ]

    msg = "get_qso_signals: %s " % reason
    for (sig,val) in zip(keys, result):
        msg += "%s %s " % (sig, repr(val))

    if reason:
        log(g_logger.info, msg.strip())

    return result

def wait_for_qso_start(ser):
    log(g_logger.info, "wait for qso start")

    global g_wait_signals
    global g_debounce_time

    #
    # wait for status change
    #
    while True:

        (dsr, cts, dcd) = get_qso_signals(ser, "start loop")

        #
        # qso happening already? (dsr XOR cts)
        # if not then wait for change
        #
        if dsr == cts and not dcd:
            log(g_logger.info, "waiting for activity")
            ioctl(ser.fd, TIOCMIWAIT, g_wait_signals)
        else:
            log(g_logger.info,"activity already happening")

        #
        # debounce
        #
        signals = get_qso_signals(ser, "activity detected")

        #
        # sample signals
        #
        unstable = 0
        for i in range(5):
            newsignals = get_qso_signals(ser, "stability check")
            if signals != newsignals:
                unstable += 1
            time.sleep(g_debounce_time)
        #
        # check for stability
        #
        if unstable > 1:
            log(g_logger.info,"qso signals did not stabilise: %d values" % unstable)
            #
            # wait for inactivity
            #
            count = 0
            while count < 1000:
                stopsignals = get_qso_signals(ser, "stability inactivity check")
                if stopsignals == [False, False, False]:
                    log(g_logger.info,"stability inactivity check passed attempt %d" % count)
                    break
                time.sleep(g_debounce_time)
                count += 1
        else:
            newsignals = get_qso_signals(ser, "after  debounce")

            if newsignals == signals:
                (dsr, cts, dcd) = signals

                if dcd:
                    #
                    # tx active on both rigs
                    #
                    break

                elif dsr and cts:
                    #
                    # HACK - bogus response
                    # wait until we get just dsr or cts; dcd for debug
                    #
                    log(g_logger.info, "dsr and cts set, re-arm")
                elif (not dsr) and (not cts):
                    #
                    # HACK - bogus response
                    # wait until we get just dsr or cts; dcd for debug
                    #
                    log(g_logger.info,"dsr and cts clear, re-arm")
                else:
                    #
                    # either dsr or cts is active - a qso is
                    # happening one way or the other
                    #
                    break
            else:
                log(g_logger.info,"debounce: %s did not match %s" % (newsignals,signals))
        
    result = None
    
    if dsr:
        result = "6_10"

    elif cts:
        result = "10_6"

    elif dcd:
        result = "bothtx"

    return result

def wait_for_inactivity(ser):
    dsr = ser.getDSR()
    dtr = ser.getCTS()

    if not dsr and not dtr:
        return

    wait_for_qso_stop(ser)

def wait_for_qso_stop(ser, loop):
    log(g_logger.info, "wait for qso stop loop %d" % loop)
    global g_wait_signals
    ioctl(ser.fd, TIOCMIWAIT, g_wait_signals)

    get_qso_signals(ser, "wait for qso stop loop %d" % loop)

    return

def wait_for_beacon_stop(ser, loop, maxwait):
    log(g_logger.info, "wait for beacon stop loop %d" % loop)

    for i in range((maxwait+5)*5):
        (dsr, cts, dcd) = get_qso_signals(ser)
        time.sleep(0.2)
        if not dcd:
            break
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
    global g_logger

    # TODO set machine timezone to UTC

    t = datetime.datetime.utcnow()

    dstdirname = "%04d_%02d" % ( t.year, t.month )

    # horrible hack if ntp hasn't come up
    if t.year==1970:
        log(g_logger.info, "no ntp: %s" % dstdirname )
        dstdirname = "2015_11"

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

    log(g_logger.info, "recording %s" % fullpath)

    try:
        f = open(os.path.join(fullpath), "wb")
    except IOError, err:
        log(g_logger.error, "IOERROR: " + repr(err))
        return

    with f:
        try:
            p = subprocess.Popen(['arecord','-fcd','-Dhw:0'], stdout=f, stderr=subprocess.PIPE)
            log(g_logger.info, "/usr/bin/chrt -r -p 99 %s" % p.pid)
            os.system("/usr/bin/chrt -r -p 99 %s" % p.pid)
        except OSError as e:
            log(g_logger.info, e.errno)
            log(g_logger.info, repr(e))
            return
            

    return p

def stop_record(p):

    p.terminate()

    status = p.communicate()
    log(g_logger.info, "stop record communicate status %s" % repr(status))

    retcode = p.wait()
    log(g_logger.info,"stop record retcode %d" % retcode)

    ensure_record_stopped()

    return

def play_last_recording():
    global g_logger
    (dstdir_dirname,_) = dstdir_fname()

    fq_dstdir_dirname = os.path.join(data_dir(), dstdir_dirname)

    # there may be no recordings
    if not os.path.exists(fq_dstdir_dirname):
        log(g_logger.info,"play_last_recording: %s does not exist" % fq_dstdir_dirname)
        return

    if len(os.listdir(fq_dstdir_dirname)) == 0:
        log(g_logger.info,"play_last_recording: %s is empty" % fq_dstdir_dirname)
        return

    mtime = lambda f: os.stat(os.path.join(fq_dstdir_dirname, f)).st_mtime

    play_fn=list(sorted(os.listdir(fq_dstdir_dirname), key=mtime))[-1]

    full_play_fn = os.path.join(fq_dstdir_dirname, play_fn)

    play_ext = play_fn.split('.')[1]

    if play_ext == "mp3":
        playcmd = "/usr/local/bin/lame --silent --decode %s - | /usr/bin/aplay -Fcd -Dplughw:0 2>/dev/null" % full_play_fn
    elif play_ext == "wav":
        playcmd = "/usr/bin/aplay -Fcd -Dplughw:0 %s 2>/dev/null" % full_play_fn

    log(g_logger.info, "play last recording: %s" % playcmd)

    os.system(playcmd)

    return

def sysuptime():
    from datetime import timedelta

    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime_string = str(timedelta(seconds = uptime_seconds))

    return uptime_string

def main():
    global g_logger

    # 180 seconds max allowed time for an over
    NHRC_TIMEOUT = 180

    # seconds minimum before both rigs on tx is classed
    # as a beacon
    MIN_BEACON_TIME = 5

    # maximum seconds allowed for a beacon
    MAX_BEACON_TIME = 30

    g_logger = get_logger()

    ofcom_logger = get_ofcom_logger()

    log(g_logger.info, "gb3wx-record startup, sysuptime " + sysuptime())

    serport = '/dev/ttyUSB0'

    ser = serial.Serial(serport)

    watchdog = Watchdog()

    watchdog.start()

    green_led = LED(ser, "green")

    red_led = LED(ser, "red")

    green_led.set_state( "off" )
    red_led.set_state( "off" )

    if not ser:
        log(g_logger.critical,"serial port %s not found" % serport)
        sys.exit(1)

    wait_for_inactivity(ser)

    ofcom_logger.info("System start")

    # show we've started
    ledpattern(ser,5,"startup")

    for (sig,fn) in zip([ "DSR", "CTS", "DCD" ], [ser.getDSR, ser.getCTS, ser.getCD]):
        g_qso_signals[sig] = fn

    loop = 0
    while True:

        loop += 1

        mode = wait_for_qso_start(ser)

        if mode == "bothtx":
            beaconstart = datetime.datetime.now()

            #
            # if both rigs are beaconing there's no point
            # looking for a qso as both are transmitting
            # so block waiting here for that condition to
            # clear
            #
            beacon_stop_thread = threading.Thread(target=wait_for_beacon_stop,args=(ser, loop, MAX_BEACON_TIME))

            beacon_stop_thread.start()

            beacon_stop_thread.join(timeout=MAX_BEACON_TIME)

            beacon_duration = datetime.datetime.now() - beaconstart

            if beacon_duration.seconds > MIN_BEACON_TIME:
                ledtest_thread = threading.Thread(target=ledpattern,args=(ser,2))
                ledtest_thread.start()
                log(g_logger.info, "beacon detected: %d seconds" % beacon_duration.seconds)
                watchdog.activity()
            elif beacon_duration.seconds >= MAX_BEACON_TIME:
                log(g_logger.info, "max beacon time exceeded: %d seconds" % beacon_duration.seconds)
            else:
                log(g_logger.info, "beacon period too short for a real beacon: %d seconds" % beacon_duration.seconds)
        else:
            watchdog.qso_active()

            qso_stop_thread = threading.Thread(target=wait_for_qso_stop,args=(ser,loop))
            qso_stop_thread.start()

            rec_handle = start_record(mode)

            if mode == "10_6":
                led = red_led
            elif mode == "6_10":
                led = green_led
            else:
                assert ( False )

            led.set_state( "on" )

            log(g_logger.info, "recording")

            ofcom_logger.info("activity start " + mode)

            qso_stop_thread.join(timeout=NHRC_TIMEOUT+5)

            if qso_stop_thread.isAlive():
                log(g_logger.info, "transmit timeout - missed QSO stop")
                ofcom_logger.info("transmit timeout - missed QSO stop " + mode)
            else:
                log(g_logger.info, "QSO stopped")
                ofcom_logger.info("activity stop " + mode)

            stop_record(rec_handle)

            led.set_state( "off" )

            watchdog.qso_stopped()

if __name__ == "__main__":
    main()



