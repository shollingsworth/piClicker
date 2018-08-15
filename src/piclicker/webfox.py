#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from random import randint
import requests
from os import environ
import json
logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


FIELD_BSSID = 'bssid'
FIELD_SSID = 'ssid'
FIELD_PASSPHRASE = 'passphrase'
FIELD_CREATED = 'created'
FIELD_UPDATED = 'updated'
FIELD_SOURCE = 'source'


API_KEY = environ.get('CTFTOKEN')
if not API_KEY:
    raise ValueError("Error, env var: '{}' not set".format('CTFTOKEN'))

BASE_URL = environ.get('BASE_URL')
if not BASE_URL:
    raise ValueError("Error, env var: '{}' not set".format('BASE_URL'))

URL_POST_ADD_FOX = '{}/add_fox'.format(BASE_URL)
URL_POST_UPDATE_FOX = '{}/update_fox'.format(BASE_URL)
URL_POST_UPDATE_FOX = '{}/update_fox'.format(BASE_URL)
URL_POST_DELETE_FOX = '{}/delete_fox'.format(BASE_URL)
URL_GET_FOXES = '{}/foxes'.format(BASE_URL)
HEADER = {
    'CTFTOKEN': API_KEY,
    'Content-Type': 'application/json',
}


class WebFox(object):
    def __init__(
        self,
        timeout=5,
    ):
        self.timeout = timeout

    def mod_fox(self, dval):
        r = requests.post(
            URL_POST_UPDATE_FOX,
            json=dval,
            headers=HEADER,
            timeout=self.timeout,
        )
        return r.json()

    def add_fox(self, dval):
        r = requests.post(
            URL_POST_ADD_FOX,
            json=dval,
            headers=HEADER,
            timeout=self.timeout,
        )
        return r.json()

    def get_foxes(self):
        r = requests.get(
            URL_GET_FOXES,
            headers=HEADER,
            timeout=self.timeout,
        )
        return r.json()

    def delete_fox(self, dval):
        r = requests.post(
            URL_POST_DELETE_FOX,
            json=dval,
            headers=HEADER,
            timeout=self.timeout,
        )
        return r.json()

    def gen_mac_address(self):
        return ":".join([
            str('{:02x}'.format(randint(1, 254)))
            for i in range(6)
        ])


if __name__ == '__main__':
    obj = WebFox()
    foxes = obj.get_foxes()
    LOG.debug("JSON:\n{}".format(json.dumps(foxes, indent=4, separators=(',', ' : '))))
