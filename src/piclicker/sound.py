#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
from state_instance import STATE
import util
from subprocess import Popen, PIPE
import state
import plog
import binaries
LOG = plog.logging.getLogger(__name__)
LOG.setLevel(plog.DEFAULT_LOG_LEVEL)

CLICK_RATE_MULTIPLIER = .002


class SoundController(object):
    def __init__(self):
        self.state = STATE

    def say(self, text):
        opts = [
            # voice
            '-v',
            'english-us',
            # speed
            '-s',
            '150',
            # pitch
            '-p',
            '20',
            '"{}"'.format(text),
        ]
        cmd_arr = [binaries.espeak] + opts
        p = Popen(cmd_arr, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        rc = p.returncode
        if rc != 0:
            raise Exception("\n".join([
                "Error running command: {}".format(" ".join(cmd_arr)),
                "Return code: {}".format(rc),
                "STDERR:\n{}".format(err),
                "STDOUT:\n{}".format(output),
            ]))
        return [output, err, rc]

    def aplay_sound(self, snd=None):
        if snd:
            cmd_arr = [binaries.aplay, snd]
        else:
            cmd_arr = [util.which('aplay'), self.state.wavefile]
        # p = Popen(cmd_arr, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        p = Popen(cmd_arr, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        rc = p.returncode
        if rc != 0:
            raise Exception("\n".join([
                "Error running command: {}".format(" ".join(cmd_arr)),
                "Return code: {}".format(rc),
                "STDERR:\n{}".format(err),
                "STDOUT:\n{}".format(output),
            ]))
        return [output, err, rc]

    def play_interp(self, val):
        if not val:
            raise ValueError("Wave Value is not set")
        if val.startswith(util.SAY_PREFIX):
            text = val.replace(util.SAY_PREFIX, '')
            self.say(text)
        else:
            self.aplay_sound(val)

    def main(self):
        while True:
            while self.state.queue_sound:
                snd = self.state.queue_pop()
                self.play_interp(snd)
            click_rate = self.state.click_rate
            mysleep = self.state.sleep_rate
            if self.state.wavefile == state.SOUND_CLICK:
                mysleep = click_rate * CLICK_RATE_MULTIPLIER
            self.play_interp(self.state.wavefile)
            time.sleep(mysleep)
