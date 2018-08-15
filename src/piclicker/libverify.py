#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import re

logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


# https://stackoverflow.com/a/7629690/7049363
def verify_bssid(bssid):
    replaces = [
        (' ' , ':'),
        ('-' , ':'),
    ]
    if not isinstance(bssid, (str, unicode)):
        raise ValueError("param is not a string/unicode")
    bssid = bssid.strip()
    bssid = bssid.lower()
    for rep in replaces:
        bssid = bssid.replace(*rep)
    if not re.match("[0-9a-f]{2}([:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", bssid):
        raise ValueError("Invalid BSSID / MAC address")
    return bssid


def test_bssids():
    # goods
    oks = [
        '  99 99 99 99 99 99',
        '  99-99-99-99-99-99',
        '  99:99:99:99:99:99',
        '  99:99:99:99:99:99    '
    ]
    # Fails
    fails = [
        {},
        'foo bar baz',
        '99:99:99:99:99:zz',
        '99:99:99:99:99:',
        '99:99:99:99:99',
        '99-99-99-99-99',
        '99 99 99 99 99',
    ]
    for i in fails:
        try:
            verify_bssid(i)
        except Exception:
            print("Fail OK: {}".format(i))
    for i in oks:
        print('OK: {}'.format(verify_bssid(i)))


if __name__ == '__main__':
    test_bssids()
