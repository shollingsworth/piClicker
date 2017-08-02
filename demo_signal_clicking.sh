#!/usr/bin/env bash

err() {
    echo "${1?"argv[1]: error text"}"
    exit 1
}

clicker_prog="./clicker.py"
clicker_pid=$(pgrep -f $(basename ${clicker_prog}))
test -z "${clicker_pid}" && err "Error, couldn't find ${clicker_prog} running"
export click_rate="${1?"argv[1]: click rate (int)"}"
jq -n '.click_rate=env.click_rate' ./config_template.json  > config.json
echo "Sending click rate: ${click_rate} to pid: ${clicker_pid}"
kill -s HUP ${clicker_pid}
