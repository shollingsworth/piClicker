#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from util import exec_cmd, get_say
from pyric import pyw
import plog
import state
import binaries
import json
import time
import util
from state_instance import STATE
LOG = plog.logging.getLogger(__name__)
LOG.setLevel(plog.DEFAULT_LOG_LEVEL)


class piCrack(object):
    """ Handshake Capture / Monitoring plugin for piClicker """
    def __init__(
            self,
            file_prefix='capture'
    ):
        self.orig_dir = os.getcwd()
        self.dest_dir = state.PCAP_DIR
        self.cracked = state.CRACKED_FILE
        self.hs_dir = os.path.join(*[self.dest_dir, 'hs'])
        if not os.path.isdir(self.dest_dir):
            LOG.warn("path {} not detected, creating!".format(self.dest_dir))
            os.mkdir(self.dest_dir)
        self.file_prefix = os.path.join(*[self.dest_dir, file_prefix])
        self.state = STATE
        self.adapter = self.state.scan_adapter.encode('ascii')
        self.mon_adapter = None
        self.card = pyw.getcard(self.adapter)
        self.phy = self.card.phy
        self.bssid = self.state.bssid
        wordlist = self.state.wordlist
        if not os.path.exists(wordlist):
            raise IOError("Could not find file: {}".format(wordlist))
        self.wordlist = os.path.abspath(wordlist)
        self.channel = STATE.channel
        self.args = {
            'bssid': self.bssid,
            'adapter': self.adapter,
            'channel': self.channel if self.channel else '',
            'airdump': binaries.airodump_ng,
            'airmon': binaries.airmon_ng,
            'aircrack': binaries.aircrack_ng,
            'wifite': binaries.wifite,
            'wordlist': self.wordlist,
        }

    def get_cracked(self):
        LOG.debug("Checking cracked file: {}".format(self.cracked))
        if os.path.exists(self.cracked):
            LOG.debug("Opening cracked file: {}".format(self.cracked))
            with open(self.cracked, 'r') as fh:
                dat = json.load(fh)
            LOG.debug("crack dat: {}".format(dat))
        else:
            LOG.warn("No crack file found at: {}".format(self.cracked))
            dat = []
        match = [i for i in dat if i.get('bssid', '').lower() == self.bssid.lower()]
        if match:
            return match[0]

    def __enter__(self):
        LOG.info("starting monitor mode on {}".format(self.adapter))
        cmd = '{airmon} start {adapter}'.format(**self.args)
        exec_cmd(cmd)
        time.sleep(2)
        for iface in pyw.interfaces():
            try:
                c = pyw.getcard(iface)
            except Exception:
                LOG.exception("error getting interface: {}".format(iface))
                continue
            if c.phy == self.phy:
                LOG.info("Found monitor adapter: {}".format(c.dev))
                self.mon_adapter = c.dev
                self.args['mon_adapter'] = self.mon_adapter
                break
        if not self.mon_adapter:
            raise Exception("Error, could not determin monitoring adapter")
        return self

    def __exit__(self, type, value, tb):
        """ exit loop for enter, make sure airmon stops on the interface """
        LOG.info("Shutting down monitor mode on {}".format(self.mon_adapter))
        cmd = '{airmon} stop {mon_adapter}'.format(**self.args)
        exec_cmd(cmd)

    def capture(self):
        """ capture pcap handshake with wifite """
        if self.get_cracked():
            acracked = util.get_say("already cracked")
            self.state.queue_add(acracked)
            LOG.warn("Error, bssid: {} is already cracked".format(self.bssid))
            return

        LOG.info("attempting, handshake capture")
        os.chdir(self.dest_dir)
        cmd = ['{wifite}']
        if self.channel:
            cmd.append('-c {channel}')
        cmd = cmd + [
            '-b {bssid}',
            '-i {mon_adapter}',
            '--dict {wordlist}',
        ]
        cmd_str = " ".join(cmd).format(**self.args)
        try:
            exec_cmd(cmd_str, timeout=60 * 3, display=True)
        except Exception:
            # @TODO dammit gif
            # self.state.queue_add("FUUUCK!")
            self.state.queue_add(get_say("fuck unknown error"))
            LOG.exception("Error!")
