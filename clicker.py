#!/usr/bin/env python
# -*- coding: utf-8 -*-
import __future__ 
import sys
import wave
import time
import alsaaudio
import signal
import json
import os

debug=False

def handler(signum, frame):
    if debug: print("Signal {} received.".format(signum))
    os.execv(__file__, sys.argv)
mypath = os.path.dirname(os.path.abspath(__file__))
signal.signal(signal.SIGHUP, handler)

config_fn = "{}/config.json".format(mypath)
config = json.load(open(config_fn, 'r'))

if debug: print("My process is: {}".format(os.getpid()))
clickfile="{}/snd_click.wav".format(mypath)
nopefile="{}/snd_whitenoise.wav".format(mypath)
errorfile="{}/snd_laugh.wav".format(mypath)
default_sleep = 2
nope = False

if config.get('click_rate') is None:
    raise Exception("Error, click rate could not be determined from file: {}".format(config_fn))

sleep = int(config.get('click_rate'))
if debug: print("Sleep Val: {}".format(sleep))
if sleep < 0:
    nope = True
    wavefile=errorfile
elif sleep == 0:
    nope = True
    wavefile=nopefile
else:
    wavefile=clickfile

__min_sleep__ = 10
sleep_wait = sleep * .001

def setdev(device, wavefile):    
    f = getNewWave(wavefile)
    if debug: print('%d channels, %d sampling rate\n' % (f.getnchannels(),f.getframerate()))
    # Set attributes
    device.setchannels(f.getnchannels())
    device.setrate(f.getframerate())
    # 8bit is unsigned in wav files
    if f.getsampwidth() == 1:
        device.setformat(alsaaudio.PCM_FORMAT_U8)
    # Otherwise we assume signed data, little endian
    elif f.getsampwidth() == 2:
        device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    elif f.getsampwidth() == 3:
        device.setformat(alsaaudio.PCM_FORMAT_S24_LE)
    elif f.getsampwidth() == 4:
        device.setformat(alsaaudio.PCM_FORMAT_S32_LE)
    else:
        raise ValueError('Unsupported format')
    f.close()

def playfile(device,wavefile):
    f = getNewWave(wavefile)
    periodsize = f.getframerate() / 8
    data = f.readframes(periodsize)
    while data:
        # Read data from stdin
        device.write(data)
        #data = f.readframes(320)
        data = f.readframes(periodsize)
    f.close()

def getNewWave(wavefile):
    return wave.open(wavefile, 'rb')

"""===================================================
BEGIN
==================================================="""
device = alsaaudio.PCM(mode=alsaaudio.PCM_NONBLOCK)
setdev(device,wavefile)
while True:
    wf = getNewWave(wavefile)
    if not nope:
        time.sleep(sleep_wait)
    else:
        time.sleep(default_sleep)
    playfile(device, wavefile)
