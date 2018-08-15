#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
# log settings
DEFAULT_LOG_LEVEL = logging.DEBUG
logging.basicConfig(
    format=" ".join([
        '%(asctime)s',
        '%(levelname)s',
        '%(name)s',
        '%(message)s',
    ])
)
LOG = logging.getLogger(__name__)
LOG.setLevel(DEFAULT_LOG_LEVEL)
