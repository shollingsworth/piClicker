#!/usr/bin/env python
# -*- coding: utf-8 -*-
import plog
from state_instance import STATE
import time
import webfox
import state
import util
LOG = plog.logging.getLogger(__name__)
LOG.setLevel(plog.DEFAULT_LOG_LEVEL)

# grab wordlist / check if changed
# post status updates?
# check for internet connectivity
POLL_INTERVAL = 60 * 2
DEFAULT_TIMEOUT = 5
SOUND_INTERNET_OK = state.SOUND_BEEP_SOFT
SOUND_NO_NET = state.SOUND_HONK
SOUND_FOX_CHANGE_DETECTED = util.get_say('fox change detected')


class InterWebber(object):
    def __init__(
        self,
        timeout=DEFAULT_TIMEOUT,
    ):
        self.state = STATE
        self.webfox = webfox.WebFox(timeout)

    def queue_sound(self, sound):
        if sound not in self.state.queue_sound:
            self.state.queue_add(sound)

    def is_remote_different(self, remote):
        compare_fields = [
            webfox.FIELD_SSID,
            webfox.FIELD_BSSID,
            webfox.FIELD_PASSPHRASE,
        ]
        local = self.state.foxlist
        if len(remote) != len(local):
            return True
        lvals = [x.get(i) for i in compare_fields for x in local]
        rvals = [x.get(i) for i in compare_fields for x in remote]
        compare_vals = [i[0] == i[1] for i in zip(lvals, rvals)]
        if all(compare_vals):
            return False
        else:
            LOG.debug("Compare vals differ: {}".format(compare_vals))
            return True

    def get_remote_fox_status(self):
        LOG.info("Polling remote fox status...")
        try:
            remote = self.webfox.get_foxes()
            # import json
            # LOG.debug("JSON:\n{}".format(json.dumps(remote, indent=4, separators=(',', ' : '))))
            # interwebs are connecting
            # raise ValueError("honk test")
            if self.is_remote_different(remote):
                self.state.foxlist = remote
                self.queue_sound(SOUND_FOX_CHANGE_DETECTED)
            else:
                self.queue_sound(SOUND_INTERNET_OK)
        except Exception:
            LOG.exception("Error getting fox list")
            self.queue_sound(SOUND_NO_NET)
        pass

    def run(self):
        while True:
            self.get_remote_fox_status()
            time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    obj = InterWebber(.001)
    obj.get_remote_fox_status()
