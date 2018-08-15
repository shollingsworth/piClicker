#!/usr/bin/env bash
sleep_time=5
while /bin/true; do
    find -type f -name '*.pyc' -delete
    rsync -av --delete --exclude venv/ --exclude dist/ -e ssh ./ pi:"~/piClicker"
    sleep ${sleep_time}
done
