#!/usr/bin/env python
# -*- coding: utf-8 -*-
from transitions import Machine
from weakref import WeakKeyDictionary
import os
from multiprocessing import Lock
from sys import modules
import json
import plog
import netifaces
import pickle
import atexit
import getpass
import cfg
import datetime
import util
from pyric import pyw
from glob import glob
MYNAME = 'piclicker'
LOG = plog.logging.getLogger(MYNAME)
LOG.setLevel(plog.DEFAULT_LOG_LEVEL)

MEM_DIR = '/dev/shm/{}'.format(MYNAME)
PERSIST_DIR = '/var/lib/{}'.format(MYNAME)
PCAP_DIR = '{}/pcap'.format(PERSIST_DIR)
CRACKED_FILE = '{}/cracked.txt'.format(PCAP_DIR)

# Field keys
FIELD_CHANNEL = 'channel'
FIELD_QUEUE_SOUND = 'queue_sound'
FIELD_LOCAL_IP = 'local_ip'
FIELD_BSSID = 'bssid'
FIELD_CLICK_RATE = 'click_rate'
FIELD_SLEEP_RATE = 'sleep_rate'
FIELD_WAVEFILE = 'wavefile'
FIELD_DBM = 'dbm'
FIELD_PERCENTAGE = 'percentage'
FIELD_WORDLIST = 'wordlist'
FIELD_STATUS = 'status'
FIELD_HAS_INTERWEBS = 'has_interwebs'
FIELD_FOX_LIST = 'foxlist'
FIELD_CAN_CRACK = 'can_crack'

# MODES
MODE_INIT = 'initializing'
MODE_CONFIG = 'need_config'
MODE_SCANNING = 'scanning_for_signal'
MODE_CRACKING = 'cracking'

# TRIGGERS
TRIG_SCAN = 'set_scan'
TRIG_CRACK = 'set_crack'
TRIG_CONFIG = 'set_config'

# BSSID Statuses
STATUS_CRACK_FAIL = 'crack_fail'
STATUS_CRACK_OK = 'crack_ok'

# resources and resource paths
EXEC_PATH = os.path.dirname(os.path.abspath(__file__))
RESOURCE_PATH = os.path.join(*[EXEC_PATH, 'piclicker_resources'])
with open(os.path.join(*[RESOURCE_PATH, 'ref_dbm_map.json']), 'r') as fh:
    DBM_MAP = json.load(fh)

# Sounds
SOUND_CLICK = os.path.join(*[RESOURCE_PATH, 'snd_click.wav'])
SOUND_SONAR = os.path.join(*[RESOURCE_PATH, 'snd_sonar.wav'])
SOUND_DING_FRIES_ARE_DONE = os.path.join(*[RESOURCE_PATH, 'snd_ding_fries_are_done.wav'])
SOUND_BEEP_SOFT = os.path.join(*[RESOURCE_PATH, 'snd_beep.wav'])
SOUND_ELEVATOR = os.path.join(*[RESOURCE_PATH, 'snd_elevator.wav'])
SOUND_HONK = os.path.join(*[RESOURCE_PATH, 'snd_honk.wav'])

# Cracking constants
CRACK_PERCENTAGE_OK = 80
CRACK_GO_COUNT = 4

# Templates
TFIELD_POLL_COUNT = 'poll_count'
TFIELD_OK_CNT = 'ok_cnt'
TFIELD_CRACK_STATUS = 'crack_status'
TEMPLATE_STATUS = {
    TFIELD_OK_CNT: 0,
    TFIELD_CRACK_STATUS: None,
    TFIELD_POLL_COUNT: 0,
}


class StateDescriptor(object):
    SAVE_DIR = MEM_DIR
    """A property that will alert observers when upon updates"""
    def __init__(self, field, default, key=None):
        self.lock = Lock()
        self.key = key
        self.data = WeakKeyDictionary()
        self.callbacks = WeakKeyDictionary()
        self.field = field
        self.default = default
        self.fn = "{}/{}".format(self.SAVE_DIR, self.field)
        self.init_file()
        # in case something bad happens
        LOG.debug("Setting {} -> {}, file: {}".format(
            field,
            default,
            self.fn,
        ))

    def init_file(self):
        if not os.path.isdir(self.SAVE_DIR):
            LOG.info("Creating Memory Directory: {}".format(self.SAVE_DIR))
            os.mkdir(self.SAVE_DIR)
        if not os.path.exists(self.fn):
            with open(self.fn, 'wb') as fh:
                pickle.dump(self.default, fh)

    def __write_val(self, value):
        try:
            self.lock.acquire()
            with open(self.fn, 'wb') as fh:
                pickle.dump(value, fh)
            LOG.debug("SET: {} => {}".format(self.field, value))
        finally:
            LOG.debug("{} WRITE lock released".format(self.field))
            self.lock.release()

    def __get_val(self):
        with open(self.fn, 'r') as fh:
            val = pickle.load(fh)
        if self.key:
            return val.get(self.key)
        else:
            return val

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.__get_val()

    def __set__(self, instance, value):
        """ setter wrap method for our various states """
        for callback in self.callbacks.get(instance, []):
            # alert callback function of new value
            callback(value)
        try:
            if getattr(instance, self.field) == value:
                return
        except AttributeError:
            setattr(instance, self.field, value)
        self.__write_val(value)

    def add_callback(self, instance, callback):
        """Add a new function to call everytime the descriptor within instance updates"""
        if instance not in self.callbacks:
            self.callbacks[instance] = []
        self.callbacks[instance].append(callback)


class PersistantStorage(StateDescriptor):
    SAVE_DIR = PERSIST_DIR


class piClickerState(object):
    # in mem
    channel = StateDescriptor(FIELD_CHANNEL, 0)
    status = StateDescriptor(FIELD_STATUS, {})
    queue_sound = StateDescriptor(FIELD_QUEUE_SOUND, [])
    local_ip = StateDescriptor(FIELD_LOCAL_IP, None)
    bssid = StateDescriptor(FIELD_BSSID, None)
    click_rate = StateDescriptor(FIELD_CLICK_RATE, 0)
    sleep_rate = StateDescriptor(FIELD_SLEEP_RATE, 3)
    wavefile = StateDescriptor(FIELD_WAVEFILE, util.get_say('initializing'))
    dbm = StateDescriptor(FIELD_DBM, 0)
    wordlist = StateDescriptor(FIELD_WORDLIST, cfg.DEFAULT_WORDLIST)
    percentage = StateDescriptor(FIELD_PERCENTAGE, 0)
    scan_adapter = StateDescriptor(cfg.FIELD_ADAPTER_SCAN, cfg.get_config().get(cfg.FIELD_ADAPTER_SCAN))
    has_interwebs = StateDescriptor(FIELD_HAS_INTERWEBS, False)
    can_crack = StateDescriptor(FIELD_CAN_CRACK, False)

    # persitants
    foxlist = PersistantStorage(FIELD_FOX_LIST, [])

    def __init__(self, inet_adapter, polling_interval, scan_adapter=None):
        # register cleanup routine
        atexit.register(self.__cleanup)

        if cfg.ROOT_ONLY and getpass.getuser() != 'root':
            raise Exception("Error, I need to be run as root")
        self.signal_map = {i.get('dbm'): i.get('percentage') for i in DBM_MAP}
        self.inet_adapter = inet_adapter
        self.polling_interval = polling_interval
        avail_wireless = self.get_available_wireless()
        self.me = modules[__name__]

        # set callbacks
        self.__class__.bssid.add_callback(self, self.set_bssid)
        self.__class__.scan_adapter.add_callback(self, self.set_scan_adapter)

        # if I only have one, go ahead and set it
        if len(avail_wireless) == 1:
            self.scan_adapter = avail_wireless[0]

        # Configure the state machine
        self.machine = Machine(
            model=self,
            states=self.__get_states(),
            initial=MODE_INIT,
        )

        ####################################
        # Now we setup all the transitions
        ####################################
        # init -> config
        self.machine.add_transition(
            trigger=TRIG_CONFIG,
            source=MODE_INIT,
            dest=MODE_CONFIG,
            unless=self.can_scan_mode.__name__,
            after=self.set_config_mode.__name__,
        )
        # config -> scanning
        self.machine.add_transition(
            trigger=TRIG_SCAN,
            source=MODE_CONFIG,
            dest=MODE_SCANNING,
            conditions=self.can_scan_mode.__name__,
            after=self.set_scan_mode.__name__,
        )
        # scanning -> crack
        self.machine.add_transition(
            trigger=TRIG_CRACK,
            source=MODE_SCANNING,
            dest=MODE_CRACKING,
            conditions=self.can_crack_mode.__name__,
            after=self.set_crack_mode.__name__,
        )

    ##############################
    # Custom Callbacks
    ##############################
    def set_bssid(self, value):
        LOG.debug("Setting self.status key value to: {}".format(value))
        self.__class__.status.key = value
        self.status = TEMPLATE_STATUS.copy()

    def set_scan_adapter(self, value):
        """ wireless adapter being used to scan / inject """
        if value:
            value = value.encode('ascii')
        else:
            value = None

        if value and pyw.isinterface(value):
            card = pyw.getcard(value)
            if 'monitor' not in pyw.devmodes(card):
                raise Exception("Error, adapter: {} cannot perform monitor mode".format(value))
        elif value:
            LOG.error("Invalid Card detected: {}, saving None to config")
            value = None
        config = cfg.get_config()
        config[cfg.FIELD_ADAPTER_SCAN] = value
        cfg.write_config(config)

    ##############################
    # Dunders
    ##############################
    def __cleanup(self):
        """ remove all the state file from the /dev/shm location """
        LOG.info("initializing cleanup")
        for i in glob("{}/*".format(MEM_DIR)):
            LOG.debug("removing file: {}".format(i))
            os.unlink(i)

    def __get_states(self):
        """ get a list of our various modes, to set as machine states """
        return [getattr(self.me, i) for i in dir(self.me) if i.startswith('MODE_')]

    ##############################
    # callables
    ##############################
    def to_dict(self):
        """ convert this class state to a dict """
        return {
            FIELD_LOCAL_IP: self.local_ip,
            FIELD_QUEUE_SOUND: self.queue_sound,
            FIELD_BSSID: self.bssid,
            FIELD_STATUS: self.status,
            FIELD_PERCENTAGE: self.percentage,
            FIELD_WORDLIST: self.wordlist,
            FIELD_SLEEP_RATE: self.sleep_rate,
            FIELD_DBM: self.dbm,
            FIELD_WAVEFILE: self.wavefile,
            FIELD_CLICK_RATE: self.click_rate,
            FIELD_FOX_LIST: self.foxlist,
            FIELD_HAS_INTERWEBS: self.has_interwebs,
            cfg.FIELD_ADAPTER_SCAN: self.scan_adapter,
            cfg.FIELD_ADAPTER_INET: self.inet_adapter,
            'timestamp': datetime.datetime.now().strftime('%s'),
            'state': self.get_state(),
        }

    def set_local_ip(self):
        """ if ip is not set, find it and set it, otherwise log an error """
        if not self.local_ip:
            try:
                ip = netifaces.ifaddresses(self.inet_adapter)[2][0].get('addr')
                err = None
            except Exception as e:
                ip = None
                err = "error getting ip from {}, {}".format(self.inet_adapter, e.message)
            if ip:
                self.local_ip = ip
            else:
                LOG.error(err)

    def set_crack_mode(self):
        """ set mode to cracking """
        self.sleep_rate = 0
        self.wavefile = SOUND_ELEVATOR

    def set_scan_mode(self):
        """ set mode to scanning """
        self.sleep_rate = 2
        if self.percentage == 0:
            self.wavefile = SOUND_SONAR
        elif self.percentage > 0:
            self.wavefile = SOUND_CLICK

    def set_config_mode(self):
        """ set mode to configuration """
        self.sleep_rate = 10
        self.set_local_ip()

        if not self.local_ip:
            self.wavefile = util.get_say('no local ip detected')
        elif not self.get_available_wireless():
            self.wavefile = util.get_say('no available scan adapters detected {}'.format(self.local_ip))
        elif not self.scan_adapter:
            self.wavefile = util.get_say('configure scan adapter at {}'.format(self.local_ip))
        elif not self.bssid:
            self.wavefile = util.get_say('configure bssid at {}'.format(self.local_ip))
        else:
            self.wavefile = util.get_say("I'm in danger")

    def get_available_wireless(self):
        """ get a list of adapters that are no our inet adapter """
        return [i for i in pyw.winterfaces() if i != self.inet_adapter]

    def get_cracked_list(self):
        if os.path.exists(CRACKED_FILE):
            try:
                with open(CRACKED_FILE, 'r') as fh:
                    dat = json.load(fh)
            except Exception:
                LOG.exception("Error, opening: {}".format(CRACKED_FILE))
                dat = []
        else:
            LOG.debug("Cracked file: {} doesnt exist yet".format(CRACKED_FILE))
            dat = []
        for idx, v in enumerate(dat):
            dval = v['date']
            ts = datetime.datetime.fromtimestamp(float(dval))
            dat[idx]['ts'] = ts
            dat[idx]['date_human'] = str(ts)
        return dat

    def can_scan_mode(self):
        """ can haz scan mode? all these need to be true to proceed """
        return all([
            self.local_ip,
            self.scan_adapter,
            self.bssid,
        ])

    def can_crack_mode(self):
        """ can we start crack-a-lackin? this will tell us """
        ok_cnt = self.get_bssid_ok_count() >= CRACK_GO_COUNT
        if not self.can_crack:
            LOG.debug("crack mode not enabled")
            return False
        elif ok_cnt and (not self.wordlist or not os.path.exists(self.wordlist)):
            self.wavefile = util.get_say("need wordlist at {}".format(self.local_ip))
            return False
        else:
            return all([
                self.get_bssid_ok_count() >= CRACK_GO_COUNT,
                self.wordlist,
            ])

    def call_trigger(self, mode):
        """ all this with CONSTANTS that begin with MODE_* to switch our status (if conditions allow)"""
        orig_state = self.get_state()
        func = getattr(self, mode)
        func()
        if self.get_state() != orig_state:
            LOG.debug("New State: {}".format(self.get_state()))

    def get_bssid_status(self):
        """ get the status of the bssid we're working on """
        return self.status[TFIELD_CRACK_STATUS]

    def get_bssid_ok_count(self):
        """ get the status of the bssid we're working on """
        return self.status[TFIELD_OK_CNT]

    def get_total_poll_count(self):
        """ get the status of the bssid we're working on """
        return self.status[TFIELD_POLL_COUNT]

    def set_total_poll_count(self, cnt):
        cur = self.status.copy()
        cur[TFIELD_POLL_COUNT] = cnt
        self.status = cur

    def set_bssid_ok_count(self, cnt):
        cur = self.status.copy()
        cur[TFIELD_OK_CNT] = cnt
        self.status = cur

    def set_bssid_status(self, value):
        """ set status of the bssid we're working on """
        cur = self.status.copy()
        cur[TFIELD_CRACK_STATUS] = value
        self.status = cur

    def get_state(self):
        """ get our current state """
        return self.state

    def queue_pop(self):
        """ pop the first value from the sound queue list """
        queue = self.queue_sound
        if not queue:
            return None
        val = queue.pop(0)
        self.queue_sound = queue
        return val

    def queue_add(self, sound):
        """ add a value to the sound queue list """
        queue = list(self.queue_sound)
        queue.append(sound)
        self.queue_sound = queue
