#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import plog

# normally this will be True, but False when testing / debugging as a non root user
ROOT_ONLY = False

# Config settings
CONFIG_DIR = '/etc/piclicker'
CONFIG_SETTINGS_FILE = os.path.join(*[CONFIG_DIR, 'config.json'])
CONFIG_DEFAULT_POLLING_INTERVAL = 2

# default wordlist location
DEFAULT_WORDLIST = os.path.join(*[CONFIG_DIR, 'wordlist.txt'])

FIELD_ADAPTER_INET = 'adapter_inet'
FIELD_ADAPTER_SCAN = 'adapter_scan'
FIELD_POLLING_INTERVAL = 'polling_interval'
DEFAULT_CONFIG = {
    FIELD_ADAPTER_INET: 'wlan0',
    FIELD_ADAPTER_SCAN: None,
    FIELD_POLLING_INTERVAL: CONFIG_DEFAULT_POLLING_INTERVAL,
}
LOG = plog.logging.getLogger(__name__)
LOG.setLevel(plog.DEFAULT_LOG_LEVEL)


def write_config(obj):
    with open(CONFIG_SETTINGS_FILE, 'w') as fh:
        fh.write(json.dumps(obj, indent=4, separators=(',', ' : ')))


def get_config():
    if not os.path.isdir(CONFIG_DIR):
        LOG.info("{} missing, creating now".format(CONFIG_DIR))
        os.mkdir(CONFIG_DIR)

    if not os.path.exists(CONFIG_SETTINGS_FILE):
        LOG.debug("piclicker config file: {} doesn't exist, creating now".format(
            CONFIG_SETTINGS_FILE
        ))
        write_config(DEFAULT_CONFIG)
    with open(CONFIG_SETTINGS_FILE, 'r') as fh:
        config = json.load(fh)
    return config
