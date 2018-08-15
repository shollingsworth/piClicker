#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from pyric import pyw
from wifi import Cell  # https://wifi.readthedocs.io/en/latest/scanning.html
import plog
import state
import libverify
from state_instance import STATE
LOG = plog.logging.getLogger(__name__)
LOG.setLevel(plog.DEFAULT_LOG_LEVEL)
# raw low/high - ping time ranges 1000 to 10 (weak => strong)
RLO = 1000
RHI = 10
# engineering low/high percentage taken from signal_map
ELO = 1
EHI = 100


class SignalStrengthController(object):
    def __init__(self):
        # seconds before it refreshs it's scan, if zero it will do realtime, but it sounds erratic
        self.normal_interval = 4
        # if set, scan will be realtime, at a cost (usually erratic sounds)
        self.no_timing = False
        # if the scan takes less than this amount of time, something is broken
        self.scan_speed_low = .01
        self.state = STATE
        # pyric seems to hate unicode for whatever fucking reason
        self.adapter = self.state.scan_adapter
        self.current = -1

    def upcard(self):
        card = pyw.getcard(self.adapter)
        if not pyw.isup(card):
            pyw.up(card)

    def get_calc(self, dbm):
        if not dbm:
            return 0, 0
        perc = int(self.state.signal_map.get(str(dbm)))
        if perc >= state.CRACK_PERCENTAGE_OK:
            cur_cnt = self.state.get_bssid_ok_count()
            cur_cnt += 1
            self.state.set_bssid_ok_count(cur_cnt)
        else:
            LOG.info("Resetting ok count for bssid: {} to zero(0)".format(self.state.bssid))
            self.state.set_bssid_ok_count(0)
        # I knew my ICS/SCADA experience would come in handy someday :-P (convert raws to eng)
        calc_out = (((perc - ELO) * ((RHI - RLO) / (EHI - ELO))) + RLO)
        return perc, calc_out

    def manip_speed(self, dbm, perc, click_rate):
        # inc poll count
        poll_cnt = self.state.get_total_poll_count()
        poll_cnt += 1
        self.state.set_total_poll_count(poll_cnt)

        if str(click_rate) != str(self.current):
            LOG.debug("signal raw: {} / perc: {} / click_rate: {}".format(dbm, perc, click_rate))
            self.state.click_rate = click_rate
            self.state.dbm = dbm
            self.state.percentage = perc
        else:
            LOG.info("no change...")

    def get_address_signal(self):
        cells = Cell.all(self.adapter)
        if len(cells) == 0:
            LOG.error("Error, no scan results detected. Is the adapter plugged in?")
        for o in cells:
            bssid = o.address
            if bssid != self.bssid:
                continue
            dbm = o.signal
            return dbm

    def check_scan_time(self, start, end):
        res = end - start
        if res <= self.scan_speed_low:
            raise Exception(" ".join([
                "Error, scan speed is much too low = '{}'".format(res),
                "low threshold = '{}' I see this when it's not actually scanning".format(self.scan_speed_low),
            ]))
        return res

    def run(self):
        self.adapter = self.state.scan_adapter.encode('ascii')
        self.upcard()
        LOG.info("Starting program: {}".format(__file__))
        LOG.debug("using Adapter: {}".format(self.adapter))
        init = False
        while True:
            self.bssid = self.state.bssid
            if not self.bssid:
                # we don't have a bssid yet
                time.sleep(2)
                continue

            # gotta make sure it's upper
            self.bssid = libverify.verify_bssid(self.bssid).upper()
            if not init:
                LOG.debug("using BSSID: {}".format(self.bssid))
                init = True

            # do the things
            start_time = time.time()
            dbm = self.get_address_signal()
            perc, click_rate = self.get_calc(dbm)
            self.manip_speed(dbm, perc, click_rate)
            self.current = click_rate
            # sleep if need be
            if self.no_timing:
                continue  # continue if we've disabled timing
            end_time = time.time()
            loop_time = self.check_scan_time(start_time, end_time)
            remaining = self.normal_interval - loop_time
            LOG.debug("timings - loop_time: {}, remaining: {}".format(loop_time, remaining))
            if remaining > 0:
                LOG.debug("iwlist sleeping: {}".format(remaining))
                time.sleep(remaining)


if __name__ == '__main__':
    obj = SignalStrengthController()
    obj.run()
