#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
from subprocess import Popen, PIPE
import psutil
import shlex
import plog
LOG = plog.logging.getLogger(__name__)
LOG.setLevel(plog.DEFAULT_LOG_LEVEL)
SAY_PREFIX = 'SAY__'


def get_say(text):
    """ return a parsable string to sound class that says something """
    return "{}{}".format(SAY_PREFIX, text)


def ansi_escape(string):
    """hacker tools like ANSI colors, I do too, just not for parsing output"""
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', string)


def exec_cmd(cmd_str, timeout=5, display=False, throw=False):
    """ execute command, optionally throw execption if exit status is non zero """
    LOG.debug("executing: '{}', timeout: {}".format(cmd_str, timeout))
    cmd_arr = shlex.split(cmd_str)
    if display:
        p = Popen(cmd_arr)
    else:
        p = Popen(cmd_arr, stdout=PIPE, stderr=PIPE)
    # stty: 'standard input': Inappropriate ioctl for device
    # p = Popen(cmd_arr, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    pid = psutil.Process(p.pid)
    try:
        pid.wait(timeout=timeout)
        output, err = p.communicate()
        LOG.debug("Output:\n{}\n".format(output))
        LOG.debug("Err:\n{}\n".format(err))
    except psutil.TimeoutExpired:
        pid.kill()
        output, err = 'TIMEOUT', 'TIMEOUT'
    rc = p.returncode
    warn_msg = "Warning: {} exited with return value: {}, err: {}".format(cmd_str, rc, err)
    if rc != 0 and throw:
        raise Exception(warn_msg)
    elif rc != 0:
        LOG.warn(warn_msg)
    return output


def which(pgm):
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return None
