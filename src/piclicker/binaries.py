#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import util
from sys import modules
logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
ME = modules[__name__]


airodump_ng = util.which('airodump-ng')
aircrack_ng = util.which('aircrack-ng')
airmon_ng = util.which('airmon-ng')
wifite = util.which('wifite')
espeak = util.which('espeak')
aplay = util.which('aplay')

empties = [i for i in dir(ME) if not getattr(ME, i) and not i.startswith('_')]
if empties:
    raise SystemError("The following programs need to be present before proceeding: {}".format(
        ",".join(empties),
    ))
