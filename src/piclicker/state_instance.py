#!/usr/bin/env python
# -*- coding: utf-8 -*-
import state
import cfg

config = cfg.get_config()
STATE = state.piClickerState(
    config.get(cfg.FIELD_ADAPTER_INET),
    config.get(cfg.FIELD_POLLING_INTERVAL),
    config.get(cfg.FIELD_ADAPTER_SCAN),
)
