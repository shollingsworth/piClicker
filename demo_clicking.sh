#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

runfor="${1?"argv[1]: run time in seconds (int)"}"
export click_rate="${2?"argv[2]: click rate (int)"}"
clicker_prog="./clicker.py"
jq -n '.click_rate=env.click_rate' ./config_template.json  > config.json
echo "I will end in ${runfor} seconds!" && \
timeout ${runfor} ${clicker_prog} &
