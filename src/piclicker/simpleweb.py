#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import json
from flask import Flask, redirect, render_template
from state_instance import STATE
from webfox import (
    FIELD_SSID,
    FIELD_BSSID,
)
logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
app = Flask(__name__)
json


def get_bssids():
    vals = []
    foxes = STATE.foxlist
    LOG.debug("status: {}".format(STATE.status))
    for i in foxes:
        bssid = i.get(FIELD_BSSID)
        name = i.get(FIELD_SSID)
        if not name:
            name = 'EMPTY'

        if bssid == STATE.bssid:
            scanning = True
        else:
            scanning = False
        vals.append({
            'bssid': bssid,
            'name': name,
            'scanning': scanning,
        })
    return vals


def get_adapters():
    vals = []
    for i in STATE.get_available_wireless():
        vals.append("<a href='/scan_adapter/{0}'>{0}</a>".format(i))
    return "\n<br>".join(vals)


@app.route("/")
def def_route():
    return render_template(
        'index.html',
        STATE = STATE,
        bssids = get_bssids(),
        cracked = STATE.get_cracked_list(),
    )


@app.route("/can_crack/<state>")
def can_crack(state):
    LOG.info("crack {}".format(state))
    if int(state):
        STATE.can_crack = True
    else:
        STATE.can_crack = False
    return redirect("/", code=302)


@app.route("/scan_adapter/<adapter>")
def scan_adapter_set(adapter):
    LOG.info("scan adapter change: {}".format(adapter))
    STATE.scan_adapter = adapter
    return redirect("/", code=302)


@app.route("/bssid/<bssid>")
def bssid_route(bssid):
    LOG.info("state: {} / bssid: {}".format(STATE, STATE.bssid))
    LOG.info("Changing BSSID to: {}".format(bssid))
    STATE.bssid = bssid
    return redirect("/", code=302)


def run(debug=False):
    app.run(debug=debug, host='0.0.0.0')


if __name__ == '__main__':
    run(True)
