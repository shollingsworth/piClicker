#!/usr/bin/env python
# -*- coding: utf-8 -*-
import __future__
import sys
import os
import logging
import subprocess
import signal
import json
import atexit
import argparse
import time
from wifi import Cell, Scheme # https://wifi.readthedocs.io/en/latest/scanning.html
import getpass

debug = False
no_timing = True

myuser = getpass.getuser()
if myuser != 'root':
    raise Exception("Error, I need to be run as root")

"""===================================================
globals / mostly static stuff on initial execution
==================================================="""
click_proc = None
normal_interval = 4 #seconds before it refreshs it's scan, if zero it will do realtime, but it sounds erratic
scan_speed_low = .01
mypath = os.path.dirname(os.path.abspath(__file__))
clicker_prog="{}/clicker.py".format(mypath)
config_fn = "{}/config.json".format(mypath)
runfile = "{}/runfile".format(mypath)
#this is log not linear hence the map, haven't found a good formula for
#this conversation
tmp_map = json.loads(open("{}/ref_dbm_map.json".format(mypath), 'r').read())
signal_map = {}
for i in tmp_map: signal_map[i.get('dbm')] = i.get('percentage')

"""===================================================
Static Engineering vars
==================================================="""
#ping time ranges 1000 to 10 (weak => strong)
rlow=1000
rhigh=10
#percentage taken from signal_map
elow=1
ehigh=100


if os.path.exists(runfile):
    running_pid = open(runfile, 'r').read().strip()
    raise Exception("Error, runfile: {} exist check if the pid  exists or remove".format(running_pid))
else:
    running_pid = os.getpid()
    fh = open(runfile, 'w')
    fh.write(str(running_pid))
    fh.close()

def getConfig():
    fh = open(config_fn, 'r')
    retval = json.load(fh)
    fh.close()
    return retval

def writeConfig(click_rate):
    fh = open(config_fn, 'w')
    vals = {}
    vals['adapter'] = adapter
    vals['bssid'] = bssid
    vals['click_rate'] = click_rate
    fh.write(json.dumps(vals, indent=5))
    fh.close()

def getBssid():
    config = getConfig()
    bssid_config=config.get('bssid')
    bssid_env = os.environ.get('TEST_BSSID')
    if bssid_env:
        if debug: print("using environment var")
        verifyAddress(bssid_env)
        return bssid_env
    elif bssid_config:
        if debug: print("using config file for address")
        verifyAddress(bssid_config)
        return bssid_config
    else:
        raise Exception("Error, bssid is not found in environment or config")

def getAdapter():
    config = getConfig()
    adapter=config.get('interface')
    if not adapter:
        raise Exception("Error, adapter is not set in config file: {}".format(config_fn))
    return adapter

def cleanUp():
    os.unlink(runfile)
    if click_proc:
        writeConfig(0)
        click_proc.kill()
    print("bye!")

def manipSpeedfile(num):
    if str(num) != str(current):
        writeConfig(num)
        os.kill(click_pid, signal.SIGHUP)
    else:
        print("no change...")

def getNum(sig):
    if not sig: return 0
    num = int(signal_map.get(str(sig)))
    #I knew my SCADA stuff would come in handy someday :-P
    calc_out=(((num - elow)*((rhigh - rlow)/(ehigh - elow))) + rlow)
    return calc_out

def getAddressSignal(match_address):
    cells = Cell.all(adapter)
    if len(cells) == 0:
        sys.stderr.write("Error, no scan results detected. Is the adapter plugged in?")
    for o in cells:
        bssid = o.address
        if bssid != match_address: continue
        ssid = o.ssid
        db = o.signal
        return db

def checkScantime(start,end):
    res = end - start
    if res <= scan_speed_low:
        raise Exception("Error, scan speed is much too low = '{}' low threshold = '{}' I see this when it's not actually scanning".format
            (res,scan_speed_low)
        )
    return res

def verifyAddress(address):
    ascii_ok = []
    ascii_ok.extend(range(65,71))
    ascii_ok.extend(range(48,58))
    if len(address.split(':')) != 6:
        raise Exception("invalid mac addres, octet length is {}".format(len(address.split(':'))))
    for c in list(address.replace(':','')):
        if ord(c) not in ascii_ok:
            raise Exception("Error, invalid character: {} in mac: {} (use all uppercase)".format(c,address))
    return True

if __name__ == '__main__':
    atexit.register(cleanUp)
    program_desc = "Run wireless audio ping scanner"
    parser = argparse.ArgumentParser(description=program_desc, add_help=True)
    parser.add_argument("adapter", help="wireless adapter used for scanning")
    parser.add_argument("bssid", help="wireless address you are looking for")
    args = parser.parse_args()
    """===================================================
    START MAIN
    ==================================================="""
    current = -1
    adapter=args.adapter
    bssid=args.bssid
    click_proc = subprocess.Popen([clicker_prog])
    click_pid = click_proc.pid
    writeConfig(0) #init config
    while True:
        start_time = time.time()
        if debug: print("using address: {}".format(bssid))
        sig = getAddressSignal(bssid)
        num = getNum(sig)
        print("signal raw: {} / translated: {}".format(str(sig),str(num)))
        manipSpeedfile(num)
        current = num
        if no_timing: continue #continue if we've disabled timing
        end_time = time.time()
        loop_time = checkScantime(start_time,end_time)
        remaining = normal_interval - loop_time
        if debug: print("timings:\n\tloop_time: {}\n\tremaining: {}".format(loop_time,remaining))
        if remaining > 0:
            if debug: print("iwlist sleeping: {}".format(remaining))
            time.sleep(remaining)
