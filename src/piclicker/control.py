#!/usr/bin/env python
# -*- coding: utf-8 -*-
import multiprocessing
import time
from state_instance import STATE
import sys
import state
from sound import SoundController
from signal_strength import SignalStrengthController
from interwebber import InterWebber
from crack import piCrack
import simpleweb
import plog
LOG = plog.logging.getLogger(__name__)
LOG.setLevel(plog.DEFAULT_LOG_LEVEL)

WEB_TIMEOUT = 5


class Controller(object):
    def __init__(self):
        self.snd_ctl = SoundController()
        self.sig_ctl = SignalStrengthController()
        self.int_ctl = InterWebber(WEB_TIMEOUT)
        self.high_polls = {}
        self.state = STATE

        self.interwebber = self.getproc(self.int_ctl.run, 'Internet Polling')
        self.sound = self.getproc(self.snd_ctl.main, 'Sound Controller')
        # start stuff in order, otherwise we'll the json may not load
        self.web = self.getproc(simpleweb.run, 'Simple Web Config')
        self.signal_strength = None

    def getproc(self, func, name):
        proc = multiprocessing.Process(target=func, name=name)
        return proc

    def start_signal(self):
        if not self.signal_strength or not self.signal_strength.is_alive():
            self.signal_strength = self.getproc(self.sig_ctl.run, 'Signal Controller')
            self.signal_strength.start()
            LOG.info("Signal Process started, pid: {}".format(self.signal_strength.pid))

    def stop_signal(self):
        if self.signal_strength:
            self.signal_strength.terminate()
            self.signal_strength = None
            LOG.info("Signal Process stopped")

    def start_crack(self):
        self.stop_signal()
        found_key = None
        try:
            with piCrack() as obj:
                obj.capture()
                found_key = obj.get_cracked()
                LOG.error("Found key: {}".format(found_key))
        except Exception:
            LOG.exception("Error, cracking")

        if found_key:
            self.state.queue_add(state.SOUND_DING_FRIES_ARE_DONE)
            self.state.bssid = None

    def check_daemons(self):
        if not self.sound.is_alive():
            raise Exception("Sound Daemon is not alive, aborting")
            self.hard_stop()
        if not self.web.is_alive():
            raise Exception("Web Daemon is not alive, aborting")
            self.hard_stop()

    def hard_stop(self):
        self.stop_signal()
        self.web.terminate()
        self.sound.terminate()
        sys.exit(-1)

    def poll_state(self):
        self.check_daemons()
        current_state = self.state.get_state()
        LOG.debug("current state: {}".format(current_state))
        # init -> config
        if current_state == state.MODE_INIT:
            self.state.call_trigger(state.TRIG_CONFIG)

        # config -> scan
        elif current_state == state.MODE_CONFIG:
            self.state.set_config_mode()
            self.state.call_trigger(state.TRIG_SCAN)

        # scan -> crack
        elif current_state == state.MODE_SCANNING:
            self.state.set_scan_mode()
            self.start_signal()
            self.state.call_trigger(state.TRIG_CRACK)

        # crack -> unknown
        elif current_state == state.MODE_CRACKING:
            self.state.set_crack_mode()
            self.start_crack()
            # force state change for now
            self.state.machine.set_state(state.MODE_CONFIG)

        else:
            raise ValueError("Unkown Condition in state: {}".format(current_state))
            self.hard_stop()

    def run(self):
        # get processes, start
        self.sound.start()
        LOG.info("Sound Process started, pid: {}".format(self.sound.pid))
        self.web.start()
        LOG.info("Web Process started pid: {}".format(self.web.pid))
        self.interwebber.start()
        LOG.info("Internet Monitor Process started pid: {}".format(self.interwebber.pid))
        while True:
            try:
                self.poll_state()
                time.sleep(self.state.polling_interval)
            except Exception:
                LOG.exception("Error during control polling")
                self.hard_stop()


if __name__ == '__main__':
    obj = Controller()
    obj.state.channel = 5
    obj.run()
